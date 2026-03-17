# -*- coding: utf-8 -*-
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QGroupBox, QScrollArea, QWidget, QFrame
)
from PySide6.QtCore import Qt


class MediaInfoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("媒体信息")
        self.setMinimumSize(500, 400)
        self.resize(550, 450)
        self.setup_ui()
    
    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)
        
        self.file_info_group = QGroupBox("文件信息")
        self.file_info_layout = QVBoxLayout()
        self.file_info_layout.setSpacing(8)
        
        self.name_label = QLabel()
        self.name_label.setWordWrap(True)
        self.name_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        
        self.path_label = QLabel()
        self.path_label.setWordWrap(True)
        self.path_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        
        self.size_label = QLabel()
        
        self.file_info_layout.addWidget(self.name_label)
        self.file_info_layout.addWidget(self.path_label)
        self.file_info_layout.addWidget(self.size_label)
        self.file_info_group.setLayout(self.file_info_layout)
        main_layout.addWidget(self.file_info_group)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout()
        scroll_layout.setContentsMargins(0, 0, 5, 0)
        scroll_layout.setSpacing(10)
        
        self.audio_group = QGroupBox("音轨")
        self.audio_layout = QVBoxLayout()
        self.audio_layout.setSpacing(5)
        self.audio_group.setLayout(self.audio_layout)
        scroll_layout.addWidget(self.audio_group)
        
        self.subtitle_group = QGroupBox("字幕轨道")
        self.subtitle_layout = QVBoxLayout()
        self.subtitle_layout.setSpacing(5)
        self.subtitle_group.setLayout(self.subtitle_layout)
        scroll_layout.addWidget(self.subtitle_group)
        
        scroll_layout.addStretch()
        scroll_content.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area, 1)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.close_button = QPushButton("关闭")
        self.close_button.setFixedWidth(80)
        self.close_button.clicked.connect(self.accept)
        button_layout.addWidget(self.close_button)
        button_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)
    
    def set_media_info(self, file_name, file_path, file_size, audio_tracks, subtitle_tracks):
        self.name_label.setText(f"<b>文件名:</b> {file_name}")
        self.path_label.setText(f"<b>路径:</b> {file_path}")
        self.size_label.setText(f"<b>大小:</b> {file_size}")
        
        self.clear_layout(self.audio_layout)
        self.clear_layout(self.subtitle_layout)
        
        if audio_tracks:
            for i, track in enumerate(audio_tracks):
                track_label = QLabel(self.format_track(track, i))
                track_label.setWordWrap(True)
                track_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                self.audio_layout.addWidget(track_label)
        else:
            no_audio = QLabel("无音轨")
            no_audio.setStyleSheet("color: #999999; font-style: italic;")
            self.audio_layout.addWidget(no_audio)
        
        if subtitle_tracks:
            for i, track in enumerate(subtitle_tracks):
                track_label = QLabel(self.format_track(track, i))
                track_label.setWordWrap(True)
                track_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                self.subtitle_layout.addWidget(track_label)
        else:
            no_subtitle = QLabel("无字幕轨道")
            no_subtitle.setStyleSheet("color: #999999; font-style: italic;")
            self.subtitle_layout.addWidget(no_subtitle)
    
    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def format_track(self, track_info, index):
        lang = track_info.get('language', 'und')
        name = track_info.get('name', '')
        codec = track_info.get('codec', '')
        is_default = " [默认]" if track_info.get('is_default') else ""
        is_forced = " [强制]" if track_info.get('is_forced') else ""
        
        display = f"<b>#{index}</b> {lang}"
        if name:
            display += f" ({name})"
        if codec:
            display += f" [{codec}]"
        display += is_default + is_forced
        
        return display
