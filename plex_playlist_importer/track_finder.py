import re
from .string_utils import clean_title_for_search
from .library_index import PlexLibraryIndex

def find_track_advanced(plex, track_info, library_index=None, threshold=0.75, verbose=False):
    """Advanced track finding function that uses the indexed library."""
    artist = track_info['artist']
    title = track_info['title']
    album = track_info.get('album', None)
    
    print(f"Searching: {artist} - {title}")
    if verbose and album:
        print(f"  Album: {album}")
    
    # Special handling for songs with featured artists
    if 'feat.' in title or 'with' in title or '...' in title:
        clean_title = clean_title_for_search(title)
        if clean_title != title:
            print(f"  Clean title: {clean_title}")
    
    # Make sure we have an index
    if library_index is None or not library_index.initialized:
        print("  Library index not available. Building index...")
        library_index = PlexLibraryIndex(plex)
        library_index.build_index()
    
    # Find potential matches
    matches = library_index.find_track(artist, title, album)
    
    # For specific problematic tracks, lower the threshold slightly
    current_threshold = threshold
    if ('feat.' in title or 'with' in title or 
        artist.lower() in ['calvin harris', 'cobra starship', 'kelly clarkson']):
        current_threshold = max(0.7, threshold - 0.05)
        if verbose:
            print(f"  Using reduced threshold ({current_threshold}) for featured artist track")
    
    # Special case for titles with slash or joined words
    if not matches or matches[0]['score'] < current_threshold:
        alt_titles = [title]
        
        # Check for possible slash variations
        if '/' not in title and ' ' not in title:
            for i in range(1, len(title) - 1):
                if title[i].isupper():
                    alt_titles.append(title[:i] + '/' + title[i:])
                    alt_titles.append(title[:i] + ' ' + title[i:])
        
        # Check for slash to space conversion
        if '/' in title:
            alt_titles.append(title.replace('/', ' '))
        
        # Remove parentheses content if present
        if '(' in title:
            base_title = re.sub(r'\s*\(.*?\)', '', title).strip()
            alt_titles.append(base_title)
        
        # Try each alternative title
        for alt_title in alt_titles:
            if alt_title != title:
                print(f"  Trying alternative title: '{alt_title}'")
                alt_matches = library_index.find_track(artist, alt_title, album)
                
                if alt_matches and (not matches or alt_matches[0]['score'] > matches[0]['score']):
                    matches = alt_matches
    
    if matches:
        best_match = matches[0]
        
        if verbose:
            print(f"  Found {len(matches)} potential matches")
            print(f"  Best match: {best_match['artist_name']} - {best_match['track'].title}")
            print(f"    Score: {best_match['score']:.4f}")
            print(f"    Artist similarity: {best_match['artist_sim']:.4f}")
            print(f"    Title similarity: {best_match['title_sim']:.4f}")
            if best_match['album_sim'] is not None:
                print(f"    Album similarity: {best_match['album_sim']:.4f}")
        
        # Accept match if score is above threshold
        if best_match['score'] >= current_threshold:
            print(f"  Found match: {best_match['artist_name']} - {best_match['track'].title}")
            return best_match['track']
        else:
            print(f" Best match below threshold ({best_match['score']:.4f} < {current_threshold})")
            print(f" Rejected: {best_match['artist_name']} - {best_match['track'].title}")
            return None
    else:
        print("  No potential matches found")
        return None