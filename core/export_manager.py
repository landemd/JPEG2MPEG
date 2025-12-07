import os
import sys
import tempfile
import traceback
import datetime
import json
from typing import List
from PyQt5.QtCore import QObject, pyqtSignal
from PIL import Image as PILImage

from core.models import ImageItem, AudioItem


class ExportManager(QObject):
    """负责将图片序列与音频合成导出为 MP4 的管理器。

    注意：moviepy 在导出时按需导入（函数内部导入）。
    """
    progress_updated = pyqtSignal(int)    # 0-100
    export_finished = pyqtSignal(bool, str)  # success, message

    def __init__(self, parent=None):
        super().__init__(parent)
        # 支持可配置诊断日志目录：优先使用环境变量 `JPEG2MPEG_LOG_DIR`，其次使用系统临时目录
        env_dir = os.environ.get('JPEG2MPEG_LOG_DIR')
        if env_dir:
            try:
                os.makedirs(env_dir, exist_ok=True)
                self.log_dir = env_dir
            except Exception:
                self.log_dir = None
        else:
            self.log_dir = None
        self.last_diagnostic_log = None

    def export_video(self, images: List[ImageItem], audios: List[AudioItem], output_path: str):
        """主导出函数：images 顺序为显示顺序；audios 顺序用于合并。

        算法：
        - 如果存在音频，合并音频为单一音轨（使用 moviepy 的 concatenate_audioclips）
        - 计算每张图片在最终视频中的持续时长：如果存在音频，则根据图片创建时间在图片时间范围内的位置占比映射到音频总时长；否则平均分配每张图片相同时长（2s）。
        - 使用 moviepy 的 ImageSequenceClip 创建视频并写入文件。
        """
        # 准备一个导出诊断对象；最终会以 JSON 写入磁盘并记录为 last_diagnostic_log
        tmp_log_path = None
        diag = {}
        try:
            base_dir = self.log_dir if getattr(self, 'log_dir', None) else None
            if not base_dir:
                base_dir = tempfile.gettempdir()
            fname = f"jpeg2mpeg_export_{datetime.datetime.now().strftime('%Y%m%dT%H%M%S')}.json"
            tmp_log_path = os.path.join(base_dir, fname)
            diag['schema_version'] = '1.0'
            diag['start_time'] = datetime.datetime.now().isoformat()
            diag['python_executable'] = sys.executable
            diag['sys_path'] = list(sys.path)
        except Exception:
            tmp_log_path = None

        try:
            # 在导入 moviepy 前，确保 moviepy/imageio-ffmpeg 能找到 ffmpeg 可执行文件。
            # 如果用户在 Windows 上把 ffmpeg 安装在已知位置（例如 D:\Program Files\ffmpeg\bin），
            # 在虚拟环境中可能找不到系统 PATH 中的 ffmpeg，可通过设置环境变量强制指定。
            ffmpeg_guess = r"D:\Program Files\ffmpeg\bin\ffmpeg.exe"
            try:
                if 'IMAGEIO_FFMPEG_EXE' not in os.environ and os.path.exists(ffmpeg_guess):
                    os.environ['IMAGEIO_FFMPEG_EXE'] = ffmpeg_guess
                if 'FFMPEG_BINARY' not in os.environ and os.path.exists(ffmpeg_guess):
                    os.environ['FFMPEG_BINARY'] = ffmpeg_guess
            except Exception:
                pass

            # 记录 ffmpeg 相关信息到诊断对象
            diag['ffmpeg_guess'] = ffmpeg_guess
            diag['IMAGEIO_FFMPEG_EXE'] = os.environ.get('IMAGEIO_FFMPEG_EXE')
            diag['FFMPEG_BINARY'] = os.environ.get('FFMPEG_BINARY')
            # 尝试记录 moviepy 版本信息（若可用）
            try:
                import moviepy
                diag['moviepy_version'] = getattr(moviepy, '__version__', None)
            except Exception:
                diag['moviepy_version'] = None
            diag['platform'] = sys.platform

            # 延迟导入大型库。moviepy 的不同发行版可能没有 `moviepy.editor` 子模块，
            # 所以先尝试从 `moviepy.editor` 导入，失败则回退到直接从 `moviepy` 导入所需符号。
            import_source = None
            try:
                from moviepy.editor import ImageSequenceClip, AudioFileClip, concatenate_audioclips
                import_source = 'moviepy.editor'
            except Exception as e_editor:
                try:
                    from moviepy import ImageSequenceClip, AudioFileClip, concatenate_audioclips
                    import_source = 'moviepy'
                except Exception:
                    # 将子模块导入时的原始异常向外传播，以便记录更有价值的诊断信息
                    raise e_editor
            # 记录实际导入来源到诊断对象
            diag['moviepy_import_source'] = import_source
            # proglog 仍然单独导入
            from proglog import TqdmProgressBarLogger
        except Exception as e:
            # 记录详细诊断信息到临时日志，便于排查虚拟环境与导入问题
            try:
                tb = traceback.format_exc()
                info = [
                    f"Exception: {e}",
                    f"Python executable: {sys.executable}",
                    "sys.path:",
                    *[str(p) for p in sys.path],
                    "Traceback:",
                    tb,
                ]
                log_txt = "\n".join(info)
                tmp = tempfile.NamedTemporaryFile(delete=False, prefix="jpeg2mpeg_moviepy_error_", suffix=".log", mode="w", encoding="utf-8")
                tmp.write(log_txt)
                tmp_path = tmp.name
                tmp.close()
            except Exception:
                tmp_path = None
            # 控制台也打印以便本地查看
            try:
                print("[ExportManager] Missing moviepy or dependency:", e)
                if tmp_path:
                    print(f"[ExportManager] Diagnostic log written to: {tmp_path}")
            except Exception:
                pass
            msg = f"缺少 moviepy 或其依赖：{e}"
            if tmp_path:
                msg += f"。详细诊断请见: {tmp_path}"
            self.export_finished.emit(False, msg)
            return

        if not images:
            self.export_finished.emit(False, "没有图片可导出")
            return

        # 准备图片路径
        image_paths = [img.path for img in images]

        # 记录图片与初步信息到诊断日志
        if tmp_log_path:
            diag['image_count'] = len(image_paths)
            diag['image_paths_sample'] = image_paths[:10]

        # 计算 durations 列表
        durations = []
        total_audio_duration = sum(a.duration for a in audios) if audios else 0.0

        # 如果有至少两张图片且有音频，则按创建时间映射比例计算每张持续时间
        if total_audio_duration > 0 and len(images) >= 2:
            times = [img.create_time for img in images]
            t_min, t_max = min(times), max(times)
            span = max(1.0, t_max - t_min)
            # 为每张图片计算它相对于最早时间的百分比（0-1），然后以差分方式计算每张持续时间
            rels = [(t - t_min) / span for t in times]
            # durations as delta between consecutive rels scaled to total_audio_duration
            for i in range(len(rels)):
                if i == 0:
                    # first image duration is rels[0] portion
                    d = rels[0] * total_audio_duration
                else:
                    d = (rels[i] - rels[i - 1]) * total_audio_duration
                # ensure minimum duration
                durations.append(max(0.1, d))
            # last image: give remaining time
            consumed = sum(durations)
            if consumed < total_audio_duration:
                durations[-1] += total_audio_duration - consumed
        else:
            # 无音频或只有一张图片：平均分配，每张2秒（可调整）
            durations = [2.0] * len(images)

        # 将计算的 durations 写入 ImageItem（可用于 UI 显示）
        for img, d in zip(images, durations):
            img.duration = d

        # 记录 durations 与音频总时长
        if tmp_log_path:
            diag['durations'] = durations
            diag['total_audio_duration'] = total_audio_duration

        # 如果有音频，合并为单一音轨（使用 moviepy）
        temp_audio = None
        try:
            audio_clip = None
            if audios:
                clips = []
                for a in audios:
                    try:
                        clips.append(AudioFileClip(a.path))
                    except Exception:
                        # 忽略无法读取的音频
                        continue
                if clips:
                    if len(clips) == 1:
                        audio_clip = clips[0]
                    else:
                        audio_clip = concatenate_audioclips(clips)

            # 在创建视频剪辑前，确保所有图片尺寸相同（ImageSequenceClip 要求）
            # 选取 target_size 为所有图片的 max(width), max(height)，对较小或不同尺寸图片进行等比缩放并在黑色背景上居中填充
            temp_dir = None
            try:
                sizes = []
                for p in image_paths:
                    try:
                        with PILImage.open(p) as im:
                            sizes.append(im.size)
                    except Exception:
                        sizes.append((0, 0))
                # 选择最大宽高作为目标尺寸
                widths = [s[0] for s in sizes if s[0] > 0]
                heights = [s[1] for s in sizes if s[1] > 0]
                if widths and heights:
                    target_size = (max(widths), max(heights))
                else:
                    # 如果无法读取任何图片尺寸，就让 moviepy 自己抛错
                    target_size = None

                if target_size is not None:
                    temp_dir = tempfile.mkdtemp(prefix="jpeg2mpeg_frames_")
                    new_image_paths = []
                    for idx, p in enumerate(image_paths):
                        try:
                            with PILImage.open(p) as im:
                                im = im.convert('RGB')
                                if im.size != target_size:
                                    # 保持纵横比缩放到能放入 target_size
                                    resample_filter = getattr(PILImage, 'LANCZOS', getattr(PILImage, 'ANTIALIAS', 1))
                                    im.thumbnail(target_size, resample_filter)
                                    background = PILImage.new('RGB', target_size, (0, 0, 0))
                                    paste_x = (target_size[0] - im.width) // 2
                                    paste_y = (target_size[1] - im.height) // 2
                                    background.paste(im, (paste_x, paste_y))
                                    out_path = os.path.join(temp_dir, f"frame_{idx:06d}.png")
                                    background.save(out_path, format='PNG')
                                    new_image_paths.append(out_path)
                                else:
                                    # 相同尺寸，仍复制为 PNG 到临时目录以避免格式差异
                                    out_path = os.path.join(temp_dir, f"frame_{idx:06d}.png")
                                    im.save(out_path, format='PNG')
                                    new_image_paths.append(out_path)
                        except Exception:
                            # 无法打开时，记录并继续（moviepy 之后会报错）
                            continue
                    if new_image_paths:
                        used_image_paths = new_image_paths
                        if tmp_log_path:
                            diag['prepared_frames_count'] = len(new_image_paths)
                            diag['prepared_frames_dir'] = temp_dir
                    else:
                        used_image_paths = image_paths
                else:
                    used_image_paths = image_paths
            except Exception:
                used_image_paths = image_paths

            # 创建视频剪辑
            video_clip = ImageSequenceClip(used_image_paths, durations=durations)
            if tmp_log_path:
                diag['video_clip_repr'] = repr(video_clip)
            if audio_clip is not None:
                # 不同版本的 moviepy 提供不同的方法名：优先尝试 set_audio，其次尝试 with_audio
                audio_attach_method = None
                try:
                    if hasattr(video_clip, 'set_audio'):
                        video_clip = video_clip.set_audio(audio_clip)
                        audio_attach_method = 'set_audio'
                    elif hasattr(video_clip, 'with_audio'):
                        video_clip = video_clip.with_audio(audio_clip)
                        audio_attach_method = 'with_audio'
                    else:
                        # 最后尝试动态查找可能的别名
                        func = getattr(video_clip, 'attach_audio', None)
                        if callable(func):
                            video_clip = func(audio_clip)
                            audio_attach_method = 'attach_audio'
                except Exception:
                    # 如果附加失败，让后续的 write_videofile 抛出更明确的异常
                    audio_attach_method = 'failed'
                if tmp_log_path:
                    diag['audio_attach_method'] = audio_attach_method

            # 使用 proglog TqdmProgressBarLogger 并绑定回调更新信号
            try:
                logger = TqdmProgressBarLogger(bars={"t": {"title": "导出进度", "index": 0}}, callbacks=[self._prog_callback])
            except Exception:
                logger = None

            # 写出 MP4
            video_clip.write_videofile(output_path, fps=24, codec="libx264", logger=logger)

            # 成功写出：在诊断对象记录并把 JSON 写回文件，记录最后日志路径
            if tmp_log_path:
                diag['export_success'] = output_path
                try:
                    with open(tmp_log_path, 'w', encoding='utf-8') as f:
                        json.dump(diag, f, ensure_ascii=False, indent=2)
                except Exception:
                    pass
                self.last_diagnostic_log = tmp_log_path
            else:
                self.last_diagnostic_log = None
            self.progress_updated.emit(100)
            msg = "导出完成"
            if getattr(self, 'last_diagnostic_log', None):
                msg += f"。诊断日志: {self.last_diagnostic_log}"
            self.export_finished.emit(True, msg)
        except Exception as e:
            # 遇到异常时将 traceback 写入诊断日志（如果可用），并在 UI 中返回诊断日志路径
            try:
                tb = traceback.format_exc()
                diag['export_error'] = str(e)
                diag['traceback'] = tb
                if tmp_log_path:
                    with open(tmp_log_path, 'w', encoding='utf-8') as f:
                        json.dump(diag, f, ensure_ascii=False, indent=2)
                    err_path = tmp_log_path
                    self.last_diagnostic_log = tmp_log_path
                else:
                    err_tmp = tempfile.NamedTemporaryFile(delete=False, prefix="jpeg2mpeg_export_error_", suffix=".json", mode="w", encoding="utf-8")
                    json.dump(diag, err_tmp, ensure_ascii=False, indent=2)
                    err_path = err_tmp.name
                    err_tmp.close()
                    self.last_diagnostic_log = err_path
            except Exception:
                err_path = None
                self.last_diagnostic_log = getattr(self, 'last_diagnostic_log', None)
            msg = f"导出失败：{e}"
            if err_path:
                msg += f"。详细诊断请见: {err_path}"
            self.export_finished.emit(False, msg)
        finally:
            try:
                if temp_audio and os.path.exists(temp_audio):
                    os.remove(temp_audio)
            except Exception:
                pass
            # 清理临时生成的帧目录（如果存在）
            try:
                if 'temp_dir' in locals() and temp_dir:
                    import shutil
                    shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass

    def _prog_callback(self, **kwargs):
        """proglog 回调：尝试从 kwargs 中获取完成比例并转换为 0-100。"""
        try:
            # proglog 会传入 "progress" 等字段，尝试查找常见键
            progress = 0.0
            if "progress" in kwargs:
                progress = float(kwargs.get("progress") or 0.0)
            elif "t" in kwargs:
                progress = float(kwargs.get("t") or 0.0)
            pct = max(0, min(100, int(progress * 100)))
            self.progress_updated.emit(pct)
        except Exception:
            pass
