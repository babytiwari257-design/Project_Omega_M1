import http.server
import socketserver
import json
import os
import sys
import urllib.parse

# Core directory alignment
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

from core.vault_manager import authenticate_user, save_user_chat, load_user_chat
from core.lobby_manager import LobbyManager
from core.llm_engine import query_omega_brain
from vision_module import (
    process_omega_response,
    scan_and_fix_uploaded_file,
    scan_entire_desktop,
    auto_fix_desktop_file,
    get_file_path,
    list_workspace_files
)

PORT = int(os.environ.get("PORT", 8080))
WEB_DIR = os.path.join(BASE_DIR, "web")
lobby_sys = LobbyManager()

class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

class OmegaHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        clean_path = parsed.path.rstrip("/")

        # 1. VISION File Download Route
        if clean_path.startswith("/vision/download/"):
            filename = urllib.parse.unquote(clean_path.replace("/vision/download/", "", 1))
            filepath = get_file_path(filename)
            if os.path.isfile(filepath):
                with open(filepath, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "application/octet-stream")
                self.send_header("Content-Disposition", f'attachment; filename="{os.path.basename(filepath)}"')
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(content)
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"VISION Error: File not found.")
            return

        # 2. VISION Workspace Files List Route
        if clean_path == "/api/vision/files":
            files = list_workspace_files()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success", "files": files}).encode("utf-8"))
            return

        # Default static web UI serving
        super().do_GET()

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else ""

        try:
            req_json = json.loads(post_data) if post_data else {}
        except Exception:
            req_json = {}

        clean_path = self.path.split("?")[0].strip().rstrip("/")
        response_data = {"status": "error", "message": f"Invalid endpoint: '{self.path}'"}

        # 1. Isolated User Authentication & History
        if clean_path in ("/api/login", "/login") or clean_path.endswith("login"):
            handle = req_json.get("handle", "").strip().lower()
            pin = req_json.get("pin", "").strip()
            auth_ok, msg = authenticate_user(handle, pin)
            if auth_ok:
                history = load_user_chat(handle)
                response_data = {
                    "status": "success",
                    "message": msg,
                    "handle": handle,
                    "history": history
                }
            else:
                response_data = {"status": "error", "message": msg}

        # 2. Omega AI Reasoning Core + VISION Auto-File Forge & Voice Command Trigger
        elif clean_path in ("/api/query", "/query", "/api/chat", "/chat") or clean_path.endswith(("query", "chat", "ask")):
            handle = req_json.get("handle", "guest").strip().lower()
            prompt = req_json.get("prompt") or req_json.get("query") or req_json.get("message") or ""
            prompt = str(prompt).strip()

            if not prompt:
                response_data = {"status": "error", "response": "Empty query received."}
            elif prompt.lower() in ("scan pc", "scan desktop", "read all files", "vision scan"):
                # Ek command par poore PC ki files auto-read & audit!
                desktop_report = scan_entire_desktop()
                bug_list = "\n".join([f"- `{b['name']}` ({b['status']})" for b in desktop_report["buggy_files"]]) or "None — Sabhi files clean hain!"
                ai_reply = (
                    f"⚡ **[VISION DESKTOP AUTO-SCAN COMPLETE]**\n"
                    f"• **Total Files Indexed & Connected:** {desktop_report['total_scanned']}\n"
                    f"• **Bugs / Warnings Detected:** {desktop_report['bugs_detected']}\n\n"
                    f"**Files Needing Attention:**\n{bug_list}"
                )
                save_user_chat(handle, "user", prompt)
                save_user_chat(handle, "assistant", ai_reply)
                response_data = {"status": "success", "response": ai_reply, "desktop_scan": desktop_report}
            else:
                history = load_user_chat(handle)
                ai_reply = query_omega_brain(prompt, chat_context=history)

                # VISION Engine: Auto-detect code, fix bugs, verify syntax & save file!
                vision_info = process_omega_response(prompt, ai_reply, username=handle)
                if vision_info.get("file_created"):
                    fname = vision_info["filename"]
                    v_status = vision_info["status"]
                    ai_reply += f"\n\n---\n⚡ **[VISION FILE FORGED]** `{fname}`\n🔍 **Audit:** {v_status}\n📥 **Download Link:** `/vision/download/{fname}`"

                save_user_chat(handle, "user", prompt)
                save_user_chat(handle, "assistant", ai_reply)

                response_data = {
                    "status": "success",
                    "response": ai_reply,
                    "vision": vision_info
                }

        # 3. VISION Universal File Scanner & Auto-Corrector (Uploaded File)
        elif clean_path == "/api/vision/scan":
            handle = req_json.get("handle", "friend").strip().lower()
            filename = req_json.get("filename", "untitled.txt").strip()
            content = req_json.get("content", "")
            user_note = req_json.get("instruction", "Scan, analyze, and fix any bugs or formatting issues.").strip()

            if not content:
                response_data = {"status": "error", "message": "Empty file content received."}
            else:
                scan_res = scan_and_fix_uploaded_file(filename, content, username=handle)
                ai_prompt = f"You are VISION integrated inside OMEGA. Analyze this file '{filename}' ({scan_res['line_count']} lines).\nUser request: {user_note}\nAuto-Fixer Report: {scan_res['status']}\n\nFILE CONTENT:\n{content[:4000]}"
                ai_analysis = query_omega_brain(ai_prompt, chat_context=[])

                full_reply = (
                    f"⚡ **[VISION UNIVERSAL FILE AUDIT: `{filename}`]**\n"
                    f"• **Lines Scanned:** {scan_res['line_count']}\n"
                    f"• **Auto-Fix Status:** {scan_res['status']}\n"
                    f"• **Download Fixed File:** `/vision/download/{scan_res['filename']}`\n\n"
                    f"---\n{ai_analysis}"
                )
                save_user_chat(handle, "user", f"[Uploaded File: {filename}] {user_note}")
                save_user_chat(handle, "assistant", full_reply)

                response_data = {
                    "status": "success",
                    "response": full_reply,
                    "vision": scan_res
                }

        # 4. VISION Desktop Install Mode: Full PC Scan & Direct Disk Repair
        elif clean_path == "/api/vision/desktop_scan":
            report = scan_entire_desktop()
            response_data = {"status": "success", "desktop_scan": report}

        elif clean_path == "/api/vision/desktop_fix":
            filepath = req_json.get("filepath", "").strip()
            fix_res = auto_fix_desktop_file(filepath)
            response_data = {"status": "success" if fix_res.get("success") else "error", "result": fix_res}

        # 5. Two-User Tactical Room with Passcode System
        elif clean_path in ("/api/lobby", "/lobby") or clean_path.endswith("lobby"):
            action = req_json.get("action", "")
            room_id = req_json.get("room_id", "alpha").strip().lower()
            passcode = req_json.get("passcode", "").strip()
            sender = req_json.get("sender", "operator").strip()
            text = req_json.get("text", "")

            if action == "join":
                ok, msg = lobby_sys.join_room(room_id, passcode, sender)
                response_data = {"status": "success" if ok else "error", "message": msg}

            elif action == "send":
                ok, msg = lobby_sys.send_message(room_id, passcode, sender, text)
                response_data = {"status": "success" if ok else "error", "message": msg}

            elif action == "fetch":
                ok, msgs = lobby_sys.fetch_messages(room_id, passcode)
                if ok:
                    response_data = {"status": "success", "messages": msgs}
                else:
                    response_data = {"status": "error", "message": "Unauthorized room access."}

        # Safe Header Response Delivery
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

if __name__ == "__main__":
    with ReusableTCPServer(("", PORT), OmegaHandler) as httpd:
        print("========================================")
        print("       PROJECT OMEGA (MARK-1) READY     ")
        print("       VISION UNIFIED ENGINE: ONLINE    ")
        print("       ARCHITECT: ARIS INDUSTRIES       ")
        print("========================================")
        print(f"[*] Core Server URL   : http://localhost:{PORT}")
        print("[*] Storage Pipeline  : Isolated Local Vaults Active")
        print("[*] VISION Mode       : Cloud Forge + Desktop Auto-Reader")
        print("[*] Tactical Lobby    : Passcode Protected")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[*] Server shutdown safely completed.")