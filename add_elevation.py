import csv

ROOM_HEIGHT = 2.9     
BEAM_HEIGHT = 0.5       
FLOOR_TO_FLOOR = ROOM_HEIGHT + BEAM_HEIGHT  

FLOOR_NUMBER = 1  

input_file = "data/room_labels.csv"
output_file = f"data/room_labels_floor{FLOOR_NUMBER}.csv"

rows = []
with open(input_file, "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        row["floor"] = FLOOR_NUMBER
        row["z_min"] = round((FLOOR_NUMBER - 1) * FLOOR_TO_FLOOR, 2)      
        row["z_max"] = round(row["z_min"] + ROOM_HEIGHT, 2)                  
        row["z_slab_top"] = round(FLOOR_NUMBER * FLOOR_TO_FLOOR, 2)          
        rows.append(row)

fieldnames = list(rows[0].keys())
with open(output_file, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"Saved {len(rows)} rows with elevation data to {output_file}")