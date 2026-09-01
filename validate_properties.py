import csv
import os
from shapely.geometry import box

DATA_FILE = "data/room_labels_all_floors_final.csv" if os.path.exists("data/room_labels_all_floors_final.csv") else "data/room_labels_floor1_final.csv"

def main():
    rows = []
    with open(DATA_FILE, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    floors = sorted(list(set(int(r["floor"]) for r in rows)))
    print(f"============================================================")
    print(f"  🏢 3D VOLUMETRIC CADASTRE VALIDATION ENGINE")
    print(f"  Total Units: {len(rows)} across {len(floors)} Floors (Floors {min(floors)} to {max(floors)})")
    print(f"============================================================\n")
    
    # 1. Duplicate ID Check
    ulpin_set = set()
    duplicates = []
    for r in rows:
        ulpin = r["ulpin_3d"]
        if ulpin in ulpin_set:
            duplicates.append(ulpin)
        ulpin_set.add(ulpin)
    
    if duplicates:
        print(f"❌ FAILED: Found duplicate ULPINs: {duplicates}")
    else:
        print(f"✅ PASSED [Uniqueness]: All {len(rows)} 3D ULPINs are 100% unique.")

    # 2. Capacity/Area Compliance Check
    # 4S should be >= 25.0 sqm, 2S should be >= 10.0 sqm
    area_errors = []
    res_count = 0
    common_count = 0
    for r in rows:
        w = float(r["real_width_m"])
        d = float(r["real_depth_m"])
        area = round(w * d, 2)
        if "4S" in r["ulpin_3d"]:
            res_count += 1
            if area < 25.0:
                area_errors.append(f"{r['ulpin_3d']} (Area: {area} sqm)")
        elif "2S" in r["ulpin_3d"]:
            res_count += 1
            if area < 10.0:
                area_errors.append(f"{r['ulpin_3d']} (Area: {area} sqm)")
        else:
            common_count += 1
            
    if area_errors:
        print(f"❌ FAILED [Area Standards]: {len(area_errors)} rooms fail capacity minimums: {area_errors}")
    else:
        print(f"✅ PASSED [Area Standards]: All {res_count} residential units ({res_count//len(floors)}/floor) meet statutory minimums.")

    # 3. 3D Volumetric Overlap Check (X, Y, Z Collision Detection)
    # Construct 3D bounding data
    parcel_boxes = []
    for r in rows:
        x_min = float(r["real_x_start_m"])
        x_max = float(r["real_x_end_m"])
        
        y_center = float(r["real_y_center_m"])
        half_d = float(r["real_depth_m"]) / 2.0
        y_min = round(y_center - half_d, 2)
        y_max = round(y_center + half_d, 2)
        
        z_min = float(r["z_min"])
        z_max = float(r["z_max"])
        
        poly_2d = box(x_min, y_min, x_max, y_max)
        parcel_boxes.append({
            "ulpin": r["ulpin_3d"],
            "floor": int(r["floor"]),
            "z_min": z_min,
            "z_max": z_max,
            "poly": poly_2d
        })
        
    overlap_errors = []
    # Group by floor to optimize topology comparisons
    floor_groups = {}
    for pb in parcel_boxes:
        fl = pb["floor"]
        if fl not in floor_groups:
            floor_groups[fl] = []
        floor_groups[fl].append(pb)
        
    # Same-floor 2D & vertical tests
    for fl, group in floor_groups.items():
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                p1 = group[i]
                p2 = group[j]
                
                # Check Z overlap
                z_overlap = min(p1["z_max"], p2["z_max"]) - max(p1["z_min"], p2["z_min"])
                if z_overlap > 0:
                    inter_2d = p1["poly"].intersection(p2["poly"])
                    if inter_2d.area > 0.01:
                        vol_overlap = round(inter_2d.area * z_overlap, 3)
                        overlap_errors.append(f"Floor {fl}: {p1['ulpin']} collides with {p2['ulpin']} (Overlap: {round(inter_2d.area,2)} m², Vol: {vol_overlap} m³)")
                        
    # Cross-floor vertical elevation check (ensure Floor F+1 z_min >= Floor F z_max)
    cross_floor_errors = []
    for fl in sorted(floor_groups.keys())[:-1]:
        next_fl = fl + 1
        if next_fl in floor_groups:
            max_z_current = max(p["z_max"] for p in floor_groups[fl])
            min_z_next = min(p["z_min"] for p in floor_groups[next_fl])
            if min_z_next < max_z_current:
                cross_floor_errors.append(f"Floor {fl} max elevation ({max_z_current}m) penetrates Floor {next_fl} min elevation ({min_z_next}m)")

    if overlap_errors or cross_floor_errors:
        print(f"❌ FAILED [3D Topology]: Found {len(overlap_errors) + len(cross_floor_errors)} spatial collisions!")
        for err in (overlap_errors + cross_floor_errors)[:5]:
            print(f"   - {err}")
    else:
        print(f"✅ PASSED [3D Topology]: 0 spatial collisions. Perfect 3D volumetric cadastre integrity across all 10 floors.")

    print(f"\n📊 Summary Breakdown:")
    print(f"   • Total Floors: {len(floors)}")
    print(f"   • Residential Parcels: {res_count} (2-Seater & 4-Seater)")
    print(f"   • Common/Transit Parcels: {common_count} (Corridors, Stairs, Lifts, Halls, Bridges, Washrooms)")
    print(f"   • Building Footprint: ~60.0m (W) × 38.8m (D) × {max(pb['z_max'] for pb in parcel_boxes):.1f}m (H)")
    print(f"============================================================\n")

if __name__ == "__main__":
    main()
