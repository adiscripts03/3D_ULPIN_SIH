import csv
import fitz

PDF_PATH = "data/floor_plan.pdf"
SCALE_X = 12.0 / 88.1  # 0.13620885 m/pt
X_OFFSET_CAD = 19.8    # Leftmost CAD edge

def extract_cad_properties():
    doc = fitz.open(PDF_PATH)
    page = doc[0]
    drawings = page.get_drawings()
    words = page.get_text("words")

    # Deduplicate vector rectangles
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

    # Total width to horizontally mirror/flip the building to match the front-facing photo
    max_rx = max((ur['x1'] - X_OFFSET_CAD) * SCALE_X for ur in unique_rects)
    max_rx = round(max_rx, 2)

    properties = []
    washroom_idx = 1
    stairs_idx = 1
    corridor_idx = 1
    bridge_idx = 1

    for ur in unique_rects:
        # Match text inside this rectangle
        contained_words = []
        for w in words:
            cx = (w[0] + w[2]) / 2
            cy = (w[1] + w[3]) / 2
            if ur['x0'] - 2 <= cx <= ur['x1'] + 2 and ur['y0'] - 2 <= cy <= ur['y1'] + 2:
                contained_words.append(w[4])
        label_text = ' '.join(contained_words).strip()
        cy = (ur['y0'] + ur['y1']) / 2

        # Raw real X in meters relative to left edge
        raw_rx0 = (ur['x0'] - X_OFFSET_CAD) * SCALE_X
        raw_rx1 = (ur['x1'] - X_OFFSET_CAD) * SCALE_X

        # HORIZONTAL FLIP (Mirror along X so X01/entrance is on the Right to match the physical photo)
        rx0 = round(max_rx - raw_rx1, 2)
        rx1 = round(max_rx - raw_rx0, 2)

        # Categorize by CAD position and physical dimensions
        # Row 1 (Outer Top - FRONT FACADE, Y = 0 to 8.8m)
        if any(f'X{i:02d}' == label_text for i in range(1, 7)):
            ry0, ry1 = 0.0, 8.8
            ptype = "4S"
            prop_id = label_text
        elif any(f'X{i:02d}' == label_text for i in range(7, 19)):
            ry0, ry1 = 4.8, 8.8
            ptype = "2S"
            prop_id = label_text
        # Row 2 (Inner Top, facing Courtyard, Y = 10.8 to 14.8/19.6m)
        elif label_text in ["X32", "X31"]:
            ry0, ry1 = 10.8, 19.6
            ptype = "4S"
            prop_id = label_text
        elif any(f'X{i:02d}' == label_text for i in range(19, 31)):
            ry0, ry1 = 10.8, 14.8
            ptype = "2S"
            prop_id = label_text
        # Row 3 (Inner Bottom, facing Courtyard, Y = 19.2/24.0 to 28.0m)
        elif any(f'X{i:02d}' == label_text for i in range(33, 37)):
            ry0, ry1 = 19.2, 28.0
            ptype = "4S"
            prop_id = label_text
        elif any(f'X{i:02d}' == label_text for i in range(37, 45)):
            ry0, ry1 = 24.0, 28.0
            ptype = "2S"
            prop_id = label_text
        # Row 4 (Outer Bottom - BACK FACADE, Y = 30.0 to 34.0/38.8m)
        elif any(f'X{i:02d}' == label_text for i in range(53, 57)):
            ry0, ry1 = 30.0, 38.8
            ptype = "4S"
            prop_id = label_text
        elif any(f'X{i:02d}' == label_text for i in range(45, 53)):
            ry0, ry1 = 30.0, 34.0
            ptype = "2S"
            prop_id = label_text
        # Common Hall (West Wing after flip, connecting Row 2 & Row 3)
        elif "Common" in label_text or "Hall" in label_text:
            ry0, ry1 = 10.8, 28.0
            ptype = "HALL"
            prop_id = "COMMON_HALL"
        # Washrooms
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
        # Vertical Transit (Stairs & Lift)
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
        # Corridors
        elif ur['w'] > 200:
            ptype = "CORR"
            prop_id = f"CORRIDOR_{corridor_idx}"
            corridor_idx += 1
            if cy < 150:
                ry0, ry1 = 8.8, 10.8
            else:
                ry0, ry1 = 28.0, 30.0
        # Connecting Bridgeways across the Central Courtyard
        elif ur['h'] > 80:
            ptype = "BRIDGE"
            prop_id = f"BRIDGE_{bridge_idx}"
            bridge_idx += 1
            ry0, ry1 = 10.8, 28.0
        else:
            continue

        properties.append({
            "label": label_text if label_text else prop_id,
            "prop_id": prop_id,
            "type": ptype,
            "floor": 1,
            "z_min": 0.0,
            "z_max": 2.9,
            "z_slab_top": 3.4,
            "real_width_m": round(rx1 - rx0, 2),
            "real_depth_m": round(ry1 - ry0, 2),
            "real_x_start_m": rx0,
            "real_x_end_m": rx1,
            "real_y_start_m": round(ry0, 2),
            "real_y_end_m": round(ry1, 2),
            "real_y_center_m": round((ry0 + ry1) / 2.0, 2)
        })

    return properties

def generate_multi_floor_properties(base_properties, total_floors=10):
    all_properties = []
    room_height = 2.9
    beam_height = 0.5
    floor_to_floor = room_height + beam_height  # 3.4m pitch

    for floor in range(1, total_floors + 1):
        z_min = round((floor - 1) * floor_to_floor, 2)
        z_max = round(z_min + room_height, 2)
        z_slab_top = round(floor * floor_to_floor, 2)

        for base in base_properties:
            prop = dict(base)
            prop["floor"] = floor
            prop["z_min"] = z_min
            prop["z_max"] = z_max
            prop["z_slab_top"] = z_slab_top

            base_label = base["label"]
            base_prop_id = base["prop_id"]

            # Map room placeholder Xnn to actual floor room number (e.g. X01 -> 101 on F1, 201 on F2, 1001 on F10)
            if base_prop_id.startswith("X") and base_prop_id[1:].isdigit():
                num_part = base_prop_id[1:]
                room_num = f"{floor}{num_part}"
                prop["label"] = room_num
                prop["prop_id"] = room_num
            else:
                prop["label"] = base_label
                prop["prop_id"] = base_prop_id

            all_properties.append(prop)

    return all_properties

def main():
    base_properties = extract_cad_properties()
    
    # Generate Floor 1
    fieldnames = list(base_properties[0].keys())
    with open("data/room_labels_floor1_real.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(base_properties)
    print(f"Extracted {len(base_properties)} base units for Floor 1 -> data/room_labels_floor1_real.csv")

    # Generate Full 10-Floor Stack
    all_floors_properties = generate_multi_floor_properties(base_properties, total_floors=10)
    with open("data/room_labels_all_floors_real.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_floors_properties)
    print(f"Generated {len(all_floors_properties)} stacked units across 10 floors -> data/room_labels_all_floors_real.csv")

if __name__ == "__main__":
    main()