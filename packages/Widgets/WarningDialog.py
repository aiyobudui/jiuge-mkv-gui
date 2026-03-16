# -*- coding: utf-8 -*-
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QHBoxLayout, QPushButton


class WarningDialog(QDialog):
    def __init__(self, window_title="警告", info_message="", parent=None):
        super().__init__(parent)
        self.setWindowTitle(window_title)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.info_label = QLabel(info_message)
        self.info_label.setWordWrap(True)
        self.ok_button = QPushButton("确定")
        self.ok_button.setFixedWidth(80)
        self.ok_button.clicked.connect(self.accept)
        self.main_layout = QVBoxLayout()
        self.main_layout.addWidget(self.info_label)
        self.button_layout = QHBoxLayout()
        self.button_layout.addStretch()
        self.button_layout.addWidget(self.ok_button)
        self.main_layout.addLayout(self.button_layout)
        self.setLayout(self.main_layout)
        self.setMinimumWidth(300)
