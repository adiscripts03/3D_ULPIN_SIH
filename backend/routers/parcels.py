from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from backend.database import get_db_connection
from backend.models import Parcel3DResponse

router = APIRouter(prefix="/api/parcels", tags=["3D Parcels & Volumetric Cadastre"])

@router.get("", response_model=List[Parcel3DResponse])
def query_parcels(
    building_id: Optional[str] = Query(None, description="Filter by building"),
    floor: Optional[int] = Query(None, description="Filter by floor number"),
    type: Optional[str] = Query(None, description="Filter by zoning type (4S, 2S, WASH, etc.)"),
    is_common: Optional[bool] = Query(None, description="Filter by common property"),
    limit: int = Query(1000, description="Max records to return")
):
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
    SELECT p.*,
           GROUP_CONCAT(DISTINCT st.party_id) as occupants_str,
           MAX(st.max_capacity) as max_cap,
           COUNT(DISTINCT e.encumbrance_id) as active_liens_count
    FROM parcels_3d p
    LEFT JOIN strata_titles st ON p.ulpin_3d = st.ulpin_3d AND st.status = 'ACTIVE'
    LEFT JOIN encumbrances e ON p.ulpin_3d = e.ulpin_3d AND e.status = 'ACTIVE'
    WHERE 1=1
    """
    params = []
    if building_id:
        query += " AND p.building_id = ?"
        params.append(building_id)
    if floor is not None:
        query += " AND p.floor = ?"
        params.append(floor)
    if type:
        query += " AND p.type = ?"
        params.append(type)
    if is_common is not None:
        query += " AND p.is_common_property = ?"
        params.append(1 if is_common else 0)

    query += " GROUP BY p.ulpin_3d ORDER BY p.floor ASC, p.ulpin_3d ASC LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    rows = cursor.fetchall()

    results = []
    for r in rows:
        d = dict(r)
        occupants = d["occupants_str"].split(",") if d["occupants_str"] else []
        ptype = d["type"]
        cap = d["max_cap"] if d["max_cap"] else (4 if "4S" in ptype else (2 if "2S" in ptype else 0))
        
        if d["is_common_property"] or cap == 0:
            status = "Common Transit / Utility"
        elif len(occupants) == 0:
            status = "Vacant"
        elif len(occupants) < cap:
            status = "Partially Occupied"
        else:
            status = "Fully Occupied"

        d["occupants"] = occupants
        d["capacity"] = cap
        d["occupancy_status"] = status
        d["has_encumbrance"] = d["active_liens_count"] > 0
        d["active_encumbrances"] = []
        d["is_common_property"] = bool(d["is_common_property"])
        results.append(d)

    conn.close()
    return results

@router.get("/mesh-data/{building_id}")
def get_building_3d_mesh(building_id: str):
    """
    Returns pre-computed 3D bounding boxes and color states for all parcels in a building,
    ready for WebGL / Plotly / Three.js 3D rendering in the frontend.
    For non-digitized buildings, returns an honest pending status.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM buildings WHERE building_id = ?", (building_id,))
    b = cursor.fetchone()
    if not b:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Building {building_id} not found in registry.")

    if b["data_status"] != "completed":
        conn.close()
        return {
            "building_id": building_id,
            "building_name": b["building_name"],
            "data_status": b["data_status"],
            "message": "Floor plan and room data for this building has not been digitized yet - pilot volumetric data is currently only surveyed and available for Hostel Block A (HSTL01).",
            "total_units": 0,
            "floors": [],
            "parcels": []
        }

    cursor.execute("""
    SELECT p.*,
           GROUP_CONCAT(DISTINCT st.party_id) as occupants_str,
           MAX(st.max_capacity) as max_cap,
           COUNT(DISTINCT e.encumbrance_id) as active_liens_count
    FROM parcels_3d p
    LEFT JOIN strata_titles st ON p.ulpin_3d = st.ulpin_3d AND st.status = 'ACTIVE'
    LEFT JOIN encumbrances e ON p.ulpin_3d = e.ulpin_3d AND e.status = 'ACTIVE'
    WHERE p.building_id = ?
    GROUP BY p.ulpin_3d
    ORDER BY p.floor ASC
    """, (building_id,))
    rows = cursor.fetchall()
    conn.close()

    boxes = []
    floors = sorted(list(set(r["floor"] for r in rows)))

    for r in rows:
        ulpin = r["ulpin_3d"]
        ptype = r["type"]
        fl = r["floor"]
        occupants = r["occupants_str"].split(",") if r["occupants_str"] else []
        occ_count = len(occupants)
        cap = r["max_cap"] if r["max_cap"] else (4 if "4S" in ptype else (2 if "2S" in ptype else 0))
        has_lien = r["active_liens_count"] > 0

        # Assign Hex Color
        if r["is_common_property"]:
            if "WASH" in ptype: color = "#0d9488"
            elif "STR" in ptype or "LIFT" in ptype: color = "#64748b"
            elif "HALL" in ptype: color = "#b45309"
            elif "BRIDGE" in ptype: color = "#7c3aed"
            elif "CORR" in ptype: color = "#0284c7"
            else: color = "#94a3b8"
            status_label = f"Common Area ({ptype})"
        else:
            if occ_count == 0:
                color = "#16a34a"  # Green
                status_label = f"Vacant (0/{cap})"
            elif occ_count < cap:
                color = "#d97706"  # Amber
                status_label = f"Partial ({occ_count}/{cap})"
            else:
                color = "#dc2626"  # Red
                status_label = f"Full ({occ_count}/{cap})"

        boxes.append({
            "ulpin_3d": ulpin,
            "room_id": r["room_id"],
            "floor": fl,
            "type": ptype,
            "x0": r["real_x_start_m"],
            "x1": r["real_x_end_m"],
            "y0": r["real_y_start_m"],
            "y1": r["real_y_end_m"],
            "z0": r["z_min"],
            "z1": r["z_max"],
            "carpet_area": r["carpet_area_sqm"],
            "volume": r["gross_volume_cbm"],
            "uds": r["undivided_share_land"],
            "latitude": r["latitude"],
            "longitude": r["longitude"],
            "color": color,
            "status_label": status_label,
            "occupants": occupants,
            "has_lien": has_lien
        })

    return {
        "building_id": building_id,
        "building_name": b["building_name"],
        "data_status": "completed",
        "total_units": len(boxes),
        "floors": floors,
        "parcels": boxes
    }

@router.get("/{ulpin_3d}", response_model=Parcel3DResponse)
def get_parcel_detail(ulpin_3d: str):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT p.*,
           GROUP_CONCAT(DISTINCT st.party_id) as occupants_str,
           MAX(st.max_capacity) as max_cap,
           COUNT(DISTINCT e.encumbrance_id) as active_liens_count
    FROM parcels_3d p
    LEFT JOIN strata_titles st ON p.ulpin_3d = st.ulpin_3d AND st.status = 'ACTIVE'
    LEFT JOIN encumbrances e ON p.ulpin_3d = e.ulpin_3d AND e.status = 'ACTIVE'
    WHERE p.ulpin_3d = ?
    GROUP BY p.ulpin_3d
    """, (ulpin_3d,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="3D Parcel not found")

    d = dict(row)
    occupants = d["occupants_str"].split(",") if d["occupants_str"] else []
    cap = d["max_cap"] if d["max_cap"] else (4 if "4S" in d["type"] else (2 if "2S" in d["type"] else 0))

    # Fetch active encumbrances
    cursor.execute("SELECT * FROM encumbrances WHERE ulpin_3d = ?", (ulpin_3d,))
    liens = [dict(e) for e in cursor.fetchall()]

    d["occupants"] = occupants
    d["capacity"] = cap
    d["occupancy_status"] = "Vacant" if len(occupants) == 0 else ("Full" if len(occupants) >= cap else "Partial")
    d["has_encumbrance"] = len(liens) > 0
    d["active_encumbrances"] = liens
    d["is_common_property"] = bool(d["is_common_property"])

    conn.close()
    return d
