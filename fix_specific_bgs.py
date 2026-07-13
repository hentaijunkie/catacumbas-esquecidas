import os
from PIL import Image
from rembg import remove

SPRITES_DIR = r"c:\rpg\assets\sprites"

files_to_fix = [
    "inimigo_golem_barro.png",
    "inimigo_sombra_vampirica.png"
]

for filename in files_to_fix:
    path = os.path.join(SPRITES_DIR, filename)
    try:
        if os.path.exists(path):
            img = Image.open(path).convert("RGBA")
            print(f"Processing {filename} with rembg...")
            output_image = remove(img)
            output_image.save(path)
            print(f"-> Fixed {filename}")
        else:
            print(f"File not found: {filename}")
    except Exception as e:
        print(f"Error on {filename}: {e}")
print("Done!")
