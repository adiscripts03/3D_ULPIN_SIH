#!/usr/bin/env python3
"""
ingest_floorplan.py -- Universal Floor Plan -> 3D ULPIN Ingestion Pipeline
===========================================================================
ONE entry point to rule them all.

Accepts any of:
  - ResPlan .pkl / .json dataset file  (flag: --source *.pkl / *.json)
  - Pre-extracted base_units JSON       (flag: --base-units *.json)
  - Existing building config            (flag: --config *.json  OR  --building HSTL01)

Then runs the full stack:
  [parse_resplan / json loader]
        |
        v
  [cadastral_engine.run_cadastral_pipeline]   <- georef + stacking + ULPIN
        |
        v
  [visualize_3d.main (Plotly Mesh3d)]         <- interactive HTML output

Examples
--------
  # From ResPlan dataset (plan index 0, 3-storey building):
  python ingest_floorplan.py \
      --source data/resplan/ResPlan.pkl \
      --plan-index 0 \
      --building-id RESPLAN_0001 \
      --building-name "Apartment Block A" \
      --floors 3 \
      --lat 28.6139 --lon 77.2090

  # From a pre-extracted base_units JSON (output of parse_resplan.py):
  python ingest_floorplan.py \
      --base-units data/resplan_base_units_0.json \
      --building-id RESPLAN_0001 \
      --floors 5

  # From an existing building config (hostel, college, etc.):
  python ingest_floorplan.py --building HSTL01

  # From a vector CAD PDF:
  python ingest_floorplan.py \
      --pdf data/floor_plan.pdf \
      --building-id CUSTOM_01 \
      --floors 4 \
      --lat 19.076 --lon 72.877
"""

import os
import sys
import json
import argparse
import subprocess
import logging
from typing import Any, Dict, List, Optional

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_base_units_json(path: str) -> List[Dict[str, Any]]:
    """Load a pre-extracted base_units list from JSON."""
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        raise TypeError(f"Expected list in {path}, got {type(data)}")
    log.info("Loaded %d base units from %s", len(data), path)
    return data


def _build_config(args) -> "BuildingConfig":
    """Construct a BuildingConfig from CLI arguments."""
    from backend.services.cadastral_config import BuildingConfig

    building_id   = args.building_id or "RESPLAN_0001"
    building_name = args.building_name or f"Building {building_id}"

    config = BuildingConfig(
        building_id=building_id,
        building_name=building_name,
        category=args.category or "Residential / Multi-Storey",
        description=args.description or f"3D ULPIN generated from ResPlan dataset.",
        floor_plan_source=args.pdf or "data/floor_plan.pdf",
        floor_plan_type="auto" if not args.pdf else "vector_pdf",
        anchor_lat=args.lat or 20.9495556,
        anchor_lon=args.lon or 79.0294722,
        total_floors=args.floors or 1,
        floor_pitch_m=args.floor_pitch or 3.0,
        room_clear_height_m=args.room_height or 2.6,
        slab_thickness_m=0.4,
    )
    return config


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run_ingestion(args):
    """Full ingestion: parse -> engine -> visualise."""

    # ---- Step 0: Resolve base_units ----------------------------------------
    override_units: Optional[List[Dict[str, Any]]] = None

    if args.source:
        # ResPlan .pkl / .json
        ext = os.path.splitext(args.source)[1].lower()
        if ext not in (".pkl", ".json", ".geojson"):
            log.error("--source must be a .pkl or .json file. Got: %s", args.source)
            sys.exit(1)

        log.info("--- Step 0: Parsing ResPlan dataset ---")
        from parse_resplan import get_plan, extract_base_units
        plan = get_plan(args.source, args.plan_index or 0)
        override_units = extract_base_units(plan, min_area_sqm=args.min_area or 0.5)

        # Optionally persist base_units for debugging
        if args.save_base_units:
            out_path = args.save_base_units
            os.makedirs(os.path.dirname(out_path) if os.path.dirname(out_path) else ".", exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as fh:
                json.dump(override_units, fh, indent=2)
            log.info("Base units saved -> %s", out_path)

    elif args.base_units:
        # Pre-extracted JSON
        log.info("--- Step 0: Loading pre-extracted base_units ---")
        override_units = _load_base_units_json(args.base_units)

    # If neither --source nor --base-units are given, the engine uses the PDF
    # or existing config (original hostel-style pipeline path).

    # ---- Step 1: Build config ----------------------------------------------
    log.info("--- Step 1: Building configuration ---")

    from backend.services.cadastral_config import BuildingConfig

    if args.config and os.path.exists(args.config):
        config = BuildingConfig.from_json_file(args.config)
        log.info("Loaded config: %s", args.config)
    elif args.building and not args.building_id:
        # Load by well-known building ID (e.g. HSTL01)
        try:
            config = BuildingConfig.load_by_building_id(args.building)
            log.info("Loaded config for building: %s", args.building)
        except FileNotFoundError:
            log.warning("No config found for %s, using CLI args.", args.building)
            config = _build_config(args)
    else:
        config = _build_config(args)

    # CLI argument overrides (always win)
    if args.floors:
        config.total_floors = args.floors
    if args.lat:
        config.anchor_lat = args.lat
    if args.lon:
        config.anchor_lon = args.lon
    if args.floor_pitch:
        config.floor_pitch_m = args.floor_pitch
    if args.room_height:
        config.room_clear_height_m = args.room_height
    if args.pdf:
        config.floor_plan_source = args.pdf

    log.info(
        "Config: id=%s  name=%s  floors=%d  pitch=%.1fm  anchor=(%.6f, %.6f)",
        config.building_id, config.building_name, config.total_floors,
        config.floor_pitch_m, config.anchor_lat, config.anchor_lon,
    )

    # ---- Step 2: Run cadastral engine --------------------------------------
    log.info("--- Step 2: Running 3D cadastral engine ---")
    from backend.services.cadastral_engine import run_cadastral_pipeline

    result = run_cadastral_pipeline(
        config=config,
        persist_db=True,
        output_csv_dir="data",
        override_base_units=override_units,
    )

    # ---- Step 3: Summary ---------------------------------------------------
    print("\n" + "=" * 65)
    print(f"  3D ULPIN INGESTION COMPLETE")
    print("=" * 65)
    print(f"  Building   : {result['building_name']}  ({result['building_id']})")
    print(f"  Method     : {result['extraction_method'].upper()}")
    print(f"  Total 3D parcels  : {result['total_units']}")
    print(f"  Floors stacked    : {result['total_floors']}")
    print(f"  Max elevation     : {result['max_elevation_m']} m")
    print(f"  Total carpet area : {result['total_carpet_area_sqm']:,.1f} m^2")
    print(f"  Total airspace    : {result['total_volume_cbm']:,.1f} m^3")
    topo = result["topology_validation"]
    if topo["passed"]:
        print(f"  Topology          : PASS  (0 collisions, 0 duplicate ULPINs)")
    else:
        print(f"  Topology          : FAIL  ({topo['collision_count']} collisions, "
              f"{len(topo['duplicate_errors'])} duplicates)")
    print(f"  Output CSV        : {result['output_csv']}")
    print(f"  Sample ULPIN      : {result['sample_ulpin']}")
    print("=" * 65)

    # ---- Step 4: Visualise -------------------------------------------------
    if not args.no_viz:
        log.info("--- Step 3: Generating 3D Plotly visualisation ---")
        _run_visualizer(result["output_csv"], result["building_id"])

    return result


def _run_visualizer(csv_path: str, building_id: str):
    """
    Call visualize_3d.py, dynamically patching the CSV path so we
    don't have to hard-code HSTL01 paths in that script.
    """
    import importlib.util, types

    # Inject the correct CSV file into the visualizer's module globals
    spec = importlib.util.spec_from_file_location("visualize_3d", "visualize_3d.py")
    mod  = importlib.util.module_from_spec(spec)
    mod.FINAL_DATA_FILE = csv_path
    mod.OUTPUT_HTML     = f"frontend/{building_id.lower()}_3d_twin.html"

    try:
        spec.loader.exec_module(mod)
        mod.main()
        print(f"\n  3D twin HTML -> frontend/{building_id.lower()}_3d_twin.html")
        print("  Open that file in a browser to explore the interactive model.")
    except Exception as exc:
        log.warning("Visualizer failed: %s", exc)
        log.info("You can generate manually: python visualize_3d.py")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Universal Floor Plan -> 3D ULPIN ingestion pipeline.\n"
            "Supports ResPlan .pkl, pre-extracted JSON, vector PDFs, "
            "and existing building configs."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Source options (mutually exclusive groups)
    src_group = parser.add_argument_group("Input source (choose one)")
    src_group.add_argument(
        "--source",
        help="Path to ResPlan.pkl or .json dataset file.",
    )
    src_group.add_argument(
        "--plan-index", type=int, default=0, metavar="N",
        help="Zero-based plan index within the ResPlan dataset (default: 0).",
    )
    src_group.add_argument(
        "--base-units",
        help="Path to a pre-extracted base_units JSON (from parse_resplan.py).",
    )
    src_group.add_argument(
        "--pdf",
        help="Path to a vector CAD PDF floor plan.",
    )
    src_group.add_argument(
        "--config", "-c",
        help="Path to a per-building JSON config file.",
    )
    src_group.add_argument(
        "--building", "-b",
        help="Well-known building ID to load from config/buildings/ (e.g. HSTL01).",
    )

    # Building metadata
    meta_group = parser.add_argument_group("Building metadata")
    meta_group.add_argument("--building-id",   default=None, help="Building identifier (e.g. RESPLAN_0001).")
    meta_group.add_argument("--building-name", default=None, help="Human-readable building name.")
    meta_group.add_argument("--category",      default=None, help="Building category (default: Residential / Multi-Storey).")
    meta_group.add_argument("--description",   default=None, help="Short description.")

    # Physical parameters
    phys_group = parser.add_argument_group("Physical parameters")
    phys_group.add_argument("--floors",       type=int,   default=None, help="Number of floors to stack (default: 1).")
    phys_group.add_argument("--lat",          type=float, default=None, help="Anchor latitude of building origin.")
    phys_group.add_argument("--lon",          type=float, default=None, help="Anchor longitude of building origin.")
    phys_group.add_argument("--floor-pitch",  type=float, default=None, help="Floor-to-floor height in metres (default: 3.0).")
    phys_group.add_argument("--room-height",  type=float, default=None, help="Clear room height in metres (default: 2.6).")
    phys_group.add_argument("--min-area",     type=float, default=0.5,  help="Min polygon area in m^2 (ResPlan only, default: 0.5).")

    # Output options
    out_group = parser.add_argument_group("Output options")
    out_group.add_argument(
        "--save-base-units", default=None, metavar="PATH",
        help="If set, save the extracted base_units to this JSON path (useful for debugging).",
    )
    out_group.add_argument(
        "--no-viz", action="store_true",
        help="Skip the Plotly 3D visualisation step.",
    )

    args = parser.parse_args()

    # Basic validation
    sources = [bool(args.source), bool(args.base_units), bool(args.pdf),
               bool(args.config), bool(args.building)]
    if sum(sources) == 0:
        parser.error(
            "Provide one of: --source, --base-units, --pdf, --config, or --building"
        )

    run_ingestion(args)


if __name__ == "__main__":
    main()
