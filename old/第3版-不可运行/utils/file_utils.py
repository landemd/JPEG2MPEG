import os

def scan_folder(folder, extensions):
    """扫描文件夹中的特定扩展名文件"""
    files = []
    for file in os.listdir(folder):
        if any(file.lower().endswith(ext) for ext in extensions):
            files.append(os.path.join(folder, file))
    return files

def get_supported_image_formats():
    """获取支持的图片格式"""
    return ['.jpg', '.jpeg', '.png', '.bmp', '.gif']

def get_supported_audio_formats():
    """获取支持的音频格式"""
    return ['.mp3', '.wav', '.ogg', '.flac']