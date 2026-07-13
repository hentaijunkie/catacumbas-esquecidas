from PIL import Image

path = r"c:\rpg\assets\sprites\inimigo_aranha.png"
img = Image.open(path).convert("RGBA")
d = img.getdata()
print("Top-left pixel of Aranha:", d[0])
