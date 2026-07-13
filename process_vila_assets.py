import os
import shutil
from PIL import Image
from rembg import remove

brain_dir = r"C:\Users\Yuri\.gemini\antigravity-ide\brain\6bd6f4cf-fe9a-4542-8fa9-a3a5f6f6da6b"
sprites_dir = r"c:\rpg\assets\sprites"

mapping = {
    "media__1783904945172.png": {"name": "vila_ceu.png", "rembg": False},
    "media__1783904945312.jpg": {"name": "vila_chao.png", "rembg": False},
    "media__1783904945228.png": {"name": "vila_casas.png", "rembg": True},
    "media__1783904945307.png": {"name": "vila_fonte.png", "rembg": True},
    "media__1783904945338.jpg": {"name": "vila_placa.png", "rembg": True},
}

for src_name, info in mapping.items():
    src_path = os.path.join(brain_dir, src_name)
    dst_path = os.path.join(sprites_dir, info["name"])
    
    if not os.path.exists(src_path):
        print(f"NOT FOUND: {src_path}")
        continue
        
    print(f"Processing {src_name} -> {info['name']} (rembg={info['rembg']})")
    
    if info['rembg']:
        img = Image.open(src_path).convert("RGBA")
        out = remove(img)
        out.save(dst_path)
    else:
        # Convert to PNG for consistency
        img = Image.open(src_path)
        img.save(dst_path, format="PNG")
        
print("All assets processed!")
