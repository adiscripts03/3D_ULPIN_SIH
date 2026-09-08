"""
Image Analyzer Service — 3D ULPIN AI/ML Pipeline
=================================================
Multi-purpose image analysis supporting:
  1. Automatic classification: is this a floor plan or exterior building photo?
  2. Floor plan → room boundary extraction (enhanced multi-strategy CV)
  3. Exterior photo → floor count + dimension estimation (Hough line detection)
  4. Quality scoring for video frame selection

Relies only on OpenCV + NumPy (no deep-learning dependencies needed).
"""

import cv2
import numpy as np
import math
from typing import Dict, Any, List, Tuple, Optional

IMAGE_TYPE_FLOOR_PLAN = "floor_plan"
IMAGE_TYPE_EXTERIOR   = "exterior_photo"
IMAGE_TYPE_UNKNOWN    = "unknown"


# ── 1. Image Type Classifier ──────────────────────────────────────────────────

def classify_image(image: np.ndarray) -> Dict[str, Any]:
    """
    Classify image as floor plan, exterior photo, or unknown.

    Heuristics:
      - Floor plans: white background (>60%), dense rectangular edges
      - Exterior photos: colourful, horizontal line patterns (floor slabs)
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    # Feature 1: White pixel ratio (floor plans are mostly white)
    _, binary = cv2.threshold(gray, 220, 255, cv2.THRESH_BINARY)
    white_ratio = float(np.sum(binary == 255)) / (h * w)

    # Feature 2: Edge density
    edges = cv2.Canny(gray, 50, 150)
    edge_density = float(np.sum(edges > 0)) / (h * w)

    # Feature 3: Mean colour saturation
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    mean_sat = float(np.mean(hsv[:, :, 1]))

    # Feature 4: Horizontal line count (exterior buildings have floor-slab lines)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=40,
                            minLineLength=w // 8, maxLineGap=20)
    h_lines = 0
    if lines is not None:
        for ln in lines:
            pts = ln[0] if len(ln) == 1 and hasattr(ln[0], '__len__') and len(ln[0]) == 4 else ln
            if len(pts) >= 4:
                x1, y1, x2, y2 = pts[0], pts[1], pts[2], pts[3]
                angle = abs(math.degrees(math.atan2(y2 - y1, x2 - x1)))
                if angle < 12 or angle > 168:
                    h_lines += 1

    # Feature 5: Rectangular contour count (floor plans have many rectangles)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    rect_count = 0
    for cnt in contours:
        if cv2.contourArea(cnt) > 200:
            approx = cv2.approxPolyDP(cnt, 0.02 * cv2.arcLength(cnt, True), True)
            if len(approx) == 4:
                rect_count += 1

    # Decision
    if white_ratio > 0.55 and edge_density > 0.015 and rect_count >= 3:
        image_type = IMAGE_TYPE_FLOOR_PLAN
        confidence = min(95.0, white_ratio * 60 + edge_density * 400 + rect_count * 3)
    elif mean_sat > 35 or h_lines >= 4:
        image_type = IMAGE_TYPE_EXTERIOR
        confidence = min(85.0, 40 + mean_sat * 0.5 + h_lines * 4)
    elif white_ratio > 0.4:
        # Probably a scanned document / floor plan with low quality
        image_type = IMAGE_TYPE_FLOOR_PLAN
        confidence = 55.0
    else:
        image_type = IMAGE_TYPE_UNKNOWN
        confidence = 30.0

    return {
        'image_type': image_type,
        'confidence': round(confidence, 1),
        'white_ratio': round(white_ratio, 3),
        'edge_density': round(edge_density, 4),
        'mean_saturation': round(mean_sat, 1),
        'horizontal_lines': h_lines,
        'rect_count': rect_count,
    }


def compute_sharpness(image: np.ndarray) -> float:
    """Laplacian variance — higher = sharper image. Used for video frame scoring."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


# ── 2. Floor Plan Room Extraction ─────────────────────────────────────────────

def _try_extract(gray: np.ndarray, block: int, C: int, blur: int,
                 h: int, w: int) -> List[Dict]:
    """Single extraction attempt with given preprocessing parameters."""
    blurred = cv2.GaussianBlur(gray, (blur, blur), 0)
    thresh = cv2.adaptiveThreshold(
        blurred, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV,
        block, C
    )
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)
    cnts, _ = cv2.findContours(closed, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    total_area = h * w
    boxes = []
    for cnt in cnts:
        area = cv2.contourArea(cnt)
        if total_area * 0.0012 < area < total_area * 0.65:
            x, y, bw, bh = cv2.boundingRect(cnt)
            ratio = max(bw, bh) / max(min(bw, bh), 1)
            if ratio <= 15:
                boxes.append({'x': x, 'y': y, 'w': bw, 'h': bh, 'area': float(area)})
    return boxes


def _nms(boxes: List[Dict], iou_thr: float = 0.60) -> List[Dict]:
    """Non-maximum suppression to deduplicate overlapping bounding boxes."""
    boxes = sorted(boxes, key=lambda b: b['area'], reverse=True)
    unique: List[Dict] = []
    for b in boxes:
        skip = False
        for u in unique:
            ix0 = max(b['x'], u['x']); iy0 = max(b['y'], u['y'])
            ix1 = min(b['x'] + b['w'], u['x'] + u['w'])
            iy1 = min(b['y'] + b['h'], u['y'] + u['h'])
            if ix1 > ix0 and iy1 > iy0:
                inter = (ix1 - ix0) * (iy1 - iy0)
                if inter > iou_thr * min(b['area'], u['area']):
                    skip = True
                    break
        if not skip:
            unique.append(b)
    return unique


def _classify_by_shape(area: float, aspect: float) -> str:
    """Rough room-type classification when OCR is unavailable."""
    if area < 5.0:
        return 'WASH' if aspect < 2.0 else 'CORR'
    if aspect > 5.0:
        return 'CORR'
    if 5.0 <= area <= 12.0 and 0.7 < aspect < 1.4:
        return 'STR'
    if area >= 20.0:
        return '4S'
    return '2S'


def extract_rooms_from_image(
    image: np.ndarray,
    scale_x: float = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Enhanced multi-strategy room extraction from a floor plan image.
    Tries 4 different preprocessing parameter sets; picks the best result.

    Returns:
        base_units:  List of room dicts ready for floor_plan_synthesizer / cadastral_engine
        diagnostics: Extraction quality metadata
    """
    h, w = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Try multiple preprocessing strategies
    strategies = [
        {'block': 15, 'C': 3, 'blur': 5},
        {'block': 21, 'C': 5, 'blur': 3},
        {'block': 11, 'C': 4, 'blur': 7},
        {'block': 25, 'C': 6, 'blur': 5},
    ]

    candidates = []
    for s in strategies:
        boxes = _try_extract(gray, s['block'], s['C'], s['blur'], h, w)
        if boxes:
            score = len(boxes) if len(boxes) <= 200 else max(0, 300 - len(boxes))
            candidates.append((score, boxes, s))

    if not candidates:
        return [], {'error': 'No rooms detected', 'strategies_tried': len(strategies)}

    # Pick strategy with the most "reasonable" room count
    _, best_boxes, best_strategy = max(candidates, key=lambda x: x[0])
    best_boxes = _nms(best_boxes)

    # Sort top-to-bottom, left-to-right
    best_boxes.sort(key=lambda b: (b['y'] // 40, b['x']))

    # Auto-scale: assume the widest extent ≈ 60m building width
    if scale_x is None:
        max_x = max(b['x'] + b['w'] for b in best_boxes) if best_boxes else w
        scale_x = 60.0 / max(max_x, 1)
    scale_y = scale_x

    base_units = []
    for idx, b in enumerate(best_boxes, 1):
        rx0 = round(b['x'] * scale_x, 2)
        rx1 = round((b['x'] + b['w']) * scale_x, 2)
        ry0 = round(b['y'] * scale_y, 2)
        ry1 = round((b['y'] + b['h']) * scale_y, 2)
        rw = max(rx1 - rx0, 0.5)
        rd = max(ry1 - ry0, 0.5)
        aspect = rw / max(rd, 0.1)
        ptype = _classify_by_shape(rw * rd, aspect)
        is_common = ptype in {'WASH', 'STR', 'LIFT', 'CORR', 'HALL', 'UTIL'}

        base_units.append({
            'label': f'IMG_{idx:03d}',
            'prop_id': f'X{idx:02d}',
            'type': ptype,
            'is_common_property': 1 if is_common else 0,
            'real_width_m': round(rw, 2),
            'real_depth_m': round(rd, 2),
            'real_x_start_m': rx0,
            'real_x_end_m': rx1,
            'real_y_start_m': ry0,
            'real_y_end_m': ry1,
            'real_y_center_m': round((ry0 + ry1) / 2, 2),
            'extraction_method': 'image_cv_enhanced',
            'ocr_confidence': 80.0,
        })

    diagnostics = {
        'total_extracted': len(base_units),
        'best_strategy': best_strategy,
        'strategies_tried': len(strategies),
        'image_size': f'{w}×{h}',
        'scale_x_m_per_px': round(scale_x, 5),
    }
    return base_units, diagnostics


# ── 3. Exterior Photo Analysis ────────────────────────────────────────────────

def analyze_exterior_photo(image: np.ndarray) -> Dict[str, Any]:
    """
    Analyse a building exterior photo to estimate:
      - Number of floors (horizontal slab lines)
      - Approximate units per floor (window grid)
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    edges = cv2.Canny(enhanced, 30, 100)

    # Detect horizontal lines (floor slabs)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=40,
                            minLineLength=w // 5, maxLineGap=30)
    h_y_vals: List[float] = []
    if lines is not None:
        for ln in lines:
            pts = ln[0] if len(ln) == 1 and hasattr(ln[0], '__len__') and len(ln[0]) == 4 else ln
            if len(pts) >= 4:
                x1, y1, x2, y2 = pts[0], pts[1], pts[2], pts[3]
                ang = abs(math.degrees(math.atan2(y2 - y1, x2 - x1)))
                if ang < 15 or ang > 165:
                    h_y_vals.append((y1 + y2) / 2.0)

    # Cluster Y positions → distinct floor lines
    floor_positions: List[float] = []
    if h_y_vals:
        h_y_vals.sort()
        clusters: List[List[float]] = [[h_y_vals[0]]]
        for y in h_y_vals[1:]:
            if y - clusters[-1][-1] < h * 0.06:
                clusters[-1].append(y)
            else:
                clusters.append([y])
        significant = [c for c in clusters if len(c) >= 2]
        floor_positions = [round(sum(c) / len(c), 1) for c in significant]

    detected_floors = max(len(floor_positions), 1)

    # Count window-like rectangular features as proxy for units per floor
    _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    roi = thresh[:int(h * 0.85), :]
    cnts, _ = cv2.findContours(255 - roi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    windows = []
    for cnt in cnts:
        area = cv2.contourArea(cnt)
        if 80 < area < h * w * 0.04:
            x, y, cw, ch = cv2.boundingRect(cnt)
            if 0.4 < cw / max(ch, 1) < 3.5:
                windows.append({'x': x, 'y': y, 'w': cw, 'h': ch})

    units_per_floor = max(2, len(windows) // max(detected_floors, 1))

    return {
        'detected_floors': detected_floors,
        'floor_line_y_positions': floor_positions,
        'estimated_units_per_floor': units_per_floor,
        'window_candidates': len(windows),
        'confidence': round(min(80.0, 25 + detected_floors * 6 + len(windows) * 1.5), 1),
    }


# ── 4. Main Entry Point ───────────────────────────────────────────────────────

def analyze_image(
    image: np.ndarray,
    scale_x: float = None,
) -> Dict[str, Any]:
    """
    Main entry: classify image and run appropriate analysis pipeline.

    Returns a unified result dict with either:
      - 'base_units' (for floor plan images) or
      - 'exterior_analysis' + 'detected_floors' (for exterior photos)
    """
    cls = classify_image(image)

    result: Dict[str, Any] = {
        'image_type': cls['image_type'],
        'classification': cls,
        'sharpness_score': round(compute_sharpness(image), 2),
    }

    if cls['image_type'] == IMAGE_TYPE_FLOOR_PLAN or cls['image_type'] == IMAGE_TYPE_UNKNOWN:
        units, diag = extract_rooms_from_image(image, scale_x)
        result['base_units'] = units
        result['extraction_diagnostics'] = diag
        result['total_rooms_detected'] = len(units)
    else:
        ext = analyze_exterior_photo(image)
        result['exterior_analysis'] = ext
        result['detected_floors'] = ext['detected_floors']
        result['estimated_units_per_floor'] = ext['estimated_units_per_floor']

    return result
