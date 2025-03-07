import re
import time
from collections import defaultdict

from .string_utils import normalize_string, get_multi_similarity, clean_title_for_search

class PlexLibraryIndex:
    """Index a Plex library for faster and smarter searching."""
    
    def __init__(self, plex):
        """Initialize the index with a PlexServer instance."""
        self.plex = plex
        self.artist_index = {}  # Maps normalized artist name to artist object
        self.artist_aliases = {}  # Maps aliases to canonical artist names
        self.track_index = defaultdict(list)  # Maps normalized track title to list of track objects
        self.initialized = False
    
    def build_index(self, music_library=None, callback=None):
        """Build the library index. This may take time for large libraries."""
        start_time = time.time()
        print("Building Plex library index...")
        
        if music_library is None:
            music_sections = [section for section in self.plex.library.sections() 
                             if section.type == 'artist']
            if not music_sections:
                print("No music library found in Plex!")
                return False
            music_library = music_sections[0]
        
        all_artists = music_library.all()
        total_artists = len(all_artists)
        
        for i, artist in enumerate(all_artists):
            if callback and i % 10 == 0:
                callback(i, total_artists)
                
            norm_name = normalize_string(artist.title)
            self.artist_index[norm_name] = artist
            
            variations = self._get_artist_variations(artist.title)
            for variation in variations:
                norm_var = normalize_string(variation)
                if norm_var and norm_var != norm_name:
                    self.artist_aliases[norm_var] = norm_name
            
            try:
                for album in artist.albums():
                    for track in album.tracks():
                        norm_title = normalize_string(track.title)
                        self.track_index[norm_title].append({
                            'track': track,
                            'artist': artist,
                            'album': album
                        })
                        
                        base_title = re.sub(r'\s*\(.*?\)', '', norm_title).strip()
                        if base_title and base_title != norm_title:
                            self.track_index[base_title].append({
                                'track': track,
                                'artist': artist,
                                'album': album
                            })
            except Exception as e:
                print(f"Error indexing tracks for {artist.title}: {e}")
        
        elapsed = time.time() - start_time
        print(f"Library index built in {elapsed:.2f} seconds")
        print(f"Indexed {len(self.artist_index)} artists and {len(self.track_index)} unique track titles")
        
        self.initialized = True
        return True
    
    def _get_artist_variations(self, artist_name):
        """Generate common variations of artist names."""
        variations = [artist_name]
        
        if "/" in artist_name:
            variations.append(artist_name.replace("/", " "))
            variations.append(artist_name.replace("/", "-"))
            variations.append(artist_name.replace("/", ""))
        
        if artist_name.lower().startswith("the "):
            variations.append(artist_name[4:])
        else:
            variations.append("The " + artist_name)
        
        if re.search(r'\b[A-Z]\.', artist_name):
            variations.append(re.sub(r'\.', '', artist_name))
        
        return variations
    
    def find_artist(self, artist_name, threshold=0.7):
        """Find an artist in the indexed library."""
        if not self.initialized:
            print("Library index not initialized. Call build_index() first.")
            return None
        
        norm_name = normalize_string(artist_name)
        
        if norm_name in self.artist_index:
            return self.artist_index[norm_name]
        
        if norm_name in self.artist_aliases:
            canonical = self.artist_aliases[norm_name]
            return self.artist_index[canonical]
        
        best_match = None
        best_score = threshold
        
        for indexed_name, artist in self.artist_index.items():
            score = get_multi_similarity(norm_name, indexed_name)
            if score > best_score:
                best_score = score
                best_match = artist
        
        return best_match
    
    def find_track(self, artist_name, track_title, album_title=None):
        """Find a track in the indexed library."""
        if not self.initialized:
            print("Library index not initialized. Call build_index() first.")
            return []
        
        clean_title = clean_title_for_search(track_title)
        
        norm_title = normalize_string(track_title)
        clean_norm_title = normalize_string(clean_title)
        norm_artist = normalize_string(artist_name)
        norm_album = normalize_string(album_title) if album_title else None
        
        artist = self.find_artist(artist_name, threshold=0.6)
        
        matches = []
        
        title_variants = [norm_title]
        if clean_norm_title != norm_title:
            title_variants.append(clean_norm_title)
            
        for title_var in title_variants:
            if title_var in self.track_index:
                direct_matches = self.track_index[title_var]
                for match_info in direct_matches:
                    track = match_info['track']
                    track_artist = match_info['artist']
                    
                    artist_sim = get_multi_similarity(norm_artist, normalize_string(track_artist.title))
                    title_sim = 1.0  # Direct title match
                    
                    album_sim = 0.0
                    if norm_album and match_info['album']:
                        album_sim = get_multi_similarity(norm_album, normalize_string(match_info['album'].title))
                    
                    score = (artist_sim * 0.4) + (title_sim * 0.6)
                    if norm_album:
                        score = (score * 0.8) + (album_sim * 0.2)
                    
                    matches.append({
                        'track': track,
                        'artist_name': track_artist.title,
                        'album_name': match_info['album'].title if match_info['album'] else None,
                        'score': score,
                        'artist_sim': artist_sim,
                        'title_sim': title_sim,
                        'album_sim': album_sim if norm_album else None
                    })
        
        # Special lookup for tracks with featured artists
        if not matches and ('feat.' in track_title or 'with' in track_title):
            clean_title = clean_title_for_search(track_title)
            
            for indexed_title, track_infos in self.track_index.items():
                clean_indexed = clean_title_for_search(indexed_title)
                indexed_sim = get_multi_similarity(clean_title.lower(), clean_indexed.lower())
                
                if indexed_sim > 0.85:
                    for track_info in track_infos:
                        track = track_info['track']
                        track_artist = track_info['artist']
                        
                        artist_sim = get_multi_similarity(norm_artist, normalize_string(track_artist.title))
                        
                        if artist_sim > 0.7:
                            score = (artist_sim * 0.4) + (indexed_sim * 0.6)
                            
                            matches.append({
                                'track': track,
                                'artist_name': track_artist.title,
                                'album_name': track_info['album'].title if track_info['album'] else None,
                                'score': score,
                                'artist_sim': artist_sim,
                                'title_sim': indexed_sim,
                                'album_sim': None
                            })
                            
        # If we have a specific artist, search their tracks
        if artist and not matches:
            try:
                for album in artist.albums():
                    for track in album.tracks():
                        norm_track_title = normalize_string(track.title)
                        clean_track_title = normalize_string(clean_title_for_search(track.title))
                        
                        title_variants = [
                            (norm_title, norm_track_title),
                            (clean_norm_title, clean_track_title)
                        ]
                        
                        best_title_sim = 0
                        for src_title, target_title in title_variants:
                            this_sim = get_multi_similarity(src_title, target_title)
                            best_title_sim = max(best_title_sim, this_sim)
                        
                        if best_title_sim > 0.7:
                            album_sim = 0.0
                            if norm_album:
                                album_sim = get_multi_similarity(norm_album, normalize_string(album.title))
                            
                            score = (1.0 * 0.4) + (best_title_sim * 0.6)
                            if norm_album:
                                score = (score * 0.8) + (album_sim * 0.2)
                            
                            matches.append({
                                'track': track,
                                'artist_name': artist.title,
                                'album_name': album.title,
                                'score': score,
                                'artist_sim': 1.0,
                                'title_sim': best_title_sim,
                                'album_sim': album_sim if norm_album else None
                            })
            except Exception as e:
                print(f"Error searching tracks for artist {artist.title}: {e}")
        
        # Fuzzy search through all tracks as last resort
        if not matches:
            for indexed_title, track_infos in self.track_index.items():
                title_sim = get_multi_similarity(norm_title, indexed_title)
                clean_title_sim = get_multi_similarity(clean_norm_title, indexed_title)
                
                best_title_sim = max(title_sim, clean_title_sim)
                
                if best_title_sim > 0.8:
                    for track_info in track_infos:
                        track = track_info['track']
                        track_artist = track_info['artist']
                        
                        artist_sim = get_multi_similarity(norm_artist, normalize_string(track_artist.title))
                        
                        if artist_sim > 0.6:
                            album_sim = 0.0
                            if norm_album and track_info['album']:
                                album_sim = get_multi_similarity(norm_album, 
                                                               normalize_string(track_info['album'].title))
                            
                            score = (artist_sim * 0.4) + (best_title_sim * 0.6)
                            if norm_album:
                                score = (score * 0.8) + (album_sim * 0.2)
                            
                            matches.append({
                                'track': track,
                                'artist_name': track_artist.title,
                                'album_name': track_info['album'].title if track_info['album'] else None,
                                'score': score,
                                'artist_sim': artist_sim,
                                'title_sim': best_title_sim,
                                'album_sim': album_sim if norm_album else None
                            })
        
        return sorted(matches, key=lambda x: x['score'], reverse=True)