# -*- coding: utf-8 -*-
"""表格辅助工具函数。"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTableWidgetItem


def populate_video_ref_table(video_table, after_populate_callback=None):
    """将 GlobalSetting.VIDEO_SELECTED_INDICES 填充到视频参考表中。

    用于 Audio/Subtitle/Attachment 三个 Tab 中显示「视频列表」参考表。

    Args:
        video_table: 目标 QTableWidget（2 列：序号 + 视频文件）
        after_populate_callback: 填充后的回调（如 auto_match_by_index）
    """
    from packages.Tabs.GlobalSetting import GlobalSetting

    video_table.setRowCount(0)
    for idx, video_idx in enumerate(GlobalSetting.VIDEO_SELECTED_INDICES, 1):
        if video_idx < len(GlobalSetting.VIDEO_FILES_LIST):
            video_name = GlobalSetting.VIDEO_FILES_LIST[video_idx]
            row = video_table.rowCount()
            video_table.insertRow(row)
            idx_item = QTableWidgetItem(str(idx))
            idx_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            video_table.setItem(row, 0, idx_item)
            video_table.setItem(row, 1, QTableWidgetItem(video_name))

    if after_populate_callback:
        after_populate_callback()
