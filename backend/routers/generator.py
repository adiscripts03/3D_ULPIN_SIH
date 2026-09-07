import os
import shutil
import tempfile
import cv2
import numpy as np
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, FileResponse

from backend.services.cadastral_config import BuildingConfig
from backend.services.cadastral_engine import run_cadastral_pipeline
from backend.services.advanced_cv_pipeline import extract_rooms_advanced
from parse_resplan import get_plan, extract_base_units
import visualize_3d as viz

router = APIRouter(prefix="/api/generator", tags=["3D Building Generator"])

UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs("frontend", exist_ok=True)

@router.post("/build")
async def build_3d_building(
    file: Optional[UploadFile] = File(None),
    dataset_plan_index: Optional[int] = Form(None),
    building_id: Optional[str] = Form(None),
    building_name: Optional[str] = Form(None),
    floors: int = Form(4),
    floor_height_m: float = Form(3.0),
    known_scale_m_per_px: Optional[float] = Form(None),
    building_width_m: Optional[float] = Form(None),
    building_depth_m: Optional[float] = Form(None),
    total_area_sqm: Optional[float] = Form(None)
):
    """
    Bare-minimum endpoint: Upload any floor plan (PNG, JPG, PDF, PKL, JSON) 
    or pick a dataset index -> returns full 3D interactive model HTML + parcel stats.
    """
    bid = (building_id or "BLDG_" + os.urandom(3).hex().upper()).strip()
    bname = building_name or f"3D Building {bid}"
    base_units = []

    try:
        # Case 1: Picked from ResPlan dataset directly
        if dataset_plan_index is not None:
            pkl_path = "data/resplan/ResPlan.pkl"
            if not os.path.exists(pkl_path):
                raise HTTPException(status_code=400, detail="ResPlan.pkl not found at data/resplan/ResPlan.pkl")
            plan = get_plan(pkl_path, dataset_plan_index)
            base_units = extract_base_units(plan)

        # Case 2: File uploaded
        elif file and file.filename:
            ext = os.path.splitext(file.filename)[1].lower()
            fd, temp_path = tempfile.mkstemp(suffix=ext, dir=UPLOAD_DIR)
            with os.fdopen(fd, 'wb') as buffer:
                shutil.copyfileobj(file.file, buffer)

            if ext == ".pkl":
                import pickle
                with open(temp_path, "rb") as fh:
                    pkl_data = pickle.load(fh)
                plan = pkl_data[0] if isinstance(pkl_data, list) else pkl_data
                base_units = extract_base_units(plan)

            elif ext in (".json", ".geojson"):
                import json
                with open(temp_path, "r", encoding="utf-8") as fh:
                    raw_json = json.load(fh)
                plan = raw_json[0] if isinstance(raw_json, list) else raw_json
                base_units = extract_base_units(plan)

            elif ext in (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"):
                img = cv2.imread(temp_path)
                if img is None:
                    raise HTTPException(status_code=422, detail="Invalid image file.")
                extracted, _ = extract_rooms_advanced(
                    img,
                    scale_x=known_scale_m_per_px,
                    building_type="residential",
                    known_width_m=building_width_m,
                    known_depth_m=building_depth_m,
                    known_area_m2=total_area_sqm
                )
                if not extracted:
                    raise HTTPException(status_code=422, detail="No rooms detected in floor plan.")

                base_units = extracted

            elif ext == ".pdf":
                config_temp = BuildingConfig(
                    building_id=bid,
                    building_name=bname,
                    floor_plan_source=temp_path,
                    total_floors=floors,
                    floor_pitch_m=floor_height_m,
                    room_clear_height_m=round(floor_height_m - 0.4, 2)
                )
                from backend.services.vector_extractor import extract_units_from_vector_pdf
                base_units = extract_units_from_vector_pdf(config_temp)

            try:
                os.remove(temp_path)
            except Exception:
                pass

        if not base_units:
            raise HTTPException(status_code=400, detail="Please upload a floor plan or select a dataset plan index.")

        # Run 3D Cadastral Pipeline
        config = BuildingConfig(
            building_id=bid,
            building_name=bname,
            category="Residential / Multi-Storey",
            total_floors=floors,
            floor_pitch_m=floor_height_m,
            room_clear_height_m=round(floor_height_m - 0.4, 2),
            anchor_lat=20.9495556,
            anchor_lon=79.0294722,
            floor_plan_source="uploaded_file",
        )

        pipeline_result = run_cadastral_pipeline(
            config=config,
            persist_db=True,
            output_csv_dir="data",
            override_base_units=base_units,
        )

        # Generate Plotly 3D HTML Model
        html_twin_filename = f"{bid.lower()}_3d_twin.html"
        html_twin_path = os.path.join("frontend", html_twin_filename)
        viz.generate_3d_twin(
            csv_file=pipeline_result["output_csv"],
            output_html=html_twin_path,
            building_title=f"<b>3D ULPIN Digital Twin — {bname} ({bid})</b><br><sup>{pipeline_result.get('total_units', 0)} Volumetric 3D Parcels across {floors} Floors (Height: {pipeline_result.get('max_elevation_m', 0):.1f}m)</sup>"
        )

        # Update latest
        shutil.copyfile(html_twin_path, "frontend/latest_3d_twin.html")

        return {
            "status": "success",
            "building_id": bid,
            "building_name": bname,
            "total_floors": floors,
            "total_parcels": pipeline_result.get("total_units", 0),
            "carpet_area_sqm": pipeline_result.get("total_carpet_area_sqm", 0),
            "max_elevation_m": pipeline_result.get("max_elevation_m", 0),
            "sample_ulpin": pipeline_result.get("sample_ulpin", "N/A"),
            "model_url": f"/static/{html_twin_filename}",
            "csv_file": pipeline_result.get("output_csv")
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
