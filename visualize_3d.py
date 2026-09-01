import csv
import json
import plotly.graph_objects as go
import os

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

def main():
    rows = []
    with open(FINAL_DATA_FILE, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    # Load live occupancy database
    occupancy_db = {}
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                occupancy_db = json.load(f)
        except Exception:
            occupancy_db = {}

    fig = go.Figure()

    # Track bounds for annotations & axis setup
    min_x, max_x = float("inf"), float("-inf")
    min_y, max_y = float("inf"), float("-inf")
    min_z, max_z = float("inf"), float("-inf")

    floors = sorted(list(set(int(r["floor"]) for r in rows)))
    trace_floor_map = [] # stores floor number for each trace

    for r in rows:
        ulpin = r["ulpin_3d"]
        label = r["room_id"]
        ptype = r.get("type", "")
        floor_num = int(r["floor"])
        
        # Real-world metric boundaries
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

        # Color-coding by spatial parcel classification & occupancy
        opacity = 0.88
        if "WASH" in ptype or "WASH" in ulpin:
            color = "#00BCD4" # Cyan
            status = "Non-Residential (Washroom)"
        elif "STR" in ptype or "LIFT" in ptype:
            color = "#78909C" # Slate Grey
            status = "Vertical Transit (Stairwell/Lift)"
        elif "HALL" in ptype or "HALL" in ulpin:
            color = "#FFB300" # Warm Amber
            status = "Common Space (Common Hall)"
            opacity = 0.82
        elif "BRIDGE" in ptype or "BRIDGE" in ulpin:
            color = "#8E24AA" # Purple Bridgeway
            status = "Connecting Bridgeway (Inter-Wing Transit)"
            opacity = 0.85
        elif "CORR" in ptype or "CORR" in ulpin:
            color = "#42A5F5" # Blue Corridor
            status = "Horizontal Corridor"
            opacity = 0.60
        else:
            # Residential room (2S / 4S)
            cap = 4 if "4S" in ulpin else 2
            occupants = occupancy_db.get(ulpin, [])
            occ_count = len(occupants)
            
            if occ_count == 0:
                color = "#2ECC71" # Emerald Green (Vacant)
                status = f"Vacant (0/{cap})"
            elif occ_count < cap:
                color = "#F39C12" # Orange (Partially Occupied)
                status = f"Partial ({occ_count}/{cap})"
            else:
                color = "#E74C3C" # Red (Full)
                status = f"Full ({occ_count}/{cap})"
                
            if occupants:
                status += f"<br>Occupants: {', '.join(occupants)}"

        hover_text = (
            f"<b>Floor {floor_num} | Unit: {label}</b><br>"
            f"<b>3D ULPIN:</b> {ulpin}<br>"
            f"<b>Type:</b> {ptype}<br>"
            f"<b>Status:</b> {status}<br>"
            f"<b>Dimensions:</b> {round(x1-x0,2)}m × {round(y1-y0,2)}m × {round(z1-z0,2)}m<br>"
            f"<b>Area:</b> {area_sqm} m²<br>"
            f"<b>Coordinates:</b> Lat {lat}, Lon {lon}<br>"
            f"<b>Elevation:</b> {z0}m – {z1}m (Slab: {r.get('z_slab_top', z1)}m)"
        )
        
        mesh = get_box_mesh(x0, x1, y0, y1, z0, z1, color, label, hover_text, floor_num, opacity)
        fig.add_trace(mesh)
        trace_floor_map.append(floor_num)

    total_parcel_traces = len(trace_floor_map)
    mid_x = (min_x + max_x) / 2.0
    
    # 3D Ground Orientation Badges / Labels
    fig.add_trace(go.Scatter3d(
        x=[mid_x, max_x - 8.0],
        y=[-4.0, -4.0],
        z=[0.0, 0.0],
        mode="text",
        text=["<b>▲ FRONT FACADE (Outdoor Gym / Ground View) ▲</b>", "<b>Units 01-06 (Entrance Wing) ►</b>"],
        textposition="top center",
        textfont=dict(size=14, color="#1565C0"),
        hoverinfo="none",
        name="Front Facade"
    ))
    trace_floor_map.append(0) # 0 = always visible annotation

    # Back Facade Marker
    fig.add_trace(go.Scatter3d(
        x=[mid_x, max_x - 22.0],
        y=[max_y + 4.0, max_y + 4.0],
        z=[0.0, 0.0],
        mode="text",
        text=["<b>▼ BACK FACADE (Rear Wing) ▼</b>", "<b>Units 56-53 (Rear Wing) ►</b>"],
        textposition="bottom center",
        textfont=dict(size=14, color="#C62828"),
        hoverinfo="none",
        name="Back Facade"
    ))
    trace_floor_map.append(0)

    # Vertical Floor Elevation Labels along West Wing Edge
    floor_elev_x = [min_x - 5.0] * len(floors)
    floor_elev_y = [mid_y := (min_y + max_y) / 2.0] * len(floors)
    floor_elev_z = [((f - 1) * 3.4) + 1.45 for f in floors]
    floor_elev_text = [f"<b>◄ Floor {f} ({((f-1)*3.4):.1f}m - {(((f-1)*3.4)+2.9):.1f}m)</b>" for f in floors]

    fig.add_trace(go.Scatter3d(
        x=floor_elev_x,
        y=floor_elev_y,
        z=floor_elev_z,
        mode="text",
        text=floor_elev_text,
        textposition="middle left",
        textfont=dict(size=11, color="#37474F"),
        hoverinfo="none",
        name="Floor Levels"
    ))
    trace_floor_map.append(0)

    # Build Interactive Floor Filter Dropdown / Buttons
    buttons = [
        dict(
            label="🏢 All 10 Floors (Full Tower)",
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

    # Set up 3D Scene with Default Camera looking directly at the FRONT FACADE of the full tower
    fig.update_layout(
        title=dict(
            text=f"<b>3D ULPIN Digital Twin — 10-Storey Smart Hostel Volumetric Cadastre</b><br><sup>{len(rows)} Volumetric 3D Parcels across Floors 1 to 10 (Total Height: {max_z:.1f}m)</sup>",
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
            xaxis=dict(title="East/West (Meters)", backgroundcolor="#F8F9FA", gridcolor="#E0E0E0"),
            yaxis=dict(title="Front → Back Depth (Meters)", backgroundcolor="#F8F9FA", gridcolor="#E0E0E0"),
            zaxis=dict(title="Vertical Elevation Z (Meters)", backgroundcolor="#ECEFF1", gridcolor="#CFD8DC"),
            aspectmode="data", # 1:1:1 True Metric Real World Aspect Ratio
            camera=dict(
                # Camera placed facing the FRONT FACADE with elevated perspective for the 10-floor tower
                eye=dict(x=0.0, y=-2.15, z=1.25),
                center=dict(x=0.0, y=0.0, z=0.15),
                up=dict(x=0.0, y=0.0, z=1.0)
            )
        ),
        margin=dict(l=0, r=0, b=0, t=75),
        showlegend=False
    )

    os.makedirs(os.path.dirname(OUTPUT_HTML), exist_ok=True)
    fig.write_html(OUTPUT_HTML)
    print(f"✅ 10-Storey 3D Digital Twin successfully generated ({len(rows)} units) at: {OUTPUT_HTML}")

if __name__ == "__main__":
    main()
