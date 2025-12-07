from PyQt5.QtWidgets import QListWidget, QListWidgetItem, QAbstractItemView
from PyQt5.QtCore import Qt, QSize, QMimeData
from PyQt5.QtGui import QPixmap, QIcon, QDrag, QPainter, QColor, QPen, QBrush

class DraggableListWidget(QListWidget):
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
    
    def add_item(self, name, thumbnail, info):
        """添加项目到列表"""
        item = QListWidgetItem()
        item.setText(name)
        item.setToolTip(info)
        
        if thumbnail:
            item.setIcon(QIcon(thumbnail))
        
        item.setSizeHint(QSize(120, 120))
        self.addItem(item)
    
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