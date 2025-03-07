import os

from .playlist_parser import parse_m3u8
from .library_index import PlexLibraryIndex
from .track_finder import find_track_advanced
from .playlist_creator import create_plex_playlist, save_missing_tracks

def process_playlist(plex, playlist_file, threshold=0.75, create_playlist=True, 
                     playlist_name=None, verbose=False, skip_confirmation=False):
    # Parse playlist
    print(f"Parsing playlist: {playlist_file}")
    tracks_info = parse_m3u8(playlist_file)
    
    if not tracks_info:
        print("No tracks found in playlist!")
        return [], []
    
    print(f"Found {len(tracks_info)} tracks in playlist")
    
    # Build library index
    print("Building Plex library index...")
    library_index = PlexLibraryIndex(plex)
    library_index.build_index()
    
    # Find tracks
    print("Finding tracks in Plex library...")
    matched_tracks = []
    missing_tracks = []
    
    for i, track_info in enumerate(tracks_info):
        print(f"\nProcessing track {i+1}/{len(tracks_info)}: {track_info['artist']} - {track_info['title']}")
        
        # Find track
        track = find_track_advanced(plex, track_info, library_index, threshold, verbose)
        
        if track:
            matched_tracks.append(track)
        else:
            missing_tracks.append(track_info)
            print(f"No match found for: {track_info['artist']} - {track_info['title']}")
    
    # Report results
    match_percent = (len(matched_tracks) / len(tracks_info)) * 100 if tracks_info else 0
    print(f"\nMatched {len(matched_tracks)} of {len(tracks_info)} tracks ({match_percent:.1f}%)")
    
    # Create playlist if requested
    if create_playlist and matched_tracks:
        if not playlist_name:
            playlist_name = os.path.splitext(os.path.basename(playlist_file))[0]
        
        create_plex_playlist(plex, playlist_name, matched_tracks, skip_confirmation)
    
    # Save missing tracks
    if missing_tracks:
        missing_file = f"missing_tracks_{os.path.splitext(os.path.basename(playlist_file))[0]}.txt"
        save_missing_tracks(missing_tracks, missing_file, verbose=verbose)
    
    return matched_tracks, missing_tracks

def process_playlist_folder(plex, folder_path, threshold=0.75, create_playlists=True, 
                          verbose=False, skip_confirmation=False):
    # Check if folder exists
    if not os.path.isdir(folder_path):
        print(f"Error: Folder not found: {folder_path}")
        return {}
    
    # Find all M3U8 files in the folder
    m3u8_files = [f for f in os.listdir(folder_path) 
                 if f.lower().endswith('.m3u8') and os.path.isfile(os.path.join(folder_path, f))]
    
    if not m3u8_files:
        print(f"No M3U8 files found in {folder_path}")
        return {}
    
    print(f"Found {len(m3u8_files)} M3U8 files in {folder_path}")
    
    # Build library index once for all playlists
    library_index = PlexLibraryIndex(plex)
    library_index.build_index()
    
    # Process each playlist
    results = {}
    for i, m3u8_file in enumerate(m3u8_files, 1):
        playlist_path = os.path.join(folder_path, m3u8_file)
        playlist_name = os.path.splitext(m3u8_file)[0]
        
        print(f"\n[{i}/{len(m3u8_files)}] Processing playlist: {playlist_name}")
        
        # Parse playlist
        tracks_info = parse_m3u8(playlist_path)
        
        if not tracks_info:
            print("No tracks found in playlist!")
            results[playlist_name] = ([], [])
            continue
        
        print(f"Found {len(tracks_info)} tracks in playlist")
        
        # Find tracks
        print("Finding tracks in Plex library...")
        matched_tracks = []
        missing_tracks = []
        
        for j, track_info in enumerate(tracks_info):
            print(f"\nProcessing track {j+1}/{len(tracks_info)}: {track_info['artist']} - {track_info['title']}")
            
            # Find track
            track = find_track_advanced(plex, track_info, library_index, threshold, verbose)
            
            if track:
                matched_tracks.append(track)
            else:
                missing_tracks.append(track_info)
                print(f"No match found for: {track_info['artist']} - {track_info['title']}")
        
        # Report results
        match_percent = (len(matched_tracks) / len(tracks_info)) * 100 if tracks_info else 0
        print(f"\nMatched {len(matched_tracks)} of {len(tracks_info)} tracks ({match_percent:.1f}%)")
        
        # Create playlist if requested
        if create_playlists and matched_tracks:
            if skip_confirmation:
                # Auto-create the playlist
                existing = [p for p in plex.playlists() if p.title == playlist_name]
                if existing:
                    existing[0].delete()
                playlist = plex.createPlaylist(playlist_name, items=matched_tracks)
                print(f"Playlist '{playlist_name}' created with {len(matched_tracks)} tracks")
            else:
                create_plex_playlist(plex, playlist_name, matched_tracks, skip_confirmation)
        
        # Save missing tracks
        if missing_tracks:
            missing_file = f"missing_tracks_{playlist_name}.txt"
            save_missing_tracks(missing_tracks, missing_file, verbose=verbose)
        
        results[playlist_name] = (matched_tracks, missing_tracks)
    
    # Print summary
    print("\n=== SUMMARY ===")
    print(f"Processed {len(m3u8_files)} playlists:")
    
    total_tracks = 0
    total_matched = 0
    
    for playlist_name, (matched, missing) in results.items():
        playlist_total = len(matched) + len(missing)
        match_percent = (len(matched) / playlist_total) * 100 if playlist_total else 0
        print(f"  {playlist_name}: {len(matched)}/{playlist_total} tracks matched ({match_percent:.1f}%)")
        
        total_tracks += playlist_total
        total_matched += len(matched)
    
    overall_percent = (total_matched / total_tracks) * 100 if total_tracks else 0
    print(f"Overall: {total_matched}/{total_tracks} tracks matched ({overall_percent:.1f}%)")
    
    return results