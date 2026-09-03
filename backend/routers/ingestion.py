import os
import json
import shutil
from typing import Optional, List
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from backend.services.cadastral_config import BuildingConfig, RoomTypeRule
from backend.services.cadastral_engine import run_cadastral_pipeline

router = APIRouter(prefix="/api/ingestion", tags=["Surveyor Data Ingestion"])

UPLOAD_DIR = "data/uploads"
BUILDINGS_CONFIG_DIR = "config/buildings"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(BUILDINGS_CONFIG_DIR, exist_ok=True)


@router.get("/configs")
def list_building_configs():
    """Lists all registered building configuration files."""
    configs = []
    if os.path.exists(BUILDINGS_CONFIG_DIR):
        for fname in os.listdir(BUILDINGS_CONFIG_DIR):
            if fname.endswith(".json") and not fname.startswith("template"):
                fpath = os.path.join(BUILDINGS_CONFIG_DIR, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        configs.append({
                            "building_id": data.get("building_id"),
                            "building_name": data.get("building_name"),
                            "total_floors": data.get("total_floors"),
                            "rules_count": len(data.get("room_type_rules", [])),
                            "filename": fname
                        })
                except Exception:
                    continue
    return configs


@router.get("/configs/{building_id}")
def get_building_config(building_id: str):
    """Retrieves full JSON configuration for a specific building."""
    try:
        config = BuildingConfig.load_by_building_id(building_id, BUILDINGS_CONFIG_DIR)
        return config.dict()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Configuration for building '{building_id}' not found.")


@router.post("/run")
async def run_ingestion_job(
    file: UploadFile = File(..., description="Architectural CAD floor plan (PDF or scanned image)"),
    point_cloud: Optional[UploadFile] = File(None, description="Optional drone photogrammetry point cloud (.ply, .xyz, .las)"),
    building_id: str = Form(..., description="Unique Building ID (e.g. ADMIN01, ACAD01)"),
    building_name: str = Form(..., description="Human-readable building name"),
    category: Optional[str] = Form("Institutional Complex"),
    total_floors: int = Form(..., ge=1, le=100),
    floor_pitch_m: float = Form(3.4, ge=2.0, le=10.0),
    room_clear_height_m: float = Form(2.9, ge=1.8, le=9.0),
    slab_thickness_m: float = Form(0.5, ge=0.1, le=3.0),
    anchor_lat: float = Form(20.9495556),
    anchor_lon: float = Form(79.0294722),
    scale_x: Optional[float] = Form(None),
    flip_horizontal: bool = Form(False),
    rules_json: Optional[str] = Form(None, description="JSON array of room_type_rules")
):
    """
    Field Surveyor Ingestion Endpoint:
    Receives uploaded floor plans, parses room classification rules, executes CV/OCR
    and vector extraction, performs ML point cloud floor validation, and registers 3D parcels.
    """
    clean_bldg_id = building_id.strip().upper()

    # 1. Save uploaded floor plan
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_ext = os.path.splitext(file.filename)[1].lower() if file.filename else ".pdf"
    target_plan_path = os.path.join(UPLOAD_DIR, f"{clean_bldg_id}_floor_plan{file_ext}")
    
    with open(target_plan_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 2. Save optional point cloud
    target_point_cloud_path = None
    if point_cloud and point_cloud.filename:
        pc_ext = os.path.splitext(point_cloud.filename)[1].lower()
        target_point_cloud_path = os.path.join(UPLOAD_DIR, f"{clean_bldg_id}_point_cloud{pc_ext}")
        with open(target_point_cloud_path, "wb") as buffer:
            shutil.copyfileobj(point_cloud.file, buffer)

    # 3. Parse room type rules
    parsed_rules = []
    if rules_json:
        try:
            raw_rules = json.loads(rules_json)
            if isinstance(raw_rules, list):
                for r in raw_rules:
                    parsed_rules.append(RoomTypeRule(**r))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid room_type_rules JSON: {str(e)}")

    # 4. Construct BuildingConfig
    config = BuildingConfig(
        building_id=clean_bldg_id,
        building_name=building_name,
        category=category,
        floor_plan_source=target_plan_path,
        floor_plan_type="auto",
        anchor_lat=anchor_lat,
        anchor_lon=anchor_lon,
        total_floors=total_floors,
        floor_pitch_m=floor_pitch_m,
        room_clear_height_m=room_clear_height_m,
        slab_thickness_m=slab_thickness_m,
        scale_x=scale_x if scale_x else 0.1362088535754824,
        flip_horizontal=flip_horizontal,
        point_cloud_source=target_point_cloud_path,
        room_type_rules=parsed_rules
    )

    # 5. Persist Building JSON configuration
    config_file_path = os.path.join(BUILDINGS_CONFIG_DIR, f"{clean_bldg_id}.json")
    with open(config_file_path, "w", encoding="utf-8") as f:
        json.dump(config.dict(), f, indent=2)

    # 6. Execute Generalized Pipeline
    try:
        result = run_cadastral_pipeline(config, persist_db=True, output_csv_dir="data")
        result["config_file"] = config_file_path
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cadastral pipeline execution failed: {str(e)}")
