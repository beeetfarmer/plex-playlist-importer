import os
import time
import re

def handle_existing_playlist(plex, playlist_name, matched_tracks):
    """
    Handle an existing playlist with the given name.
    Returns the playlist and a boolean indicating if processing should continue.
    """
    existing = [p for p in plex.playlists() if p.title == playlist_name]
    if not existing:
        return None, True
    
    existing_playlist = existing[0]
    print(f"Playlist '{playlist_name}' already exists.")
    
    print("Options:")
    print("  1. Replace existing playlist")
    print("  2. Add only new tracks to existing playlist")
    print("  3. Cancel")
    
    while True:
        try:
            choice = input("Enter your choice (1-3): ")
            if choice == '1':
                print(f"Replacing playlist '{playlist_name}'...")
                existing_playlist.delete()
                return None, True  # Continue with creating a new playlist
            elif choice == '2':
                existing_keys = {item.key for item in existing_playlist.items()}
                
                new_tracks = [track for track in matched_tracks if track.key not in existing_keys]
                
                if new_tracks:
                    print(f"Adding {len(new_tracks)} new tracks to existing playlist")
                    existing_playlist.addItems(new_tracks)
                    print(f"Added {len(new_tracks)} tracks to existing playlist")
                else:
                    print("No new tracks to add to existing playlist")
                
                return existing_playlist, False  # Don't continue with creating a new playlist
            elif choice == '3':
                print("Operation cancelled.")
                return None, False  # Don't continue with creating a new playlist
            else:
                print("Invalid choice. Please enter 1, 2, or 3.")
        except ValueError:
            print("Invalid input. Please enter a number.")
    
def create_plex_playlist(plex, playlist_name, matched_tracks, skip_confirmation=False):
    """Create a new Plex playlist or update an existing one."""
    if not matched_tracks:
        print("No tracks to add to playlist.")
        return None
    
    # Handle existing playlist
    existing_playlist, should_continue = handle_existing_playlist(plex, playlist_name, matched_tracks)
    
    if not should_continue:
        return existing_playlist
    
    # Confirm before creating
    if not skip_confirmation:
        print(f"\nReady to create playlist '{playlist_name}' with {len(matched_tracks)} tracks.")
        response = input("Continue? (y/n): ")
        if response.lower() not in ['y', 'yes']:
            print("Playlist creation cancelled.")
            return None
    
    # Create the playlist
    playlist = plex.createPlaylist(playlist_name, items=matched_tracks)
    print(f"Playlist '{playlist_name}' created with {len(matched_tracks)} tracks")
    
    return playlist

def save_missing_tracks(missing_tracks, filename, verbose=True):
    """Save list of missing tracks to a text file with diagnostic information."""
    if not missing_tracks:
        return
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"# Missing tracks from playlist\n")
            f.write(f"# Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# Total missing tracks: {len(missing_tracks)}\n\n")
            
            for i, track in enumerate(missing_tracks, 1):
                f.write(f"Track {i}: {track['artist']} - {track['title']}\n")
                
                if track.get('album'):
                    f.write(f"  Album: {track['album']}\n")
                
                f.write(f"  Path: {track['path']}\n")
                
                if verbose:
                    f.write("  --- Matching Diagnostics ---\n")
                    
                    if '(' in track['title']:
                        base_title = re.sub(r'\s*\(.*?\)', '', track['title']).strip()
                        f.write(f"  Base title (without parentheses): {base_title}\n")
                    
                    if '/' not in track['title'] and ' ' not in track['title']:
                        for i in range(1, len(track['title']) - 1):
                            if track['title'][i].isupper():
                                f.write(f"  Potential split point detected in title at position {i}: {track['title'][:i]}/{track['title'][i:]}\n")
                                break
                    
                    if 'feat.' in track['title'] or 'ft.' in track['title'] or 'with' in track['title']:
                        clean_title = clean_title_for_search(track['title'])
                        f.write(f"  Title contains featured artist. Clean title: {clean_title}\n")
                    
                    if ',' in track['artist']:
                        artists = track['artist'].split(',')
                        f.write(f"  Multiple artists detected: {', '.join(artists)}\n")
                        f.write(f"  Using first artist: {artists[0].strip()}\n")
                    
                    f.write("  Suggested manual search terms:\n")
                    f.write(f"    - Artist: {track['artist'].split(',')[0].strip()}\n")
                    
                    if '(' in track['title']:
                        f.write(f"    - Title (without parentheses): {base_title}\n")
                    else:
                        f.write(f"    - Title: {track['title']}\n")
                
                f.write("\n")
                
        print(f"Missing tracks saved to: {filename}")
    except Exception as e:
        print(f"Error saving missing tracks: {e}")