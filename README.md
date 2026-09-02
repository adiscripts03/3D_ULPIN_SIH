# 🏛️ National 3D ULPIN & Volumetric Cadastre Platform
### Smart India Hackathon (SIH) — PS 26011 | Ministry of Rural Development — Department of Land Resources (DoLR)
**Category:** Software | **Theme:** Smart Automation | **Cadastral Standard:** ISO 19152 LADM v2 & Maharashtra Land Revenue (Survey 140/1)

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
- **Verified Government Land Record Georeferencing**: Aligned with the official Government of Maharashtra Bhunaksha / Mahabhulekh record: **Survey No. 140/1**, **Khata No. 341**, **Waranga (वारंगा)**, **Nagpur Rural**, with State Parcel ID **`pu-id: 33550994106`** under State Government (*Sarkar*) tenure.
- **Genuine CAD Extrusion Dataset**: 700 3D volumetric parcels extracted directly from verified architectural vector drawings for **Hostel Block A (`HSTL01`)** across 10 floors ($16,979\text{ m}^2$ carpet area, $49,239.2\text{ m}^3$ airspace volume).
- **4-Building Campus Structure**: Clean 4-building estate layout representing **Admin Building (`ADMIN01`)**, **Academic Building (`ACAD01`)**, **Hostel Block A (`HSTL01`)**, and **Residential Building (`RES01`)** with transparent survey statuses.
- **Intelligent 3D Topology & Geometry Validation Engine**: Performs computational geometry collision audits (`shapely`), verifying $Z$-interval intersections, planar polygon overlaps ($A \cap B$), statutory minimum areas, and primary key uniqueness ($100\%$ compliance score).
- **ISO 19152 LADM v2 RRR Rights & Encumbrance Ledger**: Enforces statutory occupancy caps, locks inalienable common elements (corridors, stairs, washrooms), registers mortgage liens, and automatically blocks fraudulent conveyances on encumbered units (demonstration records clearly badged as simulated).
- **FastAPI RESTful Backend**: Modular REST API with 7 routers handling estate queries, 3D mesh streaming, real-time title mutation, mortgage stamping, and spatial analytics.
- **Bilingual Official Landing & 3D Digital Twin Portal**: Authentic Department of Land Resources interface with Mahabhulekh-style cascading parcel search and interactive WebGL 3D twin viewer.

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
│  └── /api/analytics        ──► Built-up Area, Volume & Financial Metrics    │
│                                      │                                      │
│                                      ▼                                      │
│  [ CORE DOMAIN ENGINES (backend/services/) ]                                │
│  ├── cadastral_engine.py   ──► Vector CAD Parser & 3D Volumetric Extrusion  │
│  ├── topology_validator.py ──► 3D Bounding Box & Polygon Collision Check   │
│  └── rights_manager.py     ──► ISO 19152 LADM v2 RRR & Anti-Fraud Governance│
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
| `ADMIN01` | Admin Building | Administrative | — | 0 | 0 | 0 |
| `ACAD01` | Academic Building | Academic / Labs | — | 0 | 0 | 0 |
| `HSTL01` | Hostel Block A | Student Residence | 10 | **700** | 560 | 140 |
| `RES01` | Residential Building | Staff / Faculty | — | 0 | 0 | 0 |
| **TOTAL** | **4 Buildings** | — | **10** | **700** | **560** | **140** |

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

### 3. Initialize & Seed the Verified 3D Cadastral Database
Populates the relational spatial database with verified Bhunaksha land parcel metadata, 4 campus buildings, genuine 700 3D parcels for Hostel Block A, and sample demonstration titles:
```bash
PYTHONPATH=. python backend/seed_data.py
```

### 4. Start the FastAPI Cadastral Server
```bash
PYTHONPATH=. python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

Open **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)** in your browser.

---

## 🧪 Comprehensive API Endpoint Verification

| Router | Method | Endpoint | Description |
|---|---|---|---|
| **Institutions** | `GET` | `/api/institutions` | List registered campus estates with Bhunaksha pu-id |
| **Buildings** | `GET` | `/api/buildings` | List 4 campus buildings with survey readiness |
| **3D Parcels** | `GET` | `/api/parcels/mesh-data/HSTL01` | Stream WebGL 3D volumetric parcels for Hostel Block A |
| **3D Parcels** | `GET` | `/api/parcels/{ulpin_3d}` | Query title card, RERA carpet area, volume, UDS |
| **Rights / RRR** | `POST` | `/api/rights/allot` | Dynamic strata title allotment (Simulated Demo) |
| **Rights / RRR** | `POST` | `/api/rights/transfer` | Strata conveyance mutation with anti-fraud lien lock |
| **Encumbrances** | `POST` | `/api/encumbrances/stamp` | Register bank mortgage lien (Simulated Demo) |
| **Topology** | `GET` | `/api/topology/validate/HSTL01` | Run live 3D geometric collision audit |
| **Analytics** | `GET` | `/api/analytics/summary` | Query built-up carpet area, gross volume, parcel counts |
| **FastAPI Docs** | `GET` | `/docs` | Interactive Swagger UI API console |

---

## ⚖️ Standards Compliance & Legal Disclaimer

- **ISO 19152 LADM v2**: Conforms to the international Land Administration Domain Model (`LA_SpatialUnit`, `LA_BAUnit`, `LA_Party`, `LA_RRR`).
- **Data Integrity Notice**: Real parcel data is sourced from Government of Maharashtra Bhunaksha / Mahabhulekh (Survey 140/1, Khata 341, Waranga, Nagpur Rural, pu-id: 33550994106).
- **Demonstration RRR Notice**: Any bank mortgage liens or citizen names in the demonstration UI are **SIMULATED DATA FOR TECHNICAL DEMONSTRATION PURPOSES ONLY**.
