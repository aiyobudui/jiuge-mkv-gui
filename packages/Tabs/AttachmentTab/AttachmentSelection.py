# -*- coding: utf-8 -*-
import os
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QFileDialog, QGroupBox
)

from packages.Startup import GlobalIcons
from packages.Startup.Options import Options
from packages.Tabs.GlobalSetting import GlobalSetting
from packages.Startup.PreDefined import ATTACHMENT_EXTENSIONS
from packages.Utils.TrackInfo import get_attachments


class AttachmentSelectionSetting(QWidget):
    activation_signal = Signal(bool)
    tab_clicked_signal = Signal()
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.connect_signals()
    
    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        source_group = QGroupBox("附件源")
        source_layout = QVBoxLayout()
        
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("附件源文件夹："))
        self.source_path_edit = QLineEdit()
        self.source_path_edit.setReadOnly(True)
        self.source_path_edit.setPlaceholderText("选择包含附件文件的文件夹")
        path_layout.addWidget(self.source_path_edit)
        
        self.clear_button = QPushButton("清空")
        self.clear_button.setFixedWidth(60)
        path_layout.addWidget(self.clear_button)
        
        self.refresh_button = QPushButton("刷新")
        self.refresh_button.setFixedWidth(60)
        path_layout.addWidget(self.refresh_button)
        
        self.browse_button = QPushButton("浏览")
        self.browse_button.setFixedWidth(60)
        path_layout.addWidget(self.browse_button)
        
        source_layout.addLayout(path_layout)
        
        options_layout = QHBoxLayout()
        
        options_layout.addWidget(QLabel("视频附件："))
        self.attachment_combo = QComboBox()
        self.attachment_combo.setFixedWidth(200)
        self.attachment_combo.addItem("无")
        options_layout.addWidget(self.attachment_combo)
        
        options_layout.addWidget(QLabel("附件名称："))
        self.attachment_name_edit = QLineEdit()
        self.attachment_name_edit.setFixedWidth(150)
        self.attachment_name_edit.setReadOnly(True)
        self.attachment_name_edit.setPlaceholderText("自动读取")
        options_layout.addWidget(self.attachment_name_edit)
        
        options_layout.addStretch()
        source_layout.addLayout(options_layout)
        
        source_group.setLayout(source_layout)
        main_layout.addWidget(source_group)
        
        match_group = QGroupBox("附件匹配")
        match_layout = QHBoxLayout()
        
        video_table_widget = QWidget()
        video_layout = QVBoxLayout()
        video_layout.setContentsMargins(0, 0, 0, 0)
        video_layout.addWidget(QLabel("视频名称"))
        self.video_table = QTableWidget()
        self.video_table.setColumnCount(1)
        self.video_table.setHorizontalHeaderLabels(["视频文件"])
        self.video_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.video_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.video_table.setEditTriggers(QTableWidget.NoEditTriggers)
        video_layout.addWidget(self.video_table)
        video_table_widget.setLayout(video_layout)
        
        attachment_table_widget = QWidget()
        attachment_layout = QVBoxLayout()
        attachment_layout.setContentsMargins(0, 0, 0, 0)
        attachment_layout.addWidget(QLabel("附件名称"))
        self.attachment_table = QTableWidget()
        self.attachment_table.setColumnCount(1)
        self.attachment_table.setHorizontalHeaderLabels(["附件文件"])
        self.attachment_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.attachment_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.attachment_table.setEditTriggers(QTableWidget.NoEditTriggers)
        attachment_layout.addWidget(self.attachment_table)
        attachment_table_widget.setLayout(attachment_layout)
        
        match_layout.addWidget(video_table_widget, 1)
        match_layout.addWidget(attachment_table_widget, 1)
        
        match_group.setLayout(match_layout)
        main_layout.addWidget(match_group)
        
        self.setLayout(main_layout)
    
    def connect_signals(self):
        self.browse_button.clicked.connect(self.browse_folder)
        self.clear_button.clicked.connect(self.clear_files)
        self.refresh_button.clicked.connect(self.refresh_files)
        
        self.video_table.itemSelectionChanged.connect(self.on_video_selected)
        self.attachment_combo.currentIndexChanged.connect(self.on_attachment_selected)
        self.attachment_table.itemSelectionChanged.connect(self.on_file_selected)
    
    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择附件源文件夹")
        if folder:
            self.source_path_edit.setText(folder)
            self.load_attachments()
    
    def clear_files(self):
        self.source_path_edit.clear()
        self.attachment_table.setRowCount(0)
    
    def refresh_files(self):
        if self.source_path_edit.text():
            self.load_attachments()
    
    def load_attachments(self):
        folder = self.source_path_edit.text()
        if not folder or not os.path.isdir(folder):
            return
        
        self.attachment_table.setRowCount(0)
        
        files = []
        for f in os.listdir(folder):
            ext = os.path.splitext(f)[1].lower()
            if ext in ATTACHMENT_EXTENSIONS:
                files.append(f)
        
        files.sort()
        
        for file_name in files:
            row = self.attachment_table.rowCount()
            self.attachment_table.insertRow(row)
            self.attachment_table.setItem(row, 0, QTableWidgetItem(file_name))
        
        if files:
            self.apply_attachment_to_all_videos(files[0])
    
    def refresh_video_list(self):
        self.video_table.setRowCount(0)
        for video_name in GlobalSetting.VIDEO_FILES_LIST:
            row = self.video_table.rowCount()
            self.video_table.insertRow(row)
            self.video_table.setItem(row, 0, QTableWidgetItem(video_name))
    
    def on_video_selected(self):
        selected = self.video_table.selectedItems()
        if not selected:
            self.reset_attachment_info()
            return
        
        video_row = selected[0].row()
        self.update_attachment_combo(video_row)
    
    def reset_attachment_info(self):
        self.attachment_combo.clear()
        self.attachment_combo.addItem("无")
        self.attachment_name_edit.clear()
    
    def update_attachment_combo(self, video_row):
        self.attachment_combo.clear()
        
        if video_row < len(GlobalSetting.VIDEO_OLD_ATTACHMENTS_INFO):
            attachments = GlobalSetting.VIDEO_OLD_ATTACHMENTS_INFO[video_row]
            if attachments:
                for i, att in enumerate(attachments):
                    filename = att.get('filename', '')
                    display = f"#{i} {filename}" if filename else f"#{i}"
                    self.attachment_combo.addItem(display, att)
            else:
                self.attachment_combo.addItem("无")
        else:
            self.attachment_combo.addItem("无")
    
    def on_attachment_selected(self):
        index = self.attachment_combo.currentIndex()
        
        if index < 0:
            return
        
        att_data = self.attachment_combo.currentData()
        if att_data:
            filename = att_data.get('filename', '')
            self.attachment_name_edit.setText(filename)
        else:
            self.attachment_name_edit.clear()
    
    def on_file_selected(self):
        selected = self.attachment_table.selectedItems()
        if not selected:
            return
        
        file_name = selected[0].text()
        self.attachment_name_edit.setText(file_name)
    
    def apply_attachment_to_all_videos(self, attachment_file):
        folder = self.source_path_edit.text()
        attachment_path = os.path.join(folder, attachment_file)
        
        if not os.path.exists(attachment_path):
            return
        
        if not hasattr(GlobalSetting, 'ATTACHMENT_FILES_ABSOLUTE_PATH_LIST'):
            GlobalSetting.ATTACHMENT_FILES_ABSOLUTE_PATH_LIST = {}
        
        video_count = len(GlobalSetting.VIDEO_FILES_LIST) if hasattr(GlobalSetting, 'VIDEO_FILES_LIST') else 0
        for video_idx in range(video_count):
            if video_idx not in GlobalSetting.ATTACHMENT_FILES_ABSOLUTE_PATH_LIST:
                GlobalSetting.ATTACHMENT_FILES_ABSOLUTE_PATH_LIST[video_idx] = []
            if attachment_path not in GlobalSetting.ATTACHMENT_FILES_ABSOLUTE_PATH_LIST[video_idx]:
                GlobalSetting.ATTACHMENT_FILES_ABSOLUTE_PATH_LIST[video_idx].append(attachment_path)
        
        GlobalSetting.ATTACHMENT_ENABLED = True
    
    def update_theme_mode_state(self):
        pass
    
    def set_preset_options(self):
        self.refresh_video_list()
