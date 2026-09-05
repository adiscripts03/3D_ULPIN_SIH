"""
Video Processor Service — 3D ULPIN AI/ML Pipeline
==================================================
Processes video inputs (building walkthroughs, drone footage, plan scans)
by extracting key frames and selecting the best quality ones for analysis.

Workflow:
  1. Open video with OpenCV VideoCapture
  2. Sample frames at regular intervals
  3. Score each frame by sharpness (Laplacian variance)
  4. Detect which frames likely contain a floor plan
  5. Return the top N best frames as numpy arrays
"""

import cv2
import numpy as np
import os
import tempfile
from typing import List, Dict, Any, Tuple, Optional


def _laplacian_sharpness(frame: np.ndarray) -> float:
    """Returns the Laplacian variance — higher = sharper."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def _is_likely_floor_plan_frame(frame: np.ndarray) -> Tuple[bool, float]:
    """
    Heuristic: is this frame likely a floor plan?
    Floor plan frames tend to be:
      - Mostly white/light coloured
      - High edge density with rectangular patterns
      - Low colour saturation
    Returns (is_floor_plan, confidence_0_to_1)
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    # White ratio
    _, bin_img = cv2.threshold(gray, 210, 255, cv2.THRESH_BINARY)
    white_ratio = float(np.sum(bin_img == 255)) / (h * w)

    # Edge density
    edges = cv2.Canny(gray, 50, 150)
    edge_density = float(np.sum(edges > 0)) / (h * w)

    # Saturation
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mean_sat = float(np.mean(hsv[:, :, 1]))

    score = 0.0
    if white_ratio > 0.55:
        score += 0.4
    if edge_density > 0.015:
        score += 0.3
    if mean_sat < 30:
        score += 0.3

    return score >= 0.5, round(score, 2)


def extract_frames(
    video_path: str,
    max_frames: int = 30,
    sample_interval_s: float = 1.0,
) -> List[Dict[str, Any]]:
    """
    Extract frames from a video file at regular intervals.

    Args:
        video_path:        Path to the video file
        max_frames:        Maximum frames to extract (caps sampling)
        sample_interval_s: Seconds between sampled frames

    Returns:
        List of frame dicts with:
          - 'frame': np.ndarray (BGR image)
          - 'timestamp_s': float
          - 'frame_index': int
          - 'sharpness': float
          - 'is_floor_plan': bool
          - 'floor_plan_score': float
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration_s = total_frames / fps

    # Determine sampling interval in frames
    frame_interval = max(1, int(fps * sample_interval_s))

    frames: List[Dict[str, Any]] = []
    frame_idx = 0

    while len(frames) < max_frames:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if not ret:
            break

        sharpness = _laplacian_sharpness(frame)
        is_fp, fp_score = _is_likely_floor_plan_frame(frame)

        frames.append({
            'frame': frame,
            'frame_index': frame_idx,
            'timestamp_s': round(frame_idx / fps, 2),
            'sharpness': round(sharpness, 2),
            'is_floor_plan': is_fp,
            'floor_plan_score': fp_score,
        })

        frame_idx += frame_interval
        if frame_idx >= total_frames:
            break

    cap.release()

    return frames


def select_best_frames(
    frames: List[Dict[str, Any]],
    n: int = 5,
    prefer_floor_plans: bool = True,
) -> List[Dict[str, Any]]:
    """
    Select the N best frames by quality + floor-plan likelihood.

    Scoring formula:
      score = (sharpness_normalized × 0.4) + (floor_plan_score × 0.6)
    If prefer_floor_plans=False, only uses sharpness.
    """
    if not frames:
        return []

    max_sharpness = max(f['sharpness'] for f in frames) or 1.0

    def _score(f: Dict) -> float:
        s_norm = f['sharpness'] / max_sharpness
        if prefer_floor_plans:
            return s_norm * 0.4 + f['floor_plan_score'] * 0.6
        return s_norm

    ranked = sorted(frames, key=_score, reverse=True)
    return ranked[:n]


def process_video(
    video_path: str,
    max_sample_frames: int = 40,
    top_n: int = 5,
    prefer_floor_plans: bool = True,
) -> Dict[str, Any]:
    """
    Main entry: process a video file and return the best frames for analysis.

    Returns:
        {
          'best_frames': [{'frame': ndarray, 'timestamp_s': ..., ...}, ...],
          'total_sampled': int,
          'floor_plan_frames_found': int,
          'video_duration_s': float,
          'fps': float,
        }
    """
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()

    duration_s = round(total / fps, 2)

    # Adaptive sampling interval: aim for ~40 samples regardless of duration
    interval = max(0.5, duration_s / max_sample_frames)

    all_frames = extract_frames(video_path, max_frames=max_sample_frames, sample_interval_s=interval)
    best = select_best_frames(all_frames, n=top_n, prefer_floor_plans=prefer_floor_plans)
    fp_count = sum(1 for f in all_frames if f['is_floor_plan'])

    return {
        'best_frames': best,
        'total_sampled': len(all_frames),
        'floor_plan_frames_found': fp_count,
        'video_duration_s': duration_s,
        'fps': round(fps, 2),
        'video_path': video_path,
    }


def save_frame_to_temp(frame: np.ndarray, suffix: str = '.jpg') -> str:
    """Save a frame to a temporary file and return its path."""
    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    cv2.imwrite(tmp.name, frame)
    tmp.close()
    return tmp.name
