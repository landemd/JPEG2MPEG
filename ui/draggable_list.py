from PyQt5.QtWidgets import QListWidget, QListWidgetItem, QAbstractItemView
from PyQt5.QtCore import Qt, pyqtSignal, QMimeData
from PyQt5.QtGui import QDrag, QPixmap, QPainter, QColor


class DraggableList(QListWidget):
    """可拖拽并支持内部重排的列表（用于图片/音频区）。

    提供 `item_moved(old_index, new_index)` 信号。
    """
    item_moved = pyqtSignal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFlow(QListWidget.LeftToRight)
        self.setWrapping(True)
        self.setResizeMode(QListWidget.Adjust)
        self.setSpacing(10)
        self.setViewMode(QListWidget.IconMode)
        self.setIconSize(self.iconSize())
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setSelectionMode(QListWidget.SingleSelection)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setAutoScroll(True)

    def dropEvent(self, event):
        """处理内部拖拽移动并发出 item_moved 信号。"""
        source_row = self.currentRow()
        super().dropEvent(event)
        new_row = self.currentRow()
        if source_row != new_row and source_row >= 0:
            self.item_moved.emit(source_row, new_row)

    def startDrag(self, supportedActions):
        item = self.currentItem()
        if item is None:
            return
        # 尝试取出 item 对应的 widget 中的缩略图
        widget = self.itemWidget(item)
        pix = None
        if widget is not None:
            lbls = widget.findChildren(type(widget))
        # fallback to icon
        if item.icon() and not item.icon().isNull():
            pix = item.icon().pixmap(100, 100)
        if pix is None:
            pix = QPixmap(100, 100)
            pix.fill(Qt.lightGray)

        drag = QDrag(self)
        mime = QMimeData()
        mime.setText(item.text() if item.text() else '')
        drag.setMimeData(mime)

        preview = pix.copy()
        painter = QPainter(preview)
        painter.fillRect(preview.rect(), QColor(0, 0, 0, 120))
        painter.end()
        drag.setPixmap(preview)
        drag.setHotSpot(preview.rect().center())
        drag.exec_(supportedActions)

