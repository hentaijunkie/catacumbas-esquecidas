import os
import sys

try:
    from rembg import remove
    from PIL import Image
except ImportError:
    print("Waiting for rembg to install...")
    sys.exit(1)

SPRITES_DIR = r"c:\rpg\assets\sprites"

def process_image(path):
    try:
        input_image = Image.open(path)
        # Rembg automatically removes background and creates a transparent PNG
        output_image = remove(input_image)
        output_image.save(path)
        print(f"Processed {os.path.basename(path)}")
    except Exception as e:
        print(f"Error on {path}: {e}")

if __name__ == "__main__":
    for f in os.listdir(SPRITES_DIR):
        if f.endswith(".png"):
            process_image(os.path.join(SPRITES_DIR, f))

