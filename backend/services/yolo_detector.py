"""
YOLO + Deep Learning Room Detector — 3D ULPIN AI/ML Pipeline
=============================================================
Uses YOLOv8 (Ultralytics) for:
  1. Floor plan room segmentation (YOLOv8-seg on architectural drawings)
  2. Building exterior analysis (floor count, window detection)
  3. Fallback to OpenCV if YOLO not available or confidence too low

Architecture:
  - Primary:  YOLOv8n-seg (nano, fast) for floor plan room boxes
  - Secondary: YOLOv8n for exterior building analysis  
  - Tertiary: OpenCV contour pipeline (always available, no GPU needed)

YOLO Categories mapped to 3D ULPIN room types:
  room       → residential (4S/2S based on size)
  bathroom   → WASH
  corridor   → CORR
  staircase  → STR
  elevator   → LIFT
  office     → OFFICE
  window     → (exterior: used to count units per floor)
  door       → (used to anchor room boundaries)
"""

import cv2
import numpy as np
import math
import os
from typing import Dict, Any, List, Optional, Tuple

# YOLO availability flag — degrades gracefully if ultralytics not installed
_YOLO_AVAILABLE = False
_yolo_model_seg = None
_yolo_model_det = None

try:
    from ultralytics import YOLO
    _YOLO_AVAILABLE = True
except ImportError:
    pass

# ── YOLO room-type mapping ────────────────────────────────────────────────────
YOLO_CLASS_TO_ULPIN: Dict[str, str] = {
    'room':        '4S',
    'bedroom':     '4S',
    'living room': '4S',
    'bathroom':    'WASH',
    'toilet':      'WASH',
    'washroom':    'WASH',
    'corridor':    'CORR',
    'hallway':     'CORR',
    'staircase':   'STR',
    'stairs':      'STR',
    'elevator':    'LIFT',
    'lift':        'LIFT',
    'office':      'OFFICE',
    'kitchen':     'UTIL',
    'lobby':       'LOBBY',
    'conference':  'CONF',
    'parking':     'PARK',
    'balcony':     'UTIL',
}

# Size thresholds (area in m² after scaling) to distinguish room types
SIZE_THRESHOLDS = {
    'large':  30.0,   # → 4S hostel / 3BHK
    'medium': 15.0,   # → 2S hostel / 2BHK  
    'small':   6.0,   # → WASH / utility
}


def _load_yolo_seg(model_name: str = 'yolov8n-seg.pt') -> Optional[Any]:
    """Load YOLOv8 segmentation model. Returns None if unavailable."""
    if not _YOLO_AVAILABLE:
        return None
    global _yolo_model_seg
    if _yolo_model_seg is not None:
        return _yolo_model_seg
    try:
        _yolo_model_seg = YOLO(model_name)
        return _yolo_model_seg
    except Exception:
        return None


def _load_yolo_det(model_name: str = 'yolov8n.pt') -> Optional[Any]:
    """Load YOLOv8 detection model. Returns None if unavailable."""
    if not _YOLO_AVAILABLE:
        return None
    global _yolo_model_det
    if _yolo_model_det is not None:
        return _yolo_model_det
    try:
        _yolo_model_det = YOLO(model_name)
        return _yolo_model_det
    except Exception:
        return None


# ── 1. YOLO Floor Plan Room Detection ────────────────────────────────────────

def detect_rooms_yolo(image: np.ndarray, scale_x: float = None,
                       conf_threshold: float = 0.25) -> Tuple[List[Dict], Dict]:
    """
    Use YOLOv8 to detect rooms in a floor plan image.
    Falls back to OpenCV if YOLO unavailable or detects <3 rooms.

    Returns:
        base_units: List of room dicts compatible with cadastral_engine
        diagnostics: Detection metadata
    """
    model = _load_yolo_seg()
    yolo_used = False
    yolo_rooms = []

    if model is not None:
        try:
            results = model(image, verbose=False, conf=conf_threshold)
            if results and len(results) > 0:
                r = results[0]
                boxes = r.boxes
                if boxes is not None and len(boxes) > 0:
                    for i, box in enumerate(boxes):
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        conf = float(box.conf[0].cpu().numpy())
                        cls_id = int(box.cls[0].cpu().numpy())
                        cls_name = model.names.get(cls_id, 'room').lower()
                        ulpin_type = YOLO_CLASS_TO_ULPIN.get(cls_name, '4S')
                        yolo_rooms.append({
                            'x': int(x1), 'y': int(y1),
                            'w': int(x2 - x1), 'h': int(y2 - y1),
                            'area': float((x2 - x1) * (y2 - y1)),
                            'conf': conf,
                            'cls_name': cls_name,
                            'ulpin_type': ulpin_type,
                        })
                    if len(yolo_rooms) >= 3:
                        yolo_used = True
        except Exception:
            pass

    # If YOLO didn't get enough detections, fall back to OpenCV
    if not yolo_used:
        from backend.services.advanced_cv_pipeline import detect_rooms_advanced_cv
        cv_rooms = detect_rooms_advanced_cv(image)
        boxes_raw = cv_rooms.get('boxes', [])
        base_units, diag = _boxes_to_base_units(boxes_raw, image.shape, scale_x,
                                                 method='opencv_fallback')
        diag['yolo_available'] = _YOLO_AVAILABLE
        diag['yolo_detections'] = 0
        diag['fallback_reason'] = 'yolo_insufficient_detections' if _YOLO_AVAILABLE else 'yolo_not_installed'
        return base_units, diag

    # Convert YOLO boxes → base_units
    base_units, diag = _boxes_to_base_units(yolo_rooms, image.shape, scale_x,
                                             method='yolov8_seg', is_yolo=True)
    diag['yolo_available'] = True
    diag['yolo_detections'] = len(yolo_rooms)
    diag['yolo_conf_threshold'] = conf_threshold
    return base_units, diag


def _boxes_to_base_units(boxes: List[Dict], img_shape: Tuple,
                          scale_x: float, method: str,
                          is_yolo: bool = False) -> Tuple[List[Dict], Dict]:
    """Convert raw bounding boxes to cadastral base_unit dicts."""
    h_img, w_img = img_shape[:2]

    if scale_x is None:
        max_x = max((b['x'] + b['w']) for b in boxes) if boxes else w_img
        scale_x = 60.0 / max(max_x, 1)
    scale_y = scale_x

    base_units = []
    for idx, b in enumerate(boxes, 1):
        rx0 = round(b['x'] * scale_x, 2)
        rx1 = round((b['x'] + b['w']) * scale_x, 2)
        ry0 = round(b['y'] * scale_y, 2)
        ry1 = round((b['y'] + b['h']) * scale_y, 2)
        rw = max(rx1 - rx0, 0.5)
        rd = max(ry1 - ry0, 0.5)
        area_m2 = rw * rd
        aspect = rw / max(rd, 0.1)

        # Determine room type
        if is_yolo and 'ulpin_type' in b:
            ptype = b['ulpin_type']
        else:
            ptype = _classify_by_size_and_shape(area_m2, aspect)

        is_common = ptype in {'WASH', 'STR', 'LIFT', 'CORR', 'HALL', 'UTIL', 'LOBBY', 'CONF', 'PARK'}
        conf = b.get('conf', 80.0) * 100.0 if is_yolo else 75.0

        base_units.append({
            'label': b.get('cls_name', f'{method}_{idx:03d}'),
            'prop_id': f'Y{idx:02d}' if is_yolo else f'C{idx:02d}',
            'type': ptype,
            'is_common_property': 1 if is_common else 0,
            'real_width_m': round(rw, 2),
            'real_depth_m': round(rd, 2),
            'real_x_start_m': rx0,
            'real_x_end_m': rx1,
            'real_y_start_m': ry0,
            'real_y_end_m': ry1,
            'real_y_center_m': round((ry0 + ry1) / 2, 2),
            'extraction_method': method,
            'ocr_confidence': round(conf, 2),
        })

    diag = {
        'total_extracted': len(base_units),
        'method': method,
        'scale_x_m_per_px': round(scale_x, 5),
        'image_size': f'{w_img}×{h_img}',
    }
    return base_units, diag


def _classify_by_size_and_shape(area_m2: float, aspect: float) -> str:
    """Classify room type by area and aspect ratio."""
    if area_m2 < 3.0:
        return 'UTIL'
    if area_m2 < SIZE_THRESHOLDS['small']:
        return 'WASH' if aspect < 2.0 else 'CORR'
    if aspect > 5.0:
        return 'CORR'
    if 5.0 <= area_m2 <= 12.0 and 0.7 < aspect < 1.4:
        return 'STR'
    if area_m2 >= SIZE_THRESHOLDS['large']:
        return '4S'
    if area_m2 >= SIZE_THRESHOLDS['medium']:
        return '2S'
    return '2S'


# ── 2. YOLO Exterior Building Analysis ───────────────────────────────────────

def analyze_exterior_yolo(image: np.ndarray) -> Dict[str, Any]:
    """
    Use YOLOv8 detection to analyze a building exterior photo.
    Detects windows, doors, and structural elements to estimate:
      - Floor count
      - Units per floor
      - Building width/depth estimate
    Falls back to OpenCV Hough-line analysis.
    """
    model = _load_yolo_det()
    yolo_windows = []
    yolo_used = False

    if model is not None:
        try:
            results = model(image, verbose=False, conf=0.20)
            if results and len(results) > 0:
                r = results[0]
                boxes = r.boxes
                if boxes is not None:
                    for box in boxes:
                        cls_id = int(box.cls[0].cpu().numpy())
                        cls_name = model.names.get(cls_id, '').lower()
                        if cls_name in ('window', 'door', 'building'):
                            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                            yolo_windows.append({
                                'cls': cls_name,
                                'x': float(x1), 'y': float(y1),
                                'w': float(x2 - x1), 'h': float(y2 - y1),
                                'cy': float((y1 + y2) / 2),
                                'conf': float(box.conf[0].cpu().numpy()),
                            })
                    if len(yolo_windows) >= 2:
                        yolo_used = True
        except Exception:
            pass

    if yolo_used:
        return _analyze_windows_from_yolo(image, yolo_windows)
    else:
        return _analyze_exterior_opencv(image)


def _analyze_windows_from_yolo(image: np.ndarray, detections: List[Dict]) -> Dict[str, Any]:
    """Estimate floor count from YOLO-detected windows by Y-clustering."""
    h, w = image.shape[:2]
    windows = [d for d in detections if d['cls'] == 'window']

    if not windows:
        return _analyze_exterior_opencv(image)

    # Cluster windows by Y-position → floors
    y_vals = sorted([win['cy'] for win in windows])
    clusters: List[List[float]] = [[y_vals[0]]]
    for y in y_vals[1:]:
        if y - clusters[-1][-1] < h * 0.08:
            clusters[-1].append(y)
        else:
            clusters.append([y])

    significant_clusters = [c for c in clusters if len(c) >= 1]
    detected_floors = max(len(significant_clusters), 1)
    units_per_floor = max(2, len(windows) // max(detected_floors, 1))

    return {
        'detected_floors': detected_floors,
        'estimated_units_per_floor': units_per_floor,
        'window_candidates': len(windows),
        'confidence': min(90.0, 50 + detected_floors * 5 + len(windows) * 2),
        'method': 'yolov8_detection',
        'floor_line_y_positions': [round(sum(c) / len(c), 1) for c in significant_clusters],
    }


def _analyze_exterior_opencv(image: np.ndarray) -> Dict[str, Any]:
    """OpenCV Hough-line based exterior analysis (enhanced)."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    # CLAHE enhancement for low-contrast building photos
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    # Multi-scale edge detection
    edges_tight = cv2.Canny(enhanced, 30, 90)
    edges_wide  = cv2.Canny(enhanced, 15, 60)
    edges = cv2.bitwise_or(edges_tight, edges_wide)

    # Detect horizontal lines (floor slabs / window sills)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=50,
                            minLineLength=w // 6, maxLineGap=40)
    h_y_vals: List[float] = []
    if lines is not None:
        for ln in lines:
            x1, y1, x2, y2 = ln[0]
            ang = abs(math.degrees(math.atan2(y2 - y1, x2 - x1)))
            if ang < 12 or ang > 168:
                h_y_vals.append((y1 + y2) / 2.0)

    # Cluster Y positions → distinct floor levels
    floor_positions: List[float] = []
    if h_y_vals:
        h_y_vals.sort()
        clusters_: List[List[float]] = [[h_y_vals[0]]]
        for y in h_y_vals[1:]:
            if y - clusters_[-1][-1] < h * 0.07:
                clusters_[-1].append(y)
            else:
                clusters_.append([y])
        significant = [c for c in clusters_ if len(c) >= 2]
        floor_positions = [round(sum(c) / len(c), 1) for c in significant]

    detected_floors = max(len(floor_positions), 1)

    # Window detection via Otsu + contours
    _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # Detect rectangular bright regions as windows
    cnts, _ = cv2.findContours(255 - thresh[:int(h * 0.88), :],
                                cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    windows = []
    for cnt in cnts:
        area = cv2.contourArea(cnt)
        if 100 < area < h * w * 0.035:
            x, y, cw, ch = cv2.boundingRect(cnt)
            if 0.3 < cw / max(ch, 1) < 3.5 and cw > 10:
                windows.append({'x': x, 'y': y, 'w': cw, 'h': ch})

    units_per_floor = max(2, len(windows) // max(detected_floors, 1))

    return {
        'detected_floors': detected_floors,
        'floor_line_y_positions': floor_positions,
        'estimated_units_per_floor': units_per_floor,
        'window_candidates': len(windows),
        'confidence': round(min(80.0, 25 + detected_floors * 7 + len(windows) * 1.5), 1),
        'method': 'opencv_hough_enhanced',
    }


# ── 3. Multi-Image Fusion ─────────────────────────────────────────────────────

def fuse_multi_image_predictions(
    floor_plan_result: Optional[Dict],
    exterior_result: Optional[Dict],
    room_photo_results: Optional[List[Dict]],
    text_params: Optional[Dict],
) -> Dict[str, Any]:
    """
    Fuse predictions from multiple image types into a single authoritative
    building parameter set. Priority: floor_plan > exterior > room_photos > text.

    Returns: unified params dict compatible with building_predictor.py
    """
    fused = {
        'total_floors': 5,
        'rooms_per_floor': 20,
        'room_types': ['4S', '2S'],
        'common_types': ['WASH', 'CORR', 'STR'],
        'residential_ratio': 0.80,
        'floor_pitch_m': 3.4,
        'room_clear_height_m': 2.9,
        'building_type': 'hostel',
        'building_name': 'AI Predicted College Building',
        'category': 'Institutional / Multi-Storey',
        'anchor_lat': 20.9495556,
        'anchor_lon': 79.0294722,
        'building_width_m': None,
        'building_depth_m': None,
        'confidence': 30.0,
        'fusion_sources': [],
    }

    # Start with text params as baseline
    if text_params and 'error' not in text_params:
        fused.update({
            'total_floors': text_params.get('total_floors', fused['total_floors']),
            'rooms_per_floor': text_params.get('rooms_per_floor', fused['rooms_per_floor']),
            'room_types': text_params.get('room_types', fused['room_types']),
            'floor_pitch_m': text_params.get('floor_pitch_m', fused['floor_pitch_m']),
            'building_type': text_params.get('building_type', fused['building_type']),
            'building_name': text_params.get('building_name', fused['building_name']),
            'anchor_lat': text_params.get('anchor_lat', fused['anchor_lat']),
            'anchor_lon': text_params.get('anchor_lon', fused['anchor_lon']),
            'building_width_m': text_params.get('building_width_m'),
            'building_depth_m': text_params.get('building_depth_m'),
        })
        fused['confidence'] = max(fused['confidence'], text_params.get('confidence', 30.0))
        fused['fusion_sources'].append('text_nlp')

    # Exterior photo supplements floor count
    if exterior_result and exterior_result.get('detected_floors', 0) > 1:
        ext_floors = exterior_result['detected_floors']
        ext_units = exterior_result.get('estimated_units_per_floor', 0)

        # Only override text if exterior is confident
        if exterior_result.get('confidence', 0) > 50:
            fused['total_floors'] = ext_floors
            fused['fusion_sources'].append('exterior_photo')
            if ext_units > 0 and 'text_nlp' not in fused['fusion_sources']:
                fused['rooms_per_floor'] = ext_units
        fused['confidence'] = min(95.0, fused['confidence'] + 15.0)

    # Room photos supplement room type inference
    if room_photo_results:
        room_types_seen = set()
        for rp in room_photo_results:
            rtype = rp.get('inferred_room_type', '4S')
            room_types_seen.add(rtype)
        if room_types_seen:
            residential = [r for r in room_types_seen if r in {'4S', '2S', '2BHK', '3BHK', '1BHK', 'OFFICE', 'WARD'}]
            if residential:
                fused['room_types'] = list(residential)[:2]
                fused['fusion_sources'].append('room_photos')
                fused['confidence'] = min(95.0, fused['confidence'] + 10.0)

    # Floor plan is highest authority — overrides everything for base_units
    if floor_plan_result and floor_plan_result.get('base_units'):
        fused['floor_plan_base_units'] = floor_plan_result['base_units']
        fused['fusion_sources'].append('floor_plan_image')
        fused['confidence'] = min(95.0, fused['confidence'] + 25.0)
        # Auto-detect rooms per floor from extraction
        fused['rooms_per_floor'] = len(floor_plan_result['base_units'])

    fused['confidence'] = round(fused['confidence'], 1)
    return fused


# ── 4. Room Photo Classifier ─────────────────────────────────────────────────

def classify_room_photo(image: np.ndarray) -> Dict[str, Any]:
    """
    Classify what type of room a photo shows.
    Uses colour, edge patterns, and YOLO (if available).
    Returns inferred_room_type in ULPIN codes.
    """
    h, w = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Feature extraction
    mean_brightness = float(np.mean(gray))
    mean_sat = float(np.mean(hsv[:, :, 1]))

    # Dominant hues
    hue_hist = cv2.calcHist([hsv], [0], None, [18], [0, 180])
    dominant_hue = int(np.argmax(hue_hist)) * 10  # degrees

    # Edge density & structure
    edges = cv2.Canny(gray, 50, 150)
    edge_density = float(np.sum(edges > 0)) / (h * w)

    # White tile pattern detection (bathroom)
    _, bin_img = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
    white_ratio = float(np.sum(bin_img == 255)) / (h * w)

    # Classify room type heuristically
    if white_ratio > 0.55 and mean_sat < 25:
        inferred = 'WASH'
        confidence = 75.0
    elif edge_density > 0.08 and mean_brightness < 80:
        inferred = 'CORR'
        confidence = 60.0
    elif mean_sat > 40 and mean_brightness > 120:
        inferred = '4S'
        confidence = 65.0
    elif white_ratio > 0.35:
        inferred = '2S'
        confidence = 55.0
    else:
        inferred = '4S'
        confidence = 45.0

    # Try YOLO for better classification
    model = _load_yolo_det()
    if model is not None:
        try:
            results = model(image, verbose=False, conf=0.25)
            if results and len(results) > 0:
                r = results[0]
                if r.boxes is not None and len(r.boxes) > 0:
                    cls_ids = [int(b.cls[0].cpu().numpy()) for b in r.boxes]
                    cls_names = [model.names.get(i, '').lower() for i in cls_ids]
                    for name in cls_names:
                        if name in YOLO_CLASS_TO_ULPIN:
                            inferred = YOLO_CLASS_TO_ULPIN[name]
                            confidence = 80.0
                            break
        except Exception:
            pass

    return {
        'inferred_room_type': inferred,
        'confidence': round(confidence, 1),
        'features': {
            'white_ratio': round(white_ratio, 3),
            'mean_brightness': round(mean_brightness, 1),
            'mean_saturation': round(mean_sat, 1),
            'edge_density': round(edge_density, 4),
        },
    }
