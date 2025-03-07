# Plex Playlist Importer

A Python tool for importing M3U8 playlists into Plex with intelligent track matching algorithms.

## Features

- Multi-algorithm string similarity for better matching
- Library indexing for faster searches
- Smart handling of parentheses, special characters, and short titles
- Proper handling of existing playlists
- Support for both single playlist and batch folder imports

## Requirements

- Python 3.6+
- plexapi
- python-Levenshtein
- fuzzywuzzy

## Installation

```bash
# Clone the repository
git clone https://github.com/beeetfarmer/plex-playlist-importer.git
cd plex-playlist-importer

# Install requirements
pip install -r requirements.txt
```

## Usage

```bash
# Import a single playlist
python main.py --file "/path/to/playlist.m3u8" --token "your-plex-token"

# Import all playlists in a folder
python main.py --folder "/path/to/playlists/" --token "your-plex-token"

# Additional options
python main.py --file "/path/to/playlist.m3u8" --token "your-plex-token" \
  --url "http://plexserver:32400" \
  --playlist-name "Custom Playlist Name" \
  --threshold 0.7 \
  --verbose
```

### Command Line Arguments

- `--file`: Path to a single M3U8 file (required if --folder not used)
- `--folder`: Path to a folder containing M3U8 files (required if --file not used)
- `--url`: Plex server URL (default: http://localhost:32400)
- `--token`: Plex authentication token (required)
- `--playlist-name`: Custom name for the created playlist (single file mode only)
- `--verbose`, `-v`: Enable verbose output
- `--no-create`: Don't create playlists, just find matches
- `--threshold`: Match confidence threshold (0.0-1.0, default: 0.55)
- `--yes`, `-y`: Skip all confirmation prompts

## How it Works

The tool uses multiple string similarity algorithms to match tracks from your M3U8 playlists to tracks in your Plex library. It first builds an in-memory index of your Plex library to speed up search operations, then processes each track in the playlist to find the best match. The playlist files need to have the absolute path of the tracks in your drive as entries.

For unmatched tracks, it generates a diagnostic report to help you understand why the match failed.