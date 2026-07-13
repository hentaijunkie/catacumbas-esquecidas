import os
import sys
from PIL import Image
import numpy as np

SPRITES_DIR = r"c:\rpg\assets\sprites"

def process_image(path):
    try:
        img = Image.open(path).convert("RGBA")
        data = np.array(img)
        
        # Look at the top-left pixel as the background color
        # Typical generated checkerboard is exactly 231,231,231 or 255,255,255 or similar light grays
        # We will make anything close to the 4 corners transparent.
        
        corners = [
            data[0, 0],
            data[0, -1],
            data[-1, 0],
            data[-1, -1]
        ]
        
        bg_colors = []
        for c in corners:
            # We assume it's background if it's somewhat grey/white and opaque
            if c[3] > 0 and (c[0] > 180 and c[1] > 180 and c[2] > 180):
                bg_colors.append(c[:3])
                
        if not bg_colors:
            return # nothing to do
            
        # For each bg_color, find pixels that match it within a threshold
        mask = np.zeros((data.shape[0], data.shape[1]), dtype=bool)
        
        for bg in bg_colors:
            # color distance
            dist = np.abs(data[:, :, 0].astype(int) - bg[0]) + \
                   np.abs(data[:, :, 1].astype(int) - bg[1]) + \
                   np.abs(data[:, :, 2].astype(int) - bg[2])
            mask = mask | (dist < 20)
            
        # Also, check if it's purely #ffffff or checkerboard pattern
        checker_dist = np.abs(data[:, :, 0].astype(int) - 231) + \
                       np.abs(data[:, :, 1].astype(int) - 231) + \
                       np.abs(data[:, :, 2].astype(int) - 231)
        mask = mask | (checker_dist < 20)
        
        checker_dist2 = np.abs(data[:, :, 0].astype(int) - 255) + \
                        np.abs(data[:, :, 1].astype(int) - 255) + \
                        np.abs(data[:, :, 2].astype(int) - 255)
        mask = mask | (checker_dist2 < 10)

        # Apply transparency where mask is true
        data[mask, 3] = 0
        
        new_img = Image.fromarray(data)
        new_img.save(path)
        print(f"Processed {os.path.basename(path)}")
        
    except Exception as e:
        print(f"Error on {path}: {e}")

if __name__ == "__main__":
    for f in os.listdir(SPRITES_DIR):
        if f.endswith(".png"):
            process_image(os.path.join(SPRITES_DIR, f))

