安装与运行指南

环境与依赖
- Python 3.8+
- 推荐在虚拟环境中安装依赖：

依赖版本（与要求一致）:
- colorama==0.4.6
- decorator==5.2.1
- imageio==2.37.2
- imageio-ffmpeg==0.6.0
- moviepy==2.2.1
- mutagen==1.47.0
- numpy==2.3.5
- pillow==11.3.0
- proglog==0.1.12
- python-dotenv==1.2.1
- tqdm==4.67.1
- PyQt5==5.15.11
- PyQt5-Qt5==5.15.2
- PyQt5_sip==12.17.1

安装示例（PowerShell）:

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

运行程序

```powershell
python main.py
```

FFmpeg 说明
- 本程序在导出视频时依赖 moviepy，而 moviepy 需要系统上安装 FFmpeg。
- Windows 用户可以从 https://www.gyan.dev/ffmpeg/builds/ 或 https://ffmpeg.org/ 下载并安装。
- 将 `ffmpeg.exe` 所在目录添加到系统 `PATH`，或在程序运行时设置环境变量 `IMAGEIO_FFMPEG_EXE` 指向 ffmpeg 可执行文件。

注意事项
- 程序延迟导入 moviepy，以避免启动时导入失败阻塞界面。
- Pillow 图像处理遵循安全规范：不使用 PIL.ImageQt，优先转换为 RGB/RGBA，并提供占位图像作为回退。

如果遇到问题，请在控制台查看堆栈信息，或在界面中查看友好错误提示。