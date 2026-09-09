 🏛️ National 3D ULPIN & Volumetric Cadastre Platform
### Smart India Hackathon (SIH) — PS 26011 | Ministry of Rural Development — Department of Land Resources (DoLR)
**Category:** Software | **Theme:** Smart Automation | **Cadastral Standard:** ISO 19152 LADM v2 & Maharashtra Land Revenue (Survey 140/1)

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI%200.110+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![SQLite Spatial](https://img.shields.io/badge/Database-SQLite%203D%20Cadastre-003B57.svg?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![ISO 19152](https://img.shields.io/badge/Cadastral%20Standard-ISO%2019152%20LADM%20v2-blue.svg)](https://www.iso.org/standard/51206.html)
[![Plotly 3D](https://img.shields.io/badge/Digital%20Twin-WebGL%20Plotly-orange.svg?logo=plotly&logoColor=white)](https://plotly.com/)
[![Three.js](https://img.shields.io/badge/3D%20Studio-Three.js%20WebGL-black.svg?logo=three.js&logoColor=white)](https://threejs.org/)
[![Shapely](https://img.shields.io/badge/Topology%20Engine-Shapely%202.0-green.svg)](https://shapely.readthedocs.io/)
[![OpenCV](https://img.shields.io/badge/Computer%20Vision-OpenCV%204.8+-5C3EE8.svg?logo=opencv&logoColor=white)](https://opencv.org/)
[![scikit-learn](https://img.shields.io/badge/ML-scikit--learn%201.6+-F7931E.svg?logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📌 Executive Summary

Traditional cadastral systems in India rely on **2D land parcel identifiers (ULPIN / Bhu-Aadhaar)**. While 2D parcel identification works for surface land plots, it fails in dense multi-storey urban structures where multiple distinct ownership rights, residential apartments, utility conduits, and commercial airspace units are stacked vertically over the exact same $(X, Y)$ ground coordinates.

This repository delivers an **enterprise multi-building, multi-tenant 3D Cadastral System** conforming to the international **ISO 19152 LADM v2** standard and the **Department of Land Resources (DoLR)** national framework:
- **Verified Government Land Record Georeferencing**: Aligned with the official Government of Maharashtra Bhunaksha / Mahabhulekh record: **Survey No. 140/1**, **Khata No. 341**, **Waranga (वारंगा)**, **Nagpur Rural**, with State Parcel ID **`pu-id: 33550994106`** under State Government (*Sarkar*) tenure.
- **Genuine 16-Digit 3D ULPIN Standard**: Every individual volumetric entity is assigned an immutable 16-digit identifier that directly inherits the 11-digit 2D land parcel ID, followed by building, floor, and unit coordinates (`3355099410630712`).
- **2 Core Production Endpoints**:
  1. **`/app` — National 3D ULPIN Cadastral Management System**: Official Mahabhulekh cascading search (District $\rightarrow$ Taluka $\rightarrow$ Village $\rightarrow$ Survey No.), live WebGL 3D twin with synchronized hover title inspection, and ISO 19152 LADM v2 strata mutation console.
  2. **`/studio` — 3D Cadastre Studio & AI Extrusion Workstation**: Ingests architectural floor plans (PNG, JPG, CAD PDF), runs OpenCV wall segmentation and vector contour detection, extrudes multi-storey 3D structures, computes Undivided Land Share ($\text{UDS}$), and exports OBJ models & cadastral registries.
- **Computational Geometry & Topology Validation**: Enforces zero spatial collisions ($A \cap B = \emptyset$), $Z$-interval airspace isolation, statutory carpet area checks, and 100% identifier uniqueness using **Shapely 2.0**.
- **Anti-Fraud Rights, Restrictions & Responsibilities (RRR) Ledger**: Prevents overcrowding via statutory capacity limits, locks inalienable common elements (corridors, lifts, stairs), and blocks conveyances on encumbered units with active bank mortgage liens.

---

## 🏛️ System Architecture

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 NATIONAL 3D ULPIN CADASTRAL PLATFORM                                  │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                        │
│  [ CLIENT WORKSTATION INTERFACES ]                                                                     │
│  │                                                                                                     │
│  ├── /app  ──► National Cadastral System                                                               │
│  │   ├── Mahabhulekh Cascading Search (District -> Taluka -> Village -> Survey/Gat No.)                │
│  │   ├── 4-Building Estate Selector (Admin, Academic, Hostel Block A, Residential)                     │
│  │   ├── Plotly WebGL 3D Digital Twin (Real-Time Hover Inspection & Floor Filtering)                   │
│  │   ├── Cadastral Title Record (16-digit 3D ULPIN, Bhu-Aadhaar 3D Unit Card, Dimensions, UDS)        │
│  │   └── Strata Mutation Console (Primary Allotment, Conveyance Transfer, Bank Mortgage Stamping)     │
│  │                                                                                                     │
│  └── /studio ──► 3D Cadastre Studio & AI Extrusion Workstation                                         │
│      ├── Multi-Format Blueprint Ingestion (PNG, JPG, Vector CAD PDF)                                   │
│      ├── OpenCV Wall Segmentation & Contour Vectorization                                              │
│      ├── Three.js WebGL 3D Interactive Canvas (Exploded Floors, Wireframe, Camera Orbit)               │
│      ├── Automated 16-Digit 3D ULPIN Generation & Undivided Land Share (UDS) Calculation               │
│      └── Cadastre Registry Export (OBJ 3D Mesh, Unity JSON, CSV Registry, Print Title Deed)            │
│                                                                                                        │
│                                      │                                                                 │
│                                      ▼ REST JSON / OpenAPI                                             │
│  [ FASTAPI CADASTRAL REST BACKEND (backend/main.py) ]                                                  │
│  ├── /api/institutions     ──► Campus Estate Registry & Bhunaksha Parcel Lineage                       │
│  ├── /api/buildings        ──► Building Profiles, Georeferenced Anchors & Survey Readiness             │
│  ├── /api/parcels          ──► 3D Spatial Queries, Mesh Streaming & Volumetric Metadata                │
│  ├── /api/rights           ──► ISO 19152 LADM v2 Strata Allotment & Title Transfer                     │
│  ├── /api/encumbrances     ──► Bank Mortgage Liens, Sanction Tracking & Conveyance Lockout             │
│  ├── /api/topology         ──► Shapely 2.0 3D Spatial Collision Audit & Compliance Reporting           │
│  ├── /api/analytics        ──► Estate-wide Area, Airspace Volume & Financial Metrics                   │
│  ├── /api/ingestion        ──► Surveyor Architectural Upload & Rule-Based Parsing                      │
│  └── /api/ai               ──► Hybrid AI Floor Plan Extrusion, Mesh Export & YOLO Classifier           │
│                                                                                                        │
│                                      │                                                                 │
│                                      ▼                                                                 │
│  [ COMPUTATIONAL ENGINES & GEOSPATIAL PIPELINE ]                                                       │
│  ├── cadastral_engine.py   ──► Vector CAD Parser & 3D Volumetric Extrusion Pipeline                    │
│  ├── floorplan_3d_ml.py    ──► Multi-Storey Floor Plan Extrusion, UDS Calculator & OBJ Generator       │
│  ├── topology_validator.py ──► 3D Bounding Box & Polygon Intersection Geometry (Shapely 2.0)           │
│  ├── rights_manager.py     ──► Anti-Fraud Strata Conveyance, Lien Registry & Audit Logging             │
│  ├── cv_extractor.py       ──► OpenCV Adaptive Thresholding, Morphological Wall Filtering & OCR        │
│  └── pointcloud_validator  ──► Drone Photogrammetry ML Height Verification (scikit-learn DBSCAN)      │
│                                                                                                        │
│                                      │                                                                 │
│                                      ▼                                                                 │
│  [ SPATIAL RELATIONAL DATABASE (data/cadastre_3d.db) ]                                                 │
│  ├── institutions          ──► Survey 140/1, Khata 341, Waranga, pu-id: 33550994106                    │
│  ├── buildings             ──► ADMIN01, ACAD01, HSTL01 (700 units), RES01                              │
│  ├── parcels_3d            ──► 700 Verified 16-Digit Volumetric Parcels (WGS84, UDS, Z-Limits)         │
│  ├── parties               ──► Citizen & Institutional Titleholders (Aadhaar Masked)                   │
│  ├── strata_titles         ──► Active Strata Freehold, Leasehold & Statutory Capacity Records          │
│  ├── encumbrances          ──► Active Bank Mortgage Liens (NOC Lock Protocol)                          │
│  └── mutation_audit_log    ──► Immutable Audit Trail for Conveyance & Mortgage Events                  │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🏷️ The 16-Digit 3D ULPIN Standard

The core purpose of 3D ULPIN is to establish an unbroken, traceable lineage from the **2D base surface land parcel** to every vertically stacked **3D private room or common airspace unit**.

Every 3D volumetric entity is assigned a **16-digit numerical ULPIN**:

$$\underbrace{\mathbf{33550994106}}_{\text{11-digit 2D Land Parcel (Survey 140/1)}} \;+\; \underbrace{\mathbf{3}}_{\text{1-digit Building}} \;+\; \underbrace{\mathbf{FL}}_{\text{2-digit Floor (01--10)}} \;+\; \underbrace{\mathbf{UN}}_{\text{2-digit Unit Sequence}} \;=\; \mathbf{16\text{ Digits}}$$

```
  33550994106       -       3       -       07       -       12       =  3355099410630712
 └───────────┘             └───┘           └───┘            └───┘
  11-digit 2D               1-digit         2-digit          2-digit
  Base Land Parcel          Building Code   Floor Level      Unit Sequence
  (Waranga Survey 140/1)    (Hostel Block)  (Floor 7)        (Unit 12)
```

### Breakdown of Identifiers

| Component | Digits | Purpose | Example |
| :--- | :---: | :--- | :--- |
| **2D Land Parcel (`pu-id`)** | 11 | Direct reference to the parent Maharashtra Bhunaksha / Mahabhulekh parcel | `33550994106` |
| **Building Digit** | 1 | Numeric building code within campus estate (`1`=Admin, `2`=Acad, `3`=Hostel, `4`=Res) | `3` (Hostel Block A) |
| **Floor Level** | 2 | Zero-padded vertical level index (`01` to `10`) | `07` (Level 7), `10` (Level 10) |
| **Unit Sequence** | 2 | Unique unit index (`01`–`56` private rooms, `71`–`97` common transit cores) | `12` (Unit 712), `04` (Unit 1004) |
| **Full 3D ULPIN** | **16** | **100% unique primary key for the volumetric unit** | **`3355099410630712`** |

### Mathematical Fractional Undivided Land Share ($\text{UDS}$) Calculus
Every vertical 3D unit is legally and mathematically linked to equity in the underlying 2D surface plot:
$$\text{UDS}_i = \left( \frac{\text{Carpet Area}_i}{\sum_{k=1}^N \text{Carpet Area}_k} \right) \times A_{\text{surface}}$$

---

## 🖥️ The Two Core Endpoints

The web application exposes two dedicated endpoints:

```
                  ┌──────────────────────────────────────────────┐
                  │            http://127.0.0.1:8000/            │
                  │             (Redirects to /app)              │
                  └──────────────────────┬───────────────────────┘
                                         │
                    ┌────────────────────┴────────────────────┐
                    ▼                                         ▼
   ┌─────────────────────────────────┐       ┌─────────────────────────────────┐
   │              /app               │       │             /studio             │
   │   National 3D ULPIN Cadastre    │       │     3D AI Extrusion Studio      │
   │  -----------------------------  │       │  -----------------------------  │
   │  • Mahabhulekh Cascading Search │       │  • Blueprint Upload (PNG/CAD)   │
   │  • 4 Campus Building Selector   │       │  • OpenCV Edge/Contour AI       │
   │  • WebGL 3D Digital Twin        │       │  • Parametric Multi-Storey 3D   │
   │  • Real-Time Hover Inspector    │       │  • Three.js Interactive Viewer  │
   │  • Strata Title Mutation Ledger │       │  • OBJ / Unity / CSV Export     │
   │  • Bank Mortgage Lien Stamping  │       │  • Printable Title Certificate  │
   └─────────────────────────────────┘       └─────────────────────────────────┘
```

### 1. `/app` — National 3D ULPIN Cadastral Management System
The `/app` endpoint provides an authentic land administration portal modeled on the Department of Land Resources (DoLR) and Maharashtra Land Revenue standards:

1. **Step 1: Mahabhulekh / Bhunaksha 3D Cadastre Search**:
   - **District (जिल्हा)**: Cascading dropdown with 23 Maharashtra districts (`Nagpur (नागपूर)` on top and pre-selected).
   - **Taluka (तालुका)**: Cascading dropdown with 14 Nagpur talukas (`Nagpur Rural (नागपूर ग्रामीण)` on top and pre-selected).
   - **Village (गाव)**: Cascading dropdown with 38 villages (`Waranga (वारंगा)` on top and pre-selected).
   - **Survey / Gat No. (गट क्र.)**: Free-text editable input (`140/1` pre-filled).
   - **One-Click Resolution**: Clicking **Search 3D Cadastral Record** resolves the record to `Survey 140/1 (pu-id: 33550994106)` and smoothly transitions to the 3D twin workspace.

2. **Step 2: 3D Stratum Inspection Workspace**:
   - **4-Building Selector Cards**: Inspect **Admin Building (`ADMIN01`)**, **Academic Building (`ACAD01`)**, **Hostel Block A (`HSTL01`)**, or **Residential Building (`RES01`)**.
   - **WebGL 3D Twin Viewport (Plotly.js)**:
     - Real-time synchronized hover (`plotly_hover`) and click (`plotly_click`) inspection.
     - Controls for Floor Isolation (All 10 Floors or individual levels 1–10) and Zoning Filter (All 700 units, Residential 560, Common Core 140).
     - Color-coded zoning: green = vacant, amber = partially occupied, red = fully occupied, slate blue = common corridors, transit slate = stairs/lifts, teal = washrooms.
   - **Cadastral Title Record (Bhu-Aadhaar 3D Unit Card)**:
     - **Spatial Identification**: 16-digit 3D ULPIN, 2D Base Parcel (`33550994106`), Unit Designation, Classification (`4S / 2S Private Stratum` or `Common Property`), Vertical Level ($Z_{min}$ to $Z_{max}$).
     - **Dimensions & Land Equity**: RERA Carpet Area ($m^2$), Enclosed Airspace Volume ($m^3$), Undivided Land Share ($\text{UDS}$ % of surface), Centroid GPS Coordinates (WGS84).
     - **Rights & Titleholders**: Registered citizens, right type (`STRATA_FREEHOLD`, `ALLOTMENT`), capacity limit tracking.
     - **Encumbrance & Lien Registry**: Real-time bank mortgage lien status with anti-fraud conveyance lockout.
   - **Cadastral Actions (Mutation Console)**:
     - Allot citizen to private stratum unit.
     - Strata title conveyance transfer (validates lien status before permitting transfer).
     - Bank mortgage lien stamping and release.

---

### 2. `/studio` — 3D Cadastre Studio & AI Extrusion Workstation
The `/studio` endpoint enables surveyors, town planners, and citizens to convert any 2D architectural blueprint into an extruded, georeferenced 3D volumetric cadastre:

```
  ┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
  │  2D Floor Plan  │  ──►  │ OpenCV Wall &   │  ──►  │ Parametric 3D   │
  │  PNG / JPG / CAD│       │ Contour Vector  │       │ Multi-Storey    │
  └─────────────────┘       └─────────────────┘       └─────────────────┘
                                                               │
                                                               ▼
  ┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
  │  Export & Print │  ◄──  │ ISO 19152 LADM  │  ◄──  │ Three.js WebGL  │
  │  OBJ/CSV/Deed   │       │ 16-Digit ULPINs │       │ 3D Orbit Viewer │
  └─────────────────┘       └─────────────────┘       └─────────────────┘
```

1. **Blueprint Ingestion**:
   - Accepts PNG, JPG, or vector CAD PDF uploads.
   - Includes 5 pre-loaded sample architectural blueprints (2BHK flat, multi-unit floor plan, CAD vector plan, hostel block, residential floor plan).
2. **Computer Vision & Wall Extraction Engine**:
   - Adaptive bilateral filtering + Otsu thresholding for wall boundary isolation.
   - Morphological closing to bridge wall line gaps.
   - Hierarchy contour extraction to separate private residential boundaries from common corridors.
3. **Parametric 3D Extrusion Engine**:
   - Configurable floor count (1 to 25 floors).
   - Configurable wall clear height (1.0m to 6.0m) and structural slab thickness (0.25m to 0.50m).
   - Automatic floor-to-floor $Z$-elevation stacking ($Z_{min} = (fl - 1) \times H$, $Z_{max} = Z_{min} + H_{wall}$).
4. **Interactive Three.js WebGL Viewport**:
   - Full 3D orbit controls (rotate, pan, zoom).
   - **Exploded View Slider**: Dynamically expands floors vertically along the $Z$-axis to inspect internal layouts.
   - **Floor Level Isolation**: Select and inspect any individual floor level.
   - **Wireframe Mode Toggle**: Switch between solid volumetric mesh and wireframe structural outlines.
5. **Automated Cadastral Registry & UDS Calculus**:
   - Auto-generates the 16-digit 3D ULPIN (`335509941061{floor}{unit}`) for each unit.
   - Computes RERA carpet area, airspace volume, and Undivided Share of Land ($\text{UDS}$) in $m^2$ and %.
6. **Multi-Format Export Actions**:
   - **Download Wavefront `.OBJ` 3D Mesh**: Ready for Autodesk Revit, Blender, or GIS software.
   - **Export Unity Client JSON**: Direct integration with Unity / Unreal 3D visualization engines.
   - **Download Cadastral CSV Registry**: Complete tabular dataset of all units and metadata.
   - **Print Bhu-Aadhaar 3D Title Deed**: Generates official Government of Maharashtra Certificate of 3D Strata Freehold Title.

---

## 🔧 Complete Technology Stack

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                   TECHNOLOGY STACK                                     │
├────────────────────────────────────────────────────────────────────────────────────────┤
│  FRONTEND PRESENTATION TIER                                                            │
│  ├── HTML5 & CSS3           Modern government UI design system (Mahabhulekh aesthetic)  │
│  ├── ES6+ Vanilla JS        Zero-framework, high-performance DOM & async REST API      │
│  ├── Plotly.js 5.18+ (WebGL) Hardware-accelerated 3D mesh rendering for /app twin     │
│  └── Three.js (WebGL)       Interactive 3D orbit, exploded floor view & wireframe for /studio│
├────────────────────────────────────────────────────────────────────────────────────────┤
│  BACKEND REST API TIER                                                                 │
│  ├── Python 3.9+            Core backend runtime environment                           │
│  ├── FastAPI 0.110+         High-performance asynchronous REST API framework           │
│  ├── Uvicorn 0.28+          Lightning-fast ASGI production server                      │
│  ├── Pydantic v2            Strict data validation & serialization schemas             │
│  └── python-multipart       Multipart form parsing for architectural file uploads      │
├────────────────────────────────────────────────────────────────────────────────────────┤
│  AI, COMPUTER VISION & COMPUTATIONAL GEOMETRY TIER                                     │
│  ├── OpenCV 4.8+            Wall segmentation, contour detection, morphological filters│
│  ├── PyMuPDF (fitz) 1.24+   Native vector CAD PDF drawing path & text parser           │
│  ├── Tesseract OCR          Optical character recognition for scanned room numbers     │
│  ├── Shapely 2.0+ (GEOS)    Computational geometry: 3D bounding box & polygon overlaps│
│  ├── scikit-learn 1.6+      DBSCAN clustering for drone photogrammetry floor heights   │
│  └── scipy 1.13+            Signal processing & peak detection for Z-density histograms│
├────────────────────────────────────────────────────────────────────────────────────────┤
│  DATA PERSISTENCE & GIS TIER                                                           │
│  ├── SQLite 3 (Spatial)     Relational database with FK constraints & spatial indexes  │
│  ├── pyproj 3.6+            WGS84 EPSG:4326 geodetic coordinate transformations       │
│  └── Pandas 2.0+            High-throughput tabular cadastral processing               │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### Detailed Component Matrix

| Tier | Technology | Version | Purpose in 3D ULPIN | Key Implementation File |
| :--- | :--- | :--- | :--- | :--- |
| **Web Server** | **FastAPI** | `0.110+` | Async REST routing, OpenAPI documentation, static file serving | [backend/main.py](file:///Users/adityasingh/3D_UPLIN_SIH/backend/main.py) |
| **ASGI Engine** | **Uvicorn** | `0.28+` | Production asynchronous runtime with hot reloading | `backend.main:app` |
| **Database** | **SQLite 3** | Built-in | Relational spatial storage (7 tables, ACID transactions, indexes) | [data/cadastre_3d.db](file:///Users/adityasingh/3D_UPLIN_SIH/data/cadastre_3d.db) |
| **Validation** | **Pydantic** | `2.6+` | Data schemas for cadastral parcels, strata titles, encumbrances | [backend/models.py](file:///Users/adityasingh/3D_UPLIN_SIH/backend/models.py) |
| **Topology** | **Shapely** | `2.0+` | Polygon intersection ($A \cap B$), boundary verification, 0-collision audit | [backend/services/topology_validator.py](file:///Users/adityasingh/3D_UPLIN_SIH/backend/services/topology_validator.py) |
| **Vision** | **OpenCV** | `4.8+` | Floor plan thresholding, wall extraction, contour vectorization | [backend/services/cv_extractor.py](file:///Users/adityasingh/3D_UPLIN_SIH/backend/services/cv_extractor.py) |
| **CAD Parser** | **PyMuPDF** | `1.24+` | Vector PDF geometry parser for architectural blueprints | [backend/services/vector_extractor.py](file:///Users/adityasingh/3D_UPLIN_SIH/backend/services/vector_extractor.py) |
| **OCR** | **pytesseract**| `0.3.10+` | Text recognition for room labels from scanned floor plans | [backend/services/cv_extractor.py](file:///Users/adityasingh/3D_UPLIN_SIH/backend/services/cv_extractor.py) |
| **Machine Learning**| **scikit-learn**| `1.6+`| DBSCAN clustering to detect building floors from LiDAR points | [backend/services/pointcloud_validator.py](file:///Users/adityasingh/3D_UPLIN_SIH/backend/services/pointcloud_validator.py) |
| **Signal Processing**| **scipy** | `1.13+` | Peak detection on point cloud elevation histograms | [backend/services/pointcloud_validator.py](file:///Users/adityasingh/3D_UPLIN_SIH/backend/services/pointcloud_validator.py) |
| **3D Twin** | **Plotly.js** | `5.18+` | Hardware-accelerated WebGL mesh rendering on `/app` | [frontend/app.js](file:///Users/adityasingh/3D_UPLIN_SIH/frontend/app.js) |
| **3D Studio** | **Three.js** | `r128` | Interactive 3D orbit canvas, wireframe, exploded view on `/studio` | [frontend/floorplan_3d_studio.html](file:///Users/adityasingh/3D_UPLIN_SIH/frontend/floorplan_3d_studio.html) |
| **Geodesy** | **pyproj** | `3.6+` | Local CAD meters $\leftrightarrow$ WGS84 GPS coordinates (EPSG:4326) | [backend/services/cadastral_engine.py](file:///Users/adityasingh/3D_UPLIN_SIH/backend/services/cadastral_engine.py) |

---

## 🗄️ Relational Database Schema

The spatial database (`data/cadastre_3d.db`) comprises **7 normalized tables**:

```
┌─────────────────────────────────┐       ┌─────────────────────────────────┐
│          institutions           │       │            buildings            │
├─────────────────────────────────┤       ├─────────────────────────────────┤
│ institution_id (PK)             │1     N│ building_id (PK)                │
│ institution_name                ├──────►│ institution_id (FK)             │
│ state_parcel_id_puid            │       │ building_name                   │
│ survey_number                   │       │ category                        │
│ village, taluka, district       │       │ data_status                     │
│ campus_anchor_lat / lon         │       │ total_floors, floor_pitch_m     │
│ total_plot_area_sqm             │       │ room_clear_height_m             │
└─────────────────────────────────┘       └────────────────┬────────────────┘
                                                           │ 1
                                                           │
                                                           │ N
                                          ┌────────────────▼────────────────┐
                                          │           parcels_3d            │
                                          ├─────────────────────────────────┤
                                          │ ulpin_3d (PK) [16-digit unique] │
                                          │ building_id (FK)                │
                                          │ floor, room_id, type            │
                                          │ z_min, z_max, z_slab_top        │
                                          │ real_width_m, real_depth_m      │
                                          │ latitude, longitude (WGS84)     │
                                          │ carpet_area_sqm                 │
                                          │ gross_volume_cbm                │
                                          │ undivided_share_land (UDS)      │
                                          │ is_common_property (0/1)        │
                                          └───────┬─────────────────┬───────┘
                                                  │ 1               │ 1
                                                  │                 │
                                                  │ N               │ N
                    ┌─────────────────────────────▼─┐     ┌─────────▼─────────────────────┐
                    │         strata_titles         │     │         encumbrances          │
                    ├───────────────────────────────┤     ├───────────────────────────────┤
                    │ title_id (PK)                 │     │ encumbrance_id (PK)           │
                    │ ulpin_3d (FK)                 │     │ ulpin_3d (FK)                 │
                    │ party_id (FK)                 │     │ encumbrance_type              │
                    │ right_type                    │     │ mortgagee_name                │
                    │ status (ACTIVE/TRANSFERRED)   │     │ sanction_reference (UK)       │
                    │ max_capacity                  │     │ loan_amount_inr               │
                    └───────────────┬───────────────┘     │ status (ACTIVE/RELEASED)      │
                                    │ N                   └───────────────────────────────┘
                                    │
                                    │ 1
                    ┌───────────────▼───────────────┐     ┌───────────────────────────────┐
                    │            parties            │     │      mutation_audit_log       │
                    ├───────────────────────────────┤     ├───────────────────────────────┤
                    │ party_id (PK)                 │     │ tx_id (PK)                    │
                    │ name                          │     │ ulpin_3d (FK)                 │
                    │ party_type                    │     │ tx_type                       │
                    │ aadhaar_masked                │     │ from_party, to_party          │
                    │ is_simulated                  │     │ details, timestamp            │
                    └───────────────────────────────┘     └───────────────────────────────┘
```

---

## 🚀 Step-by-Step Execution Guide

### Prerequisites
- **Python 3.9+** (`python3 --version`)
- **pip** package installer (`pip --version`)
- **Git** (`git --version`)
- *(Optional)* **Tesseract OCR** for scanned image extraction:
  - macOS: `brew install tesseract`
  - Ubuntu/Debian: `sudo apt update && sudo apt install -y tesseract-ocr`

---

### Step 1: Clone the Repository
```bash
git clone https://github.com/adiscripts03/3D_UPLIN_SIH.git
cd 3D_UPLIN_SIH
```

---

### Step 2: Set Up Virtual Environment
```bash
# Create virtual environment
python3 -m venv ulpin_env

# Activate on macOS / Linux:
source ulpin_env/bin/activate

# Activate on Windows (cmd.exe):
# ulpin_env\Scripts\activate.bat

# Activate on Windows (PowerShell):
# ulpin_env\Scripts\Activate.ps1
```

---

### Step 3: Install Required Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

### Step 4: Seed the 3D Cadastre Database
This command initializes `data/cadastre_3d.db` and loads the verified Bhunaksha Survey 140/1 data, 4 campus buildings, and all **700 3D volumetric parcels** with **16-digit unique ULPINs**:
```bash
PYTHONPATH=. python backend/seed_data.py
```

Expected output:
```
🚀 Initializing Verified 3D Cadastre Database & Tables...
🧹 Removed previous database file for fresh verified seed.
✅ Real Institution (Survey 140/1, Khata 341, Waranga, pu-id: 33550994106) & 4 Buildings registered.
📦 Loading Genuine Measured 3D Volumetric Parcels from data/room_labels_all_floors_final.csv...
✅ Ingested exactly 700 genuine 3D Volumetric Parcels for Hostel Block A (HSTL01).
👥 Seeding Sample Demonstration Occupancy & Titles (SIMULATED DATA)...
🏦 Seeding Sample Demonstration Mortgage Liens (SIMULATED DATA)...
🎉 Verified 3D Cadastral Database Seeding Completed Successfully!
```

---

### Step 5: Start the FastAPI Application
```bash
PYTHONPATH=. uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

---

### Step 6: Access the Application Endpoints

Open your web browser and navigate to:

| Workstation / Interface | URL | Description |
| :--- | :--- | :--- |
| 📊 **National 3D ULPIN Cadastre** | **[http://127.0.0.1:8000/app](http://127.0.0.1:8000/app)** | Official Mahabhulekh search, 4 campus buildings, live WebGL 3D twin, hover inspection, title mutation |
| 🏢 **3D Cadastre Studio** | **[http://127.0.0.1:8000/studio](http://127.0.0.1:8000/studio)** | Architectural blueprint upload, OpenCV AI wall detection, parametric 3D extrusion, OBJ/CSV export |
| 📖 **Interactive Swagger UI** | **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)** | Test all REST endpoints with live payload validation |
| 📖 **ReDoc API Reference** | **[http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)** | Clean technical OpenAPI specification |
| ❤️ **Health Check** | **[http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)** | Operational status check |

---

## 🧪 Comprehensive API Testing Commands

You can verify all endpoints directly using `curl`:

```bash
# 1. Health check
curl -s http://127.0.0.1:8000/health

# 2. List registered campus estates
curl -s http://127.0.0.1:8000/api/institutions | jq .

# 3. List campus buildings and survey statuses
curl -s http://127.0.0.1:8000/api/buildings | jq .

# 4. Stream 3D mesh bounding boxes for Hostel Block A (700 units)
curl -s http://127.0.0.1:8000/api/parcels/mesh-data/HSTL01 | jq '{total: .total_units, sample: .parcels[0]}'

# 5. Look up specific 16-digit 3D ULPIN (Unit 712 on Floor 7)
curl -s http://127.0.0.1:8000/api/parcels/3355099410630712 | jq .

# 6. Look up specific 16-digit 3D ULPIN (Unit 1004 on Floor 10)
curl -s http://127.0.0.1:8000/api/parcels/3355099410631004 | jq .

# 7. Run 3D topology collision audit
curl -s http://127.0.0.1:8000/api/topology/validate/HSTL01 | jq .

# 8. Allot an occupant to a 3D unit (enforcing statutory capacity)
curl -s -X POST http://127.0.0.1:8000/api/rights/allot \
  -H "Content-Type: application/json" \
  -d '{"ulpin_3d": "3355099410630712", "party_id": "CITIZEN_DEMO_01", "name": "Aditya Singh"}' | jq .

# 9. Stamp a bank mortgage lien against a 3D unit
curl -s -X POST http://127.0.0.1:8000/api/encumbrances/stamp \
  -H "Content-Type: application/json" \
  -d '{"ulpin_3d": "3355099410630712", "mortgagee_name": "State Bank of India", "sanction_reference": "SBI-SANCTION-2026-99", "loan_amount_inr": 5500000}' | jq .

# 10. Attempt conveyance transfer on encumbered unit (automatically blocked!)
curl -s -X POST http://127.0.0.1:8000/api/rights/transfer \
  -H "Content-Type: application/json" \
  -d '{"ulpin_3d": "3355099410630712", "from_party_id": "CITIZEN_DEMO_01", "to_party_id": "BUYER_99", "to_party_name": "New Owner", "price_inr": 7500000}' | jq .
```

---

## 🧪 Automated Testing & Topology Validation

Run the automated integration test suite and computational topology verification:

```bash
# Run integration test suite
PYTHONPATH=. python test_pipeline.py

# Run standalone 3D topology & geometry validation report
PYTHONPATH=. python validate_properties.py
```

Expected validation output:
```
============================================================
  🏢 3D VOLUMETRIC CADASTRE VALIDATION ENGINE
  Total Units: 700 across 10 Floors (Floors 1 to 10)
============================================================

✅ PASSED [Uniqueness]: All 700 16-Digit 3D ULPINs are 100% unique.
✅ PASSED [Area Standards]: All 560 residential units meet statutory minimums.
✅ PASSED [3D Topology]: 0 spatial collisions. Perfect 3D volumetric cadastre integrity.

📊 Summary Breakdown:
   • Total Floors: 10
   • Residential Parcels: 560 (2-Seater & 4-Seater Private Stratum)
   • Common/Transit Parcels: 140 (Corridors, Stairs, Lifts, Washrooms, Halls)
   • 2D Land Parcel Origin: Survey 140/1, Waranga (pu-id: 33550994106)
   • Building Envelope: ~60.0m (W) × 38.8m (D) × 34.0m (H)
============================================================
```

---

## ⚖️ Standards Compliance & Legal Disclaimer

- **ISO 19152 LADM v2 Standard**: Strictly follows international Land Administration Domain Model specifications for `LA_SpatialUnit`, `LA_BAUnit`, `LA_Party`, and `LA_RRR` (Rights, Restrictions, Responsibilities).
- **Government of Maharashtra Cadastral Data**: Base surface cadastre is georeferenced to official Bhunaksha / Mahabhulekh records for **Survey 140/1**, **Khata No. 341**, **Waranga**, **Nagpur Rural**, **State Parcel ID `pu-id: 33550994106`**.
- **Demonstration RRR Notice**: Names, simulated Aadhaar numbers, and demonstration mortgage sanction references are synthetic test data generated solely to demonstrate the mathematical, topological, and legal capabilities of the platform.

---

## 👥 Team & Attribution

- **Institution:** Indian Institute of Information Technology, Nagpur (IIIT Nagpur)
- **Event:** Smart India Hackathon (SIH) 2026
- **Problem Statement:** PS 26011 — 3D ULPIN Generation and Vertical Property Mapping System
- **Nodal Ministry:** Ministry of Rural Development — Department of Land Resources (DoLR), Government of India
- **Repository:** [adiscripts03/3D_UPLIN_SIH](https://github.com/adiscripts03/3D_UPLIN_SIH)

---

<p align="center">
  <b>🏛️ National 3D ULPIN & Volumetric Cadastre Platform</b><br>
  <i>Every room. Every floor. Every right. One 16-digit 3D identity.</i><br><br>
  Built with ❤️ for Smart India Hackathon 2026
</p>
