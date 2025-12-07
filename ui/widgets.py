from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QComboBox, QListWidget, QListWidgetItem, QProgressBar)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap

from utils.image_utils import generate_thumbnail


class CardWidget(QWidget):
    """带标题的卡片组件（圆角、深色背景）。支持在右上放置控件（如排序下拉）。"""
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QWidget { border:1px solid #333; border-radius:8px; background-color:#252526 }
            QWidget:hover { border:1px solid #007ACC }
        """)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)

        # header: left=two-line title, right=optional controls
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)

        title_widget = QWidget()
        title_layout = QVBoxLayout(title_widget)
        title_layout.setContentsMargins(0, 0, 0, 0)
        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.title_label.setStyleSheet('color:#D4D4D4; font-weight:bold')
        title_layout.addWidget(self.title_label)

        header_layout.addWidget(title_widget, stretch=1)
        # placeholder for right-side widgets (e.g., sort combo)
        self.header_right = QWidget()
        self.header_right.setLayout(QHBoxLayout())
        self.header_right.layout().setContentsMargins(0, 0, 0, 0)
        header_layout.addWidget(self.header_right, 0, Qt.AlignRight)

        outer.addWidget(header)

        self._content_layout = QVBoxLayout()
        self._content_layout.setContentsMargins(0, 6, 0, 0)
        outer.addLayout(self._content_layout)

    def content_layout(self):
        return self._content_layout

    def set_header_widget(self, widget):
        """将一个控件放到右上角（例如排序下拉）。"""
        # 清除旧的占位
        layout = self.header_right.layout()
        while layout.count():
            it = layout.takeAt(0)
            if it.widget():
                it.widget().setParent(None)
        layout.addWidget(widget)


class SortComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.addItems(["按修改日期", "按文件名", "按文件大小"])
        self.setStyleSheet("""
            QComboBox { background-color: #252526; color: #D4D4D4; border:1px solid #333; border-radius:4px; padding:2px }
            QComboBox:hover { border:1px solid #007ACC }
        """)


class DraggableList(QListWidget):
    """通用可显示缩略图的可拖拽列表（图片/音频）。"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFlow(QListWidget.LeftToRight)
        self.setWrapping(False)  # 禁止自动换行，单行显示
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setResizeMode(QListWidget.Adjust)
        self.setSpacing(10)
        self.setViewMode(QListWidget.IconMode)
        self.setIconSize(QSize(100, 100))
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setSelectionMode(QListWidget.SingleSelection)
        self.setStyleSheet("""
            QListWidget { background-color:#252526; border:1px solid #333; border-radius:4px }
            QListWidget::item { padding:5px }
            QListWidget::item:selected { background-color:#007ACC; }
        """)

    def add_media_item(self, image_path: str, title: str, subtitle: str, seq_num: int = None):
        """向列表添加一项，文件名在缩略图上方，修改日期在下方。
        可选参数 `seq_num` 用于在缩略图上方显示序列号（从1开始）。"""
        item = QListWidgetItem()
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(4, 4, 4, 4)

        # 文件名（上方）
        title_label = QLabel(title)
        title_label.setStyleSheet('color:#D4D4D4; font-weight:bold; font-size:12px')
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFixedWidth(100)
        title_label.setWordWrap(True)
        title_label.setMaximumHeight(32)  # 限制最大高度，避免过长撑开
        title_label.setToolTip(title)
        title_label.setContextMenuPolicy(Qt.CustomContextMenu)
        def make_menu(label):
            def on_context(pos):
                menu = label.createStandardContextMenu()
                menu.addSeparator()
                copy_act = menu.addAction('复制文本')
                def copy_text():
                    from PyQt5.QtWidgets import QApplication
                    QApplication.clipboard().setText(label.text())
                copy_act.triggered.connect(copy_text)
                menu.exec_(label.mapToGlobal(pos))
            return on_context
        title_label.customContextMenuRequested.connect(make_menu(title_label))
        layout.addWidget(title_label)

        # 缩略图（中间）
        icon_label = QLabel()
        icon_label.setFixedSize(100, 100)
        icon_label.setAlignment(Qt.AlignCenter)
        if image_path:
            try:
                pix = generate_thumbnail(image_path)
                icon_label.setPixmap(pix.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            except Exception:
                icon_label.setStyleSheet('background-color: lightgray')
        else:
            icon_label.setStyleSheet('background-color: lightgray')
        layout.addWidget(icon_label, alignment=Qt.AlignCenter)

            # 序号（可选，在缩略图下方）
        if seq_num is not None:
            seq_label = QLabel(f"#{int(seq_num)}")
            seq_label.setStyleSheet('color:#CCCCCC; font-size:11px;')
            seq_label.setAlignment(Qt.AlignCenter)
            seq_label.setFixedWidth(100)
            layout.addWidget(seq_label)


        # 修改日期（下方，格式化）
        import time
        try:
            # subtitle 传入的是修改日期的原始秒数或字符串
            ts = float(subtitle) if subtitle else None
        except Exception:
            ts = None
        if ts:
            tstruct = time.localtime(ts)
            time_str = time.strftime('%S:%M:%H %d-%m-%y', tstruct)
        else:
            time_str = ''
        subtitle_label = QLabel(time_str)
        subtitle_label.setStyleSheet('color:#AAAAAA; font-size:10px')
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setFixedWidth(100)
        subtitle_label.setWordWrap(False)
        subtitle_label.setToolTip(time_str)
        subtitle_label.setContextMenuPolicy(Qt.CustomContextMenu)
        subtitle_label.customContextMenuRequested.connect(make_menu(subtitle_label))
        layout.addWidget(subtitle_label)

        item.setSizeHint(container.sizeHint())
        self.addItem(item)
        self.setItemWidget(item, container)


class StatusbarWithProgress(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 0, 4, 0)
        self.label = QLabel("就绪")
        self.label.setStyleSheet("color:#D4D4D4")
        layout.addWidget(self.label)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet("QProgressBar{background:#252526;border:1px solid #333;border-radius:4px} QProgressBar::chunk{background:#007ACC}")
        self.progress.hide()
        layout.addWidget(self.progress)

    def showMessage(self, msg: str):
        self.label.setText(msg)
        self.progress.hide()

    def set_status(self, status: str):
        """设置状态颜色：'ready'|'working'|'error'"""
        if status == 'ready':
            color = '#00C853'  # green
        elif status == 'working':
            color = '#FFB300'  # yellow
        elif status == 'error':
            color = '#D32F2F'  # red
        else:
            color = '#D4D4D4'
        self.label.setStyleSheet(f'color: {color}')

    def showProgress(self, value: int):
        self.progress.setValue(value)
        self.progress.show()
