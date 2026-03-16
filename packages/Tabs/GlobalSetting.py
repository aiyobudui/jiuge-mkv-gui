# -*- coding: utf-8 -*-
import copy
import hashlib
import json
import logging
import os
import re
from collections import defaultdict
from pathlib import Path
from typing import List

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget

from packages.Startup import GlobalFiles
from packages.Startup.PreDefined import ISO_639_2_SYMBOLS


def get_readable_filesize(size_bytes, suffix='B'):
    for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if abs(size_bytes) < 1024.0:
            return "%3.2f %s%s" % (size_bytes, unit, suffix)
        size_bytes /= 1024.0
    return "%.2f %s%s" % (size_bytes, 'Y', suffix)


def get_attribute(data, attribute, default_value):
    return data.get(attribute) or default_value


def sort_names_like_windows(names_list):
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
    return sorted(names_list, key=alphanum_key)


class SingleOldTrackData:
    def __init__(self):
        self.id = ""
        self.track_name = ""
        self.language = ""
        self.is_default = False
        self.is_forced = False
        self.is_enabled = True
        self.uid = "-1"
        self.order = 0


class PathData:
    def __init__(self, video_index=-1, attachment_path=""):
        self.video_index = video_index
        self.attachment_path = attachment_path


class GlobalSetting(QWidget):
    LAST_DIRECTORY_PATH = ""
    
    VIDEO_SOURCE_PATHS = []
    VIDEO_FILES_LIST = []
    VIDEO_FILES_SIZE_LIST = []
    VIDEO_FILES_ABSOLUTE_PATH_LIST = []
    VIDEO_SOURCE_MKV_ONLY = False
    VIDEO_DEFAULT_DURATION_FPS = ""
    
    VIDEO_OLD_TRACKS_AUDIOS_INFO: List[List[dict]] = []
    VIDEO_OLD_TRACKS_SUBTITLES_INFO: List[List[dict]] = []
    VIDEO_OLD_ATTACHMENTS_INFO: List[List[dict]] = []
    VIDEO_OLD_TRACKS_AUDIOS_BULK_SETTING = defaultdict(SingleOldTrackData)
    VIDEO_OLD_TRACKS_SUBTITLES_BULK_SETTING = defaultdict(SingleOldTrackData)
    
    SUBTITLE_ENABLED = False
    SUBTITLE_TAB_ENABLED = defaultdict(bool)
    SUBTITLE_FILES_LIST = defaultdict(list)
    SUBTITLE_FILES_ABSOLUTE_PATH_LIST = defaultdict(list)
    SUBTITLE_TRACK_NAME = defaultdict(str)
    SUBTITLE_LANGUAGE = defaultdict(str)
    
    AUDIO_ENABLED = False
    AUDIO_TAB_ENABLED = defaultdict(bool)
    AUDIO_FILES_LIST = defaultdict(list)
    AUDIO_FILES_ABSOLUTE_PATH_LIST = defaultdict(list)
    AUDIO_TRACK_NAME = defaultdict(str)
    AUDIO_LANGUAGE = defaultdict(str)
    
    ATTACHMENT_ENABLED = False
    ATTACHMENT_FILES_LIST = []
    ATTACHMENT_FILES_ABSOLUTE_PATH_LIST = {}
    
    CHAPTER_ENABLED = False
    CHAPTER_FILES_LIST = []
    CHAPTER_FILES_ABSOLUTE_PATH_LIST = []
    CHAPTER_DISCARD_OLD = False
    
    MUX_SETTING_AUDIO_TRACKS_LIST = []
    MUX_SETTING_ONLY_KEEP_THOSE_AUDIOS_ENABLED = False
    MUX_SETTING_ONLY_KEEP_THOSE_AUDIOS_TRACKS_IDS = []
    
    MUX_SETTING_SUBTITLE_TRACKS_LIST = []
    MUX_SETTING_ONLY_KEEP_THOSE_SUBTITLES_ENABLED = False
    MUX_SETTING_ONLY_KEEP_THOSE_SUBTITLES_TRACKS_IDS = []
    
    MUX_SETTING_MAKE_THIS_AUDIO_DEFAULT_ENABLED = False
    MUX_SETTING_MAKE_THIS_AUDIO_DEFAULT_TRACK = ""
    
    MUX_SETTING_MAKE_THIS_SUBTITLE_DEFAULT_ENABLED = False
    MUX_SETTING_MAKE_THIS_SUBTITLE_DEFAULT_TRACK = ""
    
    MUX_SETTING_ABORT_ON_ERRORS = False
    MUX_SETTING_KEEP_LOG_FILE = False
    MUX_SETTING_ADD_CRC = False
    
    DESTINATION_FOLDER_PATH = ""
    OVERWRITE_SOURCE_FILES = False
    
    JOB_QUEUE_EMPTY = True
    JOB_QUEUE_FINISHED = False
    MUXING_ON = False
    
    def __init__(self):
        super().__init__()
