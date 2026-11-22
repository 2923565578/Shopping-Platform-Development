"""Build the Chinese Word version of the ShopStream report from content_zh.py."""
import os
import sys
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from PIL import Image as PILImage

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from content_zh import blocks  # noqa: E402

ASSETS = Path(r"F:\Final Project\ShopStream\docs\report-assets")
OUT = Path(r"F:\Final Project\ShopStream\docs\ShopStream_Final_Report_ZH.docx")

TEXT_W = 16.0  # cm, A4 21cm minus 2x2.5cm margins
SONG, HEI, MONO, WEST = "宋体", "黑体", "Consolas", "Times New Roman"


def set_run_font(run, cn=SONG, west=WEST, size=12, bold=False):
    run.font.name = west
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = RGBColor(0, 0, 0)
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    rfonts.set(qn("w:ascii"), west)
    rfonts.set(qn("w:hAnsi"), west)
    rfonts.set(qn("w:eastAsia"), cn)


def set_style_font(style, cn, west, size, bold=False):
    style.font.name = west
    style.font.size = Pt(size)
    style.font.bold = bold
    style.font.color.rgb = RGBColor(0, 0, 0)
    rpr = style.element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    rfonts.set(qn("w:ascii"), west)
    rfonts.set(qn("w:hAnsi"), west)
    rfonts.set(qn("w:eastAsia"), cn)


def set_first_line_chars(p, chars=200):
    pf = p.paragraph_format
    pf.first_line_indent = Pt(24)
    ind = p._p.get_or_add_pPr().find(qn("w:ind"))
    if ind is None:
        ind = OxmlElement("w:ind")
        p._p.get_or_add_pPr().append(ind)
    ind.set(qn("w:firstLineChars"), str(chars))


def shade(cell_or_par, color="F2F2F2"):
    pr = cell_or_par._tc.get_or_add_tcPr() if hasattr(cell_or_par, "_tc") else None
    if pr is None:
        pr = cell_or_par._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), color)
    pr.append(shd)


def table_borders(tbl):
    tblPr = tbl._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge, sz in (("top", 8), ("bottom", 8), ("insideH", 4)):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), str(sz))
        el.set(qn("w:color"), "000000")
        borders.append(el)
    for edge in ("left", "right", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "none")
        borders.append(el)
    tblPr.append(borders)


def row_props(row, header=False):
    trPr = row._tr.get_or_add_trPr()
    cant = OxmlElement("w:cantSplit")
    trPr.append(cant)
    if header:
        hdr = OxmlElement("w:tblHeader")
        trPr.append(hdr)


def add_cell_text(cell, text, bold=False, align=WD_ALIGN_PARAGRAPH.LEFT, size=9):
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    cell.paragraphs[0].text = ""
    for i, line in enumerate(str(text).split("\n")):
        p = cell.paragraphs[0] if i == 0 else cell.add_paragraph()
        pf = p.paragraph_format
        pf.first_line_indent = Pt(0)
        pf.left_indent = Pt(0)
        pf.space_before = Pt(0)
        pf.space_after = Pt(0)
        pf.line_spacing = 1.0
        p.alignment = align
        run = p.add_run(line)
        set_run_font(run, SONG, WEST, size, bold)


def add_heading(doc, text, level):
    p = doc.add_heading(level=level)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    size = {1: 16, 2: 14}.get(level, 12)
    set_run_font(run, HEI, WEST, size, True)
    return p


def add_body(doc, text):
    p = doc.add_paragraph(style="Normal")
    set_first_line_chars(p, 200)
    run = p.add_run(text)
    set_run_font(run, SONG, WEST, 12)
    return p


def add_code(doc, text):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.first_line_indent = Pt(0)
    pf.line_spacing = 1.0
    pf.space_before = Pt(4)
    pf.space_after = Pt(6)
    shade(p, "F5F7FA")
    for i, line in enumerate(text.split("\n")):
        if i:
            p.add_run().add_break()
        run = p.add_run(line)
        set_run_font(run, SONG, MONO, 9)
    return p


def add_caption(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf = p.paragraph_format
    pf.first_line_indent = Pt(0)
    pf.space_before = Pt(4)
    pf.space_after = Pt(12)
    pf.line_spacing = 1.0
    run = p.add_run(text)
    set_run_font(run, SONG, WEST, 10.5)


def add_image(doc, fname, cap):
    path = ASSETS / fname
    with PILImage.open(path) as im:
        w, h = im.size
    width_cm = TEXT_W
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Pt(0)
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(str(path), width=Cm(width_cm))
    add_caption(doc, cap)


def add_table(doc, data, widths_cm):
    ncols = len(data[0])
    scale = TEXT_W / sum(widths_cm[:ncols])
    tbl = doc.add_table(rows=0, cols=ncols)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    table_borders(tbl)
    for r, row in enumerate(data):
        cells = tbl.add_row().cells
        row_props(tbl.rows[-1], header=(r == 0))
        for c, text in enumerate(row):
            cells[c].width = Cm(widths_cm[c] * scale)
            align = WD_ALIGN_PARAGRAPH.LEFT
            add_cell_text(cells[c], text, bold=(r == 0), align=align)
            if r == 0:
                shade(cells[c], "F2F2F2")
    # column widths must also be set on grid
    for c in range(ncols):
        for row in tbl.rows:
            row.cells[c].width = Cm(widths_cm[c] * scale)
    return tbl


def add_toc_field(doc):
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Pt(0)
    run = p.add_run()
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = r'TOC \o "1-2" \h \z \u'
    fld_sep = OxmlElement("w:fldChar")
    fld_sep.set(qn("w:fldCharType"), "separate")
    placeholder = OxmlElement("w:t")
    placeholder.text = "目录已生成，若未显示请右键选择“更新域”。"
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    for el in (fld_begin, instr, fld_sep, placeholder, fld_end):
        run._r.append(el)


def add_page_field(par):
    run = par.add_run()
    fld = OxmlElement("w:fldChar")
    fld.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    for el in (fld, instr, end):
        run._r.append(el)
    set_run_font(run, SONG, WEST, 10.5)


def restart_numbering(section):
    sectPr = section._sectPr
    pg = sectPr.find(qn("w:pgNumType"))
    if pg is None:
        pg = OxmlElement("w:pgNumType")
        sectPr.append(pg)
    pg.set(qn("w:start"), "1")


def main():
    doc = Document()
    # base styles
    normal = doc.styles["Normal"]
    set_style_font(normal, SONG, WEST, 12)
    normal.paragraph_format.line_spacing = 1.5
    normal.paragraph_format.space_before = Pt(0)
    normal.paragraph_format.space_after = Pt(0)
    for lvl, sz in ((1, 16), (2, 14), (3, 12)):
        st = doc.styles[f"Heading {lvl}"]
        set_style_font(st, HEI, WEST, sz, True)
        st.paragraph_format.space_before = Pt(14 if lvl == 1 else 11)
        st.paragraph_format.space_after = Pt(6 if lvl == 1 else 5)
        st.paragraph_format.line_spacing = 1.5

    for section in doc.sections:
        section.page_width = Cm(21)
        section.page_height = Cm(29.7)
        for attr in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
            setattr(section, attr, Cm(2.5))

    B = blocks()

    # ---------------- cover ----------------
    _, t, subt, metas = B[0]
    for _ in range(4):
        doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Pt(0)
    set_run_font(p.add_run(t), HEI, WEST, 18, True)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Pt(0)
    p.paragraph_format.space_before = Pt(18)
    set_run_font(p.add_run(subt), "楷体", WEST, 12)
    doc.add_paragraph()
    for line in metas:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.first_line_indent = Pt(0)
        p.paragraph_format.line_spacing = 1.5
        set_run_font(p.add_run(line), SONG, WEST, 10.5)

    # ---------------- TOC section ----------------
    sec = doc.add_section(WD_SECTION.NEW_PAGE)
    sec.footer.is_linked_to_previous = False
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Pt(0)
    p.paragraph_format.space_after = Pt(12)
    set_run_font(p.add_run("目　录"), HEI, WEST, 16, True)
    add_toc_field(doc)

    # ---------------- body section ----------------
    body = doc.add_section(WD_SECTION.NEW_PAGE)
    body.footer.is_linked_to_previous = False
    restart_numbering(body)
    fp = body.footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_page_field(fp)

    skip_toc = False
    started = False
    for b in B:
        kind = b[0]
        if kind == "titlepage":
            continue
        if not started and kind == "h1" and b[1] == "目录":
            skip_toc = True
            continue
        if skip_toc:
            if kind == "break":
                skip_toc = False
                started = True
            continue
        if kind == "break":
            doc.add_page_break()
            continue
        if kind == "h1":
            add_heading(doc, b[1], 1)
        elif kind == "h2":
            add_heading(doc, b[1], 2)
        elif kind == "p":
            add_body(doc, b[1])
        elif kind == "bullets":
            for item in b[1]:
                p = doc.add_paragraph(style="List Bullet")
                p.paragraph_format.line_spacing = 1.5
                p.paragraph_format.space_after = Pt(3)
                set_run_font(p.add_run(item), SONG, WEST, 12)
        elif kind == "code":
            add_code(doc, b[1])
        elif kind == "table":
            add_table(doc, b[1], b[2])
            doc.add_paragraph().paragraph_format.space_after = Pt(4)
        elif kind == "img":
            add_image(doc, b[1], b[2])
        elif kind == "imgw":
            add_image(doc, b[1], b[2])
        else:
            raise ValueError(kind)

    # ask Word to refresh fields (TOC + page numbers) on open
    settings = doc.settings.element
    upd = OxmlElement("w:updateFields")
    upd.set(qn("w:val"), "true")
    settings.append(upd)

    doc.save(str(OUT))
    print("built", OUT, OUT.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
