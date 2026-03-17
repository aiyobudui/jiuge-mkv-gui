# -*- coding: utf-8 -*-
import os
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTreeWidget, QTreeWidgetItem, QHeaderView, QCheckBox, QDialogButtonBox,
    QComboBox, QWidget
)
from packages.Tabs.GlobalSetting import GlobalSetting


AUDIO_LANGUAGES = [
    ('chi', '国语'),
    ('chi', '粤语'),
    ('eng', '英语'),
    ('jpn', '日语'),
    ('kor', '韩语'),
    ('und', '其他')
]

SUBTITLE_LANGUAGES = [
    ('chi', '国语'),
    ('chi', '中英'),
    ('chi', '中日'),
    ('chi', '中韩'),
    ('eng', '英语'),
    ('und', '其他')
]


class TrackSelectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("轨道选择")
        self.setMinimumSize(1000, 600)
        self.resize(1100, 700)
        
        self.track_selections = {}
        self.radio_buttons = {}
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        label = QLabel("勾选要保留的轨道，勾选默认轨道（每个视频每种类型只能有一个默认），可修改语言：")
        layout.addWidget(label)
        
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["视频名称", "类型", "轨道信息", "语言", "保留", "默认"])
        self.tree.header().setDefaultAlignment(Qt.AlignCenter)
        self.tree.header().setSectionsMovable(True)
        self.tree.header().setStretchLastSection(True)
        self.tree.setRootIsDecorated(False)
        self.tree.setAlternatingRowColors(True)
        
        self.tree.header().setSectionResizeMode(0, QHeaderView.Interactive)
        self.tree.header().setSectionResizeMode(1, QHeaderView.Interactive)
        self.tree.header().setSectionResizeMode(2, QHeaderView.Interactive)
        self.tree.header().setSectionResizeMode(3, QHeaderView.Interactive)
        self.tree.header().setSectionResizeMode(4, QHeaderView.Interactive)
        self.tree.header().setSectionResizeMode(5, QHeaderView.Interactive)
        
        self.tree.setColumnWidth(0, 565)
        self.tree.setColumnWidth(1, 65)
        self.tree.setColumnWidth(2, 165)
        self.tree.setColumnWidth(3, 120)
        self.tree.setColumnWidth(4, 75)
        self.tree.setColumnWidth(5, 75)
        
        layout.addWidget(self.tree)
        
        self.load_tracks()
        
        button_layout = QHBoxLayout()
        
        self.select_all_btn = QPushButton("全选保留")
        self.select_all_btn.clicked.connect(self.select_all)
        button_layout.addWidget(self.select_all_btn)
        
        self.deselect_all_btn = QPushButton("全不选保留")
        self.deselect_all_btn.clicked.connect(self.deselect_all)
        button_layout.addWidget(self.deselect_all_btn)
        
        self.set_external_sub_default_btn = QPushButton("外部字幕设为默认")
        self.set_external_sub_default_btn.clicked.connect(self.set_external_subtitle_default)
        button_layout.addWidget(self.set_external_sub_default_btn)
        
        button_layout.addStretch()
        
        button_box = QDialogButtonBox()
        ok_button = QPushButton("确定")
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)
        button_box.addButton(ok_button, QDialogButtonBox.AcceptRole)
        button_box.addButton(cancel_button, QDialogButtonBox.RejectRole)
        button_layout.addWidget(button_box)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def create_centered_checkbox(self, checked=False):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)
        checkbox = QCheckBox()
        checkbox.setChecked(checked)
        checkbox.setStyleSheet("QCheckBox::indicator { width: 16px; height: 16px; }")
        layout.addWidget(checkbox)
        return widget
    
    def create_centered_combobox(self, items, current_index=0, fixed_width=100):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)
        combo = QComboBox()
        combo.addItems(items)
        combo.setCurrentIndex(current_index)
        combo.setFixedWidth(fixed_width)
        layout.addWidget(combo)
        return widget
    
    def load_tracks(self):
        self.tree.clear()
        self.track_checkboxes = {}
        self.default_checkboxes = {'audio': {}, 'subtitle': {}}
        self.language_combos = {'audio': {}, 'subtitle': {}}
        
        for video_idx, video_name in enumerate(GlobalSetting.VIDEO_FILES_LIST):
            audio_tracks = GlobalSetting.VIDEO_OLD_TRACKS_AUDIOS_INFO[video_idx] if video_idx < len(GlobalSetting.VIDEO_OLD_TRACKS_AUDIOS_INFO) else []
            subtitle_tracks = GlobalSetting.VIDEO_OLD_TRACKS_SUBTITLES_INFO[video_idx] if video_idx < len(GlobalSetting.VIDEO_OLD_TRACKS_SUBTITLES_INFO) else []
            external_audios = GlobalSetting.AUDIO_FILES_ABSOLUTE_PATH_LIST.get(video_idx, [])
            external_subs = GlobalSetting.SUBTITLE_FILES_ABSOLUTE_PATH_LIST.get(video_idx, [])
            
            for track_idx, track in enumerate(audio_tracks):
                track_id = track.get('id', track_idx)
                lang = track.get('language', 'und')
                name = track.get('name', '')
                is_default = track.get('is_default', False)
                
                info = f"#{track_idx}"
                if name:
                    info += f" {name}"
                if is_default:
                    info += " ★默认"
                
                item = QTreeWidgetItem(self.tree)
                item.setText(0, video_name if track_idx == 0 else "")
                item.setText(1, "音轨")
                item.setText(2, info)
                item.setTextAlignment(0, Qt.AlignLeft | Qt.AlignVCenter)
                item.setTextAlignment(1, Qt.AlignCenter)
                item.setTextAlignment(2, Qt.AlignLeft | Qt.AlignVCenter)
                
                lang_widget = self.create_centered_combobox(
                    [lang_name for _, lang_name in AUDIO_LANGUAGES],
                    self.get_lang_index(lang, AUDIO_LANGUAGES),
                    100
                )
                lang_combo = lang_widget.findChild(QComboBox)
                self.tree.setItemWidget(item, 3, lang_widget)
                
                keep_widget = self.create_centered_checkbox(True)
                keep_checkbox = keep_widget.findChild(QCheckBox)
                self.tree.setItemWidget(item, 4, keep_widget)
                
                default_widget = self.create_centered_checkbox(is_default)
                default_checkbox = default_widget.findChild(QCheckBox)
                default_checkbox.setProperty("track_type", "audio")
                default_checkbox.setProperty("video_idx", video_idx)
                default_checkbox.setProperty("track_idx", track_idx)
                default_checkbox.clicked.connect(self.on_default_clicked)
                self.tree.setItemWidget(item, 5, default_widget)
                
                key = ('audio', video_idx, track_idx, track_id, False)
                self.track_checkboxes[key] = keep_checkbox
                self.default_checkboxes['audio'][(video_idx, track_idx)] = default_checkbox
                self.language_combos['audio'][(video_idx, track_idx)] = lang_combo
            
            for ext_idx, audio_path in enumerate(external_audios):
                audio_name = os.path.splitext(os.path.basename(audio_path))[0]
                info = f"外部 #{ext_idx} {audio_name}"
                
                item = QTreeWidgetItem(self.tree)
                item.setText(0, "")
                item.setText(1, "音轨")
                item.setText(2, info)
                item.setTextAlignment(0, Qt.AlignLeft | Qt.AlignVCenter)
                item.setTextAlignment(1, Qt.AlignCenter)
                item.setTextAlignment(2, Qt.AlignLeft | Qt.AlignVCenter)
                item.setForeground(2, Qt.darkGreen)
                
                lang_widget = self.create_centered_combobox(
                    [lang_name for _, lang_name in AUDIO_LANGUAGES],
                    0,
                    100
                )
                lang_combo = lang_widget.findChild(QComboBox)
                self.tree.setItemWidget(item, 3, lang_widget)
                
                keep_widget = self.create_centered_checkbox(True)
                keep_checkbox = keep_widget.findChild(QCheckBox)
                self.tree.setItemWidget(item, 4, keep_widget)
                
                default_widget = self.create_centered_checkbox(False)
                default_checkbox = default_widget.findChild(QCheckBox)
                default_checkbox.setProperty("track_type", "audio")
                default_checkbox.setProperty("video_idx", video_idx)
                default_checkbox.setProperty("track_idx", f"ext_{ext_idx}")
                default_checkbox.setProperty("is_external", True)
                default_checkbox.clicked.connect(self.on_default_clicked)
                self.tree.setItemWidget(item, 5, default_widget)
                
                key = ('audio', video_idx, ext_idx, ext_idx, True)
                self.track_checkboxes[key] = keep_checkbox
                self.default_checkboxes['audio'][(video_idx, f"ext_{ext_idx}")] = default_checkbox
                self.language_combos['audio'][(video_idx, f"ext_{ext_idx}")] = lang_combo
            
            for track_idx, track in enumerate(subtitle_tracks):
                track_id = track.get('id', track_idx)
                lang = track.get('language', 'und')
                name = track.get('name', '')
                is_default = track.get('is_default', False)
                
                info = f"#{track_idx}"
                if name:
                    info += f" {name}"
                if is_default:
                    info += " ★默认"
                
                item = QTreeWidgetItem(self.tree)
                item.setText(0, "")
                item.setText(1, "字幕")
                item.setText(2, info)
                item.setTextAlignment(0, Qt.AlignLeft | Qt.AlignVCenter)
                item.setTextAlignment(1, Qt.AlignCenter)
                item.setTextAlignment(2, Qt.AlignLeft | Qt.AlignVCenter)
                
                lang_widget = self.create_centered_combobox(
                    [lang_name for _, lang_name in SUBTITLE_LANGUAGES],
                    self.get_lang_index(lang, SUBTITLE_LANGUAGES),
                    100
                )
                lang_combo = lang_widget.findChild(QComboBox)
                self.tree.setItemWidget(item, 3, lang_widget)
                
                keep_widget = self.create_centered_checkbox(True)
                keep_checkbox = keep_widget.findChild(QCheckBox)
                self.tree.setItemWidget(item, 4, keep_widget)
                
                default_widget = self.create_centered_checkbox(is_default)
                default_checkbox = default_widget.findChild(QCheckBox)
                default_checkbox.setProperty("track_type", "subtitle")
                default_checkbox.setProperty("video_idx", video_idx)
                default_checkbox.setProperty("track_idx", track_idx)
                default_checkbox.clicked.connect(self.on_default_clicked)
                self.tree.setItemWidget(item, 5, default_widget)
                
                key = ('subtitle', video_idx, track_idx, track_id, False)
                self.track_checkboxes[key] = keep_checkbox
                self.default_checkboxes['subtitle'][(video_idx, track_idx)] = default_checkbox
                self.language_combos['subtitle'][(video_idx, track_idx)] = lang_combo
            
            for ext_idx, sub_path in enumerate(external_subs):
                sub_name = os.path.splitext(os.path.basename(sub_path))[0]
                info = f"外部 #{ext_idx} {sub_name}"
                
                item = QTreeWidgetItem(self.tree)
                item.setText(0, "")
                item.setText(1, "字幕")
                item.setText(2, info)
                item.setTextAlignment(0, Qt.AlignLeft | Qt.AlignVCenter)
                item.setTextAlignment(1, Qt.AlignCenter)
                item.setTextAlignment(2, Qt.AlignLeft | Qt.AlignVCenter)
                item.setForeground(2, Qt.darkGreen)
                
                lang_widget = self.create_centered_combobox(
                    [lang_name for _, lang_name in SUBTITLE_LANGUAGES],
                    0,
                    100
                )
                lang_combo = lang_widget.findChild(QComboBox)
                self.tree.setItemWidget(item, 3, lang_widget)
                
                keep_widget = self.create_centered_checkbox(True)
                keep_checkbox = keep_widget.findChild(QCheckBox)
                self.tree.setItemWidget(item, 4, keep_widget)
                
                default_widget = self.create_centered_checkbox(False)
                default_checkbox = default_widget.findChild(QCheckBox)
                default_checkbox.setProperty("track_type", "subtitle")
                default_checkbox.setProperty("video_idx", video_idx)
                default_checkbox.setProperty("track_idx", f"ext_{ext_idx}")
                default_checkbox.setProperty("is_external", True)
                default_checkbox.clicked.connect(self.on_default_clicked)
                self.tree.setItemWidget(item, 5, default_widget)
                
                key = ('subtitle', video_idx, ext_idx, ext_idx, True)
                self.track_checkboxes[key] = keep_checkbox
                self.default_checkboxes['subtitle'][(video_idx, f"ext_{ext_idx}")] = default_checkbox
                self.language_combos['subtitle'][(video_idx, f"ext_{ext_idx}")] = lang_combo
    
    def get_lang_index(self, lang, lang_list):
        for i, (lang_code, _) in enumerate(lang_list):
            if lang_code == lang:
                return i
        return len(lang_list) - 1
    
    def get_lang_code(self, index, lang_list):
        if 0 <= index < len(lang_list):
            return lang_list[index][0]
        return 'und'
    
    def on_default_clicked(self, checked):
        sender = self.sender()
        track_type = sender.property("track_type")
        video_idx = sender.property("video_idx")
        track_idx = sender.property("track_idx")
        
        if checked:
            for (v_idx, t_idx), checkbox in self.default_checkboxes[track_type].items():
                if v_idx == video_idx and t_idx != track_idx:
                    checkbox.setChecked(False)
    
    def select_all(self):
        for checkbox in self.track_checkboxes.values():
            checkbox.setChecked(True)
    
    def deselect_all(self):
        for checkbox in self.track_checkboxes.values():
            checkbox.setChecked(False)
    
    def set_external_subtitle_default(self):
        for video_idx in range(len(GlobalSetting.VIDEO_FILES_LIST)):
            external_subs = GlobalSetting.SUBTITLE_FILES_ABSOLUTE_PATH_LIST.get(video_idx, [])
            if not external_subs:
                continue
            
            for (v_idx, t_idx), checkbox in list(self.default_checkboxes['subtitle'].items()):
                if v_idx == video_idx:
                    checkbox.blockSignals(True)
                    checkbox.setChecked(False)
                    checkbox.blockSignals(False)
            
            first_external_key = (video_idx, "ext_0")
            if first_external_key in self.default_checkboxes['subtitle']:
                checkbox = self.default_checkboxes['subtitle'][first_external_key]
                checkbox.blockSignals(True)
                checkbox.setChecked(True)
                checkbox.blockSignals(False)
    
    def get_selections(self):
        result = {
            'audio': {}, 
            'subtitle': {}, 
            'default_audio': {}, 
            'default_subtitle': {},
            'external_audio': {},
            'external_subtitle': {},
            'audio_languages': {},
            'subtitle_languages': {}
        }
        
        for key, checkbox in self.track_checkboxes.items():
            track_type, video_idx, track_idx, track_id, is_external = key
            if video_idx not in result[track_type]:
                result[track_type][video_idx] = []
            if is_external:
                if video_idx not in result[f'external_{track_type}']:
                    result[f'external_{track_type}'][video_idx] = []
                if checkbox.isChecked():
                    result[f'external_{track_type}'][video_idx].append(track_idx)
            else:
                if checkbox.isChecked():
                    result[track_type][video_idx].append(track_id)
        
        for (video_idx, track_idx), combo in self.language_combos['audio'].items():
            if video_idx not in result['audio_languages']:
                result['audio_languages'][video_idx] = {}
            result['audio_languages'][video_idx][track_idx] = self.get_lang_code(combo.currentIndex(), AUDIO_LANGUAGES)
        
        for (video_idx, track_idx), combo in self.language_combos['subtitle'].items():
            if video_idx not in result['subtitle_languages']:
                result['subtitle_languages'][video_idx] = {}
            result['subtitle_languages'][video_idx][track_idx] = self.get_lang_code(combo.currentIndex(), SUBTITLE_LANGUAGES)
        
        for (video_idx, track_idx), checkbox in self.default_checkboxes['audio'].items():
            if checkbox.isChecked():
                is_external = checkbox.property("is_external") or False
                result['default_audio'][video_idx] = {'idx': track_idx, 'external': is_external}
        
        for (video_idx, track_idx), checkbox in self.default_checkboxes['subtitle'].items():
            if checkbox.isChecked():
                is_external = checkbox.property("is_external") or False
                result['default_subtitle'][video_idx] = {'idx': track_idx, 'external': is_external}
        
        return result
