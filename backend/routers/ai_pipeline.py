from fastapi import APIRouter, File, UploadFile, Form, HTTPException, BackgroundTasks
from typing import Optional, Dict, Any
import os
import shutil
import tempfile
from fastapi.responses import JSONResponse

from backend.services.building_predictor import predict_building

router = APIRouter()

UPLOAD_DIR = "data/ai_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("/status")
def ai_pipeline_status():
    return {
        "status": "online",
        "capabilities": [
            "text_nlp_extraction",
            "image_cv_extraction",
            "exterior_photo_analysis",
            "video_frame_extraction",
            "synthetic_floor_plan_generation",
            "3d_ulpin_prediction"
        ],
        "models_loaded": "deterministic_cv_and_nlp"
    }


@router.post("/predict")
async def predict_3d_building(
    text_prompt: Optional[str] = Form(None),
    building_id: Optional[str] = Form(None),
    persist_db: bool = Form(True),
    image_file: Optional[UploadFile] = File(None),
    video_file: Optional[UploadFile] = File(None),
):
    """
    Master AI endpoint. 
    Accepts text prompt, image (floor plan/exterior), or video walkthrough.
    Returns full 3D building prediction + meshes.
    """
    if not any([text_prompt, image_file, video_file]):
        raise HTTPException(
            status_code=400,
            detail="Must provide at least one input: text_prompt, image_file, or video_file."
        )

    # Save uploaded files temporarily
    image_path = None
    if image_file:
        ext = os.path.splitext(image_file.filename)[1]
        fd, image_path = tempfile.mkstemp(suffix=ext, dir=UPLOAD_DIR)
        with os.fdopen(fd, 'wb') as f:
            shutil.copyfileobj(image_file.file, f)

    video_path = None
    if video_file:
        ext = os.path.splitext(video_file.filename)[1]
        fd, video_path = tempfile.mkstemp(suffix=ext, dir=UPLOAD_DIR)
        with os.fdopen(fd, 'wb') as f:
            shutil.copyfileobj(video_file.file, f)

    try:
        # Run orchestrator
        result = predict_building(
            text=text_prompt,
            image_path=image_path,
            video_path=video_path,
            building_id=building_id,
            persist_db=persist_db
        )
        
        return JSONResponse(status_code=200 if result.get('status') == 'success' else 207, content=result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup temp files
        if image_path and os.path.exists(image_path):
            os.remove(image_path)
        if video_path and os.path.exists(video_path):
            os.remove(video_path)


@router.post("/analyze/text")
async def analyze_text_input(prompt: str = Form(...)):
    """Analyze text NLP only."""
    result = predict_building(text=prompt, persist_db=False)
    if 'stages' in result and 'text_analysis' in result['stages']:
        return result['stages']['text_analysis']
    return result


@router.post("/analyze/image")
async def analyze_image_input(image_file: UploadFile = File(...)):
    """Analyze image CV only."""
    ext = os.path.splitext(image_file.filename)[1]
    fd, image_path = tempfile.mkstemp(suffix=ext, dir=UPLOAD_DIR)
    with os.fdopen(fd, 'wb') as f:
        shutil.copyfileobj(image_file.file, f)
    
    try:
        result = predict_building(image_path=image_path, persist_db=False)
        if 'stages' in result and 'image_analysis' in result['stages']:
            return result['stages']['image_analysis']
        return result
    finally:
        if os.path.exists(image_path):
            os.remove(image_path)
