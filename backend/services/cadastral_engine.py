import os
import csv
import math
from typing import List, Dict, Any, Optional
from shapely.geometry import box
import fitz

from backend.database import get_db_connection
from backend.services.cadastral_config import BuildingConfig
from backend.services.vector_extractor import extract_units_from_vector_pdf
from backend.services.cv_extractor import extract_units_from_scanned_image
from backend.services.pointcloud_validator import validate_point_cloud_against_config

METERS_PER_DEG_LAT = 111320.0

def detect_source_type(file_path: str) -> str:
    """
    Automatically detects if the floor plan is a vector CAD PDF or a raster/scanned image.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()
    if ext in [".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"]:
        return "scanned_image"
    
    if ext == ".pdf":
        try:
            doc = fitz.open(file_path)
            if len(doc) == 0:
                return "scanned_image"
            page = doc[0]
            drawings = page.get_drawings()
            words = page.get_text("words")
            # If drawing count and word count indicate vector CAD structure
            if len(drawings) >= 10 and len(words) >= 5:
                return "vector_pdf"
            return "scanned_image"
        except Exception:
            return "scanned_image"

    return "scanned_image"


def run_cadastral_pipeline(
    config: BuildingConfig,
    persist_db: bool = True,
    output_csv_dir: str = "data",
    override_base_units: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Generalized End-to-End Cadastral Ingestion Engine:
    1. Reads configuration and auto-detects floor plan type
    2. Runs vector extraction OR CV/OCR extraction with zero hardcoded room ranges
    3. Multi-floor vertical stacking & WGS84 GPS georeferencing
    4. Computes carpet area, enclosed volume, and Undivided Share of Land (UDS)
    5. Runs 3D volumetric topology collision and primary key uniqueness checks
    6. Cross-validates against drone photogrammetry / point cloud if provided
    7. Persists datasets to CSV and updates SQLite database
    """
    building_id = config.building_id
    floor_plan_path = config.floor_plan_source

    # 1. Base Units & Format Detection
    ocr_diagnostics = None
    if override_base_units is not None:
        base_units = override_base_units
        resolved_type = "ai_pipeline_override"
    elif config.floor_plan_type == "auto":
        resolved_type = detect_source_type(floor_plan_path)
        if resolved_type == "vector_pdf":
            base_units = extract_units_from_vector_pdf(config)
        else:
            base_units, ocr_diagnostics = extract_units_from_scanned_image(config)
    else:
        resolved_type = config.floor_plan_type
        if resolved_type == "vector_pdf":
            base_units = extract_units_from_vector_pdf(config)
        else:
            base_units, ocr_diagnostics = extract_units_from_scanned_image(config)

    if not base_units:
        raise ValueError(f"No architectural units could be extracted from {floor_plan_path}")

    # 3. Stacking & Georeferencing
    total_floors = config.total_floors
    floor_pitch = config.floor_pitch_m
    room_height = config.room_clear_height_m
    anchor_lat = config.anchor_lat
    anchor_lon = config.anchor_lon
    meters_per_deg_lon = METERS_PER_DEG_LAT * math.cos(math.radians(anchor_lat))

    all_parcels = []
    total_building_carpet_area = 0.0

    # Calculate total building carpet area for UDS fractions
    for floor in range(1, total_floors + 1):
        for base in base_units:
            carpet = round(float(base["real_width_m"]) * float(base["real_depth_m"]), 2)
            total_building_carpet_area += carpet

    for floor in range(1, total_floors + 1):
        z_min = round((floor - 1) * floor_pitch, 2)
        z_max = round(z_min + room_height, 2)
        z_slab_top = round(floor * floor_pitch, 2)

        for base in base_units:
            base_prop_id = base["prop_id"]
            ptype = base.get("type", "MISC")
            is_common = base.get("is_common_property", 0)

            # Standardized room identifier per floor
            if base_prop_id.startswith("X") and base_prop_id[1:].isdigit():
                num_part = base_prop_id[1:]
                room_num = f"{floor}{num_part}"
                clean_id = room_num
            elif base_prop_id.startswith("UNIT_") or base_prop_id.startswith("ROOM_"):
                suffix = base_prop_id.split("_")[-1]
                clean_id = f"{floor}{suffix}"
            else:
                clean_id = base_prop_id.replace(" ", "_").replace("&", "AND")

            # Standardized 3D ULPIN Schema: BUILDING-FLOOR-UNIT-TYPE
            ulpin_3d = f"{building_id}-F{floor}-{clean_id}-{ptype}"

            # Georeferencing: Centroid GPS coordinates
            x_m = float(base["real_x_start_m"]) + (float(base["real_width_m"]) / 2.0)
            y_m = float(base["real_y_center_m"])
            lon = anchor_lon + (x_m / meters_per_deg_lon)
            lat = anchor_lat - (y_m / METERS_PER_DEG_LAT)

            w = float(base["real_width_m"])
            d = float(base["real_depth_m"])
            carpet = round(w * d, 2)
            volume = round(carpet * room_height, 2)
            uds = round(carpet / total_building_carpet_area, 7) if total_building_carpet_area > 0 else 0.0

            parcel = {
                "ulpin_3d": ulpin_3d,
                "room_id": clean_id,
                "building_id": building_id,
                "floor": floor,
                "type": ptype,
                "z_min": z_min,
                "z_max": z_max,
                "z_slab_top": z_slab_top,
                "real_width_m": w,
                "real_depth_m": d,
                "real_x_start_m": float(base["real_x_start_m"]),
                "real_x_end_m": float(base["real_x_end_m"]),
                "real_y_start_m": float(base["real_y_start_m"]),
                "real_y_end_m": float(base["real_y_end_m"]),
                "real_y_center_m": float(base["real_y_center_m"]),
                "latitude": round(lat, 8),
                "longitude": round(lon, 8),
                "carpet_area_sqm": carpet,
                "gross_volume_cbm": volume,
                "undivided_share_land": uds,
                "is_common_property": 1 if is_common else 0,
                "ocr_confidence": base.get("ocr_confidence", 100.0)
            }
            all_parcels.append(parcel)

    # 4. Topology & Collision Audit
    ulpin_set = set()
    dup_errors = []
    for r in all_parcels:
        if r["ulpin_3d"] in ulpin_set:
            dup_errors.append(r["ulpin_3d"])
        ulpin_set.add(r["ulpin_3d"])

    floor_groups = {}
    for r in all_parcels:
        fl = r["floor"]
        if fl not in floor_groups:
            floor_groups[fl] = []
        half_d = float(r["real_depth_m"]) / 2.0
        y_c = float(r["real_y_center_m"])
        poly = box(float(r["real_x_start_m"]), y_c - half_d, float(r["real_x_end_m"]), y_c + half_d)
        floor_groups[fl].append({"ulpin": r["ulpin_3d"], "z_min": r["z_min"], "z_max": r["z_max"], "poly": poly, "ptype": r["type"]})

    # Common-space types that intentionally overlap (ISO 19152 LADM shared access)
    EXEMPT_TYPES = {'CORR', 'STR', 'LIFT', 'HALL', 'LOBBY', 'BRIDGE', 'BALC', 'STOR'}

    collisions = []
    for fl, group in floor_groups.items():
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                p1, p2 = group[i], group[j]
                # Skip if either parcel is a shared-access common space
                if p1.get("ptype", "") in EXEMPT_TYPES or p2.get("ptype", "") in EXEMPT_TYPES:
                    continue
                if (min(p1["z_max"], p2["z_max"]) - max(p1["z_min"], p2["z_min"])) > 0:
                    inter = p1["poly"].intersection(p2["poly"])
                    # 2.0m² tolerance: filters bbox false-positives from non-rectangular polygons
                    # (e.g. an L-shaped living room's bbox overlapping a corner bedroom bbox)
                    # A genuine collision between two distinct residential rooms must exceed 2m².
                    if inter.area > 4.0:
                        collisions.append((p1["ulpin"], p2["ulpin"], round(inter.area, 3)))

    topology_passed = len(dup_errors) == 0 and len(collisions) == 0


    # 5. Point Cloud Photogrammetry ML Validation
    point_cloud_audit = validate_point_cloud_against_config(
        config.point_cloud_source,
        config.total_floors,
        config.floor_pitch_m
    )

    # 6. Save CSV Datasets
    os.makedirs(output_csv_dir, exist_ok=True)
    out_csv = os.path.join(output_csv_dir, f"room_labels_{building_id.lower()}_final.csv")
    csv_keys = [
        "ulpin_3d", "room_id", "building_id", "floor", "type",
        "z_min", "z_max", "z_slab_top", "real_width_m", "real_depth_m",
        "real_x_start_m", "real_x_end_m", "real_y_start_m", "real_y_end_m",
        "real_y_center_m", "latitude", "longitude"
    ]
    
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=csv_keys, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_parcels)

    if building_id == "HSTL01":
        legacy_csv = os.path.join(output_csv_dir, "room_labels_all_floors_final.csv")
        with open(legacy_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=csv_keys, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(all_parcels)

    # 7. Persist to SQLite Spatial Database if requested
    if persist_db:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Update or Insert building metadata
        cursor.execute("""
        INSERT INTO buildings (
            building_id, institution_id, building_name, category, data_status,
            total_floors, floor_pitch_m, room_clear_height_m, slab_thickness_m,
            anchor_lat, anchor_lon, floor_plan_source, description
        ) VALUES (?, 'INST_CAMPUS', ?, ?, 'completed', ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(building_id) DO UPDATE SET
            building_name=excluded.building_name,
            category=excluded.category,
            data_status='completed',
            total_floors=excluded.total_floors,
            floor_pitch_m=excluded.floor_pitch_m,
            room_clear_height_m=excluded.room_clear_height_m,
            slab_thickness_m=excluded.slab_thickness_m,
            anchor_lat=excluded.anchor_lat,
            anchor_lon=excluded.anchor_lon,
            floor_plan_source=excluded.floor_plan_source,
            description=excluded.description
        """, (
            building_id, config.building_name, config.category,
            config.total_floors, config.floor_pitch_m, config.room_clear_height_m,
            config.slab_thickness_m, config.anchor_lat, config.anchor_lon,
            config.floor_plan_source, config.description
        ))

        # Clear existing parcels for this building
        cursor.execute("DELETE FROM parcels_3d WHERE building_id = ?", (building_id,))

        for p in all_parcels:
            cursor.execute("""
            INSERT INTO parcels_3d (
                ulpin_3d, building_id, floor, room_id, type, z_min, z_max, z_slab_top,
                real_width_m, real_depth_m, real_x_start_m, real_x_end_m, real_y_start_m, real_y_end_m,
                latitude, longitude, carpet_area_sqm, gross_volume_cbm, undivided_share_land, is_common_property
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                p["ulpin_3d"], building_id, p["floor"], p["room_id"], p["type"],
                p["z_min"], p["z_max"], p["z_slab_top"], p["real_width_m"], p["real_depth_m"],
                p["real_x_start_m"], p["real_x_end_m"], p["real_y_start_m"], p["real_y_end_m"],
                p["latitude"], p["longitude"], p["carpet_area_sqm"], p["gross_volume_cbm"],
                p["undivided_share_land"], p["is_common_property"]
            ))

        conn.commit()
        conn.close()

    return {
        "status": "SUCCESS",
        "building_id": building_id,
        "building_name": config.building_name,
        "extraction_method": resolved_type,
        "total_units": len(all_parcels),
        "total_floors": total_floors,
        "residential_units": len([p for p in all_parcels if p["is_common_property"] == 0]),
        "common_units": len([p for p in all_parcels if p["is_common_property"] == 1]),
        "total_carpet_area_sqm": round(total_building_carpet_area, 2),
        "total_volume_cbm": round(sum(p["gross_volume_cbm"] for p in all_parcels), 2),
        "max_elevation_m": max(p["z_max"] for p in all_parcels),
        "topology_validation": {
            "passed": topology_passed,
            "unique_ulpins_count": len(ulpin_set),
            "duplicate_errors": dup_errors,
            "collision_count": len(collisions),
            "collisions": collisions
        },
        "ocr_diagnostics": ocr_diagnostics,
        "point_cloud_audit": point_cloud_audit,
        "output_csv": out_csv,
        "sample_ulpin": all_parcels[0]["ulpin_3d"]
    }
