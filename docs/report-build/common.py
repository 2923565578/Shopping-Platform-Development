"""Shared layout / builder for the ShopStream final report (EN + ZH)."""
import os
import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, KeepTogether,
)

ASSETS = r"F:\Final Project\ShopStream\docs\report-assets"

ACCENT = colors.HexColor("#1f4e79")
LIGHT = colors.HexColor("#eef3f8")
GRIDC = colors.HexColor("#9fb3c8")


def register_fonts(lang):
    """Return (body_font, mono_font, bold_font)."""
    mono = "Courier"
    if lang == "zh":
        from reportlab.pdfbase.cidfonts import UnicodeCIDFont
        f = r"C:\Windows\Fonts\simhei.ttf"
        pdfmetrics.registerFont(TTFont("SimHei", f))
        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
        return "SimHei", mono
    return "Helvetica", mono


def styles_for(lang):
    font, mono = register_fonts(lang)
    base = getSampleStyleSheet()
    size = 10.5 if lang == "en" else 10.2
    lead = 1.45 * size

    s = {}
    s["title"] = ParagraphStyle(
        "title", parent=base["Normal"], fontName=font, fontSize=26,
        leading=32, textColor=ACCENT, alignment=TA_LEFT, spaceAfter=6,
    )
    s["subtitle"] = ParagraphStyle(
        "subtitle", parent=base["Normal"], fontName=font, fontSize=13,
        leading=18, textColor=colors.HexColor("#33475b"), spaceAfter=4,
    )
    s["meta"] = ParagraphStyle(
        "meta", parent=base["Normal"], fontName=font, fontSize=10,
        leading=15, textColor=colors.HexColor("#4a5b6d"),
    )
    s["h1"] = ParagraphStyle(
        "h1", parent=base["Normal"], fontName=font, fontSize=15, leading=19,
        textColor=ACCENT, spaceBefore=10, spaceAfter=8, alignment=TA_LEFT,
    )
    s["h2"] = ParagraphStyle(
        "h2", parent=base["Normal"], fontName=font, fontSize=11.8, leading=15,
        textColor=colors.HexColor("#26425a"), spaceBefore=8, spaceAfter=5,
    )
    s["body"] = ParagraphStyle(
        "body", parent=base["Normal"], fontName=font, fontSize=size,
        leading=lead, alignment=TA_LEFT, spaceAfter=5,
    )
    s["bullet"] = ParagraphStyle(
        "bullet", parent=s["body"], leftIndent=14, bulletIndent=4, spaceAfter=3,
    )
    code_font = font if lang == "zh" else mono
    s["code"] = ParagraphStyle(
        "code", parent=base["Normal"], fontName=code_font, fontSize=8.2, leading=10.5,
        textColor=colors.HexColor("#20303f"), backColor=colors.HexColor("#f5f7fa"),
        borderPadding=(4, 5, 4, 5), spaceBefore=3, spaceAfter=6,
    )
    s["caption"] = ParagraphStyle(
        "caption", parent=base["Normal"], fontName=font, fontSize=8.6,
        leading=11, textColor=colors.HexColor("#4a5b6d"), alignment=TA_CENTER,
        spaceBefore=2, spaceAfter=10,
    )
    s["th"] = ParagraphStyle(
        "th", parent=base["Normal"], fontName=font, fontSize=8.8, leading=11,
        textColor=colors.white,
    )
    s["td"] = ParagraphStyle(
        "td", parent=base["Normal"], fontName=font, fontSize=8.8, leading=11.4,
    )
    s["tdk"] = ParagraphStyle(
        "tdk", parent=s["td"], textColor=colors.HexColor("#12324f"),
    )
    s["toc"] = ParagraphStyle(
        "toc", parent=s["body"], fontSize=9.8, leading=17,
    )
    return s, font


class Doc(BaseDocTemplate):
    def __init__(self, path, title, lang, **kw):
        self.report_title = title
        self.lang = lang
        super().__init__(
            path, pagesize=A4,
            leftMargin=2.0 * cm, rightMargin=2.0 * cm,
            topMargin=1.9 * cm, bottomMargin=1.7 * cm,
            title=title, author="Xu Haojie (DTR5N0)",
            subject="ShopStream final project report",
            **kw,
        )
        self.lang = lang  # set after super().__init__: BaseDocTemplate defines .lang
        frame = Frame(
            self.leftMargin, self.bottomMargin,
            self.width, self.height, id="normal",
        )
        self.addPageTemplates([
            PageTemplate(id="page", frames=[frame], onPage=self._decorate),
        ])

    def _decorate(self, canv, doc):
        canv.saveState()
        folio_font = "Helvetica"
        if self.lang == "zh":
            folio_font = "STSong-Light"
        canv.setFont(folio_font, 8)
        canv.setFillColor(colors.HexColor("#7a8a99"))
        canv.drawString(2.0 * cm, 1.05 * cm, self.report_title)
        canv.drawRightString(A4[0] - 2.0 * cm, 1.05 * cm, str(doc.page))
        canv.setStrokeColor(colors.HexColor("#c9d6e2"))
        canv.setLineWidth(0.5)
        canv.line(2.0 * cm, 1.35 * cm, A4[0] - 2.0 * cm, 1.35 * cm)
        canv.restoreState()


def esc(text):
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def table(data, widths, st, header=True, zebra=True, font=None):
    """data: list of rows; each cell is str (wrapped as Paragraph)."""
    ncols = len(data[0])
    usable = 17.0 * cm
    widths = list(widths[:ncols])
    if len(widths) < ncols:
        widths += [usable / ncols] * (ncols - len(widths))
    total = sum(widths)
    if total < usable:
        idx = 2 if ncols > 2 else ncols - 1
        widths[idx] += usable - total
    rows = []
    for r, row in enumerate(data):
        cur = []
        for cell in row:
            style = st["th"] if (header and r == 0) else st["td"]
            txt = cell if cell.startswith("<") else esc(cell).replace("\n", "<br/>")
            cur.append(Paragraph(txt, style))
        rows.append(cur)
    t = Table(rows, colWidths=widths, repeatRows=1 if header else 0)
    cmds = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, GRIDC),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]
    if header:
        cmds += [("BACKGROUND", (0, 0), (-1, 0), ACCENT)]
    if zebra:
        for i in range(1, len(rows)):
            if i % 2 == 0:
                cmds += [("BACKGROUND", (0, i), (-1, i), LIGHT)]
    t.setStyle(TableStyle(cmds))
    return t


def image(fname, st, width=None, max_h=None):
    path = os.path.join(ASSETS, fname)
    from PIL import Image as PILImage
    with PILImage.open(path) as im:
        w, h = im.size
    width = width or (17.0 * cm)
    height = width * (h / w)
    if max_h and height > max_h:
        height = max_h
        width = height * (w / h)
    return Image(path, width=width, height=height)


def _flowable(b, st, font):
    """One content block -> list of flowables (no page handling)."""
    kind = b[0]
    if kind == "h2":
        return [Paragraph(esc(b[1]), st["h2"])]
    if kind == "code":
        return [Paragraph(esc(b[1]).replace("\n", "<br/>"), st["code"])]
    if kind == "bullets":
        out = [Paragraph(esc(x), st["bullet"], bulletText="\u2022") for x in b[1]]
        out.append(Spacer(1, 3))
        return out
    if kind == "table":
        _, data, widths = b[0:3]
        return [table(data, widths, st, font=font), Spacer(1, 7)]
    if kind == "img":
        _, fname, cap = b
        return [image(fname, st), Paragraph(esc(cap), st["caption"])]
    if kind == "imgw":
        _, fname, cap, wcm, mxh = b
        return [image(fname, st, width=wcm * cm, max_h=mxh * cm),
                Paragraph(esc(cap), st["caption"])]
    raise ValueError(kind)


def build(blocks, out_path, title, lang):
    st, font = styles_for(lang)
    doc = Doc(out_path, title, lang)
    story = []
    skip = set()
    for i, b in enumerate(blocks):
        if i in skip:
            continue
        kind = b[0]
        if kind == "titlepage":
            _, t, subt, metas = b
            story.append(Spacer(1, 2.2 * cm))
            story.append(Paragraph(esc(t), st["title"]))
            story.append(Spacer(1, 0.15 * cm))
            story.append(Paragraph(esc(subt), st["subtitle"]))
            story.append(Spacer(1, 0.6 * cm))
            for line in metas:
                story.append(Paragraph(line, st["meta"]))
            story.append(Spacer(1, 0.8 * cm))
        elif kind == "h1":
            story.append(Paragraph(esc(b[1]), st["h1"]))
        elif kind == "h2":
            head = Paragraph(esc(b[1]), st["h2"])
            # do not leave a heading alone at the bottom of a page
            nxt = blocks[i + 1] if i + 1 < len(blocks) else None
            if nxt and nxt[0] in ("img", "imgw", "table"):
                story.append(KeepTogether([head] + _flowable(nxt, st, font)))
                skip.add(i + 1)
            else:
                story.append(head)
        elif kind == "p":
            para = Paragraph(esc(b[1]), st["body"])
            # a short lead-in line ("Step 4: ...") must not sit alone above its code block
            nxt = blocks[i + 1] if i + 1 < len(blocks) else None
            if nxt and nxt[0] in ("code", "bullets") and len(b[1]) <= 200:
                story.append(KeepTogether([para] + _flowable(nxt, st, font)))
                skip.add(i + 1)
            else:
                story.append(para)
        elif kind == "bullets":
            for item in b[1]:
                story.append(Paragraph(esc(item), st["bullet"], bulletText="\u2022"))
            story.append(Spacer(1, 3))
        elif kind == "code":
            story.append(KeepTogether([Paragraph(esc(b[1]).replace("\n", "<br/>"), st["code"])]))
        elif kind == "table":
            _, data, widths = b[0:3]
            story.append(table(data, widths, st, font=font))
            story.append(Spacer(1, 7))
        elif kind == "img":
            _, fname, cap = b
            story.append(KeepTogether([image(fname, st), Paragraph(esc(cap), st["caption"])]))
        elif kind == "imgw":
            _, fname, cap, wcm, mxh = b
            story.append(KeepTogether([
                image(fname, st, width=wcm * cm, max_h=mxh * cm),
                Paragraph(esc(cap), st["caption"]),
            ]))
        elif kind == "break":
            story.append(PageBreak())
        elif kind == "gap":
            story.append(Spacer(1, b[1] * cm))
        else:
            raise ValueError(kind)
    doc.build(story)
    return out_path
