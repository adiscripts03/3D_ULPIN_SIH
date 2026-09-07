"""
Building Predictor — 3D ULPIN AI/ML Pipeline Central Orchestrator v2
=====================================================================
Accepts ANY combination of inputs:
  - text description (natural language)
  - floor_plan image (scanned / CAD / photographed)
  - exterior_photo (building outside photo → floor count detection)
  - room_photos (interior room photos → room type inference)
  - video (walkthrough → best frame extraction → image pipeline)

Pipeline stages:
  1. Text NLP analysis (regex-based, zero API dependency)
  2. Floor plan → YOLO / Advanced OpenCV room extraction
  3. Exterior photo → YOLO / OpenCV floor count estimation
  4. Room photos → room type classification
  5. Multi-source fusion (floor_plan > exterior > room_photos > text)
  6. Floor plan synthesis (if no image available)
  7. Cadastral pipeline → 3D ULPIN generation + topology validation
  8. 3D mesh data generation for WebGL rendering
"""

import os
import uuid
import json
import traceback
from typing import Optional, Dict, Any, List

import cv2
import numpy as np

from dotenv import load_dotenv
load_dotenv()

from backend.services.text_analyzer import analyze_text
from backend.services.image_analyzer import analyze_image, IMAGE_TYPE_FLOOR_PLAN, IMAGE_TYPE_EXTERIOR
from backend.services.video_processor import process_video, save_frame_to_temp
from backend.services.floor_plan_synthesizer import synthesize_floor_plan
from backend.services.cadastral_config import BuildingConfig
from backend.services.cadastral_engine import run_cadastral_pipeline
from backend.services.advanced_cv_pipeline import extract_rooms_advanced
from backend.services.yolo_detector import (
    detect_rooms_yolo,
    analyze_exterior_yolo,
    fuse_multi_image_predictions,
    classify_room_photo,
    _YOLO_AVAILABLE,
)

UPLOAD_DIR = "data/ai_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ─────────────────── helpers ─────────────────────────────────────────────────

def _load_image(path: str) -> Optional[np.ndarray]:
    if not path or not os.path.exists(path):
        return None
    img = cv2.imread(path)
    if img is None:
        try:
            from PIL import Image as PILImage
            import numpy as _np
            pil = PILImage.open(path).convert("RGB")
            img = cv2.cvtColor(_np.array(pil), cv2.COLOR_RGB2BGR)
        except Exception:
            return None
    return img


def _make_building_config(params: Dict[str, Any], building_id: str,
                           plan_path: str) -> BuildingConfig:
    return BuildingConfig(
        building_id=building_id,
        building_name=params.get('building_name', 'AI Predicted Block'),
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


def _generate_mesh_data(pipeline_result: Dict[str, Any]) -> Dict[str, Any]:
    """Generate Plotly-compatible 3D mesh data from pipeline result."""
    building_id = pipeline_result.get('building_id', '?')
    try:
        from backend.database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ulpin_3d, floor, type, z_min, z_max,
                   real_x_start_m, real_x_end_m, real_y_start_m, real_y_end_m,
                   carpet_area_sqm, is_common_property, latitude, longitude
            FROM parcels_3d WHERE building_id = ? LIMIT 2000
        """, (building_id,))
        rows = cursor.fetchall()
        conn.close()

        ZONING_COLORS = {
            'BEDRM': '#4CAF50', 'LIVRM': '#FF7043', 'KITCH': '#FFA726',
            'WASH': '#00BCD4', 'BALC': '#AB47BC', 'STOR': '#8D6E63',
            'STR': '#78909C', 'LIFT': '#607D8B', 'CORR': '#42A5F5',
            'HALL': '#FFB300', 'LOBBY': '#FF7043', 'UTIL': '#8D6E63',
            'PARK': '#546E7A', 'BRIDGE': '#9C27B0', 'OFFICE': '#2196F3',
            'CABIN': '#42A5F5', 'CONF': '#29B6F6', 'WARD': '#00BCD4',
            '4S': '#4CAF50', '2S': '#8BC34A', 'MISC': '#78909C'
        }
        STATUS_COLORS = {'vacant': '#4CAF50', 'partial': '#FFC107', 'full': '#F44336'}

        parcels_out = []
        for row in rows:
            (ulpin, floor_, ptype, z_min, z_max,
             x0, x1, y0, y1, area, is_common, lat, lon) = row

            color = ZONING_COLORS.get(ptype, '#BDBDBD')
            parcels_out.append({
                'ulpin': ulpin,
                'floor': floor_,
                'type': ptype,
                'z_min': z_min,
                'z_max': z_max,
                'x_min': x0, 'x_max': x1,
                'y_min': y0, 'y_max': y1,
                'carpet_area': area,
                'is_common': bool(is_common),
                'color': color,
                'lat': lat,
                'lon': lon,
            })
        return {'parcels': parcels_out, 'count': len(parcels_out)}
    except Exception as e:
        return {'parcels': [], 'count': 0, 'error': str(e)}


# ─────────────────── main orchestrator ───────────────────────────────────────

def predict_building(
    text: Optional[str] = None,
    image_path: Optional[str] = None,
    video_path: Optional[str] = None,
    exterior_image_path: Optional[str] = None,
    room_image_paths: Optional[List[str]] = None,
    building_id: Optional[str] = None,
    persist_db: bool = True,
    output_csv_dir: str = "data",
    use_yolo: bool = True,
) -> Dict[str, Any]:
    """
    Master building predictor — accepts text, images, video.
    Returns full 3D ULPIN prediction + mesh data.
    """
    if not any([text, image_path, video_path, exterior_image_path,
                room_image_paths]):
        return {'error': 'At least one input must be provided.'}

    bid = building_id or f"AI_{uuid.uuid4().hex[:6].upper()}"
    report: Dict[str, Any] = {
        'building_id': bid,
        'inputs_provided': {
            'text': bool(text),
            'floor_plan_image': bool(image_path),
            'exterior_image': bool(exterior_image_path),
            'room_images': len(room_image_paths) if room_image_paths else 0,
            'video': bool(video_path),
        },
        'yolo_available': _YOLO_AVAILABLE,
        'api_mode': 'yolo_deep_learning' if (_YOLO_AVAILABLE and use_yolo)
                   else 'advanced_opencv_cv',
        'stages': {},
    }

    # ── Stage 1: Text NLP ──────────────────────────────────────────────────
    text_params = None
    if text and text.strip():
        text_params = analyze_text(text)
        report['stages']['text_analysis'] = {
            'status': 'ok' if 'error' not in text_params else 'error',
            'confidence': text_params.get('confidence', 0),
            'building_type': text_params.get('building_type', 'hostel'),
            'total_floors': text_params.get('total_floors', 5),
            'rooms_per_floor': text_params.get('rooms_per_floor', 20),
        }

    # ── Stage 2: Video → best frame ───────────────────────────────────────
    effective_floor_plan_path = image_path
    if video_path and os.path.exists(video_path):
        try:
            v = process_video(video_path, max_sample_frames=30, top_n=3)
            report['stages']['video_processing'] = {
                'status': 'ok',
                'total_sampled': v['total_sampled'],
                'floor_plan_frames_found': v['floor_plan_frames_found'],
                'duration_s': v['video_duration_s'],
            }
            if v['best_frames']:
                best_frame = v['best_frames'][0]['frame']
                effective_floor_plan_path = save_frame_to_temp(best_frame)
                report['stages']['video_processing']['best_frame_ts'] = (
                    v['best_frames'][0]['timestamp_s'])
        except Exception as e:
            report['stages']['video_processing'] = {'status': 'error', 'error': str(e)}

    # ── Stage 3: Floor Plan Image Analysis ────────────────────────────────
    floor_plan_result = None
    base_units_from_image = None

    if effective_floor_plan_path and os.path.exists(effective_floor_plan_path):
        fp_img = _load_image(effective_floor_plan_path)
        if fp_img is not None:
            try:
                # Auto-classify image type first
                cls_result = analyze_image(fp_img)
                img_type = cls_result['image_type']
                report['stages']['floor_plan_analysis'] = {
                    'status': 'ok',
                    'image_type_detected': img_type,
                    'classification_confidence': cls_result['classification']['confidence'],
                }

                building_type = text_params.get('building_type', 'residential') if text_params else 'residential'

                if img_type in (IMAGE_TYPE_FLOOR_PLAN, 'unknown'):
                    # Use YOLO if available, else advanced OpenCV
                    if _YOLO_AVAILABLE and use_yolo:
                        base_units_yolo, yolo_diag = detect_rooms_yolo(fp_img)
                        if len(base_units_yolo) >= 3:
                            base_units_from_image = base_units_yolo
                            report['stages']['floor_plan_analysis']['extractor'] = 'yolov8'
                            report['stages']['floor_plan_analysis']['yolo_detections'] = yolo_diag.get('yolo_detections', 0)
                        else:
                            # YOLO didn't get enough → advanced OpenCV
                            base_units_from_image, adv_diag = extract_rooms_advanced(
                                fp_img, building_type=building_type)
                            report['stages']['floor_plan_analysis']['extractor'] = 'advanced_opencv'
                            report['stages']['floor_plan_analysis']['cv_strategy'] = adv_diag.get('strategy_used', 'unknown')
                    else:
                        base_units_from_image, adv_diag = extract_rooms_advanced(
                            fp_img, building_type=building_type)
                        report['stages']['floor_plan_analysis']['extractor'] = 'advanced_opencv'
                        report['stages']['floor_plan_analysis']['cv_strategy'] = adv_diag.get('strategy_used', 'unknown')

                    report['stages']['floor_plan_analysis']['rooms_extracted'] = len(base_units_from_image or [])
                    floor_plan_result = {'base_units': base_units_from_image}

                elif img_type == IMAGE_TYPE_EXTERIOR:
                    # Treat as exterior (fall through to Stage 4)
                    exterior_image_path = exterior_image_path or effective_floor_plan_path
                    report['stages']['floor_plan_analysis']['note'] = 'Reclassified as exterior photo'

            except Exception as e:
                report['stages']['floor_plan_analysis'] = {
                    'status': 'error', 'error': str(e),
                    'traceback': traceback.format_exc()
                }

    # ── Stage 4: Exterior Photo Analysis ──────────────────────────────────
    exterior_result = None
    if exterior_image_path and os.path.exists(exterior_image_path):
        ext_img = _load_image(exterior_image_path)
        if ext_img is not None:
            try:
                if _YOLO_AVAILABLE and use_yolo:
                    exterior_result = analyze_exterior_yolo(ext_img)
                    method = exterior_result.get('method', 'yolo')
                else:
                    from backend.services.image_analyzer import analyze_exterior_photo
                    exterior_result = analyze_exterior_photo(ext_img)
                    method = 'opencv_hough'

                report['stages']['exterior_analysis'] = {
                    'status': 'ok',
                    'detected_floors': exterior_result.get('detected_floors', 0),
                    'units_per_floor': exterior_result.get('estimated_units_per_floor', 0),
                    'confidence': exterior_result.get('confidence', 0),
                    'method': method,
                }
            except Exception as e:
                report['stages']['exterior_analysis'] = {'status': 'error', 'error': str(e)}

    # ── Stage 5: Room Photos Analysis ─────────────────────────────────────
    room_photo_results = None
    if room_image_paths:
        room_photo_results = []
        for rp in room_image_paths:
            if rp and os.path.exists(rp):
                try:
                    rimg = _load_image(rp)
                    if rimg is not None:
                        rresult = classify_room_photo(rimg)
                        room_photo_results.append(rresult)
                except Exception:
                    pass
        report['stages']['room_photo_analysis'] = {
            'status': 'ok',
            'photos_analyzed': len(room_photo_results),
            'inferred_types': [r['inferred_room_type'] for r in room_photo_results],
        }

    # ── Stage 6: Multi-Source Fusion ──────────────────────────────────────
    fused_params = fuse_multi_image_predictions(
        floor_plan_result=floor_plan_result,
        exterior_result=exterior_result,
        room_photo_results=room_photo_results,
        text_params=text_params,
    )
    report['stages']['fusion'] = {
        'status': 'ok',
        'sources_used': fused_params.get('fusion_sources', []),
        'final_floors': fused_params.get('total_floors'),
        'final_rooms_per_floor': fused_params.get('rooms_per_floor'),
        'final_confidence': fused_params.get('confidence'),
    }

    # ── Stage 7: Floor Plan Synthesis (if no image base_units) ────────────
    base_units = fused_params.pop('floor_plan_base_units', None)
    if not base_units:
        base_units, synth_meta = synthesize_floor_plan(
            rooms_per_floor=fused_params.get('rooms_per_floor', 8),
            room_types=fused_params.get('room_types', ['LIVRM', 'BEDRM', 'KITCH', 'WASH', 'BALC']),
            building_type=fused_params.get('building_type', 'residential'),
            building_width_m=fused_params.get('building_width_m'),
            building_depth_m=fused_params.get('building_depth_m'),
            residential_ratio=fused_params.get('residential_ratio', 0.80),
        )
        report['stages']['floor_plan_synthesis'] = {
            'status': 'ok',
            'units_generated': len(base_units),
            'layout': synth_meta.get('layout', 'double_loaded_corridor'),
            'dimensions': f"{synth_meta.get('actual_width_m', 0)}m × {synth_meta.get('actual_depth_m', 0)}m",
        }

    # ── Stage 8: Cadastral Pipeline ───────────────────────────────────────
    try:
        placeholder = os.path.join(UPLOAD_DIR, f"{bid}_placeholder.json")
        with open(placeholder, 'w') as f:
            json.dump({}, f)

        config = _make_building_config(fused_params, bid, placeholder)
        pipeline_result = run_cadastral_pipeline(
            config,
            persist_db=persist_db,
            output_csv_dir=output_csv_dir,
            override_base_units=base_units,
        )

        # Generate mesh data for 3D rendering
        mesh_data = _generate_mesh_data(pipeline_result) if persist_db else {}

        # Generate full interactive 3D HTML twin
        try:
            import visualize_3d as viz
            html_twin_path = f"frontend/{bid.lower()}_3d_twin.html"
            viz.generate_3d_twin(
                csv_file=pipeline_result["output_csv"],
                output_html=html_twin_path,
                building_title=f"<b>3D ULPIN Digital Twin — {fused_params.get('building_name', bid)} ({bid})</b><br><sup>{pipeline_result.get('total_units', 0)} Volumetric 3D Parcels across {pipeline_result.get('total_floors', 0)} Floors (Height: {pipeline_result.get('max_elevation_m', 0):.1f}m)</sup>"
            )
            report['twin_url'] = f"/static/{bid.lower()}_3d_twin.html"
            shutil.copyfile(html_twin_path, "frontend/latest_3d_twin.html")
        except Exception as ve:
            report['twin_error'] = str(ve)

        report['stages']['cadastral_pipeline'] = {
            'status': 'ok',
            'total_units': pipeline_result.get('total_units', 0),
            'total_floors': pipeline_result.get('total_floors', 0),
            'residential_units': pipeline_result.get('residential_units', 0),
            'common_units': pipeline_result.get('common_units', 0),
            'total_carpet_area_sqm': pipeline_result.get('total_carpet_area_sqm', 0),
            'topology_passed': pipeline_result.get('topology_validation', {}).get('passed', False),
            'sample_ulpin': pipeline_result.get('sample_ulpin', 'N/A'),
        }
        report['prediction_result'] = pipeline_result
        report['mesh_data'] = mesh_data
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
            'total_floors': fused_params.get('total_floors', 5),
            'units_per_floor': len(base_units) if base_units else 0,
        }

    report['building_params'] = {k: v for k, v in fused_params.items()
                                   if k not in ('profile', 'fusion_sources')}
    report['base_units_count'] = len(base_units) if base_units else 0

    return report
