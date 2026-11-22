import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import build

OUT_DIR = r"F:\Final Project\ShopStream\docs"


def main():
    lang = sys.argv[1] if len(sys.argv) > 1 else "en"
    if lang == "en":
        from content_en import blocks
        title = "ShopStream Final Project Report (EN)"
        out = os.path.join(OUT_DIR, "ShopStream_Final_Report_EN.pdf")
    else:
        from content_zh import blocks
        title = "ShopStream 期末项目实验报告（中文）"
        out = os.path.join(OUT_DIR, "ShopStream_Final_Report_ZH.pdf")
    build(blocks(), out, title, lang)
    print("built", out, os.path.getsize(out), "bytes")


if __name__ == "__main__":
    main()
