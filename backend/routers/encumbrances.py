from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from backend.database import get_db_connection
from backend.models import EncumbranceResponse, EncumbranceCreate
from backend.services.rights_manager import stamp_bank_mortgage_lien, release_bank_mortgage_lien

router = APIRouter(prefix="/api/encumbrances", tags=["Encumbrances & Mortgage Registry"])

@router.get("", response_model=List[EncumbranceResponse])
def list_encumbrances(
    ulpin_3d: Optional[str] = Query(None, description="Filter by 3D ULPIN"),
    status: Optional[str] = Query(None, description="Filter by status (ACTIVE / RELEASED)")
):
    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM encumbrances WHERE 1=1"
    params = []
    if ulpin_3d:
        query += " AND ulpin_3d = ?"
        params.append(ulpin_3d)
    if status:
        query += " AND status = ?"
        params.append(status)

    query += " ORDER BY created_at DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

@router.post("/stamp")
def stamp_lien(payload: EncumbranceCreate):
    res = stamp_bank_mortgage_lien(
        ulpin_3d=payload.ulpin_3d,
        mortgagee_name=payload.mortgagee_name,
        sanction_ref=payload.sanction_reference,
        loan_amount_inr=payload.loan_amount_inr
    )
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["message"])
    return res

@router.post("/{encumbrance_id}/release")
def release_lien(encumbrance_id: int):
    res = release_bank_mortgage_lien(encumbrance_id=encumbrance_id)
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["message"])
    return res
