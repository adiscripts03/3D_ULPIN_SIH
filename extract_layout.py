import fitz

doc = fitz.open("data/floor_plan.pdf")
page = doc[0]

words = page.get_text("words")

for w in words:
    x0, y0, x1, y1, text, block_no, line_no, word_no = w
    print(f"Label: {text:15} | Position: ({x0:.1f}, {y0:.1f}) to ({x1:.1f}, {y1:.1f})")