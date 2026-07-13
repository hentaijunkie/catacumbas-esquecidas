import os
from PIL import Image
import numpy as np

brain_dir = r"C:\Users\Yuri\.gemini\antigravity-ide\brain\6bd6f4cf-fe9a-4542-8fa9-a3a5f6f6da6b"
files = [
    "media__1783904945338.jpg",
    "media__1783904945312.jpg",
    "media__1783904945307.png",
    "media__1783904945228.png",
    "media__1783904945172.png"
]

for f in files:
    path = os.path.join(brain_dir, f)
    img = Image.open(path).convert("RGBA")
    arr = np.array(img)
    # Check if there is actual transparency
    has_alpha = np.min(arr[:,:,3]) < 255
    # Get mean color
    mean_color = np.mean(arr[:,:,:3], axis=(0,1))
    print(f"{f}: Size={img.size}, HasAlpha={has_alpha}, MeanColor={mean_color}")
