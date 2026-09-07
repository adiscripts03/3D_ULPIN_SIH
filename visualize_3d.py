import csv
import json
import plotly.graph_objects as go
import os
from typing import Optional

DB_FILE = "data/occupancy_db.json"
FINAL_DATA_FILE = "data/room_labels_all_floors_final.csv" if os.path.exists("data/room_labels_all_floors_final.csv") else "data/room_labels_floor1_final.csv"
OUTPUT_HTML = "frontend/hostel_3d_twin.html"

def get_box_mesh(x0, x1, y0, y1, z0, z1, color, label, hover_text, floor_num, opacity=0.88):
    # 8 vertices of a 3D rectangular parcel
    x = [x0, x1, x1, x0, x0, x1, x1, x0]
    y = [y0, y0, y1, y1, y0, y0, y1, y1]
    z = [z0, z0, z0, z0, z1, z1, z1, z1]
    
    # 12 triangular facets to define the 6 faces of the 3D parcel box
    i = [0, 0, 4, 4, 0, 0, 3, 3, 0, 0, 1, 1]
    j = [1, 2, 5, 6, 1, 5, 2, 6, 3, 7, 2, 6]
    k = [2, 3, 6, 7, 5, 4, 6, 7, 7, 4, 6, 5]
    
    return go.Mesh3d(
        x=x, y=y, z=z,
        i=i, j=j, k=k,
        color=color,
        opacity=opacity,
        flatshading=True,
        lighting=dict(ambient=0.7, diffuse=0.8, roughness=0.5, specular=0.2),
        name=f"F{floor_num} - {label}",
        text=hover_text,
        hoverinfo="text"
    )

def generate_3d_twin(csv_file: str, output_html: Optional[str] = None, building_title: Optional[str] = None):
    """
    Renders an interactive 3D Plotly digital twin for ANY building CSV.
    """
    if not os.path.exists(csv_file):
        raise FileNotFoundError(f"CSV file not found: {csv_file}")

    rows = []
    with open(csv_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    if not rows:
        raise ValueError(f"No parcels found in {csv_file}")

    # Load occupancy database if available
    occupancy_db = {}
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                occupancy_db = json.load(f)
        except Exception:
            occupancy_db = {}

    fig = go.Figure()

    min_x, max_x = float("inf"), float("-inf")
    min_y, max_y = float("inf"), float("-inf")
    min_z, max_z = float("inf"), float("-inf")

    floors = sorted(list(set(int(r["floor"]) for r in rows)))
    trace_floor_map = []

    # Detect building identity
    first_row = rows[0]
    bldg_id = first_row.get("building_id", "")
    if not bldg_id and "ulpin_3d" in first_row:
        bldg_id = first_row["ulpin_3d"].split("-")[0]
    
    is_hostel = (bldg_id.upper() == "HSTL01")

    # Vibrant, standard spatial classification color mapping
    COLOR_MAP = {
        "BEDRM":  {"color": "#4CAF50", "name": "Bedroom", "opacity": 0.88},
        "LIVRM":  {"color": "#FF7043", "name": "Living / Dining", "opacity": 0.88},
        "KITCH":  {"color": "#FFA726", "name": "Kitchen", "opacity": 0.88},
        "WASH":   {"color": "#00BCD4", "name": "Bathroom / Washroom", "opacity": 0.88},
        "BALC":   {"color": "#AB47BC", "name": "Balcony / Terrace", "opacity": 0.80},
        "STOR":   {"color": "#8D6E63", "name": "Storage / Utility", "opacity": 0.85},
        "STR":    {"color": "#78909C", "name": "Staircase", "opacity": 0.85},
        "LIFT":   {"color": "#607D8B", "name": "Elevator / Lift", "opacity": 0.85},
        "HALL":   {"color": "#FFB300", "name": "Common Hall", "opacity": 0.80},
        "CORR":   {"color": "#42A5F5", "name": "Corridor", "opacity": 0.65},
        "BRIDGE": {"color": "#9C27B0", "name": "Connecting Bridge", "opacity": 0.85},
        "OFFICE": {"color": "#2196F3", "name": "Office", "opacity": 0.88},
        "PARK":   {"color": "#546E7A", "name": "Parking", "opacity": 0.75},
    }

    for r in rows:
        ulpin = r["ulpin_3d"]
        label = r.get("room_id", ulpin)
        ptype = r.get("type", "").upper()
        floor_num = int(r["floor"])
        
        x0 = float(r["real_x_start_m"])
        x1 = float(r["real_x_end_m"])
        
        if "real_y_start_m" in r and "real_y_end_m" in r:
            y0 = float(r["real_y_start_m"])
            y1 = float(r["real_y_end_m"])
        else:
            y_center = float(r["real_y_center_m"])
            d = float(r["real_depth_m"])
            y0 = y_center - (d / 2.0)
            y1 = y_center + (d / 2.0)
            
        z0 = float(r["z_min"])
        z1 = float(r["z_max"])

        min_x, max_x = min(min_x, x0), max(max_x, x1)
        min_y, max_y = min(min_y, y0), max(max_y, y1)
        min_z, max_z = min(min_z, z0), max(max_z, z1)

        area_sqm = round((x1 - x0) * (y1 - y0), 1)
        lat = r.get("latitude", "N/A")
        lon = r.get("longitude", "N/A")

        # Determine Color & Status
        matched_type = None
        for k in COLOR_MAP:
            if k in ptype or k in ulpin:
                matched_type = k
                break

        if matched_type:
            cfg = COLOR_MAP[matched_type]
            color = cfg["color"]
            status = cfg["name"]
            opacity = cfg["opacity"]
        elif is_hostel:
            cap = 4 if "4S" in ulpin else 2
            occupants = occupancy_db.get(ulpin, [])
            occ_count = len(occupants)
            if occ_count == 0:
                color = "#2ECC71"
                status = f"Vacant (0/{cap})"
            elif occ_count < cap:
                color = "#F39C12"
                status = f"Partial ({occ_count}/{cap})"
            else:
                color = "#E74C3C"
                status = f"Full ({occ_count}/{cap})"
            opacity = 0.88
            if occupants:
                status += f"<br>Occupants: {', '.join(occupants)}"
        else:
            color = "#4CAF50"
            status = ptype or "Habitable Stratum Unit"
            opacity = 0.88

        hover_text = (
            f"<b>Floor {floor_num} | Unit: {label}</b><br>"
            f"<b>3D ULPIN:</b> {ulpin}<br>"
            f"<b>Type:</b> {ptype} ({status})<br>"
            f"<b>Dimensions:</b> {round(x1-x0,2)}m × {round(y1-y0,2)}m × {round(z1-z0,2)}m<br>"
            f"<b>Area:</b> {area_sqm} m²<br>"
            f"<b>Coordinates:</b> Lat {lat}, Lon {lon}<br>"
            f"<b>Elevation:</b> {z0}m – {z1}m"
        )
        
        mesh = get_box_mesh(x0, x1, y0, y1, z0, z1, color, label, hover_text, floor_num, opacity)
        fig.add_trace(mesh)
        trace_floor_map.append(floor_num)

    # Floor filter buttons
    buttons = [
        dict(
            label=f"🏢 All {len(floors)} Floors (Full Building)",
            method="update",
            args=[{"visible": [True] * len(trace_floor_map)}]
        )
    ]
    for fl in floors:
        vis = [
            (trace_floor_map[idx] == fl or trace_floor_map[idx] == 0)
            for idx in range(len(trace_floor_map))
        ]
        buttons.append(dict(
            label=f"Level {fl} (Floor {fl})",
            method="update",
            args=[{"visible": vis}]
        ))

    # Add hostel facade markers ONLY for the hostel
    if is_hostel:
        mid_x = (min_x + max_x) / 2.0
        fig.add_trace(go.Scatter3d(
            x=[mid_x], y=[-4.0], z=[0.0],
            mode="text", text=["<b>▲ FRONT FACADE ▲</b>"],
            textposition="top center", textfont=dict(size=14, color="#1565C0"),
            hoverinfo="none", name="Front Facade"
        ))
        trace_floor_map.append(0)

    # Dynamic Title
    display_title = building_title or (
        f"<b>3D ULPIN Digital Twin — {bldg_id}</b><br>"
        f"<sup>{len(rows)} Volumetric 3D Parcels across {len(floors)} Floors (Height: {max_z:.1f}m)</sup>"
    )

    fig.update_layout(
        title=dict(
            text=display_title,
            x=0.04,
            y=0.96,
            font=dict(size=18, family="Arial, sans-serif")
        ),
        updatemenus=[
            dict(
                type="dropdown",
                direction="down",
                x=0.04,
                y=0.88,
                showactive=True,
                active=0,
                buttons=buttons,
                bgcolor="#FFFFFF",
                bordercolor="#B0BEC5",
                font=dict(size=12, color="#263238")
            )
        ],
        scene=dict(
            xaxis=dict(title="X (Meters)", backgroundcolor="#F8F9FA", gridcolor="#E0E0E0"),
            yaxis=dict(title="Y (Meters)", backgroundcolor="#F8F9FA", gridcolor="#E0E0E0"),
            zaxis=dict(title="Elevation Z (Meters)", backgroundcolor="#ECEFF1", gridcolor="#CFD8DC"),
            aspectmode="data",
            camera=dict(
                eye=dict(x=1.65, y=-1.65, z=1.2),
                center=dict(x=0.0, y=0.0, z=0.0),
                up=dict(x=0.0, y=0.0, z=1.0)
            )
        ),
        margin=dict(l=0, r=0, b=0, t=75),
        showlegend=False
    )

    out_path = output_html or OUTPUT_HTML
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fig.write_html(out_path)
    print(f"[OK] 3D Digital Twin generated ({len(rows)} units) -> {out_path}")
    return out_path

def main():
    generate_3d_twin(FINAL_DATA_FILE, OUTPUT_HTML)

if __name__ == "__main__":
    main()
