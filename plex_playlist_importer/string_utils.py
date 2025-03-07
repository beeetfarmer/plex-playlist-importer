import re
import unicodedata
from difflib import SequenceMatcher

# Required for string similarity functions
try:
    import Levenshtein
    from fuzzywuzzy import fuzz
except ImportError as e:
    raise ImportError(f"Missing required package - {e}. Please install with 'pip install python-Levenshtein fuzzywuzzy'")

def normalize_string(s):
    """Normalize string by removing accents, lowercasing, and removing special chars."""
    if not s:
        return ""
    
    s = s.lower()
    s = ''.join(c for c in unicodedata.normalize('NFD', s)
                if unicodedata.category(c) != 'Mn')
    s = re.sub(r'[^\w\s]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    
    return s

def get_multi_similarity(str1, str2):
    """Calculate string similarity using multiple algorithms and return a weighted score."""
    if not str1 or not str2:
        return 0.0
    
    norm1 = normalize_string(str1)
    norm2 = normalize_string(str2)
    
    if not norm1 or not norm2:
        return 0.0
    
    seq_ratio = SequenceMatcher(None, norm1, norm2).ratio()
    lev_ratio = 1 - (Levenshtein.distance(norm1, norm2) / max(len(norm1), len(norm2)))
    token_ratio = fuzz.token_sort_ratio(norm1, norm2) / 100
    
    if min(len(norm1), len(norm2)) <= 5:
        if norm1 == norm2:
            return 1.0
        exact_word_match = norm1 in norm2.split() or norm2 in norm1.split()
        if exact_word_match:
            return 0.9
    
    base1 = re.sub(r'\s*\(.*?\)', '', norm1).strip()
    base2 = re.sub(r'\s*\(.*?\)', '', norm2).strip()
    
    base_exact_match = 1.0 if base1 == base2 and len(base1) > 3 else 0.0
    
    paren1 = re.findall(r'\((.*?)\)', str1)
    paren2 = re.findall(r'\((.*?)\)', str2)
    
    paren_sim = 0.0
    if paren1 and paren2:
        paren_sim = max(SequenceMatcher(None, p1, p2).ratio() 
                        for p1 in paren1 for p2 in paren2)
    
    weights = {
        'seq': 0.3,
        'lev': 0.3,
        'token': 0.3,
        'base_exact': 0.5,
        'paren': 0.2
    }
    
    weighted_sim = (
        weights['seq'] * seq_ratio +
        weights['lev'] * lev_ratio +
        weights['token'] * token_ratio +
        weights['base_exact'] * base_exact_match +
        weights['paren'] * paren_sim
    )
    
    total_weight = sum(weights.values())
    normalized_sim = min(1.0, weighted_sim / total_weight)
    
    return normalized_sim

def clean_title_for_search(title):
    """Clean a title specifically for search purposes."""
    if not title:
        return ""
        
    cleaned = re.sub(r'\s*\(feat\..*?\)', '', title, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s*\(with.*?\)', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s*\(ft\..*?\)', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s*feat\..*?$', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s*ft\..*?$', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s*with.*?$', '', cleaned, flags=re.IGNORECASE)
    
    cleaned = re.sub(r'\s*\(.*?version\)', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s*\(.*?edit\)', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s*\(.*?mix\)', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s*\(.*?remaster.*?\)', '', cleaned, flags=re.IGNORECASE)
    
    cleaned = re.sub(r'\.\.\.', '', cleaned)
    cleaned = cleaned.replace('/', ' ')
    
    return cleaned.strip()