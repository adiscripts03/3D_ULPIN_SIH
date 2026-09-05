import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.services.building_predictor import predict_building
from backend.services.cadastral_engine import run_cadastral_pipeline

def build_missing_campus():
    print("🚀 Initializing AI Pipeline to process remaining campus buildings...")

    buildings_to_build = [
        {
            "id": "ADMIN01",
            "prompt": "3-floor Administrative Complex with 15 rooms per floor, mostly offices and a few common washrooms."
        },
        {
            "id": "ACAD01",
            "prompt": "4-floor Academic Building with 12 rooms per floor, mostly large classrooms and a few labs."
        },
        {
            "id": "RES01",
            "prompt": "10-floor Residential Building with 8 flats per floor, mixing 3BHK and 2BHK units."
        }
    ]

    for bldg in buildings_to_build:
        print(f"\n⚙️  Processing {bldg['id']} via AI NLP Pipeline...")
        try:
            # The AI orchestrator will read the text, synthesize a floor plan, run ISO cadastral engine, and persist to DB automatically!
            result = predict_building(
                text=bldg["prompt"],
                building_id=bldg["id"],
                persist_db=True
            )
            
            if result.get("status") == "success":
                print(f"✅ Success! Generated {result.get('prediction_result', {}).get('total_units', 0)} 3D ULPIN parcels for {bldg['id']}.")
            else:
                print(f"❌ Failed to process {bldg['id']}: {result}")
        except Exception as e:
            print(f"⚠️ Error processing {bldg['id']}: {str(e)}")

    print("\n🎉 Master Campus Database fully populated via AI!")

if __name__ == "__main__":
    build_missing_campus()
