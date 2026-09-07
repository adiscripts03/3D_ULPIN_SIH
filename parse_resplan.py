#!/usr/bin/env python3
"""
parse_resplan.py - ResPlan Dataset -> 3D ULPIN Base-Units Extractor
===================================================================
Reads ResPlan.pkl (17,000 residential floor plans).

COORDINATE SYSTEM NOTE:
  ResPlan geometries are in pixel-space (256-wide canvas).
  Each plan carries 
et_area (m^2) and inner (total footprint polygon).
  We derive: scale = sqrt(net_area / inner.area)   [metres per pixel]
  This gives 0.00% error vs. ground-truth net_area on every plan.

Usage:
    # Summarise a plan before ingesting:
    python parse_resplan.py --pkl data/resplan/ResPlan.pkl --index 0 --summarise

    # Extract base_units JSON:
    python parse_resplan.py --pkl data/resplan/ResPlan.pkl --index 0 --out data/resplan_base_units_0.json

    # Run full pipeline directly:
    python ingest_floorplan.py --source data/resplan/ResPlan.pkl --plan-index 0 \
        --building-id RESPLAN_0000 --floors 4
"""

import os
import sys
import json
import pickle
import math
import argparse
import logging
from typing import Any, Dict, List, Optional, Tuple
from collections import Counter

from shapely.geometry import Polygon, MultiPolygon, GeometryCollection
from shapely import affinity

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# ResPlan category -> 3D ULPIN type mapping
# ---------------------------------------------------------------------------
# None = structural element / non-parcel (skip)

RESPLAN_TYPE_MAP: Dict[str, Optional[str]] = {
    "bedroom":    "BEDRM",
    "living":     "LIVRM",
    "kitchen":    "KITCH",
    "bathroom":   "WASH",
    "balcony":    "BALC",
    "stair":      "STR",
    "storage":    "STOR",
    "corridor":   "CORR",
    "hallway":    "CORR",
    "dining":     "LIVRM",
    "study":      "BEDRM",
    "garage":     "STOR",
    "laundry":    "WASH",
    "garden":     "BALC",   # open amenity space
    "parking":    "STOR",   # covered parking
    "pool":       None,     # skip (pools are not habitable parcels)
    # Structural elements - not spatial parcels
    "front_door": None,
    "door":       None,
    "window":     None,
    "wall":       None,
}

# Types that count as shared / common property
COMMON_TYPES = {"STR", "CORR", "HALL", "BALC", "LOBBY"}

# Minimum polygon area after scaling (m^2) - filter noise
MIN_AREA_SQM = 0.5


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def _extract_polygons(geom: Any) -> List[Polygon]:
    """Flatten Polygon / MultiPolygon / GeometryCollection -> list of Polygons."""
    if geom is None or (hasattr(geom, "is_empty") and geom.is_empty):
        return []
    if isinstance(geom, Polygon):
        return [geom] if not geom.is_empty else []
    if isinstance(geom, MultiPolygon):
        return [p for p in geom.geoms if not p.is_empty]
    if isinstance(geom, GeometryCollection):
        out = []
        for g in geom.geoms:
            out.extend(_extract_polygons(g))
        return out
    return []


def _normalize_plan_keys(plan: Dict[str, Any]) -> Dict[str, Any]:
    """Fix known key typos / variant spellings."""
    fixes = {
        "balacony":   "balcony",
        "livingroom": "living",
        "live":       "living",
        "bath":       "bathroom",
        "wc":         "bathroom",
        "staircase":  "stair",
        "stairs":     "stair",
        "hallway":    "corridor",
    }
    for old, new in fixes.items():
        if old in plan and new not in plan:
            plan[new] = plan.pop(old)
    return plan


def _compute_scale(plan: Dict[str, Any]) -> float:
    """
    Derive the pixel-to-metre scale factor for this plan.

    Formula: scale = sqrt(net_area_m2 / inner_poly_area_px)
    This gives 0.00% error vs. ground-truth net_area on all ResPlan entries.

    Falls back to a reasonable default (0.05 m/px ~ 5m per 100px) if
    net_area or inner is missing.
    """
    net_area = plan.get("net_area")
    inner    = plan.get("inner")

    try:
        net_area_f = float(net_area)
        if net_area_f > 0 and inner is not None and hasattr(inner, "area") and inner.area > 0:
            return math.sqrt(net_area_f / inner.area)
    except (TypeError, ValueError):
        pass

    # Fallback: estimate from the 'area' field (gross area including walls)
    area = plan.get("area")
    try:
        area_f = float(area)
        if area_f > 0 and inner is not None and hasattr(inner, "area") and inner.area > 0:
            return math.sqrt(area_f / inner.area)
    except (TypeError, ValueError):
        pass

    log.warning("Could not derive scale from plan metadata; using default 0.05 m/px")
    return 0.05


def _scale_polygon(poly: Polygon, scale: float) -> Polygon:
    """Scale a Shapely polygon by scale in both X and Y (origin = (0,0))."""
    return affinity.scale(poly, xfact=scale, yfact=scale, origin=(0, 0))


# ---------------------------------------------------------------------------
# Core extractor
# ---------------------------------------------------------------------------

def extract_base_units(
    plan: Dict[str, Any],
    min_area_sqm: float = MIN_AREA_SQM,
) -> List[Dict[str, Any]]:
    """
    Convert one ResPlan plan dict into the standardized base_units list
    expected by cadastral_engine.run_cadastral_pipeline(override_base_units=...).

    Applies per-plan pixel->metre scale derived from net_area + inner polygon.

    Each returned dict:
        label, prop_id, type, is_common_property,
        real_width_m, real_depth_m,
        real_x_start_m, real_x_end_m,
        real_y_start_m, real_y_end_m,
        real_y_center_m,
        extraction_method, ocr_confidence
    """
    plan = _normalize_plan_keys(plan)
    scale = _compute_scale(plan)
    log.info("Plan id=%s  scale=%.5f m/px  net_area=%s m^2",
             plan.get("id", "?"), scale, plan.get("net_area", "?"))

    base_units: List[Dict[str, Any]] = []
    counters: Dict[str, int] = {}

    for category, geom in plan.items():
        if category in ("graph", "inner", "outer", "land", "neighbor",
                        "id", "split", "area", "net_area", "wall_depth"):
            continue

        ulpin_type = RESPLAN_TYPE_MAP.get(category)
        if ulpin_type is None:
            continue

        raw_polygons = _extract_polygons(geom)
        if not raw_polygons:
            continue

        for raw_poly in raw_polygons:
            # Apply pixel->metre scale transform
            poly = _scale_polygon(raw_poly, scale)
            area = poly.area
            if area < min_area_sqm:
                log.debug("Skip tiny: %s  area=%.3f m^2", category, area)
                continue

            minx, miny, maxx, maxy = poly.bounds
            width_m = round(maxx - minx, 3)
            depth_m = round(maxy - miny, 3)

            if width_m < 0.1 or depth_m < 0.1:
                continue

            counters[ulpin_type] = counters.get(ulpin_type, 0) + 1
            prop_id    = f"{ulpin_type}_{counters[ulpin_type]}"
            is_common  = 1 if ulpin_type in COMMON_TYPES else 0

            base_units.append({
                "label":              f"{category.replace('_', ' ').title()} {counters[ulpin_type]}",
                "prop_id":            prop_id,
                "type":               ulpin_type,
                "is_common_property": is_common,
                "real_width_m":       width_m,
                "real_depth_m":       depth_m,
                "real_x_start_m":     round(minx, 3),
                "real_x_end_m":       round(maxx, 3),
                "real_y_start_m":     round(miny, 3),
                "real_y_end_m":       round(maxy, 3),
                "real_y_center_m":    round((miny + maxy) / 2.0, 3),
                "extraction_method":  "resplan_vector",
                "ocr_confidence":     100.0,
            })

    if not base_units:
        raise ValueError(
            f"No spatial parcels could be extracted from plan id={plan.get('id')}. "
            "Check that the plan contains bedroom, bathroom, kitchen, or living polygons."
        )

    log.info("Extracted %d base units  (types: %s)",
             len(base_units),
             ", ".join(sorted({u['type'] for u in base_units})))
    return base_units


# ---------------------------------------------------------------------------
# Dataset loaders
# ---------------------------------------------------------------------------

def load_resplan_pkl(pkl_path: str) -> List[Dict[str, Any]]:
    """Load the full ResPlan dataset from the official .pkl file."""
    if not os.path.exists(pkl_path):
        raise FileNotFoundError(f"ResPlan pickle not found: {pkl_path}")
    log.info("Loading %s ...", pkl_path)
    with open(pkl_path, "rb") as fh:
        data = pickle.load(fh)
    if isinstance(data, dict):
        data = list(data.values())
    if not isinstance(data, list):
        raise TypeError(f"Unexpected format. Got {type(data)}, expected list.")
    log.info("Loaded %d plans.", len(data))
    return data


def load_resplan_json(json_path: str) -> List[Dict[str, Any]]:
    """Load plans from a GeoJSON file (pre-converted from the pickle)."""
    from shapely.geometry import shape as shapely_shape
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"JSON not found: {json_path}")
    with open(json_path, "r", encoding="utf-8") as fh:
        raw = json.load(fh)
    if isinstance(raw, dict):
        raw = [raw]
    plans = []
    for entry in raw:
        plan = {}
        for key, val in entry.items():
            if isinstance(val, dict) and "type" in val:
                try:
                    plan[key] = shapely_shape(val)
                except Exception:
                    plan[key] = val
            else:
                plan[key] = val
        plans.append(plan)
    return plans


def get_plan(source_path: str, index: int = 0) -> Dict[str, Any]:
    """Load one plan by index from a .pkl or .json ResPlan file."""
    ext = os.path.splitext(source_path)[1].lower()
    if ext == ".pkl":
        plans = load_resplan_pkl(source_path)
    elif ext in (".json", ".geojson"):
        plans = load_resplan_json(source_path)
    else:
        raise ValueError(f"Unsupported extension '{ext}'. Use .pkl or .json.")

    if not (0 <= index < len(plans)):
        raise IndexError(f"Index {index} out of range. Dataset has {len(plans)} plans.")
    return plans[index]


def summarise_plan(plan: Dict[str, Any]) -> Dict[str, Any]:
    """Return a human-readable category summary for one plan, with real-world m^2."""
    plan = _normalize_plan_keys(plan)
    scale = _compute_scale(plan)
    summary: Dict[str, Any] = {
        "__meta__": {
            "id": plan.get("id"),
            "net_area_m2": plan.get("net_area"),
            "scale_m_per_px": round(scale, 5),
        }
    }
    for key, geom in plan.items():
        if key in ("graph", "id", "area", "net_area", "wall_depth", "neighbor"):
            continue
        polys = _extract_polygons(geom)
        if polys:
            real_area = sum(_scale_polygon(p, scale).area for p in polys)
            summary[key] = {
                "polygon_count":  len(polys),
                "total_area_sqm": round(real_area, 2),
            }
    return summary


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="ResPlan .pkl -> 3D ULPIN base-units extractor.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--pkl", "--json", dest="source", required=True,
                        help="Path to ResPlan.pkl (or .json).")
    parser.add_argument("--index", "-i", type=int, default=0,
                        help="Zero-based plan index (default: 0).")
    parser.add_argument("--out", "-o", default=None,
                        help="Output JSON path. Default: data/resplan_base_units_<i>.json")
    parser.add_argument("--min-area", type=float, default=MIN_AREA_SQM,
                        help=f"Min polygon area m^2 (default: {MIN_AREA_SQM}).")
    parser.add_argument("--summarise", "-s", action="store_true",
                        help="Print category summary and exit.")
    args = parser.parse_args()

    plan = get_plan(args.source, args.index)

    if args.summarise:
        summary = summarise_plan(plan)
        meta = summary.pop("__meta__", {})
        print(f"\n  Plan #{args.index}  (id={meta.get('id')}  "
              f"net_area={meta.get('net_area_m2')} m^2  "
              f"scale={meta.get('scale_m_per_px')} m/px)")
        print(f"  {'Category':<18} {'Polygons':>8}  {'Area (m^2)':>12}")
        print("  " + "-" * 42)
        for cat, info in sorted(summary.items()):
            ulpin = RESPLAN_TYPE_MAP.get(cat, "skip")
            flag  = "" if ulpin else "  [skip-structural]"
            print(f"  {cat:<18} {info['polygon_count']:>8}  {info['total_area_sqm']:>10.2f}{flag}")
        return

    base_units = extract_base_units(plan, min_area_sqm=args.min_area)
    out_path   = args.out or f"data/resplan_base_units_{args.index}.json"
    out_dir    = os.path.dirname(out_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(base_units, fh, indent=2)

    print(f"\n  Extracted {len(base_units)} base units -> {out_path}")
    print("\n  Room breakdown:")
    counts = Counter(u["type"] for u in base_units)
    for t, n in sorted(counts.items()):
        print(f"    {t.ljust(10)}  x{n}")
    total = sum(u['real_width_m'] * u['real_depth_m'] for u in base_units)
    print(f"\n  Total footprint (bbox): {total:.1f} m^2")
    print(f"\n  Next: python ingest_floorplan.py --source \"{args.source}\" "
          f"--plan-index {args.index} --building-id RESPLAN_{args.index:04d} --floors 4")


if __name__ == "__main__":
    main()
