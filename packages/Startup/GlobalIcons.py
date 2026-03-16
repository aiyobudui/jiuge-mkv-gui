# -*- coding: utf-8 -*-
import os
from PySide6.QtGui import QIcon, QPixmap
from .GlobalFiles import IconsPath

def load_icon(icon_name):
    icon_path = os.path.join(IconsPath, icon_name)
    if os.path.exists(icon_path):
        return QIcon(icon_path)
    return QIcon()

AppIcon = load_icon("App.ico")
ClearIcon = load_icon("Clear.svg")
RefreshIcon = load_icon("Refresh.svg")
FolderIcon = load_icon("SelectFolder.svg")
TopIcon = load_icon("Top_Dark.svg")
BottomIcon = load_icon("Bottom_Dark.svg")
UpIcon = load_icon("Up_Dark.svg")
DownIcon = load_icon("Down_Dark.svg")
TrashIcon = load_icon("Trash_Dark.svg")
PlusIcon = load_icon("Plus.svg")
StartMuxingIcon = load_icon("StartMultiplexing.svg")
SettingIcon = load_icon("Setting.svg")
InfoIcon = load_icon("Info.svg")
