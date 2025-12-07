import os
import time
import traceback
from typing import List
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QFileDialog, QMessageBox

# 绝对导入 utils 包
from utils.file_utils import validate_local_file, is_image_file, is_audio_file
from utils.image_utils import generate_thumbnail
from utils.audio_utils import get_audio_duration
from core.models import ImageItem, AudioItem


class MediaManager(QObject):
    """媒体文件管理器（图片/音频）。负责增删、排序、信号通知。"""
    image_list_changed = pyqtSignal(list)        # 传递 ImageItem 列表
    audio_list_changed = pyqtSignal(list)        # 传递 AudioItem 列表
    audio_duration_changed = pyqtSignal(float)   # 总音频时长（秒）

    def __init__(self, parent=None):
        super().__init__(parent)
        self.image_items: List[ImageItem] = []
        self.audio_items: List[AudioItem] = []
        self.sort_mode = "按修改日期"

    def add_images_from_dialog(self):
        """通过文件对话框添加图片（多选）。"""
        files, _ = QFileDialog.getOpenFileNames(None, "选择图片文件", "", "图片文件 (*.png *.jpg *.jpeg *.bmp);;所有文件 (*)")
        if not files:
            return
        self.add_image_files(files)

    def add_folder(self):
        """添加文件夹内的图片文件（非递归）。"""
        folder = QFileDialog.getExistingDirectory(None, "选择文件夹")
        if not folder:
            return
        candidates = [os.path.join(folder, f) for f in os.listdir(folder)]
        self.add_image_files(candidates)

    def add_image_files(self, paths: List[str]):
        """批量添加图片文件（路径列表）。忽略非本地或非图片文件。"""
        new_items = []
        for p in paths:
            try:
                # 打印验证信息，便于调试（会输出到终端）
                try:
                    exists = validate_local_file(p)
                except Exception as _e:
                    exists = False
                try:
                    is_img = is_image_file(p)
                except Exception:
                    is_img = False
                print(f"[MediaManager] add_image_files: path={p!r} exists={exists} is_image={is_img}")

                if not exists or not is_img:
                    continue

                filename = os.path.basename(p)
                size = os.path.getsize(p)
                mtime = os.path.getmtime(p)
                try:
                    thumb = generate_thumbnail(p)
                except Exception:
                    # 记录详细回溯，返回占位缩略图
                    print(f"[MediaManager] generate_thumbnail failed for {p}")
                    traceback.print_exc()
                    thumb = generate_thumbnail(None)  # 返回占位缩略图

                item = ImageItem(path=p, thumbnail=thumb, filename=filename, create_time=mtime, size=size)
                new_items.append(item)
            except Exception as e:
                # 友好提示，但不崩溃；同时打印完整回溯以便定位问题
                print(f"[MediaManager] Exception while adding image {p}: {e}")
                traceback.print_exc()
                try:
                    QMessageBox.warning(None, "图片添加失败", f"无法添加 {p}: {e}")
                except Exception:
                    # 在非 GUI 上下文或显示失败时静默处理
                    pass
        if new_items:
            self.image_items.extend(new_items)
            self._sort_images()
            self.image_list_changed.emit(self.image_items)

    def add_audio_from_dialog(self):
        """通过对话框添加音频文件。"""
        files, _ = QFileDialog.getOpenFileNames(None, "选择音频文件", "", "音频文件 (*.mp3 *.wav *.ogg);;所有文件 (*)")
        if not files:
            return
        self.add_audio_files(files)

    def add_audio_files(self, paths: List[str]):
        """批量添加音频文件并计算时长。"""
        added = []
        for p in paths:
            try:
                if not validate_local_file(p) or not is_audio_file(p):
                    continue
                duration = get_audio_duration(p)
                filename = os.path.basename(p)
                item = AudioItem(path=p, duration=duration, filename=filename)
                added.append(item)
            except Exception as e:
                QMessageBox.warning(None, "音频添加失败", f"无法添加 {p}: {e}")
        if added:
            self.audio_items.extend(added)
            self.audio_list_changed.emit(self.audio_items)
            self.audio_duration_changed.emit(self.get_total_audio_duration())

    def clear_all(self):
        """清空所有媒体，根据用户确认操作。"""
        reply = QMessageBox.question(None, "确认清空", "确定要清空所有媒体文件吗？")
        if reply == QMessageBox.Yes:
            self.image_items.clear()
            self.audio_items.clear()
            self.image_list_changed.emit(self.image_items)
            self.audio_list_changed.emit(self.audio_items)

    def update_image_time(self, index: int, new_time: float):
        """
        更新第 index 个图片的时间（例如在时间轴上拖动后调用）。
        会根据当前排序策略决定是否重新排序并发送变更通知。
        """
        try:
            if index < 0 or index >= len(self.image_items):
                return
            self.image_items[index].create_time = float(new_time)
            # 如果当前按修改日期排序，则重新排序
            if self.sort_mode == "按修改日期":
                self._sort_images()
            # 通知 UI 更新
            self.image_list_changed.emit(self.image_items)
        except Exception:
            pass
            self.audio_duration_changed.emit(0.0)

    def _sort_images(self):
        """根据当前排序方式排序 image_items。"""
        try:
            if self.sort_mode == "按修改日期":
                self.image_items.sort(key=lambda x: x.create_time)
            elif self.sort_mode == "按文件名":
                self.image_items.sort(key=lambda x: x.filename.lower())
            elif self.sort_mode == "按文件大小":
                self.image_items.sort(key=lambda x: x.size)
        except Exception:
            pass

    def set_sort_mode(self, mode: str):
        """设置排序方式并触发更新。"""
        self.sort_mode = mode
        self._sort_images()
        self.image_list_changed.emit(self.image_items)

    def reorder_images(self, new_order: list):
        """按 new_order（原始索引列表，从左到右）重新排列 image_items。
        new_order 应为包含当前所有索引的列表，例如 [2,0,1]。"""
        try:
            if not new_order or len(new_order) != len(self.image_items):
                return
            new_items = []
            for i in new_order:
                if i < 0 or i >= len(self.image_items):
                    return
                new_items.append(self.image_items[int(i)])
            self.image_items = new_items
            # emit update
            self.image_list_changed.emit(self.image_items)
        except Exception:
            pass

    def get_total_audio_duration(self) -> float:
        return sum(a.duration for a in self.audio_items)

    def get_image_time_bounds(self):
        """返回最早和最晚图片的创建时间（时间戳）。如果不足两张返回 (None,None)。"""
        if not self.image_items:
            return None, None
        times = [i.create_time for i in self.image_items]
        return min(times), max(times)
