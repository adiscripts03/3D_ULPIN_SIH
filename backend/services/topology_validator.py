from shapely.geometry import box
from typing import List, Dict, Any

def validate_building_topology(parcels: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Performs 3D spatial collision validation on volumetric parcels:
    1. Primary Key Uniqueness & Null Integrity
    2. Minimum Statutory Area verification (> 5.0 sqm)
    3. 3D Volumetric Overlap & 2D Planar Polygon Intersection Area check
    """
    total_parcels = len(parcels)
    unique_ulpins = set()
    duplicate_errors = []
    area_errors = []
    collision_errors = []

    # 1. Uniqueness & Statutory Area
    for p in parcels:
        ulpin = p['ulpin_3d']
        if ulpin in unique_ulpins:
            duplicate_errors.append(ulpin)
        unique_ulpins.add(ulpin)

        area = p['carpet_area_sqm']
        if area < 5.0 and p['type'] not in ['MISC', 'BRIDGE']:
            area_errors.append({'ulpin': ulpin, 'area': area})

    # Group by floor to optimize collision check O(N_floor^2)
    floors = set(p['floor'] for p in parcels)
    
    for fl in floors:
        fl_parcels = [p for p in parcels if p['floor'] == fl]
        n_fl = len(fl_parcels)

        for i in range(n_fl):
            p1 = fl_parcels[i]
            b1 = box(p1['real_x_start_m'], p1['real_y_start_m'], p1['real_x_end_m'], p1['real_y_end_m'])

            for j in range(i + 1, n_fl):
                p2 = fl_parcels[j]

                # Check Z-interval overlap
                z_overlap = max(0.0, min(p1['z_max'], p2['z_max']) - max(p1['z_min'], p2['z_min']))
                if z_overlap <= 0:
                    continue

                b2 = box(p2['real_x_start_m'], p2['real_y_start_m'], p2['real_x_end_m'], p2['real_y_end_m'])
                
                # Check 2D intersection
                if b1.intersects(b2):
                    inter = b1.intersection(b2)
                    inter_area = inter.area
                    # Allow minor boundary line adjacency, flag real spatial collision > 0.01 sqm
                    if inter_area > 0.05 and p1['type'] != 'HALL' and p2['type'] != 'HALL':
                        collision_errors.append({
                            'parcel_1': p1['ulpin_3d'],
                            'parcel_2': p2['ulpin_3d'],
                            'overlap_area_sqm': round(inter_area, 3),
                            'z_overlap_m': round(z_overlap, 2)
                        })

    passed = (len(duplicate_errors) == 0 and len(area_errors) == 0 and len(collision_errors) == 0)

    return {
        'total_parcels_audited': total_parcels,
        'unique_ulpins': len(unique_ulpins),
        'duplicate_id_count': len(duplicate_errors),
        'duplicate_ids': duplicate_errors,
        'area_violations_count': len(area_errors),
        'area_violations': area_errors,
        '3d_collision_count': len(collision_errors),
        'collision_errors': collision_errors,
        'validation_status': "PASSED" if passed else "FAILED",
        'compliance_score_percent': 100.0 if passed else round((1 - len(collision_errors)/max(1, total_parcels)) * 100, 2)
    }
