import os
import math
import fitz
from typing import List, Dict, Any

SCALE_X = 12.0 / 88.1  # 0.13620885 m/pt
X_OFFSET_CAD = 19.8    # Leftmost CAD edge

METERS_PER_DEG_LAT = 111320.0

def get_room_type(prop_id: str, ptype: str) -> str:
    if ptype in ["4S", "2S", "HALL", "WASH", "STR", "LIFT", "CORR", "BRIDGE", "3BHK", "2BHK", "1BHK", "PARK", "UTIL", "STOR"]:
        return ptype
    return "MISC"

def extract_units_from_cad(pdf_path: str, building_id: str, total_floors: int, 
                           floor_pitch_m: float, clear_height_m: float, slab_thickness_m: float,
                           anchor_lat: float, anchor_lon: float, total_plot_area_sqm: float = 404685.64) -> List[Dict[str, Any]]:
    """
    Extracts 2D vector CAD rectangles, maps labels, extrudes into 3D volumetric parcels,
    calculates real-world georeferenced coordinates, carpet area, volume, and Undivided Share of Land (UDS).
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"CAD drawing not found: {pdf_path}")

    doc = fitz.open(pdf_path)
    page = doc[0]
    drawings = page.get_drawings()
    words = page.get_text("words")

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

    max_rx = max((ur['x1'] - X_OFFSET_CAD) * SCALE_X for ur in unique_rects)
    max_rx = round(max_rx, 2)

    base_floor_units = []
    washroom_idx = 1
    stairs_idx = 1
    corridor_idx = 1
    bridge_idx = 1

    for ur in unique_rects:
        contained_words = []
        for w in words:
            cx = (w[0] + w[2]) / 2
            cy = (w[1] + w[3]) / 2
            if ur['x0'] - 2 <= cx <= ur['x1'] + 2 and ur['y0'] - 2 <= cy <= ur['y1'] + 2:
                contained_words.append(w[4])
        label_text = ' '.join(contained_words).strip()
        cy = (ur['y0'] + ur['y1']) / 2

        raw_rx0 = (ur['x0'] - X_OFFSET_CAD) * SCALE_X
        raw_rx1 = (ur['x1'] - X_OFFSET_CAD) * SCALE_X

        # Horizontal alignment
        rx0 = round(max_rx - raw_rx1, 2)
        rx1 = round(max_rx - raw_rx0, 2)

        if any(f'X{i:02d}' == label_text for i in range(1, 7)):
            ry0, ry1 = 0.0, 8.8
            ptype = "4S"
            prop_id = label_text
        elif any(f'X{i:02d}' == label_text for i in range(7, 19)):
            ry0, ry1 = 4.8, 8.8
            ptype = "2S"
            prop_id = label_text
        elif label_text in ["X32", "X31"]:
            ry0, ry1 = 10.8, 19.6
            ptype = "4S"
            prop_id = label_text
        elif any(f'X{i:02d}' == label_text for i in range(19, 31)):
            ry0, ry1 = 10.8, 14.8
            ptype = "2S"
            prop_id = label_text
        elif any(f'X{i:02d}' == label_text for i in range(33, 37)):
            ry0, ry1 = 19.2, 28.0
            ptype = "4S"
            prop_id = label_text
        elif any(f'X{i:02d}' == label_text for i in range(37, 45)):
            ry0, ry1 = 24.0, 28.0
            ptype = "2S"
            prop_id = label_text
        elif any(f'X{i:02d}' == label_text for i in range(53, 57)):
            ry0, ry1 = 30.0, 38.8
            ptype = "4S"
            prop_id = label_text
        elif any(f'X{i:02d}' == label_text for i in range(45, 53)):
            ry0, ry1 = 30.0, 34.0
            ptype = "2S"
            prop_id = label_text
        elif "Common" in label_text or "Hall" in label_text:
            ry0, ry1 = 10.8, 28.0
            ptype = "HALL"
            prop_id = "COMMON_HALL"
        elif "Toilet" in label_text or "Wash" in label_text or ur['w'] < 25:
            ptype = "WASH"
            prop_id = f"WASH_{washroom_idx}"
            washroom_idx += 1
            if cy < 250: ry0, ry1 = 0.0, 4.8
            elif cy < 350: ry0, ry1 = 14.8, 19.2
            else: ry0, ry1 = 34.0, 38.8
        elif "Stair" in label_text or "Lift" in label_text or (ur['w'] > 40 and ur['h'] > 40 and not label_text):
            ptype = "STR"
            prop_id = f"STAIR_{stairs_idx}"
            stairs_idx += 1
            ry0, ry1 = 10.8, 19.2
        elif ur['w'] > 200:
            ptype = "CORR"
            prop_id = f"CORRIDOR_{corridor_idx}"
            corridor_idx += 1
            if cy < 250: ry0, ry1 = 8.8, 10.8
            elif cy < 450: ry0, ry1 = 19.2, 21.2
            else: ry0, ry1 = 28.0, 30.0
        elif ur['w'] > 80 and ur['h'] < 30:
            ptype = "BRIDGE"
            prop_id = f"BRIDGE_{bridge_idx}"
            bridge_idx += 1
            ry0, ry1 = 10.8, 19.2
        else:
            ptype = "MISC"
            prop_id = f"ZONE_{len(base_floor_units)+1}"
            ry0, ry1 = 10.8, 19.2

        rw = round(rx1 - rx0, 2)
        rd = round(ry1 - ry0, 2)
        if rw <= 0 or rd <= 0:
            continue

        base_floor_units.append({
            'prop_id': prop_id,
            'type': ptype,
            'real_x_start_m': rx0,
            'real_x_end_m': rx1,
            'real_y_start_m': ry0,
            'real_y_end_m': ry1,
            'real_width_m': rw,
            'real_depth_m': rd
        })

    # Extrude across all floors
    meters_per_deg_lon = METERS_PER_DEG_LAT * math.cos(math.radians(anchor_lat))
    all_parcels = []
    total_building_carpet_area = 0.0

    # Calculate total carpet area for UDS distribution
    for fl in range(1, total_floors + 1):
        for u in base_floor_units:
            total_building_carpet_area += (u['real_width_m'] * u['real_depth_m'])

    for fl in range(1, total_floors + 1):
        z_min = round((fl - 1) * floor_pitch_m, 2)
        z_max = round(z_min + clear_height_m, 2)
        z_slab_top = round(z_min + floor_pitch_m, 2)

        for u in base_floor_units:
            pid = u['prop_id']
            ptype = u['type']

            if pid.startswith('X'):
                room_num = int(pid[1:])
                final_room_id = f"{fl}{room_num:02d}"
            else:
                final_room_id = f"{pid}_F{fl}"

            ulpin_3d = f"{building_id}-F{fl}-{final_room_id}-{ptype}"
            carpet_area = round(u['real_width_m'] * u['real_depth_m'], 2)
            volume = round(carpet_area * clear_height_m, 2)

            center_x = (u['real_x_start_m'] + u['real_x_end_m']) / 2.0
            center_y = (u['real_y_start_m'] + u['real_y_end_m']) / 2.0

            lat = anchor_lat - (center_y / METERS_PER_DEG_LAT)
            lon = anchor_lon + (center_x / meters_per_deg_lon)

            is_common = ptype in ["WASH", "STR", "LIFT", "CORR", "BRIDGE", "HALL", "UTIL"]
            uds_fraction = round(carpet_area / total_building_carpet_area, 7) if total_building_carpet_area > 0 else 0.0

            all_parcels.append({
                'ulpin_3d': ulpin_3d,
                'building_id': building_id,
                'floor': fl,
                'room_id': final_room_id,
                'type': ptype,
                'z_min': z_min,
                'z_max': z_max,
                'z_slab_top': z_slab_top,
                'real_width_m': u['real_width_m'],
                'real_depth_m': u['real_depth_m'],
                'real_x_start_m': u['real_x_start_m'],
                'real_x_end_m': u['real_x_end_m'],
                'real_y_start_m': u['real_y_start_m'],
                'real_y_end_m': u['real_y_end_m'],
                'latitude': round(lat, 8),
                'longitude': round(lon, 8),
                'carpet_area_sqm': carpet_area,
                'gross_volume_cbm': volume,
                'undivided_share_land': uds_fraction,
                'is_common_property': is_common
            })

    return all_parcels
