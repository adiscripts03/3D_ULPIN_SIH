import sqlite3
from typing import Dict, Any, List, Optional
from backend.database import get_db_connection

def allot_occupant_to_unit(ulpin_3d: str, party_id: str, name: Optional[str] = None, right_type: str = "ALLOTMENT") -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Fetch parcel
    cursor.execute("SELECT * FROM parcels_3d WHERE ulpin_3d = ?", (ulpin_3d,))
    parcel = cursor.fetchone()
    if not parcel:
        conn.close()
        return {"success": False, "message": f"❌ Error: Parcel {ulpin_3d} does not exist in 3D cadastre."}

    ptype = parcel["type"]
    if parcel["is_common_property"] or ptype in ["WASH", "STR", "LIFT", "CORR", "BRIDGE", "UTIL"]:
        conn.close()
        return {"success": False, "message": f"❌ Strata Lockout: {ulpin_3d} is an inalienable Common Property / Transit Core. Registration denied."}

    # Determine capacity
    cap = 4 if "4S" in ptype or "4S" in ulpin_3d else (2 if "2S" in ptype or "2S" in ulpin_3d else 1)

    # 2. Check current active occupants
    cursor.execute("SELECT * FROM strata_titles WHERE ulpin_3d = ? AND status = 'ACTIVE'", (ulpin_3d,))
    active_titles = cursor.fetchall()

    if len(active_titles) >= cap:
        conn.close()
        return {"success": False, "message": f"❌ Overcrowding Prevented: {ulpin_3d} is at statutory maximum capacity ({cap}/{cap})."}

    # Check if party already in unit
    for t in active_titles:
        if t["party_id"] == party_id:
            conn.close()
            return {"success": False, "message": f"⚠️ Notice: Party {party_id} already holds active rights in {ulpin_3d}."}

    # 3. Ensure party exists
    cursor.execute("SELECT * FROM parties WHERE party_id = ?", (party_id,))
    if not cursor.fetchone():
        party_name = name if name else f"Occupant {party_id}"
        cursor.execute("INSERT INTO parties (party_id, name, party_type) VALUES (?, ?, 'INDIVIDUAL')", (party_id, party_name))

    # 4. Insert strata title
    cursor.execute("""
    INSERT INTO strata_titles (ulpin_3d, party_id, right_type, status, max_capacity)
    VALUES (?, ?, ?, 'ACTIVE', ?)
    """, (ulpin_3d, party_id, right_type, cap))

    # 5. Log mutation
    cursor.execute("""
    INSERT INTO mutation_audit_log (ulpin_3d, tx_type, to_party, details)
    VALUES (?, 'PRIMARY_ALLOTMENT', ?, ?)
    """, (ulpin_3d, party_id, f"Allotted with {right_type} rights. New occupancy ({len(active_titles)+1}/{cap})."))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": f"✅ Success: {party_id} registered to 3D unit {ulpin_3d}.",
        "ulpin_3d": ulpin_3d,
        "current_occupancy": len(active_titles) + 1,
        "max_capacity": cap
    }

def transfer_strata_unit(ulpin_3d: str, from_party_id: str, to_party_id: str, 
                          to_party_name: str, price_inr: float = 0.0, deed_ref: Optional[str] = None) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Verify parcel
    cursor.execute("SELECT * FROM parcels_3d WHERE ulpin_3d = ?", (ulpin_3d,))
    parcel = cursor.fetchone()
    if not parcel:
        conn.close()
        return {"success": False, "message": f"❌ Error: Parcel {ulpin_3d} not found."}

    # 2. Check if unit has active bank mortgage lien
    cursor.execute("SELECT * FROM encumbrances WHERE ulpin_3d = ? AND status = 'ACTIVE'", (ulpin_3d,))
    liens = cursor.fetchall()
    if liens:
        conn.close()
        return {
            "success": False, 
            "message": f"❌ Conveyance Blocked: 3D Unit {ulpin_3d} has an ACTIVE Bank Mortgage Lien ({liens[0]['mortgagee_name']}, Ref: {liens[0]['sanction_reference']}). Obtain NOC first."
        }

    # 3. Verify from_party holds title
    cursor.execute("SELECT * FROM strata_titles WHERE ulpin_3d = ? AND party_id = ? AND status = 'ACTIVE'", (ulpin_3d, from_party_id))
    current_title = cursor.fetchone()
    if not current_title:
        conn.close()
        return {"success": False, "message": f"❌ Error: Party {from_party_id} does not hold active title on {ulpin_3d}."}

    # 4. Ensure to_party exists
    cursor.execute("SELECT * FROM parties WHERE party_id = ?", (to_party_id,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO parties (party_id, name, party_type) VALUES (?, ?, 'INDIVIDUAL')", (to_party_id, to_party_name))

    # 5. Execute transfer mutation
    cursor.execute("UPDATE strata_titles SET status = 'TRANSFERRED' WHERE title_id = ?", (current_title["title_id"],))

    cursor.execute("""
    INSERT INTO strata_titles (ulpin_3d, party_id, right_type, status, max_capacity)
    VALUES (?, ?, 'STRATA_FREEHOLD', 'ACTIVE', ?)
    """, (ulpin_3d, to_party_id, current_title["max_capacity"]))

    # 6. Audit Log
    cursor.execute("""
    INSERT INTO mutation_audit_log (ulpin_3d, tx_type, from_party, to_party, details)
    VALUES (?, 'STRATA_CONVEYANCE_MUTATION', ?, ?, ?)
    """, (ulpin_3d, from_party_id, to_party_id, f"Consideration: INR {price_inr:,.2f} | Deed Ref: {deed_ref or 'DEED-STRATA-2026'}"))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": f"✅ Strata Title successfully transferred from {from_party_id} to {to_party_id} ({to_party_name}).",
        "ulpin_3d": ulpin_3d,
        "mutation_type": "STRATA_CONVEYANCE_MUTATION"
    }

def stamp_bank_mortgage_lien(ulpin_3d: str, mortgagee_name: str, sanction_ref: str, loan_amount_inr: float) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Verify parcel
    cursor.execute("SELECT * FROM parcels_3d WHERE ulpin_3d = ?", (ulpin_3d,))
    if not cursor.fetchone():
        conn.close()
        return {"success": False, "message": f"❌ Error: Parcel {ulpin_3d} not found."}

    # 2. Check duplicate sanction ref
    cursor.execute("SELECT * FROM encumbrances WHERE sanction_reference = ?", (sanction_ref,))
    if cursor.fetchone():
        conn.close()
        return {"success": False, "message": f"❌ Error: Mortgage Sanction Reference {sanction_ref} is already registered."}

    # 3. Insert encumbrance
    cursor.execute("""
    INSERT INTO encumbrances (ulpin_3d, encumbrance_type, mortgagee_name, sanction_reference, loan_amount_inr, status)
    VALUES (?, 'BANK_MORTGAGE_LIEN', ?, ?, ?, 'ACTIVE')
    """, (ulpin_3d, mortgagee_name, sanction_ref, loan_amount_inr))

    # 4. Audit Log
    cursor.execute("""
    INSERT INTO mutation_audit_log (ulpin_3d, tx_type, to_party, details)
    VALUES (?, 'MORTGAGE_LIEN_STAMPED', ?, ?)
    """, (ulpin_3d, mortgagee_name, f"Lien of INR {loan_amount_inr:,.2f} stamped by {mortgagee_name} (Sanction: {sanction_ref})"))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": f"✅ Mortgage lien of INR {loan_amount_inr:,.2f} registered against 3D ULPIN {ulpin_3d} by {mortgagee_name}."
    }

def release_bank_mortgage_lien(encumbrance_id: int) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM encumbrances WHERE encumbrance_id = ?", (encumbrance_id,))
    enc = cursor.fetchone()
    if not enc:
        conn.close()
        return {"success": False, "message": "❌ Error: Encumbrance record not found."}

    cursor.execute("UPDATE encumbrances SET status = 'RELEASED' WHERE encumbrance_id = ?", (encumbrance_id,))

    cursor.execute("""
    INSERT INTO mutation_audit_log (ulpin_3d, tx_type, from_party, details)
    VALUES (?, 'MORTGAGE_LIEN_RELEASED', ?, ?)
    """, (enc["ulpin_3d"], enc["mortgagee_name"], f"Lien {enc['sanction_reference']} marked RELEASED upon debt satisfaction."))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": f"✅ Mortgage Lien {enc['sanction_reference']} successfully released. 3D Unit {enc['ulpin_3d']} title is now clear."
    }
