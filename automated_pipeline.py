#!/usr/bin/env python3
"""
🏛️ National 3D ULPIN Automated Ingestion Pipeline
Department of Land Resources (DoLR) | Ministry of Rural Development
Zero-Friction Ingestion Engine for Multi-Storey Estates, Housing Societies & Institutions
"""

import os
import sys
import json
import argparse
from typing import Optional

from backend.services.cadastral_config import BuildingConfig
from backend.services.cadastral_engine import run_cadastral_pipeline

def run_pipeline_cli(
    config_path: Optional[str] = None,
    building_id: Optional[str] = None,
    pdf_path: Optional[str] = None,
    total_floors: Optional[int] = None,
    anchor_lat: Optional[float] = None,
    anchor_lon: Optional[float] = None,
    point_cloud_path: Optional[str] = None
):
    """
    Executes the config-driven ingestion pipeline via CLI with full parameter overrides.
    """
    # 1. Load Base Configuration
    if config_path and os.path.exists(config_path):
        config = BuildingConfig.from_json_file(config_path)
    elif building_id:
        try:
            config = BuildingConfig.load_by_building_id(building_id)
        except FileNotFoundError:
            print(f"⚠️ Config not found for {building_id}, using default base configuration.")
            config = BuildingConfig(
                building_id=building_id,
                building_name=f"Building {building_id}",
                floor_plan_source=pdf_path if pdf_path else "data/floor_plan.pdf"
            )
    else:
        # Default to HSTL01
        default_config_path = "config/buildings/HSTL01.json"
        if os.path.exists(default_config_path):
            config = BuildingConfig.from_json_file(default_config_path)
        else:
            config = BuildingConfig(
                building_id="HSTL01",
                building_name="Hostel Block A",
                floor_plan_source="data/floor_plan.pdf"
            )

    # 2. Apply any CLI argument overrides
    if pdf_path:
        config.floor_plan_source = pdf_path
    if total_floors:
        config.total_floors = total_floors
    if anchor_lat:
        config.anchor_lat = anchor_lat
    if anchor_lon:
        config.anchor_lon = anchor_lon
    if point_cloud_path:
        config.point_cloud_source = point_cloud_path

    print(f"\n============================================================")
    print(f"  🏛️ NATIONAL 3D ULPIN AUTOMATED INGESTION ENGINE")
    print(f"  Department of Land Resources (DoLR) | ISO 19152 LADM v2")
    print(f"  Building: {config.building_name} ({config.building_id})")
    print(f"  Floors: {config.total_floors} | Anchor: ({config.anchor_lat}, {config.anchor_lon})")
    print(f"  Source: {config.floor_plan_source}")
    print(f"============================================================")

    print("\n[Step 1/5] Extracting architectural geometry via config-driven rules...")
    res = run_cadastral_pipeline(config, persist_db=True, output_csv_dir="data")

    print(f" -> Extraction Method: {res['extraction_method'].upper()}")
    print(f" -> Extracted {res['total_units'] // res['total_floors']} base architectural units per floor.")

    # Display OCR metrics if scanned image pipeline was used
    if res.get("ocr_diagnostics"):
        ocr = res["ocr_diagnostics"]
        print(f"\n[OCR Quality Audit]")
        print(f" -> Mean OCR Confidence: {ocr['mean_ocr_confidence']}%")
        print(f" -> High-Confidence Units: {ocr['high_confidence_units']} / {ocr['total_detected_units']}")
        if ocr['low_confidence_units_count'] > 0:
            print(f" ⚠️ Flagged {ocr['low_confidence_units_count']} low-confidence units for surveyor review:")
            for w in ocr['low_confidence_warnings'][:5]:
                print(f"    • Unit {w['unit_id']}: Confidence {w['confidence_score']}% ({w['ocr_text'] or 'Blank'})")

    print(f"\n[Step 2/5] Stacking {config.total_floors} vertical floors ({config.floor_pitch_m}m pitch)...")
    print(f" -> Generated {res['total_units']} 3D volumetric parcels.")
    print(f" -> Residential/Private Units: {res['residential_units']} | Common Core Units: {res['common_units']}")
    print(f" -> Total Carpet Area: {res['total_carpet_area_sqm']:,.2f} m² | Gross Airspace: {res['total_volume_cbm']:,.2f} m³")

    print("\n[Step 3/5] Executing 3D Volumetric Topology Audit...")
    topo = res["topology_validation"]
    if topo["passed"]:
        print(f" ✅ 3D Topology: 100% Unique ULPINs, 0 Spatial Collisions. Perfect volumetric integrity.")
    else:
        if topo["duplicate_errors"]:
            print(f" ❌ Uniqueness Error: Found duplicates: {topo['duplicate_errors']}")
        if topo["collision_count"] > 0:
            print(f" ❌ Topology Error: {topo['collision_count']} spatial collisions detected.")

    print("\n[Step 4/5] Drone Photogrammetry / Point Cloud Height Validation...")
    pc = res["point_cloud_audit"]
    if pc["status"] == "SKIPPED":
        print(f" ℹ️ Drone point cloud validation: Skipped (no .ply/.xyz file provided).")
    elif pc["status"] == "VERIFIED":
        print(f" ✅ {pc['message']}")
    else:
        print(f" ⚠️ {pc['message']}")

    print("\n[Step 5/5] Persisting Cadastral Datasets & Database...")
    print(f" -> Master CSV: {res['output_csv']}")
    print(f" -> SQLite Spatial DB: data/cadastre_3d.db (updated)")

    print(f"\n============================================================")
    print(f"  🎉 Pipeline completed successfully!")
    print(f"  Summary for Building {config.building_id}:")
    print(f"   • Total 3D Parcels: {res['total_units']}")
    print(f"   • Max Airspace Elevation: {res['max_elevation_m']}m | Floors: {config.total_floors}")
    print(f"   • Sample 3D ULPIN: {res['sample_ulpin']}")
    print(f"============================================================\n")

    return res


def main():
    parser = argparse.ArgumentParser(
        description="National 3D ULPIN Automated Ingestion Pipeline (Config-Driven)"
    )
    parser.add_argument("--config", "-c", default=None, help="Path to per-building JSON config (e.g. config/buildings/HSTL01.json)")
    parser.add_argument("--building", "-b", default="HSTL01", help="Building ID (e.g. HSTL01, ADMIN01, ACAD01, RES01)")
    parser.add_argument("--pdf", default=None, help="Override path to floor plan file (PDF or image)")
    parser.add_argument("--floors", type=int, default=None, help="Override total number of floors")
    parser.add_argument("--lat", type=float, default=None, help="Override anchor latitude")
    parser.add_argument("--lon", type=float, default=None, help="Override anchor longitude")
    parser.add_argument("--point-cloud", default=None, help="Optional path to drone photogrammetry point cloud (.ply, .xyz, .las)")

    args = parser.parse_args()
    run_pipeline_cli(
        config_path=args.config,
        building_id=args.building,
        pdf_path=args.pdf,
        total_floors=args.floors,
        anchor_lat=args.lat,
        anchor_lon=args.lon,
        point_cloud_path=args.point_cloud
    )


if __name__ == "__main__":
    main()
