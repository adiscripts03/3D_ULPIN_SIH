"""
Floor Plan Synthesizer — 3D ULPIN AI/ML Pipeline
=================================================
Generates synthetic but geometrically valid floor plans from building parameters.
Used when no actual floor plan image is available (text-only / exterior photo inputs).

Layout Strategy — Double-Loaded Corridor:
   ╔═══════╦═══════╦══════╦═══════╗
   ║ R-101 ║ R-102 ║ ...  ║ WASH  ║  ← North wing rooms
   ╠═══════╩═══════╩══════╩═══════╣
   ║    C O R R I D O R          ║  ← Central corridor
   ╠═══════╦═══════╦══════╦═══════╣
   ║ R-104 ║ R-105 ║ ...  ║ WASH  ║  ← South wing rooms
   ╚═══════╩═══════╩══════╩═══════╝
  [STR]                        [STR]  ← Stairs at building ends
"""

import math
from typing import Dict, Any, List, Tuple, Optional

# ── Per-type room dimensions (width × depth in meters) ───────────────────────
ROOM_SPEC: Dict[str, Dict[str, Any]] = {
    # Hostel
    '4S':     {'w': 6.0,  'd': 5.0,  'common': False},
    '2S':     {'w': 4.5,  'd': 5.0,  'common': False},
    # Apartment
    '2BHK':   {'w': 8.5,  'd': 12.0, 'common': False},
    '3BHK':   {'w': 11.0, 'd': 14.0, 'common': False},
    '1BHK':   {'w': 6.0,  'd': 9.0,  'common': False},
    # Office
    'OFFICE': {'w': 6.0,  'd': 5.0,  'common': False},
    'CABIN':  {'w': 4.0,  'd': 4.0,  'common': False},
    # Hospital
    'WARD':   {'w': 7.0,  'd': 9.0,  'common': False},
    'ICU':    {'w': 5.0,  'd': 7.0,  'common': False},
    'OT':     {'w': 8.0,  'd': 10.0, 'common': False},
    # Hotel
    'SUITE':  {'w': 8.0,  'd': 10.0, 'common': False},
    'DBLBED': {'w': 6.0,  'd': 7.0,  'common': False},
    'TWIN':   {'w': 5.0,  'd': 7.0,  'common': False},
    # Commercial
    'SHOP':   {'w': 5.0,  'd': 6.0,  'common': False},
    'RETAIL': {'w': 8.0,  'd': 10.0, 'common': False},
    # Common spaces
    'CORR':   {'w': None, 'd': 2.0,  'common': True},
    'WASH':   {'w': 3.0,  'd': 3.0,  'common': True},
    'STR':    {'w': 3.0,  'd': 5.0,  'common': True},
    'LIFT':   {'w': 2.5,  'd': 2.5,  'common': True},
    'HALL':   {'w': 6.0,  'd': 5.0,  'common': True},
    'LOBBY':  {'w': 8.0,  'd': 5.0,  'common': True},
    'UTIL':   {'w': 2.5,  'd': 3.0,  'common': True},
    'CONF':   {'w': 7.0,  'd': 6.0,  'common': True},
    'NURSE':  {'w': 4.0,  'd': 4.0,  'common': True},
}


def _unit(prop_id: str, ptype: str,
          x0: float, x1: float, y0: float, y1: float) -> Dict[str, Any]:
    """Construct a base_unit dict for the cadastral engine."""
    w = round(x1 - x0, 2)
    d = round(y1 - y0, 2)
    spec = ROOM_SPEC.get(ptype, {'common': False})
    return {
        'label': prop_id,
        'prop_id': prop_id,
        'type': ptype,
        'is_common_property': 1 if spec['common'] else 0,
        'real_width_m': max(w, 0.5),
        'real_depth_m': max(d, 0.5),
        'real_x_start_m': round(x0, 2),
        'real_x_end_m': round(x1, 2),
        'real_y_start_m': round(y0, 2),
        'real_y_end_m': round(y1, 2),
        'real_y_center_m': round((y0 + y1) / 2, 2),
        'extraction_method': 'synthetic_generation',
        'ocr_confidence': 100.0,
    }


def synthesize_floor_plan(
    rooms_per_floor: int,
    room_types: List[str],
    building_type: str = 'hostel',
    building_width_m: Optional[float] = None,
    building_depth_m: Optional[float] = None,
    residential_ratio: float = 0.80,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Generate a synthetic double-loaded corridor floor plan.

    Args:
        rooms_per_floor:    Target total units per floor (residential + common)
        room_types:         Primary residential room types (e.g. ['4S', '2S'])
        building_type:      Building category string
        building_width_m:   Optional forced building width (auto-computed if None)
        building_depth_m:   Optional forced building depth
        residential_ratio:  Fraction of units that are residential (rest = common)

    Returns:
        base_units:  List of unit dicts for cadastral_engine.run_cadastral_pipeline
        metadata:    Dict with actual building dimensions and layout info
    """
    if not room_types:
        room_types = ['4S']

    primary_type = room_types[0]
    secondary_type = room_types[1] if len(room_types) > 1 else primary_type

    pspec = ROOM_SPEC.get(primary_type, ROOM_SPEC['4S'])
    sspec = ROOM_SPEC.get(secondary_type, pspec)

    room_w_p = pspec['w']
    room_w_s = sspec['w']
    room_d = pspec['d']          # depth (both wings same depth)

    corr_depth = ROOM_SPEC['CORR']['d']
    stair_w = ROOM_SPEC['STR']['w']
    stair_d = ROOM_SPEC['STR']['d']
    wash_w = ROOM_SPEC['WASH']['w']
    wash_d = ROOM_SPEC['WASH']['d']

    # Number of residential rooms to place
    n_res = max(2, int(rooms_per_floor * residential_ratio))
    rooms_per_side = max(1, n_res // 2)

    # Washrooms: 1 per 8 residential rooms (at least 1)
    n_wash_per_side = max(1, rooms_per_side // 8)

    base_units: List[Dict[str, Any]] = []
    x_cursor = 0.0

    # ── West stairwell ────────────────────────────────────────────────────────
    stair_y_north = 0.0
    stair_y_south = room_d + corr_depth

    base_units.append(_unit('STR_NW', 'STR', x_cursor, x_cursor + stair_w,
                            stair_y_north, stair_y_north + stair_d))
    base_units.append(_unit('STR_SW', 'STR', x_cursor, x_cursor + stair_w,
                            stair_y_south, stair_y_south + stair_d))
    x_cursor += stair_w

    # ── Rooms on each side ────────────────────────────────────────────────────
    room_counter = 1
    for i in range(rooms_per_side):
        # Alternate between primary and secondary type
        if i % 3 == 2 and secondary_type != primary_type:
            rtype, rw = secondary_type, room_w_s
        else:
            rtype, rw = primary_type, room_w_p

        x0, x1 = x_cursor, x_cursor + rw

        # North wing room
        pid_n = f'X{room_counter:02d}'
        base_units.append(_unit(pid_n, rtype, x0, x1, 0.0, room_d))
        room_counter += 1

        # South wing room
        pid_s = f'X{room_counter:02d}'
        base_units.append(_unit(pid_s, rtype, x0, x1, room_d + corr_depth,
                                 room_d + corr_depth + room_d))
        room_counter += 1

        # Insert washroom block periodically
        if (i + 1) % (rooms_per_side // max(1, n_wash_per_side)) == 0:
            wx0, wx1 = x_cursor + rw, x_cursor + rw + wash_w
            base_units.append(_unit(f'WASH_N_{room_counter}', 'WASH', wx0, wx1, 0.0, wash_d))
            base_units.append(_unit(f'WASH_S_{room_counter}', 'WASH', wx0, wx1,
                                    room_d + corr_depth, room_d + corr_depth + wash_d))
            x_cursor += rw + wash_w
        else:
            x_cursor += rw

    # ── East stairwell + lift ─────────────────────────────────────────────────
    lift_w = ROOM_SPEC['LIFT']['w']
    base_units.append(_unit('STR_NE', 'STR', x_cursor, x_cursor + stair_w,
                            stair_y_north, stair_y_north + stair_d))
    base_units.append(_unit('STR_SE', 'STR', x_cursor, x_cursor + stair_w,
                            stair_y_south, stair_y_south + stair_d))
    base_units.append(_unit('LIFT_C', 'LIFT', x_cursor, x_cursor + lift_w,
                            stair_y_north + stair_d, stair_y_north + stair_d + ROOM_SPEC['LIFT']['d']))
    x_cursor += stair_w

    # ── Central corridor (full width) ─────────────────────────────────────────
    building_width = x_cursor
    corr_id = _unit('CORR_01', 'CORR', 0.0, building_width,
                    room_d, room_d + corr_depth)
    base_units.append(corr_id)

    # ── Compute final building dimensions ─────────────────────────────────────
    actual_width = building_width_m if building_width_m else round(building_width, 2)
    actual_depth = building_depth_m if building_depth_m else round(room_d * 2 + corr_depth, 2)

    metadata = {
        'layout': 'double_loaded_corridor',
        'building_type': building_type,
        'actual_width_m': actual_width,
        'actual_depth_m': actual_depth,
        'rooms_per_side': rooms_per_side,
        'total_units_generated': len(base_units),
        'residential_units': len([u for u in base_units if not u['is_common_property']]),
        'common_units': len([u for u in base_units if u['is_common_property']]),
        'generation_method': 'double_loaded_corridor_synthesis',
    }

    return base_units, metadata
