from fastapi import APIRouter, HTTPException
from backend.database import get_db_connection
from backend.services.topology_validator import validate_building_topology

router = APIRouter(prefix="/api/topology", tags=["3D Topology & Spatial Validation"])

@router.get("/validate/{building_id}")
def validate_building(building_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM parcels_3d WHERE building_id = ?", (building_id,))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        raise HTTPException(status_code=404, detail=f"No 3D parcels found for building {building_id}")

    parcels = [dict(r) for r in rows]
    report = validate_building_topology(parcels)
    report["building_id"] = building_id
    return report
