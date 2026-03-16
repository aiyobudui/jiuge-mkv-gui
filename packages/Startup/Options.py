# -*- coding: utf-8 -*-
import json
import os
from .GlobalFiles import ConfigDir

OptionsFilePath = os.path.join(ConfigDir, "options.json")

DefaultPresets = [
    {
        "name": "默认预设",
        "video_extensions": [".mkv", ".mp4", ".avi", ".mov", ".wmv"],
        "subtitle_extensions": [".srt", ".ass", ".ssa"],
        "audio_extensions": [".aac", ".ac3", ".flac", ".m4a", ".mp3"],
        "default_subtitle_language": "chi",
        "default_audio_language": "chi",
        "default_subtitle_delay": 0.0,
        "default_audio_delay": 0.0,
    }
]


class Options:
    FavoritePresetId = 0
    CurrentPreset = DefaultPresets[0].copy()
    Choose_Preset_On_Startup = True
    
    Mkvmerge_Path = ""
    
    @staticmethod
    def load():
        if os.path.exists(OptionsFilePath):
            try:
                with open(OptionsFilePath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    Options.FavoritePresetId = data.get("favorite_preset_id", 0)
                    Options.Choose_Preset_On_Startup = data.get("choose_preset_on_startup", True)
                    Options.Mkvmerge_Path = data.get("mkvmerge_path", "")
                    if Options.FavoritePresetId < len(DefaultPresets):
                        Options.CurrentPreset = DefaultPresets[Options.FavoritePresetId].copy()
            except:
                pass
    
    @staticmethod
    def save():
        data = {
            "favorite_preset_id": Options.FavoritePresetId,
            "choose_preset_on_startup": Options.Choose_Preset_On_Startup,
            "mkvmerge_path": Options.Mkvmerge_Path,
        }
        with open(OptionsFilePath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


def get_names_list_of_presets():
    return [preset["name"] for preset in DefaultPresets]


def save_options():
    Options.save()
