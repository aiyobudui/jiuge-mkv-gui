# -*- coding: utf-8 -*-
import os
import subprocess
import json

# Test paths
video_path = r'D:\Desktop\1\第七季（2025）大神版 12期全\20250716 大神版第2期：热点公寓（下）.mkv'
cover_path = r'D:\Desktop\1\新建文件夹\cover.png'
output_path = r'D:\Desktop\1\111\test_cover_output.mkv'
mkvmerge_path = r'D:\绿色\mkvtoolnix-64\mkvtoolnix\mkvmerge.exe'

print('Video:', video_path)
print('Video exists:', os.path.exists(video_path))
print('Cover:', cover_path)
print('Cover exists:', os.path.exists(cover_path))
print()

if os.path.exists(video_path) and os.path.exists(cover_path):
    print('Creating test file with cover...')
    
    # Build command - attachment before video file
    args = [
        mkvmerge_path, '-o', output_path, 
        '--attachment-name', 'cover.png', 
        '--attachment-mime-type', 'image/png', 
        '--attach-file', cover_path, 
        video_path
    ]
    
    result = subprocess.run(args, capture_output=True, encoding='utf-8', errors='replace')
    print('Return code:', result.returncode)
    
    if result.returncode == 0:
        print('Success!')
        print('Output size:', os.path.getsize(output_path) / 1024 / 1024, 'MB')
        
        # Get info in JSON format
        result = subprocess.run([mkvmerge_path, '-J', output_path], capture_output=True, encoding='utf-8', errors='replace')
        if result.returncode == 0:
            info = json.loads(result.stdout)
            print()
            print('--- Attachments ---')
            if 'attachments' in info:
                for att in info['attachments']:
                    print(f"  ID: {att.get('id')}, Name: {att.get('file_name')}, MIME: {att.get('content_type')}")
            else:
                print('No attachments found in JSON')
            
            print()
            print('--- Tracks ---')
            for track in info.get('tracks', []):
                print(f"  {track.get('type')}: {track.get('properties', {}).get('track_name', 'N/A')}")
    else:
        print('Failed!')
        print('Stdout:', result.stdout[:1000])
        print('Stderr:', result.stderr[:500])
else:
    print('Source files not found')
