"""
AI Pipeline Router — 3D ULPIN
Accepts multi-image uploads: floor plan + exterior photo + room photos
"""

from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from typing import Optional, List
import os
import shutil
import tempfile
from fastapi.responses import JSONResponse

from backend.services.building_predictor import predict_building
from backend.services.yolo_detector import _YOLO_AVAILABLE

router = APIRouter()

UPLOAD_DIR = "data/ai_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.get("/status")
def ai_pipeline_status():
    return {
        "status": "online",
        "yolo_available": _YOLO_AVAILABLE,
        "capabilities": [
            "text_nlp_extraction",
            "floor_plan_image_cv_extraction",
            "floor_plan_image_yolo_extraction" if _YOLO_AVAILABLE else "floor_plan_opencv_advanced",
            "exterior_photo_floor_count_detection",
            "room_photo_type_classification",
            "video_frame_extraction",
            "multi_image_fusion",
            "synthetic_floor_plan_generation",
            "3d_ulpin_prediction",
            "webgl_3d_mesh_data",
        ],
        "pipeline_version": "2.0.0",
        "deeplearning_model": "YOLOv8n-seg + YOLOv8n" if _YOLO_AVAILABLE else "Advanced OpenCV (YOLO not installed)",
    }


@router.post("/predict")
async def predict_3d_building(
    text_prompt: Optional[str] = Form(None),
    building_id: Optional[str] = Form(None),
    persist_db: bool = Form(True),
    use_yolo: bool = Form(True),
    # Multi-image support
    floor_plan_image: Optional[UploadFile] = File(None),
    exterior_image: Optional[UploadFile] = File(None),
    room_image_1: Optional[UploadFile] = File(None),
    room_image_2: Optional[UploadFile] = File(None),
    room_image_3: Optional[UploadFile] = File(None),
    video_file: Optional[UploadFile] = File(None),
):
    """
    Master AI endpoint. Accepts:
      - text_prompt: Natural language description of the building
      - floor_plan_image: Floor plan (PDF, PNG, JPG) — primary extraction source
      - exterior_image: Building outside photo → floor count detection
      - room_image_1/2/3: Interior room photos → room type inference
      - video_file: Building walkthrough video → best frame extraction

    All inputs are optional but at least one must be provided.
    Returns: full 3D ULPIN prediction + Plotly mesh data + topology validation.
    """
    if not any([text_prompt, floor_plan_image, exterior_image,
                room_image_1, video_file]):
        raise HTTPException(
            status_code=400,
            detail="Provide at least one: text_prompt, floor_plan_image, exterior_image, or video_file.",
        )

    saved_paths: List[str] = []

    def _save(upload: Optional[UploadFile]) -> Optional[str]:
        if not upload:
            return None
        ext = os.path.splitext(upload.filename or ".tmp")[1] or ".tmp"
        fd, path = tempfile.mkstemp(suffix=ext, dir=UPLOAD_DIR)
        with os.fdopen(fd, 'wb') as f:
            shutil.copyfileobj(upload.file, f)
        saved_paths.append(path)
        return path

    try:
        fp_path = _save(floor_plan_image)
        ext_path = _save(exterior_image)
        r1_path = _save(room_image_1)
        r2_path = _save(room_image_2)
        r3_path = _save(room_image_3)
        vid_path = _save(video_file)

        room_paths = [p for p in [r1_path, r2_path, r3_path] if p]

        result = predict_building(
            text=text_prompt,
            image_path=fp_path,
            video_path=vid_path,
            exterior_image_path=ext_path,
            room_image_paths=room_paths if room_paths else None,
            building_id=building_id,
            persist_db=persist_db,
            use_yolo=use_yolo,
        )

        status_code = 200 if result.get('status') == 'success' else 207
        return JSONResponse(status_code=status_code, content=result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        for p in saved_paths:
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass


@router.post("/analyze/text")
async def analyze_text_only(prompt: str = Form(...)):
    """NLP text analysis only — no image, no DB persist."""
    from backend.services.text_analyzer import analyze_text
    result = analyze_text(prompt)
    return result


@router.post("/analyze/floor-plan")
async def analyze_floor_plan(
    image_file: UploadFile = File(...),
    building_type: str = Form("hostel"),
    use_yolo: bool = Form(True),
):
    """
    Analyze a floor plan image only.
    Returns: detected rooms list + diagnostics (no DB persist).
    """
    ext = os.path.splitext(image_file.filename or ".tmp")[1]
    fd, path = tempfile.mkstemp(suffix=ext, dir=UPLOAD_DIR)
    try:
        with os.fdopen(fd, 'wb') as f:
            shutil.copyfileobj(image_file.file, f)

        import cv2 as _cv2
        img = _cv2.imread(path)
        if img is None:
            raise HTTPException(status_code=422, detail="Could not read image file.")

        from backend.services.yolo_detector import detect_rooms_yolo
        from backend.services.advanced_cv_pipeline import extract_rooms_advanced

        if _YOLO_AVAILABLE and use_yolo:
            units, diag = detect_rooms_yolo(img)
        else:
            units, diag = extract_rooms_advanced(img, building_type=building_type)

        return {
            "rooms_detected": len(units),
            "extraction_method": diag.get('method', diag.get('strategy_used', 'unknown')),
            "yolo_used": _YOLO_AVAILABLE and use_yolo,
            "rooms": units[:50],  # Return first 50 for preview
            "diagnostics": diag,
        }
    finally:
        if os.path.exists(path):
            os.remove(path)


@router.post("/analyze/exterior")
async def analyze_exterior(
    image_file: UploadFile = File(...),
    use_yolo: bool = Form(True),
):
    """
    Analyze a building exterior photo.
    Returns: estimated floor count + units per floor.
    """
    ext = os.path.splitext(image_file.filename or ".tmp")[1]
    fd, path = tempfile.mkstemp(suffix=ext, dir=UPLOAD_DIR)
    try:
        with os.fdopen(fd, 'wb') as f:
            shutil.copyfileobj(image_file.file, f)

        import cv2 as _cv2
        img = _cv2.imread(path)
        if img is None:
            raise HTTPException(status_code=422, detail="Could not read image file.")

        from backend.services.yolo_detector import analyze_exterior_yolo
        result = analyze_exterior_yolo(img)
        return result
    finally:
        if os.path.exists(path):
            os.remove(path)


@router.post("/analyze/room-photo")
async def analyze_room_photo(
    image_file: UploadFile = File(...),
):
    """
    Classify a room interior photo → infer ULPIN room type.
    """
    ext = os.path.splitext(image_file.filename or ".tmp")[1]
    fd, path = tempfile.mkstemp(suffix=ext, dir=UPLOAD_DIR)
    try:
        with os.fdopen(fd, 'wb') as f:
            shutil.copyfileobj(image_file.file, f)

        import cv2 as _cv2
        img = _cv2.imread(path)
        if img is None:
            raise HTTPException(status_code=422, detail="Could not read image file.")

        from backend.services.yolo_detector import classify_room_photo
        return classify_room_photo(img)
    finally:
        if os.path.exists(path):
            os.remove(path)


@router.get("/mesh/{building_id}")
async def get_building_mesh(building_id: str):
    """Retrieve 3D mesh data for a predicted building (for WebGL rendering)."""
    try:
        from backend.database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ulpin_3d, floor, type, z_min, z_max,
                   real_x_start_m, real_x_end_m, real_y_start_m, real_y_end_m,
                   carpet_area_sqm, is_common_property, latitude, longitude
            FROM parcels_3d WHERE building_id = ? LIMIT 3000
        """, (building_id,))
        rows = cursor.fetchall()
        conn.close()
        if not rows:
            raise HTTPException(status_code=404, detail=f"Building {building_id} not found.")

        ZONING_COLORS = {
            'BEDRM': '#4CAF50', 'LIVRM': '#FF7043', 'KITCH': '#FFA726',
            'WASH': '#00BCD4', 'BALC': '#AB47BC', 'STOR': '#8D6E63',
            'STR': '#78909C', 'LIFT': '#607D8B', 'CORR': '#42A5F5',
            'HALL': '#FFB300', 'LOBBY': '#FF7043', 'UTIL': '#8D6E63',
            'PARK': '#546E7A', 'BRIDGE': '#9C27B0', 'OFFICE': '#2196F3',
            'CABIN': '#42A5F5', 'CONF': '#29B6F6', 'WARD': '#00BCD4',
            '4S': '#4CAF50', '2S': '#8BC34A', 'MISC': '#78909C'
        }

        parcels = []
        for row in rows:
            (ulpin, floor_, ptype, z_min, z_max, x0, x1, y0, y1,
             area, is_common, lat, lon) = row
            parcels.append({
                'ulpin': ulpin, 'floor': floor_, 'type': ptype,
                'z_min': z_min, 'z_max': z_max,
                'x_min': x0, 'x_max': x1, 'y_min': y0, 'y_max': y1,
                'carpet_area': area, 'is_common': bool(is_common),
                'color': ZONING_COLORS.get(ptype, '#BDBDBD'),
                'lat': lat, 'lon': lon,
            })
        return {'building_id': building_id, 'parcels': parcels, 'count': len(parcels)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest-dataset")
async def ingest_dataset_plan(
    plan_index: Optional[int] = Form(None),
    file: Optional[UploadFile] = File(None),
    building_id: Optional[str] = Form(None),
    building_name: Optional[str] = Form(None),
    total_floors: int = Form(4),
    floor_pitch_m: float = Form(3.0),
    room_clear_height_m: float = Form(2.6),
    anchor_lat: float = Form(20.9495556),
    anchor_lon: float = Form(79.0294722),
):
    """
    Ingest a plan directly from the ResPlan dataset (by index) or by uploading
    a .pkl / .json / .geojson floor plan file.
    """
    try:
        from parse_resplan import get_plan, extract_base_units
        from backend.services.cadastral_config import BuildingConfig
        from backend.services.cadastral_engine import run_cadastral_pipeline
        from backend.services.building_predictor import _generate_mesh_data

        plan = None
        base_units = None
        bid = (building_id or "").strip().upper()

        if file and file.filename:
            ext = os.path.splitext(file.filename)[1].lower()
            fd, temp_path = tempfile.mkstemp(suffix=ext, dir=UPLOAD_DIR)
            with os.fdopen(fd, 'wb') as buffer:
                shutil.copyfileobj(file.file, buffer)

            if ext == ".pkl":
                import pickle
                with open(temp_path, "rb") as fh:
                    pkl_data = pickle.load(fh)
                if isinstance(pkl_data, list):
                    plan = pkl_data[plan_index or 0]
                elif isinstance(pkl_data, dict):
                    plan = pkl_data
            elif ext in (".json", ".geojson"):
                import json
                with open(temp_path, "r", encoding="utf-8") as fh:
                    raw_json = json.load(fh)
                if isinstance(raw_json, list):
                    plan = raw_json[plan_index or 0]
                elif isinstance(raw_json, dict):
                    plan = raw_json

            elif ext in (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"):
                import cv2
                from backend.services.advanced_cv_pipeline import extract_rooms_advanced
                img = cv2.imread(temp_path)
                if img is not None:
                    base_units, _ = extract_rooms_advanced(img, building_type="residential")
                    if base_units:
                        plan = {"id": os.path.basename(file.filename), "net_area": sum(u.get('real_width_m', 0) * u.get('real_depth_m', 0) for u in base_units)}

            elif ext == ".pdf":
                config_temp = BuildingConfig(
                    building_id=bid or "TMP_PDF",
                    building_name=building_name or "Uploaded Floor Plan",
                    floor_plan_source=temp_path,
                    total_floors=total_floors,
                    floor_pitch_m=floor_pitch_m,
                    room_clear_height_m=room_clear_height_m
                )
                from backend.services.vector_extractor import extract_units_from_vector_pdf
                base_units = extract_units_from_vector_pdf(config_temp)
                if base_units:
                    plan = {"id": os.path.basename(file.filename), "net_area": sum(u.get('real_width_m', 0) * u.get('real_depth_m', 0) for u in base_units)}

            try:
                os.remove(temp_path)
            except Exception:
                pass

        if plan is None:
            # Fall back to dataset file
            pkl_path = "data/resplan/ResPlan.pkl"
            if not os.path.exists(pkl_path):
                raise HTTPException(status_code=400, detail="ResPlan.pkl not found at data/resplan/ResPlan.pkl.")
            idx = plan_index if plan_index is not None else 0
            plan = get_plan(pkl_path, idx)
            if not bid:
                bid = f"RESPLAN_{idx:04d}"

        if not bid:
            bid = "RESPLAN_AUTO"

        bname = building_name or f"Residential Building {bid}"
        if not base_units:
            base_units = extract_base_units(plan)

        config = BuildingConfig(
            building_id=bid,
            building_name=bname,
            category="Residential / Multi-Storey",
            total_floors=total_floors,
            floor_pitch_m=floor_pitch_m,
            room_clear_height_m=room_clear_height_m,
            anchor_lat=anchor_lat,
            anchor_lon=anchor_lon,
            floor_plan_source="data/resplan/ResPlan.pkl",
        )

        pipeline_result = run_cadastral_pipeline(
            config=config,
            persist_db=True,
            output_csv_dir="data",
            override_base_units=base_units,
        )

        # Generate Plotly 3D HTML twin
        import visualize_3d as viz
        html_twin_path = f"frontend/{bid.lower()}_3d_twin.html"
        viz.generate_3d_twin(
            csv_file=pipeline_result["output_csv"],
            output_html=html_twin_path,
            building_title=f"<b>3D ULPIN Digital Twin — {bname} ({bid})</b><br><sup>{pipeline_result.get('total_units', 0)} Volumetric 3D Parcels across {total_floors} Floors (Height: {pipeline_result.get('max_elevation_m', 0):.1f}m)</sup>"
        )

        # Update latest twin
        shutil.copyfile(html_twin_path, "frontend/latest_3d_twin.html")

        # Mesh data for client preview
        mesh_data = _generate_mesh_data(pipeline_result)

        return {
            "status": "success",
            "building_id": bid,
            "building_name": bname,
            "twin_url": f"/twin?building={bid}",
            "prediction_result": pipeline_result,
            "mesh_data": mesh_data,
            "stages": {
                "dataset_extraction": {
                    "status": "ok",
                    "plan_id": plan.get("id"),
                    "net_area_m2": plan.get("net_area"),
                    "rooms_extracted": len(base_units),
                },
                "cadastral_pipeline": {
                    "status": "ok",
                    "total_units": pipeline_result.get("total_units"),
                    "total_floors": pipeline_result.get("total_floors"),
                    "total_carpet_area_sqm": pipeline_result.get("total_carpet_area_sqm"),
                    "topology_passed": pipeline_result.get("topology_validation", {}).get("passed", False),
                    "sample_ulpin": pipeline_result.get("sample_ulpin"),
                }
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dataset ingestion failed: {str(e)}")

