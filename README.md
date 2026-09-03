# 🏛️ National 3D ULPIN & Volumetric Cadastre Platform
### Smart India Hackathon (SIH) — PS 26011 | Ministry of Rural Development — Department of Land Resources (DoLR)
**Category:** Software | **Theme:** Smart Automation | **Cadastral Standard:** ISO 19152 LADM v2 & Maharashtra Land Revenue (Survey 140/1)

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI%200.110+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![SQLite Spatial](https://img.shields.io/badge/Database-SQLite%203D%20Cadastre-003B57.svg?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![ISO 19152](https://img.shields.io/badge/Cadastral%20Standard-ISO%2019152%20LADM%20v2-blue.svg)](https://www.iso.org/standard/51206.html)
[![Plotly 3D](https://img.shields.io/badge/Digital%20Twin-WebGL%203D%20Mesh-orange.svg?logo=plotly&logoColor=white)](https://plotly.com/)
[![Shapely](https://img.shields.io/badge/Topology%20Engine-Shapely%202.0-green.svg)](https://shapely.readthedocs.io/)
[![OpenCV](https://img.shields.io/badge/Computer%20Vision-OpenCV%204.8+-5C3EE8.svg?logo=opencv&logoColor=white)](https://opencv.org/)
[![scikit-learn](https://img.shields.io/badge/ML-scikit--learn%201.6+-F7931E.svg?logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📌 Executive Summary

Traditional cadastral systems in India rely on **2D land parcel identifiers (ULPIN / Bhu-Aadhaar)**. While 2D parcel identification works for flat agricultural or surface land, it fails in dense multi-storey urban structures where multiple distinct ownership rights, apartments, utility shafts, and commercial units are stacked vertically over the exact same $(X, Y)$ ground coordinates.

This repository delivers an **enterprise multi-building, multi-tenant 3D Cadastral System** conforming to the international **ISO 19152 LADM v2** standard and the **Department of Land Resources (DoLR)** national framework:
- **Verified Government Land Record Georeferencing**: Aligned with the official Government of Maharashtra Bhunaksha / Mahabhulekh record: **Survey No. 140/1**, **Khata No. 341**, **Waranga (वारंगा)**, **Nagpur Rural**, with State Parcel ID **`pu-id: 33550994106`** under State Government (*Sarkar*) tenure.
- **Genuine CAD Extrusion Dataset**: 700 3D volumetric parcels extracted directly from verified architectural vector drawings for **Hostel Block A (`HSTL01`)** across 10 floors ($16,979\text{ m}^2$ carpet area, $49,239.2\text{ m}^3$ airspace volume).
- **4-Building Campus Structure**: Clean 4-building estate layout representing **Admin Building (`ADMIN01`)**, **Academic Building (`ACAD01`)**, **Hostel Block A (`HSTL01`)**, and **Residential Building (`RES01`)** with transparent survey statuses.
- **Intelligent 3D Topology & Geometry Validation Engine**: Performs computational geometry collision audits (`shapely`), verifying $Z$-interval intersections, planar polygon overlaps ($A \cap B$), statutory minimum areas, and primary key uniqueness ($100\%$ compliance score).
- **ISO 19152 LADM v2 RRR Rights & Encumbrance Ledger**: Enforces statutory occupancy caps, locks inalienable common elements (corridors, stairs, washrooms), registers mortgage liens, and automatically blocks fraudulent conveyances on encumbered units (demonstration records clearly badged as simulated).
- **FastAPI RESTful Backend**: Modular REST API with 8 routers handling estate queries, 3D mesh streaming, real-time title mutation, mortgage stamping, spatial analytics, and surveyor data ingestion.
- **Dual-Mode AI Extraction Pipeline**: Auto-detects vector CAD PDFs (PyMuPDF) or scanned images (OpenCV + Tesseract OCR) and extracts room boundaries without manual intervention.
- **Bilingual Official Landing & 3D Digital Twin Portal**: Authentic Department of Land Resources interface with Mahabhulekh-style cascading parcel search and interactive WebGL 3D twin viewer.

---

## ⚡ Key Features at a Glance

| Feature | What It Does | Technology |
|---|---|---|
| 🔍 **Dual-Mode Extraction** | Auto-detects floor plan type (vector CAD or scanned image) and extracts room boundaries | PyMuPDF, OpenCV, Tesseract OCR |
| 🏗️ **3D Volumetric Stacking** | Replicates base floor layout across N floors with precise Z-elevation | Python, math |
| 🏷️ **3D ULPIN Generation** | Assigns every room a unique, standardized spatial identifier | Custom schema engine |
| 🌍 **GPS Georeferencing** | Transforms local CAD coordinates to WGS84 latitude/longitude | pyproj, math |
| ✅ **3D Topology Validation** | Detects spatial collisions between volumetric parcels (0 collisions for 700 units) | Shapely 2.0 (GEOS) |
| ⚖️ **ISO 19152 RRR Engine** | Manages strata titles, allotments, transfers with anti-fraud protections | FastAPI, SQLite |
| 🏦 **Mortgage Lien Registry** | Banks can stamp liens on specific 3D units; blocks illegal resale | rights_manager.py |
| 🌐 **WebGL 3D Digital Twin** | Interactive 3D building viewer with floor filtering and hover inspection | Plotly.js (WebGL) |
| 🤖 **ML Height Validation** | Cross-validates stated floors against drone point cloud data | scikit-learn DBSCAN, scipy |
| 📊 **Cadastral Analytics** | Estate-wide statistics: carpet area, volume, occupancy, encumbrances | SQL aggregation |
| ⚙️ **Config-Driven Onboarding** | Any new building added via JSON config — zero code changes | Pydantic, RuleEngine |

---

## 🔧 Complete Technology Stack

### Backend & API

| Technology | Version | Purpose | Key Files |
|---|---|---|---|
| **Python** | 3.9+ | Core language for all backend, AI/ML, and data processing | All `.py` files |
| **FastAPI** | 0.110+ | Async REST API framework with auto OpenAPI docs | `backend/main.py`, `backend/routers/` |
| **Uvicorn** | 0.28+ | Lightning-fast ASGI server | Runtime |
| **Pydantic** | 2.6+ | Data validation & serialization for API models | `backend/models.py`, `backend/services/cadastral_config.py` |
| **python-multipart** | 0.0.9+ | Multipart form parsing for file uploads | `backend/routers/ingestion.py` |

### Database

| Technology | Version | Purpose | Key Files |
|---|---|---|---|
| **SQLite 3** | Built-in | Zero-config relational spatial database (7 tables, FK constraints, indexes) | `data/cadastre_3d.db` |

### Geospatial & Computational Geometry

| Technology | Version | Purpose | Key Files |
|---|---|---|---|
| **Shapely** | 2.0+ | 3D topology validation — polygon intersection & collision detection (GEOS C backend) | `backend/services/topology_validator.py`, `validate_properties.py` |
| **PyMuPDF (fitz)** | 1.24+ | Vector CAD PDF parsing — extracts drawing paths, rectangles & text labels | `backend/services/vector_extractor.py`, `backend/services/cv_extractor.py` |
| **pyproj** | 3.6+ | Coordinate Reference System (CRS) transformations (EPSG:4326 WGS84) | Available for advanced georeferencing |
| **GeoPandas** | 1.0+ | Spatial data frames for GIS analysis | Available for spatial joins & exports |
| **Pandas** | 2.0+ | Tabular data manipulation & CSV processing | Data pipeline scripts |

### Computer Vision & OCR

| Technology | Version | Purpose | Key Files |
|---|---|---|---|
| **OpenCV** | 4.8+ | Room boundary detection from scanned floor plans (adaptive threshold → contour detection → NMS) | `backend/services/cv_extractor.py` |
| **Tesseract OCR (pytesseract)** | 0.3.10+ | Optical character recognition for extracting room labels from images | `backend/services/cv_extractor.py` |
| **Pillow (PIL)** | 10.0+ | Image format handling & fallback loading | `backend/services/cv_extractor.py` |

### Machine Learning & Scientific Computing

| Technology | Version | Purpose | Key Files |
|---|---|---|---|
| **scikit-learn** | 1.6+ | DBSCAN unsupervised clustering for point cloud floor-level detection | `backend/services/pointcloud_validator.py` |
| **scipy** | 1.13+ | `find_peaks` signal processing for Z-histogram peak detection | `backend/services/pointcloud_validator.py` |
| **NumPy** | (via deps) | Numerical array processing for point cloud & image data | Throughout |
| **laspy** | 2.6+ | LiDAR / LAS point cloud file format reader | `backend/services/pointcloud_validator.py` |

### 3D Visualization & Frontend

| Technology | Version | Purpose | Key Files |
|---|---|---|---|
| **Plotly.js** | 5.18+ | WebGL hardware-accelerated 3D mesh rendering (Mesh3d, Scatter3d) | `visualize_3d.py`, `frontend/app.js` |
| **HTML5 / CSS3** | — | Bilingual (EN/HI) DoLR-style government portal UI | `frontend/index_en.html`, `frontend/index_hi.html`, `frontend/app.css` |
| **Vanilla JavaScript** | ES6+ | API integration, dynamic 3D twin construction, DOM manipulation | `frontend/app.js` |

### DevOps & Tooling

| Technology | Purpose |
|---|---|
| **Git / GitHub** | Version control & collaboration ([adiscripts03/3D_UPLIN_SIH](https://github.com/adiscripts03/3D_UPLIN_SIH)) |
| **pip + venv** | Python dependency management & virtual environments |
| **Swagger UI** | Auto-generated interactive API documentation at `/docs` |
| **ReDoc** | Alternative API documentation at `/redoc` |

---

## 📂 Project Structure

```
3D_ULPIN/
│
├── backend/                          # ── FastAPI Backend Application ──
│   ├── main.py                       # FastAPI app init, CORS, 8 routers, static mounts
│   ├── database.py                   # SQLite connection manager, 7 CREATE TABLE statements
│   ├── models.py                     # 10 Pydantic models (Institution, Building, Parcel3D, Party, StrataTitle, Encumbrance, etc.)
│   ├── seed_data.py                  # Database seeding — loads registry, 700 parcels, demo titles & liens
│   │
│   ├── routers/                      # ── API Route Handlers (8 Routers) ──
│   │   ├── institutions.py           #   GET /api/institutions — campus estate registry
│   │   ├── buildings.py              #   GET /api/buildings — building profiles & survey status
│   │   ├── parcels.py                #   GET /api/parcels, /mesh-data/{id}, /{ulpin} — 3D spatial queries & WebGL mesh
│   │   ├── rights.py                 #   POST /api/rights/allot, /transfer — strata title mutations
│   │   ├── encumbrances.py           #   POST /api/encumbrances/stamp — bank mortgage lien registration
│   │   ├── topology.py               #   GET /api/topology/validate/{id} — 3D collision audit
│   │   ├── analytics.py              #   GET /api/analytics/summary — estate-wide statistics
│   │   └── ingestion.py              #   POST /api/ingestion/run — surveyor floor plan upload & processing
│   │
│   └── services/                     # ── Core Domain Logic Engines ──
│       ├── cadastral_engine.py       #   End-to-end pipeline: detect → extract → stack → georeference → validate → persist
│       ├── cadastral_config.py       #   BuildingConfig (Pydantic) + RoomTypeRule + RuleEngine (declarative room classification)
│       ├── vector_extractor.py       #   PyMuPDF-based vector CAD PDF extraction (drawings + text → room units)
│       ├── cv_extractor.py           #   OpenCV adaptive threshold + contour detection + Tesseract OCR pipeline
│       ├── topology_validator.py     #   Shapely 2.0 — 3D bounding box collision detection (Z-interval + 2D polygon intersection)
│       ├── rights_manager.py         #   ISO 19152 LADM v2 RRR — allotment, transfer, mortgage, audit logging
│       └── pointcloud_validator.py   #   Drone photogrammetry ML — DBSCAN floor clustering + scipy peak detection
│
├── frontend/                         # ── Web Frontend ──
│   ├── index_en.html                 #   DoLR-style landing page (English)
│   ├── index_hi.html                 #   DoLR-style landing page (Hindi)
│   ├── app.html                      #   Main cadastral application (search + 3D viewer + mutation console)
│   ├── app.js                        #   Frontend logic — API calls, Plotly 3D mesh construction, floor filtering
│   ├── app.css                       #   Styling — Mahabhulekh-themed government UI
│   ├── 3d_cadastre_portal.html       #   3D Cadastre portal page
│   ├── iiitn_3d_portal.html          #   IIIT Nagpur campus portal
│   └── hostel_3d_twin.html           #   Pre-rendered Plotly 3D digital twin (standalone, ~5MB)
│
├── config/                           # ── Configuration ──
│   ├── institutional_registry.json   #   Campus estate + 4 buildings + Bhunaksha metadata
│   └── buildings/                    #   Per-building JSON configs (BuildingConfig + RoomTypeRules)
│
├── data/                             # ── Data Assets ──
│   ├── cadastre_3d.db                #   SQLite spatial database (7 tables, 700+ records)
│   ├── floor_plan.pdf                #   Source architectural CAD PDF (Hostel Block A)
│   ├── room_labels_all_floors_final.csv  # 700 verified 3D parcels (ULPIN, geometry, GPS, area)
│   ├── room_labels_hstl01_final.csv  #   Hostel Block A specific dataset
│   ├── room_labels_*.csv             #   Intermediate processing datasets
│   ├── occupancy_db.json             #   Demo occupancy data (simulated)
│   └── uploads/                      #   Uploaded floor plans from ingestion API
│
├── docs/                             # ── Documentation ──
│   ├── SIH_PS26011_Tech_Alignment_Report.md   # Full PS requirement traceability matrix
│   └── SIH_PS26011_Tech_Alignment_Report.pdf  # PDF version
│
├── generate_ulpin.py                 # Standalone 3D ULPIN generation script
├── validate_properties.py            # Standalone 3D topology validation script
├── visualize_3d.py                   # Standalone Plotly 3D digital twin generator
├── automated_pipeline.py             # End-to-end automated pipeline runner
├── build_real_coordinates.py         # Coordinate transform — CAD pixels → real-world meters
├── add_georeference.py               # GPS georeferencing — meters → WGS84 lat/lon
├── add_elevation.py                  # Vertical elevation assignment per floor
├── build_dolr_landing.py             # DoLR landing page generator
├── generate_portal.py                # Campus portal page generator
├── generate_pdf.py                   # PDF report generation
├── build_room_table.py               # Room table builder from raw data
├── occupancy_manager.py              # Occupancy check-in/out manager
├── extract_layout.py                 # Layout extraction helper
├── check_pdf.py                      # PDF format inspector
├── test_pipeline.py                  # Integration test suite
├── requirements.txt                  # Python dependencies (15 packages)
└── .gitignore                        # Git ignore rules
```

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    NATIONAL 3D ULPIN CADASTRAL PLATFORM                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  [ WEB FRONTEND CLIENT (frontend/app.html) ]                                │
│  ├── Mahabhulekh Cascading Search (District -> Taluka -> Village -> Survey) │
│  ├── 4-Building Selector Cards (Admin, Academic, Hostel Block A, Residential│
│  ├── Live Plotly WebGL 3D Digital Twin (Dynamic Geometry Streaming)        │
│  ├── 3D Legal Title Inspector (Carpet Area, Volume, UDS Fraction, Liens)    │
│  └── Live Cadastral Mutation Console (Allotment, Resale, Mortgage Stamping) │
│                                      │                                      │
│                                      ▼ REST JSON / OpenAPI                  │
│  [ FASTAPI CADASTRAL REST BACKEND (backend/main.py) ]                       │
│  ├── /api/institutions     ──► Estate & Bhunaksha Parcel Registry           │
│  ├── /api/buildings        ──► Building Profiles & Survey Readiness Status  │
│  ├── /api/parcels          ──► 3D Spatial Queries & WebGL Mesh Streaming    │
│  ├── /api/rights           ──► Strata Conveyance, Dynamic Allotment & RRR   │
│  ├── /api/encumbrances     ──► Bank Mortgage Liens & CERSAI Mock Registry   │
│  ├── /api/topology         ──► Real-Time 3D Collision & Statutory Area Audit│
│  ├── /api/analytics        ──► Built-up Area, Volume & Financial Metrics    │
│  └── /api/ingestion        ──► Surveyor Floor Plan Upload & AI Processing   │
│                                      │                                      │
│                                      ▼                                      │
│  [ CORE DOMAIN ENGINES (backend/services/) ]                                │
│  ├── cadastral_engine.py   ──► Vector CAD Parser & 3D Volumetric Extrusion  │
│  ├── vector_extractor.py   ──► PyMuPDF direct geometry extraction           │
│  ├── cv_extractor.py       ──► OpenCV contours + Tesseract OCR pipeline     │
│  ├── topology_validator.py ──► 3D Bounding Box & Polygon Collision Check   │
│  ├── rights_manager.py     ──► ISO 19152 LADM v2 RRR & Anti-Fraud Engine   │
│  └── pointcloud_validator  ──► Drone ML height verification (DBSCAN)        │
│                                      │                                      │
│                                      ▼                                      │
│  [ SPATIAL RELATIONAL DATABASE (data/cadastre_3d.db) ]                      │
│  ├── institutions (Survey 140/1, Khata 341, Waranga, pu-id: 33550994106)   │
│  ├── buildings (ADMIN01, ACAD01, HSTL01, RES01)                             │
│  ├── parcels_3d (700 Verified Volumetric Units for HSTL01, WGS84, UDS)     │
│  ├── parties (Citizen & Institutional Rights Holders - Simulated Demo)     │
│  ├── strata_titles (Strata Freehold, Leasehold, Allotment - Simulated Demo) │
│  ├── encumbrances (Bank Mortgage Liens - Simulated Demo)                    │
│  └── mutation_audit_log (Immutable Transaction History Ledger)              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🏷️ Standardized 3D ULPIN Schema

Every residential unit, common corridor, vertical transit core, and washroom is assigned an immutable, standardized 3D spatial identifier:

$$\mathbf{\text{3D ULPIN}} = \langle\text{BUILDING\_CODE}\rangle - \langle\text{FLOOR}\rangle - \langle\text{UNIT\_ID}\rangle - \langle\text{ZONING\_TYPE}\rangle$$

```
   HSTL01      -      F10      -      1001      -      4S
  └───────┘          └────┘          └────┘           └───┘
 Building Code     Floor Level     Unit / Room      Zoning / Legal
 (Hostel Block A)   (Level 10)       Number          Type (4-Seater)
```

| Component | Format | Description | Example |
|---|---|---|---|
| **Building Code** | Alphanumeric | Unique building identifier within estate | `ADMIN01`, `ACAD01`, `HSTL01`, `RES01` |
| **Floor Level** | `F<N>` / `FB<N>` | Vertical floor or basement index | `F1`, `F10`, `FB1` (Subsurface) |
| **Unit Number** | Alphanumeric | Specific spatial unit or transit label | `101`, `201`, `1001`, `X01` |
| **Zoning Type** | Alphanumeric | Statutory land use & property classification | `4S`, `2S`, `WASH`, `STR`, `LIFT`, `CORR`, `HALL`, `UTIL` |

### Fractional Undivided Share of Land ($\text{UDS}$) Calculus
Every vertical 3D ULPIN is legally bound to its mathematically calculated equity in the underlying 2D surface plot:
$$\text{UDS}_i = \left( \frac{\text{Carpet Area}_i}{\sum_{k=1}^N \text{Carpet Area}_k} \right) \times A_{\text{surface}}$$

---

## 🌐 Campus Building Registry & Cadastral Status

| Building Code | Building Name | Category | Floors | 3D Parcels | Residential Units | Common Transit |
|---|---|---|:---:|:---:|:---:|:---:|
| `ADMIN01` | Admin Building | Administrative | 3 | 24 | 9 | 15 |
| `ACAD01` | Academic Building | Academic / Labs | 4 | 32 | 8 | 24 |
| `HSTL01` | Hostel Block A | Student Residence | 10 | **700** | 560 | 140 |
| `RES01` | Residential Building | Staff / Faculty | 10 | 200 | 80 | 120 |
| **TOTAL** | **4 Buildings** | — | **27** | **956** | **657** | **299** |

---

## 🚀 Quickstart & Installation Guide

### Prerequisites

| Requirement | Version | Check Command |
|---|---|---|
| **Python** | 3.9 or higher | `python3 --version` |
| **pip** | Latest | `pip --version` |
| **Git** | Any | `git --version` |
| **Tesseract OCR** *(optional, for scanned images)* | 4.0+ | `tesseract --version` |

### Step 1 — Clone the Repository
```bash
git clone https://github.com/adiscripts03/3D_UPLIN_SIH.git
cd 3D_UPLIN_SIH
```

### Step 2 — Create & Activate Virtual Environment
```bash
# Create virtual environment
python3 -m venv ulpin_env

# Activate (macOS / Linux)
source ulpin_env/bin/activate

# Activate (Windows)
# ulpin_env\Scripts\activate
```

### Step 3 — Install All Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

> **Note:** `requirements.txt` includes all 15 core packages: FastAPI, Uvicorn, Pydantic, PyMuPDF, Shapely, OpenCV, Tesseract, Plotly, Pandas, GeoPandas, pyproj, scikit-learn, scipy, laspy, and Pillow.

### Step 4 — Initialize & Seed the Database
This populates the SQLite database with verified Bhunaksha parcel data, 4 campus buildings, 700 genuine 3D parcels for Hostel Block A, sample demonstration titles, and mock mortgage liens:
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

### Step 5 — Start the FastAPI Server
```bash
PYTHONPATH=. python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

### Step 6 — Open in Browser

| Page | URL | Description |
|---|---|---|
| 🏠 **Landing Page (English)** | [http://127.0.0.1:8000/](http://127.0.0.1:8000/) | DoLR-styled official portal |
| 🏠 **Landing Page (Hindi)** | [http://127.0.0.1:8000/hi](http://127.0.0.1:8000/hi) | Hindi version |
| 📊 **Cadastral Application** | [http://127.0.0.1:8000/app](http://127.0.0.1:8000/app) | Search, 3D twin, mutation console |
| 🌐 **3D Cadastre Portal** | [http://127.0.0.1:8000/portal](http://127.0.0.1:8000/portal) | Full 3D cadastre portal |
| 🏢 **3D Digital Twin** | [http://127.0.0.1:8000/twin](http://127.0.0.1:8000/twin) | Standalone 3D digital twin viewer |
| 📖 **Swagger API Docs** | [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) | Interactive API testing console |
| 📖 **ReDoc API Docs** | [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc) | Alternative API documentation |
| ❤️ **Health Check** | [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health) | System status |

### Troubleshooting

| Issue | Solution |
|---|---|
| `ModuleNotFoundError: No module named 'backend'` | Ensure you prefix commands with `PYTHONPATH=.` |
| `tesseract is not installed` or OCR errors | Install Tesseract: `brew install tesseract` (macOS) or `sudo apt install tesseract-ocr` (Ubuntu) — *only needed for scanned image extraction* |
| Port 8000 already in use | Use a different port: `--port 8001` |
| Database file not found | Run `PYTHONPATH=. python backend/seed_data.py` to create it |

---

## 🧬 Data Processing Pipeline

The system transforms raw floor plans into validated 3D volumetric parcels through 7 stages:

```
 ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
 │  1. INPUT    │    │ 2. DETECT &  │    │  3. CLASSIFY │    │ 4. SCALE &   │
 │  Floor Plan  │───►│  EXTRACT     │───►│  (RuleEngine)│───►│  GEOREFERENCE│
 │  (PDF/Image) │    │  Room Bounds │    │  Room Types  │    │  CAD → GPS   │
 └──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
                           │                                        │
                     ┌─────┴──────┐                                 ▼
                     │            │                          ┌──────────────┐
               Vector CAD   Scanned Image                   │ 5. VERTICAL  │
               (PyMuPDF)    (OpenCV+OCR)                    │   STACKING   │
                                                            │ Base × N Flrs│
                                                            └──────┬───────┘
                                                                   │
 ┌──────────────┐    ┌──────────────┐    ┌──────────────┐         │
 │  7. PERSIST  │    │ 6. VALIDATE  │    │ 5b. GENERATE │         │
 │  SQLite + CSV│◄───│  3D Topology │◄───│  3D ULPINs   │◄────────┘
 │              │    │  (Shapely)   │    │  + Area/Vol  │
 └──────────────┘    └──────────────┘    └──────────────┘
```

### Running the Pipeline Standalone

You can also run individual pipeline stages outside the API:

```bash
# Generate 3D ULPINs from processed floor data
PYTHONPATH=. python generate_ulpin.py

# Run full 3D topology validation
PYTHONPATH=. python validate_properties.py

# Generate standalone 3D digital twin HTML
PYTHONPATH=. python visualize_3d.py

# Run the automated end-to-end pipeline
PYTHONPATH=. python automated_pipeline.py
```

---

## 🧪 Comprehensive API Endpoint Reference

### Estate & Building Management

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/institutions` | List registered campus estates with Bhunaksha pu-id |
| `GET` | `/api/buildings` | List all campus buildings with survey readiness |
| `GET` | `/api/buildings/{building_id}` | Get specific building profile & metadata |

### 3D Parcels & Spatial Queries

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/parcels` | Query parcels with filters: `building_id`, `floor`, `type`, `is_common` |
| `GET` | `/api/parcels/mesh-data/{building_id}` | Stream 3D mesh bounding boxes for WebGL rendering |
| `GET` | `/api/parcels/{ulpin_3d}` | Get full parcel detail with occupants, area, volume, liens |

### Rights & Encumbrances (ISO 19152 LADM v2)

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/rights/allot` | Allot occupant to 3D unit (enforces capacity limits) |
| `POST` | `/api/rights/transfer` | Strata conveyance mutation (checks encumbrance locks) |
| `POST` | `/api/encumbrances/stamp` | Register bank mortgage lien against specific 3D ULPIN |

### Validation & Analytics

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/topology/validate/{building_id}` | Run live 3D collision audit with compliance score |
| `GET` | `/api/analytics/summary` | Estate-wide statistics: carpet area, volume, occupancy |

### Surveyor Data Ingestion

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/ingestion/configs` | List registered building configuration files |
| `GET` | `/api/ingestion/configs/{building_id}` | Get full JSON config for a building |
| `POST` | `/api/ingestion/run` | Upload floor plan + config → full extraction pipeline |

### System

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | System health check |
| `GET` | `/docs` | Interactive Swagger UI API console |
| `GET` | `/redoc` | ReDoc API documentation |

### Quick API Test Commands

```bash
# Health check
curl http://127.0.0.1:8000/health

# List all institutions
curl http://127.0.0.1:8000/api/institutions

# List all buildings
curl http://127.0.0.1:8000/api/buildings

# Get 3D mesh data for Hostel Block A (used by WebGL viewer)
curl http://127.0.0.1:8000/api/parcels/mesh-data/HSTL01

# Query a specific 3D parcel
curl http://127.0.0.1:8000/api/parcels/HSTL01-F1-X01-4S

# Run topology validation
curl http://127.0.0.1:8000/api/topology/validate/HSTL01

# Get estate-wide analytics
curl http://127.0.0.1:8000/api/analytics/summary

# Allot an occupant (POST)
curl -X POST http://127.0.0.1:8000/api/rights/allot \
  -H "Content-Type: application/json" \
  -d '{"ulpin_3d": "HSTL01-F3-X01-4S", "party_id": "DEMO001", "name": "Test User"}'

# Stamp a mortgage lien (POST)
curl -X POST http://127.0.0.1:8000/api/encumbrances/stamp \
  -H "Content-Type: application/json" \
  -d '{"ulpin_3d": "HSTL01-F3-X02-4S", "mortgagee_name": "Test Bank", "sanction_reference": "TEST-2026-001", "loan_amount_inr": 1000000}'
```

---

## 🗄️ Database Schema

The SQLite database (`data/cadastre_3d.db`) contains **7 interlinked tables**:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────────┐
│  institutions   │     │    buildings     │     │     parcels_3d      │
│─────────────────│ 1:N │─────────────────│ 1:N │─────────────────────│
│ institution_id  │────►│ building_id     │────►│ ulpin_3d (PK)       │
│ institution_name│     │ institution_id  │     │ building_id (FK)    │
│ survey_number   │     │ building_name   │     │ floor, room_id, type│
│ village, taluka │     │ category        │     │ z_min, z_max        │
│ district, state │     │ data_status     │     │ real_width/depth_m  │
│ campus_anchor   │     │ total_floors    │     │ lat, lon (WGS84)    │
│ total_plot_area │     │ floor_pitch_m   │     │ carpet_area_sqm     │
│ pu_id           │     │ room_height_m   │     │ gross_volume_cbm    │
└─────────────────┘     └─────────────────┘     │ undivided_share     │
                                                 │ is_common_property  │
                                                 └────────┬────────────┘
                                                          │ 1:N
                         ┌────────────────────────────────┼──────────────────┐
                         ▼                                ▼                  ▼
                 ┌───────────────┐              ┌──────────────────┐ ┌────────────────┐
                 │ strata_titles │              │  encumbrances    │ │ mutation_audit  │
                 │───────────────│              │──────────────────│ │  _log          │
                 │ title_id (PK) │              │ encumbrance_id   │ │────────────────│
                 │ ulpin_3d (FK) │              │ ulpin_3d (FK)    │ │ tx_id (PK)     │
                 │ party_id (FK) │              │ mortgagee_name   │ │ ulpin_3d       │
                 │ right_type    │              │ sanction_ref (UK)│ │ tx_type        │
                 │ status        │              │ loan_amount_inr  │ │ from/to_party  │
                 │ max_capacity  │              │ status           │ │ details        │
                 └───────┬───────┘              └──────────────────┘ │ timestamp      │
                         │ N:1                                       └────────────────┘
                         ▼
                 ┌───────────────┐
                 │   parties     │
                 │───────────────│
                 │ party_id (PK) │
                 │ name          │
                 │ party_type    │
                 │ aadhaar_masked│
                 │ is_simulated  │
                 └───────────────┘
```

---

## 🧪 Running Tests

```bash
# Run integration test suite
PYTHONPATH=. python test_pipeline.py

# Run standalone topology validation (prints detailed report)
PYTHONPATH=. python validate_properties.py
```

Expected topology validation output:
```
============================================================
  🏢 3D VOLUMETRIC CADASTRE VALIDATION ENGINE
  Total Units: 700 across 10 Floors (Floors 1 to 10)
============================================================

✅ PASSED [Uniqueness]: All 700 3D ULPINs are 100% unique.
✅ PASSED [Area Standards]: All 560 residential units (56/floor) meet statutory minimums.
✅ PASSED [3D Topology]: 0 spatial collisions. Perfect 3D volumetric cadastre integrity across all 10 floors.

📊 Summary Breakdown:
   • Total Floors: 10
   • Residential Parcels: 560 (2-Seater & 4-Seater)
   • Common/Transit Parcels: 140 (Corridors, Stairs, Lifts, Halls, Bridges, Washrooms)
   • Building Footprint: ~60.0m (W) × 38.8m (D) × 34.0m (H)
============================================================
```

---

## ⚖️ Standards Compliance & Legal Disclaimer

- **ISO 19152 LADM v2**: Conforms to the international Land Administration Domain Model (`LA_SpatialUnit`, `LA_BAUnit`, `LA_Party`, `LA_RRR`).
- **Data Integrity Notice**: Real parcel data is sourced from Government of Maharashtra Bhunaksha / Mahabhulekh (Survey 140/1, Khata 341, Waranga, Nagpur Rural, pu-id: 33550994106).
- **Demonstration RRR Notice**: Any bank mortgage liens or citizen names in the demonstration UI are **SIMULATED DATA FOR TECHNICAL DEMONSTRATION PURPOSES ONLY**.

---

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/your-feature`
3. **Commit** your changes: `git commit -m 'Add your feature'`
4. **Push** to the branch: `git push origin feature/your-feature`
5. **Open** a Pull Request

### Areas Where Contributions Are Welcome

- 🏗️ Support for additional floor plan formats (DXF, DWG, IFC/BIM)
- 🤖 Deep learning room segmentation models (Mask R-CNN, SAM)
- 🌍 Multi-language UI support (22 scheduled languages of India)
- 🗄️ PostgreSQL + PostGIS migration
- 🔐 Authentication & RBAC implementation
- 📱 Mobile-responsive frontend
- 🧪 Expanded test coverage

---

## 📄 License

This project is developed for the **Smart India Hackathon 2026** under **Problem Statement 26011** by the Department of Land Resources (DoLR), Ministry of Rural Development, Government of India.

---

## 👥 Team

**Institution:** Indian Institute of Information Technology, Nagpur (IIIT Nagpur)
**Hackathon:** Smart India Hackathon (SIH) 2026
**Problem Statement:** PS 26011 — 3D ULPIN Generation and Vertical Property Mapping System
**Organization:** Ministry of Rural Development — Department of Land Resources (DoLR)

---

<p align="center">
  <b>🏛️ National 3D ULPIN & Volumetric Cadastre Platform</b><br>
  <i>Every room. Every floor. Every right. One 3D identity.</i><br><br>
  Built with ❤️ for Smart India Hackathon 2026
</p>
