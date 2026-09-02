from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import os
from backend.database import get_db_connection
from backend.models import BuildingResponse, BuildingCreate
from backend.services.cadastral_engine import extract_units_from_cad

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
    if not b:
        conn.close()
        raise HTTPException(status_code=404, detail="Building not found")

    pdf_source = b["floor_plan_source"]
    if not pdf_source or not os.path.exists(pdf_source):
        # Fallback to default CAD PDF if not set
        pdf_source = "data/floor_plan.pdf"

    try:
        parcels = extract_units_from_cad(
            pdf_path=pdf_source,
            building_id=b["building_id"],
            total_floors=b["total_floors"],
            floor_pitch_m=b["floor_pitch_m"],
            clear_height_m=b["room_clear_height_m"],
            slab_thickness_m=b["slab_thickness_m"],
            anchor_lat=b["anchor_lat"],
            anchor_lon=b["anchor_lon"]
        )

        # Upsert into parcels_3d
        for p in parcels:
            cursor.execute("""
            INSERT INTO parcels_3d (
                ulpin_3d, building_id, floor, room_id, type, z_min, z_max, z_slab_top,
                real_width_m, real_depth_m, real_x_start_m, real_x_end_m, real_y_start_m, real_y_end_m,
                latitude, longitude, carpet_area_sqm, gross_volume_cbm, undivided_share_land, is_common_property
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(ulpin_3d) DO UPDATE SET
                floor=excluded.floor, room_id=excluded.room_id, type=excluded.type,
                z_min=excluded.z_min, z_max=excluded.z_max, z_slab_top=excluded.z_slab_top,
                real_width_m=excluded.real_width_m, real_depth_m=excluded.real_depth_m,
                real_x_start_m=excluded.real_x_start_m, real_x_end_m=excluded.real_x_end_m,
                real_y_start_m=excluded.real_y_start_m, real_y_end_m=excluded.real_y_end_m,
                latitude=excluded.latitude, longitude=excluded.longitude,
                carpet_area_sqm=excluded.carpet_area_sqm, gross_volume_cbm=excluded.gross_volume_cbm,
                undivided_share_land=excluded.undivided_share_land, is_common_property=excluded.is_common_property
            """, (
                p["ulpin_3d"], p["building_id"], p["floor"], p["room_id"], p["type"],
                p["z_min"], p["z_max"], p["z_slab_top"], p["real_width_m"], p["real_depth_m"],
                p["real_x_start_m"], p["real_x_end_m"], p["real_y_start_m"], p["real_y_end_m"],
                p["latitude"], p["longitude"], p["carpet_area_sqm"], p["gross_volume_cbm"],
                p["undivided_share_land"], 1 if p["is_common_property"] else 0
            ))

        conn.commit()
        conn.close()

        return {
            "success": True,
            "message": f"✅ Successfully ingested {len(parcels)} 3D parcels for building {building_id}.",
            "total_parcels": len(parcels),
            "building_id": building_id
        }
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))
