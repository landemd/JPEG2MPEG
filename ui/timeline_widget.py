from PyQt5.QtWidgets import QScrollArea, QWidget
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QPainter, QFont, QPen, QColor, QPixmap


class _TimelineContent(QWidget):
    image_moved = pyqtSignal(int, float)
    image_reordered = pyqtSignal(list)  # emits new order as list of original indices
    def __init__(self, parent=None):
        super().__init__(parent)
        self.duration = 0.0  # seconds (audio total length)
        self.px_per_second = 1  # 10s -> 10px => 1 px per second
        self.images = []  # list of dicts: {pixmap, time, index}
        self.selected_index = -1
        # dragging state
        self._dragging_index = -1
        self._drag_start_x = 0
        # timeline mapping helpers
        self.t_min = 0.0
        self.t_max = 0.0
        self.span = 1.0
        self.total_width = 800

    def sizeHint(self):
        return QSize(max(800, int(self.duration * float(self.px_per_second))), 120)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(event.rect(), QColor("#252526"))
        # 先绘制图片标记（色块）在上部
        block_w = 5 if hasattr(self, 'block_w') == False else getattr(self, 'block_w', 5)
        block_h = 30 if hasattr(self, 'block_h') == False else getattr(self, 'block_h', 30)
        top_y = 5
        for info in self.images:
            try:
                x = int(info.get('x', 0))
                idx = int(info.get('index', -1))
                if idx == self.selected_index:
                    color = QColor('#D32F2F')
                else:
                    color = QColor('#FFFFFF') if (idx % 2 == 0) else QColor('#007ACC')
                painter.setBrush(color)
                painter.setPen(QPen(QColor('#333333')))
                painter.drawRect(x - block_w // 2+5, top_y + 9, block_w, block_h)
                # 绘制序号在色块上方
                seq = info.get('seq', None)
                if seq is None:
                    try:
                        seq = idx + 1
                    except Exception:
                        seq = None
                if seq is not None:
                    font = QFont("Arial", 9)
                    painter.setFont(font)
                    painter.setPen(QPen(QColor('#D4D4D4')))
                    painter.drawText(x - block_w // 2 + 2, top_y + 6, str(int(seq)))
            except Exception:
                continue
        # 再在下部绘制刻度线与时间标签，使刻度置于底部
        pen = QPen(QColor("#D4D4D4"))
        pen.setWidth(1)
        painter.setPen(pen)
        max_t = int(self.duration)
        h = self.height()
        # 计算刻度的垂直位置（靠近底部）
        line_top = h - 40
        line_bottom = h - 20
        label_y = h - 5
        for t in range(0, max_t + 10, 10):
            x = int(t * float(self.px_per_second))
            painter.drawLine(x, line_top, x, line_bottom)
            if t % 60 == 0:
                font = QFont("Arial", 9)
                painter.setFont(font)
                painter.drawText(x + 2, label_y, str(t))

        painter.end()
    
    def mousePressEvent(self, event):
        # handle press for dragging blocks
        px = event.pos().x()
        closest = None
        for info in self.images:
            ix = int(info.get('x', 0))
            if abs(px - ix) <= max(6, int(block_w := 5)):
                closest = info
                break
        if closest is not None:
            self._dragging_index = int(closest.get('index', -1))
            self._drag_start_x = px
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._dragging_index >= 0:
            new_x = int(event.pos().x())
            new_x = max(0, min(new_x, self.total_width))
            # update marker x and time
            for info in self.images:
                if int(info.get('index', -1)) == self._dragging_index:
                    info['x'] = new_x
                    # compute new time from x
                    try:
                        rel = float(new_x) / max(1.0, float(self.total_width))
                        new_time = self.t_min + rel * max(1.0, float(self.span))
                    except Exception:
                        new_time = info.get('time', 0.0)
                    info['time'] = new_time
                    break
            self.update()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._dragging_index >= 0:
            # find moved marker and emit signal
            moved_time = None
            moved_idx = self._dragging_index
            for info in self.images:
                if int(info.get('index', -1)) == moved_idx:
                    moved_time = float(info.get('time', 0.0))
                    break
            # reset dragging
            self._dragging_index = -1
            self._drag_start_x = 0
            try:
                if moved_time is not None:
                    self.image_moved.emit(moved_idx, moved_time)
            except Exception:
                pass
            # 检查是否需要重新排序（基于 x 位置）并发出重排信号
            try:
                # new_order: list of original indices in order from left->right
                sorted_by_x = sorted(self.images, key=lambda i: int(i.get('x', 0)))
                new_order = [int(i.get('index', -1)) for i in sorted_by_x]
                # always emit new order (main will decide if it needs to change)
                self.image_reordered.emit(new_order)
            except Exception:
                pass
        super().mouseReleaseEvent(event)


class TimelineWidget(QScrollArea):
    """时间轴区域：可设置 duration 与图片序列，并在图片上显示位置缩略图。"""
    image_clicked = pyqtSignal(int)  # index

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.content = _TimelineContent()
        self.setWidget(self.content)

    def setDuration(self, seconds: float):
        try:
            dur = float(seconds)
            self.content.duration = dur
            # 自动调整 px_per_second：当在默认缩放下的总宽度小于可见视口时，放大刻度间距以填满视口
            try:
                viewport_w = max(1, self.viewport().width())
                default_px = 1.0
                high_px = 10.0
                # 如果以 high_px 计算的总宽度能被视口容下，则使用高密度（10 px/s）
                if dur > 0 and (dur * high_px) <= viewport_w:
                    self.content.px_per_second = int(high_px)
                else:
                    self.content.px_per_second = int(default_px)
            except Exception:
                self.content.px_per_second = 1

            self.content.resize(self.content.sizeHint())
            self.content.update()
        except Exception:
            pass

    def set_images(self, images):
        """images: list of ImageItem (have create_time and thumbnail)."""
        self._images = images or []
        # compute image marker positions mapped to audio timeline width
        times = [i.create_time for i in self._images if i.create_time is not None]
        if not times:
            self.content.images = []
            self.content.update()
            return
        t_min, t_max = min(times), max(times)
        span = max(1.0, t_max - t_min)
        total_width = max(800, int(self.content.duration * float(self.content.px_per_second)))
        # store mapping helpers for drag operations
        self.content.t_min = t_min
        self.content.t_max = t_max
        self.content.span = span
        self.content.total_width = total_width
        markers = []
        for idx, img in enumerate(self._images):
            rel = (img.create_time - t_min) / span if span > 0 else 0.0
            x = int(rel * total_width)
            markers.append({'pixmap': img.thumbnail, 'time': img.create_time, 'x': x, 'index': idx, 'seq': idx + 1})
        self.content.images = markers
        self.content.resize(self.content.sizeHint())
        self.content.update()

    def set_selected_index(self, index: int):
        try:
            self.content.selected_index = int(index) if index is not None else -1
            self.content.update()
        except Exception:
            pass

    def resizeEvent(self, event):
        # 视口宽度变化时重新计算 px_per_second，以便在小时间轴上填满视口
        try:
            self.setDuration(self.content.duration)
        except Exception:
            pass
        super().resizeEvent(event)

    def mousePressEvent(self, event):
        # map click to image marker
        x = event.pos().x() + self.horizontalScrollBar().value()
        # find nearest marker within tolerance
        tol = 4
        best = None
        for info in getattr(self.content, 'images', []):
            if abs(x - info.get('x', 0)) <= tol:
                best = info
                break
        if best is not None:
            idx = best.get('index', -1)
            if idx >= 0:
                self.image_clicked.emit(idx)
        super().mousePressEvent(event)
