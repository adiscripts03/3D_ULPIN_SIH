# 🏢 3D ULPIN: Volumetric Cadastre & Vertical Property Mapping Engine
### Smart India Hackathon (SIH) — PS 26011 | Prototype Implementation & Case Study

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![Plotly 3D](https://img.shields.io/badge/Visualization-Plotly%203D%20Digital%20Twin-orange.svg)](https://plotly.com/)
[![Shapely](https://img.shields.io/badge/Topology-Shapely%202.0-green.svg)](https://shapely.readthedocs.io/)
[![PyMuPDF](https://img.shields.io/badge/CAD%20Extraction-PyMuPDF-red.svg)](https://pymupdf.readthedocs.io/)

---

## 📌 Executive Summary

Traditional cadastral systems in India rely on **2D land parcel identifiers (ULPIN - Unique Land Parcel Identification Number)**. While 2D parcel identification works for surface land, it fails to represent multi-storey buildings, multi-occupant units, underground utilities, and vertical real estate.

This repository provides an **end-to-end working prototype for 3D ULPIN generation, intelligent topology validation, and dynamic volumetric property mapping**:
- **Automated Floor Plan Extraction**: Extracts room polygons, corridors, stairs, lifts, and common spaces from CAD/PDF floor plans.
- **Metric Coordinate Transformation & Georeferencing**: Converts vector bounding boxes into real-world metric dimensions ($X, Y$) and projects them to global GPS coordinates (Latitude, Longitude) + Elevation ($Z_{min}, Z_{max}$).
- **Standardized 3D ULPIN Generation**: Assigns standardized, collision-free 3D spatial identifiers encoding building ID, floor level, unit index, and zoning/spatial type.
- **Intelligent Topology & Geometry Validation Engine**: Performs automated spatial overlap detection via polygon intersections (`shapely`), minimum capacity compliance checks, and duplicate ID prevention.
- **Dynamic Rights/Occupancy Management Layer**: Links vertical units to occupants/ownership records with automated capacity constraint enforcement and audit logging.
- **Interactive 3D Digital Twin**: Generates a self-contained WebGL 3D visualization showing volumetric parcels, facade orientations, and live occupancy color coding.

---

## 🏗️ System Architecture & Data Pipeline

```
                    ┌──────────────────────────────┐
                    │         INPUT LAYER          │
                    │  - CAD / Vector PDF Plans    │
                    │  - Building GPS Anchor Point │
                    │  - Measured Floor Elevations │
                    │  - Occupant / Title Data     │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │   STEP 1: CAD EXTRACTION     │  build_real_coordinates.py
                    │  - Vector geometry filtering │
                    │  - Metric scale conversion   │
                    │  - Facade orientation flip   │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │   STEP 2: GEOREFERENCING     │  add_georeference.py
                    │  - Local (X, Y) to Lat / Lon │
                    │  - Elevation (Z_min, Z_max)  │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │  STEP 3: 3D ULPIN GENERATOR  │  generate_ulpin.py
                    │  - Standardized Schema Gen   │
                    │  - Primary Key Structuring   │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │   STEP 4: VALIDATION ENGINE  │  validate_properties.py
                    │  - Shapely Overlap Check     │
                    │  - Legal Area Compliance     │
                    │  - Duplicate ID Audit        │
                    └──────────────┬───────────────┘
                                   │
                     ┌─────────────┴─────────────┐
                     ▼                           ▼
      ┌────────────────────────────┐   ┌───────────────────────────┐
      │   STEP 5: DYNAMIC RIGHTS   │   │  STEP 6: 3D DIGITAL TWIN  │
      │   occupancy_manager.py     │   │   visualize_3d.py         │
      │  - Capacity enforcement    │   │  - 3D Box Mesh generation │
      │  - Unit allotment / audit  │   │  - Plotly WebGL Digital   │
      │  - JSON Database Linkage   │   │    Twin (.html)           │
      └────────────────────────────┘   └───────────────────────────┘
```

---

## ⚙️ Prerequisites & System Requirements

### 1. System Requirements
- **Operating System**: macOS, Linux, or Windows (WSL recommended)
- **Python**: Python 3.9, 3.10, 3.11, or 3.12
- **Web Browser**: Any modern browser with WebGL enabled (Chrome, Edge, Safari, Firefox) for the 3D twin

### 2. System-Level Dependencies (Optional for OCR / Computer Vision)
If you plan to extract text from scanned bitmap drawings or images:
- **macOS (via Homebrew)**:
  ```bash
  # If brew is installed:
  brew install tesseract

  # If you get 'brew: command not found', configure your PATH first:
  eval "$(/opt/homebrew/bin/brew shellenv zsh)"
  echo 'eval "$(/opt/homebrew/bin/brew shellenv zsh)"' >> ~/.zshrc

  # If Homebrew is not installed yet on your Mac:
  # /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  ```
- **Ubuntu / Debian**:
  ```bash
  sudo apt-get update && sudo apt-get install -y tesseract-ocr
  ```
- **Windows**:
  Download and install the Tesseract OCR installer from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki).

---

## 🚀 Installation & Environment Setup

### 1. Clone the Repository
```bash
git clone https://github.com/adiscripts03/3D_UPLIN_SIH.git
cd 3D_UPLIN_SIH
```

### 2. Create and Activate Virtual Environment
```bash
# On macOS / Linux:
python3 -m venv ulpin_env
source ulpin_env/bin/activate

# On Windows (Command Prompt / PowerShell):
python -m venv ulpin_env
ulpin_env\Scripts\activate
```

### 3. Install Python Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 💻 Step-by-Step Execution Guide

You can run the entire pipeline step by step or execute the full workflow at once.

### Option A: Run Full Pipeline in One Command
```bash
python build_real_coordinates.py && \
python add_georeference.py && \
python generate_ulpin.py && \
python validate_properties.py && \
python occupancy_manager.py && \
python visualize_3d.py
```

---

### Option B: Step-by-Step Execution

#### Step 1: CAD & Metric Extraction
Extracts geometric bounding boxes and textual labels from `data/floor_plan.pdf`, applies CAD scaling ($0.1362\text{ m/pt}$), flips orientation to match physical building facade, and extrudes metric boundaries across all 10 floors ($3.4\text{m}$ pitch).
```bash
python build_real_coordinates.py
```
*Outputs*: `data/room_labels_floor1_real.csv` (70 units), `data/room_labels_all_floors_real.csv` (700 units)

#### Step 2: Spatial Georeferencing
Calculates exact GPS Centroids (Latitude, Longitude) from the building GPS anchor point and sets vertical elevations ($Z_{min}, Z_{max}$) for each floor level.
```bash
python add_georeference.py
```
*Outputs*: `data/room_labels_floor1_geo.csv` (70 units), `data/room_labels_all_floors_geo.csv` (700 units)

#### Step 3: 3D ULPIN Standardization
Constructs standardized volumetric cadastral identifiers adhering to the project schema across all 10 floors.
```bash
python generate_ulpin.py
```
*Outputs*: `data/room_labels_floor1_final.csv` (70 units), `data/room_labels_all_floors_final.csv` (700 units)

#### Step 4: Intelligent 3D Volumetric Topology Validation
Executes automated integrity checks using `shapely`:
1. **Uniqueness Audit**: Ensures all 700 3D ULPINs across 10 floors are 100% unique.
2. **Legal Area Audit**: Checks that unit areas meet minimum statutory thresholds per zoning type.
3. **3D Spatial Overlap Audit**: Performs 3D volumetric collision detection ($Z$-interval overlap + 2D polygon intersection) verifying 0 spatial collisions.
```bash
python validate_properties.py
```

#### Step 5: Dynamic Rights & Occupancy Management Demo
Simulates multi-floor student allotment (Floors 1 to 10), prevents overcrowding above legal capacity, prevents residential check-in to common/utility zones, and updates `data/occupancy_db.json`.
```bash
python occupancy_manager.py
```

#### Step 6: Generate 10-Storey 3D Interactive Digital Twin
Creates an interactive, self-contained 10-storey 3D volumetric model with hover tooltips, spatial parcel coloring, floor filter dropdowns, and facade labels.
```bash
python visualize_3d.py
```
*Output*: `frontend/hostel_3d_twin.html`

#### Step 7: View the 3D Digital Twin in Browser
```bash
# On macOS:
open frontend/hostel_3d_twin.html

# On Linux:
xdg-open frontend/hostel_3d_twin.html

# On Windows:
start frontend/hostel_3d_twin.html
```

---

## 🏷️ 3D ULPIN Standardized Schema

Every unit, corridor, vertical core, and utility space is assigned a unique alphanumeric 3D identifier following this specification:

$$\mathbf{\text{ULPIN}} = \langle\text{BUILDING\_ID}\rangle - \langle\text{FLOOR}\rangle - \langle\text{UNIT\_ID}\rangle - \langle\text{TYPE}\rangle$$

| Component | Format | Description | Example |
|---|---|---|---|
| **Building Code** | `HSTL01` | Unique primary land parcel / building code | `HSTL01` |
| **Floor Level** | `F<N>` | Vertical floor index ($F1, F2, \dots, F10$) | `F1`, `F10` |
| **Property / Unit ID** | Alphanumeric | Unit name, corridor ID, or utility zone | `101`, `201`, `1001`, `BRIDGE_1` |
| **Spatial Type** | `4S`, `2S`, `HALL`, `WASH`, `STR`, `LIFT`, `CORR`, `BRIDGE` | Legal zoning / property classification | `4S` (4-Seater Room), `WASH` (Washroom) |

### Sample 3D ULPIN Identifiers Across 10 Floors:
- `HSTL01-F1-101-4S` — Floor 1, Unit 101 (4-Seater Residential Parcel, Elev 0.0m–2.9m)
- `HSTL01-F2-201-4S` — Floor 2, Unit 201 (4-Seater Residential Parcel, Elev 3.4m–6.3m)
- `HSTL01-F5-BRIDGE_1-BRIDGE` — Floor 5, Connecting Bridgeway (Elev 13.6m–16.5m)
- `HSTL01-F10-1001-4S` — Floor 10, Penthouse Unit 1001 (Elev 30.6m–33.5m)
- `HSTL01-F1-COMMON_HALL-HALL` — Floor 1, West Wing Common Assembly Area

---

## 📂 Project Structure

```
3D_UPLIN/
├── README.md                           # Comprehensive documentation & setup guide
├── requirements.txt                    # Python package dependencies
├── .gitignore                          # Git tracking exclusions
├── 3D_ULPIN_Hostel_Prototype_Plan.md  # Detailed SIH prototype architectural plan
│
├── build_real_coordinates.py           # Extracts CAD vectors, stacks 10 floors with 3.4m pitch
├── add_georeference.py                 # Transforms metric offsets into global Lat/Lon + Elev
├── generate_ulpin.py                   # Generates standardized 3D ULPIN primary keys (700 units)
├── validate_properties.py              # 3D volumetric topology validation (overlap, area, duplicates)
├── occupancy_manager.py                # Multi-floor dynamic occupancy & capacity management engine
├── visualize_3d.py                     # 10-storey Plotly WebGL 3D digital twin generator
│
├── check_pdf.py                        # Diagnostic script for PDF inspection
├── extract_layout.py                   # Diagnostic text/coordinate dumper
├── build_room_table.py                 # Helper table builder
├── add_elevation.py                    # Elevation calculation utility
│
├── data/
│   ├── floor_plan.pdf                  # Ground truth architectural CAD floor plan
│   ├── room_labels.csv                 # Raw label extractions
│   ├── room_labels_floor1_real.csv     # Floor 1 metric coordinates ($X, Y$ in meters)
│   ├── room_labels_all_floors_real.csv # 10-Floor metric coordinates (700 units)
│   ├── room_labels_floor1_geo.csv      # Floor 1 georeferenced coordinates
│   ├── room_labels_all_floors_geo.csv  # 10-Floor georeferenced dataset (700 units)
│   ├── room_labels_floor1_final.csv    # Floor 1 3D ULPIN dataset
│   ├── room_labels_all_floors_final.csv# Final 10-Floor 3D ULPIN dataset (700 units)
│   └── occupancy_db.json               # Live dynamic rights / occupancy ledger
│
└── frontend/
    └── hostel_3d_twin.html             # Standalone interactive 10-storey 3D WebGL Digital Twin
```

---

## 🧪 Validation Engine & Test Output

When running `python validate_properties.py`, the engine validates all 700 volumetric parcels across 10 stacked floors:

```text
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
   • Building Footprint: ~60.0m (W) × 38.8m (D) × 33.5m (H)
============================================================
```

---

## 🌐 Generalization & Future Scope

While demonstrated on a multi-storey hostel as a high-density ground-truth case study, the underlying algorithms generalize directly to:
1. **Multi-Storey Apartment Complexes**: Vertical parcel demarcation for strata-title ownership and common amenity shares.
2. **Commercial Real Estate**: Office suite volumetric cadastre, retail unit leasing boundaries, and parking slot rights.
3. **Underground Infrastructure**: Metro tunnels, subterranean parking, utility conduits, and basement rights.
4. **Air Rights & Drone Corridors**: Defined 3D airspace parcels for urban air mobility (UAM) and aerial property boundaries.

---

## 📄 License & Attribution
Developed for the **Smart India Hackathon (SIH)** — Problem Statement **26011**.
Designed & implemented by the SIH 3D ULPIN Development Team.
