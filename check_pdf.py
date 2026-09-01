import fitz 

doc = fitz.open("data/floor_plan.pdf")
page = doc[0]

text = page.get_text()
print("Text found:", repr(text[:500]))

images = page.get_images(full=True)
print("Number of embedded images:", len(images))