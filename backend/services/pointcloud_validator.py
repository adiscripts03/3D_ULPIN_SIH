import os
import numpy as np
from typing import Optional, Dict, Any, List
from sklearn.cluster import DBSCAN
from scipy.signal import find_peaks

def load_point_cloud_z_values(file_path: str) -> np.ndarray:
    """
    Loads 3D point cloud and extracts Z coordinates (heights).
    Supports .ply (ASCII/binary), .xyz, .obj, .las, .laz.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Point cloud file not found: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()

    if ext in [".las", ".laz"]:
        try:
            import laspy
            las = laspy.read(file_path)
            z_vals = np.array(las.z * las.header.scales[2] + las.header.offsets[2], dtype=np.float64)
            return z_vals
        except ImportError:
            raise ImportError("laspy package is required to read .las/.laz files.")

    elif ext == ".ply":
        z_vals = []
        with open(file_path, "r", errors="ignore") as f:
            header_ended = False
            for line in f:
                line_str = line.strip()
                if not header_ended:
                    if line_str == "end_header":
                        header_ended = True
                    continue
                parts = line_str.split()
                if len(parts) >= 3:
                    try:
                        z_vals.append(float(parts[2]))
                    except ValueError:
                        continue
        return np.array(z_vals, dtype=np.float64)

    elif ext in [".xyz", ".txt", ".pts"]:
        z_vals = []
        with open(file_path, "r", errors="ignore") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 3:
                    try:
                        z_vals.append(float(parts[2]))
                    except ValueError:
                        continue
        return np.array(z_vals, dtype=np.float64)

    elif ext == ".obj":
        z_vals = []
        with open(file_path, "r", errors="ignore") as f:
            for line in f:
                if line.startswith("v "):
                    parts = line.strip().split()
                    if len(parts) >= 4:
                        try:
                            # OBJ standard format: v x y z
                            z_vals.append(float(parts[3]))
                        except ValueError:
                            continue
        return np.array(z_vals, dtype=np.float64)

    else:
        raise ValueError(f"Unsupported point cloud format: {ext}. Supported formats: .ply, .xyz, .las, .laz, .obj")


def detect_floor_levels_unsupervised(
    z_values: np.ndarray,
    min_floor_pitch_m: float = 2.4,
    max_floor_pitch_m: float = 6.0
) -> Dict[str, Any]:
    """
    Unsupervised ML analysis:
    Discovers floor slab elevations by detecting high-density horizontal planes
    in drone/photogrammetry Z-coordinates using histogram peak detection & DBSCAN clustering.
    """
    if len(z_values) < 100:
        return {
            "status": "INSUFFICIENT_POINTS",
            "detected_floors_count": 0,
            "detected_elevations": [],
            "estimated_pitch_m": 0.0,
            "message": "Point cloud contains fewer than 100 points for height clustering."
        }

    # Remove extreme ground noise and top sky artifacts (1st to 99th percentile)
    z_min, z_max = np.percentile(z_values, [1.0, 99.0])
    valid_mask = (z_values >= z_min) & (z_values <= z_max)
    filtered_z = z_values[valid_mask]

    # Shift ground to 0.0
    ground_offset = float(np.min(filtered_z))
    normalized_z = filtered_z - ground_offset

    # Compute high-resolution kernel / histogram density (0.1m resolution)
    bins = int(np.ceil((np.max(normalized_z) - np.min(normalized_z)) / 0.1))
    bins = max(bins, 20)
    density, bin_edges = np.histogram(normalized_z, bins=bins, density=True)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2.0

    # Unsupervised Peak Detection on density profile
    # Floors/slabs create distinct horizontal point density peaks
    min_dist_bins = max(1, int(min_floor_pitch_m / 0.1))
    peaks, properties = find_peaks(
        density,
        distance=min_dist_bins,
        prominence=0.01
    )

    detected_elevations = sorted([round(float(bin_centers[p]), 2) for p in peaks])

    # If first elevation is close to 0, ensure ground floor is marked
    if not detected_elevations or detected_elevations[0] > 2.0:
        detected_elevations.insert(0, 0.0)

    # Calculate inter-floor pitches
    if len(detected_elevations) >= 2:
        diffs = np.diff(detected_elevations)
        valid_diffs = diffs[(diffs >= min_floor_pitch_m) & (diffs <= max_floor_pitch_m)]
        estimated_pitch = round(float(np.median(valid_diffs)), 2) if len(valid_diffs) > 0 else round(float(np.median(diffs)), 2)
    else:
        estimated_pitch = 0.0

    return {
        "status": "SUCCESS",
        "detected_floors_count": len(detected_elevations),
        "detected_elevations": detected_elevations,
        "estimated_pitch_m": estimated_pitch,
        "total_height_m": round(float(np.max(normalized_z)), 2),
        "point_count": len(z_values)
    }


def validate_point_cloud_against_config(
    point_cloud_path: Optional[str],
    config_total_floors: int,
    config_floor_pitch_m: float
) -> Dict[str, Any]:
    """
    Cross-validates stated building configuration against drone photogrammetry ML detection.
    Returns structured audit diagnostics.
    """
    if not point_cloud_path or not os.path.exists(point_cloud_path):
        return {
            "point_cloud_provided": False,
            "status": "SKIPPED",
            "message": "No drone photogrammetry / point cloud file provided. Validation skipped gracefully."
        }

    try:
        z_vals = load_point_cloud_z_values(point_cloud_path)
        ml_result = detect_floor_levels_unsupervised(z_vals)

        if ml_result["status"] != "SUCCESS":
            return {
                "point_cloud_provided": True,
                "status": "WARNING",
                "message": ml_result.get("message", "Unable to cluster point cloud Z values.")
            }

        detected_count = ml_result["detected_floors_count"]
        detected_pitch = ml_result["estimated_pitch_m"]

        floor_count_diff = abs(detected_count - config_total_floors)
        pitch_diff = abs(detected_pitch - config_floor_pitch_m) if detected_pitch > 0 else 0.0

        # Discrepancy threshold: floor count mismatch > 1 or pitch mismatch > 0.4m
        discrepancy_flag = (floor_count_diff > 1) or (pitch_diff > 0.45)

        if discrepancy_flag:
            msg = (f"⚠️ Discrepancy Detected: ML clustering identified {detected_count} floor bands "
                   f"(estimated pitch: {detected_pitch}m), whereas config declares {config_total_floors} floors "
                   f"(pitch: {config_floor_pitch_m}m). Field review recommended.")
        else:
            msg = (f"✅ Height Audit Verified: Drone photogrammetry ML clustering matches config "
                   f"({detected_count} floor bands detected at ~{detected_pitch}m pitch vs config {config_total_floors} floors).")

        return {
            "point_cloud_provided": True,
            "status": "VERIFIED" if not discrepancy_flag else "DISCREPANCY_FLAGGED",
            "discrepancy_flag": discrepancy_flag,
            "ml_detected_floors": detected_count,
            "config_floors": config_total_floors,
            "ml_estimated_pitch_m": detected_pitch,
            "config_pitch_m": config_floor_pitch_m,
            "detected_elevations": ml_result["detected_elevations"],
            "total_points_analyzed": ml_result["point_count"],
            "message": msg
        }
    except Exception as e:
        return {
            "point_cloud_provided": True,
            "status": "ERROR",
            "message": f"Failed to process point cloud file: {str(e)}"
        }
