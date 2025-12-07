import sys
import os
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    
    # 设置应用样式
    app.setStyle("Fusion")
    app.setStyleSheet("""
        QMainWindow {
            background-color: #1E1E1E;
            color: #D4D4D4;
        }
        QWidget {
            background-color: #1E1E1E;
            color: #D4D4D4;
        }
        QToolBar {
            background-color: #333337;
            border: none;
        }
        QStatusBar {
            background-color: #333337;
            color: #D4D4D4;
        }
        QComboBox {
            background-color: #3E3E42;
            color: #D4D4D4;
            border: 1px solid #3F3F46;
            padding: 3px;
        }
        QLabel {
            color: #D4D4D4;
        }
        QGroupBox {
            color: #D4D4D4;
            border: 1px solid #3F3F46;
            border-radius: 4px;
            margin-top: 1ex;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 3px;
        }
    """)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()