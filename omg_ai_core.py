"""
OMG_AI Core Module
==================
Main orchestrator for the local AI assistant system.
Manages knowledge base, agents, avatar GUI, and voice control.
"""

import os
import sys
import json
import time
import threading
import queue
import logging
import signal
import pickle
import hashlib
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any

# ── Logging ──────────────────────────────────────────────────────────────────
LOG_DIR = Path.home() / ".omg_ai" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "omg_ai.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("OMG_AI.Core")

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR        = Path.home() / ".omg_ai"
KNOWLEDGE_DIR   = BASE_DIR / "knowledge"
AGENTS_DIR      = BASE_DIR / "agents"
CONFIG_FILE     = BASE_DIR / "config.json"
DB_PATH         = KNOWLEDGE_DIR / "knowledge.db"
MAX_KB_BYTES    = 5 * 1024 ** 3          # 5 GB hard limit
AGENT_RAM_MB    = 1024                   # ~1 GB per agent
CHECK_INTERVAL  = 30                     # seconds between housekeeping loops

for d in (KNOWLEDGE_DIR, AGENTS_DIR, LOG_DIR):
    d.mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# DEFAULT CONFIG
# ─────────────────────────────────────────────────────────────────────────────
DEFAULT_CONFIG: Dict[str, Any] = {
    "llm_backend": "ollama",          # "ollama" | "llamacpp" | "openai_compat"
    "llm_model": "llama3",
    "llm_host": "http://localhost:11434",
    "stt_engine": "whisper",          # "whisper" | "vosk"
    "tts_engine": "pyttsx3",          # "pyttsx3" | "espeak"
    "avatar_opacity": 0.92,
    "hotkey_voice": "<ctrl>+<alt>+v",
    "max_agents": 8,
    "auto_learn_interval": 3600,      # learn from new data every hour
    "version": "1.0.0",
}


def load_config() -> Dict[str, Any]:
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            cfg = json.load(f)
        # merge missing keys from defaults
        for k, v in DEFAULT_CONFIG.items():
            cfg.setdefault(k, v)
        return cfg
    cfg = DEFAULT_CONFIG.copy()
    save_config(cfg)
    return cfg


def save_config(cfg: Dict[str, Any]) -> None:
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)


# ─────────────────────────────────────────────────────────────────────────────
# KNOWLEDGE BASE
# ─────────────────────────────────────────────────────────────────────────────
class KnowledgeBase:
    """
    SQLite-backed knowledge store with a hard 5 GB ceiling.
    Stores conversation turns, learned facts, and indexed file snippets.
    """

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_db()
        logger.info("KnowledgeBase initialised at %s", db_path)

    # ── Schema ────────────────────────────────────────────────────────────────
    def _init_db(self) -> None:
        with self._conn() as cx:
            cx.executescript("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    role      TEXT NOT NULL,
                    content   TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    session   TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS facts (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    key       TEXT UNIQUE NOT NULL,
                    value     TEXT NOT NULL,
                    source    TEXT,
                    updated   TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS file_index (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    filepath  TEXT NOT NULL,
                    chunk_id  INTEGER NOT NULL,
                    content   TEXT NOT NULL,
                    embedding BLOB,
                    indexed   TEXT NOT NULL,
                    UNIQUE(filepath, chunk_id)
                );
                CREATE INDEX IF NOT EXISTS idx_conv_session
                    ON conversations(session);
                CREATE INDEX IF NOT EXISTS idx_facts_key
                    ON facts(key);
            """)

    def _conn(self):
        return sqlite3.connect(self.db_path, check_same_thread=False)

    # ── Quota guard ───────────────────────────────────────────────────────────
    def _within_quota(self) -> bool:
        used = self.db_path.stat().st_size if self.db_path.exists() else 0
        return used < MAX_KB_BYTES

    def used_bytes(self) -> int:
        return self.db_path.stat().st_size if self.db_path.exists() else 0

    def used_human(self) -> str:
        b = self.used_bytes()
        for unit in ("B", "KB", "MB", "GB"):
            if b < 1024:
                return f"{b:.1f} {unit}"
            b /= 1024
        return f"{b:.1f} TB"

    # ── Conversation ─────────────────────────────────────────────────────────
    def add_turn(self, role: str, content: str, session: str) -> None:
        if not self._within_quota():
            self._evict_oldest()
        with self._conn() as cx:
            cx.execute(
                "INSERT INTO conversations (role, content, timestamp, session) VALUES (?,?,?,?)",
                (role, content, datetime.utcnow().isoformat(), session),
            )

    def get_history(self, session: str, limit: int = 40) -> List[Dict]:
        with self._conn() as cx:
            rows = cx.execute(
                "SELECT role, content FROM conversations WHERE session=? "
                "ORDER BY id DESC LIMIT ?",
                (session, limit),
            ).fetchall()
        return [{"role": r, "content": c} for r, c in reversed(rows)]

    # ── Facts ─────────────────────────────────────────────────────────────────
    def set_fact(self, key: str, value: str, source: str = "user") -> None:
        if not self._within_quota():
            return
        with self._conn() as cx:
            cx.execute(
                "INSERT INTO facts (key, value, source, updated) VALUES (?,?,?,?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated=excluded.updated",
                (key, value, source, datetime.utcnow().isoformat()),
            )

    def get_fact(self, key: str) -> Optional[str]:
        with self._conn() as cx:
            row = cx.execute("SELECT value FROM facts WHERE key=?", (key,)).fetchone()
        return row[0] if row else None

    def search_facts(self, query: str, limit: int = 5) -> List[Dict]:
        with self._conn() as cx:
            rows = cx.execute(
                "SELECT key, value FROM facts WHERE key LIKE ? OR value LIKE ? LIMIT ?",
                (f"%{query}%", f"%{query}%", limit),
            ).fetchall()
        return [{"key": k, "value": v} for k, v in rows]

    # ── File indexing ─────────────────────────────────────────────────────────
    def index_file(self, filepath: str, content: str, chunk_size: int = 500) -> int:
        """Chunk a file's text content and store in the index. Returns chunk count."""
        if not self._within_quota():
            logger.warning("Quota full – skipping index of %s", filepath)
            return 0
        chunks = [content[i : i + chunk_size] for i in range(0, len(content), chunk_size)]
        with self._conn() as cx:
            for idx, chunk in enumerate(chunks):
                cx.execute(
                    "INSERT OR REPLACE INTO file_index "
                    "(filepath, chunk_id, content, indexed) VALUES (?,?,?,?)",
                    (filepath, idx, chunk, datetime.utcnow().isoformat()),
                )
        return len(chunks)

    def search_index(self, query: str, limit: int = 5) -> List[Dict]:
        with self._conn() as cx:
            rows = cx.execute(
                "SELECT filepath, chunk_id, content FROM file_index "
                "WHERE content LIKE ? LIMIT ?",
                (f"%{query}%", limit),
            ).fetchall()
        return [{"filepath": fp, "chunk": ci, "content": c} for fp, ci, c in rows]

    # ── Eviction (FIFO) ────────────────────────────────────────────────────────
    def _evict_oldest(self, n: int = 500) -> None:
        logger.warning("Knowledge quota approaching – evicting %d oldest conversation rows", n)
        with self._conn() as cx:
            cx.execute(
                "DELETE FROM conversations WHERE id IN "
                "(SELECT id FROM conversations ORDER BY id ASC LIMIT ?)",
                (n,),
            )
            cx.execute("VACUUM")


# ─────────────────────────────────────────────────────────────────────────────
# SELF-LEARNING ENGINE
# ─────────────────────────────────────────────────────────────────────────────
class SelfLearner:
    """
    Periodically scans the user's home directory for readable text files
    and indexes new/changed content into the KnowledgeBase.
    """

    WATCHED_EXTENSIONS = {".txt", ".md", ".py", ".json", ".csv", ".rst", ".yaml", ".yml"}

    def __init__(self, kb: KnowledgeBase, scan_root: Optional[Path] = None, interval: int = 3600):
        self.kb = kb
        self.scan_root = scan_root or Path.home()
        self.interval = interval
        self._seen: Dict[str, float] = {}   # filepath → mtime
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="SelfLearner")

    def start(self) -> None:
        self._thread.start()
        logger.info("SelfLearner started (interval=%ds)", self.interval)

    def stop(self) -> None:
        self._stop.set()

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                self._scan()
            except Exception as exc:
                logger.error("SelfLearner scan error: %s", exc)
            self._stop.wait(self.interval)

    def _scan(self) -> None:
        logger.info("SelfLearner: scanning %s …", self.scan_root)
        count = 0
        for path in self.scan_root.rglob("*"):
            if not self.kb._within_quota():
                logger.warning("SelfLearner: quota full, stopping scan")
                break
            if path.suffix.lower() not in self.WATCHED_EXTENSIONS:
                continue
            if any(part.startswith(".") for part in path.parts):
                continue          # skip hidden dirs
            try:
                mtime = path.stat().st_mtime
                if self._seen.get(str(path)) == mtime:
                    continue      # unchanged
                text = path.read_text(errors="ignore")
                n = self.kb.index_file(str(path), text)
                self._seen[str(path)] = mtime
                count += n
            except (PermissionError, OSError):
                pass
        logger.info("SelfLearner: indexed %d new chunks", count)

    def learn_from_interaction(self, user_input: str, ai_response: str) -> None:
        """Extract and store salient facts from a conversation turn."""
        # Simple heuristic: store Q/A pairs as facts keyed by hash
        key = "qa:" + hashlib.md5(user_input.encode()).hexdigest()[:12]
        self.kb.set_fact(key, f"Q: {user_input[:200]}\nA: {ai_response[:400]}", source="interaction")


# ─────────────────────────────────────────────────────────────────────────────
# LLM BACKEND (Ollama / llama.cpp compatible)
# ─────────────────────────────────────────────────────────────────────────────
class LLMBackend:
    """
    Thin wrapper around a locally-running Ollama or llama.cpp server
    (OpenAI-compatible /api/chat endpoint).
    """

    def __init__(self, cfg: Dict[str, Any]):
        self.host  = cfg.get("llm_host", "http://localhost:11434")
        self.model = cfg.get("llm_model", "llama3")

    def chat(self, messages: List[Dict], system: str = "") -> str:
        try:
            import urllib.request, json as _json
            payload = {
                "model": self.model,
                "messages": ([{"role": "system", "content": system}] if system else []) + messages,
                "stream": False,
            }
            data = _json.dumps(payload).encode()
            req  = urllib.request.Request(
                f"{self.host}/api/chat",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = _json.loads(resp.read())
            return result.get("message", {}).get("content", "")
        except Exception as exc:
            logger.error("LLM backend error: %s", exc)
            return f"[LLM unavailable: {exc}]"

    def is_available(self) -> bool:
        try:
            import urllib.request
            urllib.request.urlopen(f"{self.host}/api/tags", timeout=3)
            return True
        except Exception:
            return False


# ─────────────────────────────────────────────────────────────────────────────
# AGENT MANAGER
# ─────────────────────────────────────────────────────────────────────────────
class Agent:
    """A single specialised AI agent running in its own thread."""

    def __init__(self, agent_id: str, role: str, llm: LLMBackend, kb: KnowledgeBase):
        self.agent_id = agent_id
        self.role     = role
        self.llm      = llm
        self.kb       = kb
        self.task_q: queue.Queue = queue.Queue()
        self.result_q: queue.Queue = queue.Queue()
        self._stop    = threading.Event()
        self._thread  = threading.Thread(target=self._loop, daemon=True, name=f"Agent-{agent_id}")
        self.created  = datetime.utcnow().isoformat()
        self.tasks_done = 0
        self.state = "idle"
        self.accuracy = 0.90

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self.task_q.put(None)   # unblock

    def submit(self, task: str) -> None:
        self.task_q.put(task)

    def get_result(self, timeout: float = 30.0) -> Optional[str]:
        try:
            return self.result_q.get(timeout=timeout)
        except queue.Empty:
            return None

    def _loop(self) -> None:
        logger.info("Agent %s (%s) started", self.agent_id, self.role)
        system_prompt = (
            f"You are a specialised AI agent. Your role: {self.role}. "
            "Be concise, accurate, and helpful."
        )
        while not self._stop.is_set():
            task = self.task_q.get()
            if task is None:
                break
            self.state = "active"
            context = self.kb.search_facts(task[:60])
            context_str = "\n".join(f"{f['key']}: {f['value']}" for f in context)
            prompt = f"Context:\n{context_str}\n\nTask: {task}" if context_str else task
            response = self.llm.chat([{"role": "user", "content": prompt}], system=system_prompt)
            self.result_q.put(response)
            self.tasks_done += 1
            self.state = "idle"


class AgentManager:
    """Dynamically creates/destroys agents based on available RAM."""

    ROLES = [
        "File & code analysis",
        "Web research summariser",
        "Calendar & task planner",
        "System monitoring",
        "Data extraction & formatting",
        "Creative writing assistant",
        "Math & logic reasoning",
        "General Q&A",
    ]

    def __init__(self, llm: LLMBackend, kb: KnowledgeBase, cfg: Dict[str, Any]):
        self.llm  = llm
        self.kb   = kb
        self.cfg  = cfg
        self.agents: Dict[str, Agent] = {}
        self._lock = threading.Lock()

    def available_ram_mb(self) -> int:
        try:
            import psutil
            return psutil.virtual_memory().available // (1024 ** 2)
        except ImportError:
            return 2048   # conservative default

    def max_agents(self) -> int:
        ram = self.available_ram_mb()
        cap = max(1, ram // AGENT_RAM_MB)
        return min(cap, self.cfg.get("max_agents", 8))

    def spawn_agents(self) -> None:
        """Spawn up to max_agents() agents if not already running."""
        n = self.max_agents()
        with self._lock:
            current = len(self.agents)
            for i in range(current, n):
                role = self.ROLES[i % len(self.ROLES)]
                aid  = f"agent_{i:02d}"
                if aid not in self.agents:
                    ag = Agent(aid, role, self.llm, self.kb)
                    ag.start()
                    self.agents[aid] = ag
                    logger.info("Spawned %s – %s", aid, role)

    def scale_down(self) -> None:
        n = self.max_agents()
        with self._lock:
            ids = list(self.agents.keys())
            while len(ids) > n:
                aid = ids.pop()
                self.agents[aid].stop()
                del self.agents[aid]
                logger.info("Retired agent %s (RAM pressure)", aid)

    def dispatch(self, task: str, agent_id: Optional[str] = None) -> Optional[str]:
        """Send a task to a specific or any available agent; return result."""
        with self._lock:
            if not self.agents:
                return None
            ag = self.agents.get(agent_id) or next(iter(self.agents.values()))
        ag.submit(task)
        return ag.get_result(timeout=60.0)

    def status(self) -> List[Dict]:
        with self._lock:
            return [
                {
                    "id": ag.agent_id,
                    "role": ag.role,
                    "tasks_done": ag.tasks_done,
                    "created": ag.created,
                }
                for ag in self.agents.values()
            ]

    def stop_all(self) -> None:
        with self._lock:
            for ag in self.agents.values():
                ag.stop()
            self.agents.clear()


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ORCHESTRATOR
# ─────────────────────────────────────────────────────────────────────────────
class OMGAICore:
    """
    Top-level orchestrator.  All subsystems are started here and the main
    chat/command API is exposed through process().
    """

    def __init__(self):
        self.cfg      = load_config()
        self.kb       = KnowledgeBase()
        self.llm      = LLMBackend(self.cfg)
        self.learner  = SelfLearner(self.kb, interval=self.cfg["auto_learn_interval"])
        self.agents   = AgentManager(self.llm, self.kb, self.cfg)
        self._session = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        self._running = False

        try:
            signal.signal(signal.SIGTERM, self._handle_signal)
            signal.signal(signal.SIGINT,  self._handle_signal)
        except ValueError:
            pass # Ignore if not running in main thread

    # ── Lifecycle ─────────────────────────────────────────────────────────────
    def start(self) -> None:
        logger.info("OMG_AI Core starting …")
        self._running = True
        self.learner.start()
        self.agents.spawn_agents()
        self._housekeeping_thread = threading.Thread(
            target=self._housekeeping, daemon=True, name="Housekeeping"
        )
        self._housekeeping_thread.start()
        logger.info("OMG_AI Core ready. KB usage: %s / 5 GB", self.kb.used_human())

    def stop(self) -> None:
        logger.info("OMG_AI Core shutting down …")
        self._running = False
        self.learner.stop()
        self.agents.stop_all()

    def _handle_signal(self, signum, frame) -> None:
        logger.info("Signal %s received – shutting down", signum)
        self.stop()
        sys.exit(0)

    def _housekeeping(self) -> None:
        while self._running:
            try:
                self.agents.scale_down()
                self.agents.spawn_agents()
                save_config(self.cfg)
            except Exception as exc:
                logger.error("Housekeeping error: %s", exc)
            time.sleep(CHECK_INTERVAL)

    # ── Public API ─────────────────────────────────────────────────────────────
    def process(self, user_input: str, use_agent: bool = False) -> str:
        """
        Process a user message.  Optionally route to an agent for specialised work.
        Returns the AI's response string.
        """
        self.kb.add_turn("user", user_input, self._session)

        # Try to find relevant knowledge context
        context_chunks = self.kb.search_index(user_input[:80])
        context_facts  = self.kb.search_facts(user_input[:80])
        context_text   = ""
        if context_chunks:
            snippets = "\n".join(c["content"][:200] for c in context_chunks[:3])
            context_text += f"\n[Relevant file content]\n{snippets}"
        if context_facts:
            facts = "\n".join(f"{f['key']}: {f['value'][:150]}" for f in context_facts[:3])
            context_text += f"\n[Known facts]\n{facts}"

        history = self.kb.get_history(self._session)

        system = (
            "You are OMG_AI, a helpful, knowledgeable local AI assistant running "
            "entirely on the user's laptop. You have access to the user's files and "
            "conversation history. Be concise, accurate, and friendly."
            + (f"\n{context_text}" if context_text else "")
        )

        if use_agent and self.agents.agents:
            response = self.agents.dispatch(user_input) or self.llm.chat(history, system=system)
        else:
            response = self.llm.chat(history, system=system)

        self.kb.add_turn("assistant", response, self._session)
        self.learner.learn_from_interaction(user_input, response)
        return response

    def status_report(self) -> Dict:
        return {
            "kb_usage":    self.kb.used_human(),
            "kb_bytes":    self.kb.used_bytes(),
            "kb_max_gb":   5,
            "agents":      self.agents.status(),
            "llm_online":  self.llm.is_available(),
            "session":     self._session,
            "uptime":      str(datetime.utcnow()),
        }


# ─────────────────────────────────────────────────────────────────────────────
# Entry point (headless mode – avatar launches separately)
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    core = OMGAICore()
    core.start()
    logger.info("Running in headless mode. Use omg_ai_avatar.py for the GUI.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        core.stop()
