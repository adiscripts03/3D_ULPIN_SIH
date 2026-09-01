import csv
import math

# --- CONFIGURATION ---
# GPS Anchor (Top-Left of Building, near room X01)
# Converted from 20°56'58.4"N 79°01'46.1"E
ANCHOR_LAT = 20.9495556
ANCHOR_LON = 79.0294722

# Constants for flat-earth approximation (meters per degree at this latitude)
METERS_PER_DEG_LAT = 111320.0
METERS_PER_DEG_LON = 111320.0 * math.cos(math.radians(ANCHOR_LAT))

# We now use exact mathematically calculated Y coordinates from the CSV


def georeference_dataset(input_file, output_file):
    rows = []
    with open(input_file, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    for r in rows:
        # X coordinate: real_x_start_m + half of the room width
        x_m = float(r["real_x_start_m"]) + (float(r["real_width_m"]) / 2.0)
        
        # Y coordinate: Exact mathematically calculated center
        y_m = float(r["real_y_center_m"])
        
        # Convert to Latitude/Longitude
        # +x moves East (increases Longitude)
        # +y moves South (decreases Latitude) - Assuming "Up" on the PDF is North
        lon = ANCHOR_LON + (x_m / METERS_PER_DEG_LON)
        lat = ANCHOR_LAT - (y_m / METERS_PER_DEG_LAT)
        
        r["real_y_m"] = round(y_m, 2)
        r["latitude"] = round(lat, 8)
        r["longitude"] = round(lon, 8)

    # Save output
    fieldnames = list(rows[0].keys())
    with open(output_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Successfully georeferenced {len(rows)} properties -> {output_file}")
    return rows

def main():
    # Process Floor 1
    georeference_dataset("data/room_labels_floor1_real.csv", "data/room_labels_floor1_geo.csv")
    
    # Process All 10 Floors
    all_rows = georeference_dataset("data/room_labels_all_floors_real.csv", "data/room_labels_all_floors_geo.csv")
    print(f"Sample Floor 1 ({all_rows[0]['label']}): Lat {all_rows[0]['latitude']}, Lon {all_rows[0]['longitude']}, Elev {all_rows[0]['z_min']}m-{all_rows[0]['z_max']}m")
    sample_f10 = next(r for r in all_rows if r["floor"] == "10" or r["floor"] == 10)
    print(f"Sample Floor 10 ({sample_f10['label']}): Lat {sample_f10['latitude']}, Lon {sample_f10['longitude']}, Elev {sample_f10['z_min']}m-{sample_f10['z_max']}m")

if __name__ == "__main__":
    main()
