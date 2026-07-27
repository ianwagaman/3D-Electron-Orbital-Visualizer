import sys
import os
import ctypes
import settings_manager
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QTimer
from vispy import app
from vispy.util.quaternion import Quaternion
from canvas import OrbitalApp

###MAKE EXE FILE###
#pyinstaller --clean --onefile --noconsole --name="Orbital Viewer" --icon="icons/program_icon.ico" --add-data "icons;icons" --collect-data vispy --collect-submodules vispy.app.backends main.py
####################

try:
    myappid = 'mycompany.orbitalviewer.v2'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception:
    pass

qt_app = QApplication(sys.argv)


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


icon_path = resource_path("icons/program_icon.ico")

qt_app.setWindowIcon(QIcon(icon_path))

app.use_app('pyqt6')


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Orbital Viewer")
        self.setWindowIcon(QIcon(icon_path))
        self.resize(1000, 800)

        self.wrapper = QWidget()
        self.setCentralWidget(self.wrapper)
        self.layout = QVBoxLayout(self.wrapper)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.canvas = OrbitalApp()
        self.layout.addWidget(self.canvas.native)

        QTimer.singleShot(50, self.startup_hook)

    def showEvent(self, event):
        super().showEvent(event)
        if sys.platform == "win32":
            try:
                hwnd = int(self.winId())
                hicon = ctypes.windll.user32.LoadImageW(
                    0,
                    icon_path,
                    1,
                    0, 0,
                    0x00000010 | 0x00000040)
                if hicon:
                    ctypes.windll.user32.SendMessageW(hwnd, 0x0080, 0, hicon)
                    ctypes.windll.user32.SendMessageW(hwnd, 0x0080, 1, hicon)
            except Exception as e:
                print(f"Win32 icon override failed: {e}")

    def startup_hook(self):
        self.canvas.view.camera._quaternion = Quaternion(w=0.382, x=0, y=0.923, z=0)
        self.canvas.refresh_display()

    def closeEvent(self, event):
        if hasattr(self, 'canvas'):
            settings_manager.save_settings(self.canvas)
            self.canvas.close()
        event.accept()


if __name__ == '__main__':
    win = MainWindow()
    win.show()
    sys.exit(qt_app.exec())