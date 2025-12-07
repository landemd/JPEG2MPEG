from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter, 
    QToolBar, QStatusBar, QLabel, QFileDialog, QMessageBox, QAction,
    QComboBox, QApplication
)
from PyQt5.QtCore import Qt, QSize, QObject, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QPen, QBrush

from .timeline_widget import TimelineWidget
from .draggable_list import DraggableListWidget
from .widgets import CardWidget, IconButton, StatusIndicator
from ..core.media_manager import MediaManager
from ..core.export_manager import ExportManager
from ..utils.file_utils import get_supported_image_formats, get_supported_audio_formats

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
        image_layout.addWidget(self.image_list)
        
        # 音频管理区域
        audio_group = CardWidget("音频文件")
        audio_layout = QVBoxLayout(audio_group)
        self.audio_list = DraggableListWidget()
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
        add_images_action = QAction(QIcon(), "添加图片", self)
        add_images_action.triggered.connect(self.add_images)
        toolbar.addAction(add_images_action)
        
        # 添加文件夹按钮
        add_folder_action = QAction(QIcon(), "添加文件夹", self)
        add_folder_action.triggered.connect(self.add_folder)
        toolbar.addAction(add_folder_action)
        
        toolbar.addSeparator()
        
        # 添加音频按钮
        add_audio_action = QAction(QIcon(), "添加音频", self)
        add_audio_action.triggered.connect(self.add_audio)
        toolbar.addAction(add_audio_action)
        
        toolbar.addSeparator()
        
        # 导出视频按钮
        export_action = QAction(QIcon(), "导出视频", self)
        export_action.triggered.connect(self.export_video)
        toolbar.addAction(export_action)
        
        # 清空按钮
        clear_action = QAction(QIcon(), "清空所有", self)
        clear_action.triggered.connect(self.clear_all)
        toolbar.addAction(clear_action)
    
    def init_connections(self):
        """初始化信号连接"""
        # 这里简化处理，实际项目中应使用信号槽机制
        pass
    
    def check_dependencies(self):
        """检查依赖库是否安装"""
        missing_deps = []
        try:
            import moviepy.editor
        except ImportError:
            missing_deps.append("moviepy")
        
        try:
            from pydub import AudioSegment
        except ImportError:
            missing_deps.append("pydub")
        
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
            self.status_label.setText(f"添加了 {len(files)} 个图片文件")
            # 简化处理，实际项目中应调用media_manager
            for file in files:
                self.image_list.add_item(os.path.basename(file), None, file)
    
    def add_folder(self):
        """添加文件夹中的图片"""
        folder = QFileDialog.getExistingDirectory(self, "选择图片文件夹")
        if folder:
            # 简化处理，实际项目中应调用media_manager
            files = []
            for file in os.listdir(folder):
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                    files.append(os.path.join(folder, file))
            
            if files:
                self.status_label.setText(f"添加了 {len(files)} 个图片文件")
                for file in files:
                    self.image_list.add_item(os.path.basename(file), None, file)
    
    def add_audio(self):
        """添加音频文件"""
        formats = get_supported_audio_formats()
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择音频文件", "", 
            f"音频文件 ({';'.join(['*' + ext for ext in formats])})"
        )
        
        if files:
            self.status_label.setText(f"添加了 {len(files)} 个音频文件")
            # 简化处理，实际项目中应调用media_manager
            for file in files:
                self.audio_list.add_item(os.path.basename(file), None, file)
    
    def sort_image_items(self):
        """排序图片项"""
        # 简化处理，实际项目中应调用media_manager
        index = self.sort_combo.currentIndex()
        items = []
        for i in range(self.image_list.count()):
            items.append(self.image_list.item(i))
        
        if index == 0:  # 按创建时间
            items.sort(key=lambda x: os.path.getctime(x.toolTip()))
        elif index == 1:  # 按文件名
            items.sort(key=lambda x: x.text().lower())
        elif index == 2:  # 按文件大小
            items.sort(key=lambda x: os.path.getsize(x.toolTip()))
        
        self.image_list.clear()
        for item in items:
            self.image_list.addItem(item)
    
    def export_video(self):
        """导出视频"""
        if self.image_list.count() == 0:
            QMessageBox.warning(self, "错误", "没有添加任何图片！")
            return
        
        output_file, _ = QFileDialog.getSaveFileName(
            self, "保存视频", "", "MP4视频 (*.mp4);;所有文件 (*)"
        )
        
        if not output_file:
            return
        
        try:
            self.status_label.setText("正在导出视频...")
            self.status_indicator.set_status("导出中...", "#FFCC00")
            
            # 简化处理，实际项目中应调用export_manager
            image_paths = []
            for i in range(self.image_list.count()):
                image_paths.append(self.image_list.item(i).toolTip())
            
            # 创建视频
            clips = []
            for img_path in image_paths:
                clip = ImageClip(img_path).set_duration(3)
                clips.append(clip)
            
            video = concatenate_videoclips(clips)
            video.write_videofile(output_file, fps=24)
            
            self.status_label.setText(f"视频已成功导出: {output_file}")
            self.status_indicator.set_status("导出完成", "#4EC9B0")
            QMessageBox.information(self, "完成", "视频导出成功！")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出视频时出错:\n{str(e)}")
            self.status_label.setText("视频导出失败")
            self.status_indicator.set_status("导出失败", "#F44747")
    
    def clear_all(self):
        """清空所有内容"""
        reply = QMessageBox.question(
            self, "确认", 
            "确定要清空所有图片和音频吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.image_list.clear()
            self.audio_list.clear()
            self.timeline.clear()
            self.status_label.setText("已清空所有内容")
            self.status_indicator.set_status("就绪", "#4EC9B0")