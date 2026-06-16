# -*- coding: utf-8 -*-
import os
import re
import logging
import threading
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from PySide6.QtCore import Signal, Qt, QMimeData, QUrl
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QFileDialog, QMessageBox, QGroupBox, QCheckBox
)

from packages.Startup import GlobalIcons
from packages.Startup.Options import Options
from packages.Tabs.GlobalSetting import GlobalSetting, get_readable_filesize
from packages.Startup.PreDefined import VIDEO_EXTENSIONS
from packages.Utils.TrackInfo import get_subtitle_tracks, get_audio_tracks, get_attachments, get_video_tracks, get_video_title
from packages.Widgets.ExtractTracksDialog import ExtractTracksDialog


class VideoSelectionSetting(QWidget):
    tab_clicked_signal = Signal()
    video_list_updated = Signal()
    refresh_track_info = Signal()
    
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.current_source_dir = ""
        self.setup_ui()
        self.connect_signals()
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if not urls:
            return
        
        video_files = []
        folders = []
        non_video_files = []
        
        for url in urls:
            path = url.toLocalFile()
            if os.path.isfile(path):
                ext = os.path.splitext(path)[1].lower()
                if ext in VIDEO_EXTENSIONS:
                    video_files.append(path)
                else:
                    non_video_files.append(path)
            elif os.path.isdir(path):
                folders.append(path)
        
        if non_video_files and not video_files and not folders:
            QMessageBox.warning(self, "提示", "支持的视频格式：\n.mkv .mp4 .avi .mov .wmv .flv .webm .m2ts .ts")
            event.ignore()
            return
        
        if folders:
            folder = folders[0]
            self.current_source_dir = folder
            self.source_path_edit.setText(folder)
            self.load_videos()
        elif video_files:
            existing_files = set(GlobalSetting.VIDEO_FILES_ABSOLUTE_PATH_LIST)
            new_files = [vf for vf in video_files if vf not in existing_files]
            
            if new_files:
                total_count = len(GlobalSetting.VIDEO_FILES_ABSOLUTE_PATH_LIST) + len(new_files)
                
                if total_count == 1:
                    self.current_source_dir = os.path.dirname(new_files[0])
                    self.source_path_edit.setText(self.current_source_dir)
                else:
                    self.current_source_dir = ""
                    self.source_path_edit.clear()
                
                self.load_video_files_append(new_files)
        
        event.acceptProposedAction()
    
    def load_video_files_append(self, file_paths):
        file_paths.sort()
        
        has_mkvmerge = Options.Mkvmerge_Path and os.path.exists(Options.Mkvmerge_Path)
        
        for file_path in file_paths:
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            
            GlobalSetting.VIDEO_FILES_LIST.append(file_name)
            GlobalSetting.VIDEO_FILES_ABSOLUTE_PATH_LIST.append(file_path)
            GlobalSetting.VIDEO_FILES_SIZE_LIST.append(file_size)
            
            row = self.video_table.rowCount()
            self.video_table.insertRow(row)
            
            checkbox = QCheckBox()
            checkbox.setChecked(True)
            checkbox.clicked.connect(self.update_selected_indices)
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            self.video_table.setCellWidget(row, 0, checkbox_widget)
            
            self.video_table.setItem(row, 1, QTableWidgetItem(file_name))
            
            audio_item = QTableWidgetItem("...")
            audio_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.video_table.setItem(row, 2, audio_item)
            
            sub_item = QTableWidgetItem("...")
            sub_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.video_table.setItem(row, 3, sub_item)
            
            attachment_item = QTableWidgetItem("...")
            attachment_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.video_table.setItem(row, 4, attachment_item)
            
            title_item = QTableWidgetItem("")
            title_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.video_table.setItem(row, 5, title_item)
            
            size_item = QTableWidgetItem(get_readable_filesize(file_size))
            size_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.video_table.setItem(row, 6, size_item)
            
            if has_mkvmerge:
                subtitle_tracks = get_subtitle_tracks(file_path)
                audio_tracks = get_audio_tracks(file_path)
                video_tracks = get_video_tracks(file_path)
                attachment_tracks = get_attachments(file_path)
                GlobalSetting.VIDEO_OLD_TRACKS_VIDEOS_INFO.append(video_tracks)
                GlobalSetting.VIDEO_OLD_TRACKS_SUBTITLES_INFO.append(subtitle_tracks)
                GlobalSetting.VIDEO_OLD_TRACKS_AUDIOS_INFO.append(audio_tracks)
                GlobalSetting.VIDEO_OLD_ATTACHMENTS_INFO.append(attachment_tracks)
                
                audio_item = QTableWidgetItem(str(len(audio_tracks)))
                audio_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.video_table.setItem(row, 2, audio_item)
                
                sub_item = QTableWidgetItem(str(len(subtitle_tracks)))
                sub_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.video_table.setItem(row, 3, sub_item)
                
                attachment_item = QTableWidgetItem(str(len(attachment_tracks)))
                attachment_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.video_table.setItem(row, 4, attachment_item)
                
                title = get_video_title(file_path)
                title_item = QTableWidgetItem(title)
                title_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.video_table.setItem(row, 5, title_item)
        
        self.update_selected_indices()
        self.video_list_updated.emit()
    
    def load_video_files(self, file_paths):
        self.video_table.setRowCount(0)
        GlobalSetting.VIDEO_FILES_LIST.clear()
        GlobalSetting.VIDEO_FILES_ABSOLUTE_PATH_LIST.clear()
        GlobalSetting.VIDEO_FILES_SIZE_LIST.clear()
        GlobalSetting.VIDEO_OLD_TRACKS_VIDEOS_INFO.clear()
        GlobalSetting.VIDEO_OLD_TRACKS_SUBTITLES_INFO.clear()
        GlobalSetting.VIDEO_OLD_TRACKS_AUDIOS_INFO.clear()
        GlobalSetting.VIDEO_OLD_ATTACHMENTS_INFO.clear()
        
        file_paths.sort()
        
        has_mkvmerge = Options.Mkvmerge_Path and os.path.exists(Options.Mkvmerge_Path)
        
        for file_path in file_paths:
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            
            GlobalSetting.VIDEO_FILES_LIST.append(file_name)
            GlobalSetting.VIDEO_FILES_ABSOLUTE_PATH_LIST.append(file_path)
            GlobalSetting.VIDEO_FILES_SIZE_LIST.append(file_size)
            
            row = self.video_table.rowCount()
            self.video_table.insertRow(row)
            
            checkbox = QCheckBox()
            checkbox.setChecked(True)
            checkbox.clicked.connect(self.update_selected_indices)
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            self.video_table.setCellWidget(row, 0, checkbox_widget)
            
            self.video_table.setItem(row, 1, QTableWidgetItem(file_name))
            
            audio_item = QTableWidgetItem("...")
            audio_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.video_table.setItem(row, 2, audio_item)
            
            sub_item = QTableWidgetItem("...")
            sub_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.video_table.setItem(row, 3, sub_item)
            
            attachment_item = QTableWidgetItem("...")
            attachment_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.video_table.setItem(row, 4, attachment_item)
            
            title_item = QTableWidgetItem("")
            title_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.video_table.setItem(row, 5, title_item)
            
            size_item = QTableWidgetItem(get_readable_filesize(file_size))
            size_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.video_table.setItem(row, 6, size_item)
        
        if has_mkvmerge:
            self.load_track_info_threaded()
        
        # 更新选中索引，因为复选框默认是选中状态
        self.update_selected_indices()
        
        self.video_list_updated.emit()
    
    def refresh_track_info_now(self):
        if not Options.Mkvmerge_Path or not os.path.exists(Options.Mkvmerge_Path):
            return
        
        if not GlobalSetting.VIDEO_FILES_ABSOLUTE_PATH_LIST:
            return
        
        GlobalSetting.VIDEO_OLD_TRACKS_VIDEOS_INFO.clear()
        GlobalSetting.VIDEO_OLD_TRACKS_SUBTITLES_INFO.clear()
        GlobalSetting.VIDEO_OLD_TRACKS_AUDIOS_INFO.clear()
        GlobalSetting.VIDEO_OLD_ATTACHMENTS_INFO.clear()
        
        for i, file_path in enumerate(GlobalSetting.VIDEO_FILES_ABSOLUTE_PATH_LIST):
            subtitle_tracks = get_subtitle_tracks(file_path)
            audio_tracks = get_audio_tracks(file_path)
            video_tracks = get_video_tracks(file_path)
            attachment_tracks = get_attachments(file_path)
            GlobalSetting.VIDEO_OLD_TRACKS_VIDEOS_INFO.append(video_tracks)
            GlobalSetting.VIDEO_OLD_TRACKS_SUBTITLES_INFO.append(subtitle_tracks)
            GlobalSetting.VIDEO_OLD_TRACKS_AUDIOS_INFO.append(audio_tracks)
            GlobalSetting.VIDEO_OLD_ATTACHMENTS_INFO.append(attachment_tracks)
            
            if i < self.video_table.rowCount():
                audio_item = QTableWidgetItem(str(len(audio_tracks)))
                audio_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.video_table.setItem(i, 2, audio_item)
                
                sub_item = QTableWidgetItem(str(len(subtitle_tracks)))
                sub_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.video_table.setItem(i, 3, sub_item)
                
                attachment_item = QTableWidgetItem(str(len(attachment_tracks)))
                attachment_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.video_table.setItem(i, 4, attachment_item)
                
                title = get_video_title(file_path)
                title_item = QTableWidgetItem(title)
                self.video_table.setItem(i, 5, title_item)
    
    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        source_group = QGroupBox("视频源")
        source_layout = QVBoxLayout()
        
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("视频源："))
        self.source_path_edit = QLineEdit()
        self.source_path_edit.setReadOnly(True)
        self.source_path_edit.setPlaceholderText("选择包含视频文件的文件夹")
        path_layout.addWidget(self.source_path_edit)
        
        self.clear_button = QPushButton("清空")
        self.clear_button.setFixedWidth(60)
        self.clear_button.setIcon(GlobalIcons.ClearIcon.get())
        path_layout.addWidget(self.clear_button)
        
        self.refresh_button = QPushButton("刷新")
        self.refresh_button.setFixedWidth(60)
        self.refresh_button.setIcon(GlobalIcons.RefreshIcon.get())
        path_layout.addWidget(self.refresh_button)
        
        self.browse_button = QPushButton("浏览")
        self.browse_button.setFixedWidth(60)
        self.browse_button.setIcon(GlobalIcons.FolderIcon.get())
        path_layout.addWidget(self.browse_button)
        
        source_layout.addLayout(path_layout)
        
        info_layout = QHBoxLayout()
        self.select_all_checkbox = QCheckBox("全选")
        self.select_all_checkbox.setChecked(True)
        info_layout.addWidget(self.select_all_checkbox)
        
        info_layout.addStretch()
        
        self.extract_tracks_button = QPushButton("轨道提取")
        self.extract_tracks_button.setStyleSheet("background-color: #0078d4; color: white; font-weight: bold;")
        self.extract_tracks_button.setFixedWidth(80)
        info_layout.addWidget(self.extract_tracks_button)
        
        source_layout.addLayout(info_layout)
        
        source_group.setLayout(source_layout)
        main_layout.addWidget(source_group)
        
        table_group = QGroupBox("视频列表")
        table_layout = QVBoxLayout()
        
        self.video_table = QTableWidget()
        self.video_table.setColumnCount(7)
        self.video_table.setHorizontalHeaderLabels(["选择", "文件名", "音轨", "字幕轨", "附件", "视频标题", "大小"])
        self.video_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.video_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.video_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.video_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.video_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        self.video_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)
        self.video_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Fixed)
        self.video_table.setColumnWidth(0, 50)
        self.video_table.setColumnWidth(2, 60)
        self.video_table.setColumnWidth(3, 60)
        self.video_table.setColumnWidth(4, 60)
        self.video_table.setColumnWidth(5, 120)
        self.video_table.setColumnWidth(6, 100)
        
        from PySide6.QtWidgets import QStyledItemDelegate
        class CenterAlignDelegate(QStyledItemDelegate):
            def initStyleOption(self, option, index):
                super().initStyleOption(option, index)
                option.displayAlignment = Qt.AlignmentFlag.AlignCenter
        self.video_table.setItemDelegateForColumn(2, CenterAlignDelegate())
        self.video_table.setItemDelegateForColumn(3, CenterAlignDelegate())
        self.video_table.setItemDelegateForColumn(4, CenterAlignDelegate())
        self.video_table.setItemDelegateForColumn(5, CenterAlignDelegate())
        self.video_table.setItemDelegateForColumn(6, CenterAlignDelegate())
        
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
        self.select_all_checkbox.stateChanged.connect(self.toggle_select_all)
        self.extract_tracks_button.clicked.connect(self.show_extract_tracks_dialog)
    
    def update_selected_indices(self):
        GlobalSetting.VIDEO_SELECTED_INDICES.clear()
        for row in range(self.video_table.rowCount()):
            checkbox_widget = self.video_table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    GlobalSetting.VIDEO_SELECTED_INDICES.append(row)
        self.video_list_updated.emit()
    
    def toggle_select_all(self, state):
        checked = state == Qt.CheckState.Checked.value
        for row in range(self.video_table.rowCount()):
            checkbox_widget = self.video_table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox:
                    checkbox.setChecked(checked)
        self.update_selected_indices()
    
    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择视频源文件夹")
        if folder:
            self.current_source_dir = folder
            self.source_path_edit.setText(folder)
            self.load_videos()
    
    def clear_files(self):
        self.current_source_dir = ""
        self.source_path_edit.clear()
        self.video_table.setRowCount(0)
        GlobalSetting.VIDEO_FILES_LIST.clear()
        GlobalSetting.VIDEO_FILES_ABSOLUTE_PATH_LIST.clear()
        GlobalSetting.VIDEO_FILES_SIZE_LIST.clear()
        GlobalSetting.VIDEO_OLD_TRACKS_VIDEOS_INFO.clear()
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
        GlobalSetting.VIDEO_OLD_TRACKS_VIDEOS_INFO.clear()
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
            
            row = self.video_table.rowCount()
            self.video_table.insertRow(row)
            
            checkbox = QCheckBox()
            checkbox.setChecked(True)
            checkbox.clicked.connect(self.update_selected_indices)
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            self.video_table.setCellWidget(row, 0, checkbox_widget)
            
            self.video_table.setItem(row, 1, QTableWidgetItem(file_name))
            
            audio_item = QTableWidgetItem("...")
            audio_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.video_table.setItem(row, 2, audio_item)
            
            sub_item = QTableWidgetItem("...")
            sub_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.video_table.setItem(row, 3, sub_item)
            
            attachment_item = QTableWidgetItem("...")
            attachment_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.video_table.setItem(row, 4, attachment_item)
            
            title_item = QTableWidgetItem("")
            title_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.video_table.setItem(row, 5, title_item)
            
            size_item = QTableWidgetItem(get_readable_filesize(file_size))
            size_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.video_table.setItem(row, 6, size_item)
        
        if has_mkvmerge:
            self.load_track_info_threaded()
        
        self.update_selected_indices()
    
    def load_track_info_threaded(self):
        def get_track_info(file_path):
            subtitle_tracks = get_subtitle_tracks(file_path)
            audio_tracks = get_audio_tracks(file_path)
            video_tracks = get_video_tracks(file_path)
            attachment_tracks = get_attachments(file_path)
            return subtitle_tracks, audio_tracks, video_tracks, attachment_tracks
        
        file_paths = GlobalSetting.VIDEO_FILES_ABSOLUTE_PATH_LIST.copy()
        total_files = len(file_paths)
        
        temp_subtitles = [None] * total_files
        temp_audios = [None] * total_files
        temp_videos = [None] * total_files
        temp_attachments = [None] * total_files
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {}
            for i, fp in enumerate(file_paths):
                future = executor.submit(get_track_info, fp)
                futures[future] = i
        
            for future in as_completed(futures):
                i = futures[future]
                try:
                    subtitle_tracks, audio_tracks, video_tracks, attachment_tracks = future.result()
                    temp_subtitles[i] = subtitle_tracks
                    temp_audios[i] = audio_tracks
                    temp_videos[i] = video_tracks
                    temp_attachments[i] = attachment_tracks
                    
                    audio_item = QTableWidgetItem(str(len(audio_tracks)))
                    audio_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.video_table.setItem(i, 2, audio_item)
                    
                    sub_item = QTableWidgetItem(str(len(subtitle_tracks)))
                    sub_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.video_table.setItem(i, 3, sub_item)
                    
                    attachment_item = QTableWidgetItem(str(len(attachment_tracks)))
                    attachment_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.video_table.setItem(i, 4, attachment_item)
                    
                    title = get_video_title(file_paths[i])
                    title_item = QTableWidgetItem(title)
                    self.video_table.setItem(i, 5, title_item)
                except Exception as e:
                    logging.warning(f"轨道信息表格设置失败: {e}")
        
        GlobalSetting.VIDEO_OLD_TRACKS_VIDEOS_INFO = temp_videos
        GlobalSetting.VIDEO_OLD_TRACKS_SUBTITLES_INFO = temp_subtitles
        GlobalSetting.VIDEO_OLD_TRACKS_AUDIOS_INFO = temp_audios
        GlobalSetting.VIDEO_OLD_ATTACHMENTS_INFO = temp_attachments
    
    def update_theme_mode_state(self):
        pass
    
    def get_selected_files(self):
        """获取勾选的视频行索引"""
        selected = []
        for row in range(self.video_table.rowCount()):
            checkbox = self.video_table.cellWidget(row, 0)
            if checkbox and checkbox.findChild(QCheckBox).isChecked():
                selected.append(row)
        return selected
    
    def show_extract_tracks_dialog(self):
        """打开轨道提取对话框"""
        if not GlobalSetting.VIDEO_FILES_LIST:
            QMessageBox.warning(self, "警告", "请先添加视频文件")
            return
        
        if not Options.Mkvmerge_Path or not os.path.exists(Options.Mkvmerge_Path):
            QMessageBox.warning(self, "警告", "请先设置 mkvmerge.exe 路径")
            return
        
        selected_rows = self.get_selected_files()
        dialog = ExtractTracksDialog(self, selected_rows)
        dialog.exec()
    
    def refresh_video_list(self):
        if self.source_path_edit.text():
            self.load_videos()
    
    def set_preset_options(self):
        if self.source_path_edit.text():
            self.load_videos()