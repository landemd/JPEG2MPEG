from moviepy.editor import ImageSequenceClip, AudioFileClip, concatenate_videoclips
from PyQt5.QtCore import QObject, pyqtSignal

# 使用绝对导入
from core.models import ImageItem, AudioItem

class ExportManager(QObject):
    progress_updated = pyqtSignal(int)
    
    def export_video(self, images, audios, output_path, progress_callback=None):
        """导出视频"""
        try:
            # 准备图片序列
            image_paths = [img.path for img in images]
            durations = [img.duration for img in images]
            
            # 创建视频剪辑
            video_clip = ImageSequenceClip(image_paths, durations=durations)
            
            # 添加音频（如果有）
            if audios:
                audio_clips = []
                total_duration = video_clip.duration
                
                for i, audio in enumerate(audios):
                    audio_clip = AudioFileClip(audio.path)
                    
                    # 如果音频比视频长，截取视频长度
                    if audio_clip.duration > total_duration:
                        audio_clip = audio_clip.subclip(0, total_duration)
                    
                    audio_clips.append(audio_clip)
                    
                    # 更新进度
                    if progress_callback:
                        progress = int((i + 1) / len(audios) * 50)
                        progress_callback(progress)
                
                # 合并所有音频
                final_audio = concatenate_videoclips(audio_clips)
                
                # 如果音频总长度小于视频，循环音频
                if final_audio.duration < total_duration:
                    final_audio = final_audio.loop(duration=total_duration)
                
                video_clip = video_clip.set_audio(final_audio)
            
            # 导出视频
            video_clip.write_videofile(
                output_path, 
                fps=24, 
                codec='libx264',
                logger=None,
                progress_bar=False,
                callback=lambda x: self._update_progress(x, progress_callback)
            )
            
            return True
        except Exception as e:
            print(f"Export error: {e}")
            return False
    
    def _update_progress(self, progress, callback):
        """更新导出进度"""
        if callback:
            percent = int(progress * 100)
            callback(percent)