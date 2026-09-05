import sys
import os
import requests

# Test AI Pipeline 
def run_tests():
    url = "http://127.0.0.1:8000/api/ai/predict"
    
    # Test 1: Text only
    print("Testing Text Input...")
    try:
        r = requests.post(url, data={
            "text_prompt": "10-floor hostel with 56 rooms per floor, 4-seater and 2-seater rooms",
            "building_id": "TEST_001",
            "persist_db": False
        })
        print(f"Status: {r.status_code}")
        print("Success!" if r.status_code == 200 else r.text)
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    run_tests()
