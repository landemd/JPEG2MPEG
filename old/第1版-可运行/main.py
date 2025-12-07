import sys
import os
import time
from datetime import datetime
from PIL import Image, ImageQt
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QLabel, QListWidget, QListWidgetItem, QFileDialog,
                            QComboBox, QSlider, QSplitter, QMessageBox, QAction, QMenu, 
                            QAbstractItemView, QGraphicsView, QGraphicsScene, QGraphicsRectItem,
                            QGraphicsItem, QToolBar, QStatusBar, QInputDialog, QSizePolicy)
from PyQt5.QtCore import Qt, QSize, QRectF, QPointF, QMimeData
from PyQt5.QtGui import QPixmap, QIcon, QDrag, QPainter, QColor, QPen, QBrush, QFont

# 尝试导入必要的库
try:
    from moviepy.editor import ImageSequenceClip, AudioFileClip, concatenate_videoclips
    from pydub import AudioSegment
    PYTHON_DEPS_INSTALLED = True
except ImportError:
    PYTHON_DEPS_INSTALLED = False

class DraggableListWidget(QListWidget):
    """支持拖拽排序的列表控件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setStyleSheet("""
            QListWidget {
                background-color: #2D2D30;
                border: 1px solid #3F3F46;
                border-radius: 4px;
                color: #DCDCDC;
            }
            QListWidget::item {
                background-color: #3E3E42;
                border: 1px solid #3F3F46;
                padding: 5px;
                margin: 2px;
            }
            QListWidget::item:selected {
                background-color: #007ACC;
                color: white;
            }
        """)
    
    def startDrag(self, supportedActions):
        item = self.currentItem()
        if not item:
            return
            
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(item.text())
        drag.setMimeData(mime_data)
        
        pixmap = QPixmap(item.sizeHint())
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(Qt.white, 2))
        painter.setBrush(QBrush(QColor(62, 62, 66, 200)))
        painter.drawRoundedRect(pixmap.rect().adjusted(0, 0, -1, -1), 5, 5)
        painter.end()
        
        drag.setPixmap(pixmap)
        drag.exec_(supportedActions)

class TimelineWidget(QGraphicsView):
    """时间轴控件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setBackgroundBrush(QBrush(QColor("#1E1E1E")))
        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setMinimumHeight(150)
        self.items = []
        
        # 绘制时间刻度
        self.draw_time_ruler()
    
    def draw_time_ruler(self):
        """绘制时间刻度尺"""
        self.scene.clear()
        pen = QPen(QColor("#3F3F46"), 1)
        font = QFont("Arial", 8)
        
        # 绘制背景
        bg_rect = QGraphicsRectItem(0, 0, 1000, 40)
        bg_rect.setBrush(QBrush(QColor("#252526")))
        bg_rect.setPen(pen)
        self.scene.addItem(bg_rect)
        
        # 绘制刻度
        for i in range(0, 1000, 50):
            line = self.scene.addLine(i, 0, i, 15, pen)
            text = self.scene.addText(str(i//10), font)
            text.setPos(i-5, 15)
            text.setDefaultTextColor(QColor("#D4D4D4"))
        
        self.time_items_start_y = 45
    
    def add_image_item(self, name, duration=3, position=0):
        """添加图片项到时间轴"""
        width = duration * 20  # 每1秒对应20像素宽度
        height = 60
        y_pos = self.time_items_start_y + 10
        
        # 创建图形项
        item = QGraphicsRectItem(position, y_pos, width, height)
        item.setBrush(QBrush(QColor("#007ACC")))
        item.setPen(QPen(QColor("#005A9E"), 1))
        item.setData(0, name)  # 存储文件名
        item.setFlag(QGraphicsItem.ItemIsMovable)
        item.setFlag(QGraphicsItem.ItemIsSelectable)
        
        # 添加标签
        text = self.scene.addText(name[:20], QFont("Arial", 8))
        text.setPos(position + 5, y_pos + 5)
        text.setDefaultTextColor(Qt.white)
        
        self.scene.addItem(item)
        self.items.append((item, text))
        return item
    
    def add_audio_item(self, name, start_time=0, duration=10):
        """添加音频项到时间轴"""
        width = duration * 20  # 每1秒对应20像素宽度
        height = 40
        y_pos = self.time_items_start_y + 80
        
        # 创建图形项
        item = QGraphicsRectItem(start_time * 20, y_pos, width, height)
        item.setBrush(QBrush(QColor("#68217A")))
        item.setPen(QPen(QColor("#4B124F"), 1))
        item.setData(0, name)  # 存储文件名
        item.setFlag(QGraphicsItem.ItemIsMovable)
        item.setFlag(QGraphicsItem.ItemIsSelectable)
        
        # 添加标签
        text = self.scene.addText(name[:20], QFont("Arial", 8))
        text.setPos(start_time * 20 + 5, y_pos + 5)
        text.setDefaultTextColor(Qt.white)
        
        self.scene.addItem(item)
        self.items.append((item, text))
        return item
    
    def clear_items(self):
        """清除所有项目"""
        for item, text in self.items:
            self.scene.removeItem(item)
            self.scene.removeItem(text)
        self.items = []
        self.draw_time_ruler()

class MediaItem:
    """媒体项基类"""
    def __init__(self, path):
        self.path = path
        self.name = os.path.basename(path)
        self.created_time = os.path.getctime(path)
        self.modified_time = os.path.getmtime(path)
        self.size = os.path.getsize(path)
    
    def get_info(self):
        """获取媒体项信息"""
        return f"{self.name}\n大小: {self.size//1024} KB\n修改时间: {datetime.fromtimestamp(self.modified_time).strftime('%Y-%m-%d %H:%M')}"

class ImageItem(MediaItem):
    """图片项"""
    def __init__(self, path):
        super().__init__(path)
        try:
            with Image.open(path) as img:
                self.width, self.height = img.size
        except:
            self.width, self.height = 0, 0
    
    def get_info(self):
        base_info = super().get_info()
        return f"图片: {base_info}\n尺寸: {self.width}x{self.height}"

class AudioItem(MediaItem):
    """音频项"""
    def __init__(self, path):
        super().__init__(path)
        try:
            audio = AudioSegment.from_file(path)
            self.duration = len(audio) / 1000.0  # 转换为秒
        except:
            self.duration = 0
    
    def get_info(self):
        base_info = super().get_info()
        return f"音频: {base_info}\n时长: {self.duration:.1f}秒"

class MediaManagerApp(QMainWindow):
    """主应用程序窗口"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("媒体合成工具 - 图片与声音转视频")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(900, 600)
        
        # 初始化数据
        self.image_items = []  # 存储ImageItem对象
        self.audio_items = []  # 存储AudioItem对象
        self.video_duration = 0
        
        # 设置UI
        self.init_ui()
        
        # 检查依赖
        if not PYTHON_DEPS_INSTALLED:
            QMessageBox.warning(self, "缺少依赖", 
                               "未检测到moviepy或pydub库。视频导出功能将不可用。\n"
                               "请运行: pip install moviepy pydub pillow")
    
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
        image_group = QWidget()
        image_layout = QVBoxLayout(image_group)
        image_layout.addWidget(QLabel("图片文件"))
        
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["按创建时间", "按文件名", "按文件大小"])
        self.sort_combo.currentIndexChanged.connect(self.sort_image_items)
        image_layout.addWidget(self.sort_combo)
        
        self.image_list = DraggableListWidget()
        self.image_list.itemDoubleClicked.connect(self.show_image_preview)
        image_layout.addWidget(self.image_list)
        
        # 音频管理区域
        audio_group = QWidget()
        audio_layout = QVBoxLayout(audio_group)
        audio_layout.addWidget(QLabel("音频文件"))
        
        self.audio_list = DraggableListWidget()
        self.audio_list.itemDoubleClicked.connect(self.show_audio_info)
        audio_layout.addWidget(self.audio_list)
        
        # 添加到媒体布局
        media_layout.addWidget(image_group, 1)
        media_layout.addWidget(audio_group, 1)
        
        # 创建时间轴区域
        timeline_group = QWidget()
        timeline_layout = QVBoxLayout(timeline_group)
        timeline_layout.addWidget(QLabel("时间轴"))
        
        self.timeline = TimelineWidget()
        timeline_layout.addWidget(self.timeline)
        
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
        
        # 创建菜单
        self.create_menu()
    
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
    
    def create_menu(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        
        add_images_menu = file_menu.addMenu("添加图片")
        add_images_menu.addAction("单张图片", self.add_images)
        add_images_menu.addAction("整个文件夹", self.add_folder)
        
        add_audio_menu = file_menu.addMenu("添加音频")
        add_audio_menu.addAction("单个音频", self.add_audio)
        add_audio_menu.addAction("整个文件夹", lambda: self.add_audio(folder=True))
        
        file_menu.addSeparator()
        file_menu.addAction("导出视频", self.export_video)
        file_menu.addAction("退出", self.close)
        
        # 编辑菜单
        edit_menu = menubar.addMenu("编辑")
        edit_menu.addAction("清空所有", self.clear_all)
        edit_menu.addAction("排序方式", self.sort_image_items)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助")
        help_menu.addAction("关于", self.show_about)
    
    def add_images(self):
        """添加图片文件"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择图片文件", "", 
            "图片文件 (*.jpg *.jpeg *.png *.bmp *.gif)"
        )
        
        if files:
            self.process_added_files(files, is_image=True)
    
    def add_folder(self):
        """添加文件夹中的图片"""
        folder = QFileDialog.getExistingDirectory(self, "选择图片文件夹")
        if folder:
            files = []
            for file in os.listdir(folder):
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                    files.append(os.path.join(folder, file))
            
            if files:
                self.process_added_files(files, is_image=True)
    
    def add_audio(self, folder=False):
        """添加音频文件"""
        if folder:
            folder = QFileDialog.getExistingDirectory(self, "选择音频文件夹")
            if folder:
                files = []
                for file in os.listdir(folder):
                    if file.lower().endswith(('.mp3', '.wav', '.ogg', '.flac')):
                        files.append(os.path.join(folder, file))
                
                if files:
                    self.process_added_files(files, is_image=False)
        else:
            files, _ = QFileDialog.getOpenFileNames(
                self, "选择音频文件", "", 
                "音频文件 (*.mp3 *.wav *.ogg *.flac)"
            )
            
            if files:
                self.process_added_files(files, is_image=False)
    
    def process_added_files(self, files, is_image=True):
        """处理添加的文件"""
        if is_image:
            for file in files:
                if any(item.path == file for item in self.image_items):
                    continue
                    
                try:
                    item = ImageItem(file)
                    self.image_items.append(item)
                    
                    # 添加到列表控件
                    list_item = QListWidgetItem()
                    list_item.setText(item.name)
                    list_item.setToolTip(item.get_info())
                    
                    # 生成缩略图
                    thumbnail = self.generate_thumbnail(file)
                    list_item.setIcon(QIcon(thumbnail))
                    list_item.setSizeHint(QSize(120, 120))
                    
                    self.image_list.addItem(list_item)
                except Exception as e:
                    QMessageBox.warning(self, "错误", f"无法加载图片: {file}\n{str(e)}")
            
            self.update_timeline()
            self.status_label.setText(f"添加了 {len(files)} 个图片文件")
        else:
            for file in files:
                if any(item.path == file for item in self.audio_items):
                    continue
                    
                try:
                    item = AudioItem(file)
                    self.audio_items.append(item)
                    
                    # 添加到列表控件
                    list_item = QListWidgetItem()
                    list_item.setText(item.name)
                    list_item.setToolTip(item.get_info())
                    self.audio_list.addItem(list_item)
                except Exception as e:
                    QMessageBox.warning(self, "错误", f"无法加载音频: {file}\n{str(e)}")
            
            self.update_timeline()
            self.status_label.setText(f"添加了 {len(files)} 个音频文件")
    
    def generate_thumbnail(self, image_path, size=(100, 100)):
        """生成缩略图"""
        try:
            img = Image.open(image_path)
            img.thumbnail(size)
            return QPixmap.fromImage(ImageQt.ImageQt(img))
        except:
            # 返回默认图标
            pixmap = QPixmap(size[0], size[1])
            pixmap.fill(Qt.lightGray)
            painter = QPainter(pixmap)
            painter.setPen(Qt.black)
            painter.drawText(pixmap.rect(), Qt.AlignCenter, "No Preview")
            painter.end()
            return pixmap
    
    def sort_image_items(self):
        """排序图片项"""
        index = self.sort_combo.currentIndex()
        
        if index == 0:  # 按创建时间
            self.image_items.sort(key=lambda x: x.created_time)
        elif index == 1:  # 按文件名
            self.image_items.sort(key=lambda x: x.name.lower())
        elif index == 2:  # 按文件大小
            self.image_items.sort(key=lambda x: x.size)
        
        # 更新列表显示
        self.image_list.clear()
        for item in self.image_items:
            list_item = QListWidgetItem()
            list_item.setText(item.name)
            list_item.setToolTip(item.get_info())
            
            thumbnail = self.generate_thumbnail(item.path)
            list_item.setIcon(QIcon(thumbnail))
            list_item.setSizeHint(QSize(120, 120))
            
            self.image_list.addItem(list_item)
        
        self.update_timeline()
    
    def update_timeline(self):
        """更新时间轴显示"""
        self.timeline.clear_items()
        
        # 添加图片项
        position = 0
        for item in self.image_items:
            # 默认每张图片显示3秒
            self.timeline.add_image_item(item.name, duration=3, position=position)
            position += 3 * 20  # 20像素/秒
        
        # 添加音频项
        audio_start = 0
        for item in self.audio_items:
            self.timeline.add_audio_item(item.name, start_time=audio_start, duration=item.duration)
            audio_start += item.duration
    
    def show_image_preview(self, item):
        """显示图片预览"""
        row = self.image_list.row(item)
        if 0 <= row < len(self.image_items):
            img_item = self.image_items[row]
            pixmap = QPixmap(img_item.path)
            if not pixmap.isNull():
                dialog = QMessageBox(self)
                dialog.setWindowTitle("图片预览")
                dialog.setText(img_item.name)
                
                # 缩放图片以适应对话框
                max_size = 400
                if pixmap.width() > max_size or pixmap.height() > max_size:
                    pixmap = pixmap.scaled(max_size, max_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                
                label = QLabel()
                label.setPixmap(pixmap)
                dialog.layout().addWidget(label, 1, 0, 1, dialog.layout().columnCount())
                dialog.exec_()
    
    def show_audio_info(self, item):
        """显示音频信息"""
        row = self.audio_list.row(item)
        if 0 <= row < len(self.audio_items):
            audio_item = self.audio_items[row]
            QMessageBox.information(self, "音频信息", audio_item.get_info())
    
    def export_video(self):
        """导出视频"""
        if not self.image_items:
            QMessageBox.warning(self, "错误", "没有添加任何图片！")
            return
        
        if not PYTHON_DEPS_INSTALLED:
            QMessageBox.critical(self, "错误", "未安装必要的依赖库！")
            return
        
        output_file, _ = QFileDialog.getSaveFileName(
            self, "保存视频", "", "MP4视频 (*.mp4);;所有文件 (*)"
        )
        
        if not output_file:
            return
        
        try:
            # 准备图片序列
            image_paths = [item.path for item in self.image_items]
            durations = [3] * len(image_paths)  # 每张图片默认3秒
            
            # 创建视频剪辑
            video_clip = ImageSequenceClip(image_paths, durations=durations)
            
            # 添加音频（如果有）
            if self.audio_items:
                audio_clips = []
                for item in self.audio_items:
                    audio_clip = AudioFileClip(item.path)
                    audio_clips.append(audio_clip)
                
                # 合并所有音频
                final_audio = concatenate_videoclips(audio_clips)
                
                # 如果音频比视频长，截取视频长度
                if final_audio.duration > video_clip.duration:
                    final_audio = final_audio.subclip(0, video_clip.duration)
                # 如果音频比视频短，循环音频
                else:
                    final_audio = final_audio.loop(duration=video_clip.duration)
                
                video_clip = video_clip.set_audio(final_audio)
            
            # 导出视频
            self.status_label.setText("正在导出视频...")
            QApplication.processEvents()  # 更新UI
            
            video_clip.write_videofile(output_file, fps=24, codec='libx264')
            
            self.status_label.setText(f"视频已成功导出: {output_file}")
            QMessageBox.information(self, "完成", "视频导出成功！")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出视频时出错:\n{str(e)}")
            self.status_label.setText("视频导出失败")
    
    def clear_all(self):
        """清空所有内容"""
        reply = QMessageBox.question(
            self, "确认", 
            "确定要清空所有图片和音频吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.image_items = []
            self.audio_items = []
            self.image_list.clear()
            self.audio_list.clear()
            self.timeline.clear_items()
            self.status_label.setText("已清空所有内容")
    
    def show_about(self):
        """显示关于对话框"""
        about_text = """
        <h2>媒体合成工具</h2>
        <p>版本: 1.0</p>
        <p>功能:</p>
        <ul>
            <li>添加图片文件（单张、文件夹、拖拽）</li>
            <li>添加音频文件（单个、文件夹、拖拽）</li>
            <li>管理媒体顺序和时间</li>
            <li>导出为视频文件</li>
        </ul>
        <p>技术支持: Python 3, PyQt5, Pillow, MoviePy, PyDub</p>
        """
        QMessageBox.about(self, "关于", about_text)
    
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
            self.process_added_files(image_files, is_image=True)
        
        if audio_files:
            self.process_added_files(audio_files, is_image=False)
        
        event.acceptProposedAction()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 设置应用样式
    app.setStyle("Fusion")
    app.setStyleSheet("""
        QMainWindow {
            background-color: #1E1E1E;
            color: #D4D4D4;
        }
        QWidget {
            background-color: #1E1E1E;
            color: #D4D4D4;
        }
        QToolBar {
            background-color: #333337;
            border: none;
        }
        QStatusBar {
            background-color: #333337;
            color: #D4D4D4;
        }
        QComboBox {
            background-color: #3E3E42;
            color: #D4D4D4;
            border: 1px solid #3F3F46;
            padding: 3px;
        }
        QLabel {
            color: #D4D4D4;
        }
        QGroupBox {
            color: #D4D4D4;
            border: 1px solid #3F3F46;
            border-radius: 4px;
            margin-top: 1ex;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 3px;
        }
    """)
    
    window = MediaManagerApp()
    window.show()
    sys.exit(app.exec_())
