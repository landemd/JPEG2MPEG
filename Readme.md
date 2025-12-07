**项目说明**

【背景】听报告的时候，拍了部分照片和录音，为了将照片和录音做成视频方便分享和回顾报告内容，做了这个程序。

这是一个基于 PyQt5 的桌面工具，用于将图片序列与音频合成为 MP4 视频（JPEG2MPEG）。
主要功能包括：导入图片与音频、在时间轴上调整图片显示时间、预览缩略图、以及将图片序列与音频导出为视频文件。

**目录结构（简要）**

- `main.py`                : 应用程序入口
- `ui/`                   : 界面相关模块（窗口、控件、时间轴等）
- `core/`                 : 核心逻辑（媒体管理、导出、数据模型等）
- `utils/`                : 图片/音频/文件处理辅助函数
- `resources/`            : 资源（图标等）

**主要模块说明**

- `core/media_manager.py` : 管理图片与音频列表、排序与元数据（mtime、duration）。
- `core/export_manager.py`: 导出管理。使用 `moviepy`（延迟导入）和 `ffmpeg` 将图片序列与音频合成 MP4；包含运行时诊断日志和兼容不同 moviepy 版本的回退逻辑。
- `ui/main_window.py`     : 主窗口与菜单、工具栏、状态栏。
- `ui/timeline_widget.py` : 自定义时间轴视图，显示色块、支持拖放修改图片时间并同步回 `MediaManager`。
- `ui/widgets.py`         : 常用自定义控件（卡片、可拖拽列表、进度条等）。

**快速开始（Windows, PowerShell）**

1. 激活项目虚拟环境（假设在仓库的 `Scripts` 目录）：

```powershell
D:\Repository\JPEG2MPEG\Scripts\Activate.ps1
```

2. 安装依赖（如果尚未安装）：

```powershell
python -m pip install -r requirements.txt
```

3. 运行程序：

```powershell
python main.py
```

4. 快速验证 `moviepy` + `ffmpeg`（可选）：仓库中包含 `test_export.py`，它会生成两张临时图片并导出 `test_out.mp4`：

```powershell
python tools/test_export.py
```

**打包为 Windows 可执行文件**

项目可以打包为 Windows 上独立运行的 exe 文件，无需安装 Python 环境。

1. 确保已安装所有依赖：

```powershell
python -m pip install -r requirements.txt
```

2. 安装 PyInstaller：

```powershell
python -m pip install pyinstaller
```

3. 运行打包脚本：

```powershell
python build.py
```

4. 打包完成后，可在 `dist/JPEG2MPEG/` 目录下找到可执行文件 `JPEG2MPEG.exe` 及其依赖文件。

注意：由于使用了 `--onedir` 模式打包，生成的是一个目录而不是单个 exe 文件，这样可以更好地处理资源文件和依赖库。

**导出注意事项与故障排查**

- moviepy 导入：程序采用延迟导入并有回退逻辑（优先 `moviepy.editor`，若不可用则从顶层 `moviepy` 导入）。如果在你的虚拟环境中出现 `No module named 'moviepy.editor'`，但 `from moviepy import ImageSequenceClip` 可行，程序会自动回退并继续导出。
- ffmpeg：程序会尝试在运行时设置 `IMAGEIO_FFMPEG_EXE` / `FFMPEG_BINARY`（默认猜测 `D:\Program Files\ffmpeg\bin\ffmpeg.exe`）；如果你的 ffmpeg 安装在其他位置，请确保该路径在系统 `PATH` 中或设置相应环境变量。
- 图片尺寸：`ImageSequenceClip` 要求所有帧尺寸一致。程序已在导出前对图片做预处理：计算目标尺寸（所有图片的最大宽与高），对每张图片进行等比缩放并在黑色背景上居中填充，临时生成统一尺寸的 PNG 帧用于导出。

**诊断日志（JSON）**

导出过程中程序会为每次导出生成一个 JSON 格式的诊断日志文件（文件名以 `jpeg2mpeg_export_YYYYMMDDThhmmss.json` 或 `jpeg2mpeg_export_error_*.json` 开头）。默认写入系统临时目录；如需指定位置，请设置环境变量 `JPEG2MPEG_LOG_DIR` 指向一个可写目录。

日志结构（示例字段）：
- `schema_version`: 日志 schema 版本（当前 `1.0`）
- `start_time`: 导出开始时间（ISO 格式）
- `python_executable`: Python 可执行路径
- `sys_path`: 导出时的 `sys.path` 列表
- `ffmpeg_guess`, `IMAGEIO_FFMPEG_EXE`, `FFMPEG_BINARY`: ffmpeg 相关信息
- `moviepy_version`: 如果可用则记录 moviepy 版本
- `image_count`, `image_paths_sample`, `durations`, `total_audio_duration`: 导入的媒体信息
- `prepared_frames_dir`: 若导出前生成了统一尺寸的临时帧，此字段记录临时目录（通常会在导出结束后删除）
- `export_success` 或 `export_error` 与 `traceback`（若发生异常）

UI 中在主工具栏新增了三个相关按钮：
- **打开诊断日志**（Ctrl+Shift+L）：使用系统默认程序打开最近一次生成的诊断 JSON 文件。
- **在资源管理器中显示**（Ctrl+Alt+L）：打开包含日志文件的文件夹（Windows 使用文件管理器）。
- **复制诊断日志路径**（Ctrl+Alt+C）：将诊断日志的完整路径复制到剪贴板，便于粘贴到问题反馈或聊天中。

如果导出失败，请把 JSON 日志文件内容贴给维护者以便快速排查。

**常见问题快速解决**

- 导出报错 “ImageSequenceClip requires all images to be the same size”：说明输入图片尺寸不一致，程序会自动对图片进行缩放与填充；如果你希望使用自定义填充颜色或目标尺寸，请在 `core/export_manager.py` 中调整相关逻辑。
- 导出报错 `No module named 'moviepy.editor'`：请确认 `moviepy` 已安装（`python -m pip show moviepy`）并运行 `python -c "from moviepy import ImageSequenceClip; print('OK')"` 验证顶层导入是否可用。
- ffmpeg 未找到或编码失败：请确保 `ffmpeg` 已安装并可通过命令行运行（`ffmpeg -version`），或把 `ffmpeg.exe` 路径加入系统 `PATH`。

**开发者提示**

- 代码风格：保持模块化与延迟导入以减少启动时依赖问题。
- 日志：导出诊断日志位于临时目录，便于在不同环境下收集问题信息。

如果需要我可以：
- 将诊断日志改为 JSON 格式以便机器解析。
- 在 UI 中添加“打开诊断日志”按钮以便用户直接查看。
- 支持可配置的帧填充颜色或以第一张图片尺寸为目标。

---

作者：项目维护者
日期：2025-12-07