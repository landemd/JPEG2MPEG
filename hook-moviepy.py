# PyInstaller hook for moviepy to fix metadata issue
from PyInstaller.utils.hooks import collect_data_files, copy_metadata

# Collect metadata
datas = copy_metadata('moviepy')

# Collect data files
datas += collect_data_files('moviepy')