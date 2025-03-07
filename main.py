#!/usr/bin/env python3
"""
Plex Playlist Importer - CLI Entry Point
"""

import sys
import argparse
import traceback

try:
    from plexapi.server import PlexServer
except ImportError as e:
    print(f"Error: Missing required package - {e}")
    print("Please install required packages:")
    print("  pip install -r requirements.txt")
    sys.exit(1)

from plex_playlist_importer.process_functions import process_playlist, process_playlist_folder

def main():
    parser = argparse.ArgumentParser(description='Import M3U8 playlist(s) to Plex using advanced matching')
    # Create a mutually exclusive group for input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--file', help='Path to a single M3U8 file')
    input_group.add_argument('--folder', help='Path to a folder containing M3U8 files')
    
    parser.add_argument('--url', default='http://localhost:32400', help='Plex server URL')
    parser.add_argument('--token', required=True, help='Plex authentication token')
    parser.add_argument('--playlist-name', help='Name for the created playlist (for single file mode only)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    parser.add_argument('--no-create', action='store_true', help='Don\'t create playlists, just find matches')
    parser.add_argument('--threshold', type=float, default=0.55, help='Match confidence threshold (0.0-1.0)')
    parser.add_argument('--yes', '-y', action='store_true', help='Skip all confirmation prompts')
    
    args = parser.parse_args()
    
    try:
        # Connect to Plex
        print(f"Connecting to Plex server: {args.url}")
        plex = PlexServer(args.url, args.token)
        print(f"Connected to Plex server: {plex.friendlyName}")
        
        if args.file:
            # Single file mode
            process_playlist(
                plex=plex,
                playlist_file=args.file,
                threshold=args.threshold,
                create_playlist=not args.no_create,
                playlist_name=args.playlist_name,
                verbose=args.verbose,
                skip_confirmation=args.yes
            )
        else:
            # Folder mode
            process_playlist_folder(
                plex=plex,
                folder_path=args.folder,
                threshold=args.threshold,
                create_playlists=not args.no_create,
                verbose=args.verbose,
                skip_confirmation=args.yes
            )
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())