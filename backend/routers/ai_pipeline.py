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
