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
    
    # 1. Institutions / Estates Table (Aligned with Bhunaksha / Mahabhulekh)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS institutions (
        institution_id TEXT PRIMARY KEY,
        institution_name TEXT NOT NULL,
        institution_code TEXT NOT NULL UNIQUE,
        category TEXT NOT NULL,
        state_parcel_id_puid TEXT NOT NULL,
        tenure_type TEXT DEFAULT 'Sarkar (Government of Maharashtra)',
        khata_number TEXT DEFAULT '341',
        master_surface_ulpin TEXT,
        survey_number TEXT NOT NULL,
        village TEXT NOT NULL,
        taluka TEXT NOT NULL,
        district TEXT NOT NULL,
        state TEXT NOT NULL,
        pincode TEXT,
        campus_anchor_lat REAL NOT NULL,
        campus_anchor_lon REAL NOT NULL,
        total_plot_area_sqm REAL NOT NULL,
        master_surface_reference_note TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Buildings Table (Exactly 4 campus buildings with survey status)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS buildings (
        building_id TEXT PRIMARY KEY,
        institution_id TEXT NOT NULL,
        building_name TEXT NOT NULL,
        category TEXT NOT NULL,
        data_status TEXT NOT NULL DEFAULT 'not_yet_surveyed',
        total_floors INTEGER NOT NULL DEFAULT 0,
        floor_pitch_m REAL NOT NULL DEFAULT 3.4,
        room_clear_height_m REAL NOT NULL DEFAULT 2.9,
        slab_thickness_m REAL NOT NULL DEFAULT 0.5,
        anchor_lat REAL NOT NULL DEFAULT 20.9495556,
        anchor_lon REAL NOT NULL DEFAULT 79.0294722,
        floor_plan_source TEXT,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (institution_id) REFERENCES institutions(institution_id) ON DELETE CASCADE
    );
    """)

    # 3. 3D Parcels Table (Exclusive 3D Airspace & Common Property)
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
        undivided_share_land REAL NOT NULL DEFAULT 0.0,
        is_common_property INTEGER NOT NULL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (building_id) REFERENCES buildings(building_id) ON DELETE CASCADE
    );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_parcels_building ON parcels_3d(building_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_parcels_floor ON parcels_3d(building_id, floor);")

    # 4. Parties Table (NOTE: Seeded party records are SIMULATED DATA for demonstration)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS parties (
        party_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        party_type TEXT NOT NULL DEFAULT 'INDIVIDUAL',
        email TEXT,
        phone TEXT,
        aadhaar_masked TEXT,
        is_simulated INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 5. Strata Titles / RRR Registry (ISO 19152 LADM v2)
    # NOTE: Seeded titles are SIMULATED DATA for demonstration
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS strata_titles (
        title_id INTEGER PRIMARY KEY AUTOINCREMENT,
        ulpin_3d TEXT NOT NULL,
        party_id TEXT NOT NULL,
        right_type TEXT NOT NULL DEFAULT 'ALLOTMENT',
        status TEXT NOT NULL DEFAULT 'ACTIVE',
        max_capacity INTEGER NOT NULL DEFAULT 4,
        is_simulated INTEGER DEFAULT 1,
        registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (ulpin_3d) REFERENCES parcels_3d(ulpin_3d) ON DELETE CASCADE,
        FOREIGN KEY (party_id) REFERENCES parties(party_id) ON DELETE CASCADE
    );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_titles_ulpin ON strata_titles(ulpin_3d);")

    # 6. Encumbrances / Mortgage Liens Table (CERSAI Mock Registry)
    # NOTE: Seeded liens are SIMULATED DATA for demonstrating anti-fraud conveyance locks
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS encumbrances (
        encumbrance_id INTEGER PRIMARY KEY AUTOINCREMENT,
        ulpin_3d TEXT NOT NULL,
        encumbrance_type TEXT NOT NULL DEFAULT 'BANK_MORTGAGE_LIEN',
        mortgagee_name TEXT NOT NULL,
        sanction_reference TEXT NOT NULL UNIQUE,
        loan_amount_inr REAL DEFAULT 0.0,
        status TEXT NOT NULL DEFAULT 'ACTIVE',
        is_simulated INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (ulpin_3d) REFERENCES parcels_3d(ulpin_3d) ON DELETE CASCADE
    );
    """)

    # 7. Mutation Audit Log (Immutable Transaction Ledger)
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
