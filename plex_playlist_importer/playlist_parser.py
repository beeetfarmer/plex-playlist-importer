import os
import re

def parse_m3u8(file_path):
    """Parse M3U8 file and extract track information."""
    tracks = []
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                try:
                    # Try standard format with path structure: Album Artist/Album/tracknumber - trackname
                    if '/' in line:
                        path_parts = line.split('/')
                        if len(path_parts) >= 3:
                            artist = path_parts[0]
                            album = path_parts[1]
                            
                            remaining_path = '/'.join(path_parts[2:])
                            filename = os.path.basename(remaining_path)
                            file_extension = os.path.splitext(filename)[1].lower()
                            
                            title_match = re.search(r'^\d+\s*-\s*(.*)', filename)
                            if title_match:
                                title = title_match.group(1)
                                title = os.path.splitext(title)[0].strip()
                            else:
                                title = os.path.splitext(filename)[0].strip()
                            
                            tracks.append({
                                'artist': artist,
                                'album': album,
                                'title': title,
                                'path': line,
                                'extension': file_extension
                            })
                        else:
                            print(f"Warning: Line does not match expected path format: {line}")
                    
                    # Handle flat format "Artist - Title.ext" (with or without multiple artists)
                    elif ' - ' in line:
                        artist_part, title_part = line.split(' - ', 1)
                        
                        # Handle multiple artists separated by commas - only keep first artist
                        if ',' in artist_part:
                            artist = artist_part.split(',', 1)[0].strip()
                            print(f"Multiple artists detected: '{artist_part}' -> using '{artist}'")
                        else:
                            artist = artist_part.strip()
                        
                        title = os.path.splitext(title_part)[0].strip()
                        file_extension = os.path.splitext(title_part)[1].lower()
                        
                        tracks.append({
                            'artist': artist,
                            'album': None,
                            'title': title,
                            'path': line,
                            'extension': file_extension
                        })
                    else:
                        print(f"Warning: Line does not match any expected format: {line}")
                except Exception as e:
                    print(f"Error parsing line: {line}")
                    print(f"Error details: {e}")
        
        print(f"Successfully parsed {len(tracks)} tracks from playlist")
        return tracks
        
    except Exception as e:
        print(f"Error reading playlist file: {e}")
        return []