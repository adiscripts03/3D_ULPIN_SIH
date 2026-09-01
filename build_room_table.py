import fitz
import csv

doc = fitz.open("data/floor_plan.pdf")
page = doc[0]

words = page.get_text("words")

rows = []
for w in words:
    x0, y0, x1, y1, text, block_no, line_no, word_no = w
    rows.append({
        "label": text,
        "x0": round(x0, 1),
        "y0": round(y0, 1),
        "x1": round(x1, 1),
        "y1": round(y1, 1),
        "center_x": round((x0 + x1) / 2, 1),
        "center_y": round((y0 + y1) / 2, 1)
    })

with open("data/room_labels.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["label", "x0", "y0", "x1", "y1", "center_x", "center_y"])
    writer.writeheader()
    writer.writerows(rows)

print(f"Saved {len(rows)} labels to data/room_labels.csv")