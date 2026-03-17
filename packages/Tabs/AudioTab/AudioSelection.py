# -*- coding: utf-8 -*-
import os
from PySide6.QtCore import Signal, Qt, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QFileDialog, QGroupBox, QMessageBox, QFrame, QGraphicsOpacityEffect
)

from packages.Startup import GlobalIcons
from packages.Startup.Options import Options
from packages.Tabs.GlobalSetting import GlobalSetting
from packages.Startup.PreDefined import AUDIO_EXTENSIONS


class AudioSelectionSetting(QWidget):
    activation_signal = Signal(bool)
    tab_clicked_signal = Signal()
    
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.audio_files = []
        self.current_selected_row = -1
        self.last_click_pos = None
        self.hide_timer = QTimer()
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.start_fade_out)
        self.fade_animation = None
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
        
        audio_files = []
        folders = []
        non_audio_files = []
        
        for url in urls:
            path = url.toLocalFile()
            if os.path.isfile(path):
                ext = os.path.splitext(path)[1].lower()
                if ext in AUDIO_EXTENSIONS:
                    audio_files.append(path)
                else:
                    non_audio_files.append(path)
            elif os.path.isdir(path):
                folders.append(path)
        
        if non_audio_files and not audio_files and not folders:
            QMessageBox.warning(self, "提示", "支持的音轨格式：\nAAC, MP3, AC3, E-AC3, DTS, DTS-HD, TrueHD, FLAC, ALAC, WAV, Opus, Vorbis 等")
            event.ignore()
            return
        
        if folders:
            folder = folders[0]
            self.source_path_edit.setText(folder)
            self.load_audios()
        elif audio_files:
            existing_files = set(self.audio_files)
            new_files = [af for af in audio_files if af not in existing_files]
            
            if new_files:
                total_count = len(self.audio_files) + len(new_files)
                
                if total_count == 1:
                    self.source_path_edit.setText(os.path.dirname(new_files[0]))
                else:
                    self.source_path_edit.clear()
                
                self.load_audio_files_append(new_files)
        
        event.acceptProposedAction()
    
    def load_audio_files_append(self, file_paths):
        file_paths.sort()
        
        for file_path in file_paths:
            self.audio_files.append(file_path)
            
            row = self.audio_table.rowCount()
            self.audio_table.insertRow(row)
            idx_item = QTableWidgetItem(str(row + 1))
            idx_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.audio_table.setItem(row, 0, idx_item)
            self.audio_table.setItem(row, 1, QTableWidgetItem(os.path.basename(file_path)))
        
        self.auto_match_by_index()
    
    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        source_group = QGroupBox("音轨源")
        source_layout = QVBoxLayout()
        
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("音轨源："))
        self.source_path_edit = QLineEdit()
        self.source_path_edit.setReadOnly(True)
        self.source_path_edit.setPlaceholderText("选择包含音轨文件的文件夹")
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
        
        match_group = QGroupBox("音轨匹配（按序号一一对应）")
        match_layout = QHBoxLayout()
        
        video_table_widget = QWidget()
        video_layout = QVBoxLayout()
        video_layout.setContentsMargins(0, 0, 0, 0)
        video_layout.addWidget(QLabel("视频列表"))
        self.video_table = QTableWidget()
        self.video_table.setColumnCount(2)
        self.video_table.setHorizontalHeaderLabels(["序号", "视频文件"])
        self.video_table.verticalHeader().setVisible(False)
        self.video_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.video_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.video_table.setColumnWidth(0, 40)
        self.video_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.video_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.video_table.itemClicked.connect(self.on_video_table_clicked)
        video_layout.addWidget(self.video_table)
        video_table_widget.setLayout(video_layout)
        
        audio_table_widget = QWidget()
        audio_layout = QVBoxLayout()
        audio_layout.setContentsMargins(0, 0, 0, 0)
        audio_layout.addWidget(QLabel("音轨列表"))
        
        self.audio_table = QTableWidget()
        self.audio_table.setColumnCount(2)
        self.audio_table.setHorizontalHeaderLabels(["序号", "音轨文件"])
        self.audio_table.verticalHeader().setVisible(False)
        self.audio_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.audio_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.audio_table.setColumnWidth(0, 40)
        self.audio_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.audio_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.audio_table.itemClicked.connect(self.on_audio_clicked)
        audio_layout.addWidget(self.audio_table)
        
        self.floating_btn_frame = QFrame(self.audio_table)
        self.floating_btn_frame.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.floating_btn_frame.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.floating_btn_frame.setStyleSheet("""
            QFrame {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            QPushButton {
                background-color: #ffffff;
                border: 1px solid #ccc;
                border-radius: 3px;
                padding: 2px 8px;
                min-width: 30px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
        """)
        
        floating_layout = QHBoxLayout(self.floating_btn_frame)
        floating_layout.setContentsMargins(4, 2, 4, 2)
        floating_layout.setSpacing(4)
        
        self.up_btn = QPushButton("↑上移")
        self.up_btn.setFixedHeight(24)
        self.up_btn.clicked.connect(self.move_audio_up)
        
        self.down_btn = QPushButton("↓下移")
        self.down_btn.setFixedHeight(24)
        self.down_btn.clicked.connect(self.move_audio_down)
        
        floating_layout.addWidget(self.up_btn)
        floating_layout.addWidget(self.down_btn)
        
        self.floating_btn_frame.enterEvent = self._on_frame_enter
        self.floating_btn_frame.leaveEvent = self._on_frame_leave
        
        self.floating_btn_frame.hide()
        
        audio_table_widget.setLayout(audio_layout)
        
        match_layout.addWidget(video_table_widget, 1)
        match_layout.addWidget(audio_table_widget, 1)
        
        match_group.setLayout(match_layout)
        main_layout.addWidget(match_group)
        
        info_label = QLabel("提示：音轨按序号一一对应添加到视频（第1个音轨→第1个视频，以此类推）")
        info_label.setStyleSheet("color: gray;")
        main_layout.addWidget(info_label)
        
        self.setLayout(main_layout)
    
    def connect_signals(self):
        self.browse_button.clicked.connect(self.browse_folder)
        self.clear_button.clicked.connect(self.clear_files)
        self.refresh_button.clicked.connect(self.refresh_files)
    
    def hideEvent(self, event):
        self.hide_timer.stop()
        self.floating_btn_frame.hide()
        super().hideEvent(event)
    
    def mousePressEvent(self, event):
        if self.floating_btn_frame.isVisible():
            table_rect = self.audio_table.rect()
            table_rect.moveTo(self.audio_table.mapToGlobal(table_rect.topLeft()))
            frame_rect = self.floating_btn_frame.rect()
            frame_rect.moveTo(self.floating_btn_frame.pos())
            
            click_pos = event.globalPosition().toPoint() if hasattr(event, 'globalPosition') else event.globalPos()
            
            if not table_rect.contains(click_pos) and not frame_rect.contains(click_pos):
                self.hide_timer.stop()
                self.floating_btn_frame.hide()
        
        super().mousePressEvent(event)
    
    def on_audio_clicked(self, item):
        row = item.row()
        self.current_selected_row = row
        self.last_click_pos = self.audio_table.cursor().pos()
        self.show_floating_buttons(row, self.last_click_pos)
    
    def on_video_table_clicked(self, item):
        self.hide_timer.stop()
        self.floating_btn_frame.hide()
    
    def show_floating_buttons(self, row, global_pos=None):
        self.hide_timer.stop()
        
        if row < 0 or row >= self.audio_table.rowCount():
            self.floating_btn_frame.hide()
            return
        
        if global_pos:
            x = global_pos.x() - self.floating_btn_frame.sizeHint().width() - 10
            y = global_pos.y() - self.floating_btn_frame.sizeHint().height() // 2
        elif hasattr(self, 'last_click_pos') and self.last_click_pos:
            x = self.last_click_pos.x() - self.floating_btn_frame.sizeHint().width() - 10
            y = self.last_click_pos.y() - self.floating_btn_frame.sizeHint().height() // 2
        else:
            rect = self.audio_table.visualItemRect(self.audio_table.item(row, 1))
            table_pos = self.audio_table.mapToGlobal(rect.topRight())
            x = table_pos.x() - self.floating_btn_frame.sizeHint().width() - 5
            y = table_pos.y() + (rect.height() - self.floating_btn_frame.sizeHint().height()) // 2
        
        self.floating_btn_frame.move(x, y)
        self.floating_btn_frame.setWindowOpacity(1.0)
        self.floating_btn_frame.show()
        self.floating_btn_frame.raise_()
        
        self.up_btn.setEnabled(row > 0)
        self.down_btn.setEnabled(row < self.audio_table.rowCount() - 1)
        
        self.hide_timer.start(3000)
    
    def start_fade_out(self):
        if self.fade_animation:
            self.fade_animation.stop()
        
        self.fade_animation = QPropertyAnimation(self.floating_btn_frame, b"windowOpacity")
        self.fade_animation.setDuration(500)
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.OutQuad)
        self.fade_animation.finished.connect(self.floating_btn_frame.hide)
        self.fade_animation.start()
    
    def _on_frame_enter(self, event):
        self.hide_timer.stop()
        if self.fade_animation:
            self.fade_animation.stop()
        self.floating_btn_frame.setWindowOpacity(1.0)
    
    def _on_frame_leave(self, event):
        self.hide_timer.start(3000)
    
    def move_audio_up(self):
        row = self.current_selected_row
        if row <= 0:
            return
        
        self.audio_files[row], self.audio_files[row - 1] = \
            self.audio_files[row - 1], self.audio_files[row]
        
        self.refresh_audio_table()
        self.current_selected_row = row - 1
        self.audio_table.selectRow(self.current_selected_row)
        self.show_floating_buttons(self.current_selected_row, self.last_click_pos)
        self.auto_match_by_index()
    
    def move_audio_down(self):
        row = self.current_selected_row
        if row < 0 or row >= len(self.audio_files) - 1:
            return
        
        self.audio_files[row], self.audio_files[row + 1] = \
            self.audio_files[row + 1], self.audio_files[row]
        
        self.refresh_audio_table()
        self.current_selected_row = row + 1
        self.audio_table.selectRow(self.current_selected_row)
        self.show_floating_buttons(self.current_selected_row, self.last_click_pos)
        self.auto_match_by_index()
    
    def refresh_audio_table(self):
        self.audio_table.setRowCount(0)
        for idx, file_path in enumerate(self.audio_files, 1):
            row = self.audio_table.rowCount()
            self.audio_table.insertRow(row)
            idx_item = QTableWidgetItem(str(idx))
            idx_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.audio_table.setItem(row, 0, idx_item)
            self.audio_table.setItem(row, 1, QTableWidgetItem(os.path.basename(file_path)))
    
    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择音轨源文件夹")
        if folder:
            self.source_path_edit.setText(folder)
            self.load_audios()
    
    def clear_files(self):
        self.source_path_edit.clear()
        self.audio_table.setRowCount(0)
        self.audio_files = []
        self.current_selected_row = -1
        self.floating_btn_frame.hide()
        GlobalSetting.AUDIO_FILES_ABSOLUTE_PATH_LIST.clear()
        GlobalSetting.AUDIO_LANGUAGE.clear()
    
    def refresh_files(self):
        if self.source_path_edit.text():
            self.load_audios()
    
    def load_audios(self):
        folder = self.source_path_edit.text()
        if not folder or not os.path.isdir(folder):
            return
        
        self.audio_table.setRowCount(0)
        self.audio_files = []
        self.current_selected_row = -1
        self.floating_btn_frame.hide()
        
        files = []
        for f in os.listdir(folder):
            ext = os.path.splitext(f)[1].lower()
            if ext in AUDIO_EXTENSIONS:
                files.append(f)
        
        files.sort()
        
        for idx, file_name in enumerate(files, 1):
            file_path = os.path.join(folder, file_name)
            self.audio_files.append(file_path)
            
            row = self.audio_table.rowCount()
            self.audio_table.insertRow(row)
            idx_item = QTableWidgetItem(str(idx))
            idx_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.audio_table.setItem(row, 0, idx_item)
            self.audio_table.setItem(row, 1, QTableWidgetItem(file_name))
        
        self.auto_match_by_index()
    
    def auto_match_by_index(self):
        GlobalSetting.AUDIO_FILES_ABSOLUTE_PATH_LIST.clear()
        GlobalSetting.AUDIO_LANGUAGE.clear()
        
        for display_idx, video_idx in enumerate(GlobalSetting.VIDEO_SELECTED_INDICES):
            if display_idx < len(self.audio_files):
                audio_path = self.audio_files[display_idx]
                GlobalSetting.AUDIO_FILES_ABSOLUTE_PATH_LIST[video_idx] = [audio_path]
                GlobalSetting.AUDIO_LANGUAGE[video_idx] = 'chi'
    
    def update_theme_mode_state(self):
        pass
    
    def set_preset_options(self):
        self.refresh_video_list()
    
    def refresh_video_list(self):
        self.video_table.setRowCount(0)
        for idx, video_idx in enumerate(GlobalSetting.VIDEO_SELECTED_INDICES, 1):
            if video_idx < len(GlobalSetting.VIDEO_FILES_LIST):
                video_name = GlobalSetting.VIDEO_FILES_LIST[video_idx]
                row = self.video_table.rowCount()
                self.video_table.insertRow(row)
                idx_item = QTableWidgetItem(str(idx))
                idx_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.video_table.setItem(row, 0, idx_item)
                self.video_table.setItem(row, 1, QTableWidgetItem(video_name))
        
        self.auto_match_by_index()
