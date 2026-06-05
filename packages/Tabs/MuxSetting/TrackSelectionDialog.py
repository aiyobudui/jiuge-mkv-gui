# -*- coding: utf-8 -*-
import os
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTreeWidget, QTreeWidgetItem, QHeaderView, QCheckBox,
    QComboBox, QWidget, QLineEdit
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

# 语言代码 -> 默认轨道名称（其他/und 清空）
LANG_CODE_TO_TRACK_NAME = {
    'chi': '国语',
    'eng': '英语',
    'jpn': '日语',
    'kor': '韩语',
    'und': '',
}

def get_auto_track_name(lang_code):
    """根据语言代码返回自动轨道名称，und 返回空字符串（清空）"""
    return LANG_CODE_TO_TRACK_NAME.get(lang_code, '')


class TrackSelectionDialog(QDialog):
    def __init__(self, parent=None, track_selections=None):
        super().__init__(parent)
        self.setWindowTitle("轨道选择")

        self.track_selections = track_selections or {}

        self.setup_ui()

        self.setMinimumSize(1100, 500)
        self.resize(1100, 600)
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        label = QLabel("勾选要保留的轨道，勾选默认轨道（每个视频每种类型只能有一个默认），可修改语言和轨道名称：")
        layout.addWidget(label)
        
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["视频名称", "类型", "轨道信息", "语言", "轨道名称", "保留", "默认"])
        self.tree.header().setDefaultAlignment(Qt.AlignCenter)
        self.tree.header().setSectionsMovable(True)
        self.tree.header().setStretchLastSection(False)
        self.tree.setRootIsDecorated(True)
        self.tree.setAlternatingRowColors(True)
        
        # 视频名称自动拉伸填满剩余空间，其余列可手动拉扯
        self.tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tree.header().setSectionResizeMode(1, QHeaderView.Interactive)
        self.tree.header().setSectionResizeMode(2, QHeaderView.Interactive)
        self.tree.header().setSectionResizeMode(3, QHeaderView.Interactive)
        self.tree.header().setSectionResizeMode(4, QHeaderView.Interactive)
        self.tree.header().setSectionResizeMode(5, QHeaderView.Interactive)
        self.tree.header().setSectionResizeMode(6, QHeaderView.Interactive)
        
        self.tree.setColumnWidth(0, 300)
        self.tree.setColumnWidth(1, 70)
        self.tree.setColumnWidth(2, 250)
        self.tree.setColumnWidth(3, 85)
        self.tree.setColumnWidth(4, 150)
        self.tree.setColumnWidth(5, 55)
        self.tree.setColumnWidth(6, 55)
        
        layout.addWidget(self.tree)
        
        self.load_tracks()
        
        button_layout = QHBoxLayout()
        
        self.clear_video_names_btn = QPushButton("清空轨道名称")
        self.clear_video_names_btn.clicked.connect(self._clear_all_track_names)
        button_layout.addWidget(self.clear_video_names_btn)
        
        self.select_all_btn = QPushButton("全选保留")
        self.select_all_btn.clicked.connect(self.select_all)
        button_layout.addWidget(self.select_all_btn)
        
        self.deselect_all_btn = QPushButton("全不选保留")
        self.deselect_all_btn.clicked.connect(self.deselect_all)
        button_layout.addWidget(self.deselect_all_btn)
        
        self.set_external_audio_default_btn = QPushButton("外部音轨设为默认")
        self.set_external_audio_default_btn.clicked.connect(self.set_external_audio_default)
        button_layout.addWidget(self.set_external_audio_default_btn)
        
        self.set_external_sub_default_btn = QPushButton("外部字幕设为默认")
        self.set_external_sub_default_btn.clicked.connect(self.set_external_subtitle_default)
        button_layout.addWidget(self.set_external_sub_default_btn)
        
        button_layout.addStretch()
        
        ok_button = QPushButton("确定")
        ok_button.clicked.connect(self._on_ok_clicked)
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        
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
    
    def create_centered_combobox(self, items, current_index=0, fixed_width=80):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)
        combo = QComboBox()
        combo.addItems(items)
        combo.setCurrentIndex(current_index)
        combo.setFixedWidth(fixed_width)
        layout.addWidget(combo)
        return widget, combo
    
    def create_centered_lineedit(self, text='', fixed_width=140):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(2, 0, 2, 0)
        layout.setAlignment(Qt.AlignCenter)
        edit = QLineEdit()
        edit.setText(text)
        edit.setFixedWidth(fixed_width)
        edit.setAlignment(Qt.AlignCenter)
        layout.addWidget(edit)
        return widget, edit
    
    def load_tracks(self):
        self.tree.clear()
        self.track_checkboxes = {}
        self.default_checkboxes = {'audio': {}, 'subtitle': {}, 'video': {}}
        self.language_combos = {'audio': {}, 'subtitle': {}, 'video': {}}
        self.track_name_edits = {'audio': {}, 'subtitle': {}, 'video': {}}
        
        for video_idx, video_name in enumerate(GlobalSetting.VIDEO_FILES_LIST):
            audio_tracks = GlobalSetting.VIDEO_OLD_TRACKS_AUDIOS_INFO[video_idx] if video_idx < len(GlobalSetting.VIDEO_OLD_TRACKS_AUDIOS_INFO) else []
            subtitle_tracks = GlobalSetting.VIDEO_OLD_TRACKS_SUBTITLES_INFO[video_idx] if video_idx < len(GlobalSetting.VIDEO_OLD_TRACKS_SUBTITLES_INFO) else []
            external_audios = GlobalSetting.AUDIO_FILES_ABSOLUTE_PATH_LIST.get(video_idx, [])
            external_subs = GlobalSetting.SUBTITLE_FILES_ABSOLUTE_PATH_LIST.get(video_idx, [])
            
            # 获取之前的轨道选择设置
            selected_audio = self.track_selections.get('audio', {}).get(video_idx, [])
            selected_subtitle = self.track_selections.get('subtitle', {}).get(video_idx, [])
            default_audio = self.track_selections.get('default_audio', {}).get(video_idx, {})
            default_subtitle = self.track_selections.get('default_subtitle', {}).get(video_idx, {})
            audio_languages = self.track_selections.get('audio_languages', {}).get(video_idx, {})
            subtitle_languages = self.track_selections.get('subtitle_languages', {}).get(video_idx, {})
            audio_track_names = self.track_selections.get('audio_track_names', {}).get(video_idx, {})
            subtitle_track_names = self.track_selections.get('subtitle_track_names', {}).get(video_idx, {})
            video_track_names = self.track_selections.get('video_track_names', {}).get(video_idx, {})
            default_video = self.track_selections.get('default_video', {}).get(video_idx, {})
            video_tracks_info = GlobalSetting.VIDEO_OLD_TRACKS_VIDEOS_INFO[video_idx] if video_idx < len(GlobalSetting.VIDEO_OLD_TRACKS_VIDEOS_INFO) else []
            
            # 创建视频分组父节点（可折叠）
            video_item = QTreeWidgetItem(self.tree)
            video_item.setText(0, video_name)
            video_item.setExpanded(True)
            font = video_item.font(0)
            font.setBold(True)
            video_item.setFont(0, font)
            for col in range(7):
                video_item.setBackground(col, QColor(230, 240, 250))
            
            # === 视频轨道（最前） ===
            for track_idx, track in enumerate(video_tracks_info):
                track_id = track.get('id', track_idx)
                lang = track.get('language', 'und')
                name = track.get('name', '')
                is_default = track.get('is_default', False)
                width = track.get('width', 0)
                height = track.get('height', 0)
                codec = track.get('codec', '')
                
                # 检查是否有之前的默认设置
                if video_idx in self.track_selections.get('default_video', {}):
                    is_default = default_video.get('idx') == track_idx
                
                # 计算初始轨道名称：保存值 > 轨道自带名称
                if video_idx in self.track_selections.get('video_track_names', {}) and track_idx in video_track_names:
                    init_track_name = video_track_names[track_idx]
                else:
                    init_track_name = name  # 从轨道信息自动读取
                
                info = f"#{track_idx}"
                if codec:
                    info += f" [{codec}]"
                if width and height:
                    info += f" {width}x{height}"
                if name:
                    info += f" ({name})"
                if is_default:
                    info += " ★默认"
                
                item = QTreeWidgetItem(video_item)
                item.setText(0, "")
                item.setText(1, "视频")
                item.setText(2, info)
                item.setForeground(1, QColor("#4CAF50"))
                item.setTextAlignment(0, Qt.AlignLeft | Qt.AlignVCenter)
                item.setTextAlignment(1, Qt.AlignCenter)
                item.setTextAlignment(2, Qt.AlignLeft | Qt.AlignVCenter)
                
                # 视频轨语言（简化版，编辑时也可触发自动名称）
                lang_widget, lang_combo = self.create_centered_combobox(
                    [lang_name for _, lang_name in AUDIO_LANGUAGES],
                    self.get_lang_index(lang, AUDIO_LANGUAGES)
                )
                self.tree.setItemWidget(item, 3, lang_widget)
                
                name_widget, name_edit = self.create_centered_lineedit(init_track_name)
                self.tree.setItemWidget(item, 4, name_widget)
                
                # 视频轨保留勾选框（始终保留）
                keep_widget = self.create_centered_checkbox(True)
                keep_checkbox = keep_widget.findChild(QCheckBox)
                self.tree.setItemWidget(item, 5, keep_widget)
                
                # 默认勾选框
                default_widget = self.create_centered_checkbox(is_default)
                default_checkbox = default_widget.findChild(QCheckBox)
                default_checkbox.setProperty("track_type", "video")
                default_checkbox.setProperty("video_idx", video_idx)
                default_checkbox.setProperty("track_idx", track_idx)
                default_checkbox.clicked.connect(self.on_default_clicked)
                self.tree.setItemWidget(item, 6, default_widget)
                
                # 语言变更时自动更新轨道名称（跟音轨一样）
                lang_combo.currentIndexChanged.connect(
                    lambda idx, ne=name_edit, ll=AUDIO_LANGUAGES: self._on_lang_changed(idx, ne, ll)
                )
                
                key = ('video', video_idx, track_idx, track_id, False)
                self.track_checkboxes[key] = keep_checkbox
                self.default_checkboxes['video'][(video_idx, track_idx)] = default_checkbox
                self.language_combos['video'][(video_idx, track_idx)] = lang_combo
                self.track_name_edits['video'][(video_idx, track_idx)] = name_edit
            
            # === 音轨（内置） ===
            for track_idx, track in enumerate(audio_tracks):
                track_id = track.get('id', track_idx)
                lang = track.get('language', 'und')
                name = track.get('name', '')
                is_default = track.get('is_default', False)
                
                # 检查是否有之前的设置
                if video_idx in self.track_selections.get('audio', {}):
                    is_keep = track_id in selected_audio
                else:
                    is_keep = True
                
                # 检查是否有之前的默认设置
                if video_idx in self.track_selections.get('default_audio', {}):
                    is_default = default_audio.get('idx') == track_idx and not default_audio.get('external', False)
                
                # 检查是否有之前的语言设置
                if video_idx in self.track_selections.get('audio_languages', {}) and track_idx in audio_languages:
                    lang = audio_languages[track_idx]
                
                # 计算初始轨道名称：保存值 > 轨道自带名称 > 语言推断
                if video_idx in self.track_selections.get('audio_track_names', {}) and track_idx in audio_track_names:
                    init_track_name = audio_track_names[track_idx]
                elif name:
                    init_track_name = name  # 从轨道信息自动读取
                else:
                    init_track_name = get_auto_track_name(lang)
                
                info = f"#{track_idx}"
                if name:
                    info += f" {name}"
                if is_default:
                    info += " ★默认"
                
                item = QTreeWidgetItem(video_item)
                item.setText(0, "")
                item.setText(1, "音轨")
                item.setText(2, info)
                item.setForeground(1, QColor("#2196F3"))
                item.setTextAlignment(0, Qt.AlignLeft | Qt.AlignVCenter)
                item.setTextAlignment(1, Qt.AlignCenter)
                item.setTextAlignment(2, Qt.AlignLeft | Qt.AlignVCenter)
                
                lang_widget, lang_combo = self.create_centered_combobox(
                    [lang_name for _, lang_name in AUDIO_LANGUAGES],
                    self.get_lang_index(lang, AUDIO_LANGUAGES)
                )
                self.tree.setItemWidget(item, 3, lang_widget)
                
                name_widget, name_edit = self.create_centered_lineedit(init_track_name)
                self.tree.setItemWidget(item, 4, name_widget)
                
                keep_widget = self.create_centered_checkbox(is_keep)
                keep_checkbox = keep_widget.findChild(QCheckBox)
                self.tree.setItemWidget(item, 5, keep_widget)
                
                default_widget = self.create_centered_checkbox(is_default)
                default_checkbox = default_widget.findChild(QCheckBox)
                default_checkbox.setProperty("track_type", "audio")
                default_checkbox.setProperty("video_idx", video_idx)
                default_checkbox.setProperty("track_idx", track_idx)
                default_checkbox.clicked.connect(self.on_default_clicked)
                self.tree.setItemWidget(item, 6, default_widget)
                
                # 语言变更时自动更新轨道名称
                lang_combo.currentIndexChanged.connect(
                    lambda idx, ne=name_edit, ll=AUDIO_LANGUAGES: self._on_lang_changed(idx, ne, ll)
                )
                
                key = ('audio', video_idx, track_idx, track_id, False)
                self.track_checkboxes[key] = keep_checkbox
                self.default_checkboxes['audio'][(video_idx, track_idx)] = default_checkbox
                self.language_combos['audio'][(video_idx, track_idx)] = lang_combo
                self.track_name_edits['audio'][(video_idx, track_idx)] = name_edit
            
            for ext_idx, audio_path in enumerate(external_audios):
                audio_name = os.path.splitext(os.path.basename(audio_path))[0]
                info = f"外部 #{ext_idx} {audio_name}"
                
                # 外部音轨始终保留（混流时总是包含）
                is_keep = True
                is_default = False
                ext_key = f"ext_{ext_idx}"
                
                # 检查是否有之前的默认设置
                if video_idx in self.track_selections.get('default_audio', {}):
                    is_default = default_audio.get('idx') == ext_key and default_audio.get('external', False)
                
                # 检查是否有之前的语言设置
                lang = 'chi'  # 默认语言
                if video_idx in self.track_selections.get('audio_languages', {}) and ext_key in audio_languages:
                    lang = audio_languages[ext_key]
                
                # 计算初始轨道名称：保存值 > 文件名
                if video_idx in self.track_selections.get('audio_track_names', {}) and ext_key in audio_track_names:
                    init_track_name = audio_track_names[ext_key]
                else:
                    init_track_name = audio_name  # 外部音轨用文件名
                
                item = QTreeWidgetItem(video_item)
                item.setText(0, "")
                item.setText(1, "音轨")
                item.setText(2, info)
                item.setForeground(1, QColor("#00BCD4"))
                item.setForeground(2, QColor("#9C27B0"))
                item.setTextAlignment(0, Qt.AlignLeft | Qt.AlignVCenter)
                item.setTextAlignment(1, Qt.AlignCenter)
                item.setTextAlignment(2, Qt.AlignLeft | Qt.AlignVCenter)
                
                lang_widget, lang_combo = self.create_centered_combobox(
                    [lang_name for _, lang_name in AUDIO_LANGUAGES],
                    self.get_lang_index(lang, AUDIO_LANGUAGES)
                )
                self.tree.setItemWidget(item, 3, lang_widget)
                
                name_widget, name_edit = self.create_centered_lineedit(init_track_name)
                self.tree.setItemWidget(item, 4, name_widget)
                
                keep_widget = self.create_centered_checkbox(is_keep)
                keep_checkbox = keep_widget.findChild(QCheckBox)
                self.tree.setItemWidget(item, 5, keep_widget)
                
                default_widget = self.create_centered_checkbox(is_default)
                default_checkbox = default_widget.findChild(QCheckBox)
                default_checkbox.setProperty("track_type", "audio")
                default_checkbox.setProperty("video_idx", video_idx)
                default_checkbox.setProperty("track_idx", ext_key)
                default_checkbox.setProperty("is_external", True)
                default_checkbox.clicked.connect(self.on_default_clicked)
                self.tree.setItemWidget(item, 6, default_widget)
                
                # 语言变更时自动更新轨道名称
                lang_combo.currentIndexChanged.connect(
                    lambda idx, ne=name_edit, ll=AUDIO_LANGUAGES: self._on_lang_changed(idx, ne, ll)
                )
                
                key = ('audio', video_idx, ext_idx, ext_idx, True)
                self.track_checkboxes[key] = keep_checkbox
                self.default_checkboxes['audio'][(video_idx, ext_key)] = default_checkbox
                self.language_combos['audio'][(video_idx, ext_key)] = lang_combo
                self.track_name_edits['audio'][(video_idx, ext_key)] = name_edit
            
            for track_idx, track in enumerate(subtitle_tracks):
                track_id = track.get('id', track_idx)
                lang = track.get('language', 'und')
                name = track.get('name', '')
                is_default = track.get('is_default', False)
                
                # 检查是否有之前的设置
                if video_idx in self.track_selections.get('subtitle', {}):
                    is_keep = track_id in selected_subtitle
                else:
                    is_keep = True
                
                # 检查是否有之前的默认设置
                if video_idx in self.track_selections.get('default_subtitle', {}):
                    is_default = default_subtitle.get('idx') == track_idx and not default_subtitle.get('external', False)
                
                # 检查是否有之前的语言设置
                if video_idx in self.track_selections.get('subtitle_languages', {}) and track_idx in subtitle_languages:
                    lang = subtitle_languages[track_idx]
                
                # 计算初始轨道名称：保存值 > 轨道自带名称 > 语言推断
                if video_idx in self.track_selections.get('subtitle_track_names', {}) and track_idx in subtitle_track_names:
                    init_track_name = subtitle_track_names[track_idx]
                elif name:
                    init_track_name = name  # 从轨道信息自动读取
                else:
                    init_track_name = get_auto_track_name(lang)
                
                info = f"#{track_idx}"
                if name:
                    info += f" {name}"
                if is_default:
                    info += " ★默认"
                
                item = QTreeWidgetItem(video_item)
                item.setText(0, "")
                item.setText(1, "字幕")
                item.setText(2, info)
                item.setForeground(1, QColor("#FF9800"))
                item.setTextAlignment(0, Qt.AlignLeft | Qt.AlignVCenter)
                item.setTextAlignment(1, Qt.AlignCenter)
                item.setTextAlignment(2, Qt.AlignLeft | Qt.AlignVCenter)
                
                lang_widget, lang_combo = self.create_centered_combobox(
                    [lang_name for _, lang_name in SUBTITLE_LANGUAGES],
                    self.get_lang_index(lang, SUBTITLE_LANGUAGES)
                )
                self.tree.setItemWidget(item, 3, lang_widget)
                
                name_widget, name_edit = self.create_centered_lineedit(init_track_name)
                self.tree.setItemWidget(item, 4, name_widget)
                
                keep_widget = self.create_centered_checkbox(is_keep)
                keep_checkbox = keep_widget.findChild(QCheckBox)
                self.tree.setItemWidget(item, 5, keep_widget)
                
                default_widget = self.create_centered_checkbox(is_default)
                default_checkbox = default_widget.findChild(QCheckBox)
                default_checkbox.setProperty("track_type", "subtitle")
                default_checkbox.setProperty("video_idx", video_idx)
                default_checkbox.setProperty("track_idx", track_idx)
                default_checkbox.clicked.connect(self.on_default_clicked)
                self.tree.setItemWidget(item, 6, default_widget)
                
                # 语言变更时自动更新轨道名称
                lang_combo.currentIndexChanged.connect(
                    lambda idx, ne=name_edit, ll=SUBTITLE_LANGUAGES: self._on_lang_changed(idx, ne, ll)
                )
                
                key = ('subtitle', video_idx, track_idx, track_id, False)
                self.track_checkboxes[key] = keep_checkbox
                self.default_checkboxes['subtitle'][(video_idx, track_idx)] = default_checkbox
                self.language_combos['subtitle'][(video_idx, track_idx)] = lang_combo
                self.track_name_edits['subtitle'][(video_idx, track_idx)] = name_edit
            
            for ext_idx, sub_path in enumerate(external_subs):
                sub_name = os.path.splitext(os.path.basename(sub_path))[0]
                info = f"外部 #{ext_idx} {sub_name}"
                
                # 外部字幕始终保留（混流时总是包含）
                is_keep = True
                is_default = False
                ext_key = f"ext_{ext_idx}"
                
                # 检查是否有之前的默认设置
                if video_idx in self.track_selections.get('default_subtitle', {}):
                    is_default = default_subtitle.get('idx') == ext_key and default_subtitle.get('external', False)
                
                # 检查是否有之前的语言设置
                lang = 'chi'  # 默认语言
                if video_idx in self.track_selections.get('subtitle_languages', {}) and ext_key in subtitle_languages:
                    lang = subtitle_languages[ext_key]
                
                # 计算初始轨道名称：保存值 > 文件名
                if video_idx in self.track_selections.get('subtitle_track_names', {}) and ext_key in subtitle_track_names:
                    init_track_name = subtitle_track_names[ext_key]
                else:
                    init_track_name = sub_name  # 外部字幕用文件名
                
                item = QTreeWidgetItem(video_item)
                item.setText(0, "")
                item.setText(1, "字幕")
                item.setText(2, info)
                item.setForeground(1, QColor("#E91E63"))
                item.setForeground(2, Qt.darkGreen)
                item.setTextAlignment(0, Qt.AlignLeft | Qt.AlignVCenter)
                item.setTextAlignment(1, Qt.AlignCenter)
                item.setTextAlignment(2, Qt.AlignLeft | Qt.AlignVCenter)
                
                lang_widget, lang_combo = self.create_centered_combobox(
                    [lang_name for _, lang_name in SUBTITLE_LANGUAGES],
                    self.get_lang_index(lang, SUBTITLE_LANGUAGES)
                )
                self.tree.setItemWidget(item, 3, lang_widget)
                
                name_widget, name_edit = self.create_centered_lineedit(init_track_name)
                self.tree.setItemWidget(item, 4, name_widget)
                
                keep_widget = self.create_centered_checkbox(is_keep)
                keep_checkbox = keep_widget.findChild(QCheckBox)
                self.tree.setItemWidget(item, 5, keep_widget)
                
                default_widget = self.create_centered_checkbox(is_default)
                default_checkbox = default_widget.findChild(QCheckBox)
                default_checkbox.setProperty("track_type", "subtitle")
                default_checkbox.setProperty("video_idx", video_idx)
                default_checkbox.setProperty("track_idx", ext_key)
                default_checkbox.setProperty("is_external", True)
                default_checkbox.clicked.connect(self.on_default_clicked)
                self.tree.setItemWidget(item, 6, default_widget)
                
                # 语言变更时自动更新轨道名称
                lang_combo.currentIndexChanged.connect(
                    lambda idx, ne=name_edit, ll=SUBTITLE_LANGUAGES: self._on_lang_changed(idx, ne, ll)
                )
                
                key = ('subtitle', video_idx, ext_idx, ext_idx, True)
                self.track_checkboxes[key] = keep_checkbox
                self.default_checkboxes['subtitle'][(video_idx, ext_key)] = default_checkbox
                self.language_combos['subtitle'][(video_idx, ext_key)] = lang_combo
                self.track_name_edits['subtitle'][(video_idx, ext_key)] = name_edit
            
    
    def _on_lang_changed(self, combo_index, name_edit, lang_list):
        """语言下拉框变更时，自动更新轨道名称输入框"""
        lang_code = self.get_lang_code(combo_index, lang_list)
        name_edit.setText(get_auto_track_name(lang_code))
    
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
    
    def set_external_audio_default(self):
        for video_idx in range(len(GlobalSetting.VIDEO_FILES_LIST)):
            external_audios = GlobalSetting.AUDIO_FILES_ABSOLUTE_PATH_LIST.get(video_idx, [])
            if not external_audios:
                continue
            
            for (v_idx, t_idx), checkbox in list(self.default_checkboxes['audio'].items()):
                if v_idx == video_idx:
                    checkbox.blockSignals(True)
                    checkbox.setChecked(False)
                    checkbox.blockSignals(False)
            
            first_external_key = (video_idx, "ext_0")
            if first_external_key in self.default_checkboxes['audio']:
                checkbox = self.default_checkboxes['audio'][first_external_key]
                checkbox.blockSignals(True)
                checkbox.setChecked(True)
                checkbox.blockSignals(False)
    
    def _clear_all_track_names(self):
        """清空所有轨道的名称（视频轨、音轨、字幕轨）"""
        for track_type in ('video', 'audio', 'subtitle'):
            for edit in self.track_name_edits[track_type].values():
                edit.setText('')
    
    def _on_ok_clicked(self):
        """确定按钮：保存当前选择，关闭对话框"""
        self._save_selections()
        self.accept()

    def _save_selections(self):
        """保存当前选择到 track_selections"""
        selections = self.get_selections()
        for key in selections:
            self.track_selections[key] = selections[key]
    
    def get_selections(self):
        result = {
            'video': {},
            'audio': {}, 
            'subtitle': {}, 
            'default_audio': {}, 
            'default_subtitle': {},
            'default_video': {},
            'external_audio': {},
            'external_subtitle': {},
            'audio_languages': {},
            'subtitle_languages': {},
            'audio_track_names': {},
            'subtitle_track_names': {},
            'video_track_names': {}
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
        
        for (video_idx, track_idx), edit in self.track_name_edits['audio'].items():
            if video_idx not in result['audio_track_names']:
                result['audio_track_names'][video_idx] = {}
            result['audio_track_names'][video_idx][track_idx] = edit.text()
        
        for (video_idx, track_idx), edit in self.track_name_edits['subtitle'].items():
            if video_idx not in result['subtitle_track_names']:
                result['subtitle_track_names'][video_idx] = {}
            result['subtitle_track_names'][video_idx][track_idx] = edit.text()
        
        for (video_idx, track_idx), edit in self.track_name_edits['video'].items():
            if video_idx not in result['video_track_names']:
                result['video_track_names'][video_idx] = {}
            result['video_track_names'][video_idx][track_idx] = edit.text()
        
        for (video_idx, track_idx), checkbox in self.default_checkboxes['audio'].items():
            if checkbox.isChecked():
                is_external = checkbox.property("is_external") or False
                result['default_audio'][video_idx] = {'idx': track_idx, 'external': is_external}
        
        for (video_idx, track_idx), checkbox in self.default_checkboxes['subtitle'].items():
            if checkbox.isChecked():
                is_external = checkbox.property("is_external") or False
                result['default_subtitle'][video_idx] = {'idx': track_idx, 'external': is_external}
        
        for (video_idx, track_idx), checkbox in self.default_checkboxes['video'].items():
            if checkbox.isChecked():
                is_external = checkbox.property("is_external") or False
                result['default_video'][video_idx] = {'idx': track_idx, 'external': is_external}
        
        return result
