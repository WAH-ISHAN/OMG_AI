import ast
import builtins
import sys
import glob

def check_file(filename):
    with open(filename, "r", encoding="utf-8") as f:
        content = f.read()
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        print(f"SyntaxError in {filename}: {e}")
        return

    builtin_names = set(dir(builtins))
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            if isinstance(node.ctx, ast.Load):
                pass

check_file("omg_ai.py")
