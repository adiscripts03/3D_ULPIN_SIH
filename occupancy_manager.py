import csv
import json
import os

DB_FILE = "data/occupancy_db.json"

DATA_FILE = "data/room_labels_all_floors_final.csv" if os.path.exists("data/room_labels_all_floors_final.csv") else "data/room_labels_floor1_final.csv"

def load_properties():
    properties = {}
    with open(DATA_FILE, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Enforce max capacity based on the ULPIN Type flag
            if "4S" in row["ulpin_3d"]:
                capacity = 4
            elif "2S" in row["ulpin_3d"]:
                capacity = 2
            else:
                capacity = 0 # Washrooms, Stairs, etc. cannot be occupied
            
            properties[row["ulpin_3d"]] = {
                "capacity": capacity,
                "room_id": row["room_id"],
                "floor": int(row["floor"])
            }
    return properties

def load_occupancy():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {}

def save_occupancy(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=4)

def check_in(ulpin, student_bt_id, properties, db):
    if ulpin not in properties:
        return f"❌ Error: {ulpin} is not a valid ULPIN in the registry."
    
    cap = properties[ulpin]["capacity"]
    if cap == 0:
        return f"❌ Error: {ulpin} is a non-residential zone. Check-in denied."
        
    if ulpin not in db:
        db[ulpin] = []
        
    if student_bt_id in db[ulpin]:
        return f"⚠️ Notice: {student_bt_id} is already checked in to {ulpin}."
        
    if len(db[ulpin]) >= cap:
        return f"❌ Error: Overcrowding prevented! {ulpin} is at maximum legal capacity ({cap}/{cap})."
        
    db[ulpin].append(student_bt_id)
    save_occupancy(db)
    return f"✅ Success: Checked {student_bt_id} into {ulpin}. Occupancy is now ({len(db[ulpin])}/{cap})."

def main():
    props = load_properties()
    db = load_occupancy()
    
    print(f"--- 3D ULPIN Multi-Floor Occupancy Linkage Demo ({len(props)} Units) ---\n")
    
    # Grab units across multiple floors dynamically
    f1_room_2s = next(u for u, p in props.items() if p["floor"] == 1 and "2S" in u)
    f2_room_4s = next(u for u, p in props.items() if p["floor"] == 2 and "4S" in u)
    f10_room_4s = next(u for u, p in props.items() if p["floor"] == 10 and "4S" in u)
    washroom = next(u for u in props if "WASH" in u)
    
    print("[Demo 1: Checking into a Floor 1 2-Seater Property]")
    print(check_in(f1_room_2s, "BT_ID_ALEX", props, db))
    print(check_in(f1_room_2s, "BT_ID_SARAH", props, db))
    print(check_in(f1_room_2s, "BT_ID_JOHN", props, db)) # This MUST fail due to 2S capacity!
    
    print("\n[Demo 2: Checking into a Non-Residential Zone]")
    print(check_in(washroom, "BT_ID_JOHN", props, db)) # This MUST fail!
    
    print("\n[Demo 3: Checking into Floor 2 & Floor 10 4-Seater Properties]")
    print(check_in(f2_room_4s, "BT_ID_JOHN", props, db))   # Floor 2 allocation
    print(check_in(f10_room_4s, "BT_ID_PRIYA", props, db)) # Floor 10 penthouse allocation
    
    print(f"\n--- Live Database State ({DB_FILE}) ---")
    print(json.dumps(db, indent=2))

if __name__ == "__main__":
    main()
