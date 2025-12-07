from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsTextItem
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QColor, QBrush, QPen, QFont, QPainter

class TimelineWidget(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setBackgroundBrush(QColor("#1E1E1E"))
        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setMinimumHeight(150)
        
        # 绘制时间刻度
        self.draw_time_ruler()
        self.items = []
    
    def draw_time_ruler(self):
        """绘制时间刻度尺"""
        self.scene.clear()
        pen = QPen(QColor("#3F3F46"), 1)
        font = QFont("Arial", 8)
        
        # 绘制背景
        bg_rect = self.scene.addRect(0, 0, 1000, 40, pen, QBrush(QColor("#252526")))
        
        # 绘制刻度
        for i in range(0, 1000, 50):
            line = self.scene.addLine(i, 0, i, 15, pen)
            text = QGraphicsTextItem(str(i//10))
            text.setFont(font)
            text.setDefaultTextColor(QColor("#D4D4D4"))
            text.setPos(i-5, 15)
            self.scene.addItem(text)
        
        self.time_items_start_y = 45
    
    def add_images(self, images):
        """添加图片到时间轴"""
        y_pos = self.time_items_start_y + 10
        position = 0
        
        for image in images:
            duration = image.duration
            width = duration * 20  # 每1秒对应20像素宽度
            height = 60
            
            # 创建图形项
            item = QGraphicsRectItem(position, y_pos, width, height)
            item.setBrush(QBrush(QColor("#007ACC")))
            item.setPen(QPen(QColor("#005A9E"), 1))
            item.setFlag(QGraphicsRectItem.ItemIsMovable)
            item.setFlag(QGraphicsRectItem.ItemIsSelectable)
            
            # 添加标签
            text = QGraphicsTextItem(image.name[:20])
            text.setFont(QFont("Arial", 8))
            text.setDefaultTextColor(Qt.white)
            text.setPos(position + 5, y_pos + 5)
            self.scene.addItem(text)
            
            self.scene.addItem(item)
            self.items.append((item, text))
            
            position += width
    
    def add_audios(self, audios):
        """添加音频到时间轴"""
        y_pos = self.time_items_start_y + 80
        position = 0
        
        for audio in audios:
            duration = audio.duration
            width = duration * 20  # 每1秒对应20像素宽度
            height = 40
            
            # 创建图形项
            item = QGraphicsRectItem(position, y_pos, width, height)
            item.setBrush(QBrush(QColor("#68217A")))
            item.setPen(QPen(QColor("#4B124F"), 1))
            item.setFlag(QGraphicsRectItem.ItemIsMovable)
            item.setFlag(QGraphicsRectItem.ItemIsSelectable)
            
            # 添加标签
            text = QGraphicsTextItem(audio.name[:20])
            text.setFont(QFont("Arial", 8))
            text.setDefaultTextColor(Qt.white)
            text.setPos(position + 5, y_pos + 5)
            self.scene.addItem(text)
            
            self.scene.addItem(item)
            self.items.append((item, text))
            
            position += width
    
    def clear(self):
        """清除所有项目"""
        self.scene.clear()
        self.draw_time_ruler()
        self.items = []