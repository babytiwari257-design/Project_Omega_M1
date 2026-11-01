import os
import json
import hashlib
import time

# Directory setup for isolated vaults
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VAULT_DIR = os.path.join(BASE_DIR, "data", "vaults")
CONFIG_FILE = os.path.join(BASE_DIR, "data", "users_config.json")
AUDIT_LOG = os.path.join(BASE_DIR, "data", "audit_log.json")

os.makedirs(VAULT_DIR, exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)

def _hash_pin(pin: str, salt: str = "omega_salt_m1") -> str:
    return hashlib.pbkdf2_hmac("sha256", pin.encode(), salt.encode(), 100000).hex()

def _load_users():
    if not os.path.exists(CONFIG_FILE):
        return {}
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _save_users(users_data):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(users_data, f, indent=4)

def log_audit(event_type: str, handle: str, details: str = ""):
    log_entry = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "event": event_type,
        "handle": handle,
        "details": details
    }
    logs = []
    if os.path.exists(AUDIT_LOG):
        try:
            with open(AUDIT_LOG, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except Exception:
            logs = []
    logs.append(log_entry)
    with open(AUDIT_LOG, "w", encoding="utf-8") as f:
        json.dump(logs[-100:], f, indent=2)

def authenticate_user(handle: str, pin: str):
    handle = handle.strip().lower()
    if not handle or not pin:
        return False, "Handle ya PIN khali nahi ho sakta."

    users = _load_users()
    pin_hash = _hash_pin(pin)

    # First time login = auto register user vault
    if handle not in users:
        users[handle] = {"pin_hash": pin_hash, "created_at": time.time()}
        _save_users(users)
        log_audit("REGISTER", handle, "New isolated vault initialized")
        return True, "Naya secure vault register ho gaya!"

    # Existing user verification
    if users[handle]["pin_hash"] == pin_hash:
        log_audit("LOGIN_SUCCESS", handle, "Access granted to vault")
        return True, "Authentication successful."
    
    log_audit("LOGIN_FAIL", handle, "Invalid PIN attempt")
    return False, "Galat PIN. Access denied."

def get_user_vault_path(handle: str):
    clean_handle = "".join(c for c in handle if c.isalnum() or c in ("_", "-"))
    return os.path.join(VAULT_DIR, f"{clean_handle}_vault.json")

def load_user_chat(handle: str) -> list:
    vault_file = get_user_vault_path(handle)
    if not os.path.exists(vault_file):
        return []
    try:
        with open(vault_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("history", [])
    except Exception:
        return []

def save_user_chat(handle: str, role: str, content: str):
    vault_file = get_user_vault_path(handle)
    history = load_user_chat(handle)
    
    history.append({
        "role": role,
        "content": content,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    })
    
    # Store history inside sandboxed vault JSON
    with open(vault_file, "w", encoding="utf-8") as f:
        json.dump({"handle": handle, "history": history[-30:]}, f, indent=2)