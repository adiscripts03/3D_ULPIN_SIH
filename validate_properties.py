import csv
from shapely.geometry import box

def main():
    rows = []
    with open("data/room_labels_floor1_final.csv", "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    print(f"--- Starting Validation Engine for {len(rows)} properties ---\n")
    
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
        print("✅ PASSED: All 3D ULPINs are perfectly unique.")

    # 2. Capacity/Area Check
    # 4S should be 3.35 * 8.8 = ~29.48 sqm
    # 2S should be 3.0 * 4.0 = ~12.0 sqm
    area_errors = []
    for r in rows:
        w = float(r["real_width_m"])
        d = float(r["real_depth_m"])
        area = w * d
        if "4S" in r["ulpin_3d"] and area < 25.0:
            area_errors.append(f"{r['ulpin_3d']} (Area: {area} sqm)")
        elif "2S" in r["ulpin_3d"] and area < 10.0:
            area_errors.append(f"{r['ulpin_3d']} (Area: {area} sqm)")
            
    if area_errors:
        print(f"❌ FAILED: Some rooms fail capacity minimums: {area_errors}")
    else:
        print("✅ PASSED: All rooms meet their specific capacity area requirements.")

    # 3. 3D Overlap Check (using Shapely)
    # Since they all share Floor 1, we check 2D bounding boxes (X, Y)
    # (If analyzing multiple floors, we would check Z-elevation overlap too)
    polygons = []
    for r in rows:
        x_min = float(r["real_x_start_m"])
        x_max = float(r["real_x_end_m"])
        
        # Calculate Y bounds from the mathematically aligned center and depth
        y_center = float(r["real_y_center_m"])
        half_d = float(r["real_depth_m"]) / 2.0
        y_min = y_center - half_d
        y_max = y_center + half_d
        
        poly = box(x_min, y_min, x_max, y_max)
        polygons.append((r["ulpin_3d"], poly))
        
    overlap_errors = []
    for i in range(len(polygons)):
        for j in range(i + 1, len(polygons)):
            id1, poly1 = polygons[i]
            id2, poly2 = polygons[j]
            
            # Using intersection() to calculate overlap area. 
            # A simple touching of walls (intersection area = 0) is perfectly valid!
            intersection = poly1.intersection(poly2)
            
            # 0.01 sqm tolerance handles minor floating point precision math
            if intersection.area > 0.01: 
                overlap_errors.append(f"{id1} overlaps with {id2} (Area: {round(intersection.area, 2)} sqm)")
                
    if overlap_errors:
        print(f"❌ FAILED: Found {len(overlap_errors)} overlapping property boundaries!")
        for err in overlap_errors[:5]: # Show first 5
            print(f"   - {err}")
        if len(overlap_errors) > 5:
            print("   ... and more.")
    else:
        print("✅ PASSED: Perfect topological integrity! No overlapping properties found.")

    print("\nValidation complete.")

if __name__ == "__main__":
    main()
