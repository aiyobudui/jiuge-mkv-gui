# -*- coding: utf-8 -*-
import webbrowser
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QCursor


class MktoolnixNotFoundDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("MKVToolNix 未安装")
        self.setFixedSize(420, 220)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setup_ui()
    
    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(25, 25, 25, 20)
        main_layout.setSpacing(15)
        
        title_label = QLabel("未检测到 MKVToolNix")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        desc_label = QLabel("MKVToolNix 是处理 MKV 文件的必备工具。\n请安装后再使用本程序。")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        main_layout.addWidget(desc_label)
        
        link_layout = QHBoxLayout()
        link_layout.addStretch()
        
        self.link_label = QLabel()
        self.link_label.setText('<a href="https://mkvtoolnix.download/downloads.html#windows" style="color: #0078d4; text-decoration: none;">点击访问 MKVToolNix 官方下载页面</a>')
        self.link_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        self.link_label.setOpenExternalLinks(False)
        self.link_label.linkActivated.connect(self.open_download_page)
        self.link_label.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        link_layout.addWidget(self.link_label)
        
        link_layout.addStretch()
        main_layout.addLayout(link_layout)
        
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(line)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.download_button = QPushButton("打开下载页面")
        self.download_button.setFixedWidth(100)
        self.download_button.clicked.connect(self.open_download_page)
        button_layout.addWidget(self.download_button)
        
        self.select_button = QPushButton("手动选择")
        self.select_button.setFixedWidth(80)
        self.select_button.clicked.connect(self.accept)
        button_layout.addWidget(self.select_button)
        
        self.close_button = QPushButton("关闭")
        self.close_button.setFixedWidth(60)
        self.close_button.clicked.connect(self.reject)
        button_layout.addWidget(self.close_button)
        
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)
    
    def open_download_page(self):
        webbrowser.open("https://mkvtoolnix.download/downloads.html#windows")
