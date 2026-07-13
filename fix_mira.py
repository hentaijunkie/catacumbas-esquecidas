import sys
from rembg import remove
from PIL import Image

path = r"c:\rpg\assets\sprites\mira.png"
try:
    input_image = Image.open(path)
    output_image = remove(input_image)
    output_image.save(path)
    print("Background removed successfully using rembg.")
except Exception as e:
    print(f"Error: {e}")
