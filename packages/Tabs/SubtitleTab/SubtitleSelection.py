# -*- coding: utf-8 -*-
import os
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QFileDialog, QGroupBox, QMessageBox
)

from packages.Startup import GlobalIcons
from packages.Startup.Options import Options
from packages.Tabs.GlobalSetting import GlobalSetting
from packages.Startup.PreDefined import SUBTITLE_EXTENSIONS
from packages.Utils.TrackInfo import get_subtitle_tracks


class SubtitleSelectionSetting(QWidget):
    activation_signal = Signal(bool)
    tab_clicked_signal = Signal()
    
    def __init__(self):
        super().__init__()
        self.subtitle_files = []
        self.setup_ui()
        self.connect_signals()
    
    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        source_group = QGroupBox("字幕源")
        source_layout = QVBoxLayout()
        
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("字幕源文件夹："))
        self.source_path_edit = QLineEdit()
        self.source_path_edit.setReadOnly(True)
        self.source_path_edit.setPlaceholderText("选择包含字幕文件的文件夹")
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
        source_group.setLayout(source_layout)
        main_layout.addWidget(source_group)
        
        match_group = QGroupBox("字幕匹配（按序号一一对应）")
        match_layout = QHBoxLayout()
        
        video_table_widget = QWidget()
        video_layout = QVBoxLayout()
        video_layout.setContentsMargins(0, 0, 0, 0)
        video_layout.addWidget(QLabel("视频列表"))
        self.video_table = QTableWidget()
        self.video_table.setColumnCount(2)
        self.video_table.setHorizontalHeaderLabels(["序号", "视频文件"])
        self.video_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.video_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.video_table.setColumnWidth(0, 50)
        self.video_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.video_table.setEditTriggers(QTableWidget.NoEditTriggers)
        video_layout.addWidget(self.video_table)
        video_table_widget.setLayout(video_layout)
        
        subtitle_table_widget = QWidget()
        subtitle_layout = QVBoxLayout()
        subtitle_layout.setContentsMargins(0, 0, 0, 0)
        subtitle_layout.addWidget(QLabel("字幕列表"))
        self.subtitle_table = QTableWidget()
        self.subtitle_table.setColumnCount(2)
        self.subtitle_table.setHorizontalHeaderLabels(["序号", "字幕文件"])
        self.subtitle_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.subtitle_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.subtitle_table.setColumnWidth(0, 50)
        self.subtitle_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.subtitle_table.setEditTriggers(QTableWidget.NoEditTriggers)
        subtitle_layout.addWidget(self.subtitle_table)
        subtitle_table_widget.setLayout(subtitle_layout)
        
        match_layout.addWidget(video_table_widget, 1)
        match_layout.addWidget(subtitle_table_widget, 1)
        
        match_group.setLayout(match_layout)
        main_layout.addWidget(match_group)
        
        info_label = QLabel("提示：字幕按序号一一对应匹配到视频（第1个字幕→第1个视频，第2个字幕→第2个视频...）")
        info_label.setStyleSheet("color: gray;")
        main_layout.addWidget(info_label)
        
        self.setLayout(main_layout)
    
    def connect_signals(self):
        self.browse_button.clicked.connect(self.browse_folder)
        self.clear_button.clicked.connect(self.clear_files)
        self.refresh_button.clicked.connect(self.refresh_files)
    
    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择字幕源文件夹")
        if folder:
            self.source_path_edit.setText(folder)
            self.load_subtitles()
    
    def clear_files(self):
        self.source_path_edit.clear()
        self.subtitle_table.setRowCount(0)
        self.subtitle_files = []
        GlobalSetting.SUBTITLE_FILES_ABSOLUTE_PATH_LIST.clear()
        GlobalSetting.SUBTITLE_LANGUAGE.clear()
    
    def refresh_files(self):
        if self.source_path_edit.text():
            self.load_subtitles()
    
    def load_subtitles(self):
        folder = self.source_path_edit.text()
        if not folder or not os.path.isdir(folder):
            return
        
        self.subtitle_table.setRowCount(0)
        self.subtitle_files = []
        
        files = []
        for f in os.listdir(folder):
            ext = os.path.splitext(f)[1].lower()
            if ext in SUBTITLE_EXTENSIONS:
                files.append(f)
        
        files.sort()
        
        for idx, file_name in enumerate(files, 1):
            file_path = os.path.join(folder, file_name)
            self.subtitle_files.append(file_path)
            
            row = self.subtitle_table.rowCount()
            self.subtitle_table.insertRow(row)
            self.subtitle_table.setItem(row, 0, QTableWidgetItem(str(idx)))
            self.subtitle_table.setItem(row, 1, QTableWidgetItem(file_name))
        
        self.auto_match_by_index()
    
    def auto_match_by_index(self):
        GlobalSetting.SUBTITLE_FILES_ABSOLUTE_PATH_LIST.clear()
        GlobalSetting.SUBTITLE_LANGUAGE.clear()
        
        for video_idx in range(len(GlobalSetting.VIDEO_FILES_LIST)):
            sub_idx = video_idx
            
            if sub_idx < len(self.subtitle_files):
                sub_path = self.subtitle_files[sub_idx]
                GlobalSetting.SUBTITLE_FILES_ABSOLUTE_PATH_LIST[video_idx] = [sub_path]
                GlobalSetting.SUBTITLE_LANGUAGE[video_idx] = 'chi'
    
    def refresh_video_list(self):
        self.video_table.setRowCount(0)
        for idx, video_name in enumerate(GlobalSetting.VIDEO_FILES_LIST, 1):
            row = self.video_table.rowCount()
            self.video_table.insertRow(row)
            self.video_table.setItem(row, 0, QTableWidgetItem(str(idx)))
            self.video_table.setItem(row, 1, QTableWidgetItem(video_name))
        
        self.auto_match_by_index()
    
    def update_theme_mode_state(self):
        pass
    
    def set_preset_options(self):
        self.refresh_video_list()
