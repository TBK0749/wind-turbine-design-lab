"""Generate the Onshape workflow manual PDF from Markdown."""

from __future__ import annotations

import re
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_MD = PROJECT_ROOT / "docs" / "onshape_workflow_manual.md"
OUTPUT_PDF = PROJECT_ROOT / "output" / "pdf" / "Wind_Turbine_Design_Lab_Onshape_Workflow_Manual.pdf"


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "ManualTitle",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=27,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#1F2937"),
            spaceAfter=14,
        ),
        "h2": ParagraphStyle(
            "ManualHeading2",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#111827"),
            spaceBefore=10,
            spaceAfter=7,
        ),
        "h3": ParagraphStyle(
            "ManualHeading3",
            parent=base["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#374151"),
            spaceBefore=8,
            spaceAfter=5,
        ),
        "body": ParagraphStyle(
            "ManualBody",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13.2,
            textColor=colors.HexColor("#1F2937"),
            spaceAfter=6,
        ),
        "bullet": ParagraphStyle(
            "ManualBullet",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.3,
            leading=12.8,
            leftIndent=8,
            textColor=colors.HexColor("#1F2937"),
        ),
        "code": ParagraphStyle(
            "ManualCode",
            parent=base["Code"],
            fontName="Courier",
            fontSize=8,
            leading=10,
            leftIndent=4,
            rightIndent=4,
            backColor=colors.HexColor("#F3F4F6"),
            borderColor=colors.HexColor("#E5E7EB"),
            borderWidth=0.5,
            borderPadding=5,
            spaceBefore=3,
            spaceAfter=7,
        ),
        "footer": ParagraphStyle(
            "ManualFooter",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8,
            textColor=colors.HexColor("#6B7280"),
        ),
    }


def _clean_inline(text: str) -> str:
    """Convert a small Markdown subset to ReportLab paragraph markup."""

    clean = escape(text)
    clean = clean.replace("**", "<b>", 1).replace("**", "</b>", 1)
    while "**" in clean:
        clean = clean.replace("**", "<b>", 1).replace("**", "</b>", 1)
    clean = clean.replace("`", '<font name="Courier">', 1).replace("`", "</font>", 1)
    while "`" in clean:
        clean = clean.replace("`", '<font name="Courier">', 1).replace("`", "</font>", 1)
    return clean


def _paragraph(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(_clean_inline(text), style)


def _table_from_lines(lines: list[str], styles: dict[str, ParagraphStyle]) -> Table:
    rows: list[list[Paragraph]] = []
    for line in lines:
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if all(set(cell) <= {"-", ":", " "} for cell in cells):
            continue
        rows.append([_paragraph(cell, styles["body"]) for cell in cells])

    table = Table(rows, repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E5E7EB")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#111827")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D1D5DB")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def _flush_paragraph(
    story: list,
    paragraph_lines: list[str],
    styles: dict[str, ParagraphStyle],
) -> None:
    if paragraph_lines:
        story.append(_paragraph(" ".join(paragraph_lines), styles["body"]))
        paragraph_lines.clear()


def _flush_bullets(
    story: list,
    bullet_lines: list[str],
    styles: dict[str, ParagraphStyle],
) -> None:
    if not bullet_lines:
        return
    for line in bullet_lines:
        story.append(_paragraph(f"- {line}", styles["bullet"]))
    story.append(Spacer(1, 0.1 * cm))
    bullet_lines.clear()


def _flush_numbered(
    story: list,
    numbered_lines: list[str],
    styles: dict[str, ParagraphStyle],
) -> None:
    if not numbered_lines:
        return
    for line in numbered_lines:
        story.append(_paragraph(line, styles["bullet"]))
    story.append(Spacer(1, 0.1 * cm))
    numbered_lines.clear()


def build_story(markdown_text: str) -> list:
    """Convert the manual Markdown subset to ReportLab flowables."""

    styles = _styles()
    story: list = []
    paragraph_lines: list[str] = []
    bullet_lines: list[str] = []
    numbered_lines: list[str] = []
    table_lines: list[str] = []
    code_lines: list[str] = []
    in_code = False

    for raw_line in markdown_text.splitlines():
        line = raw_line.rstrip()

        if line.startswith("```"):
            if in_code:
                story.append(Preformatted("\n".join(code_lines), styles["code"]))
                code_lines.clear()
                in_code = False
            else:
                _flush_paragraph(story, paragraph_lines, styles)
                _flush_bullets(story, bullet_lines, styles)
                _flush_numbered(story, numbered_lines, styles)
                in_code = True
            continue

        if in_code:
            code_lines.append(line)
            continue

        if line.startswith("|"):
            _flush_paragraph(story, paragraph_lines, styles)
            _flush_bullets(story, bullet_lines, styles)
            _flush_numbered(story, numbered_lines, styles)
            table_lines.append(line)
            continue
        if table_lines:
            story.append(_table_from_lines(table_lines, styles))
            story.append(Spacer(1, 0.18 * cm))
            table_lines.clear()

        if not line:
            _flush_paragraph(story, paragraph_lines, styles)
            _flush_bullets(story, bullet_lines, styles)
            _flush_numbered(story, numbered_lines, styles)
            continue

        if line.startswith("# "):
            _flush_paragraph(story, paragraph_lines, styles)
            _flush_bullets(story, bullet_lines, styles)
            _flush_numbered(story, numbered_lines, styles)
            story.append(_paragraph(line[2:], styles["title"]))
            story.append(Spacer(1, 0.2 * cm))
            continue

        if line.startswith("## "):
            _flush_paragraph(story, paragraph_lines, styles)
            _flush_bullets(story, bullet_lines, styles)
            _flush_numbered(story, numbered_lines, styles)
            story.append(_paragraph(line[3:], styles["h2"]))
            continue

        if line.startswith("### "):
            _flush_paragraph(story, paragraph_lines, styles)
            _flush_bullets(story, bullet_lines, styles)
            _flush_numbered(story, numbered_lines, styles)
            story.append(_paragraph(line[4:], styles["h3"]))
            continue

        if line.startswith("- "):
            _flush_paragraph(story, paragraph_lines, styles)
            _flush_numbered(story, numbered_lines, styles)
            bullet_lines.append(line[2:])
            continue

        if re.match(r"^\d+\. ", line):
            _flush_paragraph(story, paragraph_lines, styles)
            _flush_bullets(story, bullet_lines, styles)
            numbered_lines.append(line)
            continue

        _flush_numbered(story, numbered_lines, styles)
        paragraph_lines.append(line)

    if table_lines:
        story.append(_table_from_lines(table_lines, styles))
    _flush_paragraph(story, paragraph_lines, styles)
    _flush_bullets(story, bullet_lines, styles)
    _flush_numbered(story, numbered_lines, styles)
    return story


def _draw_footer(canvas, document) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#6B7280"))
    canvas.drawString(1.6 * cm, 1.1 * cm, "Wind Turbine Design Lab - Onshape Workflow Manual")
    canvas.drawRightString(19.4 * cm, 1.1 * cm, f"Page {document.page}")
    canvas.restoreState()


def main() -> None:
    OUTPUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    markdown_text = SOURCE_MD.read_text(encoding="utf-8")
    document = SimpleDocTemplate(
        str(OUTPUT_PDF),
        pagesize=A4,
        leftMargin=1.6 * cm,
        rightMargin=1.6 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.7 * cm,
        title="Wind Turbine Design Lab Onshape Workflow Manual",
        author="Wind Turbine Design Lab",
    )
    document.build(build_story(markdown_text), onFirstPage=_draw_footer, onLaterPages=_draw_footer)
    print(OUTPUT_PDF)


if __name__ == "__main__":
    main()
