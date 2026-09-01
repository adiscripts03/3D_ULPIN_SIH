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

    # Load occupancy
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
                status += f"<br>Occupants: {', '.join(occupants)}"

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

        x = [x0, x1, x1, x0, x0, x1, x1, x0]
        y = [y0, y0, y1, y1, y0, y0, y1, y1]
        z = [z0, z0, z0, z0, z1, z1, z1, z1]
        i = [0, 0, 4, 4, 0, 0, 3, 3, 0, 0, 1, 1]
        j = [1, 2, 5, 6, 1, 5, 2, 6, 3, 7, 2, 6]
        k = [2, 3, 6, 7, 5, 4, 6, 7, 7, 4, 6, 5]

        mesh = go.Mesh3d(
            x=x, y=y, z=z, i=i, j=j, k=k,
            color=color, opacity=opacity,
            flatshading=True,
            lighting=dict(ambient=0.7, diffuse=0.8, roughness=0.5, specular=0.2),
            name=f"F{fl}-{label}",
            text=hover_text,
            hoverinfo="text",
            customdata=[ulpin] * 8
        )
        fig.add_trace(mesh)
        trace_meta.append({
            "trace_index": idx,
            "ulpin": ulpin,
            "room_id": label,
            "floor": fl,
            "type": ptype,
            "color": color,
            "area_sqm": area_sqm,
            "dim": f"{round(x1-x0,2)}m × {round(y1-y0,2)}m × {round(z1-z0,2)}m",
            "lat": r.get('latitude'),
            "lon": r.get('longitude'),
            "z_min": z0,
            "z_max": z1,
            "occupants": occupants,
            "capacity": cap
        })

    mid_x = (min_x + max_x) / 2.0
    mid_y = (min_y + max_y) / 2.0

    # Facade Markers without emoticons
    fig.add_trace(go.Scatter3d(
        x=[mid_x, max_x - 8.0],
        y=[-4.0, -4.0],
        z=[0.0, 0.0],
        mode="text",
        text=["<b>FRONT FACADE (Entrance View)</b>", "<b>Units 01-06 (Entrance Wing)</b>"],
        textposition="top center",
        textfont=dict(size=14, color="#1565C0"),
        hoverinfo="none",
        name="Front Facade"
    ))

    fig.add_trace(go.Scatter3d(
        x=[mid_x, max_x - 22.0],
        y=[max_y + 4.0, max_y + 4.0],
        z=[0.0, 0.0],
        mode="text",
        text=["<b>BACK FACADE (Rear Wing)</b>", "<b>Units 56-53 (Rear Wing)</b>"],
        textposition="bottom center",
        textfont=dict(size=14, color="#C62828"),
        hoverinfo="none",
        name="Back Facade"
    ))

    floor_elev_x = [min_x - 5.0] * len(floors)
    floor_elev_y = [mid_y] * len(floors)
    floor_elev_z = [((f - 1) * 3.4) + 1.45 for f in floors]
    floor_elev_text = [f"<b>Floor {f} ({((f-1)*3.4):.1f}m - {(((f-1)*3.4)+2.9):.1f}m)</b>" for f in floors]

    fig.add_trace(go.Scatter3d(
        x=floor_elev_x, y=floor_elev_y, z=floor_elev_z,
        mode="text", text=floor_elev_text,
        textposition="middle left",
        textfont=dict(size=11, color="#37474F"),
        hoverinfo="none",
        name="Floor Levels"
    ))

    fig.update_layout(
        scene=dict(
            xaxis=dict(title="East/West (Meters)", backgroundcolor="#F8F9FA", gridcolor="#E0E0E0"),
            yaxis=dict(title="Front / Back Depth (Meters)", backgroundcolor="#F8F9FA", gridcolor="#E0E0E0"),
            zaxis=dict(title="Vertical Elevation Z (Meters)", backgroundcolor="#ECEFF1", gridcolor="#CFD8DC"),
            aspectmode="data",
            camera=dict(
                eye=dict(x=0.0, y=-2.15, z=1.25),
                center=dict(x=0.0, y=0.0, z=0.15),
                up=dict(x=0.0, y=0.0, z=1.0)
            )
        ),
        margin=dict(l=0, r=0, b=0, t=10),
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )

    plot_div = pio.to_html(fig, full_html=False, include_plotlyjs="cdn", config={"responsive": True, "displayModeBar": True})
    trace_meta_json = json.dumps(trace_meta)
    registry_json = json.dumps(registry)

    # Clean Fullscreen Template without emoticons
    template = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>3D ULPIN Volumetric Cadastre Platform</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
  :root {
    --primary: #0f172a;
    --primary-blue: #1e3a8a;
    --accent: #2563eb;
    --accent-light: #3b82f6;
    --success: #10b981;
    --warning: #f59e0b;
    --danger: #ef4444;
    --bg-page: #f8fafc;
    --bg-card: #ffffff;
    --text-main: #0f172a;
    --text-muted: #64748b;
    --border: #e2e8f0;
    --radius: 12px;
    --shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.08), 0 8px 10px -6px rgba(15, 23, 42, 0.04);
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    font-family: 'Inter', sans-serif;
    background-color: var(--bg-page);
    color: var(--text-main);
    display: flex;
    flex-direction: column;
    height: 100vh;
    overflow: hidden;
  }

  /* Main Workspace Layout (Full Height) */
  .workspace {
    display: grid;
    grid-template-columns: 350px 1fr 360px;
    flex: 1;
    height: 100vh;
    overflow: hidden;
  }

  /* Left Panel: Hierarchy & Search */
  .left-panel {
    background: var(--bg-card);
    border-right: 1px solid var(--border);
    padding: 18px;
    display: flex;
    flex-direction: column;
    gap: 16px;
    overflow-y: auto;
  }

  .panel-section-title {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    font-weight: 700;
    color: var(--text-muted);
    margin-bottom: 6px;
  }

  .search-box {
    position: relative;
  }

  .search-input {
    width: 100%;
    padding: 11px 14px 11px 14px;
    border-radius: 10px;
    border: 1.5px solid var(--border);
    font-size: 13px;
    font-family: inherit;
    background: #f8fafc;
    color: var(--text-main);
    transition: all 0.2s;
  }

  .search-input:focus {
    outline: none;
    border-color: var(--accent);
    background: #ffffff;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15);
  }

  .suggestions {
    margin-top: 6px;
    background: #ffffff;
    border: 1px solid var(--border);
    border-radius: 8px;
    max-height: 150px;
    overflow-y: auto;
    display: none;
    box-shadow: var(--shadow);
  }

  .suggestion-item {
    padding: 8px 12px;
    font-size: 12px;
    font-family: 'JetBrains Mono', monospace;
    cursor: pointer;
    border-bottom: 1px solid #f1f5f9;
  }

  .suggestion-item:hover {
    background: #eff6ff;
    color: var(--accent);
  }

  .select-group label {
    font-size: 12px;
    font-weight: 600;
    color: var(--text-main);
    display: block;
    margin-bottom: 4px;
  }

  .custom-select {
    width: 100%;
    padding: 9px 12px;
    border-radius: 8px;
    border: 1.5px solid var(--border);
    background: #ffffff;
    font-size: 12.5px;
    font-weight: 500;
    color: var(--text-main);
    cursor: pointer;
  }

  .custom-select:focus {
    outline: none;
    border-color: var(--accent);
  }

  .floor-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 6px;
  }

  .floor-btn {
    padding: 7px 0;
    border: 1px solid var(--border);
    background: #f8fafc;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s;
    text-align: center;
  }

  .floor-btn:hover {
    background: #e2e8f0;
  }

  .floor-btn.active {
    background: var(--primary-blue);
    color: #ffffff;
    border-color: var(--primary-blue);
  }

  /* Middle: 3D WebGL Canvas */
  .center-panel {
    position: relative;
    background: #ffffff;
    overflow: hidden;
  }

  .plot-container-wrap {
    width: 100%;
    height: 100%;
  }

  .hud-overlay {
    position: absolute;
    top: 16px;
    left: 16px;
    background: rgba(255, 255, 255, 0.94);
    backdrop-filter: blur(8px);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 10px 16px;
    font-size: 12px;
    box-shadow: var(--shadow);
    pointer-events: none;
    z-index: 10;
  }

  .hud-overlay strong {
    color: var(--primary-blue);
  }

  /* Right Panel: Cadastral Property Card */
  .right-panel {
    background: var(--bg-card);
    border-left: 1px solid var(--border);
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 16px;
    overflow-y: auto;
  }

  .property-card {
    background: #f8fafc;
    border: 1.5px solid var(--border);
    border-radius: var(--radius);
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .card-header-badge {
    display: inline-block;
    align-self: flex-start;
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    background: #dbeafe;
    color: #1e40af;
  }

  .ulpin-title {
    font-size: 15px;
    font-weight: 800;
    font-family: 'JetBrains Mono', monospace;
    color: var(--primary-blue);
    word-break: break-all;
  }

  .property-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    font-size: 11.5px;
  }

  .prop-item {
    background: #ffffff;
    padding: 8px 10px;
    border-radius: 6px;
    border: 1px solid #e2e8f0;
  }

  .prop-label {
    color: var(--text-muted);
    font-size: 10.5px;
    margin-bottom: 2px;
  }

  .prop-val {
    font-weight: 700;
    color: var(--text-main);
  }

  .occupant-box {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 10px 12px;
    font-size: 12px;
  }

  .occupant-box strong {
    display: block;
    color: var(--text-muted);
    font-size: 10.5px;
    margin-bottom: 4px;
  }

  .status-tag {
    display: inline-flex;
    align-items: center;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
  }

  .status-valid {
    background: #d1fae5;
    color: #065f46;
  }
</style>
</head>
<body>

<!-- Main Workspace -->
<div class="workspace">

  <!-- Left Sidebar -->
  <aside class="left-panel">
    
    <!-- Tier 1: Institution / Estate Selector -->
    <div class="select-group">
      <div class="panel-section-title">Tier 1: Registered Estate / Institution</div>
      <select id="institutionSelect" class="custom-select" onchange="onInstitutionChange()">
        <option value="INST_IIITN">IIIT Nagpur Campus (Pilot Case Study - Active)</option>
        <option value="INST_DDA01">DDA Multi-Storey Residential Complex (Dwarka, Delhi)</option>
      </select>
    </div>

    <!-- Quick Search -->
    <div>
      <div class="panel-section-title">Quick 3D ULPIN Search</div>
      <div class="search-box">
        <input type="text" id="searchInput" class="search-input" placeholder="Search 3D ULPIN or Unit (e.g. 304, 1001)..." onkeyup="handleSearch(event)">
      </div>
      <div id="suggestionsBox" class="suggestions"></div>
    </div>

    <!-- Tier 2: Building Selector -->
    <div class="select-group">
      <div class="panel-section-title">Tier 2: Building Sub-Structure</div>
      <select id="buildingSelect" class="custom-select" onchange="onBuildingChange()">
        <option value="HSTL01">Hostel Block 1 (Main 10-Storey Tower - 700 Parcels)</option>
        <option value="HSTL02">Hostel Block 2 (Girls Wing - 8 Floors - 560 Parcels)</option>
        <option value="ACAD01">Academic Complex (6 Floors - 300 Parcels)</option>
      </select>
    </div>

    <!-- Floor Slicer -->
    <div>
      <div class="panel-section-title">Vertical Floor Slicer</div>
      <div class="floor-grid">
        <button class="floor-btn active" onclick="sliceFloor('all')">All</button>
        <button class="floor-btn" onclick="sliceFloor(1)">F1</button>
        <button class="floor-btn" onclick="sliceFloor(2)">F2</button>
        <button class="floor-btn" onclick="sliceFloor(3)">F3</button>
        <button class="floor-btn" onclick="sliceFloor(4)">F4</button>
        <button class="floor-btn" onclick="sliceFloor(5)">F5</button>
        <button class="floor-btn" onclick="sliceFloor(6)">F6</button>
        <button class="floor-btn" onclick="sliceFloor(7)">F7</button>
        <button class="floor-btn" onclick="sliceFloor(8)">F8</button>
        <button class="floor-btn" onclick="sliceFloor(9)">F9</button>
        <button class="floor-btn" onclick="sliceFloor(10)">F10</button>
      </div>
    </div>

  </aside>

  <!-- Middle 3D View -->
  <main class="center-panel">
    <div class="hud-overlay">
      <strong>Active Structure:</strong> <span id="hudBuildingText">Hostel Block 1</span> | <span id="hudFloorText">All 10 Floors (700 Parcels)</span>
    </div>
    <div class="plot-container-wrap">
      __PLOT_DIV_PLACEHOLDER__
    </div>
  </main>

  <!-- Right Sidebar -->
  <aside class="right-panel">
    <div class="panel-section-title">Tier 3: 3D Cadastral Title Card</div>

    <div class="property-card" id="propertyCard">
      <span class="card-header-badge" id="cardCategory">Residential Parcel</span>
      <div class="ulpin-title" id="cardUlpin">HSTL01-F1-101-4S</div>

      <div class="property-grid">
        <div class="prop-item">
          <div class="prop-label">Unit / Room No</div>
          <div class="prop-val" id="cardRoom">Room 101</div>
        </div>
        <div class="prop-item">
          <div class="prop-label">Vertical Level</div>
          <div class="prop-val" id="cardFloor">Floor 1 (0.0m - 2.9m)</div>
        </div>
        <div class="prop-item">
          <div class="prop-label">Carpet Area</div>
          <div class="prop-val" id="cardArea">29.48 m²</div>
        </div>
        <div class="prop-item">
          <div class="prop-label">Dimensions</div>
          <div class="prop-val" id="cardDim">3.35m × 8.8m × 2.9m</div>
        </div>
      </div>

      <div class="occupant-box">
        <strong>CURRENT TITLE / ALLOTMENT LEDGER</strong>
        <div id="cardOccupants" style="font-weight:600; color:#1e293b;">BT_ID_JOHN (1/4 Capacity)</div>
      </div>

      <div style="display:flex; justify-content:space-between; align-items:center; margin-top:4px;">
        <span class="status-tag status-valid">Topologically Valid</span>
        <span style="font-size:10.5px; color:#64748b;">DoLR PS 26011 Compliant</span>
      </div>
    </div>

    <div>
      <div class="panel-section-title">Base Land Record Metadata</div>
      <div id="estateMetadataBox" style="font-size:11.5px; line-height:1.6; color:#475569; background:#f8fafc; padding:12px; border-radius:8px; border:1px solid #e2e8f0;">
        <strong>Registered Entity:</strong> IIIT Nagpur (Pilot Case Study)<br>
        <strong>Master 2D ULPIN:</strong> MH-NGP-IIITN-2026<br>
        <strong>Bhu-Aadhaar:</strong> 27-712-004-891024<br>
        <strong>Survey No:</strong> Survey 140, 141/1 (Waranga)<br>
        <strong>Taluka:</strong> Nagpur Rural | <strong>State:</strong> Maharashtra<br>
        <strong>Base Elevation:</strong> 298m MSL | <strong>Plot Area:</strong> 100.0 Acres
      </div>
    </div>
  </aside>

</div>

<script>
  const traceMeta = __TRACE_META_PLACEHOLDER__;
  const registry = __REGISTRY_PLACEHOLDER__;

  function sliceFloor(fl) {
    const plotDiv = document.getElementsByClassName('plotly-graph-div')[0];
    if (!plotDiv) return;

    document.querySelectorAll('.floor-btn').forEach(btn => {
      btn.classList.remove('active');
      if (btn.textContent.toLowerCase() === (fl === 'all' ? 'all' : 'f' + fl)) {
        btn.classList.add('active');
      }
    });

    document.getElementById('hudFloorText').textContent = (fl === 'all') ? 'All 10 Floors (700 Parcels)' : 'Level ' + fl + ' Only';

    const update = { visible: [] };
    for (let i = 0; i < traceMeta.length; i++) {
      if (fl === 'all' || traceMeta[i].floor === parseInt(fl)) {
        update.visible.push(true);
      } else {
        update.visible.push(false);
      }
    }
    update.visible.push(true, true, true);

    Plotly.restyle(plotDiv, update);

    // Dynamically update Title Card to the selected floor's unit
    if (fl === 'all') {
      const firstUnit = traceMeta[0];
      if (firstUnit) updateCardOnly(firstUnit);
    } else {
      const floorUnit = traceMeta.find(m => m.floor === parseInt(fl));
      if (floorUnit) updateCardOnly(floorUnit);
    }
  }

  function updateCardOnly(target) {
    if (!target) return;
    document.getElementById('cardCategory').textContent = target.type + ' Spatial Parcel';
    document.getElementById('cardUlpin').textContent = target.ulpin;
    document.getElementById('cardRoom').textContent = 'Unit ' + target.room_id;
    document.getElementById('cardFloor').textContent = 'Floor ' + target.floor + ' (' + target.z_min + 'm - ' + target.z_max + 'm)';
    document.getElementById('cardArea').textContent = target.area_sqm + ' m²';
    document.getElementById('cardDim').textContent = target.dim;

    const occ = (target.occupants && target.occupants.length > 0) ? target.occupants.join(', ') + ' (' + target.occupants.length + '/' + target.capacity + ' Capacity)' : 'Vacant (0/' + target.capacity + ' Legal Capacity)';
    document.getElementById('cardOccupants').textContent = occ;
  }

  // Attach interactive 3D click listener
  window.addEventListener('load', function() {
    const plotDiv = document.getElementsByClassName('plotly-graph-div')[0];
    if (plotDiv && plotDiv.on) {
      plotDiv.on('plotly_click', function(data) {
        if (data && data.points && data.points.length > 0) {
          const pt = data.points[0];
          const traceIdx = pt.curveNumber;
          if (traceIdx < traceMeta.length) {
            updateCardOnly(traceMeta[traceIdx]);
          }
        }
      });
    }
  });

  function handleSearch(e) {
    const val = document.getElementById('searchInput').value.trim().toUpperCase();
    const sugBox = document.getElementById('suggestionsBox');

    if (!val) {
      sugBox.style.display = 'none';
      return;
    }

    const matches = traceMeta.filter(m => m.ulpin.includes(val) || m.room_id.includes(val)).slice(0, 8);
    if (matches.length > 0) {
      sugBox.innerHTML = matches.map(m => `<div class="suggestion-item" onclick="selectUnit('${m.ulpin}')">${m.ulpin} (Unit ${m.room_id})</div>`).join('');
      sugBox.style.display = 'block';
    } else {
      sugBox.style.display = 'none';
    }

    if (e.key === 'Enter' && matches.length > 0) {
      selectUnit(matches[0].ulpin);
    }
  }

  function selectUnit(ulpin) {
    const target = traceMeta.find(m => m.ulpin === ulpin);
    if (!target) return;

    document.getElementById('suggestionsBox').style.display = 'none';
    document.getElementById('searchInput').value = target.ulpin;

    sliceFloor(target.floor);

    document.getElementById('cardCategory').textContent = target.type + ' Spatial Parcel';
    document.getElementById('cardUlpin').textContent = target.ulpin;
    document.getElementById('cardRoom').textContent = 'Unit ' + target.room_id;
    document.getElementById('cardFloor').textContent = `Floor ${target.floor} (${target.z_min}m - ${target.z_max}m)`;
    document.getElementById('cardArea').textContent = target.area_sqm + ' m²';
    document.getElementById('cardDim').textContent = target.dim;

    const occ = (target.occupants && target.occupants.length > 0) ? target.occupants.join(', ') + ` (${target.occupants.length}/${target.capacity} Capacity)` : `Vacant (0/${target.capacity} Legal Capacity)`;
    document.getElementById('cardOccupants').textContent = occ;
  }

  function onInstitutionChange() {
    const instVal = document.getElementById('institutionSelect').value;
    const bldgSelect = document.getElementById('buildingSelect');
    
    if (instVal === 'INST_IIITN') {
      document.getElementById('estateMetadataBox').innerHTML = `
        <strong>Registered Entity:</strong> IIIT Nagpur (Pilot Case Study)<br>
        <strong>Master 2D ULPIN:</strong> MH-NGP-IIITN-2026<br>
        <strong>Bhu-Aadhaar:</strong> 27-712-004-891024<br>
        <strong>Survey No:</strong> Survey 140, 141/1 (Waranga)<br>
        <strong>Taluka:</strong> Nagpur Rural | <strong>State:</strong> Maharashtra<br>
        <strong>Base Elevation:</strong> 298m MSL | <strong>Plot Area:</strong> 100.0 Acres
      `;
      bldgSelect.innerHTML = `
        <option value="HSTL01">Hostel Block 1 (Main 10-Storey Tower - 700 Parcels)</option>
        <option value="HSTL02">Hostel Block 2 (Girls Wing - 8 Floors - 560 Parcels)</option>
        <option value="ACAD01">Academic Complex (6 Floors - 300 Parcels)</option>
      `;
      sliceFloor('all');
    } else if (instVal === 'INST_DDA01') {
      document.getElementById('estateMetadataBox').innerHTML = `
        <strong>Registered Entity:</strong> DDA Housing Society (Sector 19B, Dwarka)<br>
        <strong>Master 2D ULPIN:</strong> DL-SW-DDA-2026<br>
        <strong>Bhu-Aadhaar:</strong> 07-101-002-451201<br>
        <strong>Survey No:</strong> Plot No. 4, Pocket 3 (Dwarka)<br>
        <strong>District:</strong> South West Delhi | <strong>State:</strong> Delhi<br>
        <strong>Base Elevation:</strong> 216m MSL | <strong>Plot Area:</strong> 21.0 Acres
      `;
      bldgSelect.innerHTML = `
        <option value="TOWER_A">Tower A (14-Storey HIG Tower - 112 Parcels)</option>
        <option value="TOWER_B">Tower B (14-Storey HIG Tower - 112 Parcels)</option>
      `;
    }
  }

  function onBuildingChange() {
    document.getElementById('hudBuildingText').textContent = document.getElementById('buildingSelect').selectedOptions[0].text.split('(')[0];
    sliceFloor('all');
  }
</script>

</body>
</html>
"""

    final_html = template.replace("__PLOT_DIV_PLACEHOLDER__", plot_div).replace("__TRACE_META_PLACEHOLDER__", trace_meta_json).replace("__REGISTRY_PLACEHOLDER__", registry_json)

    output_path = "frontend/3d_cadastre_portal.html"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_html)

    # Also sync iiitn_3d_portal.html
    with open("frontend/iiitn_3d_portal.html", "w", encoding="utf-8") as f:
        f.write(final_html)

    print(f"✅ Clean Fullscreen 3D Cadastre Portal successfully updated at: {output_path}")

if __name__ == "__main__":
    generate_portal_html()
