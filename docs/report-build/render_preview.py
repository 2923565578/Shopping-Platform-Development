import pymupdf, os
p = r"F:\Final Project\ShopStream\docs\ShopStream_Final_Report_EN.pdf"
doc = pymupdf.open(p)
print("pages:", doc.page_count)
os.makedirs("preview", exist_ok=True)
for i in [0,1,3,5,9]:
    if i < doc.page_count:
        pix = doc[i].get_pixmap(matrix=pymupdf.Matrix(1.4,1.4))
        pix.save(f"preview/en_p{i+1}.png")
print("ok")
