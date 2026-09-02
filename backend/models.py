from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

# --- Institution / Estate Models ---
class InstitutionBase(BaseModel):
    institution_id: str
    institution_name: str
    institution_code: str
    category: str
    master_surface_ulpin: str
    bhu_aadhaar_id: Optional[str] = None
    survey_number: Optional[str] = None
    village: Optional[str] = None
    taluka: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    campus_anchor_lat: float
    campus_anchor_lon: float
    total_plot_area_sqm: float

class InstitutionCreate(InstitutionBase):
    pass

class InstitutionResponse(InstitutionBase):
    total_buildings: int = 0
    total_parcels: int = 0
    created_at: Optional[str] = None


# --- Building Models ---
class BuildingBase(BaseModel):
    building_id: str
    institution_id: str
    building_name: str
    category: str
    total_floors: int
    floor_pitch_m: float = 3.4
    room_clear_height_m: float = 2.9
    slab_thickness_m: float = 0.5
    anchor_lat: float
    anchor_lon: float
    floor_plan_source: Optional[str] = None

class BuildingCreate(BuildingBase):
    pass

class BuildingResponse(BuildingBase):
    total_parcels: int = 0
    residential_units: int = 0
    common_transit_units: int = 0
    created_at: Optional[str] = None


# --- 3D Parcel Models ---
class Parcel3DBase(BaseModel):
    ulpin_3d: str
    building_id: str
    floor: int
    room_id: str
    type: str
    z_min: float
    z_max: float
    z_slab_top: float
    real_width_m: float
    real_depth_m: float
    real_x_start_m: float
    real_x_end_m: float
    real_y_start_m: float
    real_y_end_m: float
    latitude: float
    longitude: float
    carpet_area_sqm: float
    gross_volume_cbm: float
    undivided_share_land: float = 0.0
    is_common_property: bool = False

class Parcel3DCreate(Parcel3DBase):
    pass

class Parcel3DResponse(Parcel3DBase):
    occupants: List[str] = []
    capacity: int = 0
    occupancy_status: str = "Vacant"
    has_encumbrance: bool = False
    active_encumbrances: List[Dict[str, Any]] = []


# --- Party Models ---
class PartyBase(BaseModel):
    party_id: str
    name: str
    party_type: str = "INDIVIDUAL"  # INDIVIDUAL, HOA, BANK, INSTITUTION
    email: Optional[str] = None
    phone: Optional[str] = None
    aadhaar_masked: Optional[str] = None

class PartyCreate(PartyBase):
    pass


# --- Strata Title / RRR Models ---
class StrataTitleBase(BaseModel):
    ulpin_3d: str
    party_id: str
    party_name: Optional[str] = None
    right_type: str = "ALLOTMENT"  # STRATA_FREEHOLD, LEASEHOLD, ALLOTMENT
    status: str = "ACTIVE"
    max_capacity: int = 4

class AllotmentRequest(BaseModel):
    ulpin_3d: str
    party_id: str
    name: Optional[str] = None
    right_type: str = "ALLOTMENT"

class TitleTransferRequest(BaseModel):
    ulpin_3d: str
    from_party_id: str
    to_party_id: str
    to_party_name: str
    conveyance_price_inr: Optional[float] = 0.0
    deed_registration_ref: Optional[str] = None


# --- Encumbrance / Mortgage Models ---
class EncumbranceCreate(BaseModel):
    ulpin_3d: str
    encumbrance_type: str = "BANK_MORTGAGE_LIEN"
    mortgagee_name: str
    sanction_reference: str
    loan_amount_inr: float = 0.0

class EncumbranceResponse(BaseModel):
    encumbrance_id: int
    ulpin_3d: str
    encumbrance_type: str
    mortgagee_name: str
    sanction_reference: str
    loan_amount_inr: float
    status: str
    created_at: str


# --- Mutation Audit Log ---
class MutationAuditLogResponse(BaseModel):
    tx_id: int
    ulpin_3d: str
    tx_type: str
    from_party: Optional[str] = None
    to_party: Optional[str] = None
    details: Optional[str] = None
    timestamp: str
