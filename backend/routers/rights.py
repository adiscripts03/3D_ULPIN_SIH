from fastapi import APIRouter, HTTPException
from typing import List
from backend.database import get_db_connection
from backend.models import AllotmentRequest, TitleTransferRequest, MutationAuditLogResponse
from backend.services.rights_manager import allot_occupant_to_unit, transfer_strata_unit

router = APIRouter(prefix="/api/rights", tags=["Strata Rights & Dynamic Mutation"])

@router.post("/allot")
def allot_unit(payload: AllotmentRequest):
    res = allot_occupant_to_unit(
        ulpin_3d=payload.ulpin_3d,
        party_id=payload.party_id,
        name=payload.name,
        right_type=payload.right_type
    )
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["message"])
    return res

@router.post("/transfer")
def transfer_title(payload: TitleTransferRequest):
    res = transfer_strata_unit(
        ulpin_3d=payload.ulpin_3d,
        from_party_id=payload.from_party_id,
        to_party_id=payload.to_party_id,
        to_party_name=payload.to_party_name,
        price_inr=payload.conveyance_price_inr,
        deed_ref=payload.deed_registration_ref
    )
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["message"])
    return res

@router.get("/audit-log", response_model=List[MutationAuditLogResponse])
def get_mutation_log(limit: int = 100):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM mutation_audit_log ORDER BY timestamp DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]
