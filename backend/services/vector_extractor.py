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
            if config.room_type_rules:
                # Specific rules exist for this building, so skip unmatched geometric artifacts
                continue
            # Fallback for generic vector PDFs with no predefined rules:
            if ur['w'] < 15 or ur['h'] < 15:
                continue

            lbl_clean = label_text.strip()
            lbl_upper = lbl_clean.upper()
            if any(k in lbl_upper for k in ["WASH", "TOILET", "WC", "BATH"]):
                ptype = "WASH"
                is_common = True
            elif any(k in lbl_upper for k in ["STAIR", "STR", "LIFT", "ELEVATOR"]):
                ptype = "STR"
                is_common = True
            elif any(k in lbl_upper for k in ["CORR", "PASSAGE", "HALLWAY"]):
                ptype = "CORR"
                is_common = True
            elif any(k in lbl_upper for k in ["LOBBY", "FOYER", "HALL"]):
                ptype = "LOBBY"
                is_common = True
            elif any(k in lbl_upper for k in ["OFFICE", "CABIN", "CONF"]):
                ptype = "OFFICE"
                is_common = False
            elif any(k in lbl_upper for k in ["BED", "ROOM", "4S", "2S"]):
                ptype = "ROOM"
                is_common = False
            else:
                ptype = "ROOM"
                is_common = False

            prop_id = lbl_clean if lbl_clean else f"UNIT_{len(base_properties) + 1:02d}"
            raw_y0 = (ur['y0'] - y_offset) * scale_y
            raw_y1 = (ur['y1'] - y_offset) * scale_y
            ry0 = round(raw_y0, 2)
            ry1 = round(raw_y1, 2)
        else:
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

        # Ensure prop_id is unique within base_properties
        base_pid = prop_id
        if base_pid in seen_prop_ids:
            seen_prop_ids[base_pid] += 1
            prop_id = f"{base_pid}_{seen_prop_ids[base_pid]}"
        else:
            seen_prop_ids[base_pid] = 1

        norm_x0 = min(rx0, rx1)
        norm_x1 = max(rx0, rx1)
        norm_y0 = min(ry0, ry1)
        norm_y1 = max(ry0, ry1)
        real_w = round(max(norm_x1 - norm_x0, 0.5), 2)
        real_d = round(max(norm_y1 - norm_y0, 0.5), 2)

        base_properties.append({
            "label": label_text if label_text else prop_id,
            "prop_id": prop_id,
            "type": ptype,
            "is_common_property": 1 if is_common else 0,
            "real_width_m": real_w,
            "real_depth_m": real_d,
            "real_x_start_m": norm_x0,
            "real_x_end_m": round(norm_x0 + real_w, 2),
            "real_y_start_m": norm_y0,
            "real_y_end_m": round(norm_y0 + real_d, 2),
            "real_y_center_m": round((norm_y0 + norm_y1) / 2.0, 2),
            "extraction_method": "vector_pdf",
            "ocr_confidence": 100.0
        })

    return base_properties
