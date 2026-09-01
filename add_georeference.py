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


def main():
    rows = []
    with open("data/room_labels_floor1_real.csv", "r") as f:
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
    with open("data/room_labels_floor1_geo.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Successfully georeferenced {len(rows)} rooms.")
    print("Saved to data/room_labels_floor1_geo.csv")
    print(f"Sample {rows[0]['label']}: Lat {rows[0]['latitude']}, Lon {rows[0]['longitude']}")

if __name__ == "__main__":
    main()
