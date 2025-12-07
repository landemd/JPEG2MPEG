from mutagen import File
import os

def get_audio_duration(audio_path):
    """获取音频时长（秒）"""
    try:
        if not os.path.exists(audio_path):
            return 0
            
        audio = File(audio_path)
        if audio is not None and audio.info is not None:
            return audio.info.length
        return 0
    except Exception as e:
        print(f"Error getting audio duration for {audio_path}: {e}")
        return 0