from fastapi import APIRouter
from backend.database import get_db_connection

router = APIRouter(prefix="/api/analytics", tags=["Cadastral Intelligence & Analytics"])

@router.get("/summary")
def get_cadastre_summary():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Total Institutions
    cursor.execute("SELECT COUNT(*) FROM institutions")
    total_institutions = cursor.fetchone()[0]

    # Total Buildings & Status breakdown
    cursor.execute("""
    SELECT COUNT(*),
           SUM(CASE WHEN data_status = 'completed' THEN 1 ELSE 0 END),
           SUM(CASE WHEN data_status != 'completed' THEN 1 ELSE 0 END)
    FROM buildings
    """)
    b_row = cursor.fetchone()
    total_buildings = b_row[0] or 0
    surveyed_buildings = b_row[1] or 0
    pending_buildings = b_row[2] or 0

    # Total Real Measured Parcels
    cursor.execute("SELECT COUNT(*), SUM(carpet_area_sqm), SUM(gross_volume_cbm) FROM parcels_3d")
    p_row = cursor.fetchone()
    total_parcels = p_row[0] or 0
    total_carpet_area = round(p_row[1] or 0.0, 2)
    total_volume = round(p_row[2] or 0.0, 2)

    # Residential vs Common
    cursor.execute("SELECT SUM(CASE WHEN is_common_property = 0 THEN 1 ELSE 0 END), SUM(CASE WHEN is_common_property = 1 THEN 1 ELSE 0 END) FROM parcels_3d")
    u_row = cursor.fetchone()
    total_residential = u_row[0] or 0
    total_common = u_row[1] or 0

    # Total Active Occupants / Titles (Simulated demonstration data)
    cursor.execute("SELECT COUNT(DISTINCT party_id), COUNT(*) FROM strata_titles WHERE status = 'ACTIVE'")
    t_row = cursor.fetchone()
    unique_occupants = t_row[0] or 0
    active_titles = t_row[1] or 0

    # Active Liens (Simulated demonstration data)
    cursor.execute("SELECT COUNT(*), SUM(loan_amount_inr) FROM encumbrances WHERE status = 'ACTIVE'")
    e_row = cursor.fetchone()
    active_liens = e_row[0] or 0
    total_encumbered_amount = round(e_row[1] or 0.0, 2)

    conn.close()

    return {
        "total_institutions_estates": total_institutions,
        "total_buildings_towers": total_buildings,
        "surveyed_buildings": surveyed_buildings,
        "pending_digitization_buildings": pending_buildings,
        "total_3d_parcels": total_parcels,
        "residential_units": total_residential,
        "common_transit_units": total_common,
        "total_carpet_area_sqm": total_carpet_area,
        "total_volume_cbm": total_volume,
        "active_occupants_registered": unique_occupants,
        "active_strata_titles": active_titles,
        "active_bank_mortgage_liens": active_liens,
        "total_encumbered_value_inr": total_encumbered_amount,
        "is_rrr_simulated_demonstration": True,
        "cadastral_standard": "ISO 19152 LADM v2 & Maharashtra Land Revenue (Survey 140/1)"
    }
