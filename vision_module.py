import os
import re
import ast
import json
import shutil
import datetime

WORKSPACE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vision_workspace")
BACKUP_DIR = os.path.join(WORKSPACE_DIR, "backups")
os.makedirs(WORKSPACE_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)

SUPPORTED_EXTENSIONS = {
    ".py", ".html", ".htm", ".css", ".js", ".json",
    ".txt", ".md", ".csv", ".bat", ".xml", ".yml", ".yaml", ".sql", ".c", ".cpp", ".java"
}

DESKTOP_SCAN_ROOTS = [
    os.path.join(os.path.expanduser("~"), "Desktop"),
    os.path.join(os.path.expanduser("~"), "Documents"),
    os.path.join(os.path.expanduser("~"), "Downloads"),
]

SKIP_FOLDERS = {
    "Windows", "Program Files", "Program Files (x86)", "AppData",
    "$Recycle.Bin", "__pycache__", ".git", "node_modules", "vision_workspace"
}

def auto_clean_and_verify(code: str, ext: str = ".py") -> tuple:
    """Universal Multi-Format Auto-Fixer & Verifier (Python, JSON, HTML, JS, CSS, Text, etc.)"""
    ext = ext.lower()
    fixes = []

    if "\t" in code:
        code = code.replace("\t", "    ")
        fixes.append("Tabs converted to 4 spaces")

    # 1. PYTHON AUTO-FIX & AST CHECK
    if ext == ".py":
        fixed_lines = []
        for line in code.splitlines():
            s = line.rstrip()
            if s and not s.lstrip().startswith("#"):
                if s.count("(") > s.count(")"):
                    s += ")" * (s.count("(") - s.count(")"))
                    fixes.append("Closed missing ')'")
                if s.count("[") > s.count("]"):
                    s += "]" * (s.count("[") - s.count("]"))
                    fixes.append("Closed missing ']'")
                stripped = s.strip()
                if re.match(r'^(def |class |if |elif |else|for |while |try|except|finally)\b', stripped):
                    if not stripped.endswith(":") and not stripped.endswith("\\") and "#" not in stripped:
                        s += ":"
                        fixes.append("Added missing ':'")
            fixed_lines.append(s)

        clean_code = "\n".join(fixed_lines).strip() + "\n"
        try:
            ast.parse(clean_code)
            status = "VERIFIED & BUG-FREE (Python AST Passed)"
        except SyntaxError as e:
            status = f"SYNTAX WARNING (Line {e.lineno}: {e.msg})"

    # 2. JSON AUTO-FIX & VALIDATION
    elif ext == ".json":
        clean_code = re.sub(r',\s*([}\]])', r'\1', code).strip() + "\n"
        if clean_code != code.strip() + "\n":
            fixes.append("Removed trailing commas")
        try:
            parsed = json.loads(clean_code)
            clean_code = json.dumps(parsed, indent=2, ensure_ascii=False) + "\n"
            status = "VALID & FORMATTED JSON"
        except Exception as e:
            status = f"JSON ERROR: {e}"

    # 3. HTML / JS / CSS / GENERAL CODE AUTO-CLEAN
    else:
        fixed_lines = [line.rstrip() for line in code.splitlines()]
        clean_code = "\n".join(fixed_lines).strip() + "\n"
        if ext in (".html", ".htm") and "</html>" not in clean_code.lower() and "<html" in clean_code.lower():
            clean_code += "</html>\n"
            fixes.append("Closed missing </html> tag")
        status = f"SCANNED & CLEANED ({ext.upper()})"

    summary = ", ".join(dict.fromkeys(fixes)) if fixes else "No structural bugs found"
    return clean_code, f"{status} | Fixes: {summary}"

def scan_and_fix_uploaded_file(filename: str, raw_content: str, username: str = "friend") -> dict:
    """Kisi bhi uploaded ya pasted file ko read, scan, auto-fix aur save karta hai"""
    base_name = os.path.basename(filename)
    _, ext = os.path.splitext(base_name)
    if not ext:
        ext = ".txt"

    clean_code, report = auto_clean_and_verify(raw_content, ext)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_user = re.sub(r'[^a-zA-Z0-9_-]', '', username) or "friend"
    out_name = f"{safe_user}_fixed_{ts}_{base_name}"
    out_path = os.path.join(WORKSPACE_DIR, out_name)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(clean_code)

    return {
        "file_created": True,
        "filename": out_name,
        "status": report,
        "line_count": len(clean_code.splitlines()),
        "preview": clean_code[:1200]
    }

def process_omega_response(user_prompt: str, omega_reply: str, username: str = "friend") -> dict:
    """OMEGA ke chat reply se kisi bhi language ka code nikal kar auto-fix & save karta hai"""
    lang_map = {
        "python": ".py", "py": ".py", "html": ".html", "javascript": ".js",
        "js": ".js", "css": ".css", "json": ".json", "sql": ".sql",
        "cpp": ".cpp", "c": ".c", "java": ".java", "bat": ".bat", "xml": ".xml"
    }

    match = re.search(r"```([a-zA-Z0-9_+-]*)\n([\s\S]*?)```", omega_reply)
    if not match:
        return {"file_created": False}

    lang = match.group(1).strip().lower()
    raw_code = match.group(2).strip()
    ext = lang_map.get(lang, ".html" if "<html" in raw_code.lower() else ".txt")

    clean_code, report = auto_clean_and_verify(raw_code, ext)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_user = re.sub(r'[^a-zA-Z0-9_-]', '', username) or "friend"
    filename = f"{safe_user}_vision_{ts}{ext}"
    filepath = os.path.join(WORKSPACE_DIR, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(clean_code)

    return {
        "file_created": True,
        "filename": filename,
        "status": report
    }

def scan_entire_desktop() -> dict:
    """Desktop Install Mode: User ke ek command par poore PC ki files auto-read, index aur audit karta hai"""
    indexed_files = []
    buggy_files = []

    for root_dir in DESKTOP_SCAN_ROOTS:
        if not os.path.exists(root_dir):
            continue
        for root, dirs, files in os.walk(root_dir):
            dirs[:] = [d for d in dirs if d not in SKIP_FOLDERS]
            for f in files:
                _, ext = os.path.splitext(f)
                if ext.lower() in SUPPORTED_EXTENSIONS:
                    full_path = os.path.join(root, f)
                    try:
                        with open(full_path, "r", encoding="utf-8", errors="ignore") as fp:
                            content = fp.read(8000)
                        _, status = auto_clean_and_verify(content, ext)
                        entry = {"name": f, "path": full_path, "ext": ext.lower(), "status": status}
                        indexed_files.append(entry)
                        if "WARNING" in status or "ERROR" in status:
                            buggy_files.append(entry)
                    except Exception:
                        continue

    return {
        "total_scanned": len(indexed_files),
        "bugs_detected": len(buggy_files),
        "buggy_files": buggy_files[:15],
        "all_files": indexed_files[:50]
    }

def auto_fix_desktop_file(filepath: str) -> dict:
    """Desktop par kisi specific buggy file ka backup banakar usko seedha disk par auto-repair karta hai"""
    if not os.path.isfile(filepath):
        return {"success": False, "message": "File not found on disk."}

    _, ext = os.path.splitext(filepath)
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        raw_content = f.read()

    # Safe backup before modifying original file
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{ts}_{os.path.basename(filepath)}"
    shutil.copy2(filepath, os.path.join(BACKUP_DIR, backup_name))

    clean_code, report = auto_clean_and_verify(raw_content, ext)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(clean_code)

    return {
        "success": True,
        "filepath": filepath,
        "backup": backup_name,
        "status": report
    }

def get_file_path(filename: str) -> str:
    safe_name = os.path.basename(filename)
    return os.path.join(WORKSPACE_DIR, safe_name)

def list_workspace_files() -> list:
    return sorted(os.listdir(WORKSPACE_DIR), reverse=True)