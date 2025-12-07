from PyQt5.QtCore import QObject, pyqtSignal
import subprocess
import os
from proglog import TqdmProgressBarLogger

# 使用绝对导入
from core.models import ImageItem, AudioItem

class ExportManager(QObject):
    progress_updated = pyqtSignal(int)
    
    def export_video(self, images, audios, output_path, progress_callback=None):
        """导出视频"""
        try:
            # 在函数内部导入 moviepy，避免模块加载时出错
            from moviepy.editor import ImageSequenceClip, AudioFileClip
            
            # 准备图片序列
            image_paths = [img.path for img in images]
            durations = [img.duration for img in images]
            
            # 创建临时目录
            temp_dir = os.path.dirname(output_path)
            temp_audio = os.path.join(temp_dir, "temp_audio.mp3")
            
            # 合并所有音频文件
            if audios:
                self.merge_audio_files(audios, temp_audio, progress_callback)
                
                # 创建视频剪辑
                video_clip = ImageSequenceClip(image_paths, durations=durations)
                
                # 添加音频
                audio_clip = AudioFileClip(temp_audio)
                video_clip = video_clip.set_audio(audio_clip)
                
                # 导出视频
                logger = TqdmProgressBarLogger(
                    bars={
                        't': {'title': '导出进度', 'index': 0}
                    },
                    callbacks=[lambda x: self._update_progress(x, progress_callback)]
                )
                
                video_clip.write_videofile(
                    output_path, 
                    fps=24, 
                    codec='libx264',
                    logger=logger,
                    threads=4
                )
                
                # 清理临时文件
                if os.path.exists(temp_audio):
                    os.remove(temp_audio)
            else:
                # 没有音频的情况
                video_clip = ImageSequenceClip(image_paths, durations=durations)
                
                logger = TqdmProgressBarLogger(
                    bars={
                        't': {'title': '导出进度', 'index': 0}
                    },
                    callbacks=[lambda x: self._update_progress(x, progress_callback)]
                )
                
                video_clip.write_videofile(
                    output_path, 
                    fps=24, 
                    codec='libx264',
                    logger=logger,
                    threads=4
                )
            
            return True
        except ImportError:
            print("MoviePy is not installed. Cannot export video.")
            return False
        except Exception as e:
            print(f"Export error: {e}")
            return False
    
    def merge_audio_files(self, audios, output_path, progress_callback=None):
        """合并多个音频文件"""
        try:
            # 使用FFmpeg合并音频
            cmd = ['ffmpeg']
            
            # 添加输入文件
            for audio in audios:
                cmd.extend(['-i', audio.path])
            
            # 添加过滤器
            filter_complex = ""
            for i in range(len(audios)):
                filter_complex += f"[{i}:0]"
            
            filter_complex += f"concat=n={len(audios)}:v=0:a=1[out]"
            cmd.extend(['-filter_complex', filter_complex])
            cmd.extend(['-map', '[out]'])
            cmd.extend(['-y', output_path])
            
            # 执行命令
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                print(f"FFmpeg error: {stderr.decode()}")
                return False
            
            return True
        except Exception as e:
            print(f"Error merging audio files: {e}")
            return False
    
    def _update_progress(self, progress, callback):
        """更新导出进度"""
        if callback:
            percent = int(progress * 100)
            callback(percent)