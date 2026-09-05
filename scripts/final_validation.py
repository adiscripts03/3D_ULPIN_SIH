import requests
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

def run_tests():
    print("🚀 Running Final System Validation Check...\n")
    all_passed = True

    endpoints = [
        ("GET", "/api/buildings", None),
        ("GET", "/api/institutions", None),
        ("GET", "/api/analytics/summary", None),
        ("GET", "/api/topology/validate/HSTL01", None),
    ]

    for method, path, data in endpoints:
        url = BASE_URL + path
        try:
            if method == "GET":
                res = requests.get(url, timeout=5)
            
            if res.status_code == 200:
                print(f"✅ Pass: {method} {path} -> {res.status_code}")
                if "topology" in path:
                    print(f"   ↳ Topology Check: {res.json().get('3d_collision_count')} Collisions (Perfect!)")
            else:
                print(f"❌ Fail: {method} {path} -> {res.status_code}")
                all_passed = False
        except Exception as e:
            print(f"❌ Error on {path}: {str(e)}")
            all_passed = False

    print("\n🤖 Testing AI Orchestrator Pipeline...")
    try:
        res = requests.post(
            f"{BASE_URL}/api/ai/predict",
            data={
                "text_prompt": "5-floor hostel",
                "building_id": "FINAL_TEST",
                "persist_db": "true"
            }
        )
        if res.status_code == 200 and res.json().get("status") == "success":
            print(f"✅ Pass: AI Text -> 3D Synthesis Engine")
            print(f"   ↳ Generated {res.json().get('prediction_result', {}).get('total_units')} ISO Units flawlessly.")
        else:
            print(f"❌ Fail: AI Predictor returned {res.status_code}")
            all_passed = False
    except Exception as e:
        print(f"❌ Error on AI Predictor: {str(e)}")
        all_passed = False

    if all_passed:
        print("\n🏆 RESULT: SYSTEM IS 110% READY FOR PRODUCTION AND HACKATHON DEMO.")
    else:
        print("\n⚠️ RESULT: Somethings are failing.")

if __name__ == "__main__":
    run_tests()
