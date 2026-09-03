import os
import cv2
import numpy as np
import pytesseract
from PIL import Image
from typing import List, Dict, Any, Tuple
import fitz  # PyMuPDF for rendering raster PDFs

from backend.services.cadastral_config import BuildingConfig, RuleEngine

def load_image_from_source(source_path: str, dpi: int = 300) -> np.ndarray:
    """
    Loads an image from either a standard image file (.png, .jpg, etc.)
    or renders the first page of a raster PDF into an OpenCV BGR image.
    """
    if not os.path.exists(source_path):
        raise FileNotFoundError(f"Floor plan file not found at: {source_path}")

    ext = os.path.splitext(source_path)[1].lower()
    if ext in [".pdf"]:
        doc = fitz.open(source_path)
        if len(doc) == 0:
            raise ValueError(f"PDF {source_path} has 0 pages.")
        page = doc[0]
        # Render at specified DPI
        pix = page.get_pixmap(dpi=dpi)
        img_data = np.frombuffer(pix.samples, dtype=np.uint8)
        if pix.n == 4:
            img = img_data.reshape((pix.height, pix.width, 4))
            img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
        elif pix.n == 3:
            img = img_data.reshape((pix.height, pix.width, 3))
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        else:
            img = img_data.reshape((pix.height, pix.width, 1))
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        return img
    else:
        img = cv2.imread(source_path)
        if img is None:
            # Fallback to PIL
            pil_img = Image.open(source_path).convert("RGB")
            img = np.array(pil_img)
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        return img


def detect_room_contours(image: np.ndarray) -> List[Dict[str, Any]]:
    """
    Applies computer vision algorithms (adaptive thresholding, morphological closing,
    and contour hierarchy detection) to extract closed room boundaries.
    """
    img_h, img_w = image.shape[:2]
    total_area = img_h * img_w

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Denoising
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Adaptive thresholding to extract walls and line structures
    thresh = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV, 15, 3
    )

    # Morphological closing to bridge small gaps in architectural walls
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)

    # Find external & internal contours
    contours, hierarchy = cv2.findContours(closed, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    detected_boxes = []
    min_room_area = total_area * 0.0015  # At least 0.15% of total floor plan area
    max_room_area = total_area * 0.70    # Filter out entire building outer perimeter

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if min_room_area < area < max_room_area:
            x, y, w, h = cv2.boundingRect(cnt)
            # Filter extreme thin slivers (e.g. wall thickness artifacts)
            aspect = max(w / max(h, 1), h / max(w, 1))
            if aspect > 15:
                continue

            detected_boxes.append({
                "x": x, "y": y, "w": w, "h": h,
                "x0": x, "y0": y, "x1": x + w, "y1": y + h,
                "area": area
            })

    # Non-maximum suppression / deduplication of overlapping bounding boxes
    unique_boxes = []
    # Sort by area descending
    detected_boxes.sort(key=lambda b: b["area"], reverse=True)
    
    for b in detected_boxes:
        overlap = False
        for ub in unique_boxes:
            # Check intersection over area
            ix0 = max(b["x0"], ub["x0"])
            iy0 = max(b["y0"], ub["y0"])
            ix1 = min(b["x1"], ub["x1"])
            iy1 = min(b["y1"], ub["y1"])
            if ix1 > ix0 and iy1 > iy0:
                inter_area = (ix1 - ix0) * (iy1 - iy0)
                if inter_area > 0.65 * b["area"]:
                    overlap = True
                    break
        if not overlap:
            unique_boxes.append(b)

    return unique_boxes


def extract_ocr_text_and_confidence(roi_image: np.ndarray) -> Tuple[str, float]:
    """
    Runs PyTesseract OCR on an extracted room region of interest (ROI)
    and computes the average word confidence score.
    """
    try:
        data = pytesseract.image_to_data(roi_image, output_type=pytesseract.Output.DICT)
        words = []
        confs = []
        
        for i in range(len(data['text'])):
            txt = data['text'][i].strip()
            conf = float(data['conf'][i])
            if txt and conf > 0:
                words.append(txt)
                confs.append(conf)

        if words:
            label = ' '.join(words)
            avg_conf = round(float(np.mean(confs)), 2)
            return label, avg_conf
        return "", 0.0
    except Exception as e:
        return "", 0.0


def extract_units_from_scanned_image(config: BuildingConfig) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Full CV Pipeline for scanned/photographed floor plans:
    1. Preprocesses image
    2. Detects room boundaries via contour analysis
    3. Runs OCR on each room ROI
    4. Evaluates config rules
    5. Reports per-unit OCR confidence and flags low-confidence reads.
    """
    image = load_image_from_source(config.floor_plan_source)
    img_h, img_w = image.shape[:2]

    # Detect room boundaries
    room_boxes = detect_room_contours(image)

    # Sort boxes top-to-bottom, left-to-right for consistent labeling
    room_boxes.sort(key=lambda b: (b["y"] // 50, b["x"]))

    rule_engine = RuleEngine(config.room_type_rules)
    base_properties = []
    low_confidence_warnings = []
    confidences = []

    scale_x = config.scale_x if config.scale_x else (1.0 / 30.0) # default pixel to meter scale
    scale_y = config.scale_y if config.scale_y is not None else scale_x
    x_offset = config.x_offset_cad
    y_offset = config.y_offset_cad

    max_rx = max((b["x1"] - x_offset) * scale_x for b in room_boxes) if room_boxes else 0.0
    max_rx = round(max_rx, 2)

    for idx, b in enumerate(room_boxes, 1):
        # Crop ROI with small margin
        pad = 2
        y_min = max(0, b["y0"] - pad)
        y_max = min(img_h, b["y1"] + pad)
        x_min = max(0, b["x0"] - pad)
        x_max = min(img_w, b["x1"] + pad)
        
        roi = image[y_min:y_max, x_min:x_max]
        
        ocr_label, ocr_conf = extract_ocr_text_and_confidence(roi)
        confidences.append(ocr_conf)

        cy = (b["y0"] + b["y1"]) / 2.0

        # Transform coordinates
        raw_rx0 = (b["x0"] - x_offset) * scale_x
        raw_rx1 = (b["x1"] - x_offset) * scale_x

        if config.flip_horizontal:
            rx0 = round(max_rx - raw_rx1, 2)
            rx1 = round(max_rx - raw_rx0, 2)
        else:
            rx0 = round(raw_rx0, 2)
            rx1 = round(raw_rx1, 2)

        eval_result = rule_engine.evaluate(
            label_text=ocr_label,
            rect_w=b["w"],
            rect_h=b["h"],
            cy=cy,
            cad_y0=b["y0"],
            cad_y1=b["y1"]
        )

        if eval_result:
            prop_id = eval_result["prop_id"]
            ptype = eval_result["type"]
            is_common = eval_result["is_common"]
            if eval_result["ry0"] is not None and eval_result["ry1"] is not None:
                ry0 = eval_result["ry0"]
                ry1 = eval_result["ry1"]
            elif eval_result["depth_m"] is not None:
                raw_y0 = (b["y0"] - y_offset) * scale_y
                ry0 = round(raw_y0, 2)
                ry1 = round(ry0 + eval_result["depth_m"], 2)
            else:
                ry0 = round((b["y0"] - y_offset) * scale_y, 2)
                ry1 = round((b["y1"] - y_offset) * scale_y, 2)
        else:
            # Default room unit fallback if no specific rule matched
            prop_id = ocr_label if ocr_label else f"ROOM_{idx:02d}"
            ptype = "OFFICE" if "ADMIN" in config.building_id else "ROOM"
            is_common = False
            ry0 = round((b["y0"] - y_offset) * scale_y, 2)
            ry1 = round((b["y1"] - y_offset) * scale_y, 2)

        # Flag low-confidence OCR results
        if ocr_conf < 60.0 or not ocr_label:
            low_confidence_warnings.append({
                "unit_id": prop_id,
                "box": {"x": b["x0"], "y": b["y0"], "w": b["w"], "h": b["h"]},
                "ocr_text": ocr_label,
                "confidence_score": ocr_conf,
                "warning": "Low OCR confidence or empty label text. Please review extracted boundary."
            })

        base_properties.append({
            "label": ocr_label if ocr_label else prop_id,
            "prop_id": prop_id,
            "type": ptype,
            "is_common_property": 1 if is_common else 0,
            "real_width_m": round(max(rx1 - rx0, 0.5), 2),
            "real_depth_m": round(max(ry1 - ry0, 0.5), 2),
            "real_x_start_m": rx0,
            "real_x_end_m": rx1,
            "real_y_start_m": round(ry0, 2),
            "real_y_end_m": round(ry1, 2),
            "real_y_center_m": round((ry0 + ry1) / 2.0, 2),
            "extraction_method": "cv_ocr_scanned",
            "ocr_confidence": ocr_conf
        })

    # Compute overall OCR diagnostics report
    mean_conf = round(float(np.mean(confidences)), 2) if confidences else 0.0
    ocr_report = {
        "total_detected_units": len(base_properties),
        "mean_ocr_confidence": mean_conf,
        "high_confidence_units": len([c for c in confidences if c >= 70.0]),
        "low_confidence_units_count": len(low_confidence_warnings),
        "low_confidence_warnings": low_confidence_warnings
    }

    return base_properties, ocr_report
