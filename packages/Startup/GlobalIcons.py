# -*- coding: utf-8 -*-
import os
from PySide6.QtGui import QIcon
from .GlobalFiles import IconsPath

_icons_cache = {}

def _load_icon(icon_name):
    if icon_name in _icons_cache:
        return _icons_cache[icon_name]
    
    icon_path = os.path.join(IconsPath, icon_name)
    if os.path.exists(icon_path):
        icon = QIcon(icon_path)
    else:
        icon = QIcon()
    
    _icons_cache[icon_name] = icon
    return icon

class _IconAccessor:
    def __init__(self, icon_name):
        self._icon_name = icon_name
        self._icon = None
    
    def get(self):
        if self._icon is None:
            self._icon = _load_icon(self._icon_name)
        return self._icon
    
    def __bool__(self):
        return not self.get().isNull()

AppIcon = _IconAccessor("App.ico")
ClearIcon = _IconAccessor("Clear.svg")
RefreshIcon = _IconAccessor("Refresh.svg")
FolderIcon = _IconAccessor("SelectFolder.svg")
