"""
Archive of the original root-level test_export.py moved to tools/
This file is a backup and can be deleted later if you are satisfied.
"""
from PIL import Image
from moviepy import ImageSequenceClip

# 生成两张测试图
Image.new('RGB', (320, 240), (255, 0, 0)).save('img1.png')
Image.new('RGB', (320, 240), (0, 255, 0)).save('img2.png')

# 创建并写出视频（会调用 ffmpeg）
clip = ImageSequenceClip(['img1.png', 'img2.png'], durations=[1, 1])
clip.write_videofile('test_out.mp4', fps=24)
