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
  brew install tesseract
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
Extracts geometric bounding boxes and textual labels from `data/floor_plan.pdf`, applies CAD scaling ($0.1362\text{ m/pt}$), flips orientation to match physical building facade, and assigns metric boundaries.
```bash
python build_real_coordinates.py
```
*Output*: `data/room_labels_floor1_real.csv`

#### Step 2: Spatial Georeferencing
Calculates exact GPS Centroids (Latitude, Longitude) from the building GPS anchor point and sets vertical elevations ($Z_{min}, Z_{max}$).
```bash
python add_georeference.py
```
*Output*: `data/room_labels_floor1_geo.csv`

#### Step 3: 3D ULPIN Standardization
Constructs standardized volumetric cadastral identifiers adhering to the project schema.
```bash
python generate_ulpin.py
```
*Output*: `data/room_labels_floor1_final.csv`

#### Step 4: Intelligent Topology & Geometry Validation
Executes automated integrity checks using `shapely`:
1. **Uniqueness Audit**: Ensures zero duplicate IDs.
2. **Legal Area Audit**: Checks that unit areas meet minimum statutory thresholds.
3. **Topological Overlap Audit**: Detects any polygon intersections ($>0.01\text{ m}^2$) between distinct parcels.
```bash
python validate_properties.py
```

#### Step 5: Dynamic Rights & Occupancy Management Demo
Simulates allotment, prevents overcrowding above legal capacity, prevents residential check-in to common/utility zones, and updates `data/occupancy_db.json`.
```bash
python occupancy_manager.py
```

#### Step 6: Generate 3D Interactive Digital Twin
Creates an interactive, self-contained 3D volumetric model with hover tooltips, spatial parcel coloring, and facade labels.
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
| **Floor Level** | `F<N>` | Vertical floor index ($F1, F2, \dots$) | `F1` |
| **Property / Unit ID** | Alphanumeric | Unit name, corridor ID, or utility zone | `X01`, `BRIDGE_1`, `COMMON_HALL` |
| **Spatial Type** | `4S`, `2S`, `HALL`, `WASH`, `STR`, `LIFT`, `CORR`, `BRIDGE` | Legal zoning / property classification | `4S` (4-Seater Room), `WASH` (Washroom) |

### Sample 3D ULPIN Identifiers:
- `HSTL01-F1-X01-4S` — Floor 1, Unit X01 (4-Seater Residential Parcel)
- `HSTL01-F1-X07-2S` — Floor 1, Unit X07 (2-Seater Residential Parcel)
- `HSTL01-F1-COMMON_HALL-HALL` — Floor 1, West Wing Common Assembly Area
- `HSTL01-F1-BRIDGE_1-BRIDGE` — Floor 1, Courtyard Transit Bridgeway
- `HSTL01-F1-STAIRS1-STR` — Floor 1, Vertical Transit Core (Stairwell)

---

## 📂 Project Structure

```
3D_UPLIN/
├── README.md                           # Comprehensive documentation & setup guide
├── requirements.txt                    # Python package dependencies
├── .gitignore                          # Git tracking exclusions
├── 3D_ULPIN_Hostel_Prototype_Plan.md  # Detailed SIH prototype architectural plan
│
├── build_real_coordinates.py           # Extracts CAD vectors, scales to meters, flips facade
├── add_georeference.py                 # Transforms metric offsets into global Lat/Lon
├── generate_ulpin.py                   # Generates standardized 3D ULPIN primary keys
├── validate_properties.py              # Shapely topology validation (overlap, area, duplicates)
├── occupancy_manager.py                # Dynamic occupancy & capacity management engine
├── visualize_3d.py                     # Plotly WebGL 3D digital twin generator
│
├── check_pdf.py                        # Diagnostic script for PDF inspection
├── extract_layout.py                   # Diagnostic text/coordinate dumper
├── build_room_table.py                 # Helper table builder
├── add_elevation.py                    # Elevation calculation utility
│
├── data/
│   ├── floor_plan.pdf                  # Ground truth architectural CAD floor plan
│   ├── room_labels.csv                 # Raw label extractions
│   ├── room_labels_floor1_real.csv     # Metric coordinates ($X, Y$ in meters)
│   ├── room_labels_floor1_geo.csv      # Georeferenced coordinates (Lat, Lon, Elevation)
│   ├── room_labels_floor1_final.csv    # Final 3D ULPIN dataset with all attributes
│   └── occupancy_db.json               # Live dynamic rights / occupancy ledger
│
└── frontend/
    └── hostel_3d_twin.html             # Standalone interactive 3D WebGL Digital Twin
```

---

## 🧪 Validation Engine & Test Output

When running `python validate_properties.py`, the engine validates 70 individual volumetric parcels across multiple geometric dimensions:

```text
--- Starting Validation Engine for 70 properties ---

✅ PASSED: All 3D ULPINs are perfectly unique.
✅ PASSED: All rooms meet their specific capacity area requirements.
✅ PASSED: Perfect topological integrity! No overlapping properties found.

Validation complete.
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
