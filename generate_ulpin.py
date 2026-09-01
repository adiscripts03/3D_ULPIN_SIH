import csv

HOSTEL_CODE = "HSTL01"

def get_room_type(prop_id, ptype):
    if ptype in ["4S", "2S", "HALL", "WASH", "STR", "LIFT", "CORR", "BRIDGE"]:
        return ptype
    return "MISC"

def generate_ulpins_for_dataset(input_file, output_file):
    rows = []
    with open(input_file, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    for r in rows:
        prop_id = r["prop_id"].strip().upper()
        ptype = get_room_type(prop_id, r.get("type", "MISC"))
        
        # Clean ID for standard ULPIN format
        clean_id = prop_id.replace(" ", "_").replace("&", "AND")
        
        # Construct the final standardized 3D ULPIN
        # Schema: HOSTEL_CODE - FLOOR - PROPERTY_ID - TYPE
        ulpin = f"{HOSTEL_CODE}-F{r['floor']}-{clean_id}-{ptype}"
        
        r["ulpin_3d"] = ulpin
        r["room_id"] = clean_id

    # Reorder columns to put ULPIN right at the front
    fieldnames = list(rows[0].keys())
    if "ulpin_3d" in fieldnames:
        fieldnames.remove("ulpin_3d")
    if "room_id" in fieldnames:
        fieldnames.remove("room_id")
    fieldnames.insert(0, "ulpin_3d")
    fieldnames.insert(1, "room_id")

    with open(output_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated 3D ULPINs for {len(rows)} properties -> {output_file}")
    return rows

def main():
    # Process Floor 1
    f1_rows = generate_ulpins_for_dataset("data/room_labels_floor1_geo.csv", "data/room_labels_floor1_final.csv")
    
    # Process All 10 Floors
    all_rows = generate_ulpins_for_dataset("data/room_labels_all_floors_geo.csv", "data/room_labels_all_floors_final.csv")
    
    print("\n--- 3D ULPIN Samples Across Floors ---")
    print(f"Floor 1 Unit 101:  {all_rows[0]['ulpin_3d']}")
    sample_f2 = next(r for r in all_rows if r["floor"] == "2" or r["floor"] == 2)
    print(f"Floor 2 Unit 201:  {sample_f2['ulpin_3d']}")
    sample_f5 = next(r for r in all_rows if (r["floor"] == "5" or r["floor"] == 5) and "BRIDGE" in r["ulpin_3d"])
    print(f"Floor 5 Bridgeway: {sample_f5['ulpin_3d']}")
    sample_f10 = next(r for r in all_rows if r["floor"] == "10" or r["floor"] == 10)
    print(f"Floor 10 Unit 1001: {sample_f10['ulpin_3d']}")

if __name__ == "__main__":
    main()
