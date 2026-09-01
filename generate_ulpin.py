import csv

HOSTEL_CODE = "HSTL01"

def get_room_type(prop_id, ptype):
    if ptype in ["4S", "2S", "HALL", "WASH", "STR", "LIFT", "CORR", "BRIDGE"]:
        return ptype
    return "MISC"

def main():
    rows = []
    with open("data/room_labels_floor1_geo.csv", "r") as f:
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

    with open("data/room_labels_floor1_final.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated 3D ULPINs for {len(rows)} properties.")
    print("Saved to data/room_labels_floor1_final.csv")
    print("\n--- Samples ---")
    print(f"Room X01: {rows[0]['ulpin_3d']}")
    for r in rows:
        if "COMMON" in r["ulpin_3d"] or "BRIDGE" in r["ulpin_3d"]:
            print(f"{r['room_id']}: {r['ulpin_3d']}")

if __name__ == "__main__":
    main()
