from PIL import Image

path = r"c:\rpg\assets\sprites\inimigo.png"
img = Image.open(path).convert("RGBA")
d = img.getdata()
print("Top-left pixel of inimigo:", d[0])
