from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

# --- Institution / Estate Models (Aligned with Bhunaksha / Mahabhulekh) ---
class InstitutionBase(BaseModel):
    institution_id: str
    institution_name: str
    institution_code: str
    category: str
    state_parcel_id_puid: str = "33550994106"
    tenure_type: str = "Sarkar (Government of Maharashtra)"
    khata_number: str = "341"
    master_surface_ulpin: Optional[str] = "33550994106"
    survey_number: str = "140/1"
    village: str = "Waranga (वारंगा)"
    taluka: str = "Nagpur Rural (नागपूर ग्रामीण)"
    district: str = "Nagpur (नागपूर)"
    state: str = "Maharashtra"
    pincode: Optional[str] = "441108"
    campus_anchor_lat: float = 20.9495556
    campus_anchor_lon: float = 79.0294722
    total_plot_area_sqm: float = 404685.64
    master_surface_reference_note: Optional[str] = None

class InstitutionCreate(InstitutionBase):
    pass

class InstitutionResponse(InstitutionBase):
    total_buildings: int = 0
    total_parcels: int = 0
    surveyed_buildings: int = 0
    pending_buildings: int = 0
    created_at: Optional[str] = None


# --- Building Models (4 Genuine Campus Buildings) ---
class BuildingBase(BaseModel):
    building_id: str
    institution_id: str
    building_name: str
    category: str
    data_status: str = "not_yet_surveyed"  # "completed" or "not_yet_surveyed"
    total_floors: int = 0
    floor_pitch_m: float = 3.4
    room_clear_height_m: float = 2.9
    slab_thickness_m: float = 0.5
    anchor_lat: float = 20.9495556
    anchor_lon: float = 79.0294722
    floor_plan_source: Optional[str] = None
    description: Optional[str] = None

class BuildingCreate(BuildingBase):
    pass

class BuildingResponse(BuildingBase):
    total_parcels: int = 0
    residential_units: int = 0
    common_transit_units: int = 0
    created_at: Optional[str] = None


# --- 3D Parcel Models (Hostel Block A 700 Genuine Units) ---
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


# --- Party Models (Simulated Demonstration Data) ---
class PartyBase(BaseModel):
    party_id: str
    name: str
    party_type: str = "INDIVIDUAL"  # INDIVIDUAL, HOA, BANK, INSTITUTION
    email: Optional[str] = None
    phone: Optional[str] = None
    aadhaar_masked: Optional[str] = None
    is_simulated: bool = True

class PartyCreate(PartyBase):
    pass


# --- Strata Title / RRR Models (Simulated Demonstration Data) ---
class StrataTitleBase(BaseModel):
    ulpin_3d: str
    party_id: str
    party_name: Optional[str] = None
    right_type: str = "ALLOTMENT"  # STRATA_FREEHOLD, LEASEHOLD, ALLOTMENT
    status: str = "ACTIVE"
    max_capacity: int = 4
    is_simulated: bool = True

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


# --- Encumbrance / Mortgage Models (Simulated Demonstration Data) ---
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
    is_simulated: bool = True
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
