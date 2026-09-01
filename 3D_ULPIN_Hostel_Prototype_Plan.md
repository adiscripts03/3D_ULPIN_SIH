# 3D ULPIN Generation & Vertical Property Mapping — Prototype Plan
### SIH PS 26011 | Internal Hackathon Build Plan (Hostel Case Study)

---

## 1. Scope Statement

**What we are building:** A working proof-of-concept pipeline that ingests real building data (floor plans, imagery, elevation, occupancy) and outputs unique, validated **3D spatial IDs** for every unit in a multi-storey building, dynamically linked to occupant/ownership records — demonstrated on our 10-floor, ~580-room hostel as ground truth, with an explicit narrative for generalizing to apartment ownership, underground infrastructure, and air rights.

**What we are NOT claiming:** A production-ready national cadastral system, legal title transfer, or nationwide data integration. This is a scoped technical prototype proving the core mechanism works.

---

## 2. PS Requirement → Our Module Traceability Matrix

This table exists so no core ask gets dropped. Cross-check this before final submission.

| PS Requirement | Our Module | Status |
|---|---|---|
| Surface land parcels | Building footprint (GPS corners) | Covered |
| Multi-storey apartments | Per-room 3D units across 10 floors | Covered |
| Underground infrastructure | Basement/utility notes (stretch) | Partial/Narrative |
| Drone imagery | Phone high-res photos (photogrammetry) | Covered (substitute) |
| LiDAR/3D point cloud | Photogrammetry-derived point cloud (Polycam/Meshroom) | Covered (substitute) |
| GIS parcel layers | Digitized floor plan polygons | Covered |
| Building floor plans | Actual hostel PDF floor plans | Covered (real data) |
| GNSS/CORS coordinates | Building corner GPS (phone/Maps) | Covered (approx) |
| DEM/DSM | Manual measured floor heights (raw + beam) | Covered (measured, not modeled) |
| Automated building extraction | CV-based contour/segmentation on floor plan | Covered |
| Floor segmentation | Height-clustering on point cloud OR direct floor-plan-per-floor extraction | Covered |
| Vertical parcel delineation | Z-elevation assignment per room via measured heights | Covered |
| Intelligent topology validation | Rule-based overlap/capacity/duplicate checks | Covered |
| Standardized 3D ULPIN generation | Custom ID schema script | Covered |
| Mapping ownership rights | BT ID ↔ Room ID table (dynamic) | Covered (occupancy proxy) |
| Volumetric cadastre support | 3D visualization (extruded floors) | Covered |

---

## 3. System Architecture

```
                    ┌─────────────────────┐
                    │   INPUT LAYER        │
                    │ - Floor plan PDFs    │
                    │ - Phone photos       │
                    │ - Manual height data │
                    │ - Hostel databook    │
                    │ - Building GPS point │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  EXTRACTION LAYER    │
                    │ - PDF/image parsing  │
                    │ - Room segmentation  │
                    │ - OCR (room numbers) │
                    │ - Feature classify   │
                    │   (stairs/bath/etc)  │
                    │ - Point cloud gen    │
                    │   (photogrammetry)   │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  GEOREFERENCING      │
                    │ - Local (x,y) →      │
                    │   real lat/long      │
                    │ - Floor → elevation  │
                    │   (measured heights) │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  3D ID GENERATION    │
                    │ - Unique ID per room │
                    │ - Encodes (x,y,z)    │
                    │ - Encodes room type  │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  VALIDATION LAYER    │
                    │ - Overlap check      │
                    │ - Capacity check     │
                    │ - Duplicate ID check │
                    │ - Gap/void check     │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  OWNERSHIP LAYER     │
                    │ - BT ID ↔ Room ID    │
                    │ - Dynamic updates    │
                    │   (check-in/out)     │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  VISUALIZATION LAYER │
                    │ - 3D stacked floors  │
                    │ - Click-to-inspect   │
                    │ - Live update demo   │
                    └─────────────────────┘
```

---

## 4. Phase-Wise Execution Plan

### Phase 0 — Setup (Day 1)
1. Create shared repo (GitHub) and folder structure: `/data`, `/extraction`, `/backend`, `/frontend`, `/docs`
2. Set up Python environment: `opencv-python`, `pytesseract`, `shapely`, `pandas`, `geopandas`
3. Assign roles (see Section 6)
4. Upload floor plan PDF, height notes, and databook into `/data` — this is your single source of truth

### Phase 1 — Data Digitization (Day 1–2)
5. Determine PDF type: vector (has selectable layers/text) vs scanned image — changes extraction method
6. If vector: extract layers/paths directly using `pdfplumber` or `PyMuPDF`
7. If scanned: convert PDF pages to images, proceed with CV pipeline
8. Build height table: `floor_number | raw_height | beam_height | cumulative_elevation`
9. Digitize hostel databook into: `room_number | seater_type | floor | BT_ID(s)`
10. Sanity check: room count in databook == room count in floor plan (catch mismatches early)

### Phase 2 — Automated Extraction (Day 2–4) — *core AI/ML component*
11. Run contour detection (OpenCV `findContours`) on floor plan image to isolate room boundaries
12. Classify detected shapes: room / stairwell / bathroom / water cooler (by size, aspect ratio, or a small trained classifier if time allows)
13. Run OCR (Tesseract) on each detected room polygon's label region to auto-read room numbers
14. Manually correct any OCR misreads (expect ~10-20% correction needed — note this openly in your report as a known limitation)
15. Output: structured JSON — `{room_id, polygon_coords, room_number, feature_type, floor}`
16. (Stretch) Capture 15–20 high-res photos of one floor's corridor, run through Meshroom/Polycam to generate a point cloud
17. (Stretch) Apply height-based clustering (simple Z-histogram) on the point cloud to auto-detect floor separation — demonstrates "floor segmentation from 3D data" directly from the PS

### Phase 3 — Georeferencing (Day 4–5)
18. Capture building corner GPS coordinates via phone GPS/Google Maps pin
19. Write a coordinate transform: local floor-plan pixel coordinates → real-world offset from the GPS anchor point (simple affine scaling using floor plan's known real-world dimensions, e.g., "1 room = 3m wide")
20. Assign each floor's elevation using your measured height table (cumulative from ground)
21. Merge into final room record: `{room_id, lat, long, elevation_range(z_min, z_max), floor, room_number}`

### Phase 4 — 3D ULPIN Generation (Day 5–6)
22. Design ID schema on paper, e.g.: `HOSTELCODE-FLOOR-ROOMNO-TYPE` (document your schema logic clearly — this shows "standardization" to judges)
23. Write generator script: input the merged room record → output unique alphanumeric 3D ID
24. Store all generated IDs in SQLite/PostGIS with full geometry + elevation + metadata
25. Add a duplicate-ID safety check in the generator itself (hash collision check)

### Phase 5 — Validation Engine (Day 6–7) — *"intelligent topology validation"*
26. Write overlap check: no two room polygons on the same floor should intersect (use `shapely.intersects`)
27. Write capacity check: number of BT IDs linked to a room ≤ room's seater capacity
28. Write duplicate check: no BT ID linked to more than one room simultaneously
29. Write completeness check: every physical room in the floor plan has a generated 3D ID (no gaps)
30. Run full validation suite, log and fix all flagged issues, keep the validation report — show this log to judges as evidence of "intelligent validation," not just a claim

### Phase 6 — Dynamic Ownership Layer (Day 7–8)
31. Build simple check-in/check-out function: updates BT ID ↔ Room ID table
32. Re-run capacity + duplicate validation automatically on every update (this is your "dynamic" story)
33. Add a small audit log: timestamp + what changed + who (BT ID) moved where

### Phase 7 — Visualization (Day 8–9)
34. Build 3D visualization: extrude each floor's room polygons to their elevation range (Plotly 3D mesh, or Three.js if a frontend dev is available)
35. Color-code by occupancy state (empty / partial / full)
36. Add click/hover: shows 3D ID, room number, occupant BT ID(s), floor, elevation
37. Add a live demo trigger: perform a check-out/check-in on stage and show the visualization + validation updating in real time

### Phase 8 — Documentation & Pitch (Day 9–10)
38. Write a 1-page technical summary: architecture diagram + data flow + tech stack
39. Prepare slide 1: the core issue (2D cadastre can't handle vertical/underground ownership)
40. Prepare slide 2: our approach (imagery/plan → AI extraction → georeferencing → 3D ID → validation → dynamic ownership)
41. Prepare slide 3: what's real vs. what's a proxy (be upfront — occupancy stands in for ownership; hostel stands in for apartment complex)
42. Prepare slide 4: how this generalizes (apartment units, underground utilities, air rights — brief future-scope note)
43. Record a backup demo video in case live demo fails
44. Rehearse Q&A: "how is this different from just a room database?" → answer: standardized geospatial 3D ID, automated extraction, and topology validation are what make it a cadastral system, not a spreadsheet

---

## 5. Honest Limitations to State Upfront (builds credibility, not weakness)

- GPS/elevation precision is approximate (phone-grade, not survey-grade GNSS/CORS)
- OCR requires manual correction — not fully automated end-to-end yet
- Underground infrastructure and air-rights are addressed narratively, not physically modeled in this prototype
- Occupant allotment (BT ID) is used as a proxy for legal ownership since the hostel has single institutional ownership

Stating these clearly, with a "next steps to production" note, reads as engineering maturity to judges — don't hide them.

---

## 6. Suggested Role Split (adjust to team size)

| Role | Responsibility |
|---|---|
| Data/GIS lead | Floor plan digitization, georeferencing, height table |
| CV/ML lead | Contour detection, OCR, feature classification, point cloud (stretch) |
| Backend/DB lead | ID generation schema, database, validation engine |
| Frontend/Viz lead | 3D visualization, dynamic demo interface |
| Pitch/Docs lead | Slides, traceability matrix, Q&A prep, video backup |

---

## 7. Milestone Checklist (10-day sprint)

- [ ] Day 1–2: All raw data digitized (floor plans, heights, databook)
- [ ] Day 4: Automated room extraction working on at least 1 floor
- [ ] Day 5: Georeferencing merged into room records
- [ ] Day 6: 3D IDs generated for all rooms, no duplicates
- [ ] Day 7: Validation suite passes with logged report
- [ ] Day 8: Dynamic check-in/out updates working
- [ ] Day 9: 3D visualization functional and demo-ready
- [ ] Day 10: Slides + video backup + Q&A rehearsed
