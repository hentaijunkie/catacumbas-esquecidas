from PIL import Image

path = r"c:\rpg\assets\sprites\inimigo.png"
img = Image.open(path).convert("RGBA")
d = img.getdata()
print("Top-left pixel:", d[0])
print("A few more border pixels:")
for i in range(1, 10):
    print(d[i])
