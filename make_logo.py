import os
import zlib
import struct
import math

os.makedirs("static", exist_ok=True)

width, height = 512, 512
cx, cy = width // 2, height // 2

pixels = bytearray()
for y in range(height):
    pixels.append(0)
    for x in range(width):
        dx = x - cx
        dy = y - cy
        dist = math.sqrt(dx * dx + dy * dy)

        # Dark futuristic background (#0b0f19)
        r, g, b = 11, 15, 25

        # Outer cyan glowing ring
        if 175 <= dist <= 205:
            r, g, b = 0, 210, 255
        elif 165 <= dist < 175 or 205 < dist <= 215:
            r, g, b = 0, 90, 130

        # Inner reactor core ring
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
print("OMEGA Logo created successfully at static/logo.png!")