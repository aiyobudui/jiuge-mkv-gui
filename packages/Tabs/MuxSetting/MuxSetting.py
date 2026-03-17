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
    QProgressBar, QMessageBox
)

from packages.Startup import GlobalIcons
from packages.Startup.Options import Options
from packages.Tabs.GlobalSetting import GlobalSetting, get_readable_filesize
from packages.Tabs.MuxSetting.TrackSelectionDialog import TrackSelectionDialog


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
        self.track_selections = {
            'audio': {}, 
            'subtitle': {}, 
            'default_audio': {}, 
            'default_subtitle': {},
            'external_audio': {},
            'external_subtitle': {},
            'audio_languages': {},
            'subtitle_languages': {}
        }
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
        
        output_layout.addWidget(QLabel("输出格式："))
        self.output_format_combo = QComboBox()
        self.output_format_combo.addItems(["MP4", "MKV"])
        self.output_format_combo.setFixedWidth(80)
        output_layout.addWidget(self.output_format_combo)
        
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
        
        button_group.setLayout(button_layout)
        top_layout.addWidget(button_group)
        
        main_layout.addLayout(top_layout)
        
        options_group = QGroupBox("混流选项")
        options_layout = QHBoxLayout()
        
        self.add_crc_check = QCheckBox("CRC校验")
        options_layout.addWidget(self.add_crc_check)
        self.remove_crc_check = QCheckBox("移除旧CRC")
        options_layout.addWidget(self.remove_crc_check)
        
        self.keep_log_check = QCheckBox("保留日志")
        options_layout.addWidget(self.keep_log_check)
        self.abort_on_error_check = QCheckBox("出错中止")
        self.abort_on_error_check.setChecked(True)
        options_layout.addWidget(self.abort_on_error_check)
        
        options_layout.addStretch()
        
        options_layout.addWidget(QLabel("轨道选择："))
        self.track_select_button = QPushButton("选择想要保留的轨道")
        self.track_select_button.setFixedWidth(150)
        self.track_select_button.setEnabled(False)
        self.track_select_button.setStyleSheet("""
            QPushButton {
                background-color: #e0e0e0;
                color: #999999;
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
            }
        """)
        options_layout.addWidget(self.track_select_button)
        
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
        progress_layout.addWidget(QLabel("总进度"))
        self.total_progress_bar = QProgressBar()
        self.total_progress_bar.setTextVisible(True)
        self.total_progress_bar.setFormat("%p% - %v/%m")
        progress_layout.addWidget(self.total_progress_bar)
        progress_group = QWidget()
        progress_group.setLayout(progress_layout)
        main_layout.addWidget(progress_group)
        
        self.setLayout(main_layout)
    
    def connect_signals(self):
        self.browse_output_button.clicked.connect(self.browse_output_folder)
        self.clear_all_button.clicked.connect(self.clear_all_tasks)
        self.add_to_queue_button.clicked.connect(self.add_to_queue)
        self.start_button.clicked.connect(self.toggle_muxing)
        
        self.update_task_signal.connect(self.on_update_task)
        self.update_progress_signal.connect(self.on_update_progress)
        self.muxing_finished_signal.connect(self.on_muxing_finished)
        
        self.track_select_button.clicked.connect(self.show_track_selection_dialog)
    
    def show_track_selection_dialog(self):
        if not GlobalSetting.VIDEO_FILES_LIST:
            QMessageBox.warning(self, "警告", "请先添加视频文件")
            return
        dialog = TrackSelectionDialog(self)
        if dialog.exec():
            selections = dialog.get_selections()
            self.track_selections['audio'] = selections['audio']
            self.track_selections['subtitle'] = selections['subtitle']
            self.track_selections['default_audio'] = selections['default_audio']
            self.track_selections['default_subtitle'] = selections['default_subtitle']
            self.track_selections['external_audio'] = selections['external_audio']
            self.track_selections['external_subtitle'] = selections['external_subtitle']
            self.track_selections['audio_languages'] = selections['audio_languages']
            self.track_selections['subtitle_languages'] = selections['subtitle_languages']
    
    def on_update_task(self, row, status, progress, output_size):
        if row < self.task_table.rowCount():
            self.task_table.setItem(row, 1, QTableWidgetItem(status))
            self.task_table.setItem(row, 3, QTableWidgetItem(progress))
            self.task_table.setItem(row, 4, QTableWidgetItem(output_size))
    
    def on_update_progress(self, progress, text):
        self.total_progress_bar.setMaximum(100)
        self.total_progress_bar.setValue(progress)
        self.total_progress_bar.setFormat(f"%p% - {text}")
    
    def on_muxing_finished(self):
        self.set_button_state(is_muxing=False)
        GlobalSetting.MUXING_ON = False
        GlobalSetting.JOB_QUEUE_FINISHED = True
        
        success_count = sum(1 for i in range(self.task_table.rowCount()) 
                          if self.task_table.item(i, 1) and self.task_table.item(i, 1).text() == "成功")
        fail_count = self.task_table.rowCount() - success_count
        
        self.total_progress_bar.setValue(100)
        if fail_count == 0:
            self.total_progress_bar.setFormat(f"100% - 完成！成功: {success_count}")
        else:
            self.total_progress_bar.setFormat(f"100% - 完成！成功: {success_count}，失败: {fail_count}")
    
    def set_button_state(self, is_muxing):
        if is_muxing:
            self.start_button.setText("停止混流")
            self.start_button.setStyleSheet("background-color: #d13438; color: white; font-weight: bold;")
            self.clear_all_button.setEnabled(False)
            self.add_to_queue_button.setEnabled(False)
        else:
            self.start_button.setText("开始混流")
            self.start_button.setStyleSheet("background-color: #0078d4; color: white; font-weight: bold;")
            self.clear_all_button.setEnabled(True)
            self.add_to_queue_button.setEnabled(True)
    
    def toggle_muxing(self):
        if GlobalSetting.MUXING_ON:
            self.stop_muxing()
        else:
            self.start_muxing()
    
    def browse_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择输出文件夹")
        if folder:
            self.output_path_edit.setText(folder)
    
    def clear_all_tasks(self):
        self.task_table.setRowCount(0)
        self.track_selections = {
            'audio': {}, 
            'subtitle': {}, 
            'default_audio': {}, 
            'default_subtitle': {},
            'external_audio': {},
            'external_subtitle': {},
            'audio_languages': {},
            'subtitle_languages': {}
        }
        self.track_select_button.setEnabled(False)
        self.track_select_button.setStyleSheet("""
            QPushButton {
                background-color: #e0e0e0;
                color: #999999;
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
            }
        """)
    
    def update_track_menus(self):
        self.track_selections = {
            'audio': {}, 
            'subtitle': {}, 
            'default_audio': {}, 
            'default_subtitle': {},
            'external_audio': {},
            'external_subtitle': {},
            'audio_languages': {},
            'subtitle_languages': {}
        }
    
    def get_selected_audio_tracks(self):
        result = {}
        if self.track_selections['audio']:
            for video_idx, track_ids in self.track_selections['audio'].items():
                result[video_idx] = track_ids
        return result
    
    def get_selected_subtitle_tracks(self):
        result = {}
        if self.track_selections['subtitle']:
            for video_idx, track_ids in self.track_selections['subtitle'].items():
                result[video_idx] = track_ids
        return result
    
    def add_to_queue(self):
        if not GlobalSetting.VIDEO_FILES_LIST:
            QMessageBox.warning(self, "警告", "请先在视频选项卡中添加视频文件")
            return
        
        self.update_track_menus()
        
        self.task_table.setRowCount(0)
        
        for video_idx in GlobalSetting.VIDEO_SELECTED_INDICES:
            if video_idx < len(GlobalSetting.VIDEO_FILES_LIST):
                video_name = GlobalSetting.VIDEO_FILES_LIST[video_idx]
                video_size = get_readable_filesize(GlobalSetting.VIDEO_FILES_SIZE_LIST[video_idx])
                
                row = self.task_table.rowCount()
                self.task_table.insertRow(row)
                self.task_table.setItem(row, 0, QTableWidgetItem(video_name))
                self.task_table.setItem(row, 1, QTableWidgetItem("等待中"))
                self.task_table.setItem(row, 2, QTableWidgetItem(video_size))
                self.task_table.setItem(row, 3, QTableWidgetItem("0%"))
                self.task_table.setItem(row, 4, QTableWidgetItem("-"))
        
        self.total_tasks = self.task_table.rowCount()
        self.completed_count = 0
        
        self.track_select_button.setEnabled(True)
        self.track_select_button.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: 1px solid #006cbd;
                border-radius: 4px;
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
        """)
    
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
        
        self.set_button_state(is_muxing=True)
        GlobalSetting.MUXING_ON = True
        self.stop_requested = False
        self.completed_count = 0
        
        self.start_muxing_signal.emit()
        
        thread_count = 4
        self.muxing_thread = threading.Thread(target=self.run_muxing_tasks_parallel, args=(thread_count,), daemon=True)
        self.muxing_thread.start()
    
    def run_muxing_tasks_parallel(self, thread_count):
        total_tasks = self.task_table.rowCount()
        self.update_progress_signal.emit(0, f"正在处理 0/{total_tasks}")
        
        futures = {}
        completed = [0]
        lock = threading.Lock()
        
        with ThreadPoolExecutor(max_workers=thread_count) as executor:
            for i in range(total_tasks):
                if self.stop_requested:
                    break
                
                video_path = GlobalSetting.VIDEO_FILES_ABSOLUTE_PATH_LIST[i]
                output_path = self.get_output_path(video_path)
                args = self.build_mkvmerge_args(i, video_path, output_path)
                
                future = executor.submit(self.process_single_task, i, args)
                futures[future] = i
            
            for future in as_completed(futures):
                task_index = futures[future]
                try:
                    success, output_size = future.result()
                    if success:
                        self.update_task_signal.emit(task_index, "成功", "100%", output_size)
                    else:
                        self.update_task_signal.emit(task_index, "失败", "0%", "-")
                except Exception:
                    self.update_task_signal.emit(task_index, "失败", "0%", "-")
                
                with lock:
                    completed[0] += 1
                progress = int((completed[0] / total_tasks) * 100)
                self.update_progress_signal.emit(progress, f"正在处理 {completed[0]}/{total_tasks}")
        
        if not self.stop_requested:
            self.muxing_finished_signal.emit()
    
    def stop_muxing(self):
        self.stop_requested = True
        GlobalSetting.MUXING_ON = False
        self.set_button_state(is_muxing=False)
    
    def process_single_task(self, task_index, args):
        self.update_task_signal.emit(task_index, "执行中", "50%", "-")
        
        try:
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            
            result = subprocess.run(
                [Options.Mkvmerge_Path] + args,
                capture_output=True,
                encoding='utf-8',
                errors='replace',
                creationflags=subprocess.CREATE_NO_WINDOW,
                env=env
            )
            
            if result.returncode in [0, 1]:
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
            output_format = self.output_format_combo.currentText().lower()
            return os.path.join(output_dir, video_name + "." + output_format)
        else:
            return video_path
    
    def build_mkvmerge_args(self, video_index, video_path, output_path):
        args = ['-o', output_path]
        
        selected_audio = self.get_selected_audio_tracks()
        if video_index in selected_audio:
            if selected_audio[video_index]:
                tracks_str = ','.join(str(t) for t in selected_audio[video_index])
                args.extend(['--audio-tracks', tracks_str])
            else:
                args.append('--no-audio')
        else:
            video_audios = GlobalSetting.VIDEO_OLD_TRACKS_AUDIOS_INFO[video_index] if video_index < len(GlobalSetting.VIDEO_OLD_TRACKS_AUDIOS_INFO) else []
            if video_audios:
                tracks_str = ','.join(str(track.get('id', i)) for i, track in enumerate(video_audios))
                args.extend(['--audio-tracks', tracks_str])
        
        selected_subtitle = self.get_selected_subtitle_tracks()
        sub_list = GlobalSetting.SUBTITLE_FILES_ABSOLUTE_PATH_LIST.get(video_index, [])
        if video_index in selected_subtitle:
            if selected_subtitle[video_index]:
                tracks_str = ','.join(str(t) for t in selected_subtitle[video_index])
                args.extend(['--subtitle-tracks', tracks_str])
            else:
                args.append('--no-subtitles')
        else:
            video_subs = GlobalSetting.VIDEO_OLD_TRACKS_SUBTITLES_INFO[video_index] if video_index < len(GlobalSetting.VIDEO_OLD_TRACKS_SUBTITLES_INFO) else []
            if video_subs:
                tracks_str = ','.join(str(track.get('id', i)) for i, track in enumerate(video_subs))
                args.extend(['--subtitle-tracks', tracks_str])
        
        video_subs_info = []
        if video_index < len(GlobalSetting.VIDEO_OLD_TRACKS_SUBTITLES_INFO):
            video_subs_info = GlobalSetting.VIDEO_OLD_TRACKS_SUBTITLES_INFO[video_index] or []
        
        video_audios_info = []
        if video_index < len(GlobalSetting.VIDEO_OLD_TRACKS_AUDIOS_INFO):
            video_audios_info = GlobalSetting.VIDEO_OLD_TRACKS_AUDIOS_INFO[video_index] or []
        
        default_sub_info = self.track_selections.get('default_subtitle', {}).get(video_index, {})
        default_sub_idx = default_sub_info.get('idx', -1) if isinstance(default_sub_info, dict) else -1
        default_sub_external = default_sub_info.get('external', False) if isinstance(default_sub_info, dict) else False
        
        sub_languages = self.track_selections.get('subtitle_languages', {}).get(video_index, {})
        
        for i, track in enumerate(video_subs_info):
            track_id = track.get('id', i)
            new_lang = sub_languages.get(i)
            if new_lang:
                args.extend(['--language', f'{track_id}:{new_lang}'])
            if not default_sub_external and i == default_sub_idx:
                args.extend(['--default-track', f'{track_id}:yes'])
            else:
                args.extend(['--default-track', f'{track_id}:no'])
        
        default_audio_info = self.track_selections.get('default_audio', {}).get(video_index, {})
        default_audio_idx = default_audio_info.get('idx', -1) if isinstance(default_audio_info, dict) else -1
        default_audio_external = default_audio_info.get('external', False) if isinstance(default_audio_info, dict) else False
        
        audio_languages = self.track_selections.get('audio_languages', {}).get(video_index, {})
        
        for i, track in enumerate(video_audios_info):
            track_id = track.get('id', i)
            new_lang = audio_languages.get(i)
            if new_lang:
                args.extend(['--language', f'{track_id}:{new_lang}'])
            if not default_audio_external and i == default_audio_idx:
                args.extend(['--default-track', f'{track_id}:yes'])
            else:
                args.extend(['--default-track', f'{track_id}:no'])
        
        attachment_list = GlobalSetting.ATTACHMENT_FILES_ABSOLUTE_PATH_LIST.get(video_index, [])
        if attachment_list:
            for attachment_path in attachment_list:
                if os.path.exists(attachment_path):
                    ext = os.path.splitext(attachment_path)[1].lower()
                    mime_type = self.get_attachment_mime_type(ext)
                    args.extend(['--attachment-name', 'cover' + ext])
                    args.extend(['--attachment-mime-type', mime_type])
                    args.extend(['--attach-file', attachment_path])
        
        args.append(video_path)
        
        if sub_list:
            for i, sub_path in enumerate(sub_list):
                ext_lang = sub_languages.get(f'ext_{i}', 'chi')
                args.extend(['--language', f'0:{ext_lang}'])
                if default_sub_external and f'ext_{i}' == default_sub_idx:
                    args.extend(['--default-track', '0:yes'])
                else:
                    args.extend(['--default-track', '0:no'])
                args.append(sub_path)
        
        audio_list = GlobalSetting.AUDIO_FILES_ABSOLUTE_PATH_LIST.get(video_index, [])
        if audio_list:
            for i, audio_path in enumerate(audio_list):
                ext_lang = audio_languages.get(f'ext_{i}', 'chi')
                args.extend(['--language', f'0:{ext_lang}'])
                if default_audio_external and f'ext_{i}' == default_audio_idx:
                    args.extend(['--default-track', '0:yes'])
                else:
                    args.extend(['--default-track', '0:no'])
                args.append(audio_path)
        
        return args
    
    def get_attachment_mime_type(self, ext):
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp',
            '.webp': 'image/webp',
            '.ttf': 'font/ttf',
            '.otf': 'font/otf',
            '.woff': 'font/woff',
            '.woff2': 'font/woff2',
        }
        return mime_types.get(ext, 'application/octet-stream')
    
    def update_theme_mode_state(self):
        pass
    
    def set_preset_options(self):
        self.update_track_menus()
