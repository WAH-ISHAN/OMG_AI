import os
file_path = "c:\\Users\\USER\\OneDrive\\Documents\\test\\omg_ai.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace config with configure and tk constants
content = content.replace(".config(", ".configure(")
content = content.replace("tk.END", "\"end\"")
content = content.replace("tk.NORMAL", "\"normal\"")
content = content.replace("tk.DISABLED", "\"disabled\"")
content = content.replace("tk.WORD", "\"word\"")
content = content.replace("tk.BOTH", "\"both\"")
content = content.replace("tk.X", "\"x\"")
content = content.replace("tk.LEFT", "\"left\"")
content = content.replace("tk.RIGHT", "\"right\"")
content = content.replace("tk.BOTTOM", "\"bottom\"")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("tkinter constants fixed")
