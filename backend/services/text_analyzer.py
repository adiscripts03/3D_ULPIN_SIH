"""
Text Analyzer Service — 3D ULPIN AI/ML Pipeline
================================================
Parses natural language building descriptions into structured building parameters.

Handles inputs like:
  - "10-floor hostel with 56 rooms per floor, 4-seater and 2-seater rooms"
  - "G+9 residential apartment, 4 units per floor, near 20.95N 79.03E"
  - "Office building, 5 storeys, open plan, 60m x 40m footprint"
  - "Hospital with 8 floors, 20 wards per floor, ICU on ground floor"
"""

import re
import math
from typing import Dict, Any, List, Optional

# ── Word → Integer lookup ──────────────────────────────────────────────────────
WORD_TO_INT: Dict[str, int] = {
    'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
    'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
    'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15,
    'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19, 'twenty': 20,
    'twenty-five': 25, 'thirty': 30, 'forty': 40, 'fifty': 50,
}

# ── Building type profiles ─────────────────────────────────────────────────────
BUILDING_PROFILES: Dict[str, Dict[str, Any]] = {
    'hostel': {
        'category': 'Student Residence',
        'floor_pitch_m': 3.4,
        'room_clear_height_m': 2.9,
        'room_types': ['4S', '2S'],
        'common_types': ['WASH', 'CORR', 'STR', 'LIFT'],
        'residential_ratio': 0.80,
        'default_rooms_per_floor': 56,
        'room_dims': {'4S': (6.0, 5.0), '2S': (4.5, 5.0)},
    },
    'apartment': {
        'category': 'Residential Apartments',
        'floor_pitch_m': 3.2,
        'room_clear_height_m': 2.7,
        'room_types': ['2BHK', '3BHK', '1BHK'],
        'common_types': ['LOBBY', 'CORR', 'STR', 'LIFT', 'UTIL'],
        'residential_ratio': 0.75,
        'default_rooms_per_floor': 8,
        'room_dims': {'2BHK': (8.5, 12.0), '3BHK': (11.0, 14.0), '1BHK': (6.0, 9.0)},
    },
    'office': {
        'category': 'Commercial / Office',
        'floor_pitch_m': 3.8,
        'room_clear_height_m': 3.2,
        'room_types': ['OFFICE', 'CABIN'],
        'common_types': ['CONF', 'CORR', 'STR', 'LIFT', 'LOBBY'],
        'residential_ratio': 0.65,
        'default_rooms_per_floor': 12,
        'room_dims': {'OFFICE': (6.0, 5.0), 'CABIN': (4.0, 4.0)},
    },
    'hospital': {
        'category': 'Healthcare',
        'floor_pitch_m': 4.0,
        'room_clear_height_m': 3.5,
        'room_types': ['WARD', 'ICU'],
        'common_types': ['CORR', 'STR', 'LIFT', 'UTIL', 'NURSE', 'WASH'],
        'residential_ratio': 0.60,
        'default_rooms_per_floor': 20,
        'room_dims': {'WARD': (7.0, 9.0), 'ICU': (5.0, 7.0)},
    },
    'hotel': {
        'category': 'Hospitality',
        'floor_pitch_m': 3.6,
        'room_clear_height_m': 3.0,
        'room_types': ['DBLBED', 'SUITE'],
        'common_types': ['CORR', 'STR', 'LIFT', 'LOBBY'],
        'residential_ratio': 0.80,
        'default_rooms_per_floor': 20,
        'room_dims': {'DBLBED': (6.0, 7.0), 'SUITE': (8.0, 10.0)},
    },
    'commercial': {
        'category': 'Commercial / Retail',
        'floor_pitch_m': 4.0,
        'room_clear_height_m': 3.5,
        'room_types': ['SHOP', 'RETAIL'],
        'common_types': ['CORR', 'STR', 'LIFT', 'UTIL'],
        'residential_ratio': 0.70,
        'default_rooms_per_floor': 16,
        'room_dims': {'SHOP': (5.0, 6.0), 'RETAIL': (8.0, 10.0)},
    },
}

DEFAULT_PROFILE = BUILDING_PROFILES['hostel']


# ── Individual extractors ──────────────────────────────────────────────────────

def extract_floor_count(text: str) -> Optional[int]:
    """Extract total floor count from text. Returns None if not found."""
    t = text.lower()

    # G+N notation (e.g. G+10 = 11 floors total)
    m = re.search(r'g\s*\+\s*(\d+)', t)
    if m:
        return int(m.group(1)) + 1

    # Digit before floor keyword
    m = re.search(r'(\d+)\s*[\-\s]?(?:floor|floors|storey|storeys|story|stories|level|levels)', t)
    if m:
        n = int(m.group(1))
        if 1 <= n <= 200:
            return n

    # Floor keyword then digit
    m = re.search(r'(?:floor|storey|story|level)s?\s*[:\-=]?\s*(\d+)', t)
    if m:
        n = int(m.group(1))
        if 1 <= n <= 200:
            return n

    # Word numbers before floor
    for word, num in WORD_TO_INT.items():
        if re.search(rf'\b{word}\s*[\-\s]?(?:floor|storey|story|level)', t):
            return num

    return None


def extract_rooms_per_floor(text: str) -> Optional[int]:
    """Extract rooms per floor from text. Returns None if not found."""
    t = text.lower()
    patterns = [
        r'(\d+)\s*(?:rooms?|units?|flats?|apartments?|beds?)\s*(?:per|each|on each)\s*(?:floor|level|storey)',
        r'(?:per|each)\s+(?:floor|level)\s+(?:has|have|with|contains?)\s*(\d+)\s*(?:rooms?|units?)',
        r'(\d+)\s*(?:rooms?|units?)\s*per\s*floor',
        r'each\s+floor\s+(?:has|contains?|includes?)\s*(\d+)\s*(?:rooms?|units?)',
    ]
    for pattern in patterns:
        m = re.search(pattern, t)
        if m:
            n = int(m.group(1))
            if 1 <= n <= 500:
                return n
    return None


def extract_total_rooms(text: str) -> Optional[int]:
    """Extract total room count from text."""
    t = text.lower()
    patterns = [
        r'(\d+)\s*(?:rooms?|units?|flats?|beds?)\s*(?:total|in total|altogether)',
        r'total\s+(?:of\s+)?(\d+)\s*(?:rooms?|units?)',
        r'(\d+)\s*(?:rooms?|units?)\s*(?:across|throughout)',
    ]
    for pattern in patterns:
        m = re.search(pattern, t)
        if m:
            n = int(m.group(1))
            if 1 <= n <= 50000:
                return n
    return None


def extract_building_type(text: str) -> str:
    """Determine building type from text keywords."""
    t = text.lower()
    keywords = {
        'hostel': ['hostel', 'dormitory', 'dorm', 'pg', 'boarding', 'student housing', 'student residence'],
        'apartment': ['apartment', 'flat', 'residential', 'bhk', 'condominium', 'housing society', 'society'],
        'office': ['office', 'corporate', 'workspace', 'it park', 'business park', 'commercial complex'],
        'hospital': ['hospital', 'clinic', 'healthcare', 'medical', 'ward', 'icu', 'nursing home'],
        'hotel': ['hotel', 'resort', 'inn', 'lodge', 'motel', 'service apartment'],
        'commercial': ['mall', 'shopping', 'retail', 'market', 'showroom', 'shop'],
    }
    for btype, kws in keywords.items():
        for kw in kws:
            if kw in t:
                return btype
    return 'hostel'


def extract_room_types(text: str, building_type: str) -> List[str]:
    """Extract specific room type codes mentioned in text."""
    t = text.lower()
    profile = BUILDING_PROFILES.get(building_type, DEFAULT_PROFILE)

    type_kw_map = {
        '4S': ['4-seater', '4 seater', 'four seater', '4s', 'quad'],
        '2S': ['2-seater', '2 seater', 'two seater', '2s', 'twin'],
        '2BHK': ['2bhk', '2-bhk', 'two bedroom', '2 bedroom'],
        '3BHK': ['3bhk', '3-bhk', 'three bedroom', '3 bedroom'],
        '1BHK': ['1bhk', '1-bhk', 'studio', 'one bedroom'],
        'OFFICE': ['open office', 'open plan', 'workspace'],
        'CABIN': ['cabin', 'private office', 'individual office'],
        'WARD': ['ward', 'patient room', 'general ward'],
        'ICU': ['icu', 'intensive care', 'critical care'],
        'DBLBED': ['double bed', 'double room', 'twin bed'],
        'SUITE': ['suite', 'deluxe room'],
        'SHOP': ['shop', 'retail unit', 'showroom'],
    }

    found = []
    for code, kws in type_kw_map.items():
        for kw in kws:
            if kw in t and code not in found:
                found.append(code)

    return found if found else profile['room_types'][:2]


def extract_dimensions(text: str) -> Dict[str, Optional[float]]:
    """Extract building footprint dimensions if mentioned."""
    t = text.lower()
    patterns = [
        r'(\d+(?:\.\d+)?)\s*m\s*[×x\*by]+\s*(\d+(?:\.\d+)?)\s*m',
        r'(\d+(?:\.\d+)?)\s*(?:meter|metre)s?\s*(?:wide|width).*?(\d+(?:\.\d+)?)\s*(?:meter|metre)s?\s*(?:deep|depth)',
        r'(\d+(?:\.\d+)?)\s*(?:feet|ft)\s*[×x]+\s*(\d+(?:\.\d+)?)\s*(?:feet|ft)',
    ]
    for pattern in patterns:
        m = re.search(pattern, t)
        if m:
            w, d = float(m.group(1)), float(m.group(2))
            if 'feet' in pattern or 'ft' in pattern:
                w, d = w * 0.3048, d * 0.3048
            if 5.0 <= w <= 500.0 and 5.0 <= d <= 500.0:
                return {'width_m': w, 'depth_m': d}
    return {'width_m': None, 'depth_m': None}


def extract_gps(text: str) -> Dict[str, float]:
    """Extract GPS coordinates if mentioned, else return IIIT Nagpur defaults."""
    # Pattern: 20.9495N, 79.0294E  or  lat:20.9495 lon:79.0294
    m = re.search(r'(\d{1,3}\.\d+)\s*[°\s]*[Nn],?\s*(\d{1,3}\.\d+)\s*[°\s]*[Ee]', text)
    if m:
        lat, lon = float(m.group(1)), float(m.group(2))
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            return {'lat': lat, 'lon': lon}
    m = re.search(r'lat(?:itude)?\s*[:\=]?\s*(\d{1,3}\.\d+).*?lon(?:gitude)?\s*[:\=]?\s*(\d{1,3}\.\d+)', text, re.IGNORECASE)
    if m:
        lat, lon = float(m.group(1)), float(m.group(2))
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            return {'lat': lat, 'lon': lon}
    return {'lat': 20.9495556, 'lon': 79.0294722}  # Default: IIIT Nagpur


def extract_building_name(text: str, building_type: str) -> str:
    """Try to extract a building name from text."""
    m = re.search(r'(?:called?|named?|known as|building[:\s]+)["\']?([A-Z][a-zA-Z\s\-]+)["\']?', text)
    if m:
        return m.group(1).strip()[:50]
    return f"AI Predicted {building_type.capitalize()} Block"


def extract_floor_height(text: str, profile: Dict) -> float:
    """Extract floor-to-floor height if mentioned."""
    t = text.lower()
    m = re.search(r'(\d+(?:\.\d+)?)\s*m\s*(?:floor\s*(?:to|height)|clear\s*height|ceiling)', t)
    if m:
        h = float(m.group(1))
        if 2.0 <= h <= 8.0:
            return h
    return profile['floor_pitch_m']


# ── Main Entry Point ───────────────────────────────────────────────────────────

def analyze_text(text: str) -> Dict[str, Any]:
    """
    Main entry: parse text description → structured building parameters.

    Returns dict with fields compatible with BuildingConfig and the synthesizer.
    """
    if not text or not text.strip():
        return {'error': 'Empty text input provided.'}

    building_type = extract_building_type(text)
    profile = BUILDING_PROFILES.get(building_type, DEFAULT_PROFILE)

    floors = extract_floor_count(text) or 5
    rooms_per_floor = extract_rooms_per_floor(text)
    total_rooms = extract_total_rooms(text)

    # Resolve rooms per floor
    if rooms_per_floor is None:
        if total_rooms is not None:
            rooms_per_floor = max(2, total_rooms // floors)
        else:
            rooms_per_floor = profile['default_rooms_per_floor']

    room_types = extract_room_types(text, building_type)
    dims = extract_dimensions(text)
    gps = extract_gps(text)
    building_name = extract_building_name(text, building_type)
    floor_pitch = extract_floor_height(text, profile)

    # Confidence score
    confidence = 50.0
    if extract_floor_count(text): confidence += 20
    if extract_rooms_per_floor(text): confidence += 20
    if len(text.split()) > 15: confidence += 10
    confidence = min(100.0, confidence)

    return {
        'building_type': building_type,
        'building_name': building_name,
        'category': profile['category'],
        'total_floors': floors,
        'rooms_per_floor': rooms_per_floor,
        'room_types': room_types,
        'common_types': profile['common_types'],
        'residential_ratio': profile['residential_ratio'],
        'floor_pitch_m': floor_pitch,
        'room_clear_height_m': profile['room_clear_height_m'],
        'anchor_lat': gps['lat'],
        'anchor_lon': gps['lon'],
        'building_width_m': dims.get('width_m'),
        'building_depth_m': dims.get('depth_m'),
        'profile': profile,
        'extraction_method': 'text_nlp',
        'confidence': round(confidence, 1),
    }
