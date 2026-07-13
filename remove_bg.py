import os
from PIL import Image

SPRITES_DIR = r"c:\rpg\assets\sprites"

def process_image(path):
    try:
        img = Image.open(path).convert("RGBA")
        datas = img.getdata()
        
        # We assume the top-left pixel is part of the checkerboard.
        # Often the checkerboard is made of 2 alternating colors.
        # Let's find the two most common colors in the border.
        border_pixels = []
        width, height = img.size
        for x in range(width):
            border_pixels.append(datas[x]) # top row
            border_pixels.append(datas[(height-1)*width + x]) # bottom row
        for y in range(height):
            border_pixels.append(datas[y*width]) # left col
            border_pixels.append(datas[y*width + width - 1]) # right col
            
        # Count border pixel colors
        from collections import Counter
        counts = Counter(border_pixels)
        # The background should be the most common colors on the border.
        # Since it's a checkerboard, there are likely 2 colors with high counts.
        bg_colors = [color for color, count in counts.most_common(2)]
        
        # Let's check if the most common color is somewhat gray/white (checkerboard)
        # Or we can just make the 2 most common border colors transparent everywhere!
        # But wait, what if the character has the exact same color?
        # A flood fill from the borders is safer.
        
        # A simple BFS for flood fill from all border pixels
        visited = set()
        queue = []
        for x in range(width):
            queue.append((x, 0))
            queue.append((x, height - 1))
        for y in range(height):
            queue.append((0, y))
            queue.append((width - 1, y))
            
        # Create a new image data list
        new_data = list(datas)
        
        def color_dist(c1, c2):
            return abs(c1[0]-c2[0]) + abs(c1[1]-c2[1]) + abs(c1[2]-c2[2])
            
        while queue:
            x, y = queue.pop(0)
            if (x, y) in visited:
                continue
            
            idx = y * width + x
            c = new_data[idx]
            
            # Check if this pixel color is one of the bg_colors
            # Give a small tolerance of 10 per channel to account for compression artifacts
            is_bg = False
            for bg in bg_colors:
                if color_dist(c, bg) < 30:
                    is_bg = True
                    break
                    
            if is_bg:
                visited.add((x, y))
                # Make transparent
                new_data[idx] = (c[0], c[1], c[2], 0)
                
                # Add neighbors
                if x > 0: queue.append((x-1, y))
                if x < width - 1: queue.append((x+1, y))
                if y > 0: queue.append((x, y-1))
                if y < height - 1: queue.append((x, y+1))
            else:
                visited.add((x, y))
                
        img.putdata(new_data)
        img.save(path)
        print(f"Processed {os.path.basename(path)}")
        
    except Exception as e:
        print(f"Error on {path}: {e}")

if __name__ == "__main__":
    for f in os.listdir(SPRITES_DIR):
        if f.endswith(".png"):
            process_image(os.path.join(SPRITES_DIR, f))

