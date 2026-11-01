import http.server
import socketserver
import json
import os
import sys

# Core directory alignment
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

from core.vault_manager import authenticate_user, save_user_chat, load_user_chat
from core.lobby_manager import LobbyManager
from core.llm_engine import query_omega_brain

PORT = int(os.environ.get("PORT", 8080))
WEB_DIR = os.path.join(BASE_DIR, "web")
lobby_sys = LobbyManager()

class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

class OmegaHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

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

        # 2. Omega AI Reasoning Core (With Math Preservation & Sandboxed Memory)
        elif clean_path in ("/api/query", "/query", "/api/chat", "/chat") or clean_path.endswith(("query", "chat", "ask")):
            handle = req_json.get("handle", "guest").strip().lower()
            prompt = req_json.get("prompt") or req_json.get("query") or req_json.get("message") or ""
            prompt = str(prompt).strip()

            if not prompt:
                response_data = {"status": "error", "response": "Empty query received."}
            else:
                history = load_user_chat(handle)
                ai_reply = query_omega_brain(prompt, chat_context=history)

                # Persist to local disk
                save_user_chat(handle, "user", prompt)
                save_user_chat(handle, "assistant", ai_reply)

                response_data = {"status": "success", "response": ai_reply}

        # 3. Two-User Tactical Room with Passcode System
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
        print("        ARCHITECT: ARIS INDUSTRIES      ")
        print("========================================")
        print(f"[*] Core Server URL   : http://localhost:{PORT}")
        print("[*] Storage Pipeline  : Isolated Local Vaults Active")
        print("[*] Tactical Lobby    : Passcode Protected")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[*] Server shutdown safely completed.")