import os
import zlib
import struct
import math

# 1. Create folders automatically
os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)

# 2. Generate Glowing OMEGA Logo (static/logo.png)
width, height = 512, 512
cx, cy = width // 2, height // 2
pixels = bytearray()

for y in range(height):
    pixels.append(0)
    for x in range(width):
        dx = x - cx
        dy = y - cy
        dist = math.sqrt(dx * dx + dy * dy)
        r, g, b = 11, 15, 25

        if 175 <= dist <= 205:
            r, g, b = 0, 210, 255
        elif 165 <= dist < 175 or 205 < dist <= 215:
            r, g, b = 0, 90, 130

        if 75 <= dist <= 92:
            r, g, b = 56, 189, 248
        elif dist < 45:
            r, g, b = 14, 165, 233

        pixels.extend([r, g, b])

def write_png(filename, w, h, raw_data):
    def chunk(tag, data):
        return struct.pack("!I", len(data)) + tag + data + struct.pack("!I", zlib.crc32(tag + data) & 0xffffffff)
    ihdr = struct.pack("!IIBBBBB", w, h, 8, 2, 0, 0, 0)
    with open(filename, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(chunk(b"IHDR", ihdr))
        f.write(chunk(b"IDAT", zlib.compress(bytes(raw_data), 9)))
        f.write(chunk(b"IEND", b""))

write_png("static/logo.png", width, height, pixels)

# 3. Create Mobile + Desktop App UI (templates/index.html)
html_code = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OMEGA | Aris Industries</title>
    <link rel="icon" type="image/png" href="/static/logo.png">
    <link rel="apple-touch-icon" href="/static/logo.png">
    <meta name="theme-color" content="#0b0f19">
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', system-ui, sans-serif; }
        body { background: #0b0f19; color: #e2e8f0; display: flex; flex-direction: column; height: 100vh; }
        header { background: #111827; padding: 14px 20px; border-bottom: 1px solid #1e293b; display: flex; align-items: center; gap: 12px; }
        header img { width: 32px; height: 32px; border-radius: 50%; }
        header h1 { font-size: 1.15rem; font-weight: 600; color: #38bdf8; letter-spacing: 0.5px; }
        header span { font-size: 0.75rem; background: #0f172a; color: #38bdf8; padding: 3px 8px; border-radius: 12px; border: 1px solid #1e293b; }
        #chat-box { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 14px; }
        .msg { max-width: 82%; padding: 12px 16px; border-radius: 14px; line-height: 1.55; font-size: 0.96rem; word-wrap: break-word; }
        .user { align-self: flex-end; background: #0284c7; color: #fff; border-bottom-right-radius: 4px; }
        .bot { align-self: flex-start; background: #1e293b; color: #f1f5f9; border-bottom-left-radius: 4px; border: 1px solid #334155; }
        .bot p { margin-bottom: 8px; }
        .bot p:last-child { margin-bottom: 0; }
        .bot ul, .bot ol { margin-left: 20px; margin-bottom: 8px; }
        .bot code { background: #0f172a; padding: 2px 6px; border-radius: 4px; color: #38bdf8; font-family: monospace; }
        .bot pre { background: #0f172a; padding: 10px; border-radius: 8px; overflow-x: auto; margin: 8px 0; }
        #input-area { display: flex; padding: 14px; background: #111827; border-top: 1px solid #1e293b; gap: 10px; }
        input { flex: 1; padding: 12px 16px; border-radius: 10px; border: 1px solid #334155; background: #0f172a; color: #fff; font-size: 1rem; outline: none; }
        input:focus { border-color: #38bdf8; }
        button { padding: 12px 22px; background: #0284c7; color: white; border: none; border-radius: 10px; font-weight: 600; cursor: pointer; }
        button:hover { background: #0369a1; }
    </style>
</head>
<body>
    <header>
        <img src="/static/logo.png" alt="OMEGA">
        <h1>OMEGA</h1>
        <span>MARK-1 • ARIS INDUSTRIES</span>
    </header>
    <div id="chat-box">
        <div class="msg bot">Systems online. Main hoon <strong>OMEGA</strong> — batao aaj kis cheez par kaam karna hai?</div>
    </div>
    <div id="input-area">
        <input type="text" id="user-input" placeholder="Ask OMEGA anything..." onkeypress="if(event.key==='Enter') sendMessage()">
        <button onclick="sendMessage()">Send</button>
    </div>

    <script>
        let history = [];
        async function sendMessage() {
            const input = document.getElementById("user-input");
            const text = input.value.trim();
            if (!text) return;

            appendMessage(text, "user");
            input.value = "";
            const loadingDiv = appendMessage("Thinking...", "bot");

            try {
                const res = await fetch("/ask", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ query: text, history: history })
                });
                const data = await res.json();
                const reply = data.response || data.error || "No response.";
                loadingDiv.innerHTML = marked.parse(reply);
                history.push({ role: "user", content: text }, { role: "assistant", content: reply });
            } catch (err) {
                loadingDiv.textContent = "Connection error. Please try again.";
            }
        }

        function appendMessage(text, sender) {
            const box = document.getElementById("chat-box");
            const div = document.createElement("div");
            div.className = "msg " + sender;
            if (sender === "bot") div.innerHTML = marked.parse(text);
            else div.textContent = text;
            box.appendChild(div);
            box.scrollTop = box.scrollHeight;
            return div;
        }
    </script>
</body>
</html>"""

with open("templates/index.html", "w", encoding="utf-8") as f:
    f.write(html_code)

print("SUCCESS! Logo aur Mobile/Desktop App UI dono ready hain!")