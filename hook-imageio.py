# PyInstaller hook for imageio to fix metadata issue
from PyInstaller.utils.hooks import collect_data_files, copy_metadata

# Collect metadata
datas = copy_metadata('imageio')

# Collect data files
datas += collect_data_files('imageio')