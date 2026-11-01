import time

class LobbyManager:
    def __init__(self):
        # In-memory transient storage
        self.rooms = {}
        self.passcodes = {}

    def join_room(self, room_id: str, passcode: str, sender: str):
        room_id = room_id.strip().lower()
        passcode = passcode.strip()
        sender = sender.strip()

        if not room_id or not passcode:
            return False, "Room ID aur Passcode dono zaroori hain."

        # Naya room register karna
        if room_id not in self.rooms:
            self.rooms[room_id] = {
                "created_at": time.time(),
                "users": set(),
                "messages": []
            }
            self.passcodes[room_id] = passcode
            self.rooms[room_id]["users"].add(sender)
            return True, f"Naya Room '{room_id}' initialize ho gaya."

        # Existing room me passcode verification
        if self.passcodes.get(room_id) != passcode:
            return False, "Galat Passcode! Access Denied."

        self.rooms[room_id]["users"].add(sender)
        return True, f"Room '{room_id}' me connect ho gaye."

    def send_message(self, room_id: str, passcode: str, sender: str, text: str):
        room_id = room_id.strip().lower()
        passcode = passcode.strip()
        text = text.strip()

        if not text:
            return False, "Message khali nahi ho sakta."

        if room_id not in self.rooms:
            return False, "Room exist nahi karta. Pehle join karein."

        if self.passcodes.get(room_id) != passcode:
            return False, "Passcode mismatch! Message reject ho gaya."

        msg_entry = {
            "sender": sender,
            "text": text,
            "time": time.strftime("%H:%M:%S")
        }

        self.rooms[room_id]["messages"].append(msg_entry)
        if len(self.rooms[room_id]["messages"]) > 60:
            self.rooms[room_id]["messages"].pop(0)

        return True, "Message delivered."

    def fetch_messages(self, room_id: str, passcode: str):
        room_id = room_id.strip().lower()
        if room_id not in self.rooms:
            return False, []

        if self.passcodes.get(room_id) != passcode.strip():
            return False, []

        return True, self.rooms[room_id]["messages"]