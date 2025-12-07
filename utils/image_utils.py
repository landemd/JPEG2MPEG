import io
from typing import Optional, Tuple
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt
from PIL import Image


THUMB_SIZE: Tuple[int, int] = (100, 100)


def _placeholder_pixmap(size: Tuple[int, int] = THUMB_SIZE) -> QPixmap:
    qimg = QImage(size[0], size[1], QImage.Format_RGB32)
    qimg.fill(Qt.lightGray)
    return QPixmap.fromImage(qimg)


def generate_thumbnail(path: Optional[str], size: Tuple[int, int] = THUMB_SIZE) -> QPixmap:
    """生成缩略图：PIL -> PNG bytes -> QImage -> QPixmap。

    - 处理 RGB/RGBA 模式
    - 如果出错或路径为空，返回占位图
    - 不使用 PIL.ImageQt
    """
    if not path:
        return _placeholder_pixmap(size)
    try:
        with Image.open(path) as im:
            # 转为 RGBA 或 RGB，保持兼容性
            if im.mode not in ("RGB", "RGBA"):
                im = im.convert("RGBA")
            im.thumbnail(size)
            buf = io.BytesIO()
            im.save(buf, format="PNG")
            data = buf.getvalue()
            qimg = QImage.fromData(data)
            if qimg.isNull():
                return _placeholder_pixmap(size)
            return QPixmap.fromImage(qimg)
    except Exception as e:
        # 打印详细错误到控制台以便调试
        print(f"generate_thumbnail error for {path}: {e}")
        return _placeholder_pixmap(size)
