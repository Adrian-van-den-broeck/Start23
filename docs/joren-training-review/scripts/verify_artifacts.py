"""Offline PDF/workbook package integrity and visual-review contact sheets."""

import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile

import pdfplumber
from PIL import Image, ImageDraw
from pypdf import PdfReader

OUT = Path(__file__).resolve().parents[1]
QA = OUT / "qa"
PDF = OUT / "WOMBO_Complete_Training_Logic.pdf"
XLSX = OUT / "WOMBO_Training_Simulator.xlsx"
reader = PdfReader(PDF)
texts = [page.extract_text() or "" for page in reader.pages]
rules = json.loads((OUT / "fixtures/reviewed_rules.json").read_text(encoding="utf8"))
missing_rules = [r["id"] for r in rules if r["id"] not in "\n".join(texts)]
blank_pages = [i + 1 for i, t in enumerate(texts) if len(t.strip()) < 80]
overflow = []
with pdfplumber.open(PDF) as doc:
    for i, page in enumerate(doc.pages):
        for c in page.chars:
            if (
                c["x0"] < 39
                or c["x1"] > page.width - 39
                or c["top"] < 30
                or c["bottom"] > page.height - 16
            ):
                overflow.append(
                    {
                        "page": i + 1,
                        "char": c["text"],
                        "x0": c["x0"],
                        "x1": c["x1"],
                        "top": c["top"],
                        "bottom": c["bottom"],
                    }
                )

ns = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
with ZipFile(XLSX) as z:
    entries = z.namelist()
    workbook = ET.fromstring(z.read("xl/workbook.xml"))
    sheets = [x.attrib["name"] for x in workbook.findall("s:sheets/s:sheet", ns)]
    formula_count = sum(
        len(ET.fromstring(z.read(n)).findall(".//s:f", ns))
        for n in entries
        if n.startswith("xl/worksheets/sheet") and n.endswith(".xml")
    )
    external_links = [
        n for n in entries if "externalLink" in n or n.endswith("vbaProject.bin")
    ]
    protected = [
        n
        for n in entries
        if n.startswith("xl/worksheets/sheet")
        and n.endswith(".xml")
        and ET.fromstring(z.read(n)).find("s:sheetProtection", ns) is not None
    ]


# Contact sheets are QA aids; full-size page/sheet renders remain available.
def contacts(files, prefix, tile=(600, 850), per=8):
    output = []
    for start in range(0, len(files), per):
        batch = files[start : start + per]
        canvas = Image.new(
            "RGB", (tile[0] * 2, tile[1] * ((len(batch) + 1) // 2)), "#dce3eb"
        )
        draw = ImageDraw.Draw(canvas)
        for idx, file in enumerate(batch):
            img = Image.open(file).convert("RGB")
            img.thumbnail((tile[0] - 12, tile[1] - 34))
            xx = (idx % 2) * tile[0] + 6
            yy = (idx // 2) * tile[1] + 28
            canvas.paste(img, (xx, yy))
            draw.text((xx, yy - 20), file.stem, fill="#243c58")
        target = QA / (prefix + f"-{start // per + 1:02d}.png")
        canvas.save(target)
        output.append(str(target))
    return output


pages = sorted((QA / "pdf-final").glob("page-*.png"))
sheet_images = sorted(QA.glob("[0-2][0-9]_*.png"))
result = {
    "pdf_pages": len(reader.pages),
    "rendered_pdf_pages": len(pages),
    "pdf_blank_pages": blank_pages,
    "pdf_missing_rule_ids": missing_rules,
    "pdf_out_of_margin_chars": overflow,
    "pdf_replacement_characters": sum(t.count("\ufffd") for t in texts),
    "workbook_sheets": sheets,
    "workbook_formula_count": formula_count,
    "workbook_external_links_or_vba": external_links,
    "protected_sheets": protected,
    "pdf_contact_sheets": contacts(pages, "pdf-contact"),
    "workbook_contact_sheets": contacts(
        sheet_images, "workbook-contact", tile=(900, 570), per=6
    ),
    "pdf_sha256": hashlib.sha256(PDF.read_bytes()).hexdigest(),
    "xlsx_sha256": hashlib.sha256(XLSX.read_bytes()).hexdigest(),
    "visual_review": (
        "FINAL PDF PAGES AND 29 WORKSHEET SAMPLE RENDERS INSPECTED"
        if "--visual-review-confirmed" in sys.argv
        else "PENDING VISUAL INSPECTION; structural checks alone are insufficient"
    ),
}
(QA / "artifact-validation.json").write_text(
    json.dumps(result, indent=2, ensure_ascii=False), encoding="utf8"
)
print(
    json.dumps(
        {
            k: v
            for k, v in result.items()
            if k not in ["workbook_sheets", "pdf_out_of_margin_chars"]
        }
    )
)
if (
    missing_rules
    or blank_pages
    or overflow
    or len(pages) != len(reader.pages)
    or len(sheets) != 29
    or external_links
    or protected
):
    raise SystemExit("Artifact structural QA failed; see qa/artifact-validation.json")
