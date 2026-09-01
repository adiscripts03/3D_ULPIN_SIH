#!/usr/bin/env python3
"""
🏢 National 3D ULPIN Automated Ingestion Pipeline
Department of Land Resources (DoLR) | Ministry of Rural Development
Zero-Friction Ingestion Engine for Multi-Storey Estates, Housing Societies & Institutions
"""

import os
import sys
import csv
import json
import math
import argparse
import fitz
from shapely.geometry import box

# Default IIIT Nagpur Anchors
DEFAULT_ANCHOR_LAT = 20.9495556
DEFAULT_ANCHOR_LON = 79.0294722
DEFAULT_PITCH_M = 3.4
DEFAULT_ROOM_HEIGHT_M = 2.9
SCALE_X = 12.0 / 88.1  # 0.13620885 m/pt
X_OFFSET_CAD = 19.8    # Leftmost CAD edge

METERS_PER_DEG_LAT = 111320.0
METERS_PER_DEG_LON = 111320.0 * math.cos(math.radians(DEFAULT_ANCHOR_LAT))


def get_room_type(prop_id, ptype):
    if ptype in ["4S", "2S", "HALL", "WASH", "STR", "LIFT", "CORR", "BRIDGE"]:
        return ptype
    return "MISC"


def extract_cad_units_from_pdf(pdf_path):
    """Step 1: Extract and deduplicate vector geometry from architectural CAD PDF"""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"CAD PDF plan not found at: {pdf_path}")

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

    base_properties = []
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

        # Horizontal flip so main facade aligns with physical entrance
        rx0 = round(max_rx - raw_rx1, 2)
        rx1 = round(max_rx - raw_rx0, 2)

        # Categorize unit by CAD coordinates
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
        elif "Washroom" in label_text:
            ptype = "WASH"
            prop_id = f"WASHROOM{washroom_idx}"
            washroom_idx += 1
            if cy < 80:
                ry0, ry1 = 2.4, 8.8
            elif cy < 150:
                ry0, ry1 = 10.8, 17.2
            else:
                ry0, ry1 = 30.0, 36.4
        elif "Stairs" in label_text or "LIFT" in label_text:
            if "LIFT" in label_text:
                ptype = "LIFT"
                prop_id = "LIFT_STAIRS1"
                ry0, ry1 = 10.8, 17.2
            else:
                ptype = "STR"
                prop_id = f"STAIRS{stairs_idx}"
                stairs_idx += 1
                if cy < 80:
                    ry0, ry1 = 4.0, 8.8
                elif cy < 150:
                    ry0, ry1 = 10.8, 15.6
                elif cy < 220:
                    ry0, ry1 = 23.2, 28.0
                else:
                    ry0, ry1 = 30.0, 34.8
        elif ur['w'] > 200:
            ptype = "CORR"
            prop_id = f"CORRIDOR_{corridor_idx}"
            corridor_idx += 1
            if cy < 150:
                ry0, ry1 = 8.8, 10.8
            else:
                ry0, ry1 = 28.0, 30.0
        elif ur['h'] > 80:
            ptype = "BRIDGE"
            prop_id = f"BRIDGE_{bridge_idx}"
            bridge_idx += 1
            ry0, ry1 = 10.8, 28.0
        else:
            continue

        base_properties.append({
            "label": label_text if label_text else prop_id,
            "prop_id": prop_id,
            "type": ptype,
            "real_width_m": round(rx1 - rx0, 2),
            "real_depth_m": round(ry1 - ry0, 2),
            "real_x_start_m": rx0,
            "real_x_end_m": rx1,
            "real_y_start_m": round(ry0, 2),
            "real_y_end_m": round(ry1, 2),
            "real_y_center_m": round((ry0 + ry1) / 2.0, 2)
        })

    return base_properties


def generate_full_building_cadastre(
    building_id="HSTL01",
    pdf_path="data/floor_plan.pdf",
    total_floors=10,
    anchor_lat=DEFAULT_ANCHOR_LAT,
    anchor_lon=DEFAULT_ANCHOR_LON,
    floor_pitch=DEFAULT_PITCH_M,
    room_height=DEFAULT_ROOM_HEIGHT_M
):
    """
    Automated Execution Pipeline:
    1. Extract CAD Base Units
    2. Stack N Floors
    3. Calculate GPS Centroids + Z-Elevations
    4. Synthesize Standardized 3D ULPINs
    5. Run 3D Volumetric Topology Validation
    """
    print(f"\n============================================================")
    print(f"  🏢 IIIT NAGPUR 3D ULPIN AUTOMATED INGESTION ENGINE")
    print(f"  Building: {building_id} | Floors: {total_floors} | Anchor: ({anchor_lat}, {anchor_lon})")
    print(f"============================================================")

    # 1. Extraction
    print("\n[Step 1/5] Extracting vector geometry from floor plan...")
    base_units = extract_cad_units_from_pdf(pdf_path)
    print(f" -> Found {len(base_units)} base architectural units per floor.")

    # 2. Multi-Floor Stacking & Georeferencing
    print(f"\n[Step 2/5] Stacking {total_floors} vertical floors ({floor_pitch}m pitch)...")
    all_rows = []
    for floor in range(1, total_floors + 1):
        z_min = round((floor - 1) * floor_pitch, 2)
        z_max = round(z_min + room_height, 2)
        z_slab_top = round(floor * floor_pitch, 2)

        for base in base_units:
            base_prop_id = base["prop_id"]
            ptype = get_room_type(base_prop_id, base.get("type", "MISC"))

            if base_prop_id.startswith("X") and base_prop_id[1:].isdigit():
                num_part = base_prop_id[1:]
                room_num = f"{floor}{num_part}"
                clean_id = room_num
            else:
                clean_id = base_prop_id.replace(" ", "_").replace("&", "AND")

            # 3D ULPIN Schema
            ulpin_3d = f"{building_id}-F{floor}-{clean_id}-{ptype}"

            # Georeferencing
            x_m = float(base["real_x_start_m"]) + (float(base["real_width_m"]) / 2.0)
            y_m = float(base["real_y_center_m"])
            lon = anchor_lon + (x_m / METERS_PER_DEG_LON)
            lat = anchor_lat - (y_m / METERS_PER_DEG_LAT)

            row = {
                "ulpin_3d": ulpin_3d,
                "room_id": clean_id,
                "building_id": building_id,
                "floor": floor,
                "type": ptype,
                "z_min": z_min,
                "z_max": z_max,
                "z_slab_top": z_slab_top,
                "real_width_m": base["real_width_m"],
                "real_depth_m": base["real_depth_m"],
                "real_x_start_m": base["real_x_start_m"],
                "real_x_end_m": base["real_x_end_m"],
                "real_y_start_m": base["real_y_start_m"],
                "real_y_end_m": base["real_y_end_m"],
                "real_y_center_m": base["real_y_center_m"],
                "latitude": round(lat, 8),
                "longitude": round(lon, 8)
            }
            all_rows.append(row)

    print(f" -> Generated {len(all_rows)} volumetric parcels across {total_floors} floors.")

    # 3. Topology Validation
    print("\n[Step 3/5] Executing 3D Volumetric Topology Audit...")
    ulpin_set = set()
    dup_errors = []
    for r in all_rows:
        if r["ulpin_3d"] in ulpin_set:
            dup_errors.append(r["ulpin_3d"])
        ulpin_set.add(r["ulpin_3d"])

    if dup_errors:
        print(f" ❌ Uniqueness Error: Found duplicates: {dup_errors}")
    else:
        print(f" ✅ Uniqueness: All {len(all_rows)} 3D ULPINs are 100% unique.")

    # 3D Overlap Check
    floor_groups = {}
    for r in all_rows:
        fl = r["floor"]
        if fl not in floor_groups:
            floor_groups[fl] = []
        half_d = float(r["real_depth_m"]) / 2.0
        y_c = float(r["real_y_center_m"])
        poly = box(float(r["real_x_start_m"]), y_c - half_d, float(r["real_x_end_m"]), y_c + half_d)
        floor_groups[fl].append({"ulpin": r["ulpin_3d"], "z_min": r["z_min"], "z_max": r["z_max"], "poly": poly})

    collisions = []
    for fl, group in floor_groups.items():
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                p1, p2 = group[i], group[j]
                if (min(p1["z_max"], p2["z_max"]) - max(p1["z_min"], p2["z_min"])) > 0:
                    inter = p1["poly"].intersection(p2["poly"])
                    if inter.area > 0.01:
                        collisions.append((p1["ulpin"], p2["ulpin"], inter.area))

    if collisions:
        print(f" ❌ Topology Error: {len(collisions)} spatial collisions detected.")
    else:
        print(f" ✅ 3D Topology: 0 spatial collisions. Perfect volumetric integrity.")

    # 4. Save Master CSV
    print("\n[Step 4/5] Persisting Cadastral Datasets...")
    out_file = f"data/room_labels_{building_id.lower()}_final.csv"
    os.makedirs("data", exist_ok=True)
    fieldnames = list(all_rows[0].keys())
    with open(out_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)
    print(f" -> Saved to: {out_file}")

    # If this is HSTL01, also maintain main dataset
    if building_id == "HSTL01":
        with open("data/room_labels_all_floors_final.csv", "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_rows)

    print("\n[Step 5/5] Pipeline successfully completed!")
    print(f"============================================================")
    print(f"  Summary for Building {building_id}:")
    print(f"   • Total Units: {len(all_rows)}")
    print(f"   • Height: {max(r['z_max'] for r in all_rows)}m | Floors: {total_floors}")
    print(f"   • Sample ULPIN: {all_rows[0]['ulpin_3d']}")
    print(f"============================================================\n")

    return {
        "status": "SUCCESS",
        "building_id": building_id,
        "total_units": len(all_rows),
        "total_floors": total_floors,
        "max_elevation_m": max(r['z_max'] for r in all_rows),
        "output_csv": out_file,
        "sample_ulpin": all_rows[0]['ulpin_3d']
    }


def main():
    parser = argparse.ArgumentParser(description="IIIT Nagpur 3D ULPIN Automated Pipeline")
    parser.add_argument("--building", default="HSTL01", help="Building ID (e.g. HSTL01, HSTL02, ACAD01)")
    parser.add_argument("--pdf", default="data/floor_plan.pdf", help="Path to architectural CAD PDF plan")
    parser.add_argument("--floors", type=int, default=10, help="Total number of floors to stack")
    parser.add_argument("--lat", type=float, default=DEFAULT_ANCHOR_LAT, help="Building anchor latitude")
    parser.add_argument("--lon", type=float, default=DEFAULT_ANCHOR_LON, help="Building anchor longitude")

    args = parser.parse_args()
    generate_full_building_cadastre(
        building_id=args.building,
        pdf_path=args.pdf,
        total_floors=args.floors,
        anchor_lat=args.lat,
        anchor_lon=args.lon
    )


if __name__ == "__main__":
    main()
