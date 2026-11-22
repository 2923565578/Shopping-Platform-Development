import pymupdf
p = r"F:\Final Project\ShopStream\docs\ShopStream_Final_Report_EN.pdf"
d = pymupdf.open(p)
print("pages", d.page_count)
for i in range(d.page_count):
    pix = d[i].get_pixmap(matrix=pymupdf.Matrix(1.2,1.2))
    pix.save(f"preview/en_all_p{i+1}.png")
