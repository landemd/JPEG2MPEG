import os
from PyQt5.QtWidgets import (QMainWindow, QSplitter, QToolBar, QAction,
                             QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt, QSize, QUrl
from PyQt5.QtGui import QIcon, QPalette, QColor
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import QApplication

from ui.widgets import CardWidget, SortComboBox, StatusbarWithProgress, DraggableList
from ui.timeline_widget import TimelineWidget
from core.media_manager import MediaManager
from core.export_manager import ExportManager


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("JPEG2MPEG-[*新视频]")
        self.setMinimumSize(900, 600)
        self.resize(1200, 800)
        self.setDarkTheme()

        # 管理器
        self.media_manager = MediaManager()
        self.export_manager = ExportManager()

        # 布局：垂直分割器（图片区、时间轴、音频区）
        self.splitter = QSplitter(Qt.Vertical)

        # 图片区
        self.image_card = CardWidget("图片文件")
        self.image_list = DraggableList()
        # 排序下拉放到卡片右上
        self.sort_combo = SortComboBox()
        self.image_card.set_header_widget(self.sort_combo)
        self.image_card.content_layout().addWidget(self.image_list)

        # 时间轴区
        self.timeline_card = CardWidget("时间轴")
        self.timeline = TimelineWidget()
        self.timeline_card.content_layout().addWidget(self.timeline)

        # 音频区
        self.audio_card = CardWidget("音频文件")
        self.audio_list = DraggableList()
        self.audio_card.content_layout().addWidget(self.audio_list)

        self.splitter.addWidget(self.image_card)
        self.splitter.addWidget(self.timeline_card)
        self.splitter.addWidget(self.audio_card)
        self.splitter.setSizes([int(self.height() * 0.35), int(self.height() * 0.25), int(self.height() * 0.40)])

        self.setCentralWidget(self.splitter)

        self.initToolbar()
        # 状态栏：使用 QStatusBar 容器承载自定义状态控件
        from PyQt5.QtWidgets import QStatusBar
        self._statusbar = QStatusBar()
        self.status_widget = StatusbarWithProgress()
        self._statusbar.addPermanentWidget(self.status_widget)
        self.setStatusBar(self._statusbar)

        self.connectSignals()

        # 允许拖拽文件到窗口
        self.setAcceptDrops(True)

    def setDarkTheme(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor("#1E1E1E"))
        palette.setColor(QPalette.WindowText, QColor("#D4D4D4"))
        palette.setColor(QPalette.Base, QColor("#252526"))
        palette.setColor(QPalette.AlternateBase, QColor("#1E1E1E"))
        palette.setColor(QPalette.ToolTipBase, QColor("#D4D4D4"))
        palette.setColor(QPalette.ToolTipText, QColor("#D4D4D4"))
        palette.setColor(QPalette.Text, QColor("#D4D4D4"))
        palette.setColor(QPalette.Button, QColor("#3A3A3A"))
        palette.setColor(QPalette.ButtonText, QColor("#D4D4D4"))
        palette.setColor(QPalette.Highlight, QColor("#007ACC"))
        palette.setColor(QPalette.HighlightedText, QColor("#1E1E1E"))
        self.setPalette(palette)

    def initToolbar(self):
        toolbar = QToolBar("主工具栏")
        toolbar.setIconSize(QSize(32, 32))

        add_img = QAction(QIcon.fromTheme("document-open"), "添加图片", self)
        add_img.setShortcut("Ctrl+O")
        add_img.triggered.connect(self.media_manager.add_images_from_dialog)
        toolbar.addAction(add_img)

        add_folder = QAction(QIcon.fromTheme("folder-open"), "添加文件夹", self)
        add_folder.setShortcut("Ctrl+Shift+O")
        add_folder.triggered.connect(self.media_manager.add_folder)
        toolbar.addAction(add_folder)

        toolbar.addSeparator()

        add_audio = QAction(QIcon.fromTheme("audio-x-generic"), "添加音频", self)
        add_audio.setShortcut("Ctrl+Shift+A")
        add_audio.triggered.connect(self.media_manager.add_audio_from_dialog)
        toolbar.addAction(add_audio)

        export_act = QAction(QIcon.fromTheme("video-x-generic"), "导出视频", self)
        export_act.setShortcut("Ctrl+E")
        export_act.triggered.connect(self.on_export)
        toolbar.addAction(export_act)

        open_log_act = QAction(QIcon.fromTheme("text-x-log"), "打开诊断日志", self)
        open_log_act.setShortcut("Ctrl+Shift+L")
        open_log_act.triggered.connect(self.open_diagnostic_log)
        toolbar.addAction(open_log_act)

        show_in_explorer_act = QAction(QIcon.fromTheme("folder-open"), "在资源管理器中显示", self)
        show_in_explorer_act.setShortcut("Ctrl+Alt+L")
        show_in_explorer_act.triggered.connect(self.show_diagnostic_in_explorer)
        toolbar.addAction(show_in_explorer_act)

        copy_path_act = QAction(QIcon.fromTheme("edit-copy"), "复制诊断日志路径", self)
        copy_path_act.setShortcut("Ctrl+Alt+C")
        copy_path_act.triggered.connect(self.copy_diagnostic_path)
        toolbar.addAction(copy_path_act)

        clear_act = QAction(QIcon.fromTheme("edit-clear-all"), "清空所有", self)
        clear_act.setShortcut("Ctrl+L")
        clear_act.triggered.connect(self.media_manager.clear_all)
        toolbar.addAction(clear_act)

        self.addToolBar(toolbar)

    def connectSignals(self):
        # 排序切换
        self.sort_combo.currentTextChanged.connect(self.media_manager.set_sort_mode)

        # 滚动同步
        self.timeline.horizontalScrollBar().valueChanged.connect(self.syncScroll)
        self.image_list.horizontalScrollBar().valueChanged.connect(self.syncScroll)
        self.audio_list.horizontalScrollBar().valueChanged.connect(self.syncScroll)

        # 媒体管理器
        self.media_manager.image_list_changed.connect(self.updateImageList)
        self.media_manager.audio_list_changed.connect(self.updateAudioList)
        self.media_manager.audio_duration_changed.connect(self.timeline.setDuration)

        # 导出管理（连接到状态栏控件的方法）
        self.export_manager.progress_updated.connect(self.status_widget.showProgress)
        def _on_export_finished(ok, msg):
            if ok:
                self.status_widget.set_status('ready')
            else:
                self.status_widget.set_status('error')
            self.status_widget.showMessage(msg)
        self.export_manager.export_finished.connect(_on_export_finished)
        # 时间轴点击跳转
        self.timeline.image_clicked.connect(self._on_timeline_image_clicked)
        # 当图片列表选中变化，通知时间轴高亮对应色块
        self.image_list.itemSelectionChanged.connect(self._on_image_selection_changed)
        # 时间轴内部拖动完成后更新媒体管理器中的图片时间
        try:
            self.timeline.content.image_moved.connect(self._on_timeline_image_moved)
        except Exception:
            pass
        # timeline 内部重排信号（拖动色块改变次序）
        try:
            self.timeline.content.image_reordered.connect(self._on_timeline_image_reordered)
        except Exception:
            pass

    def open_diagnostic_log(self):
        """打开 ExportManager 最近一次生成的诊断日志（JSON）。"""
        try:
            path = getattr(self.export_manager, 'last_diagnostic_log', None)
            if not path or not os.path.exists(path):
                QMessageBox.information(self, "诊断日志", "未找到诊断日志文件。请先执行一次导出。")
                return
            # 使用系统默认程序打开文件
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))
        except Exception as e:
            QMessageBox.critical(self, "打开日志失败", str(e))

    def show_diagnostic_in_explorer(self):
        """在文件管理器中显示包含诊断日志的文件夹并选中该文件（Windows 优先）。"""
        try:
            path = getattr(self.export_manager, 'last_diagnostic_log', None)
            if not path or not os.path.exists(path):
                QMessageBox.information(self, "诊断日志", "未找到诊断日志文件。请先执行一次导出。")
                return
            # Windows: 使用 os.startfile 打开 containing folder
            try:
                folder = os.path.dirname(path)
                if os.name == 'nt':
                    # 使用 explorer 并选中文件
                    os.startfile(folder)
                else:
                    QDesktopServices.openUrl(QUrl.fromLocalFile(folder))
            except Exception:
                QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(path)))
        except Exception as e:
            QMessageBox.critical(self, "打开日志失败", str(e))

    def copy_diagnostic_path(self):
        """把最近一次诊断日志的路径复制到剪贴板。"""
        try:
            path = getattr(self.export_manager, 'last_diagnostic_log', None)
            if not path:
                QMessageBox.information(self, "复制路径", "未找到诊断日志文件。请先执行一次导出。")
                return
            QApplication.clipboard().setText(path)
            QMessageBox.information(self, "复制路径", "诊断日志路径已复制到剪贴板。")
        except Exception as e:
            QMessageBox.critical(self, "复制失败", str(e))

    def syncScroll(self, value):
        sender = self.sender()
        if sender == self.timeline.horizontalScrollBar():
            self.image_list.horizontalScrollBar().setValue(value)
            self.audio_list.horizontalScrollBar().setValue(value)
        elif sender == self.image_list.horizontalScrollBar():
            self.timeline.horizontalScrollBar().setValue(value)
            self.audio_list.horizontalScrollBar().setValue(value)
        elif sender == self.audio_list.horizontalScrollBar():
            self.timeline.horizontalScrollBar().setValue(value)
            self.image_list.horizontalScrollBar().setValue(value)

    def updateImageList(self, image_items):
        self.image_list.clear()
        for idx, it in enumerate(image_items):
            mt_str = "" if it.create_time is None else str(int(it.create_time))
            self.image_list.add_media_item(it.path, it.filename, mt_str, seq_num=idx + 1)
        # 更新时间轴上的图片位置显示
        try:
            self.timeline.set_images(image_items)
        except Exception:
            pass

    def _on_timeline_image_reordered(self, new_order: list):
        """当时间轴色块顺序被用户通过拖动改变时，通知 MediaManager 重新排列图片顺序并刷新视图。"""
        try:
            # new_order 是原始索引顺序，传递给 media_manager 以按此新序列重排
            self.media_manager.reorder_images(new_order)
            # 更新列表与时间轴显示
            self.updateImageList(self.media_manager.image_items)
            try:
                self.timeline.set_images(self.media_manager.image_items)
            except Exception:
                pass
        except Exception:
            pass

    def updateAudioList(self, audio_items):
        self.audio_list.clear()
        for it in audio_items:
            dur = f"{int(it.duration)}s"
            self.audio_list.add_media_item(None, it.filename, dur)

    def _on_timeline_image_clicked(self, index: int):
        # 当时间轴上的图片缩略图被点击，滚动图片列表并选中该项
        if index < 0 or index >= self.image_list.count():
            return
        item = self.image_list.item(index)
        self.image_list.setCurrentItem(item)
        self.image_list.scrollToItem(item)
        # 标记时间轴选中项（界面高亮）
        try:
            self.timeline.set_selected_index(index)
        except Exception:
            pass

    def _on_image_selection_changed(self):
        # 将当前图片选择同步到时间轴（显示为红色块）
        try:
            idx = self.image_list.currentRow()
            if idx is None:
                idx = -1
            self.timeline.set_selected_index(idx)
        except Exception:
            pass

    def _on_timeline_image_moved(self, index: int, new_time: float):
        # 当时间轴上某个色块拖动后，更新 MediaManager 中对应图片的时间
        try:
            self.media_manager.update_image_time(index, new_time)
            # 同步到时间轴（重绘）
            self.timeline.set_images(self.media_manager.image_items)
        except Exception:
            pass

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        image_paths = []
        audio_paths = []
        for u in urls:
            p = u.toLocalFile()
            if p:
                ext = os.path.splitext(p)[1].lower()
                if ext in ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff'):
                    image_paths.append(p)
                elif ext in ('.mp3', '.wav', '.ogg', '.m4a', '.flac'):
                    audio_paths.append(p)

        if image_paths:
            self.media_manager.add_image_files(image_paths)
        if audio_paths:
            self.media_manager.add_audio_files(audio_paths)

    def on_export(self):
        out, _ = QFileDialog.getSaveFileName(self, "保存视频为", "", "MP4 文件 (*.mp4);;所有文件 (*)")
        if not out:
            return
        try:
            self.status_widget.set_status('working')
            self.status_widget.showMessage("导出开始")
            self.export_manager.export_video(self.media_manager.image_items, self.media_manager.audio_items, out)
        except Exception as e:
            QMessageBox.critical(self, "导出错误", str(e))
