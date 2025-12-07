import os
from urllib.parse import urlparse

IMAGE_EXTS = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff'}
AUDIO_EXTS = {'.mp3', '.wav', '.ogg', '.m4a', '.flac'}


def is_local_path(path: str) -> bool:
    try:
        if not path:
            return False
        parsed = urlparse(path)
        # 本地文件没有 scheme 或 scheme 为 file
        return parsed.scheme in ('', 'file')
    except Exception:
        return False


def validate_local_file(path: str) -> bool:
    """验证是否为本地存在的文件。"""
    try:
        if not is_local_path(path):
            return False
        return os.path.isfile(path)
    except Exception:
        return False


def is_image_file(path: str) -> bool:
    try:
        ext = os.path.splitext(path)[1].lower()
        return ext in IMAGE_EXTS
    except Exception:
        return False


def is_audio_file(path: str) -> bool:
    try:
        ext = os.path.splitext(path)[1].lower()
        return ext in AUDIO_EXTS
    except Exception:
        return False
import os
from PyQt5.QtWidgets import QFileDialog

def open_file_dialog(title, directory, filter_="所有文件 (*)"):
    """打开文件选择对话框"""
    options = QFileDialog.Options()
    options |= QFileDialog.DontUseNativeDialog
    file_paths, _ = QFileDialog.getOpenFileNames(
        None, title, directory, filter_, options=options
    )
    return file_paths

def open_folder_dialog(title, directory):
    """打开文件夹选择对话框"""
    options = QFileDialog.Options()
    options |= QFileDialog.ShowDirsOnly | QFileDialog.DontUseNativeDialog
    folder = QFileDialog.getExistingDirectory(
        None, title, directory, options=options
    )
    return folder

def get_image_files(file_paths):
    """从文件列表中筛选图片"""
    image_exts = {'.png', '.jpg', '.jpeg', '.bmp'}
    return [f for f in file_paths if os.path.splitext(f)[1].lower() in image_exts]

def get_audio_files(file_paths):
    """从文件列表中筛选音频"""
    audio_exts = {'.mp3', '.wav', '.ogg'}
    return [f for f in file_paths if os.path.splitext(f)[1].lower() in audio_exts]

def validate_local_file(path):
    """验证是否为本地有效文件"""
    return os.path.isfile(path)