import os
from datetime import datetime
from PyQt5.QtCore import QObject, pyqtSignal, Qt
from PyQt5.QtGui import QPixmap

# 使用绝对导入
from utils.file_utils import scan_folder, get_supported_image_formats, get_supported_audio_formats
from utils.image_utils import generate_thumbnail
from utils.audio_utils import get_audio_duration
from core.models import ImageItem, AudioItem

class MediaManager(QObject):
    images_updated = pyqtSignal(list)
    audios_updated = pyqtSignal(list)
    timeline_updated = pyqtSignal(list, list)
    
    def __init__(self):
        super().__init__()
        self.images = []
        self.audios = []
    
    def add_images(self, paths):
        """添加图片"""
        new_images = []
        for path in paths:
            if not any(img.path == path for img in self.images):
                try:
                    image = ImageItem(path)
                    image.thumbnail = generate_thumbnail(path)
                    image.info = self._get_image_info(image)
                    self.images.append(image)
                    new_images.append(image)
                except Exception as e:
                    print(f"Error loading image {path}: {e}")
        
        if new_images:
            self.images_updated.emit(self.images)
            self._update_timeline()
    
    def add_images_from_folder(self, folder):
        """从文件夹添加图片"""
        extensions = get_supported_image_formats()
        files = scan_folder(folder, extensions)
        if files:
            self.add_images(files)
    
    def add_audios(self, paths):
        """添加音频"""
        new_audios = []
        for path in paths:
            if not any(aud.path == path for aud in self.audios):
                try:
                    audio = AudioItem(path)
                    audio.duration = get_audio_duration(path)
                    audio.info = self._get_audio_info(audio)
                    self.audios.append(audio)
                    new_audios.append(audio)
                except Exception as e:
                    print(f"Error loading audio {path}: {e}")
        
        if new_audios:
            self.audios_updated.emit(self.audios)
            self._update_timeline()
    
    def sort_images(self, sort_type):
        """排序图片"""
        if sort_type == 0:  # 按创建时间
            self.images.sort(key=lambda x: x.created_time)
        elif sort_type == 1:  # 按文件名
            self.images.sort(key=lambda x: x.name.lower())
        elif sort_type == 2:  # 按文件大小
            self.images.sort(key=lambda x: x.size)
        
        self.images_updated.emit(self.images)
        self._update_timeline()
    
    def _update_timeline(self):
        """更新时间轴"""
        self.timeline_updated.emit(self.images, self.audios)
    
    def clear_all(self):
        """清空所有媒体"""
        self.images = []
        self.audios = []
        self.images_updated.emit([])
        self.audios_updated.emit([])
        self._update_timeline()
    
    def _get_image_info(self, image):
        """获取图片信息字符串"""
        return (
            f"图片: {image.name}\n"
            f"大小: {image.size//1024} KB\n"
            f"尺寸: {image.width}x{image.height}\n"
            f"修改时间: {datetime.fromtimestamp(image.modified_time).strftime('%Y-%m-%d %H:%M')}"
        )
    
    def _get_audio_info(self, audio):
        """获取音频信息字符串"""
        return (
            f"音频: {audio.name}\n"
            f"大小: {audio.size//1024} KB\n"
            f"时长: {audio.duration:.1f}秒\n"
            f"修改时间: {datetime.fromtimestamp(audio.modified_time).strftime('%Y-%m-%d %H:%M')}"
        )