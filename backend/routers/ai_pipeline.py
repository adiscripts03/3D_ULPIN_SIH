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
            '4S': '#4CAF50', '2S': '#8BC34A',
            '2BHK': '#4CAF50', '3BHK': '#66BB6A', '1BHK': '#A5D6A7',
            'OFFICE': '#2196F3', 'CABIN': '#42A5F5',
            'WARD': '#00BCD4', 'ICU': '#EF9A9A',
            'WASH': '#26C6DA', 'CORR': '#5C6BC0', 'STR': '#78909C',
            'LIFT': '#AB47BC', 'HALL': '#FF7043', 'LOBBY': '#FF7043',
            'UTIL': '#9E9E9E', 'CONF': '#29B6F6', 'PARK': '#8D6E63',
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


# ── FLOOR PLAN → 3D ARCHITECTURE & OWNERSHIP CADASTRE ENDPOINTS ──────────────

@router.get("/floorplan-3d/status")
async def get_floorplan_3d_status():
    """Returns availability of the two ML models and 3D architectural pipeline."""
    from backend.services.floorplan_3d_ml import get_model_status
    return get_model_status()


@router.get("/floorplan-3d/samples")
async def get_floorplan_3d_samples():
    """Returns verified real sample floor plans for instant testing."""
    samples = [
        {
            "id": "sample_2bhk",
            "name": "2BHK Residential Apartment",
            "description": "Standard 2BHK residential flat with master bedroom, living hall, kitchen, and balcony.",
            "type": "Residential Flat",
            "path": "data/clean_sample_floor_plan.png",
            "format": "PNG",
        },
        {
            "id": "sample_multi_unit",
            "name": "Multi-Unit Apartment Floor",
            "description": "Floor plan dividing into distinct private flats of different owners along a central corridor.",
            "type": "Residential Complex",
            "path": "data/ideal_sample_floor_plan.png",
            "format": "PNG",
        },
        {
            "id": "sample_cad",
            "name": "Architectural CAD Drawing",
            "description": "High-precision CAD blueprint showing structural wall vectors and partitions.",
            "type": "CAD Vector Blueprint",
            "path": "data/sample_cad_floor_plan.png",
            "format": "PNG",
        },
        {
            "id": "sample_hostel_pdf",
            "name": "Hostel Multi-Storey Wing (PDF)",
            "description": "Official 10-floor institutional hostel block layout with 56 rooms per floor (HSTL01).",
            "type": "Institutional Multi-Storey",
            "path": "data/uploads/HSTL01_floor_plan.pdf",
            "format": "PDF",
        },
        {
            "id": "sample_fdd22",
            "name": "Residential Tower Block (FDD22)",
            "description": "High-density residential tower layout with symmetrical apartment units.",
            "type": "Residential Tower",
            "path": "data/uploads/FDD22_floor_plan.jpg",
            "format": "JPG",
        },
    ]

    # Check existence
    for s in samples:
        s["available"] = os.path.exists(s["path"])
    return {"samples": samples}


@router.post("/floorplan-3d/generate")
async def generate_floorplan_3d(
    floor_plan: Optional[UploadFile] = File(None),
    sample_id: Optional[str] = Form(None),
    building_name: str = Form("Surya Heights Residency"),
    floors: int = Form(5),
    wall_height: float = Form(3.0),
    model_type: str = Form("hybrid"),
):
    """
    Primary endpoint: converts a 2D floor plan into a 3D multi-storey building
    and identifies the distinct flats of different owners.
    """
    from backend.services.floorplan_3d_ml import run_floorplan_3d_pipeline

    file_bytes: Optional[bytes] = None
    filename = "floor_plan.png"

    if floor_plan and floor_plan.filename:
        filename = floor_plan.filename
        file_bytes = await floor_plan.read()
    elif sample_id:
        sample_map = {
            "sample_2bhk": "data/clean_sample_floor_plan.png",
            "sample_multi_unit": "data/ideal_sample_floor_plan.png",
            "sample_cad": "data/sample_cad_floor_plan.png",
            "sample_hostel_pdf": "data/uploads/HSTL01_floor_plan.pdf",
            "sample_fdd22": "data/uploads/FDD22_floor_plan.jpg",
        }
        sample_path = sample_map.get(sample_id)
        if not sample_path or not os.path.exists(sample_path):
            raise HTTPException(status_code=404, detail=f"Sample {sample_id} not found on disk.")
        filename = os.path.basename(sample_path)
        with open(sample_path, "rb") as f:
            file_bytes = f.read()
    else:
        # Default to clean sample floor plan if nothing provided
        default_path = "data/clean_sample_floor_plan.png"
        if os.path.exists(default_path):
            filename = "clean_sample_floor_plan.png"
            with open(default_path, "rb") as f:
                file_bytes = f.read()
        else:
            raise HTTPException(status_code=400, detail="Please upload a floor plan file or choose a sample.")

    if not file_bytes:
        raise HTTPException(status_code=400, detail="Empty floor plan file provided.")

    try:
        # Constrain floors between 1 and 25
        floors = max(1, min(int(floors), 25))
        wall_height = max(1.0, min(float(wall_height), 6.0))

        result = run_floorplan_3d_pipeline(
            file_bytes=file_bytes,
            filename=filename,
            building_name=building_name,
            floors=floors,
            wall_height_m=wall_height,
            model_type=model_type,
        )
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"3D Architecture Generation Failed: {str(e)}")


@router.get("/floorplan-3d/export-obj/{session_id}")
async def export_floorplan_obj(session_id: str):
    """Downloads the generated building as a standard Wavefront .OBJ 3D file."""
    from fastapi.responses import Response
    from backend.services.floorplan_3d_ml import EXPORT_CACHE

    cached = EXPORT_CACHE.get(session_id)
    if not cached or "obj" not in cached:
        raise HTTPException(status_code=404, detail="Session expired or not found. Please re-generate.")

    obj_content = cached["obj"]
    filename = f"Building_Architecture_{session_id}.obj"
    return Response(
        content=obj_content,
        media_type="text/plain",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.get("/floorplan-3d/export-unity/{session_id}")
async def export_floorplan_unity(session_id: str):
    """Downloads the generated building in FloorPlanTo3D Unity Client JSON format."""
    from backend.services.floorplan_3d_ml import EXPORT_CACHE

    cached = EXPORT_CACHE.get(session_id)
    if not cached or "unity" not in cached:
        raise HTTPException(status_code=404, detail="Session expired or not found. Please re-generate.")

    return cached["unity"]


@router.get("/floorplan-3d/export-cadastre/{session_id}")
async def export_floorplan_cadastre(session_id: str):
    """Downloads the full 3D ULPIN cadastral flat ownership registry."""
    from backend.services.floorplan_3d_ml import EXPORT_CACHE

    cached = EXPORT_CACHE.get(session_id)
    if not cached or "flats" not in cached:
        raise HTTPException(status_code=404, detail="Session expired or not found. Please re-generate.")

    return cached["flats"]

