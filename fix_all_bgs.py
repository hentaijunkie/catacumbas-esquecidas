import os
from PIL import Image
from rembg import remove

SPRITES_DIR = r"c:\rpg\assets\sprites"

def process_all():
    count = 0
    for filename in os.listdir(SPRITES_DIR):
        if not filename.endswith(".png"):
            continue
        path = os.path.join(SPRITES_DIR, filename)
        try:
            img = Image.open(path).convert("RGBA")
            # Check top-left pixel alpha
            pixel = img.getpixel((0, 0))
            if pixel[3] == 255:
                print(f"{filename} seems to have a solid background. Processing with rembg...")
                # It has a background, let's remove it
                output_image = remove(img)
                output_image.save(path)
                count += 1
                print(f"-> Fixed {filename}")
        except Exception as e:
            print(f"Error on {filename}: {e}")
    print(f"Done! Processed {count} files.")

process_all()
