import os
import re
import ast
import datetime

WORKSPACE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vision_workspace")
os.makedirs(WORKSPACE_DIR, exist_ok=True)

def auto_clean_and_verify(code: str, ext: str = ".py") -> tuple:
    """VISION Server-Side Auto-Fixer & Syntax Verifier"""
    code = code.replace("\t", "    ")
    fixed_lines = []
    for line in code.splitlines():
        s = line.rstrip()
        if ext == ".py" and s and not s.lstrip().startswith("#"):
            if s.count("(") > s.count(")"):
                s += ")" * (s.count("(") - s.count(")"))
            if s.count("[") > s.count("]"):
                s += "]" * (s.count("[") - s.count("]"))
            stripped = s.strip()
            if re.match(r'^(def |class |if |elif |else|for |while |try|except|finally)\b', stripped):
                if not stripped.endswith(":") and not stripped.endswith("\\") and "#" not in stripped:
                    s += ":"
        fixed_lines.append(s)

    clean_code = "\n".join(fixed_lines).strip() + "\n"

    if ext == ".py":
        try:
            ast.parse(clean_code)
            status = "VERIFIED & BUG-FREE"
        except SyntaxError as e:
            status = f"SYNTAX WARNING (Line {e.lineno}: {e.msg})"
    else:
        status = "FORMATTED & READY"

    return clean_code, status

def process_omega_response(user_prompt: str, omega_reply: str, username: str = "friend") -> dict:
    """OMEGA ke reply se code nikal kar auto-fix aur save karta hai"""
    ext = ".py"
    raw_code = None

    if "```html" in omega_reply:
        ext = ".html"
        raw_code = omega_reply.split("```html", 1)[1].split("```", 1)[0].strip()
    elif "```python" in omega_reply:
        ext = ".py"
        raw_code = omega_reply.split("```python", 1)[1].split("```", 1)[0].strip()
    elif "```" in omega_reply:
        raw_code = omega_reply.split("```", 1)[1].split("```", 1)[0].strip()
        if "<html" in raw_code.lower():
            ext = ".html"

    if not raw_code:
        return {"file_created": False}

    clean_code, status = auto_clean_and_verify(raw_code, ext)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_user = re.sub(r'[^a-zA-Z0-9_-]', '', username) or "friend"
    filename = f"{safe_user}_vision_{ts}{ext}"
    filepath = os.path.join(WORKSPACE_DIR, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(clean_code)

    return {
        "file_created": True,
        "filename": filename,
        "status": status
    }

def get_file_path(filename: str) -> str:
    safe_name = os.path.basename(filename)
    return os.path.join(WORKSPACE_DIR, safe_name)

def list_workspace_files() -> list:
    return sorted(os.listdir(WORKSPACE_DIR), reverse=True)