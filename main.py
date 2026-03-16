# -*- coding: utf-8 -*-
import logging
import signal
import sys
import os
from traceback import format_exception
import psutil
from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QApplication
from packages.Startup import GlobalFiles
from packages.Startup import GlobalIcons
from packages.MainWindow import MainWindow

if sys.platform == "win32":
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("jiuge.mkv.gui")

window: MainWindow
app: QApplication


def setup_application_font():
    if os.path.exists(GlobalFiles.MyFontPath):
        try:
            font_id = QFontDatabase.addApplicationFont(GlobalFiles.MyFontPath)
            if font_id >= 0:
                font_families = QFontDatabase.applicationFontFamilies(font_id)
                if font_families:
                    font_name = font_families[0]
                    font = QFont(font_name, 10)
                    app.setFont(font)
        except Exception:
            pass


def create_application():
    global app
    app = QApplication(sys.argv)
    if GlobalIcons.AppIcon:
        app.setWindowIcon(GlobalIcons.AppIcon)


def create_window():
    global window
    window = MainWindow()


def run_application():
    app_execute = app.exec()
    kill_all_children()
    sys.exit(app_execute)


def kill_all_children():
    try:
        current_process = psutil.Process()
        children = current_process.children(recursive=True)
        for child in children:
            try:
                child.terminate()
            except:
                pass
    except:
        pass


def logger_exception(exception_type, exception_value, exception_trace_back):
    for string in format_exception(exception_type, exception_value, exception_trace_back):
        logging.error(string)


def setup_logger():
    log_dir = os.path.dirname(GlobalFiles.AppLogFilePath)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    logging.basicConfig(
        format='(%(asctime)s): %(name)s [%(levelname)s]: %(message)s',
        datefmt='%m/%d/%Y %I:%M:%S %p',
        level=logging.DEBUG,
        handlers=[
            logging.FileHandler(filename=GlobalFiles.AppLogFilePath, encoding='utf-8', mode='a+'),
            logging.StreamHandler()
        ]
    )
    sys.excepthook = logger_exception


if __name__ == "__main__":
    setup_logger()
    create_application()
    setup_application_font()
    create_window()
    run_application()
