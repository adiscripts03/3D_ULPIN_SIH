import os
import json
import csv
from backend.database import init_db, get_db_connection
from backend.services.cadastral_engine import extract_units_from_cad
from backend.services.rights_manager import allot_occupant_to_unit, stamp_bank_mortgage_lien

REGISTRY_FILE = "config/institutional_registry.json"
DATA_FILE_CSV = "data/room_labels_all_floors_final.csv"
OCCUPANCY_DB_FILE = "data/occupancy_db.json"

def seed_database():
    print("🚀 Initializing 3D Cadastre Database & Tables...")
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Ingest Institutional Registry
    if os.path.exists(REGISTRY_FILE):
        with open(REGISTRY_FILE, "r") as f:
            registry = json.load(f)

        for inst in registry.get("active_institutions", []):
            loc = inst.get("location", {})
            cursor.execute("""
            INSERT INTO institutions (
                institution_id, institution_name, institution_code, category,
                master_surface_ulpin, bhu_aadhaar_id, survey_number, village,
                taluka, district, state, pincode, campus_anchor_lat, campus_anchor_lon,
                total_plot_area_sqm
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(institution_id) DO UPDATE SET
                institution_name=excluded.institution_name,
                master_surface_ulpin=excluded.master_surface_ulpin,
                total_plot_area_sqm=excluded.total_plot_area_sqm
            """, (
                inst["institution_id"], inst["institution_name"], inst["institution_code"], inst["category"],
                inst["master_surface_ulpin"], inst.get("bhu_aadhaar_id"), loc.get("survey_number"),
                loc.get("village"), loc.get("taluka"), loc.get("district"), loc.get("state"),
                loc.get("pincode"), loc.get("campus_anchor_lat", 20.9495556),
                loc.get("campus_anchor_lon", 79.0294722), loc.get("total_plot_area_sqm", 404685.64)
            ))

            for b in inst.get("buildings", []):
                cursor.execute("""
                INSERT INTO buildings (
                    building_id, institution_id, building_name, category, total_floors,
                    floor_pitch_m, room_clear_height_m, slab_thickness_m, anchor_lat,
                    anchor_lon, floor_plan_source
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(building_id) DO UPDATE SET
                    building_name=excluded.building_name,
                    total_floors=excluded.total_floors,
                    anchor_lat=excluded.anchor_lat,
                    anchor_lon=excluded.anchor_lon
                """, (
                    b["building_id"], inst["institution_id"], b["building_name"], b["category"],
                    b.get("total_floors", 10), b.get("floor_pitch_m", 3.4),
                    b.get("room_clear_height_m", 2.9), b.get("slab_thickness_m", 0.5),
                    b.get("anchor_lat", 20.9495556), b.get("anchor_lon", 79.0294722),
                    b.get("floor_plan_source", "data/floor_plan.pdf")
                ))

        conn.commit()
        print("✅ Institutions & Buildings successfully registered.")

    # 2. Ingest 3D Parcels from CSV (or CAD extraction)
    if os.path.exists(DATA_FILE_CSV):
        print(f"📦 Loading 3D Volumetric Parcels from {DATA_FILE_CSV}...")
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
            ON CONFLICT(ulpin_3d) DO UPDATE SET
                carpet_area_sqm=excluded.carpet_area_sqm,
                gross_volume_cbm=excluded.gross_volume_cbm,
                undivided_share_land=excluded.undivided_share_land,
                is_common_property=excluded.is_common_property
            """, (
                ulpin, fl, r["room_id"], ptype, z0, z1, zs, w, d, x0, x1, y0, y1,
                lat, lon, carpet, volume, uds, 1 if is_common else 0
            ))

        conn.commit()
        print(f"✅ Ingested {len(rows)} 3D Volumetric Parcels for HSTL01.")

    conn.close()

    # 3. Ingest Pre-existing Occupancy & Titles
    if os.path.exists(OCCUPANCY_DB_FILE):
        print(f"👥 Seeding Occupancy & Strata Titles from {OCCUPANCY_DB_FILE}...")
        with open(OCCUPANCY_DB_FILE, "r") as f:
            occ_db = json.load(f)

        for ulpin, occupants in occ_db.items():
            for occ in occupants:
                allot_occupant_to_unit(ulpin_3d=ulpin, party_id=occ, name=f"Occupant {occ}")

    # 4. Seed Sample Bank Encumbrances (Mortgage Liens)
    print("🏦 Seeding Sample Bank Mortgage Liens (CERSAI Registry)...")
    stamp_bank_mortgage_lien(
        ulpin_3d="HSTL01-F1-X01-4S",
        mortgagee_name="State Bank of India (SBI)",
        sanction_ref="SBI-HL-2026-90412",
        loan_amount_inr=4500000.0
    )
    stamp_bank_mortgage_lien(
        ulpin_3d="HSTL01-F2-201-4S",
        mortgagee_name="HDFC Bank",
        sanction_ref="HDFC-MORT-882109",
        loan_amount_inr=5200000.0
    )

    print("🎉 3D Cadastral Database Seeding Completed Successfully!")

if __name__ == "__main__":
    seed_database()
