import csv
import json
import os
import plotly.graph_objects as go
import plotly.io as pio

def build_dolr_official_page():
    # Load 10-floor dataset
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
        textfont=dict(size=13, color="#1565C0"),
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
        textfont=dict(size=13, color="#C62828"),
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
            zaxis=dict(title="Elevation Z (Meters)", backgroundcolor="#ECEFF1", gridcolor="#CFD8DC"),
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

    # Master DoLR HTML Template
    template = """<!DOCTYPE html>
<html lang="en-US">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Bhu-Aadhar : 3D Unique Land Parcel Identification Number (3D ULPIN) | Department of Land Resources</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Noto+Sans:wght@400;600;700&family=Noto+Sans+Devanagari:wght@400;600;700;800&family=JetBrains+Mono:wght@400;600;700&display=swap" rel="stylesheet">
<style>
  :root {
    --gov-blue: #003366;
    --gov-header-bg: #ffffff;
    --gov-orange: #e67e22;
    --gov-dark: #1e293b;
    --text-dark: #2d3748;
    --bg-light: #f8fafc;
    --border-color: #cbd5e1;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    font-family: 'Noto Sans', 'Inter', -apple-system, sans-serif;
    color: var(--text-dark);
    background-color: #ffffff;
    line-height: 1.6;
    font-size: 14px;
  }

  /* Top Bar */
  #topBar {
    background-color: #f1f5f9;
    border-bottom: 1px solid #cbd5e1;
    font-size: 11.5px;
    padding: 6px 4%;
    display: flex;
    justify-content: space-between;
    align-items: center;
    color: #475569;
  }

  .topBar-left {
    display: flex;
    align-items: center;
    gap: 10px;
    font-weight: 700;
  }

  .topBar-right {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .topBar-right a {
    color: inherit;
    text-decoration: none;
  }

  .utility-icons {
    display: flex;
    gap: 8px;
    align-items: center;
  }

  .icon-btn {
    background: #e2e8f0;
    padding: 3px 7px;
    border-radius: 4px;
    font-size: 11px;
    cursor: pointer;
    font-weight: 600;
  }

  /* Header Wrapper */
  .header-wrapper {
    padding: 16px 4%;
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #ffffff;
    border-bottom: 1px solid #e2e8f0;
  }

  .header-brand {
    display: flex;
    align-items: center;
    gap: 18px;
  }

  .emblem-logo {
    height: 70px;
    width: auto;
  }

  .ministry-text h2 {
    font-size: 15px;
    font-weight: 700;
    color: #0f172a;
    line-height: 1.2;
  }

  .ministry-text h1 {
    font-size: 21px;
    font-weight: 800;
    color: #0f172a;
    letter-spacing: -0.3px;
    text-transform: uppercase;
    line-height: 1.2;
    margin: 2px 0;
  }

  .ministry-text p {
    font-size: 13px;
    font-weight: 700;
    color: var(--gov-blue);
    letter-spacing: 0.5px;
    text-transform: uppercase;
  }

  .header-logos {
    display: flex;
    align-items: center;
    gap: 22px;
  }

  .swachh-img {
    height: 52px;
  }

  /* Menu Wrapper */
  .menuWrapper {
    background-color: #ffffff;
    border-bottom: 2px solid #e2e8f0;
    padding: 0 4%;
    box-shadow: 0 2px 4px rgba(0,0,0,0.03);
  }

  .main-nav {
    display: flex;
    list-style: none;
    align-items: center;
    flex-wrap: wrap;
  }

  .nav-item a {
    display: block;
    padding: 12px 14px;
    color: #1e293b;
    text-decoration: none;
    font-weight: 600;
    font-size: 13px;
    transition: background 0.15s, color 0.15s;
  }

  .nav-item.active a, .nav-item a:hover {
    background-color: var(--gov-orange);
    color: #ffffff;
  }

  .nav-btn-highlight {
    background: linear-gradient(135deg, #003366, #1e3a8a) !important;
    color: #ffffff !important;
    border-radius: 4px;
    margin-left: auto;
    padding: 8px 16px !important;
    box-shadow: 0 2px 6px rgba(0,51,102,0.3);
  }

  .nav-btn-highlight:hover {
    background: #1e3a8a !important;
  }

  /* Breadcrumb */
  .breadcrumb {
    background-color: #f8fafc;
    padding: 8px 4%;
    font-size: 11.5px;
    color: #64748b;
    border-bottom: 1px solid #e2e8f0;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .breadcrumb a {
    color: var(--gov-blue);
    text-decoration: none;
    font-weight: 600;
  }

  /* Master Layout */
  .page-container {
    display: grid;
    grid-template-columns: 1.1fr 1fr;
    gap: 30px;
    padding: 24px 4%;
    max-width: 1650px;
    margin: 0 auto;
  }

  /* Left Article Content */
  .article-col h1 {
    font-size: 24px;
    font-weight: 800;
    color: #0f172a;
    margin-bottom: 14px;
    letter-spacing: -0.4px;
    border-bottom: 2px solid #e2e8f0;
    padding-bottom: 8px;
  }

  .article-col p {
    font-size: 13.5px;
    color: #334155;
    margin-bottom: 14px;
    text-align: justify;
    line-height: 1.7;
  }

  .section-h2 {
    font-size: 17px;
    font-weight: 700;
    color: var(--gov-blue);
    margin-top: 24px;
    margin-bottom: 10px;
    border-left: 4px solid var(--gov-orange);
    padding-left: 10px;
  }

  .ordered-steps {
    padding-left: 20px;
    margin-bottom: 16px;
    font-size: 13px;
    color: #334155;
  }

  .ordered-steps li {
    margin-bottom: 10px;
    line-height: 1.6;
  }

  .benefit-list {
    list-style: none;
    margin-bottom: 20px;
  }

  .benefit-list li {
    position: relative;
    padding-left: 20px;
    margin-bottom: 8px;
    font-size: 13px;
    color: #334155;
    line-height: 1.6;
  }

  .benefit-list li::before {
    content: "•";
    position: absolute;
    left: 4px;
    color: var(--gov-orange);
    font-weight: bold;
    font-size: 18px;
  }

  /* Right Column: Live Embedded 3D Cadastral Digital Twin */
  .cadastre-col {
    background: #ffffff;
    border: 1.5px solid #cbd5e1;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 10px 25px -5px rgba(0,0,0,0.08);
    display: flex;
    flex-direction: column;
    height: fit-content;
  }

  .cadastre-header {
    background: linear-gradient(135deg, #090d16 0%, #003366 100%);
    padding: 14px 18px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .cadastre-header h3 {
    font-size: 13.5px;
    font-weight: 600;
    color: #cbd5e1;
    letter-spacing: 0.3px;
    text-transform: uppercase;
  }

  .cadastre-controls {
    background: #f8fafc;
    padding: 12px 18px;
    border-bottom: 1px solid #e2e8f0;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .search-row {
    display: flex;
    gap: 8px;
    position: relative;
  }

  .search-inp {
    flex: 1;
    padding: 8px 12px;
    border: 1.5px solid #cbd5e1;
    border-radius: 6px;
    font-size: 12.5px;
    font-family: 'JetBrains Mono', monospace;
  }

  .search-inp:focus {
    outline: none;
    border-color: #2563eb;
    box-shadow: 0 0 0 3px rgba(37,99,235,0.15);
  }

  .btn-search {
    background: #2563eb;
    color: #ffffff;
    border: none;
    padding: 8px 14px;
    border-radius: 6px;
    font-weight: 700;
    font-size: 12px;
    cursor: pointer;
  }

  .floor-btn-row {
    display: flex;
    gap: 4px;
    overflow-x: auto;
    padding-bottom: 2px;
  }

  .f-btn {
    padding: 5px 9px;
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
    cursor: pointer;
    white-space: nowrap;
  }

  .f-btn.active {
    background: #003366;
    color: #ffffff;
    border-color: #003366;
  }

  .viewer-3d-wrap {
    width: 100%;
    height: 440px;
    background: #ffffff;
  }

  /* Cadastral Title Card below 3D */
  .title-card {
    padding: 14px 18px;
    background: #f8fafc;
    border-top: 1px solid #e2e8f0;
    font-size: 12px;
  }

  .title-card-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    margin-top: 8px;
  }

  .title-item {
    background: #ffffff;
    padding: 6px 10px;
    border-radius: 4px;
    border: 1px solid #e2e8f0;
  }

  .title-item span {
    color: #64748b;
    font-size: 10px;
    display: block;
  }

  .title-item strong {
    color: #0f172a;
    font-size: 11.5px;
    font-family: 'JetBrains Mono', monospace;
  }

  /* Official DoLR Footer */
  footer {
    background: #0f172a;
    color: #94a3b8;
    padding: 24px 4% 12px;
    font-size: 11.5px;
    border-top: 4px solid var(--gov-orange);
    margin-top: 30px;
  }

  .footer-links {
    display: flex;
    justify-content: center;
    gap: 20px;
    list-style: none;
    margin-bottom: 12px;
  }

  .footer-links a {
    color: #cbd5e1;
    text-decoration: none;
  }

  .footer-copy {
    text-align: center;
    color: #64748b;
    font-size: 10.5px;
  }
</style>
</head>
<body>

<!-- Header (Matching Official DoLR Elements Tree) -->
<header id="mainHeader">
  <!-- topBar start -->
  <div id="topBar">
    <div class="topBar-left">
      <span>भारत सरकार</span> | <span>GOVERNMENT OF INDIA</span>
    </div>
    <div class="topBar-right">
      <a href="#articleStart">Skip to Main Content</a>
      <span>|</span>
      <span>Screen Reader Access</span>
      <span>|</span>
      <span>English / हिन्दी</span>
      <span>|</span>
      <div class="utility-icons">
        <span class="icon-btn">A-</span>
        <span class="icon-btn">A</span>
        <span class="icon-btn">A+</span>
        <span class="icon-btn">Search</span>
      </div>
    </div>
  </div>
  <!-- topBar end -->

  <!-- header-wrapper start -->
  <div class="header-wrapper">
    <div class="header-brand">
      <!-- National Lion Emblem of India SVG -->
      <svg class="emblem-logo" viewBox="0 0 60 90" fill="#1e293b" xmlns="http://www.w3.org/2000/svg">
        <path d="M30 5C22 5 18 10 18 16C18 20 20 23 23 25C20 27 16 31 16 38C16 46 22 52 30 52C38 52 44 46 44 38C44 31 40 27 37 25C40 23 42 20 42 16C42 10 38 5 30 5ZM30 10C34 10 37 12 37 16C37 20 34 22 30 22C26 22 23 20 23 16C23 12 26 10 30 10ZM30 28C35 28 39 32 39 38C39 44 35 47 30 47C25 47 21 44 21 38C21 32 25 28 30 28Z" fill="#0f172a"/>
        <path d="M12 55H48V60H12V55ZM16 63H44V66H16V63ZM20 69H40V72H20V69ZM14 75H46V78H14V75Z" fill="#334155"/>
        <circle cx="30" cy="57.5" r="2" fill="#e67e22"/>
      </svg>
      <div class="ministry-text">
        <h2>भूमि संसाधन विभाग</h2>
        <h1>DEPARTMENT OF LAND RESOURCES</h1>
        <p>MINISTRY OF RURAL DEVELOPMENT</p>
      </div>
    </div>

    <div class="header-logos">
      <!-- Swachh Bharat Official Emblem -->
      <svg class="swachh-img" viewBox="0 0 160 54" xmlns="http://www.w3.org/2000/svg" style="height: 52px; width: auto;">
        <!-- Left & Right Spectacle Lenses -->
        <circle cx="50" cy="20" r="16.5" stroke="#1e293b" stroke-width="2.2" fill="none"/>
        <circle cx="110" cy="20" r="16.5" stroke="#1e293b" stroke-width="2.2" fill="none"/>
        <!-- Bridge between lenses -->
        <path d="M 66.5 20 Q 80 14 93.5 20" stroke="#1e293b" stroke-width="2.2" fill="none"/>
        <!-- Left Temple Arm -->
        <path d="M 33.5 20 C 20 16 10 24 2 19" stroke="#1e293b" stroke-width="2" fill="none"/>
        <!-- Right Temple Arm -->
        <path d="M 126.5 20 C 140 16 150 24 158 19" stroke="#1e293b" stroke-width="2" fill="none"/>
        <!-- Text inside Left Lens: स्वच्छ -->
        <text x="50" y="24" text-anchor="middle" font-family="'Noto Sans Devanagari', 'Noto Sans', sans-serif" font-size="10" font-weight="700" fill="#0f172a">स्वच्छ</text>
        <!-- Text inside Right Lens: भारत -->
        <text x="110" y="24" text-anchor="middle" font-family="'Noto Sans Devanagari', 'Noto Sans', sans-serif" font-size="10" font-weight="700" fill="#0f172a">भारत</text>
        <!-- Tagline below: एक कदम स्वच्छता की ओर -->
        <text x="80" y="48" text-anchor="middle" font-family="'Noto Sans Devanagari', 'Noto Sans', sans-serif" font-size="8.5" font-weight="600" fill="#334155" letter-spacing="0.2px">एक कदम स्वच्छता की ओर</text>
      </svg>
    </div>
  </div>
  <!-- header-wrapper end -->

  <!-- menuWrapper start -->
  <div class="menuWrapper">
    <ul class="main-nav">
      <li class="nav-item"><a href="#">Home</a></li>
      <li class="nav-item"><a href="#">Ministry</a></li>
      <li class="nav-item active"><a href="#">Schemes</a></li>
      <li class="nav-item"><a href="#">Acts, Rules & Policies</a></li>
      <li class="nav-item"><a href="#">NAKSHA</a></li>
      <li class="nav-item"><a href="#">Documents</a></li>
      <li class="nav-item"><a href="#">Centre of Excellence</a></li>
      <li class="nav-item"><a href="#">Events</a></li>
      <li class="nav-item"><a href="#">Media</a></li>
      <li class="nav-item"><a href="#">Services</a></li>
      <li class="nav-item"><a href="#">RTI</a></li>
      <li class="nav-item" style="margin-left:auto;">
        <a href="3d_cadastre_portal.html" class="nav-btn-highlight">
          Open Fullscreen 3D Portal
        </a>
      </li>
    </ul>
  </div>
  <!-- menuWrapper end -->
</header>

<!-- Breadcrumb -->
<div class="breadcrumb">
  <div>
    <a href="#">Home</a> &gt; <a href="#">Schemes</a> &gt; <a href="#">Land Reforms Initiatives</a> &gt; <span>Bhu-Aadhar : 3D Unique Land Parcel Identification Number (3D ULPIN)</span>
  </div>
  <div style="display:flex; gap:8px;">
    <span>Share:</span>
    <a href="#" style="color:#1d4ed8;">Facebook</a>
    <a href="#" style="color:#0f172a;">X</a>
    <a href="#" style="color:#0284c7;">LinkedIn</a>
  </div>
</div>

<!-- Main Page Container -->
<div class="page-container" id="articleStart">

  <!-- Left Column: Official Scheme Content -->
  <div class="article-col">
    <h1>Bhu-Aadhar : 3D Unique Land Parcel Identification Number (3D ULPIN)</h1>

    <p>
      The <strong>3D Unique Land Parcel Identification Number (3D ULPIN)</strong> is part of the <strong>Digital India Land Records Modernization Programme (DILRMP)</strong> under the Department of Land Resources, Ministry of Rural Development. It provides a standardized alphanumeric spatial identity for volumetric property units in multi-storey buildings, elevated transit corridors, underground utilities, and multi-owner strata estates.
    </p>

    <p>
      While conventional 2D ULPIN defines surface land parcels, the 3D ULPIN framework extends land administration into the third dimension (Z-elevation). Based on <strong>ISO 19152 (Land Administration Domain Model - LADM)</strong> and <strong>OGC CityGML</strong> standards, it assigns a Single Authoritative Source of Truth to vertical and subsurface property rights.
    </p>

    <h2 class="section-h2">Generation of 3D ULPIN</h2>
    <ol class="ordered-steps">
      <li>
        <strong>Property Natural Identifier Lot (PNIL):</strong> 
        The 14-digit base surface parcel ID computed from the georeferenced boundary coordinates of the surface plot.
      </li>
      <li>
        <strong>Building Sub-Structure Identifier:</strong> 
        Unique alphanumeric structural code assigned to each multi-storey tower (e.g. <code>HSTL01</code>, <code>ACAD01</code>, <code>TOWER_A</code>).
      </li>
      <li>
        <strong>Property Natural Identifier Unit (PNIU) in 3D:</strong> 
        Derived from the exact volumetric bounds (X, Y, Z_min, Z_max), vertical floor index (F1 to FN), unit designation, and zoning type:
        <div style="background:#f1f5f9; padding:8px 12px; border-radius:6px; font-family:'JetBrains Mono', monospace; font-size:12px; margin:6px 0; border:1px solid #cbd5e1;">
          3D_ULPIN = &lt;SURFACE_ULPIN&gt; - &lt;BUILDING_ID&gt; - &lt;FLOOR&gt; - &lt;UNIT_ID&gt; - &lt;TYPE&gt;<br>
          <strong style="color:#003366;">Active Example: MH-NGP-IIITN-2026-HSTL01-F3-304-4S</strong>
        </div>
      </li>
    </ol>

    <h2 class="section-h2">Key Benefits of 3D Volumetric Cadastre</h2>
    <ul class="benefit-list">
      <li><strong>Defines Unambiguous Vertical Ownership:</strong> Establishes clear volumetric titles for multi-storey residential and commercial flats, preventing conflicting ownership claims.</li>
      <li><strong>Underground & Subsurface Infrastructure:</strong> Uniquely registers basement parking bays, subterranean water sumps, electrical transformer units, and metro utility easements in negative elevation space.</li>
      <li><strong>Intelligent 3D Topology Validation:</strong> Automated computational geometry audits verify zero spatial collisions (0.00 sqm overlap) before registration.</li>
      <li><strong>Seamless Property Governance:</strong> Integrates with state land record portals (e-Dharti, Bhoomi, Dharani, NGDRS) for streamlined property tax assessment and title conveyance.</li>
      <li><strong>Urban Disaster & Utility Planning:</strong> Provides high-precision volumetric models for fire-safety compliance and urban spatial analytics.</li>
    </ul>
  </div>

  <!-- Right Column: Live Embedded 3D Volumetric Digital Twin -->
  <div class="cadastre-col">
    <div class="cadastre-header">
      <h3>Live 3D Cadastral Digital Twin</h3>
    </div>

    <!-- 3D Controls -->
    <div class="cadastre-controls">
      <div class="search-row">
        <input type="text" id="liveSearchInp" class="search-inp" placeholder="Search 3D ULPIN or Unit (e.g. 304, 1001)..." onkeyup="handleLiveSearch(event)">
        <button class="btn-search" onclick="executeSearch()">Find</button>
      </div>

      <div style="display:flex; justify-content:space-between; align-items:center; font-size:11px;">
        <strong>Floor Level:</strong>
        <span id="activeFloorLabel" style="color:#2563eb; font-weight:700;">All 10 Floors (700 Parcels)</span>
      </div>

      <div class="floor-btn-row">
        <button class="f-btn active" onclick="sliceLiveFloor('all')">All</button>
        <button class="f-btn" onclick="sliceLiveFloor(1)">F1</button>
        <button class="f-btn" onclick="sliceLiveFloor(2)">F2</button>
        <button class="f-btn" onclick="sliceLiveFloor(3)">F3</button>
        <button class="f-btn" onclick="sliceLiveFloor(4)">F4</button>
        <button class="f-btn" onclick="sliceLiveFloor(5)">F5</button>
        <button class="f-btn" onclick="sliceLiveFloor(6)">F6</button>
        <button class="f-btn" onclick="sliceLiveFloor(7)">F7</button>
        <button class="f-btn" onclick="sliceLiveFloor(8)">F8</button>
        <button class="f-btn" onclick="sliceLiveFloor(9)">F9</button>
        <button class="f-btn" onclick="sliceLiveFloor(10)">F10</button>
      </div>
    </div>

    <!-- Embedded Plotly 3D Canvas -->
    <div class="viewer-3d-wrap">
      __PLOT_DIV_PLACEHOLDER__
    </div>

    <!-- Live Title Card -->
    <div class="title-card">
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <strong id="cardUlpinText" style="font-family:'JetBrains Mono', monospace; color:#003366; font-size:13px;">HSTL01-F1-101-4S</strong>
        <span style="background:#d1fae5; color:#065f46; padding:2px 6px; border-radius:4px; font-size:10.5px; font-weight:700;">Topologically Valid</span>
      </div>

      <div class="title-card-grid">
        <div class="title-item">
          <span>UNIT NUMBER</span>
          <strong id="cardUnitText">Unit 101 (4S)</strong>
        </div>
        <div class="title-item">
          <span>VERTICAL LEVEL</span>
          <strong id="cardLevelText">Floor 1 (0.0m - 2.9m)</strong>
        </div>
        <div class="title-item">
          <span>CARPET AREA</span>
          <strong id="cardAreaText">29.48 m²</strong>
        </div>
        <div class="title-item">
          <span>OWNER / ALLOTMENT</span>
          <strong id="cardOwnerText">BT_ID_JOHN (1/4 Cap)</strong>
        </div>
      </div>
    </div>

  </div>

</div>

<!-- Official Footer -->
<footer>
  <ul class="footer-links">
    <li><a href="#">Feedback</a></li>
    <li><a href="#">Website Policies</a></li>
    <li><a href="#">Contact Us</a></li>
    <li><a href="#">Web Information Manager</a></li>
    <li><a href="#">Institutional Memory</a></li>
  </ul>
  <div class="footer-copy">
    Content Owned by <strong>Department of Land Resources, Ministry of Rural Development</strong>.<br>
    Developed and hosted by <strong>National Informatics Centre (NIC)</strong>, Ministry of Electronics & Information Technology, Government of India.
  </div>
</footer>

<script>
  const traceMeta = __TRACE_META_PLACEHOLDER__;

  function sliceLiveFloor(fl) {
    const plotDiv = document.getElementsByClassName('plotly-graph-div')[0];
    if (!plotDiv) return;

    document.querySelectorAll('.f-btn').forEach(btn => {
      btn.classList.remove('active');
      if (btn.textContent.toLowerCase() === (fl === 'all' ? 'all' : 'f' + fl)) {
        btn.classList.add('active');
      }
    });

    document.getElementById('activeFloorLabel').textContent = (fl === 'all') ? 'All 10 Floors (700 Parcels)' : 'Level ' + fl + ' Only';

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

    // Dynamically update Title Card to the selected floor's first unit
    if (fl === 'all') {
      const firstUnit = traceMeta[0];
      if (firstUnit) updateCardWithUnit(firstUnit);
    } else {
      const floorUnit = traceMeta.find(m => m.floor === parseInt(fl));
      if (floorUnit) updateCardWithUnit(floorUnit);
    }
  }

  function updateCardWithUnit(target) {
    if (!target) return;
    document.getElementById('cardUlpinText').textContent = target.ulpin;
    document.getElementById('cardUnitText').textContent = 'Unit ' + target.room_id + ' (' + target.type + ')';
    document.getElementById('cardLevelText').textContent = 'Floor ' + target.floor + ' (' + target.z_min + 'm - ' + target.z_max + 'm)';
    document.getElementById('cardAreaText').textContent = target.area_sqm + ' m²';
    
    const occ = (target.occupants && target.occupants.length > 0) ? target.occupants.join(', ') + ' (' + target.occupants.length + '/' + target.capacity + ')' : 'Vacant (0/' + target.capacity + ')';
    document.getElementById('cardOwnerText').textContent = occ;
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
            updateCardWithUnit(traceMeta[traceIdx]);
          }
        }
      });
    }
  });

  function handleLiveSearch(e) {
    if (e.key === 'Enter') {
      executeSearch();
    }
  }

  function executeSearch() {
    const val = document.getElementById('liveSearchInp').value.trim().toUpperCase();
    if (!val) return;

    const target = traceMeta.find(m => m.ulpin.includes(val) || m.room_id === val || m.room_id.includes(val));
    if (!target) {
      alert('3D ULPIN / Unit "' + val + '" not found in active building registry.');
      return;
    }

    sliceLiveFloor(target.floor);
    updateCardWithUnit(target);
  }
</script>

</body>
</html>
"""

    final_html = template.replace("__PLOT_DIV_PLACEHOLDER__", plot_div).replace("__TRACE_META_PLACEHOLDER__", trace_meta_json)
    output_path = "frontend/index.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_html)

    print(f"✅ Clean Official DoLR Landing Page successfully generated at: {output_path}")

if __name__ == "__main__":
    build_dolr_official_page()
