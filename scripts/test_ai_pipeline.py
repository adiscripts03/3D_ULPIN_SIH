import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.services.building_predictor import predict_building
from backend.services.image_analyzer import classify_image, IMAGE_TYPE_FLOOR_PLAN
import numpy as np

def run_tests():
    print("Testing 1: Text-only prediction...")
    result = predict_building(text="10-floor hostel with 56 rooms per floor, 4-seater and 2-seater rooms", persist_db=False)
    if result.get("status") != "success":
        print(f"FAILED Text test: {result.get('stages', {}).get('cadastral_pipeline')}")
    else:
        print(f"PASS Text test. Generated {result['prediction_result']['total_units']} 3D parcels.")
        
    print("Testing 2: Image analyzer classifier sanity check...")
    # create a mock white image for floor plan
    mock_floor_plan = np.ones((800, 800, 3), dtype=np.uint8) * 255
    res = classify_image(mock_floor_plan)
    # Even if it lacks edges, lets see what it says
    print(f"Mock image classification: {res['image_type']}")

if __name__ == "__main__":
    run_tests()
