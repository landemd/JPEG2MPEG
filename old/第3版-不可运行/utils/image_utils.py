from PIL import Image, ImageQt
from PyQt5.QtGui import QPixmap
import os

def generate_thumbnail(image_path, size=(100, 100)):
    """生成缩略图"""
    try:
        img = Image.open(image_path)
        img.thumbnail(size)
        return QPixmap.fromImage(ImageQt.ImageQt(img))
    except:
        # 返回默认图标
        pixmap = QPixmap(size[0], size[1])
        pixmap.fill(Qt.lightGray)
        return pixmap