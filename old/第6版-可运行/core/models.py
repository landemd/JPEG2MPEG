import os
from datetime import datetime

class MediaItem:
    def __init__(self, path):
        self.path = path
        self.name = os.path.basename(path)
        self.created_time = os.path.getctime(path)
        self.modified_time = os.path.getmtime(path)
        self.size = os.path.getsize(path)
        self.thumbnail = None
        self.info = ""
        self.duration = 3  # 默认持续时间（秒）

class ImageItem(MediaItem):
    def __init__(self, path):
        super().__init__(path)
        try:
            from PIL import Image
            with Image.open(path) as img:
                self.width, self.height = img.size
        except:
            self.width, self.height = 0, 0

class AudioItem(MediaItem):
    def __init__(self, path):
        super().__init__(path)
        self.duration = 0  # 将在加载时设置