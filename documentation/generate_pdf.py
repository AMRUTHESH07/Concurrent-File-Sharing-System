import re
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether
)

BASE = Path(__file__).resolve().parent
SOURCE = BASE / "project_report.md"
OUTPUT = BASE / "project_report.pdf"

styles = getSampleStyleSheet()

styles.add(ParagraphStyle(
    name="CoverTitle",
    parent=styles["Title"],
    fontSize=23,
    leading=30,
    alignment=TA_CENTER,
    spaceAfter=18,
))

styles.add(ParagraphStyle(
    name="Section",
    parent=styles["Heading1"],
    fontSize=16,
    leading=20,
    spaceBefore=15,
    spaceAfter=9,
    textColor=colors.HexColor("#17365D"),
    keepWithNext=True,
))

styles.add(ParagraphStyle(
    name="Subsection",
    parent=styles["Heading2"],
    fontSize=12,
    leading=16,
    spaceBefore=10,
    spaceAfter=6,
    textColor=colors.HexColor("#24527A"),
    keepWithNext=True,
))

styles.add(ParagraphStyle(
    name="BodyCustom",
    parent=styles["BodyText"],
    fontSize=10,
    leading=15,
    alignment=4,
    spaceAfter=8,
))

styles.add(ParagraphStyle(
    name="BulletCustom",
    parent=styles["BodyText"],
    fontSize=10,
    leading=14,
    leftIndent=16,
    firstLineIndent=-9,
    spaceAfter=4,
))

styles.add(ParagraphStyle(
    name="TableCell",
    parent=styles["BodyText"],
    fontSize=8.5,
    leading=11,
))

def inline_format(text):
    text = escape(text.strip())
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`(.+?)`", r"<font name='Courier'>\1</font>", text)
    return text

def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.grey)
    canvas.drawString(20 * mm, 12 * mm, "Concurrent File Sharing System Using SDN")
    canvas.drawRightString(190 * mm, 12 * mm, f"Page {doc.page}")
    canvas.restoreState()

if not SOURCE.exists():
    raise FileNotFoundError(f"Report not found: {SOURCE}")

lines = SOURCE.read_text(encoding="utf-8").splitlines()

doc = SimpleDocTemplate(
    str(OUTPUT),
    pagesize=A4,
    rightMargin=20 * mm,
    leftMargin=20 * mm,
    topMargin=20 * mm,
    bottomMargin=22 * mm,
    title="Concurrent File Sharing System Using Software-Defined Networking",
    author="Project Report",
)

story = []

# Cover page
title = "Concurrent File Sharing System Using Software-Defined Networking"
story.append(Spacer(1, 55 * mm))
story.append(Paragraph(escape(title), styles["CoverTitle"]))
story.append(Spacer(1, 12 * mm))
story.append(Paragraph("PROJECT REPORT", ParagraphStyle(
    "CoverLabel", parent=styles["Heading2"],
    alignment=TA_CENTER, fontSize=15, spaceAfter=12
)))
story.append(Spacer(1, 65 * mm))
story.append(Paragraph(
    "Department Project Documentation",
    ParagraphStyle("CoverInfo", parent=styles["BodyText"],
                   alignment=TA_CENTER, fontSize=11)
))
story.append(PageBreak())

# Report body
i = 0
while i < len(lines):
    line = lines[i].strip()

    if not line or line == "---":
        i += 1
        continue

    if line.startswith("# "):
        i += 1
        continue

    if line.startswith("## "):
        story.append(Paragraph(escape(line[3:]), styles["Section"]))
        i += 1
        continue

    if line.startswith("### "):
        story.append(Paragraph(escape(line[4:]), styles["Subsection"]))
        i += 1
        continue

    # Markdown table
    if line.startswith("|") and i + 1 < len(lines) and lines[i + 1].strip().startswith("|"):
        rows = []
        while i < len(lines) and lines[i].strip().startswith("|"):
            cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
            if not all(re.fullmatch(r":?-{2,}:?", c) for c in cells):
                rows.append([
                    Paragraph(inline_format(c), styles["TableCell"])
                    for c in cells
                ])
            i += 1

        if rows:
            col_count = max(len(row) for row in rows)
            page_width = A4[0] - 40 * mm
            table = Table(
                rows,
                colWidths=[page_width / col_count] * col_count,
                repeatRows=1,
                hAlign="LEFT",
            )
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D9EAF7")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#17365D")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))
            story.append(KeepTogether([table, Spacer(1, 8)]))
        continue

    if line.startswith("- "):
        story.append(Paragraph(
            "• " + inline_format(line[2:]),
            styles["BulletCustom"]
        ))
        i += 1
        continue

    # Normal paragraph; join wrapped Markdown lines
    paragraph_lines = [line]
    i += 1
    while i < len(lines):
        next_line = lines[i].strip()
        if (
            not next_line
            or next_line.startswith("#")
            or next_line.startswith("|")
            or next_line.startswith("- ")
        ):
            break
        paragraph_lines.append(next_line)
        i += 1

    story.append(Paragraph(
        inline_format(" ".join(paragraph_lines)),
        styles["BodyCustom"]
    ))

doc.build(story, onFirstPage=footer, onLaterPages=footer)

print(f"PDF created successfully: {OUTPUT}")
print(f"PDF size: {OUTPUT.stat().st_size:,} bytes")
