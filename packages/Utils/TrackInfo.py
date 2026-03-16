# -*- coding: utf-8 -*-
import subprocess
import json
import os


def get_video_tracks_info(video_path, mkvmerge_path=None):
    if mkvmerge_path is None:
        from packages.Startup.Options import Options
        mkvmerge_path = Options.Mkvmerge_Path
    
    if not mkvmerge_path:
        return None
    
    if not os.path.exists(mkvmerge_path):
        return None
    
    if not os.path.exists(video_path):
        return None
    
    try:
        result = subprocess.run(
            [mkvmerge_path, '-J', video_path],
            capture_output=True,
            encoding='utf-8',
            errors='ignore',
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        if result.returncode == 0:
            return json.loads(result.stdout)
        return None
    except Exception:
        return None


def get_subtitle_tracks(video_path, mkvmerge_path=None):
    info = get_video_tracks_info(video_path, mkvmerge_path)
    if not info:
        return []
    
    subtitles = []
    tracks = info.get('tracks', [])
    
    for track in tracks:
        if track.get('type') == 'subtitles':
            properties = track.get('properties', {})
            sub_info = {
                'id': track.get('id', 0),
                'language': properties.get('language', 'und'),
                'name': properties.get('track_name', ''),
                'is_default': properties.get('default_track', False),
                'is_forced': properties.get('forced_track', False),
                'codec': track.get('codec', '')
            }
            subtitles.append(sub_info)
    
    return subtitles


def get_audio_tracks(video_path, mkvmerge_path=None):
    info = get_video_tracks_info(video_path, mkvmerge_path)
    if not info:
        return []
    
    audios = []
    tracks = info.get('tracks', [])
    
    for track in tracks:
        if track.get('type') == 'audio':
            properties = track.get('properties', {})
            audio_info = {
                'id': track.get('id', 0),
                'language': properties.get('language', 'und'),
                'name': properties.get('track_name', ''),
                'is_default': properties.get('default_track', False),
                'is_forced': properties.get('forced_track', False),
                'codec': track.get('codec', ''),
                'channels': properties.get('audio_channels', 0),
                'sample_rate': properties.get('audio_sampling_rate', 0)
            }
            audios.append(audio_info)
    
    return audios


def format_track_info(track_info, index):
    lang = track_info.get('language', 'und')
    name = track_info.get('name', '')
    codec = track_info.get('codec', '')
    is_default = " [默认]" if track_info.get('is_default') else ""
    is_forced = " [强制]" if track_info.get('is_forced') else ""
    
    display = f"#{index} {lang}"
    if name:
        display += f" ({name})"
    if codec:
        display += f" [{codec}]"
    display += is_default + is_forced
    
    return display


def get_attachments(video_path, mkvmerge_path=None):
    info = get_video_tracks_info(video_path, mkvmerge_path)
    if not info:
        return []
    
    attachments = []
    attachment_list = info.get('attachments', [])
    
    for attachment in attachment_list:
        att_info = {
            'id': attachment.get('id', 0),
            'filename': attachment.get('file_name', ''),
            'mime_type': attachment.get('content_type', ''),
            'size': attachment.get('size', 0)
        }
        attachments.append(att_info)
    
    return attachments
