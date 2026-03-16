import os
import subprocess
import json

output_path = r'D:\Desktop\1\111\test_cover.mkv'
mkvmerge_path = r'D:\绿色\mkvtoolnix-64\mkvtoolnix\mkvmerge.exe'

print('Checking file:', output_path)
print('Exists:', os.path.exists(output_path))

if os.path.exists(output_path):
    print('Size:', os.path.getsize(output_path) / 1024 / 1024, 'MB')
    
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
        print('Error:', result.stderr)
else:
    print('File not found')
