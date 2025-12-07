from pydub import AudioSegment

def get_audio_duration(audio_path):
    """获取音频时长（秒）"""
    try:
        audio = AudioSegment.from_file(audio_path)
        return len(audio) / 1000.0
    except Exception as e:
        print(f"Error getting audio duration for {audio_path}: {e}")
        return 0