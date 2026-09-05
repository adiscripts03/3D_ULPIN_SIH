"""
Building Predictor — 3D ULPIN AI/ML Pipeline Central Orchestrator
==================================================================
Takes ANY combination of inputs (text, image, video) and produces a
fully predicted 3D building: floor plans → 3D parcels → Plotly mesh data.
"""

import os
import uuid
import json
import traceback
from typing import Optional, Dict, Any, List

import cv2
import numpy as np

# Load environment variables if external API Keys are provided
from dotenv import load_dotenv
load_dotenv()

from backend.services.text_analyzer import analyze_text
from backend.services.image_analyzer import analyze_image, IMAGE_TYPE_FLOOR_PLAN
from backend.services.video_processor import process_video, save_frame_to_temp
from backend.services.floor_plan_synthesizer import synthesize_floor_plan
from backend.services.cadastral_config import BuildingConfig
from backend.services.cadastral_engine import run_cadastral_pipeline

UPLOAD_DIR = "data/ai_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def _load_image(path: str) -> Optional[np.ndarray]:
    if not path or not os.path.exists(path): return None
    return cv2.imread(path)

def _params_from_text(text: str) -> Dict[str, Any]:
    if not text or not text.strip():
        return {
            'building_type': 'hostel',
            'building_name': 'AI Predicted Block',
            'category': 'Student Residence',
            'total_floors': 5,
            'rooms_per_floor': 20,
            'room_types': ['4S', '2S'],
            'common_types': ['WASH', 'CORR', 'STR'],
            'residential_ratio': 0.80,
            'floor_pitch_m': 3.4,
            'room_clear_height_m': 2.9,
            'anchor_lat': 20.9495556,
            'anchor_lon': 79.0294722,
            'building_width_m': None,
            'building_depth_m': None,
            'confidence': 30.0,
            'extraction_method': 'defaults',
        }
    return analyze_text(text)

def _make_building_config(params: Dict[str, Any], building_id: str, plan_path: str) -> BuildingConfig:
    return BuildingConfig(
        building_id=building_id,
        building_name=params.get('building_name', 'AI Block'),
        category=params.get('category', 'Institutional / Multi-Storey'),
        floor_plan_source=plan_path,
        floor_plan_type='auto',
        anchor_lat=params.get('anchor_lat', 20.9495556),
        anchor_lon=params.get('anchor_lon', 79.0294722),
        total_floors=params.get('total_floors', 5),
        floor_pitch_m=params.get('floor_pitch_m', 3.4),
        room_clear_height_m=params.get('room_clear_height_m', 2.9),
        slab_thickness_m=0.5,
        scale_x=0.1362088535754824,
        room_type_rules=[],
    )

def predict_building(
    text: Optional[str] = None,
    image_path: Optional[str] = None,
    video_path: Optional[str] = None,
    building_id: Optional[str] = None,
    persist_db: bool = True,
    output_csv_dir: str = "data",
) -> Dict[str, Any]:
    
    if not any([text, image_path, video_path]):
        return {'error': 'At least one input (text, image, or video) must be provided.'}

    bid = building_id or f"AI_{uuid.uuid4().hex[:6].upper()}"
    report: Dict[str, Any] = {
        'building_id': bid,
        'inputs_provided': {
            'text': bool(text),
            'image': bool(image_path),
            'video': bool(video_path),
        },
        'api_mode': 'external_llm_vision' if os.getenv('OPENAI_API_KEY') else 'local_deterministic_cv',
        'stages': {},
    }

    # 1. Text Analysis
    params = _params_from_text(text) if text else _params_from_text('')
    if text:
        report['stages']['text_analysis'] = {
            'status': 'ok' if 'error' not in params else 'error',
            'confidence': params.get('confidence', 0),
            'extracted': {k: v for k, v in params.items() if k != 'profile'},
        }

    # 2. Image / Video Analysis
    base_units = None
    effective_image_path = image_path

    if video_path and os.path.exists(video_path):
        try:
            vresult = process_video(video_path, max_sample_frames=30, top_n=3)
            report['stages']['video_processing'] = {
                'status': 'ok',
                'total_sampled': vresult['total_sampled'],
                'floor_plan_frames_found': vresult['floor_plan_frames_found'],
                'duration_s': vresult['video_duration_s'],
            }
            if vresult['best_frames']:
                best_frame = vresult['best_frames'][0]['frame']
                effective_image_path = save_frame_to_temp(best_frame)
                report['stages']['video_processing']['best_frame_ts'] = vresult['best_frames'][0]['timestamp_s']
        except Exception as e:
            report['stages']['video_processing'] = {'status': 'error', 'error': str(e)}

    if effective_image_path and os.path.exists(effective_image_path):
        img = _load_image(effective_image_path)
        if img is not None:
            iresult = analyze_image(img)
            report['stages']['image_analysis'] = {
                'status': 'ok',
                'image_type': iresult['image_type'],
                'classification_confidence': iresult['classification']['confidence'],
            }
            if iresult['image_type'] == IMAGE_TYPE_FLOOR_PLAN:
                base_units = iresult.get('base_units', [])
                report['stages']['image_analysis']['rooms_extracted'] = len(base_units)
            else:
                ext = iresult.get('exterior_analysis', {})
                dfloors = ext.get('detected_floors', params.get('total_floors', 5))
                dunits = ext.get('estimated_units_per_floor', params.get('rooms_per_floor', 20))
                if not text:
                    params['total_floors'] = dfloors
                    params['rooms_per_floor'] = dunits
                report['stages']['image_analysis']['detected_floors'] = dfloors
                report['stages']['image_analysis']['est_units_per_floor'] = dunits
        else:
            report['stages']['image_analysis'] = {'status': 'error', 'error': 'Could not load image'}

    # 3. Floor Plan Synthesis
    if not base_units:
        base_units, synth_meta = synthesize_floor_plan(
            rooms_per_floor=params.get('rooms_per_floor', 20),
            room_types=params.get('room_types', ['4S', '2S']),
            building_type=params.get('building_type', 'hostel'),
            building_width_m=params.get('building_width_m'),
            building_depth_m=params.get('building_depth_m'),
            residential_ratio=params.get('residential_ratio', 0.80),
        )
        report['stages']['floor_plan_synthesis'] = {
            'status': 'ok',
            'metadata': synth_meta,
            'units_generated': len(base_units),
        }

    # 4. Cadastral Pipeline
    try:
        placeholder = os.path.join(UPLOAD_DIR, f"{bid}_placeholder.json")
        with open(placeholder, 'w') as f: json.dump({}, f)
        config = _make_building_config(params, bid, placeholder)

        # Call the engine with the override parameter
        pipeline_result = run_cadastral_pipeline(
            config, 
            persist_db=persist_db,
            output_csv_dir=output_csv_dir,
            override_base_units=base_units
        )

        report['stages']['cadastral_pipeline'] = {
            'status': 'ok',
            'total_units': pipeline_result.get('total_units', len(base_units)),
            'sample_ulpin': pipeline_result.get('sample_ulpin', 'N/A'),
            'topology_validation': pipeline_result.get('topology_validation', {}),
        }
        report['prediction_result'] = pipeline_result
        report['status'] = 'success'

    except Exception as e:
        report['stages']['cadastral_pipeline'] = {
            'status': 'error',
            'error': str(e),
            'traceback': traceback.format_exc(),
        }
        report['status'] = 'partial'
        report['prediction_result'] = {
            'building_id': bid,
            'total_floors': params.get('total_floors', 5),
            'units_per_floor': len(base_units) if base_units else 0,
            'params': {k: v for k, v in params.items() if k != 'profile'},
        }

    report['building_params'] = {k: v for k, v in params.items() if k != 'profile'}
    report['base_units_count'] = len(base_units) if base_units else 0

    return report
