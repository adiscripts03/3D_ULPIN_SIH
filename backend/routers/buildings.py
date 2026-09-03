from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import os
from backend.database import get_db_connection
from backend.models import BuildingResponse, BuildingCreate
from backend.services.cadastral_config import BuildingConfig
from backend.services.cadastral_engine import run_cadastral_pipeline

router = APIRouter(prefix="/api/buildings", tags=["Buildings & Towers"])


@router.get("", response_model=List[BuildingResponse])
def list_buildings(institution_id: Optional[str] = Query(None, description="Filter by institution")):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
    SELECT b.*,
           COUNT(DISTINCT p.ulpin_3d) as total_parcels,
           SUM(CASE WHEN p.is_common_property = 0 THEN 1 ELSE 0 END) as residential_units,
           SUM(CASE WHEN p.is_common_property = 1 THEN 1 ELSE 0 END) as common_transit_units
    FROM buildings b
    LEFT JOIN parcels_3d p ON b.building_id = p.building_id
    """
    params = []
    if institution_id:
        query += " WHERE b.institution_id = ?"
        params.append(institution_id)
    query += " GROUP BY b.building_id"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

@router.get("/{building_id}", response_model=BuildingResponse)
def get_building(building_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT b.*,
           COUNT(DISTINCT p.ulpin_3d) as total_parcels,
           SUM(CASE WHEN p.is_common_property = 0 THEN 1 ELSE 0 END) as residential_units,
           SUM(CASE WHEN p.is_common_property = 1 THEN 1 ELSE 0 END) as common_transit_units
    FROM buildings b
    LEFT JOIN parcels_3d p ON b.building_id = p.building_id
    WHERE b.building_id = ?
    GROUP BY b.building_id
    """, (building_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Building not found")
    return dict(row)

@router.post("", response_model=BuildingResponse)
def create_building(payload: BuildingCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO buildings (
            building_id, institution_id, building_name, category, total_floors,
            floor_pitch_m, room_clear_height_m, slab_thickness_m, anchor_lat,
            anchor_lon, floor_plan_source
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            payload.building_id, payload.institution_id, payload.building_name, payload.category,
            payload.total_floors, payload.floor_pitch_m, payload.room_clear_height_m,
            payload.slab_thickness_m, payload.anchor_lat, payload.anchor_lon, payload.floor_plan_source
        ))
        conn.commit()
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=400, detail=str(e))
    conn.close()
    return get_building(payload.building_id)

@router.post("/{building_id}/ingest")
def ingest_building_cad(building_id: str):
    """Triggers automated CAD vector parsing and 3D parcel extrusion into SQLite database."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM buildings WHERE building_id = ?", (building_id,))
    b = cursor.fetchone()
    conn.close()
    if not b:
        raise HTTPException(status_code=404, detail="Building not found")

    try:
        try:
            config = BuildingConfig.load_by_building_id(building_id)
        except FileNotFoundError:
            pdf_source = b["floor_plan_source"] if b["floor_plan_source"] and os.path.exists(b["floor_plan_source"]) else "data/floor_plan.pdf"
            config = BuildingConfig(
                building_id=b["building_id"],
                building_name=b["building_name"],
                category=b["category"],
                total_floors=b["total_floors"],
                floor_pitch_m=b["floor_pitch_m"],
                room_clear_height_m=b["room_clear_height_m"],
                slab_thickness_m=b["slab_thickness_m"],
                anchor_lat=b["anchor_lat"],
                anchor_lon=b["anchor_lon"],
                floor_plan_source=pdf_source
            )

        res = run_cadastral_pipeline(config, persist_db=True)
        return {
            "success": True,
            "message": f"✅ Successfully ingested {res['total_units']} 3D parcels for building {building_id}.",
            "total_parcels": res["total_units"],
            "building_id": building_id,
            "extraction_method": res["extraction_method"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

