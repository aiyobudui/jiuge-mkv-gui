# -*- coding: utf-8 -*-
import os
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QFileDialog, QMessageBox, QGroupBox, QCheckBox
)

from packages.Startup import GlobalIcons
from packages.Startup.Options import Options
from packages.Tabs.GlobalSetting import GlobalSetting, get_readable_filesize
from packages.Startup.PreDefined import VIDEO_EXTENSIONS
from packages.Utils.TrackInfo import get_subtitle_tracks, get_audio_tracks, get_attachments, format_track_info
from packages.Widgets.MediaInfoDialog import MediaInfoDialog


class VideoSelectionSetting(QWidget):
    tab_clicked_signal = Signal()
    video_list_updated = Signal()
    refresh_track_info = Signal()
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.connect_signals()
    
    def refresh_track_info_now(self):
        if not Options.Mkvmerge_Path or not os.path.exists(Options.Mkvmerge_Path):
            return
        
        if not GlobalSetting.VIDEO_FILES_ABSOLUTE_PATH_LIST:
            return
        
        GlobalSetting.VIDEO_OLD_TRACKS_SUBTITLES_INFO.clear()
        GlobalSetting.VIDEO_OLD_TRACKS_AUDIOS_INFO.clear()
        GlobalSetting.VIDEO_OLD_ATTACHMENTS_INFO.clear()
        
        for i, file_path in enumerate(GlobalSetting.VIDEO_FILES_ABSOLUTE_PATH_LIST):
            subtitle_tracks = get_subtitle_tracks(file_path)
            audio_tracks = get_audio_tracks(file_path)
            attachment_tracks = get_attachments(file_path)
            GlobalSetting.VIDEO_OLD_TRACKS_SUBTITLES_INFO.append(subtitle_tracks)
            GlobalSetting.VIDEO_OLD_TRACKS_AUDIOS_INFO.append(audio_tracks)
            GlobalSetting.VIDEO_OLD_ATTACHMENTS_INFO.append(attachment_tracks)
            
            if i < self.video_table.rowCount():
                sub_item = QTableWidgetItem(str(len(subtitle_tracks)))
                sub_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.video_table.setItem(i, 2, sub_item)
                
                audio_item = QTableWidgetItem(str(len(audio_tracks)))
                audio_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.video_table.setItem(i, 3, audio_item)
    
    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        source_group = QGroupBox("视频源")
        source_layout = QVBoxLayout()
        
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("视频源文件夹："))
        self.source_path_edit = QLineEdit()
        self.source_path_edit.setReadOnly(True)
        self.source_path_edit.setPlaceholderText("选择包含视频文件的文件夹")
        path_layout.addWidget(self.source_path_edit)
        
        self.clear_button = QPushButton("清空")
        self.clear_button.setFixedWidth(60)
        self.clear_button.setIcon(GlobalIcons.ClearIcon)
        path_layout.addWidget(self.clear_button)
        
        self.refresh_button = QPushButton("刷新")
        self.refresh_button.setFixedWidth(60)
        self.refresh_button.setIcon(GlobalIcons.RefreshIcon)
        path_layout.addWidget(self.refresh_button)
        
        self.browse_button = QPushButton("浏览")
        self.browse_button.setFixedWidth(60)
        self.browse_button.setIcon(GlobalIcons.FolderIcon)
        path_layout.addWidget(self.browse_button)
        
        source_layout.addLayout(path_layout)
        
        info_layout = QHBoxLayout()
        self.select_all_checkbox = QCheckBox("全选")
        self.select_all_checkbox.setChecked(True)
        info_layout.addWidget(self.select_all_checkbox)
        
        self.media_info_button = QPushButton("媒体信息")
        self.media_info_button.setFixedWidth(80)
        info_layout.addWidget(self.media_info_button)
        info_layout.addStretch()
        source_layout.addLayout(info_layout)
        
        source_group.setLayout(source_layout)
        main_layout.addWidget(source_group)
        
        table_group = QGroupBox("视频列表")
        table_layout = QVBoxLayout()
        
        self.video_table = QTableWidget()
        self.video_table.setColumnCount(5)
        self.video_table.setHorizontalHeaderLabels(["选择", "名称", "字幕轨", "音轨", "大小"])
        self.video_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.video_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.video_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.video_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.video_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        self.video_table.setColumnWidth(0, 50)
        self.video_table.setColumnWidth(2, 60)
        self.video_table.setColumnWidth(3, 60)
        self.video_table.setColumnWidth(4, 100)
        self.video_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.video_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.video_table.setAlternatingRowColors(True)
        
        table_layout.addWidget(self.video_table)
        table_group.setLayout(table_layout)
        main_layout.addWidget(table_group)
        
        self.setLayout(main_layout)
    
    def connect_signals(self):
        self.browse_button.clicked.connect(self.browse_folder)
        self.clear_button.clicked.connect(self.clear_files)
        self.refresh_button.clicked.connect(self.refresh_files)
        self.media_info_button.clicked.connect(self.show_media_info)
        self.select_all_checkbox.stateChanged.connect(self.toggle_select_all)
    
    def toggle_select_all(self, state):
        checked = state == Qt.CheckState.Checked.value
        for row in range(self.video_table.rowCount()):
            checkbox_widget = self.video_table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox:
                    checkbox.setChecked(checked)
    
    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择视频源文件夹")
        if folder:
            self.source_path_edit.setText(folder)
            self.load_videos()
    
    def clear_files(self):
        self.source_path_edit.clear()
        self.video_table.setRowCount(0)
        GlobalSetting.VIDEO_FILES_LIST.clear()
        GlobalSetting.VIDEO_FILES_ABSOLUTE_PATH_LIST.clear()
        GlobalSetting.VIDEO_FILES_SIZE_LIST.clear()
        GlobalSetting.VIDEO_OLD_TRACKS_SUBTITLES_INFO.clear()
        GlobalSetting.VIDEO_OLD_TRACKS_AUDIOS_INFO.clear()
        GlobalSetting.VIDEO_OLD_ATTACHMENTS_INFO.clear()
        self.video_list_updated.emit()
    
    def refresh_files(self):
        if self.source_path_edit.text():
            self.load_videos()
    
    def load_videos(self):
        folder = self.source_path_edit.text()
        if not folder or not os.path.isdir(folder):
            return
        
        self.video_table.setRowCount(0)
        GlobalSetting.VIDEO_FILES_LIST.clear()
        GlobalSetting.VIDEO_FILES_ABSOLUTE_PATH_LIST.clear()
        GlobalSetting.VIDEO_FILES_SIZE_LIST.clear()
        GlobalSetting.VIDEO_OLD_TRACKS_SUBTITLES_INFO.clear()
        GlobalSetting.VIDEO_OLD_TRACKS_AUDIOS_INFO.clear()
        
        files = []
        for f in os.listdir(folder):
            ext = os.path.splitext(f)[1].lower()
            if ext in VIDEO_EXTENSIONS:
                files.append(f)
        
        files.sort()
        
        has_mkvmerge = Options.Mkvmerge_Path and os.path.exists(Options.Mkvmerge_Path)
        
        for file_name in files:
            file_path = os.path.join(folder, file_name)
            file_size = os.path.getsize(file_path)
            
            GlobalSetting.VIDEO_FILES_LIST.append(file_name)
            GlobalSetting.VIDEO_FILES_ABSOLUTE_PATH_LIST.append(file_path)
            GlobalSetting.VIDEO_FILES_SIZE_LIST.append(file_size)
            
            if has_mkvmerge:
                subtitle_tracks = get_subtitle_tracks(file_path)
                audio_tracks = get_audio_tracks(file_path)
                attachment_tracks = get_attachments(file_path)
            else:
                subtitle_tracks = []
                audio_tracks = []
                attachment_tracks = []
            
            GlobalSetting.VIDEO_OLD_TRACKS_SUBTITLES_INFO.append(subtitle_tracks)
            GlobalSetting.VIDEO_OLD_TRACKS_AUDIOS_INFO.append(audio_tracks)
            GlobalSetting.VIDEO_OLD_ATTACHMENTS_INFO.append(attachment_tracks)
            
            row = self.video_table.rowCount()
            self.video_table.insertRow(row)
            
            checkbox = QCheckBox()
            checkbox.setChecked(True)
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            self.video_table.setCellWidget(row, 0, checkbox_widget)
            
            self.video_table.setItem(row, 1, QTableWidgetItem(file_name))
            
            if has_mkvmerge:
                sub_item = QTableWidgetItem(str(len(subtitle_tracks)))
                sub_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.video_table.setItem(row, 2, sub_item)
                
                audio_item = QTableWidgetItem(str(len(audio_tracks)))
                audio_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.video_table.setItem(row, 3, audio_item)
            else:
                sub_item = QTableWidgetItem("-")
                sub_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.video_table.setItem(row, 2, sub_item)
                
                audio_item = QTableWidgetItem("-")
                audio_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.video_table.setItem(row, 3, audio_item)
            
            size_item = QTableWidgetItem(get_readable_filesize(file_size))
            size_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.video_table.setItem(row, 4, size_item)
        
        self.video_list_updated.emit()
    
    def show_media_info(self):
        selected_rows = self.video_table.selectedItems()
        if not selected_rows:
            QMessageBox.information(self, "提示", "请先选择一个视频文件")
            return
        
        row = selected_rows[0].row()
        if row < len(GlobalSetting.VIDEO_FILES_ABSOLUTE_PATH_LIST):
            file_path = GlobalSetting.VIDEO_FILES_ABSOLUTE_PATH_LIST[row]
            file_name = GlobalSetting.VIDEO_FILES_LIST[row]
            file_size = GlobalSetting.VIDEO_FILES_SIZE_LIST[row]
            
            subtitle_tracks = GlobalSetting.VIDEO_OLD_TRACKS_SUBTITLES_INFO[row]
            audio_tracks = GlobalSetting.VIDEO_OLD_TRACKS_AUDIOS_INFO[row]
            
            dialog = MediaInfoDialog(self)
            dialog.set_media_info(
                file_name,
                file_path,
                get_readable_filesize(file_size),
                audio_tracks,
                subtitle_tracks
            )
            dialog.exec()
    
    def get_selected_files(self):
        selected = []
        for row in range(self.video_table.rowCount()):
            checkbox = self.video_table.cellWidget(row, 0)
            if checkbox and checkbox.findChild(QCheckBox).isChecked():
                selected.append(row)
        return selected
    
    def update_theme_mode_state(self):
        pass
    
    def refresh_video_list(self):
        if self.source_path_edit.text():
            self.load_videos()
    
    def set_preset_options(self):
        if self.source_path_edit.text():
            self.load_videos()