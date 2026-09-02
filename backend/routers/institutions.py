from fastapi import APIRouter, HTTPException
from typing import List
from backend.database import get_db_connection
from backend.models import InstitutionResponse, InstitutionCreate

router = APIRouter(prefix="/api/institutions", tags=["Institutions & Estates"])

@router.get("", response_model=List[InstitutionResponse])
def list_institutions():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT i.*, 
           COUNT(DISTINCT b.building_id) as total_buildings,
           COUNT(DISTINCT p.ulpin_3d) as total_parcels
    FROM institutions i
    LEFT JOIN buildings b ON i.institution_id = b.institution_id
    LEFT JOIN parcels_3d p ON b.building_id = p.building_id
    GROUP BY i.institution_id
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

@router.get("/{institution_id}", response_model=InstitutionResponse)
def get_institution(institution_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT i.*, 
           COUNT(DISTINCT b.building_id) as total_buildings,
           COUNT(DISTINCT p.ulpin_3d) as total_parcels
    FROM institutions i
    LEFT JOIN buildings b ON i.institution_id = b.institution_id
    LEFT JOIN parcels_3d p ON b.building_id = p.building_id
    WHERE i.institution_id = ?
    GROUP BY i.institution_id
    """, (institution_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Institution not found")
    return dict(row)

@router.post("", response_model=InstitutionResponse)
def create_institution(payload: InstitutionCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO institutions (
            institution_id, institution_name, institution_code, category,
            master_surface_ulpin, bhu_aadhaar_id, survey_number, village,
            taluka, district, state, pincode, campus_anchor_lat, campus_anchor_lon,
            total_plot_area_sqm
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            payload.institution_id, payload.institution_name, payload.institution_code, payload.category,
            payload.master_surface_ulpin, payload.bhu_aadhaar_id, payload.survey_number, payload.village,
            payload.taluka, payload.district, payload.state, payload.pincode, payload.campus_anchor_lat,
            payload.campus_anchor_lon, payload.total_plot_area_sqm
        ))
        conn.commit()
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=400, detail=str(e))
    conn.close()
    return get_institution(payload.institution_id)
