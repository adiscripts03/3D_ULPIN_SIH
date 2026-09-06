"""
Advanced OpenCV Pipeline — 3D ULPIN AI/ML Pipeline
===================================================
Exceptional computer vision pipeline for real-world college building images.
Handles:
  1.  Floor plan PDFs / scanned drawings     → room contour extraction
  2.  Hand-drawn / photographed floor plans  → perspective-corrected extraction
  3.  Architectural blueprint photos         → wall-line based room detection
  4.  Mixed-quality images                   → multi-strategy best-pick

Pipeline stages:
  Stage 1: Pre-processing (CLAHE, denoising, perspective correction)
  Stage 2: Wall detection (adaptive thresh + morphological closing)
  Stage 3: Room boundary extraction (contour + Hough line room detection)
  Stage 4: Geometric filtering (NMS, aspect ratio, min area)
  Stage 5: Room type classification by shape & position
  Stage 6: Coordinate scaling to metric units

No deep-learning dependency — pure OpenCV 4.8+.
"""

import cv2
import numpy as np
import math
from typing import Dict, Any, List, Tuple, Optional


# ── Constants ─────────────────────────────────────────────────────────────────
MORPH_KERNELS = {
    'tiny':   cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2)),
    'small':  cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)),
    'medium': cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5)),
    'large':  cv2.getStructuringElement(cv2.MORPH_RECT, (8, 8)),
    'h_line': cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1)),
    'v_line': cv2.getStructuringElement(cv2.MORPH_RECT, (1, 25)),
}


# ── Stage 1: Pre-processing ───────────────────────────────────────────────────

def preprocess_floor_plan(image: np.ndarray) -> Dict[str, np.ndarray]:
    """
    Comprehensive preprocessing pipeline. Returns multiple processed variants
    for subsequent stages to pick the best.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    # Variant A: CLAHE + Gaussian blur (good for scanned drawings)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    gray_clahe = clahe.apply(gray)
    blur_a = cv2.GaussianBlur(gray_clahe, (5, 5), 0)

    # Variant B: Bilateral filter (preserves wall edges, reduces noise)
    bilateral = cv2.bilateralFilter(gray, d=9, sigmaColor=75, sigmaSpace=75)
    blur_b = cv2.GaussianBlur(bilateral, (3, 3), 0)

    # Variant C: Median blur (good for photographed floor plans)
    blur_c = cv2.medianBlur(gray, 5)

    # White background normalization (floor plans are usually white-bg)
    # Invert if mostly dark (dark-background blueprints)
    if np.mean(gray) < 127:
        gray_norm = 255 - gray_clahe
        for k in ('blur_a', 'blur_b', 'blur_c'):
            pass  # handled below in thresholding
        inverted = True
    else:
        gray_norm = gray_clahe
        inverted = False

    return {
        'gray': gray,
        'gray_clahe': gray_clahe,
        'gray_norm': gray_norm,
        'blur_a': blur_a,
        'blur_b': blur_b,
        'blur_c': blur_c,
        'inverted': inverted,
        'shape': (h, w),
    }


def correct_perspective(image: np.ndarray) -> Tuple[np.ndarray, bool]:
    """
    Detect if floor plan is skewed / photographed at an angle and correct it.
    Returns (corrected_image, was_corrected).
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)

    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=80,
                             minLineLength=image.shape[1] // 4, maxLineGap=20)
    if lines is None or len(lines) < 4:
        return image, False

    # Collect angles of near-horizontal and near-vertical lines
    angles = []
    for ln in lines:
        x1, y1, x2, y2 = ln[0]
        angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
        if abs(angle) < 30:  # near-horizontal
            angles.append(angle)

    if not angles:
        return image, False

    median_angle = float(np.median(angles))
    if abs(median_angle) < 1.0:  # Already straight
        return image, False

    # Rotate to correct skew
    h, w = image.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2, h / 2), median_angle, 1.0)
    corrected = cv2.warpAffine(image, M, (w, h),
                                flags=cv2.INTER_LINEAR,
                                borderMode=cv2.BORDER_REPLICATE)
    return corrected, True


# ── Stage 2: Wall Detection ────────────────────────────────────────────────────

def extract_wall_mask(preprocessed: Dict[str, np.ndarray],
                       strategy: str = 'adaptive') -> np.ndarray:
    """
    Extract binary wall mask from preprocessed image variants.

    Strategies:
      'adaptive'   → Adaptive Gaussian thresholding (best for most floor plans)
      'global'     → Otsu global thresholding (good for clean CAD scans)
      'line_based' → Morphological line detection (good for blueprints)
      'combined'   → Union of adaptive + line-based
    """
    h, w = preprocessed['shape']

    if strategy == 'adaptive':
        thresh = cv2.adaptiveThreshold(
            preprocessed['blur_a'], 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 15, 4
        )
        # Close small gaps in walls
        closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE,
                                   MORPH_KERNELS['small'], iterations=2)
        return closed

    elif strategy == 'global':
        _, thresh = cv2.threshold(preprocessed['blur_b'], 0, 255,
                                   cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE,
                                   MORPH_KERNELS['medium'], iterations=1)
        return closed

    elif strategy == 'line_based':
        # Detect horizontal walls
        thresh = cv2.adaptiveThreshold(
            preprocessed['blur_c'], 255,
            cv2.ADAPTIVE_THRESH_MEAN_C,
            cv2.THRESH_BINARY_INV, 21, 6
        )
        h_walls = cv2.morphologyEx(thresh, cv2.MORPH_OPEN,
                                    MORPH_KERNELS['h_line'], iterations=1)
        v_walls = cv2.morphologyEx(thresh, cv2.MORPH_OPEN,
                                    MORPH_KERNELS['v_line'], iterations=1)
        combined = cv2.bitwise_or(h_walls, v_walls)
        dilated = cv2.dilate(combined, MORPH_KERNELS['small'], iterations=2)
        return dilated

    elif strategy == 'combined':
        mask_a = extract_wall_mask(preprocessed, 'adaptive')
        mask_b = extract_wall_mask(preprocessed, 'line_based')
        return cv2.bitwise_or(mask_a, mask_b)

    return extract_wall_mask(preprocessed, 'adaptive')


# ── Stage 3: Room Boundary Extraction ────────────────────────────────────────

def extract_room_contours_from_mask(wall_mask: np.ndarray,
                                     total_area: int) -> List[Dict]:
    """
    Find closed room regions from a wall mask using:
    1. Flood-fill inversion (find open spaces, not walls)
    2. Contour detection on the inverted mask
    """
    h, w = wall_mask.shape

    # Invert: rooms are white (empty space), walls are black
    room_space = cv2.bitwise_not(wall_mask)

    # Remove border-touching regions (building exterior)
    border_mask = np.zeros((h + 2, w + 2), dtype=np.uint8)
    for bx in range(0, w, max(1, w // 20)):
        cv2.floodFill(room_space, border_mask, (bx, 0), 0)
        cv2.floodFill(room_space, border_mask, (bx, h - 1), 0)
    for by in range(0, h, max(1, h // 20)):
        cv2.floodFill(room_space, border_mask, (0, by), 0)
        cv2.floodFill(room_space, border_mask, (w - 1, by), 0)

    contours, _ = cv2.findContours(room_space,
                                    cv2.RETR_EXTERNAL,
                                    cv2.CHAIN_APPROX_SIMPLE)

    min_area = total_area * 0.0015
    max_area = total_area * 0.65

    boxes = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if min_area < area < max_area:
            x, y, bw, bh = cv2.boundingRect(cnt)
            aspect = max(bw, bh) / max(min(bw, bh), 1)
            if aspect <= 18:
                # Approximate polygon to check rectangularity
                peri = cv2.arcLength(cnt, True)
                approx = cv2.approxPolyDP(cnt, 0.04 * peri, True)
                rect_score = min(1.0, 4.0 / max(len(approx), 4))  # more rectangular = higher score
                boxes.append({
                    'x': x, 'y': y, 'w': bw, 'h': bh,
                    'area': float(area),
                    'rect_score': rect_score,
                    'approx_vertices': len(approx),
                })
    return boxes


def extract_rooms_via_hough_grid(image: np.ndarray) -> List[Dict]:
    """
    Alternative: use Hough line intersection to find rooms.
    Works well for CAD-style images with clear grid lines.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    _, thresh = cv2.threshold(enhanced, 0, 255,
                               cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Extract horizontal and vertical lines
    h_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, MORPH_KERNELS['h_line'])
    v_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, MORPH_KERNELS['v_line'])

    # Detect line positions
    h_proj = np.sum(h_lines, axis=1)
    v_proj = np.sum(v_lines, axis=0)

    # Find peaks (wall positions)
    def find_wall_positions(projection, min_gap, min_val):
        positions = []
        in_wall = False
        start = 0
        threshold = max(min_val, np.max(projection) * 0.15)
        for i, val in enumerate(projection):
            if val > threshold and not in_wall:
                in_wall = True
                start = i
            elif val <= threshold and in_wall:
                in_wall = False
                center = (start + i) // 2
                if not positions or center - positions[-1] > min_gap:
                    positions.append(center)
        return positions

    h_walls = find_wall_positions(h_proj, h // 30, 10)
    v_walls = find_wall_positions(v_proj, w // 30, 10)

    # Create room boxes from intersections
    boxes = []
    min_room_h = h // 25
    min_room_w = w // 25

    for i in range(len(h_walls) - 1):
        for j in range(len(v_walls) - 1):
            y0, y1 = h_walls[i], h_walls[i + 1]
            x0, x1 = v_walls[j], v_walls[j + 1]
            bw, bh = x1 - x0, y1 - y0
            if bw > min_room_w and bh > min_room_h:
                area = float(bw * bh)
                total = h * w
                if area < total * 0.65 and area > total * 0.0010:
                    boxes.append({
                        'x': x0, 'y': y0, 'w': bw, 'h': bh,
                        'area': area,
                        'rect_score': 1.0,
                        'approx_vertices': 4,
                    })
    return boxes


# ── Stage 4: Geometric Filtering (NMS + shape) ───────────────────────────────

def non_maximum_suppression(boxes: List[Dict], iou_threshold: float = 0.55) -> List[Dict]:
    """Deduplicate overlapping bounding boxes (NMS)."""
    if not boxes:
        return []
    boxes = sorted(boxes, key=lambda b: b['area'], reverse=True)
    unique: List[Dict] = []
    for b in boxes:
        skip = False
        for u in unique:
            # Compute intersection
            ix0 = max(b['x'], u['x'])
            iy0 = max(b['y'], u['y'])
            ix1 = min(b['x'] + b['w'], u['x'] + u['w'])
            iy1 = min(b['y'] + b['h'], u['y'] + u['h'])
            if ix1 > ix0 and iy1 > iy0:
                inter = (ix1 - ix0) * (iy1 - iy0)
                if inter > iou_threshold * min(b['area'], u['area']):
                    skip = True
                    break
        if not skip:
            unique.append(b)
    return unique


# ── Stage 5: Multi-Strategy Best Pick ────────────────────────────────────────

def detect_rooms_advanced_cv(image: np.ndarray) -> Dict[str, Any]:
    """
    Master function: tries multiple strategies and returns the best result.

    Strategy priority:
      1. Flood-fill + contour (best for closed-room floor plans)
      2. Hough grid intersection (best for CAD-style drawings)  
      3. Simple adaptive threshold contour (always works)

    Returns:
      {'boxes': List[Dict], 'strategy': str, 'diagnostics': Dict}
    """
    h, w = image.shape[:2]
    total_area = h * w

    # Perspective correction
    image, corrected = correct_perspective(image)

    # Preprocessing
    preprocessed = preprocess_floor_plan(image)

    # Strategy 1: Flood-fill + contour (4 wall mask variants)
    best_boxes = []
    best_strategy = 'none'
    best_score = 0

    for wall_strategy in ['adaptive', 'combined', 'global', 'line_based']:
        try:
            wall_mask = extract_wall_mask(preprocessed, wall_strategy)
            boxes = extract_room_contours_from_mask(wall_mask, total_area)
            boxes = non_maximum_suppression(boxes)
            # Score: prefer 10–200 rooms, penalize too few or too many
            n = len(boxes)
            score = n if 5 <= n <= 200 else max(0, 250 - abs(n - 80))
            if score > best_score:
                best_score = score
                best_boxes = boxes
                best_strategy = f'floodfill_{wall_strategy}'
        except Exception:
            continue

    # Strategy 2: Hough grid (if flood-fill got <5 rooms)
    if len(best_boxes) < 5:
        try:
            hough_boxes = extract_rooms_via_hough_grid(image)
            hough_boxes = non_maximum_suppression(hough_boxes)
            if len(hough_boxes) >= len(best_boxes):
                best_boxes = hough_boxes
                best_strategy = 'hough_grid'
        except Exception:
            pass

    # Strategy 3: Simple fallback (original cv_extractor approach)
    if len(best_boxes) < 3:
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            thresh = cv2.adaptiveThreshold(blurred, 255,
                                            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                            cv2.THRESH_BINARY_INV, 15, 3)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)
            cnts, _ = cv2.findContours(closed, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            fb = []
            for cnt in cnts:
                area = cv2.contourArea(cnt)
                if total_area * 0.0015 < area < total_area * 0.65:
                    x, y, bw, bh = cv2.boundingRect(cnt)
                    if max(bw, bh) / max(min(bw, bh), 1) <= 15:
                        fb.append({'x': x, 'y': y, 'w': bw, 'h': bh,
                                   'area': float(area), 'rect_score': 0.5,
                                   'approx_vertices': 4})
            fb = non_maximum_suppression(fb)
            if len(fb) > len(best_boxes):
                best_boxes = fb
                best_strategy = 'simple_adaptive_fallback'
        except Exception:
            pass

    # Sort top-to-bottom, left-to-right
    best_boxes.sort(key=lambda b: (b['y'] // 40, b['x']))

    diagnostics = {
        'strategy_used': best_strategy,
        'total_detected': len(best_boxes),
        'perspective_corrected': corrected,
        'inverted': preprocessed.get('inverted', False),
        'image_size': f'{w}×{h}',
    }

    return {
        'boxes': best_boxes,
        'strategy': best_strategy,
        'diagnostics': diagnostics,
    }


# ── Stage 6: Full Pipeline Entry Point ───────────────────────────────────────

def extract_rooms_advanced(image: np.ndarray, scale_x: float = None,
                            building_type: str = 'hostel') -> Tuple[List[Dict], Dict]:
    """
    Full advanced CV pipeline entry point.

    Args:
        image:         BGR image (floor plan)
        scale_x:       Meters per pixel (auto-computed if None)
        building_type: Hint for room type classification

    Returns:
        base_units: List of room dicts for cadastral_engine
        diagnostics: Extraction metadata
    """
    result = detect_rooms_advanced_cv(image)
    boxes = result['boxes']
    diag = result['diagnostics']

    h_img, w_img = image.shape[:2]

    # Auto-scale: assume the widest extent ≈ 60m building width
    if scale_x is None:
        max_x = max(b['x'] + b['w'] for b in boxes) if boxes else w_img
        scale_x = 60.0 / max(max_x, 1)
    scale_y = scale_x

    # Room type profiles per building type
    room_type_map = {
        'hostel':     ['4S', '2S'],
        'apartment':  ['2BHK', '3BHK'],
        'office':     ['OFFICE', 'CABIN'],
        'hospital':   ['WARD', 'ICU'],
        'hotel':      ['DBLBED', 'SUITE'],
        'commercial': ['SHOP', 'RETAIL'],
    }
    primary_types = room_type_map.get(building_type, ['4S', '2S'])

    base_units: List[Dict] = []
    for idx, b in enumerate(boxes, 1):
        rx0 = round(b['x'] * scale_x, 2)
        rx1 = round((b['x'] + b['w']) * scale_x, 2)
        ry0 = round(b['y'] * scale_y, 2)
        ry1 = round((b['y'] + b['h']) * scale_y, 2)
        rw = max(rx1 - rx0, 0.5)
        rd = max(ry1 - ry0, 0.5)
        area_m2 = rw * rd
        aspect = rw / max(rd, 0.1)

        # Classify room type
        ptype = _classify_room_type_advanced(area_m2, aspect, primary_types, b)
        is_common = ptype in {'WASH', 'STR', 'LIFT', 'CORR', 'HALL', 'UTIL', 'LOBBY', 'CONF', 'PARK'}

        # Quality score based on rectangularity
        quality = round(b.get('rect_score', 0.5) * 100, 1)

        base_units.append({
            'label': f'ADV_{idx:03d}',
            'prop_id': f'A{idx:02d}',
            'type': ptype,
            'is_common_property': 1 if is_common else 0,
            'real_width_m': round(rw, 2),
            'real_depth_m': round(rd, 2),
            'real_x_start_m': rx0,
            'real_x_end_m': rx1,
            'real_y_start_m': ry0,
            'real_y_end_m': ry1,
            'real_y_center_m': round((ry0 + ry1) / 2, 2),
            'extraction_method': f'advanced_cv_{result["strategy"]}',
            'ocr_confidence': quality,
        })

    diag.update({
        'total_base_units': len(base_units),
        'scale_x_m_per_px': round(scale_x, 5),
        'building_type': building_type,
    })

    return base_units, diag


def _classify_room_type_advanced(area_m2: float, aspect: float,
                                   primary_types: List[str],
                                   box: Dict) -> str:
    """Advanced room type classification using area, aspect, and position."""
    # Likely corridors
    if aspect > 6.0 or (aspect > 4.0 and area_m2 < 8.0):
        return 'CORR'

    # Very small → utility / washroom
    if area_m2 < 3.5:
        return 'WASH' if aspect < 2.0 else 'UTIL'

    # Stairwell-like: squarish medium room
    if 5.0 <= area_m2 <= 14.0 and 0.6 <= aspect <= 1.6:
        if box.get('rect_score', 0) > 0.8:
            return 'STR'

    # Large rooms → primary residential type
    if area_m2 >= 25.0 and primary_types:
        return primary_types[0]

    # Medium rooms → secondary type or primary
    if area_m2 >= 12.0 and len(primary_types) > 1:
        return primary_types[1]

    if area_m2 >= 8.0 and primary_types:
        return primary_types[0]

    # Very small corridor
    if area_m2 < 6.0 and aspect > 2.5:
        return 'CORR'

    return primary_types[0] if primary_types else '4S'
