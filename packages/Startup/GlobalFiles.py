# -*- coding: utf-8 -*-
import os
import sys

if getattr(sys, 'frozen', False):
    ROOT_DIR = os.path.dirname(sys.executable)
else:
    ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if sys.platform == "win32":
    ConfigDir = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'jiuge-mkv-gui')
else:
    ConfigDir = os.path.join(os.path.expanduser('~'), '.jiuge-mkv-gui')

if not os.path.exists(ConfigDir):
    os.makedirs(ConfigDir, exist_ok=True)

ResourcesPath = os.path.join(ROOT_DIR, "Resources")
FontsPath = os.path.join(ResourcesPath, "Fonts")
IconsPath = os.path.join(ResourcesPath, "Icons")
ToolsPath = os.path.join(ResourcesPath, "Tools")
LanguagesPath = os.path.join(ResourcesPath, "Languages")

if sys.platform == "win32":
    SystemToolsPath = os.path.join(ToolsPath, "Windows64")
else:
    SystemToolsPath = os.path.join(ToolsPath, "Linux")

MkvmergePath = os.path.join(SystemToolsPath, "mkvmerge.exe" if sys.platform == "win32" else "mkvmerge")
MkvpropeditPath = os.path.join(SystemToolsPath, "mkvpropedit.exe" if sys.platform == "win32" else "mkvpropedit")

AppLogFilePath = os.path.join(ROOT_DIR, "app.log")
MyFontPath = os.path.join(FontsPath, "OpenSans.ttf")
MediaInfoFolderPath = os.path.join(ROOT_DIR, "MediaInfo")

LanguageListPath = os.path.join(LanguagesPath, "iso639_language_list.json")

def create_necessary_folders():
    if not os.path.exists(MediaInfoFolderPath):
        os.makedirs(MediaInfoFolderPath)
