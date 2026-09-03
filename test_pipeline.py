import os
import cv2
import numpy as np
import json

from backend.services.cadastral_config import BuildingConfig, RoomTypeRule
from backend.services.cadastral_engine import run_cadastral_pipeline
from backend.services.cv_extractor import extract_units_from_scanned_image
from backend.services.pointcloud_validator import (
    detect_floor_levels_unsupervised,
    validate_point_cloud_against_config
)

def test_hstl01_vector_parity():
    """Test 1: Config-driven vector pipeline produces exact parity for HSTL01."""
    config = BuildingConfig.load_by_building_id("HSTL01")
    res = run_cadastral_pipeline(config, persist_db=False)
    assert res["status"] == "SUCCESS"
    assert res["total_units"] == 700
    assert res["total_floors"] == 10
    assert res["residential_units"] == 560
    assert res["common_units"] == 140
    assert res["topology_validation"]["passed"] is True
    print("✅ test_hstl01_vector_parity PASSED")


def test_pointcloud_ml_clustering():
    """Test 2: ML unsupervised height clustering detects floor bands and pitch."""
    # Generate synthetic drone point cloud with 4 floors at 3.5m pitch
    ground_pts = np.random.normal(loc=0.0, scale=0.05, size=200)
    f1_pts = np.random.normal(loc=3.5, scale=0.08, size=400)
    f2_pts = np.random.normal(loc=7.0, scale=0.08, size=400)
    f3_pts = np.random.normal(loc=10.5, scale=0.08, size=400)
    f4_pts = np.random.normal(loc=14.0, scale=0.08, size=300)
    
    all_z = np.concatenate([ground_pts, f1_pts, f2_pts, f3_pts, f4_pts])
    
    ml_res = detect_floor_levels_unsupervised(all_z, min_floor_pitch_m=2.5)
    assert ml_res["status"] == "SUCCESS"
    # Should detect 5 levels (ground, 3.5, 7.0, 10.5, 14.0)
    assert ml_res["detected_floors_count"] >= 4
    assert 3.2 <= ml_res["estimated_pitch_m"] <= 3.8
    print(f"✅ test_pointcloud_ml_clustering PASSED: Detected {ml_res['detected_floors_count']} levels at {ml_res['estimated_pitch_m']}m pitch")


def test_cv_ocr_pipeline_on_synthetic_raster():
    """Test 3: Computer Vision & OCR pipeline on scanned/rasterized floor plan."""
    # Create synthetic floor plan image with drawn rooms and text
    img = np.ones((600, 800, 3), dtype=np.uint8) * 255
    
    # Draw rooms
    cv2.rectangle(img, (50, 50), (350, 250), (0, 0, 0), 3) # Room 1
    cv2.rectangle(img, (400, 50), (750, 250), (0, 0, 0), 3) # Room 2
    cv2.rectangle(img, (50, 300), (350, 550), (0, 0, 0), 3) # Room 3
    cv2.rectangle(img, (400, 300), (750, 550), (0, 0, 0), 3) # Room 4
    
    # Put text inside rooms
    cv2.putText(img, "OFFICE 101", (80, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    cv2.putText(img, "OFFICE 102", (430, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    cv2.putText(img, "WASHROOM", (80, 420), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    cv2.putText(img, "STAIRS", (450, 420), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    
    os.makedirs("scratch", exist_ok=True)
    test_img_path = "scratch/test_scanned_plan.png"
    cv2.imwrite(test_img_path, img)
    
    config = BuildingConfig(
        building_id="TEST01",
        building_name="Test Complex",
        floor_plan_source=test_img_path,
        floor_plan_type="scanned_image",
        total_floors=2,
        scale_x=0.05,
        room_type_rules=[
            RoomTypeRule(label_pattern=".*OFFICE.*", type="OFFICE", is_common=False),
            RoomTypeRule(label_pattern=".*WASH.*", type="WASH", is_common=True),
            RoomTypeRule(label_pattern=".*STAIR.*", type="STR", is_common=True)
        ]
    )
    
    units, ocr_report = extract_units_from_scanned_image(config)
    assert len(units) >= 4
    assert ocr_report["total_detected_units"] >= 4
    print(f"✅ test_cv_ocr_pipeline PASSED: Extracted {len(units)} units with mean OCR confidence {ocr_report['mean_ocr_confidence']}%")


if __name__ == "__main__":
    test_hstl01_vector_parity()
    test_pointcloud_ml_clustering()
    test_cv_ocr_pipeline_on_synthetic_raster()
    print("\n🎉 ALL TESTS PASSED SUCCESSFULLY!")
