import os
from PIL import Image

brain_dir = r"C:\Users\Yuri\.gemini\antigravity-ide\brain\6bd6f4cf-fe9a-4542-8fa9-a3a5f6f6da6b"
files = [f for f in os.listdir(brain_dir) if f.endswith(".png")]
files.sort(key=lambda x: os.path.getctime(os.path.join(brain_dir, x)), reverse=True)

for i, f in enumerate(files[:10]):
    path = os.path.join(brain_dir, f)
    try:
        img = Image.open(path)
        print(f"[{i}] {f} - {img.size} - {img.mode} - {os.path.getctime(path)}")
    except Exception as e:
        print(f"[{i}] {f} - ERROR: {e}")
