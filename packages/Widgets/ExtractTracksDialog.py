# -*- coding: utf-8 -*-
import os
import re
import logging
import threading
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

from PySide6.QtCore import Qt, Signal, QMetaObject, Q_ARG
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTreeWidget, QTreeWidgetItem, QHeaderView, QCheckBox,
    QWidget, QLineEdit, QFileDialog, QProgressBar, QMessageBox
)

from packages.Startup.Options import Options
from packages.Tabs.GlobalSetting import GlobalSetting


class ExtractTracksDialog(QDialog):
    """轨道提取对话框
    使用视频选项卡中已加载的视频和轨道信息
    """
    update_progress_signal = Signal(int, str)
    extraction_complete_signal = Signal(int, int)

    def __init__(self, parent=None, selected_rows=None):
        super().__init__(parent)
        self.setWindowTitle("轨道提取")
        self.setMinimumSize(1000, 600)
        self.resize(1000, 700)

        self.total_tasks = 0
        self.completed_tasks = 0
        self.stop_requested = False
        self.count_lock = threading.Lock()
        self.selected_rows = selected_rows or []

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        label = QLabel("勾选要提取的轨道（字幕/音轨），点击提取后选择输出目录：")
        layout.addWidget(label)

        # 输出目录选择
        output_group = QHBoxLayout()
        output_group.addWidget(QLabel("输出目录："))
        self.output_path_edit = QLineEdit()
        self.output_path_edit.setReadOnly(True)
        self.output_path_edit.setPlaceholderText("请先点击浏览选择输出文件夹")
        output_group.addWidget(self.output_path_edit)

        self.browse_output_button = QPushButton("浏览")
        self.browse_output_button.setFixedWidth(60)
        self.browse_output_button.clicked.connect(self.browse_output_folder)
        output_group.addWidget(self.browse_output_button)

        output_widget = QWidget()
        output_widget.setLayout(output_group)
        layout.addWidget(output_widget)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["视频名称", "类型", "轨道信息", "语言", "轨道名称", "提取"])
        self.tree.header().setDefaultAlignment(Qt.AlignCenter)
        self.tree.header().setSectionsMovable(True)
        self.tree.header().setStretchLastSection(False)
        self.tree.setRootIsDecorated(True)
        self.tree.setAlternatingRowColors(True)

        self.tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tree.header().setSectionResizeMode(1, QHeaderView.Interactive)
        self.tree.header().setSectionResizeMode(2, QHeaderView.Interactive)
        self.tree.header().setSectionResizeMode(3, QHeaderView.Interactive)
        self.tree.header().setSectionResizeMode(4, QHeaderView.Interactive)
        self.tree.header().setSectionResizeMode(5, QHeaderView.Interactive)

        self.tree.setColumnWidth(0, 300)
        self.tree.setColumnWidth(1, 70)
        self.tree.setColumnWidth(2, 280)
        self.tree.setColumnWidth(3, 80)
        self.tree.setColumnWidth(4, 150)
        self.tree.setColumnWidth(5, 60)

        layout.addWidget(self.tree)

        # 进度条
        progress_layout = QHBoxLayout()
        progress_layout.addWidget(QLabel("提取进度"))
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p% - %v/%m")
        progress_layout.addWidget(self.progress_bar)
        progress_group = QWidget()
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)

        button_layout = QHBoxLayout()

        self.select_all_sub_btn = QPushButton("全选字幕")
        self.select_all_sub_btn.clicked.connect(lambda: self.select_by_type('subtitle', True))
        button_layout.addWidget(self.select_all_sub_btn)

        self.deselect_all_sub_btn = QPushButton("全不选字幕")
        self.deselect_all_sub_btn.clicked.connect(lambda: self.select_by_type('subtitle', False))
        button_layout.addWidget(self.deselect_all_sub_btn)

        self.select_all_audio_btn = QPushButton("全选音轨")
        self.select_all_audio_btn.clicked.connect(lambda: self.select_by_type('audio', True))
        button_layout.addWidget(self.select_all_audio_btn)

        self.deselect_all_audio_btn = QPushButton("全不选音轨")
        self.deselect_all_audio_btn.clicked.connect(lambda: self.select_by_type('audio', False))
        button_layout.addWidget(self.deselect_all_audio_btn)

        button_layout.addStretch()

        self.extract_button = QPushButton("提取")
        self.extract_button.setStyleSheet("background-color: #0078d4; color: white; font-weight: bold;")
        self.extract_button.clicked.connect(self.start_extraction)
        button_layout.addWidget(self.extract_button)

        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

        self.update_progress_signal.connect(self.on_update_progress)
        self.extraction_complete_signal.connect(self.on_extraction_complete)

        self.load_tracks()

    def create_centered_checkbox(self, checked=False):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)
        checkbox = QCheckBox()
        checkbox.setChecked(checked)
        checkbox.setStyleSheet("QCheckBox::indicator { width: 16px; height: 16px; }")
        layout.addWidget(checkbox)
        return widget, checkbox

    def browse_output_folder(self):
        """选择输出目录"""
        default_dir = ""
        if GlobalSetting.VIDEO_FILES_ABSOLUTE_PATH_LIST:
            default_dir = os.path.dirname(GlobalSetting.VIDEO_FILES_ABSOLUTE_PATH_LIST[0])

        folder = QFileDialog.getExistingDirectory(self, "选择输出文件夹", default_dir)
        if folder:
            self.output_path_edit.setText(folder)

    def load_tracks(self):
        """加载视频轨道信息（使用视频选项卡中已有的数据）"""
        self.tree.clear()
        self.track_checkboxes = {}

        for video_idx, video_name in enumerate(GlobalSetting.VIDEO_FILES_LIST):
            if self.selected_rows and video_idx not in self.selected_rows:
                continue

            audio_tracks = GlobalSetting.VIDEO_OLD_TRACKS_AUDIOS_INFO[video_idx] if video_idx < len(GlobalSetting.VIDEO_OLD_TRACKS_AUDIOS_INFO) else []
            subtitle_tracks = GlobalSetting.VIDEO_OLD_TRACKS_SUBTITLES_INFO[video_idx] if video_idx < len(GlobalSetting.VIDEO_OLD_TRACKS_SUBTITLES_INFO) else []

            video_item = QTreeWidgetItem(self.tree)
            video_item.setText(0, video_name)
            video_item.setExpanded(True)
            font = video_item.font(0)
            font.setBold(True)
            video_item.setFont(0, font)
            for col in range(6):
                video_item.setBackground(col, QColor(230, 240, 250))

            # === 字幕轨道 ===
            for track_idx, track in enumerate(subtitle_tracks):
                track_id = track.get('id', track_idx)
                lang = track.get('language', 'und')
                name = track.get('name', '')

                info = f"#{track_idx}"
                if name:
                    info += f" {name}"
                if track.get('is_default', False):
                    info += " ★默认"

                item = QTreeWidgetItem(video_item)
                item.setText(0, "")
                item.setText(1, "字幕")
                item.setText(2, info)
                item.setForeground(1, QColor("#FF9800"))
                item.setTextAlignment(0, Qt.AlignLeft | Qt.AlignVCenter)
                item.setTextAlignment(1, Qt.AlignCenter)
                item.setTextAlignment(2, Qt.AlignLeft | Qt.AlignVCenter)

                lang_text = self._format_lang(lang)
                item.setText(3, lang_text)
                item.setTextAlignment(3, Qt.AlignCenter)

                item.setText(4, name)
                item.setTextAlignment(4, Qt.AlignLeft | Qt.AlignVCenter)

                check_widget, checkbox = self.create_centered_checkbox(False)
                self.tree.setItemWidget(item, 5, check_widget)

                key = ('subtitle', video_idx, track_id)
                self.track_checkboxes[key] = (checkbox, track)

            # === 音轨 ===
            for track_idx, track in enumerate(audio_tracks):
                track_id = track.get('id', track_idx)
                lang = track.get('language', 'und')
                name = track.get('name', '')

                info = f"#{track_idx}"
                if name:
                    info += f" {name}"
                if track.get('is_default', False):
                    info += " ★默认"

                item = QTreeWidgetItem(video_item)
                item.setText(0, "")
                item.setText(1, "音轨")
                item.setText(2, info)
                item.setForeground(1, QColor("#2196F3"))
                item.setTextAlignment(0, Qt.AlignLeft | Qt.AlignVCenter)
                item.setTextAlignment(1, Qt.AlignCenter)
                item.setTextAlignment(2, Qt.AlignLeft | Qt.AlignVCenter)

                lang_text = self._format_lang(lang)
                item.setText(3, lang_text)
                item.setTextAlignment(3, Qt.AlignCenter)

                item.setText(4, name)
                item.setTextAlignment(4, Qt.AlignLeft | Qt.AlignVCenter)

                check_widget, checkbox = self.create_centered_checkbox(False)
                self.tree.setItemWidget(item, 5, check_widget)

                key = ('audio', video_idx, track_id)
                self.track_checkboxes[key] = (checkbox, track)

    def _format_lang(self, lang):
        """格式化语言代码为可读文本"""
        lang_map = {
            'chi': '国语',
            'eng': '英语',
            'jpn': '日语',
            'kor': '韩语',
            'und': '未定义',
        }
        return lang_map.get(lang, lang)

    def _get_track_extension(self, track_type, codec):
        """根据轨道类型和编码选择正确的文件扩展名"""
        codec_lower = codec.lower() if codec else ''

        if track_type == 'subtitle':
            if 'ass' in codec_lower or 'ssa' in codec_lower:
                return '.ass'
            elif 'pgs' in codec_lower or 'hdmv_pgs' in codec_lower:
                return '.sup'
            elif 'dvb_subtitle' in codec_lower:
                return '.sub'
            elif 'dvb_teletext' in codec_lower:
                return '.ttxt'
            elif 'text' in codec_lower:
                return '.vtt'
            else:
                return '.srt'
        else:
            if 'aac' in codec_lower:
                return '.aac'
            elif 'ac3' in codec_lower:
                return '.ac3'
            elif 'dts' in codec_lower:
                return '.dts'
            elif 'eac3' in codec_lower:
                return '.eac3'
            elif 'flac' in codec_lower:
                return '.flac'
            elif 'mp3' in codec_lower:
                return '.mp3'
            elif 'opus' in codec_lower:
                return '.opus'
            elif 'pcm' in codec_lower:
                return '.wav'
            elif 'truehd' in codec_lower:
                return '.thd'
            elif 'vorbis' in codec_lower:
                return '.ogg'
            else:
                return '.mka'

    def select_by_type(self, track_type, checked):
        """按类型全选/全不选"""
        for key, (checkbox, track) in self.track_checkboxes.items():
            if key[0] == track_type:
                checkbox.setChecked(checked)

    def start_extraction(self):
        """开始提取"""
        if not Options.Mkvmerge_Path or not os.path.exists(Options.Mkvmerge_Path):
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle("警告")
            msg_box.setText("请先设置 mkvmerge.exe 路径")
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.setButtonText(QMessageBox.Ok, "确定")
            msg_box.exec()
            return

        self.mkvextract_path = os.path.join(os.path.dirname(Options.Mkvmerge_Path), "mkvextract.exe")
        if not os.path.exists(self.mkvextract_path):
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle("警告")
            msg_box.setText("未找到 mkvextract.exe，请确保安装了完整的 MKVToolNix")
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.setButtonText(QMessageBox.Ok, "确定")
            msg_box.exec()
            return

        output_dir = self.output_path_edit.text()
        if not output_dir:
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setWindowTitle("提示")
            msg_box.setText("请先选择输出目录")
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.setButtonText(QMessageBox.Ok, "确定")
            msg_box.exec()
            self.browse_output_folder()
            output_dir = self.output_path_edit.text()
            if not output_dir:
                return

        selections = self.get_extraction_selections()
        if not selections:
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setWindowTitle("提示")
            msg_box.setText("请先勾选要提取的轨道")
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.setButtonText(QMessageBox.Ok, "确定")
            msg_box.exec()
            return

        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Question)
        msg_box.setWindowTitle("确认提取")
        msg_box.setText(f"将提取 {len(selections)} 个轨道到以下目录：\n{output_dir}\n\n是否继续？")
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setButtonText(QMessageBox.Yes, "确定")
        msg_box.setButtonText(QMessageBox.No, "取消")
        reply = msg_box.exec()
        if reply != QMessageBox.Yes:
            return

        self.total_tasks = len(selections)
        self.completed_tasks = 0
        self.stop_requested = False
        self.progress_bar.setMaximum(10000)
        self.progress_bar.setValue(0)

        self.extract_button.setEnabled(False)
        self.extract_button.setText("提取中...")
        self.cancel_button.setEnabled(False)
        self.browse_output_button.setEnabled(False)

        self.select_all_sub_btn.setEnabled(False)
        self.deselect_all_sub_btn.setEnabled(False)
        self.select_all_audio_btn.setEnabled(False)
        self.deselect_all_audio_btn.setEnabled(False)

        threading.Thread(target=self.run_extraction, args=(selections, output_dir), daemon=True).start()

    def run_extraction(self, selections, output_dir):
        """执行提取任务（在后台线程中）"""
        success_count = [0]
        fail_count = [0]
        lock = threading.Lock()

        def extract_one_task(args):
            video_idx, track_type, track = args
            video_path = GlobalSetting.VIDEO_FILES_ABSOLUTE_PATH_LIST[video_idx]
            video_name = GlobalSetting.VIDEO_FILES_LIST[video_idx]
            video_name_no_ext = os.path.splitext(video_name)[0]

            video_output_dir = os.path.join(output_dir, video_name_no_ext)
            try:
                os.makedirs(video_output_dir, exist_ok=True)
            except OSError as e:
                logging.warning(f"创建输出目录失败: {video_output_dir}, {e}")
                return False

            track_id = track.get('id', 0)
            track_lang = track.get('language', 'und')
            track_name = track.get('name', '')

            suffix_parts = [f"track{track_id}"]
            if track_lang and track_lang != 'und':
                suffix_parts.append(track_lang)
            if track_name:
                safe_name = re.sub(r'[\\/:*?"<>|]', '_', track_name)
                suffix_parts.append(safe_name)
            suffix = "_".join(suffix_parts)

            ext = self._get_track_extension(track_type, track.get('codec', ''))

            output_file = os.path.join(video_output_dir, f"{video_name_no_ext}_{suffix}{ext}")

            args_cmd = [
                self.mkvextract_path,
                'tracks',
                video_path,
                f"{track_id}:{output_file}"
            ]

            try:
                result = subprocess.run(
                    args_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    encoding='utf-8',
                    errors='replace',
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                success = result.returncode in [0, 1] and os.path.exists(output_file)
            except Exception as e:
                logging.error(f"提取异常: {e}")
                success = False

            with lock:
                if success:
                    success_count[0] += 1
                else:
                    fail_count[0] += 1

            with self.count_lock:
                self.completed_tasks += 1
                completed = self.completed_tasks

            percentage = int(completed * 10000 / self.total_tasks)
            percent_text = f"{completed * 100 / self.total_tasks:.1f}%"
            self.update_progress_signal.emit(percentage, f"{percent_text} - 正在提取 {completed}/{self.total_tasks}")

            return success

        try:
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = [executor.submit(extract_one_task, args) for args in selections]
                for future in as_completed(futures):
                    if self.stop_requested:
                        executor.shutdown(wait=False)
                        break
                    try:
                        future.result()
                    except Exception as e:
                        logging.error(f"提取任务异常: {e}")

            self.update_progress_signal.emit(10000, f"100% - 提取完成！成功: {success_count[0]}，失败: {fail_count[0]}")
            self.extraction_complete_signal.emit(success_count[0], fail_count[0])
        except Exception as e:
            logging.error(f"提取过程异常: {e}")
            QMetaObject.invokeMethod(self, "_show_error", Qt.QueuedConnection,
                                     Q_ARG(str, f"提取过程发生错误: {e}"))

    def on_update_progress(self, completed, text):
        """更新进度条（主线程）"""
        self.progress_bar.setValue(completed)
        self.progress_bar.setFormat(f"%p% - {text}")

    def on_extraction_complete(self, success_count, fail_count):
        """提取完成处理（主线程）"""
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setWindowTitle("完成")
        msg_box.setText(f"轨道提取完成！\n成功: {success_count}\n失败: {fail_count}\n\n"
                        f"文件已保存到输出目录下各视频子文件夹中")
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.setButtonText(QMessageBox.Ok, "确定")
        msg_box.exec()

        self.extract_button.setEnabled(True)
        self.extract_button.setText("提取")
        self.cancel_button.setEnabled(True)
        self.browse_output_button.setEnabled(True)

        self.select_all_sub_btn.setEnabled(True)
        self.deselect_all_sub_btn.setEnabled(True)
        self.select_all_audio_btn.setEnabled(True)
        self.deselect_all_audio_btn.setEnabled(True)

    def _show_error(self, message):
        """显示错误消息（主线程）"""
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle("错误")
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.setButtonText(QMessageBox.Ok, "确定")
        msg_box.exec()
        self.extract_button.setEnabled(True)
        self.extract_button.setText("提取")
        self.cancel_button.setEnabled(True)
        self.browse_output_button.setEnabled(True)

    def get_extraction_selections(self):
        """获取用户选择的提取任务"""
        selections = []
        for key, (checkbox, track) in self.track_checkboxes.items():
            if checkbox.isChecked():
                track_type, video_idx, _ = key
                selections.append((video_idx, track_type, track))
        return selections
