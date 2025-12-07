"""
PyInstaller runtime hook for imageio
解决imageio在打包后找不到ffmpeg等依赖的问题
"""

import os
import sys
import importlib.util

def fix_imageio_paths():
    """
    修复imageio的路径问题
    在打包后的环境中确保imageio能找到必要的资源文件
    """
    if getattr(sys, 'frozen', False):
        # 获取打包后的应用程序路径
        bundle_dir = sys._MEIPASS
        
        # 确保imageio的插件目录能被正确找到
        imageio_plugin_path = os.path.join(bundle_dir, 'imageio', 'plugins')
        if os.path.exists(imageio_plugin_path):
            # 将插件目录添加到Python路径中
            sys.path.append(os.path.dirname(imageio_plugin_path))
        
        # 设置环境变量以帮助imageio找到ffmpeg
        if not os.environ.get('IMAGEIO_FFMPEG_EXE'):
            ffmpeg_exe = os.path.join(bundle_dir, 'imageio_ffmpeg', 'binaries', 'ffmpeg.exe')
            if os.path.exists(ffmpeg_exe):
                os.environ['IMAGEIO_FFMPEG_EXE'] = ffmpeg_exe

if __name__ == '__main__':
    fix_imageio_paths()
else:
    fix_imageio_paths()
import os
import sys
import subprocess
import shutil
from pathlib import Path

def install_pyinstaller():
    """安装PyInstaller"""
    try:
        import PyInstaller
        print("PyInstaller已安装")
    except ImportError:
        print("正在安装PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

def build_exe():
    """构建exe文件"""
    print("开始构建exe文件...")
    try:
        # 使用PyInstaller构建
        cmd = [
            sys.executable, "-m", "PyInstaller", 
            "--onedir",  # 使用onedir模式以便更好地处理资源文件
            "--windowed",  # 隐藏控制台窗口
            "--name", "JPEG2MPEG",
            "--add-data", "ui;ui",
            "--add-data", "core;core",
            "--add-data", "utils;utils",
            "--additional-hooks-dir", ".",  # 添加当前目录作为hook目录
            "--runtime-hook", "rthook-imageio.py",  # 添加runtime hook
            "--hidden-import", "imageio",
            "--hidden-import", "moviepy",
            "--hidden-import", "moviepy.editor",
            "--hidden-import", "numpy",
            "--hidden-import", "PIL",
            "--collect-all", "imageio",  # 收集所有相关文件
            "--collect-all", "moviepy",  # 收集所有相关文件
            "--copy-metadata", "imageio",
            "--copy-metadata", "moviepy",
            "--copy-metadata", "numpy",
            "--copy-metadata", "pillow",
            "--exclude-module", "tkinter",
            "--exclude-module", "matplotlib",
            "--exclude-module", "scipy",
            "--clean",  # 清理缓存，确保干净构建
            "main.py"
        ]
        
        subprocess.check_call(cmd)
        print("构建完成!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"构建失败: {e}")
        return False

def main():
    print("JPEG2MPEG 打包工具")
    print("==================")
    
    # 安装PyInstaller
    install_pyinstaller()
    
    # 构建exe
    if build_exe():
        print("\n打包成功!")
        print("可执行文件位置: dist/JPEG2MPEG/")
    else:
        print("\n打包失败!")

if __name__ == "__main__":
    main()