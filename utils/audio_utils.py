from typing import Optional

def get_audio_duration(path: str) -> float:
    """尝试使用 mutagen 获取音频时长；回退到 moviepy（延迟导入）。

    返回秒（float）。在无法检测时抛出异常。
    """
    try:
        from mutagen import File as MutagenFile
        f = MutagenFile(path)
        if f is None or not hasattr(f, 'info'):
            raise ValueError("无法识别的音频文件")
        duration = float(getattr(f.info, 'length', 0.0))
        return duration
    except Exception:
        # 回退到 moviepy
        try:
            from moviepy.editor import AudioFileClip
            clip = AudioFileClip(path)
            d = float(clip.duration)
            clip.close()
            return d
        except Exception as e:
            raise e
from mutagen.mp3 import MP3
from mutagen.wave import WAVE
from mutagen.oggvorbis import OggVorbis
import os

def get_audio_duration(file_path):
    """获取音频时长（秒）"""
    try:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.mp3':
            audio = MP3(file_path)
        elif ext == '.wav':
            audio = WAVE(file_path)
        elif ext == '.ogg':
            audio = OggVorbis(file_path)
        else:
            return 0
        return int(audio.info.length)
    except Exception as e:
        print(f"音频时长获取失败：{str(e)}")
        return 0