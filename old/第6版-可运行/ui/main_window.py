import os
import sys
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter, 
    QToolBar, QStatusBar, QLabel, QFileDialog, QMessageBox, QAction,
    QComboBox, QListWidgetItem, QApplication, QGraphicsView, QAbstractItemView,
    QListWidget  # 添加这个导入
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QPen, QBrush

# 使用绝对导入
from ui.timeline_widget import TimelineWidget
from ui.draggable_list import DraggableListWidget
from ui.widgets import CardWidget, StatusIndicator
from core.media_manager import MediaManager
from core.export_manager import ExportManager
from utils.file_utils import get_supported_image_formats, get_supported_audio_formats

# 尝试导入moviepy
try:
    from moviepy.editor import ImageSequenceClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("媒体合成工具 - 图片与声音转视频")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(900, 600)
        
        # 初始化管理器
        self.media_manager = MediaManager()
        self.export_manager = ExportManager()
        
        # 初始化UI
        self.init_ui()
        self.init_connections()
        
        # 检查依赖
        self.check_dependencies()
    
    def init_ui(self):
        """初始化用户界面"""
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # 创建工具栏
        self.create_toolbar()
        
        # 创建分割器
        splitter = QSplitter(Qt.Vertical)
        
        # 创建媒体管理区域
        media_widget = QWidget()
        media_layout = QHBoxLayout(media_widget)
        
        # 图片管理区域
        image_group = CardWidget("图片文件")
        image_layout = QVBoxLayout(image_group)
        
        # 排序控件
        sort_layout = QHBoxLayout()
        sort_layout.addWidget(QLabel("排序方式:"))
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["按创建时间", "按文件名", "按文件大小"])
        self.sort_combo.currentIndexChanged.connect(self.sort_image_items)
        sort_layout.addWidget(self.sort_combo)
        sort_layout.addStretch()
        image_layout.addLayout(sort_layout)
        
        self.image_list = DraggableListWidget()
        self.image_list.setViewMode(QListWidget.IconMode)  # 现在QListWidget已导入
        self.image_list.setIconSize(QSize(100, 100))
        self.image_list.setResizeMode(QListWidget.Adjust)
        self.image_list.setSpacing(10)
        image_layout.addWidget(self.image_list)
        
        # 音频管理区域
        audio_group = CardWidget("音频文件")
        audio_layout = QVBoxLayout(audio_group)
        self.audio_list = DraggableListWidget()
        self.audio_list.setViewMode(QListWidget.ListMode)  # 现在QListWidget已导入
        audio_layout.addWidget(self.audio_list)
        
        # 添加到媒体布局
        media_layout.addWidget(image_group, 1)
        media_layout.addWidget(audio_group, 1)
        
        # 创建时间轴区域
        timeline_group = CardWidget("时间轴")
        timeline_layout = QVBoxLayout(timeline_group)
        self.timeline = TimelineWidget()
        timeline_layout.addWidget(self.timeline)
        
        # 状态指示器
        self.status_indicator = StatusIndicator("就绪")
        timeline_layout.addWidget(self.status_indicator)
        
        # 添加到分割器
        splitter.addWidget(media_widget)
        splitter.addWidget(timeline_group)
        splitter.setSizes([400, 300])
        
        main_layout.addWidget(splitter)
        
        # 创建状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_label = QLabel("就绪")
        self.status_bar.addWidget(self.status_label)
    
    def create_toolbar(self):
        """创建工具栏"""
        toolbar = QToolBar("主工具栏")
        toolbar.setIconSize(QSize(32, 32))
        self.addToolBar(Qt.TopToolBarArea, toolbar)
        
        # 添加图片按钮
        add_images_action = QAction("添加图片", self)
        add_images_action.triggered.connect(self.add_images)
        toolbar.addAction(add_images_action)
        
        # 添加文件夹按钮
        add_folder_action = QAction("添加文件夹", self)
        add_folder_action.triggered.connect(self.add_folder)
        toolbar.addAction(add_folder_action)
        
        toolbar.addSeparator()
        
        # 添加音频按钮
        add_audio_action = QAction("添加音频", self)
        add_audio_action.triggered.connect(self.add_audio)
        toolbar.addAction(add_audio_action)
        
        toolbar.addSeparator()
        
        # 导出视频按钮
        export_action = QAction("导出视频", self)
        export_action.triggered.connect(self.export_video)
        toolbar.addAction(export_action)
        
        # 清空按钮
        clear_action = QAction("清空所有", self)
        clear_action.triggered.connect(self.clear_all)
        toolbar.addAction(clear_action)
    
    def init_connections(self):
        """初始化信号连接"""
        self.media_manager.images_updated.connect(self.update_image_list)
        self.media_manager.audios_updated.connect(self.update_audio_list)
        self.media_manager.timeline_updated.connect(self.update_timeline)
    
    def check_dependencies(self):
        """检查依赖库是否安装"""
        missing_deps = []
        
        try:
            from moviepy.editor import ImageSequenceClip
        except ImportError:
            missing_deps.append("moviepy")
        
        try:
            from mutagen import File
        except ImportError:
            missing_deps.append("mutagen")
        
        try:
            from PIL import Image
        except ImportError:
            missing_deps.append("Pillow")
        
        if missing_deps:
            QMessageBox.warning(
                self, 
                "缺少依赖", 
                f"未检测到以下库: {', '.join(missing_deps)}。\n"
                "视频导出功能将不可用。\n"
                f"请运行: pip install {' '.join(missing_deps)}"
            )
    
    def add_images(self):
        """添加图片文件"""
        formats = get_supported_image_formats()
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择图片文件", "", 
            f"图片文件 ({';'.join(['*' + ext for ext in formats])})"
        )
        
        if files:
            self.media_manager.add_images(files)
            self.status_label.setText(f"添加了 {len(files)} 个图片文件")
    
    def add_folder(self):
        """添加文件夹中的图片"""
        folder = QFileDialog.getExistingDirectory(self, "选择图片文件夹")
        if folder:
            self.media_manager.add_images_from_folder(folder)
            self.status_label.setText(f"添加了文件夹中的图片")
    
    def add_audio(self):
        """添加音频文件"""
        formats = get_supported_audio_formats()
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择音频文件", "", 
            f"音频文件 ({';'.join(['*' + ext for ext in formats])})"
        )
        
        if files:
            self.media_manager.add_audios(files)
            self.status_label.setText(f"添加了 {len(files)} 个音频文件")
    
    def sort_image_items(self):
        """排序图片项"""
        index = self.sort_combo.currentIndex()
        self.media_manager.sort_images(index)
    
    def update_image_list(self, images):
        """更新图片列表显示"""
        self.image_list.clear()
        for image in images:
            self.image_list.add_item(image.name, image.thumbnail, image.info)
    
    def update_audio_list(self, audios):
        """更新音频列表显示"""
        self.audio_list.clear()
        for audio in audios:
            self.audio_list.add_item(audio.name, None, audio.info)
    
    def update_timeline(self, images, audios):
        """更新时间轴显示"""
        self.timeline.clear()
        self.timeline.add_images(images)
        self.timeline.add_audios(audios)
    
    def export_video(self):
        """导出视频"""
        if not self.media_manager.images:
            QMessageBox.warning(self, "错误", "没有添加任何图片！")
            return
        
        # 检查 moviepy 是否可用
        try:
            from moviepy.editor import ImageSequenceClip
        except ImportError:
            QMessageBox.critical(self, "错误", "未安装moviepy库，无法导出视频！")
            return
        
        output_file, _ = QFileDialog.getSaveFileName(
            self, "保存视频", "", "MP4视频 (*.mp4);;所有文件 (*)"
        )
        
        if not output_file:
            return
        
        try:
            self.status_label.setText("正在导出视频...")
            self.status_indicator.set_status("导出中...", "#FFCC00")
            
            # 导出视频
            success = self.export_manager.export_video(
                self.media_manager.images, 
                self.media_manager.audios, 
                output_file,
                self.update_export_progress
            )
            
            if success:
                self.status_label.setText(f"视频已成功导出: {output_file}")
                self.status_indicator.set_status("导出完成", "#4EC9B0")
                QMessageBox.information(self, "完成", "视频导出成功！")
            else:
                self.status_label.setText("视频导出失败")
                self.status_indicator.set_status("导出失败", "#F44747")
                QMessageBox.critical(self, "错误", "视频导出失败")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出视频时出错:\n{str(e)}")
            self.status_label.setText("视频导出失败")
            self.status_indicator.set_status("导出失败", "#F44747")
    
    def update_export_progress(self, progress):
        """更新导出进度"""
        self.status_label.setText(f"正在导出视频... {progress}%")
        QApplication.processEvents()
    
    def clear_all(self):
        """清空所有内容"""
        reply = QMessageBox.question(
            self, "确认", 
            "确定要清空所有图片和音频吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.media_manager.clear_all()
            self.status_label.setText("已清空所有内容")
            self.status_indicator.set_status("就绪", "#4EC9B0")
    
    def dragEnterEvent(self, event):
        """拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        """拖放事件"""
        urls = event.mimeData().urls()
        files = []
        
        for url in urls:
            file_path = url.toLocalFile()
            if os.path.exists(file_path):
                files.append(file_path)
        
        if not files:
            return
        
        # 判断文件类型
        image_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')
        audio_extensions = ('.mp3', '.wav', '.ogg', '.flac')
        
        image_files = [f for f in files if f.lower().endswith(image_extensions)]
        audio_files = [f for f in files if f.lower().endswith(audio_extensions)]
        
        if image_files:
            self.media_manager.add_images(image_files)
        
        if audio_files:
            self.media_manager.add_audios(audio_files)
        
        event.acceptProposedAction()