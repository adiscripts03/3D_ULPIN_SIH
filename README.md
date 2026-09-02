# 🏛️ National 3D ULPIN & Volumetric Cadastre Platform
### Smart India Hackathon (SIH) — PS 26011 | Ministry of Rural Development — Department of Land Resources (DoLR)
**Category:** Software | **Theme:** Smart Automation | **Cadastral Standard:** ISO 19152 LADM v2 & Bhu-Aadhaar 3D

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI%20REST%20API-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![SQLite Spatial](https://img.shields.io/badge/Database-SQLite%203D%20Cadastre-003B57.svg?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![ISO 19152](https://img.shields.io/badge/Cadastral%20Standard-ISO%2019152%20LADM%20v2-blue.svg)](https://www.iso.org/standard/51206.html)
[![Plotly 3D](https://img.shields.io/badge/Digital%20Twin-WebGL%203D%20Mesh-orange.svg?logo=plotly&logoColor=white)](https://plotly.com/)
[![Shapely](https://img.shields.io/badge/Topology%20Engine-Shapely%202.0-green.svg)](https://shapely.readthedocs.io/)
[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)

---

## 📌 Executive Summary

Traditional cadastral systems in India rely on **2D land parcel identifiers (ULPIN / Bhu-Aadhaar)**. While 2D parcel identification works for flat agricultural or surface land, it fails in dense multi-storey urban structures where multiple distinct ownership rights, apartments, utility shafts, and commercial units are stacked vertically over the exact same $(X, Y)$ ground coordinates.

This repository delivers an **enterprise multi-building, multi-tenant 3D Cadastral System** conforming to the international **ISO 19152 LADM v2** standard and the **Department of Land Resources (DoLR)** national framework:
- **Multi-Building & Multi-Estate Spatial Database**: Manages **2,744 volumetric 3D parcels** across **4 multi-storey towers** in multiple estates (IIIT Nagpur Campus & DDA Dwarka Residential Complex).
- **Automated CAD/BIM Extrusion Engine**: Ingests architectural CAD vector PDFs, extracts metric unit geometry with $0.00\text{m}$ error, applies geodetic WGS84 anchoring, and assigns standardized 3D ULPINs in seconds.
- **Intelligent 3D Topology & Geometry Validation Engine**: Performs computational geometry collision audits (`shapely`), verifying $Z$-interval intersections, planar polygon overlaps ($A \cap B$), statutory minimum areas, and primary key uniqueness ($100\%$ compliance score).
- **ISO 19152 LADM v2 RRR Rights & Encumbrance Ledger**: Enforces statutory occupancy caps, locks inalienable common elements (corridors, stairs, washrooms), registers bank mortgage liens (CERSAI), and automatically blocks fraudulent conveyances on encumbered units.
- **FastAPI RESTful Backend**: Modular REST API with 7 routers handling estate queries, 3D mesh streaming, real-time title mutation, mortgage stamping, and spatial analytics.
- **Live Interactive 3D Digital Twin Web Portal**: WebGL-powered 3D viewer with multi-building switching, floor slicing, click-to-inspect legal title cards, and real-time transaction modals.

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    NATIONAL 3D ULPIN CADASTRAL PLATFORM                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  [ WEB FRONTEND CLIENT (frontend/app.html) ]                                │
│  ├── Multi-Building & Multi-Estate Selector (HSTL01, HSTL02, TOWER_A...)    │
│  ├── Live Plotly WebGL 3D Digital Twin (Dynamic Geometry Streaming)        │
│  ├── 3D Legal Title Inspector (Carpet Area, Volume, UDS Fraction, Liens)    │
│  └── Live Cadastral Mutation Console (Allotment, Resale, Mortgage Stamping) │
│                                      │                                      │
│                                      ▼ REST JSON / OpenAPI                  │
│  [ FASTAPI CADASTRAL REST BACKEND (backend/main.py) ]                       │
│  ├── /api/institutions     ──► Estate & Bhu-Aadhaar Master Surface Registry │
│  ├── /api/buildings        ──► Building Profiles & Automated CAD Ingestion  │
│  ├── /api/parcels          ──► 3D Spatial Queries & WebGL Mesh Streaming    │
│  ├── /api/rights           ──► Strata Conveyance, Dynamic Allotment & RRR   │
│  ├── /api/encumbrances     ──► Bank Mortgage Liens & CERSAI Registry        │
│  ├── /api/topology         ──► Real-Time 3D Collision & Statutory Area Audit│
│  └── /api/analytics        ──► Built-up Area, Volume & Financial Metrics    │
│                                      │                                      │
│                                      ▼                                      │
│  [ CORE DOMAIN ENGINES (backend/services/) ]                                │
│  ├── cadastral_engine.py   ──► Multi-Building CAD Vector Parser & 3D Extrude│
│  ├── topology_validator.py ──► 3D Bounding Box & Polygon Collision Check   │
│  └── rights_manager.py     ──► ISO 19152 LADM v2 RRR & Anti-Fraud Governance│
│                                      │                                      │
│                                      ▼                                      │
│  [ SPATIAL RELATIONAL DATABASE (data/cadastre_3d.db) ]                      │
│  ├── institutions (Estates / Master Surface Parcels / Bhu-Aadhaar)          │
│  ├── buildings (Multi-Storey Towers, Vertical Pitch, GNSS Anchors)          │
│  ├── parcels_3d (2,744 Volumetric Units, WGS84, Area, Volume, UDS Fraction)│
│  ├── parties (Citizens, Aadhaar, HOAs, Lending Banks)                       │
│  ├── strata_titles (Strata Freehold, Leasehold, Allotment, Max Capacity)   │
│  ├── encumbrances (Bank Mortgage Liens, Sanction Refs, Loan Values)         │
│  └── mutation_audit_log (Immutable Transaction History Ledger)              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🏷️ Standardized 3D ULPIN Schema

Every residential flat, office unit, corridor, vertical transit core, and utility space is assigned an immutable, globally unique 3D spatial identifier:

$$\mathbf{\text{3D ULPIN}} = \langle\text{BUILDING\_CODE}\rangle - \langle\text{FLOOR}\rangle - \langle\text{UNIT\_ID}\rangle - \langle\text{ZONING\_TYPE}\rangle$$

```
   HSTL01      -      F10      -      1001      -      4S
  └───────┘          └────┘          └────┘           └───┘
 Building Code     Floor Level     Unit / Room      Zoning / Legal
 (Hostel Block 1)   (Level 10)       Number          Type (4-Seater)
```

| Component | Format | Description | Example |
|---|---|---|---|
| **Building Code** | Alphanumeric | Unique building identifier within estate | `HSTL01`, `HSTL02`, `ACAD01`, `TOWER_A` |
| **Floor Level** | `F<N>` / `FB<N>` | Vertical floor or basement index | `F1`, `F10`, `FB1` (Subsurface) |
| **Unit Number** | Alphanumeric | Specific spatial unit or transit label | `101`, `201`, `1001`, `PARK_01` |
| **Zoning Type** | Alphanumeric | Statutory land use & property classification | `4S`, `2S`, `3BHK`, `WASH`, `STR`, `LIFT`, `CORR`, `PARK`, `UTIL` |

### Fractional Undivided Share of Land ($\text{UDS}$) Calculus
Every vertical 3D ULPIN is legally bound to its mathematically calculated equity in the underlying 2D surface plot:
$$\text{UDS}_i = \left( \frac{\text{Carpet Area}_i}{\sum_{k=1}^N \text{Carpet Area}_k} \right) \times A_{\text{surface}}$$

---

## 🌐 Multi-Building & Multi-Estate Live Registry

The spatial database currently manages **2,744 3D volumetric parcels** across **4 multi-storey towers**:

| Estate Code | Estate Name | Building ID | Building Name | Floors | Total 3D Parcels | Residential Units | Common Transit |
|---|---|---|---|:---:|:---:|:---:|:---:|
| **IIITN** | IIIT Nagpur Campus | `HSTL01` | Boys Hostel Block 1 | 10 | **700** | 560 | 140 |
| **IIITN** | IIIT Nagpur Campus | `HSTL02` | Girls Hostel Block 2 | 8 | **584** | 448 | 136 |
| **IIITN** | IIIT Nagpur Campus | `ACAD01` | Academic Complex | 6 | **438** | 0 | 438 |
| **DDA_DWK**| DDA Dwarka Society | `TOWER_A` | Tower A (HIG Tower) | 14 | **1,022** | 1,148 | 274 |
| **TOTAL** | **2 Estates** | **4 Towers** | — | — | **2,744** | **2,156** | **588** |

---

## 🚀 Quickstart & Installation Guide

### 1. Clone the Repository
```bash
git clone https://github.com/adiscripts03/3D_UPLIN_SIH.git
cd 3D_UPLIN_SIH
```

### 2. Set Up Virtual Environment & Dependencies
```bash
# Create virtual environment
python3 -m venv ulpin_env
source ulpin_env/bin/activate

# Install core dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install fastapi uvicorn pydantic python-multipart
```

### 3. Initialize & Seed the 3D Cadastral Database
Populates the relational spatial database with estates, buildings, 3D parcels, initial occupancy records, and sample bank mortgage liens:
```bash
PYTHONPATH=. python backend/seed_data.py
```

### 4. Start the FastAPI Cadastral Server
```bash
PYTHONPATH=. python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

### 5. Open the Interactive Web Application & API Docs
* **Interactive 3D Cadastre Portal:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
* **Interactive Swagger API Docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* **ReDoc API Documentation:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 📡 RESTful Cadastral API Reference

The backend exposes a full suite of REST endpoints for national spatial data infrastructure (NSDI) integration:

### 1. Institutions & Estates
* `GET /api/institutions` — List all registered estates and master surface parcels.
* `POST /api/institutions` — Register a new institutional estate or housing complex.

### 2. Buildings & CAD Ingestion
* `GET /api/buildings` — List all buildings with floor counts, heights, and parcel totals.
* `GET /api/buildings/{building_id}` — Get single building metadata.
* `POST /api/buildings/{building_id}/ingest` — Automatically parse vector CAD drawings and extrude 3D units into database.

### 3. 3D Parcels & WebGL Mesh Streaming
* `GET /api/parcels` — Query 3D parcels (filter by `building_id`, `floor`, `type`, `is_common`).
* `GET /api/parcels/{ulpin_3d}` — Retrieve full legal card (WGS84 centroid, area, volume, UDS, occupants, active liens).
* `GET /api/parcels/mesh-data/{building_id}` — Stream optimized 3D WebGL mesh coordinates for digital twin rendering.

### 4. Strata Rights & Dynamic Mutation (ISO 19152 LADM)
* `POST /api/rights/allot` — Allot an occupant/citizen to a 3D unit with real-time capacity and zone validation.
* `POST /api/rights/transfer` — Execute secondary conveyancing / resale mutation between parties (enforces bank lien checks).
* `GET /api/rights/audit-log` — Retrieve immutable cadastral transaction history.

### 5. Encumbrances & Mortgage Registry (CERSAI)
* `GET /api/encumbrances` — List registered bank mortgage liens.
* `POST /api/encumbrances/stamp` — Stamp a new mortgage lien on a 3D ULPIN.
* `POST /api/encumbrances/{id}/release` — Release mortgage lien upon loan satisfaction.

### 6. Spatial Topology Validation
* `GET /api/topology/validate/{building_id}` — Run live 3D volumetric collision and statutory compliance audit.

### 7. Cadastral Intelligence & Analytics
* `GET /api/analytics/summary` — High-level statistics (total units, area $\text{m}^2$, volume $\text{m}^3$, financial lien totals).

---

## 🧪 Automated Testing & Validation

Run live validation tests across the system:

```bash
# 1. Health check
curl -s http://127.0.0.1:8000/health

# 2. Run 3D Topology Collision Audit
curl -s http://127.0.0.1:8000/api/topology/validate/HSTL01

# 3. Test Dynamic Occupant Allotment
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"ulpin_3d":"HSTL02-F1-101-4S","party_id":"BT_ID_ANANYA","name":"Ananya Sen"}' \
  http://127.0.0.1:8000/api/rights/allot

# 4. Test Bank Mortgage Lien Stamping (CERSAI)
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"ulpin_3d":"TOWER_A-F4-401-4S","mortgagee_name":"Punjab National Bank","sanction_reference":"PNB-2026-001","loan_amount_inr":7500000}' \
  http://127.0.0.1:8000/api/encumbrances/stamp

# 5. Verify Anti-Fraud Protection (Transfer blocked on mortgaged unit)
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"ulpin_3d":"TOWER_A-F4-401-4S","from_party_id":"PREV_OWNER","to_party_id":"NEW_BUYER","to_party_name":"Vikramaditya"}' \
  http://127.0.0.1:8000/api/rights/transfer
```

---

## 📁 Repository Structure

```
3D_ULPIN/
├── README.md                                  # Comprehensive documentation & setup guide
├── requirements.txt                           # Python dependencies
├── .gitignore                                 # Git tracking rules
│
├── backend/                                   # Enterprise FastAPI RESTful Backend
│   ├── main.py                                # FastAPI app entrypoint, CORS, static routes
│   ├── database.py                            # SQLite Spatial database DDLs, connection pooling
│   ├── models.py                              # Pydantic data schemas (LADM v2, RRR, Liens)
│   ├── seed_data.py                           # Database seeder (Institutions, Towers, Parcels)
│   ├── services/
│   │   ├── cadastral_engine.py                # Multi-building CAD vector parser & 3D extrusion
│   │   ├── topology_validator.py              # Shapely 3D collision & statutory area engine
│   │   └── rights_manager.py                  # LADM RRR engine, conveyance, mortgage stamping
│   └── routers/
│       ├── institutions.py                    # Estates & Bhu-Aadhaar surface endpoints
│       ├── buildings.py                       # Building profiles & CAD ingestion triggers
│       ├── parcels.py                         # 3D parcel queries & WebGL mesh streaming
│       ├── rights.py                          # Dynamic allotment & strata mutation
│       ├── encumbrances.py                    # Bank mortgage liens & CERSAI registry
│       ├── topology.py                        # Live 3D spatial collision audit
│       └── analytics.py                       # High-level cadastral statistics
│
├── frontend/                                  # Interactive 3D Web Application
│   ├── app.html                               # Modern 3D Digital Twin portal UI
│   ├── app.js                                 # Dynamic REST API client & Plotly 3D controller
│   ├── app.css                                # Dark mode glassmorphism styling
│   └── hostel_3d_twin.html                    # Standalone static 3D twin export
│
├── config/
│   └── institutional_registry.json            # Multi-estate & building configuration registry
│
├── data/
│   ├── cadastre_3d.db                         # SQLite Spatial Database (2,744 3D parcels)
│   ├── floor_plan.pdf                         # Ground truth architectural CAD floor plan
│   ├── room_labels_all_floors_final.csv       # 10-Floor 3D ULPIN dataset (700 units)
│   └── occupancy_db.json                      # Legacy JSON rights ledger
│
├── docs/
│   ├── SIH_PS26011_Tech_Alignment_Report.md  # Detailed Technical Alignment Report (LADM / RERA)
│   └── SIH_PS26011_Tech_Alignment_Report.pdf # Publication-quality compiled PDF report
│
├── automated_pipeline.py                      # CLI batch pipeline for processing any CAD PDF
├── generate_pdf.py                            # Headless Chrome PDF report compiler
└── visualize_3d.py                            # Plotly 3D mesh rendering utility
```

---

## 📄 Key Documentation & Reports

* **Technical Analysis & Alignment Report (Markdown):** [docs/SIH_PS26011_Tech_Alignment_Report.md](docs/SIH_PS26011_Tech_Alignment_Report.md)
* **Official Compiled Report (PDF):** [docs/SIH_PS26011_Tech_Alignment_Report.pdf](docs/SIH_PS26011_Tech_Alignment_Report.pdf)

---

## 🏛️ Regulatory & Cadastral Compliance

This platform directly aligns with:
1. **ISO 19152:2024 (LADM v2)**: Land Administration Domain Model for 3D Legal Spaces and RRR (Rights, Restrictions, Responsibilities).
2. **Real Estate (Regulation and Development) Act (RERA 2016)**: Standardized Carpet Area bounds and inalienable common property conveyance.
3. **State Apartment Ownership Acts**: Deed of Declaration (Form A) and fractional Undivided Share of Land ($\text{UDS}$) equity.
4. **Digital India Land Records Modernization Programme (DILRMP)** & **NGDRS**: Interoperable 3D parcel registration and CERSAI financial lien tracking.

---

## ⚖️ License & Attribution
Developed for the **Smart India Hackathon (SIH)** — Problem Statement **26011**.  
Designed & implemented by the **SIH 3D ULPIN Engineering Team**.
