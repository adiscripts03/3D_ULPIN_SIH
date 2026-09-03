import os
import fitz
from typing import List, Dict, Any
from backend.services.cadastral_config import BuildingConfig, RuleEngine

def extract_units_from_vector_pdf(config: BuildingConfig) -> List[Dict[str, Any]]:
    """
    Extracts architectural base units from a vector CAD PDF floor plan
    using PyMuPDF (fitz) and config-driven rules.
    """
    pdf_path = config.floor_plan_source
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Vector CAD PDF plan not found at: {pdf_path}")

    doc = fitz.open(pdf_path)
    if len(doc) == 0:
        raise ValueError(f"Vector PDF file {pdf_path} contains 0 pages.")

    page = doc[0]
    drawings = page.get_drawings()
    words = page.get_text("words")

    if not drawings and not words:
        raise ValueError(f"PDF {pdf_path} contains no vector geometry or text.")

    # Deduplicate rectangular drawings
    unique_rects = []
    for d in drawings:
        r = d['rect']
        if r.width > 600 or r.height > 700:
            continue
        found = False
        for ur in unique_rects:
            if (abs(ur['x0'] - r.x0) < 0.5 and abs(ur['y0'] - r.y0) < 0.5 and 
                abs(ur['x1'] - r.x1) < 0.5 and abs(ur['y1'] - r.y1) < 0.5):
                found = True
                break
        if not found:
            unique_rects.append({'x0': r.x0, 'y0': r.y0, 'x1': r.x1, 'y1': r.y1, 'w': r.width, 'h': r.height})

    if not unique_rects:
        raise ValueError(f"No unit boundary rectangles found in vector PDF: {pdf_path}")

    scale_x = config.scale_x
    scale_y = config.scale_y if config.scale_y is not None else scale_x
    x_offset = config.x_offset_cad
    y_offset = config.y_offset_cad

    max_rx = max((ur['x1'] - x_offset) * scale_x for ur in unique_rects)
    max_rx = round(max_rx, 2)

    rule_engine = RuleEngine(config.room_type_rules)
    base_properties = []

    for ur in unique_rects:
        contained_words = []
        for w in words:
            cx_word = (w[0] + w[2]) / 2
            cy_word = (w[1] + w[3]) / 2
            if ur['x0'] - 2 <= cx_word <= ur['x1'] + 2 and ur['y0'] - 2 <= cy_word <= ur['y1'] + 2:
                contained_words.append(w[4])
        
        label_text = ' '.join(contained_words).strip()
        cy = (ur['y0'] + ur['y1']) / 2

        # Horizontal alignment & coordinate transform
        raw_rx0 = (ur['x0'] - x_offset) * scale_x
        raw_rx1 = (ur['x1'] - x_offset) * scale_x

        if config.flip_horizontal:
            rx0 = round(max_rx - raw_rx1, 2)
            rx1 = round(max_rx - raw_rx0, 2)
        else:
            rx0 = round(raw_rx0, 2)
            rx1 = round(raw_rx1, 2)

        eval_result = rule_engine.evaluate(
            label_text=label_text,
            rect_w=ur['w'],
            rect_h=ur['h'],
            cy=cy,
            cad_y0=ur['y0'],
            cad_y1=ur['y1']
        )

        if not eval_result:
            # Skip unmatched geometric artifacts (e.g. tiny line markers)
            continue

        prop_id = eval_result["prop_id"]
        ptype = eval_result["type"]
        is_common = eval_result["is_common"]

        if eval_result["ry0"] is not None and eval_result["ry1"] is not None:
            ry0 = eval_result["ry0"]
            ry1 = eval_result["ry1"]
        elif eval_result["depth_m"] is not None:
            raw_y0 = (ur['y0'] - y_offset) * scale_y
            ry0 = round(raw_y0, 2)
            ry1 = round(ry0 + eval_result["depth_m"], 2)
        else:
            raw_y0 = (ur['y0'] - y_offset) * scale_y
            raw_y1 = (ur['y1'] - y_offset) * scale_y
            ry0 = round(raw_y0, 2)
            ry1 = round(raw_y1, 2)

        base_properties.append({
            "label": label_text if label_text else prop_id,
            "prop_id": prop_id,
            "type": ptype,
            "is_common_property": 1 if is_common else 0,
            "real_width_m": round(rx1 - rx0, 2),
            "real_depth_m": round(ry1 - ry0, 2),
            "real_x_start_m": rx0,
            "real_x_end_m": rx1,
            "real_y_start_m": round(ry0, 2),
            "real_y_end_m": round(ry1, 2),
            "real_y_center_m": round((ry0 + ry1) / 2.0, 2),
            "extraction_method": "vector_pdf",
            "ocr_confidence": 100.0
        })

    return base_properties
