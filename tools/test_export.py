from PIL import Image
from moviepy import ImageSequenceClip
import os

# Ensure script runs in its own directory
BASE = os.path.dirname(__file__)
img1_path = os.path.join(BASE, 'img1.png')
img2_path = os.path.join(BASE, 'img2.png')

# Create two simple test images in the tools directory
Image.new('RGB', (640, 480), (255, 0, 0)).save(img1_path)
Image.new('RGB', (640, 480), (0, 255, 0)).save(img2_path)

try:
    clip = ImageSequenceClip([img1_path, img2_path], durations=[1, 1])
    out = os.path.join(BASE, 'test_out.mp4')
    print('Writing', out)
    clip.write_videofile(out, fps=24)
    print('Done. Output file:', out)
finally:
    # cleanup sample images if you want to keep them comment out the removal
    try:
        if os.path.exists(img1_path):
            os.remove(img1_path)
        if os.path.exists(img2_path):
            os.remove(img2_path)
    except Exception:
        pass
