import sqlite3
import os
import json
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "cadastre_3d.db")

def get_db_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Institutions / Estates Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS institutions (
        institution_id TEXT PRIMARY KEY,
        institution_name TEXT NOT NULL,
        institution_code TEXT NOT NULL UNIQUE,
        category TEXT NOT NULL,
        master_surface_ulpin TEXT NOT NULL UNIQUE,
        bhu_aadhaar_id TEXT,
        survey_number TEXT,
        village TEXT,
        taluka TEXT,
        district TEXT,
        state TEXT,
        pincode TEXT,
        campus_anchor_lat REAL NOT NULL,
        campus_anchor_lon REAL NOT NULL,
        total_plot_area_sqm REAL NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Buildings Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS buildings (
        building_id TEXT PRIMARY KEY,
        institution_id TEXT NOT NULL,
        building_name TEXT NOT NULL,
        category TEXT NOT NULL,
        total_floors INTEGER NOT NULL,
        floor_pitch_m REAL NOT NULL DEFAULT 3.4,
        room_clear_height_m REAL NOT NULL DEFAULT 2.9,
        slab_thickness_m REAL NOT NULL DEFAULT 0.5,
        anchor_lat REAL NOT NULL,
        anchor_lon REAL NOT NULL,
        floor_plan_source TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (institution_id) REFERENCES institutions(institution_id) ON DELETE CASCADE
    );
    """)

    # 3. 3D Parcels Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS parcels_3d (
        ulpin_3d TEXT PRIMARY KEY,
        building_id TEXT NOT NULL,
        floor INTEGER NOT NULL,
        room_id TEXT NOT NULL,
        type TEXT NOT NULL,
        z_min REAL NOT NULL,
        z_max REAL NOT NULL,
        z_slab_top REAL NOT NULL,
        real_width_m REAL NOT NULL,
        real_depth_m REAL NOT NULL,
        real_x_start_m REAL NOT NULL,
        real_x_end_m REAL NOT NULL,
        real_y_start_m REAL NOT NULL,
        real_y_end_m REAL NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        carpet_area_sqm REAL NOT NULL,
        gross_volume_cbm REAL NOT NULL,
        undivided_share_land REAL DEFAULT 0.0,
        is_common_property BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (building_id) REFERENCES buildings(building_id) ON DELETE CASCADE
    );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_parcels_building ON parcels_3d(building_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_parcels_floor ON parcels_3d(building_id, floor);")

    # 4. Parties Table (Citizens / AOA / Banks)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS parties (
        party_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        party_type TEXT NOT NULL DEFAULT 'INDIVIDUAL',
        email TEXT,
        phone TEXT,
        aadhaar_masked TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 5. Strata Titles & RRR Table (Rights, Restrictions, Responsibilities)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS strata_titles (
        title_id INTEGER PRIMARY KEY AUTOINCREMENT,
        ulpin_3d TEXT NOT NULL,
        party_id TEXT NOT NULL,
        right_type TEXT NOT NULL DEFAULT 'ALLOTMENT',
        status TEXT NOT NULL DEFAULT 'ACTIVE',
        max_capacity INTEGER NOT NULL DEFAULT 4,
        registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (ulpin_3d) REFERENCES parcels_3d(ulpin_3d) ON DELETE CASCADE,
        FOREIGN KEY (party_id) REFERENCES parties(party_id) ON DELETE CASCADE
    );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_titles_ulpin ON strata_titles(ulpin_3d);")

    # 6. Encumbrances / Mortgage Liens Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS encumbrances (
        encumbrance_id INTEGER PRIMARY KEY AUTOINCREMENT,
        ulpin_3d TEXT NOT NULL,
        encumbrance_type TEXT NOT NULL DEFAULT 'BANK_MORTGAGE_LIEN',
        mortgagee_name TEXT NOT NULL,
        sanction_reference TEXT NOT NULL UNIQUE,
        loan_amount_inr REAL DEFAULT 0.0,
        status TEXT NOT NULL DEFAULT 'ACTIVE',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (ulpin_3d) REFERENCES parcels_3d(ulpin_3d) ON DELETE CASCADE
    );
    """)

    # 7. Mutation Audit Log
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mutation_audit_log (
        tx_id INTEGER PRIMARY KEY AUTOINCREMENT,
        ulpin_3d TEXT NOT NULL,
        tx_type TEXT NOT NULL,
        from_party TEXT,
        to_party TEXT,
        details TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print(f"✅ Cadastral SQLite Database initialized at {DB_PATH}")
