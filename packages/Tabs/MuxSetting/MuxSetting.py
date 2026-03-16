# -*- coding: utf-8 -*-
import os
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QFileDialog, QGroupBox, QCheckBox,
    QProgressBar, QMessageBox, QSpinBox, QMenu, QToolButton
)

from packages.Startup import GlobalIcons
from packages.Startup.Options import Options
from packages.Tabs.GlobalSetting import GlobalSetting, get_readable_filesize


class CheckableComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.checked_items = []
        self.item_changed = Signal()
    
    def add_items_with_check(self, items):
        self.clear()
        self.checked_items = []
        for i, item in enumerate(items):
            self.addItem(item)
            self.setItemData(i, Qt.Unchecked, Qt.CheckStateRole)
    
    def item_checked(self, index):
        return self.itemData(index, Qt.CheckStateRole) == Qt.Checked
    
    def set_item_checked(self, index, checked):
        self.setItemData(index, Qt.Checked if checked else Qt.Unchecked, Qt.CheckStateRole)
    
    def get_checked_indices(self):
        return [i for i in range(self.count()) if self.item_checked(i)]
    
    def hidePopup(self):
        pass


class MuxSettingTab(QWidget):
    start_muxing_signal = Signal()
    update_task_bar_progress_signal = Signal(int)
    update_task_signal = Signal(int, str, str, str)
    update_progress_signal = Signal(int, str)
    muxing_finished_signal = Signal()
    
    def __init__(self):
        super().__init__()
        self.subtitle_track_items = []
        self.audio_track_items = []
        self.setup_ui()
        self.connect_signals()
        self.total_tasks = 0
        self.stop_requested = False
        self.completed_count = 0
        self.count_lock = threading.Lock()
    
    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        top_layout = QHBoxLayout()
        
        output_group = QGroupBox("输出设置")
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("输出目录："))
        self.output_path_edit = QLineEdit()
        self.output_path_edit.setReadOnly(True)
        self.output_path_edit.setPlaceholderText("请选择输出文件夹")
        output_layout.addWidget(self.output_path_edit)
        
        self.browse_output_button = QPushButton("浏览")
        self.browse_output_button.setFixedWidth(60)
        output_layout.addWidget(self.browse_output_button)
        
        output_group.setLayout(output_layout)
        top_layout.addWidget(output_group)
        
        button_group = QGroupBox("操作按钮")
        button_layout = QHBoxLayout()
        self.clear_all_button = QPushButton("清空全部")
        self.clear_all_button.setFixedWidth(80)
        button_layout.addWidget(self.clear_all_button)
        
        self.add_to_queue_button = QPushButton("添加到队列")
        self.add_to_queue_button.setFixedWidth(100)
        button_layout.addWidget(self.add_to_queue_button)
        
        button_layout.addSpacing(20)
        
        self.start_button = QPushButton("开始混流")
        self.start_button.setFixedWidth(100)
        self.start_button.setStyleSheet("background-color: #0078d4; color: white; font-weight: bold;")
        button_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("停止")
        self.stop_button.setFixedWidth(60)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        
        button_group.setLayout(button_layout)
        top_layout.addWidget(button_group)
        
        main_layout.addLayout(top_layout)
        
        options_group = QGroupBox("混流选项")
        options_layout = QVBoxLayout()
        
        row1_layout = QHBoxLayout()
        self.keep_subtitle_check = QCheckBox("保留字幕")
        self.keep_subtitle_check.setChecked(True)
        row1_layout.addWidget(self.keep_subtitle_check)
        
        self.subtitle_select_button = QPushButton("选择字幕轨...")
        self.subtitle_select_button.setFixedWidth(120)
        self.subtitle_select_menu = QMenu(self)
        self.subtitle_select_button.setMenu(self.subtitle_select_menu)
        row1_layout.addWidget(self.subtitle_select_button)
        
        row1_layout.addWidget(QLabel("默认："))
        self.default_subtitle_combo = QComboBox()
        self.default_subtitle_combo.addItem("读取视频文件的默认字幕")
        self.default_subtitle_combo.setFixedWidth(200)
        row1_layout.addWidget(self.default_subtitle_combo)
        
        row1_layout.addSpacing(20)
        
        self.add_crc_check = QCheckBox("CRC校验")
        row1_layout.addWidget(self.add_crc_check)
        self.remove_crc_check = QCheckBox("移除旧CRC")
        row1_layout.addWidget(self.remove_crc_check)
        
        row1_layout.addStretch()
        options_layout.addLayout(row1_layout)
        
        row2_layout = QHBoxLayout()
        self.keep_audio_check = QCheckBox("保留音轨")
        self.keep_audio_check.setChecked(True)
        row2_layout.addWidget(self.keep_audio_check)
        
        self.audio_select_button = QPushButton("选择音轨...")
        self.audio_select_button.setFixedWidth(120)
        self.audio_select_menu = QMenu(self)
        self.audio_select_button.setMenu(self.audio_select_menu)
        row2_layout.addWidget(self.audio_select_button)
        
        row2_layout.addWidget(QLabel("默认："))
        self.default_audio_combo = QComboBox()
        self.default_audio_combo.addItem("读取视频文件的默认音轨")
        self.default_audio_combo.setFixedWidth(200)
        row2_layout.addWidget(self.default_audio_combo)
        
        row2_layout.addSpacing(20)
        
        self.keep_log_check = QCheckBox("保留日志")
        row2_layout.addWidget(self.keep_log_check)
        self.abort_on_error_check = QCheckBox("出错中止")
        self.abort_on_error_check.setChecked(True)
        row2_layout.addWidget(self.abort_on_error_check)
        
        row2_layout.addStretch()
        options_layout.addLayout(row2_layout)
        
        options_group.setLayout(options_layout)
        main_layout.addWidget(options_group)
        
        queue_group = QGroupBox("任务队列")
        queue_layout = QVBoxLayout()
        
        self.task_table = QTableWidget()
        self.task_table.setColumnCount(5)
        self.task_table.setHorizontalHeaderLabels(["名称", "状态", "处理前大小", "进度", "处理后大小"])
        self.task_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.task_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.task_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.task_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.task_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        self.task_table.setColumnWidth(1, 80)
        self.task_table.setColumnWidth(2, 100)
        self.task_table.setColumnWidth(3, 80)
        self.task_table.setColumnWidth(4, 100)
        self.task_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.task_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        queue_layout.addWidget(self.task_table)
        queue_group.setLayout(queue_layout)
        main_layout.addWidget(queue_group)
        
        progress_layout = QHBoxLayout()
        progress_layout.addWidget(QLabel("总进度："))
        self.total_progress_bar = QProgressBar()
        self.total_progress_bar.setFixedWidth(200)
        progress_layout.addWidget(self.total_progress_bar)
        
        self.progress_label = QLabel("已完成：0/00")
        progress_layout.addWidget(self.progress_label)
        progress_layout.addStretch()
        main_layout.addLayout(progress_layout)
        
        self.setLayout(main_layout)
    
    def connect_signals(self):
        self.browse_output_button.clicked.connect(self.browse_output_folder)
        self.clear_all_button.clicked.connect(self.clear_all_tasks)
        self.add_to_queue_button.clicked.connect(self.add_to_queue)
        self.start_button.clicked.connect(self.start_muxing)
        self.stop_button.clicked.connect(self.stop_muxing)
        
        self.update_task_signal.connect(self.on_update_task)
        self.update_progress_signal.connect(self.on_update_progress)
        self.muxing_finished_signal.connect(self.on_muxing_finished)
        
        self.keep_audio_check.stateChanged.connect(self.on_keep_audio_changed)
        self.keep_subtitle_check.stateChanged.connect(self.on_keep_subtitle_changed)
    
    def on_keep_audio_changed(self, state):
        pass
    
    def on_keep_subtitle_changed(self, state):
        pass
    
    def on_update_task(self, row, status, progress, output_size):
        if row < self.task_table.rowCount():
            self.task_table.setItem(row, 1, QTableWidgetItem(status))
            self.task_table.setItem(row, 3, QTableWidgetItem(progress))
            self.task_table.setItem(row, 4, QTableWidgetItem(output_size))
    
    def on_update_progress(self, progress, text):
        self.total_progress_bar.setValue(progress)
        self.progress_label.setText(text)
    
    def on_muxing_finished(self):
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        GlobalSetting.MUXING_ON = False
        GlobalSetting.JOB_QUEUE_FINISHED = True
        
        success_count = sum(1 for i in range(self.task_table.rowCount()) 
                          if self.task_table.item(i, 1) and self.task_table.item(i, 1).text() == "成功")
        fail_count = self.task_table.rowCount() - success_count
        
        QMessageBox.information(
            self,
            "完成",
            f"混流完成！\n成功: {success_count}\n失败: {fail_count}"
        )
    
    def browse_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if folder:
            self.output_path_edit.setText(folder)
    
    def clear_all_tasks(self):
        self.task_table.setRowCount(0)
        self.total_progress_bar.setValue(0)
        self.progress_label.setText("已完成：0/0")
        self.total_tasks = 0
        self.completed_count = 0
    
    def update_track_menus(self):
        self.subtitle_select_menu.clear()
        self.audio_select_menu.clear()
        self.default_audio_combo.clear()
        self.default_subtitle_combo.clear()
        
        self.subtitle_track_items = []
        self.audio_track_items = []
        
        default_audio_display = "无默认音轨"
        default_subtitle_display = "无默认字幕"
        
        if GlobalSetting.VIDEO_OLD_TRACKS_SUBTITLES_INFO and len(GlobalSetting.VIDEO_OLD_TRACKS_SUBTITLES_INFO) > 0:
            first_video_subs = GlobalSetting.VIDEO_OLD_TRACKS_SUBTITLES_INFO[0]
            if first_video_subs:
                for i, track in enumerate(first_video_subs):
                    lang = track.get('language', 'und')
                    name = track.get('name', '')
                    is_default = track.get('is_default', False)
                    display = f"#{i} [{lang}]"
                    if name:
                        display += f" {name}"
                    
                    action = self.subtitle_select_menu.addAction(display)
                    action.setCheckable(True)
                    action.setChecked(True)
                    self.subtitle_track_items.append(action)
                    
                    self.default_subtitle_combo.addItem(display)
                    
                    if is_default:
                        default_subtitle_display = display
        
        first_video_sub_list = GlobalSetting.SUBTITLE_FILES_ABSOLUTE_PATH_LIST.get(0, [])
        if first_video_sub_list:
            for i, sub_path in enumerate(first_video_sub_list):
                sub_name = os.path.splitext(os.path.basename(sub_path))[0]
                display = f"外部字幕 #{i} {sub_name}"
                
                action = self.subtitle_select_menu.addAction(display)
                action.setCheckable(True)
                action.setChecked(True)
                self.subtitle_track_items.append(action)
                
                self.default_subtitle_combo.addItem(display)
        
        if self.default_subtitle_combo.count() == 0:
            self.default_subtitle_combo.addItem("无字幕轨道")
        
        if GlobalSetting.VIDEO_OLD_TRACKS_AUDIOS_INFO and len(GlobalSetting.VIDEO_OLD_TRACKS_AUDIOS_INFO) > 0:
            first_video_audios = GlobalSetting.VIDEO_OLD_TRACKS_AUDIOS_INFO[0]
            if first_video_audios:
                for i, track in enumerate(first_video_audios):
                    lang = track.get('language', 'und')
                    name = track.get('name', '')
                    is_default = track.get('is_default', False)
                    display = f"#{i} [{lang}]"
                    if name:
                        display += f" {name}"
                    
                    action = self.audio_select_menu.addAction(display)
                    action.setCheckable(True)
                    action.setChecked(True)
                    self.audio_track_items.append(action)
                    
                    self.default_audio_combo.addItem(display)
                    
                    if is_default:
                        default_audio_display = display
        
        first_video_audio_list = GlobalSetting.AUDIO_FILES_ABSOLUTE_PATH_LIST.get(0, [])
        if first_video_audio_list:
            for i, audio_path in enumerate(first_video_audio_list):
                audio_name = os.path.splitext(os.path.basename(audio_path))[0]
                display = f"外部音轨 #{i} {audio_name}"
                
                action = self.audio_select_menu.addAction(display)
                action.setCheckable(True)
                action.setChecked(True)
                self.audio_track_items.append(action)
                
                self.default_audio_combo.addItem(display)
        
        if self.default_audio_combo.count() == 0:
            self.default_audio_combo.addItem("无音轨轨道")
        
        self.default_audio_combo.setCurrentText(default_audio_display)
        self.default_subtitle_combo.setCurrentText(default_subtitle_display)
    
    def get_selected_audio_tracks(self):
        if not self.keep_audio_check.isChecked():
            return {}
        result = {}
        if GlobalSetting.VIDEO_OLD_TRACKS_AUDIOS_INFO and len(GlobalSetting.VIDEO_OLD_TRACKS_AUDIOS_INFO) > 0:
            first_video_audios = GlobalSetting.VIDEO_OLD_TRACKS_AUDIOS_INFO[0]
            if first_video_audios:
                selected_tracks = []
                for i in range(len(first_video_audios)):
                    if i < len(self.audio_track_items) and self.audio_track_items[i].isChecked():
                        selected_tracks.append(i)
                if not selected_tracks:
                    selected_tracks = list(range(len(first_video_audios)))
                for video_idx in range(len(GlobalSetting.VIDEO_FILES_LIST)):
                    result[video_idx] = selected_tracks.copy()
        return result
    
    def get_selected_subtitle_tracks(self):
        if not self.keep_subtitle_check.isChecked():
            return {}
        result = {}
        if GlobalSetting.VIDEO_OLD_TRACKS_SUBTITLES_INFO and len(GlobalSetting.VIDEO_OLD_TRACKS_SUBTITLES_INFO) > 0:
            first_video_subs = GlobalSetting.VIDEO_OLD_TRACKS_SUBTITLES_INFO[0]
            if first_video_subs:
                selected_tracks = []
                for i in range(len(first_video_subs)):
                    if i < len(self.subtitle_track_items) and self.subtitle_track_items[i].isChecked():
                        selected_tracks.append(i)
                if not selected_tracks:
                    selected_tracks = list(range(len(first_video_subs)))
                for video_idx in range(len(GlobalSetting.VIDEO_FILES_LIST)):
                    result[video_idx] = selected_tracks.copy()
        return result
    
    def add_to_queue(self):
        if not GlobalSetting.VIDEO_FILES_LIST:
            QMessageBox.warning(self, "警告", "请先在视频选项卡中添加视频文件")
            return
        
        self.update_track_menus()
        
        self.task_table.setRowCount(0)
        
        for i in range(len(GlobalSetting.VIDEO_FILES_LIST)):
            video_name = GlobalSetting.VIDEO_FILES_LIST[i]
            video_size = get_readable_filesize(GlobalSetting.VIDEO_FILES_SIZE_LIST[i])
            
            row = self.task_table.rowCount()
            self.task_table.insertRow(row)
            self.task_table.setItem(row, 0, QTableWidgetItem(video_name))
            self.task_table.setItem(row, 1, QTableWidgetItem("等待中"))
            self.task_table.setItem(row, 2, QTableWidgetItem(video_size))
            self.task_table.setItem(row, 3, QTableWidgetItem("0%"))
            self.task_table.setItem(row, 4, QTableWidgetItem("-"))
        
        self.total_tasks = self.task_table.rowCount()
        self.completed_count = 0
        self.progress_label.setText(f"已完成：0/{self.total_tasks}")
    
    def start_muxing(self):
        if self.task_table.rowCount() == 0:
            QMessageBox.warning(self, "警告", "请先添加任务到队列")
            return
        
        if not Options.Mkvmerge_Path or not os.path.exists(Options.Mkvmerge_Path):
            QMessageBox.warning(self, "警告", "请先设置 mkvmerge.exe 路径")
            return
        
        output_dir = self.output_path_edit.text()
        if not output_dir:
            QMessageBox.warning(self, "警告", "请先设置输出目录")
            return
        
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        GlobalSetting.MUXING_ON = True
        self.stop_requested = False
        self.completed_count = 0
        
        self.start_muxing_signal.emit()
        
        thread_count = 4
        self.muxing_thread = threading.Thread(target=self.run_muxing_tasks_parallel, args=(thread_count,), daemon=True)
        self.muxing_thread.start()
        
    def run_muxing_tasks_parallel(self, thread_count):
        futures = {}
        with ThreadPoolExecutor(max_workers=thread_count) as executor:
            for i in range(self.task_table.rowCount()):
                if self.stop_requested:
                    break
                
                video_path = GlobalSetting.VIDEO_FILES_ABSOLUTE_PATH_LIST[i]
                output_path = self.get_output_path(video_path)
                args = self.build_mkvmerge_args(i, video_path, output_path)
                
                future = executor.submit(self.process_single_task, i, args)
                futures[future] = i
            
            for future in as_completed(futures):
                if not self.stop_requested:
                    self.muxing_finished_signal.emit()
    
    def stop_muxing(self):
        self.stop_requested = True
        GlobalSetting.MUXING_ON = False
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
    
    def process_single_task(self, task_index, args):
        self.update_task_signal.emit(task_index, "执行中", "50%", "-")
        
        try:
            result = subprocess.run(
                [Options.Mkvmerge_Path] + args,
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode == 0:
                output_path = args[1]
                if os.path.exists(output_path):
                    output_size = get_readable_filesize(os.path.getsize(output_path))
                else:
                    output_size = "-"
                return True, output_size
            else:
                return False, "-"
        except Exception:
            return False, "-"
    
    def get_output_path(self, video_path):
        output_dir = self.output_path_edit.text()
        if output_dir:
            video_name = os.path.splitext(os.path.basename(video_path))[0]
            return os.path.join(output_dir, video_name + ".mkv")
        else:
            return video_path
    
    def build_mkvmerge_args(self, video_index, video_path, output_path):
        args = ['-o', output_path]
        
        selected_audio = self.get_selected_audio_tracks()
        if selected_audio and video_index in selected_audio and selected_audio[video_index]:
            tracks_str = ','.join(str(t) for t in selected_audio[video_index])
            args.extend(['--audio-tracks', tracks_str])
        elif not self.keep_audio_check.isChecked():
            args.append('--no-audio')
        
        selected_subtitle = self.get_selected_subtitle_tracks()
        sub_list = GlobalSetting.SUBTITLE_FILES_ABSOLUTE_PATH_LIST.get(video_index, [])
        
        if selected_subtitle and video_index in selected_subtitle and selected_subtitle[video_index]:
            tracks_str = ','.join(str(t) for t in selected_subtitle[video_index])
            args.extend(['--subtitle-tracks', tracks_str])
        elif not self.keep_subtitle_check.isChecked() and not sub_list:
            args.append('--no-subtitles')
        
        video_subs_count = 0
        if video_index < len(GlobalSetting.VIDEO_OLD_TRACKS_SUBTITLES_INFO):
            video_subs_count = len(GlobalSetting.VIDEO_OLD_TRACKS_SUBTITLES_INFO[video_index])
        
        video_audios_count = 0
        if video_index < len(GlobalSetting.VIDEO_OLD_TRACKS_AUDIOS_INFO):
            video_audios_count = len(GlobalSetting.VIDEO_OLD_TRACKS_AUDIOS_INFO[video_index])
        
        sub_track = self.default_subtitle_combo.currentIndex()
        first_video_subs = len(GlobalSetting.VIDEO_OLD_TRACKS_SUBTITLES_INFO[0]) if GlobalSetting.VIDEO_OLD_TRACKS_SUBTITLES_INFO else 0
        
        audio_track = self.default_audio_combo.currentIndex()
        first_video_audios = len(GlobalSetting.VIDEO_OLD_TRACKS_AUDIOS_INFO[0]) if GlobalSetting.VIDEO_OLD_TRACKS_AUDIOS_INFO else 0
        
        for i in range(video_subs_count):
            if sub_track >= 0 and sub_track < first_video_subs:
                if i == sub_track:
                    args.extend(['--default-track', f'{i}:yes'])
                else:
                    args.extend(['--default-track', f'{i}:no'])
            elif sub_track >= first_video_subs:
                args.extend(['--default-track', f'{i}:no'])
        
        for i in range(video_audios_count):
            if audio_track >= 0 and audio_track < first_video_audios:
                if i == audio_track:
                    args.extend(['--default-track', f'{i}:yes'])
                else:
                    args.extend(['--default-track', f'{i}:no'])
            elif audio_track >= first_video_audios:
                args.extend(['--default-track', f'{i}:no'])
        
        args.append(video_path)
        
        if sub_list:
            for i, sub_path in enumerate(sub_list):
                lang = GlobalSetting.SUBTITLE_LANGUAGE.get(video_index, 'chi')
                args.extend(['--language', f'0:{lang}'])
                if sub_track >= first_video_subs:
                    external_sub_index = sub_track - first_video_subs
                    if i == external_sub_index:
                        args.extend(['--default-track', '0:yes'])
                    else:
                        args.extend(['--default-track', '0:no'])
                else:
                    args.extend(['--default-track', '0:no'])
                args.append(sub_path)
        
        audio_list = GlobalSetting.AUDIO_FILES_ABSOLUTE_PATH_LIST.get(video_index, [])
        if audio_list:
            for i, audio_path in enumerate(audio_list):
                lang = GlobalSetting.AUDIO_LANGUAGE.get(video_index, 'chi')
                args.extend(['--language', f'0:{lang}'])
                if audio_track >= first_video_audios:
                    external_audio_index = audio_track - first_video_audios
                    if i == external_audio_index:
                        args.extend(['--default-track', '0:yes'])
                    else:
                        args.extend(['--default-track', '0:no'])
                else:
                    args.extend(['--default-track', '0:no'])
                args.append(audio_path)
        
        return args
    
    def update_theme_mode_state(self):
        pass
    
    def set_preset_options(self):
        self.update_track_menus()
