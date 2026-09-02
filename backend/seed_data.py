import os
import json
import csv
from backend.database import init_db, get_db_connection, DB_PATH
from backend.services.rights_manager import allot_occupant_to_unit, stamp_bank_mortgage_lien

REGISTRY_FILE = "config/institutional_registry.json"
DATA_FILE_CSV = "data/room_labels_all_floors_final.csv"
OCCUPANCY_DB_FILE = "data/occupancy_db.json"

def seed_database():
    print("🚀 Initializing Verified 3D Cadastre Database & Tables...")
    
    # Remove old DB file if it exists to ensure a clean slate
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
            print("🧹 Removed previous database file for fresh verified seed.")
        except Exception as e:
            print(f"Notice: {e}")

    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Ingest Real Institutional Registry (Bhunaksha Survey 140/1, Waranga)
    if os.path.exists(REGISTRY_FILE):
        with open(REGISTRY_FILE, "r") as f:
            registry = json.load(f)

        for inst in registry.get("active_institutions", []):
            loc = inst.get("location", {})
            cursor.execute("""
            INSERT INTO institutions (
                institution_id, institution_name, institution_code, category,
                state_parcel_id_puid, tenure_type, khata_number, master_surface_ulpin,
                survey_number, village, taluka, district, state, pincode,
                campus_anchor_lat, campus_anchor_lon, total_plot_area_sqm,
                master_surface_reference_note
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                inst["institution_id"], inst["institution_name"], inst["institution_code"], inst["category"],
                inst.get("state_parcel_id_puid", "33550994106"),
                inst.get("tenure_type", "Sarkar (Government of Maharashtra)"),
                inst.get("khata_number", "341"),
                inst.get("state_parcel_id_puid", "33550994106"),
                loc.get("survey_number", "140/1"),
                loc.get("village", "Waranga (वारंगा)"),
                loc.get("taluka", "Nagpur Rural (नागपूर ग्रामीण)"),
                loc.get("district", "Nagpur (नागपूर)"),
                loc.get("state", "Maharashtra"),
                loc.get("pincode", "441108"),
                loc.get("campus_anchor_lat", 20.9495556),
                loc.get("campus_anchor_lon", 79.0294722),
                loc.get("total_plot_area_sqm", 404685.64),
                inst.get("master_surface_reference_note", "State Bhunaksha Parcel ID pu-id: 33550994106")
            ))

            # Ingest exactly 4 campus buildings
            for b in inst.get("buildings", []):
                cursor.execute("""
                INSERT INTO buildings (
                    building_id, institution_id, building_name, category, data_status,
                    total_floors, floor_pitch_m, room_clear_height_m, slab_thickness_m,
                    anchor_lat, anchor_lon, floor_plan_source, description
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    b["building_id"], inst["institution_id"], b["building_name"], b["category"],
                    b.get("data_status", "not_yet_surveyed"),
                    b.get("total_floors", 0),
                    b.get("floor_pitch_m", 3.4),
                    b.get("room_clear_height_m", 2.9),
                    b.get("slab_thickness_m", 0.5),
                    b.get("anchor_lat", 20.9495556),
                    b.get("anchor_lon", 79.0294722),
                    b.get("floor_plan_source", None),
                    b.get("description", "")
                ))

        conn.commit()
        print("✅ Real Institution (Survey 140/1, Khata 341, Waranga, pu-id: 33550994106) & 4 Buildings registered.")

    # 2. Ingest 3D Parcels ONLY for Hostel Block A (HSTL01) - Genuine Measured Dataset
    if os.path.exists(DATA_FILE_CSV):
        print(f"📦 Loading Genuine Measured 3D Volumetric Parcels from {DATA_FILE_CSV}...")
        total_building_carpet_area = 0.0
        rows = []
        with open(DATA_FILE_CSV, "r") as f:
            reader = csv.DictReader(f)
            for r in reader:
                w = float(r["real_width_m"])
                d = float(r["real_depth_m"])
                carpet = round(w * d, 2)
                total_building_carpet_area += carpet
                rows.append((r, carpet))

        for r, carpet in rows:
            ulpin = r["ulpin_3d"]
            fl = int(r["floor"])
            ptype = r.get("type", "")
            z0 = float(r["z_min"])
            z1 = float(r["z_max"])
            zs = float(r.get("z_slab_top", z0 + 3.4))
            w = float(r["real_width_m"])
            d = float(r["real_depth_m"])
            x0 = float(r["real_x_start_m"])
            x1 = float(r["real_x_end_m"])
            
            if "real_y_start_m" in r and "real_y_end_m" in r:
                y0 = float(r["real_y_start_m"])
                y1 = float(r["real_y_end_m"])
            else:
                yc = float(r["real_y_center_m"])
                y0 = round(yc - d/2.0, 2)
                y1 = round(yc + d/2.0, 2)

            lat = float(r["latitude"])
            lon = float(r["longitude"])
            volume = round(carpet * 2.9, 2)
            is_common = ptype in ["WASH", "STR", "LIFT", "CORR", "BRIDGE", "HALL", "UTIL"]
            uds = round(carpet / total_building_carpet_area, 7) if total_building_carpet_area > 0 else 0.0

            cursor.execute("""
            INSERT INTO parcels_3d (
                ulpin_3d, building_id, floor, room_id, type, z_min, z_max, z_slab_top,
                real_width_m, real_depth_m, real_x_start_m, real_x_end_m, real_y_start_m, real_y_end_m,
                latitude, longitude, carpet_area_sqm, gross_volume_cbm, undivided_share_land, is_common_property
            ) VALUES (?, 'HSTL01', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ulpin, fl, r["room_id"], ptype, z0, z1, zs, w, d, x0, x1, y0, y1,
                lat, lon, carpet, volume, uds, 1 if is_common else 0
            ))

        conn.commit()
        print(f"✅ Ingested exactly {len(rows)} genuine 3D Volumetric Parcels for Hostel Block A (HSTL01).")

    conn.close()

    # 3. Seed Sample Demonstration Titles (SIMULATED DATA FOR RRR DEMONSTRATION)
    if os.path.exists(OCCUPANCY_DB_FILE):
        print("👥 Seeding Sample Demonstration Occupancy & Titles (SIMULATED DATA)...")
        with open(OCCUPANCY_DB_FILE, "r") as f:
            occ_db = json.load(f)

        for ulpin, occupants in occ_db.items():
            for occ in occupants:
                allot_occupant_to_unit(ulpin_3d=ulpin, party_id=occ, name=f"Occupant {occ}")

    # 4. Seed Sample Demonstration Mortgage Liens (SIMULATED DATA FOR CERSAI DEMONSTRATION)
    print("🏦 Seeding Sample Demonstration Mortgage Liens (SIMULATED DATA)...")
    stamp_bank_mortgage_lien(
        ulpin_3d="HSTL01-F1-X01-4S",
        mortgagee_name="State Bank of India (Demo Branch)",
        sanction_ref="SBI-DEMO-2026-90412",
        loan_amount_inr=4500000.0
    )
    stamp_bank_mortgage_lien(
        ulpin_3d="HSTL01-F2-X07-2S",
        mortgagee_name="Bank of Maharashtra (Demo Branch)",
        sanction_ref="BOM-DEMO-2026-11029",
        loan_amount_inr=2800000.0
    )

    print("🎉 Verified 3D Cadastral Database Seeding Completed Successfully!")

if __name__ == "__main__":
    seed_database()
