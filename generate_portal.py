import csv
import json
import os
import plotly.graph_objects as go
import plotly.io as pio

def generate_portal_html():
    # Load registry
    registry_file = "config/institutional_registry.json"
    with open(registry_file, "r") as f:
        registry = json.load(f)

    # Active Dataset
    data_file = "data/room_labels_all_floors_final.csv"
    rows = []
    with open(data_file, "r") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)

    # Load occupancy (Simulated demonstration data)
    occ_file = "data/occupancy_db.json"
    occupancy_db = {}
    if os.path.exists(occ_file):
        try:
            with open(occ_file, "r") as f:
                occupancy_db = json.load(f)
        except Exception:
            occupancy_db = {}

    # Build 3D Plotly Figure
    fig = go.Figure()
    min_x, max_x = float("inf"), float("-inf")
    min_y, max_y = float("inf"), float("-inf")
    min_z, max_z = float("inf"), float("-inf")

    floors = sorted(list(set(int(r["floor"]) for r in rows)))
    trace_meta = []

    for idx, r in enumerate(rows):
        ulpin = r["ulpin_3d"]
        label = r["room_id"]
        ptype = r.get("type", "")
        fl = int(r["floor"])

        x0, x1 = float(r["real_x_start_m"]), float(r["real_x_end_m"])
        if "real_y_start_m" in r and "real_y_end_m" in r:
            y0, y1 = float(r["real_y_start_m"]), float(r["real_y_end_m"])
        else:
            yc = float(r["real_y_center_m"])
            d = float(r["real_depth_m"])
            y0, y1 = yc - d/2.0, yc + d/2.0
        z0, z1 = float(r["z_min"]), float(r["z_max"])

        min_x, max_x = min(min_x, x0), max(max_x, x1)
        min_y, max_y = min(min_y, y0), max(max_y, y1)
        min_z, max_z = min(min_z, z0), max(max_z, z1)

        area_sqm = round((x1 - x0) * (y1 - y0), 2)
        occupants = occupancy_db.get(ulpin, [])
        occ_count = len(occupants)
        cap = 4 if "4S" in ulpin else (2 if "2S" in ulpin else 0)

        # Color-coding
        opacity = 0.88
        if "WASH" in ptype or "WASH" in ulpin:
            color = "#00BCD4"
            status = "Non-Residential (Washroom)"
        elif "STR" in ptype or "LIFT" in ptype:
            color = "#78909C"
            status = "Vertical Transit Core"
        elif "HALL" in ptype or "HALL" in ulpin:
            color = "#FFB300"
            status = "Common Assembly Hall"
            opacity = 0.82
        elif "BRIDGE" in ptype or "BRIDGE" in ulpin:
            color = "#8E24AA"
            status = "Connecting Bridgeway"
            opacity = 0.85
        elif "CORR" in ptype or "CORR" in ulpin:
            color = "#42A5F5"
            status = "Horizontal Corridor"
            opacity = 0.60
        else:
            if occ_count == 0:
                color = "#2ECC71"
                status = f"Vacant (0/{cap})"
            elif occ_count < cap:
                color = "#F39C12"
                status = f"Partial ({occ_count}/{cap})"
            else:
                color = "#E74C3C"
                status = f"Full ({occ_count}/{cap})"
            if occupants:
                status += f"<br>Occupants (Demo): {', '.join(occupants)}"

        hover_text = (
            f"<b>Floor {fl} | Unit: {label}</b><br>"
            f"<b>3D ULPIN:</b> {ulpin}<br>"
            f"<b>Type:</b> {ptype}<br>"
            f"<b>Status:</b> {status}<br>"
            f"<b>Dimensions:</b> {round(x1-x0,2)}m × {round(y1-y0,2)}m × {round(z1-z0,2)}m<br>"
            f"<b>Area:</b> {area_sqm} m²<br>"
            f"<b>Coordinates:</b> Lat {r.get('latitude')}, Lon {r.get('longitude')}<br>"
            f"<b>Elevation:</b> {z0}m – {z1}m"
        )

        vx = [x0, x1, x1, x0, x0, x1, x1, x0]
        vy = [y0, y0, y1, y1, y0, y0, y1, y1]
        vz = [z0, z0, z0, z0, z1, z1, z1, z1]

        ti = [7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2]
        tj = [3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3]
        tk = [0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6]

        fig.add_trace(go.Mesh3d(
            x=vx, y=vy, z=vz,
            i=ti, j=tj, k=tk,
            color=color,
            opacity=opacity,
            flatshading=True,
            name=label,
            hoverinfo="text",
            hovertext=hover_text,
            showlegend=False,
            visible=True
        ))

        trace_meta.append({
            "index": idx,
            "ulpin": ulpin,
            "room_id": label,
            "floor": fl,
            "type": ptype,
            "area": area_sqm,
            "dimensions": f"{round(x1-x0,2)}m x {round(y1-y0,2)}m x {round(z1-z0,2)}m",
            "coords": f"{r.get('latitude')}, {r.get('longitude')}",
            "elevation": f"{z0}m - {z1}m",
            "occupants": occupants,
            "occupancy_status": status.split("<br>")[0]
        })

    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2
    center_z = (min_z + max_z) / 2

    camera = dict(
        eye=dict(x=1.8, y=-1.8, z=1.4),
        center=dict(x=0, y=0, z=-0.1),
        up=dict(x=0, y=0, z=1)
    )

    fig.update_layout(
        scene=dict(
            xaxis=dict(title="X (East Meters)", backgroundcolor="#0b1329", gridcolor="#1e293b", showbackground=True),
            yaxis=dict(title="Y (North Meters)", backgroundcolor="#0b1329", gridcolor="#1e293b", showbackground=True),
            zaxis=dict(title="Elevation Z (Meters)", backgroundcolor="#0b1329", gridcolor="#1e293b", showbackground=True),
            aspectmode="data",
            camera=camera
        ),
        paper_bgcolor="#0b1329",
        plot_bgcolor="#0b1329",
        margin=dict(l=0, r=0, b=0, t=0),
        height=680
    )

    plot_div = pio.to_html(fig, full_html=False, include_plotlyjs='cdn', config={'responsive': True, 'displayModeBar': True})
    trace_meta_json = json.dumps(trace_meta)
    registry_json = json.dumps(registry)

    template = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>National 3D ULPIN Cadastre Platform</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
  :root {
    --bg-dark: #070d1e;
    --panel-bg: rgba(13, 23, 48, 0.85);
    --border-color: rgba(56, 189, 248, 0.2);
    --accent: #38bdf8;
    --text-primary: #f8fafc;
    --text-secondary: #94a3b8;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }
  body { background-color: var(--bg-dark); color: var(--text-primary); }
  .header { padding: 12px 24px; background: var(--panel-bg); border-bottom: 1px solid var(--border-color); display: flex; justify-content: space-between; align-items: center; }
  .workspace { display: grid; grid-template-columns: 320px 1fr 340px; height: calc(100vh - 65px); }
  .panel { background: var(--panel-bg); padding: 16px; border-right: 1px solid var(--border-color); overflow-y: auto; }
</style>
</head>
<body>
<div class="header">
  <h2>National 3D ULPIN Cadastral Platform</h2>
  <div>Survey No. 140/1 | Waranga, Nagpur Rural | pu-id: 33550994106</div>
</div>
<div class="workspace">
  <div class="panel">
    <h3>Campus Buildings</h3>
    <p>Hostel Block A (700 3D Units Surveyed)</p>
    <p>Admin, Academic, Residential</p>
  </div>
  <div style="position:relative;">__PLOT_DIV_PLACEHOLDER__</div>
  <div class="panel" style="border-right:none; border-left: 1px solid var(--border-color);">
    <h3>Cadastral Title Details</h3>
    <p>Select unit in 3D viewer</p>
  </div>
</div>
<script>
  const traceMeta = __TRACE_META_PLACEHOLDER__;
  const registry = __REGISTRY_PLACEHOLDER__;
</script>
</body>
</html>"""

    final_html = template.replace("__PLOT_DIV_PLACEHOLDER__", plot_div).replace("__TRACE_META_PLACEHOLDER__", trace_meta_json).replace("__REGISTRY_PLACEHOLDER__", registry_json)
    with open("frontend/iiitn_3d_portal.html", "w", encoding="utf-8") as f:
        f.write(final_html)
    print("✅ Portal successfully generated.")

if __name__ == "__main__":
    generate_portal_html()
