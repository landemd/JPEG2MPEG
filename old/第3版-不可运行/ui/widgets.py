from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QSizePolicy, QSpacerItem, QGraphicsView, QGraphicsScene
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QIcon, QColor, QPalette, QPainter, QBrush, QPen

class CardWidget(QFrame):
    """卡片式容器组件"""
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setStyleSheet("""
            CardWidget {
                background-color: #252526;
                border: 1px solid #3F3F46;
                border-radius: 8px;
            }
            CardWidget:hover {
                border: 1px solid #007ACC;
            }
        """)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(8)
        
        if title:
            title_label = QLabel(title)
            title_label.setStyleSheet("""
                QLabel {
                    color: #D4D4D4;
                    font-weight: bold;
                    font-size: 14px;
                    border-bottom: 1px solid #3F3F46;
                    padding-bottom: 5px;
                }
            """)
            title_label.setAlignment(Qt.AlignLeft)
            self.layout.addWidget(title_label)

class StatusIndicator(QWidget):
    """状态指示器组件"""
    def __init__(self, status="就绪", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        
        self.indicator = QLabel()
        self.indicator.setFixedSize(12, 12)
        self.indicator.setStyleSheet("background-color: #4EC9B0; border-radius: 6px;")
        
        self.label = QLabel(status)
        self.label.setStyleSheet("color: #D4D4D4; font-size: 12px;")
        
        layout.addWidget(self.indicator)
        layout.addWidget(self.label)
        layout.addStretch()
    
    def set_status(self, status, color="#4EC9B0"):
        """更新状态"""
        self.label.setText(status)
        self.indicator.setStyleSheet(f"background-color: {color}; border-radius: 6px;")