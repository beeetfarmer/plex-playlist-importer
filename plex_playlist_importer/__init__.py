"""
Advanced Plex M3U8 Playlist Importer
-----------------------------------
Import M3U8 playlists into Plex with intelligent track matching.
"""

__version__ = '1.0.0'

from .process_functions import process_playlist, process_playlist_folder
from .track_finder import find_track_advanced
from .playlist_parser import parse_m3u8
from .library_index import PlexLibraryIndex
from .playlist_creator import create_plex_playlist, save_missing_tracks