import pymupdf
p = r"F:\Final Project\ShopStream\docs\ShopStream_Final_Report_ZH.pdf"
d = pymupdf.open(p)
for i in [4,5,10,12,15,16,17,18]:
    pix = d[i].get_pixmap(matrix=pymupdf.Matrix(1.4,1.4))
    pix.save(f"preview/zh_p{i+1}.png")
print("done", d.page_count)
