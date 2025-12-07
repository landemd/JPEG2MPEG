from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class ImageItem:
    """	图片项数据模型
    create_time 实际为文件修改日期（时间戳）"""
    path: str                 # 文件路径
    thumbnail: Any            # 缩略图（QPixmap）或占位
    filename: str             # 文件名
    create_time: float        # 修改日期（时间戳）
    size: int                 # 文件大小（字节）
    duration: Optional[float] = None  # 导出时该图片在视频中的持续时长（秒）


@dataclass
class AudioItem:
    """音频项数据模型"""
    path: str       # 文件路径
    duration: float # 时长（秒）
    filename: str   # 文件名