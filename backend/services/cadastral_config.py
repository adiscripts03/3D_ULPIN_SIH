import os
import json
import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class CadYBand(BaseModel):
    max_cad_y: float
    y_start_m: float
    y_end_m: float

class YBounds(BaseModel):
    y_start_m: float
    y_end_m: float

class RoomTypeRule(BaseModel):
    rule_id: Optional[str] = None
    label_pattern: Optional[str] = None
    shape_condition: Optional[str] = None
    type: str
    is_common: Optional[bool] = None
    depth_m: Optional[float] = None
    prop_id_override: Optional[str] = None
    prop_id_prefix: Optional[str] = None
    y_bounds: Optional[YBounds] = None
    cad_y_bands: Optional[List[CadYBand]] = None

class BuildingConfig(BaseModel):
    building_id: str
    building_name: str
    category: Optional[str] = "Institutional / Multi-Storey"
    description: Optional[str] = ""
    floor_plan_source: str = "data/floor_plan.pdf"
    floor_plan_type: str = "auto"  # "auto", "vector_pdf", "scanned_image"
    anchor_lat: float = 20.9495556
    anchor_lon: float = 79.0294722
    total_floors: int = 1
    floor_pitch_m: float = 3.4
    room_clear_height_m: float = 2.9
    slab_thickness_m: float = 0.5
    scale_x: float = 0.1362088535754824
    scale_y: Optional[float] = None
    x_offset_cad: float = 0.0
    y_offset_cad: float = 0.0
    flip_horizontal: bool = False
    flip_vertical: bool = False
    point_cloud_source: Optional[str] = None
    room_type_rules: List[RoomTypeRule] = Field(default_factory=list)

    @classmethod
    def from_json_file(cls, filepath: str) -> "BuildingConfig":
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Building config file not found: {filepath}")
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(**data)

    @classmethod
    def load_by_building_id(cls, building_id: str, config_dir: str = "config/buildings") -> "BuildingConfig":
        # Check in config/buildings/<building_id>.json
        target_path = os.path.join(config_dir, f"{building_id}.json")
        if os.path.exists(target_path):
            return cls.from_json_file(target_path)
        
        # Check lowercase
        target_path_lower = os.path.join(config_dir, f"{building_id.lower()}.json")
        if os.path.exists(target_path_lower):
            return cls.from_json_file(target_path_lower)
            
        raise FileNotFoundError(f"No config file found for building ID: '{building_id}' in {config_dir}")


class RuleEngine:
    """
    Evaluates data-driven rules against detected architectural units
    without any hardcoded building logic in Python code.
    """
    def __init__(self, rules: List[RoomTypeRule]):
        self.rules = rules
        self.prefix_counters: Dict[str, int] = {}

    def reset_counters(self):
        self.prefix_counters.clear()

    def evaluate(self, label_text: str, rect_w: float, rect_h: float, cy: float, cad_y0: float = 0.0, cad_y1: float = 0.0) -> Optional[Dict[str, Any]]:
        clean_label = label_text.strip() if label_text else ""
        
        for rule in self.rules:
            matched = False
            
            # 1. Match label pattern if specified
            if rule.label_pattern:
                try:
                    if re.search(rule.label_pattern, clean_label, re.IGNORECASE):
                        matched = True
                except re.error:
                    pass
            elif rule.shape_condition:
                # 2. Match shape condition (e.g. "w > 200", "h > 80")
                cond = rule.shape_condition.strip()
                ctx = {"w": rect_w, "h": rect_h, "cy": cy, "area": rect_w * rect_h}
                try:
                    # Safe evaluated comparison
                    matched = bool(eval(cond, {"__builtins__": None}, ctx))
                except Exception:
                    matched = False
            else:
                # Catch-all rule
                matched = True

            if matched:
                # Determine prop_id
                if rule.prop_id_override:
                    prop_id = rule.prop_id_override
                elif rule.prop_id_prefix:
                    count = self.prefix_counters.get(rule.prop_id_prefix, 1)
                    prop_id = f"{rule.prop_id_prefix}{count}"
                    self.prefix_counters[rule.prop_id_prefix] = count + 1
                else:
                    prop_id = clean_label if clean_label else f"UNIT_{len(self.prefix_counters) + 1}"

                # Determine y coordinates / depth
                ry0, ry1 = None, None
                if rule.y_bounds:
                    ry0 = rule.y_bounds.y_start_m
                    ry1 = rule.y_bounds.y_end_m
                elif rule.cad_y_bands:
                    for band in rule.cad_y_bands:
                        if cy < band.max_cad_y:
                            ry0 = band.y_start_m
                            ry1 = band.y_end_m
                            break
                    if ry0 is None and rule.cad_y_bands:
                        ry0 = rule.cad_y_bands[-1].y_start_m
                        ry1 = rule.cad_y_bands[-1].y_end_m

                # Determine is_common
                is_common = rule.is_common
                if is_common is None:
                    is_common = rule.type in ["WASH", "STR", "LIFT", "CORR", "BRIDGE", "HALL", "UTIL", "CONF", "LOBBY"]

                return {
                    "rule_id": rule.rule_id,
                    "type": rule.type,
                    "prop_id": prop_id,
                    "is_common": is_common,
                    "depth_m": rule.depth_m,
                    "ry0": ry0,
                    "ry1": ry1
                }

        return None
