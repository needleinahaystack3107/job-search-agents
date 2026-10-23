"""Build a plain, single-column DOCX resume from markdown, and check what a parser would read back.

  python3 scripts/resume_doc.py build applications/<name>/resume.md      writes Last_First_Resume_<MonYYYY>.docx beside it
  python3 scripts/resume_doc.py check applications/<name>/Last_First_Resume_<MonYYYY>.docx --keywords "dbt,Airflow,Snowflake"

Markdown understood: first line = name, second = contact line, "## Section", "- bullet",
"**bold**", and plain paragraphs. No tables, columns, text boxes or images are ever produced,
because those are what resume parsers get wrong. Standard library only.

`check` reads the text back out of the file the way a simple parser would. It is a local
approximation, not the employer's real ATS.
"""
import argparse
import datetime
import json
import re
import sys
import unicodedata
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

FONT = "Calibri"
BODY_HALF_POINTS = 21  # 10.5pt
ONE_PAGE_WORDS = 620   # rough ceiling for one page at this font size and margin
STANDARD_SECTIONS = ("Experience", "Education", "Skills")

CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
<Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>
</Types>"""
RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""
DOC_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering" Target="numbering.xml"/>
</Relationships>"""
W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
NUMBERING = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:numbering {W}>
<w:abstractNum w:abstractNumId="0"><w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="bullet"/><w:lvlText w:val="•"/><w:lvlJc w:val="left"/>
<w:pPr><w:ind w:left="300" w:hanging="200"/></w:pPr></w:lvl></w:abstractNum>
<w:num w:numId="1"><w:abstractNumId w:val="0"/></w:num>
</w:numbering>"""


def runs(text, size=BODY_HALF_POINTS, bold=False):
    """Turn text with **bold** spans into Word runs."""
    out = []
    for i, part in enumerate(re.split(r"\*\*(.+?)\*\*", text)):
        if not part:
            continue
        b = "<w:b/>" if (bold or i % 2) else ""
        out.append(
            f'<w:r><w:rPr><w:rFonts w:ascii="{FONT}" w:hAnsi="{FONT}"/>{b}<w:sz w:val="{size}"/></w:rPr>'
            f'<w:t xml:space="preserve">{escape(part)}</w:t></w:r>'
        )
    return "".join(out)


def para(text, props="", **run_args):
    return f'<w:p><w:pPr><w:spacing w:before="0" w:after="20"/>{props}</w:pPr>{runs(text, **run_args)}</w:p>'


def to_document_xml(markdown):
    lines = [l.rstrip() for l in markdown.splitlines() if l.strip() and l.strip() != "---"]
    body = [
        para(lines[0].strip("*# "), '<w:jc w:val="center"/>', size=30, bold=True),
        para(lines[1], '<w:jc w:val="center"/>'),
    ]
    for line in lines[2:]:
        if line.startswith("## "):
            rule = '<w:pBdr><w:bottom w:val="single" w:sz="6" w:space="1" w:color="000000"/></w:pBdr><w:spacing w:before="120" w:after="40"/>'
            body.append(f'<w:p><w:pPr>{rule}</w:pPr>{runs(line[3:].upper(), size=22, bold=True)}</w:p>')
        elif line.startswith("- "):
            body.append(para(line[2:], '<w:numPr><w:ilvl w:val="0"/><w:numId w:val="1"/></w:numPr>'))
        else:
            body.append(para(line))
    margins = '<w:sectPr><w:pgSz w:w="12240" w:h="15840"/><w:pgMar w:top="720" w:right="800" w:bottom="720" w:left="800" w:header="0" w:footer="0" w:gutter="0"/></w:sectPr>'
    return f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document {W}><w:body>{"".join(body)}{margins}</w:body></w:document>'


def resume_file_name(name_line, when=None):
    """The name a recruiter sees: Last_First_Resume_MonYYYY.docx, from the resume's first line."""
    when = when or datetime.date.today()
    parts = re.sub(r"[^A-Za-z\s-]", "", name_line).split()
    stem = "_".join([p.capitalize() for p in (parts[-1:] + parts[:-1])]) if parts else "Resume"
    return "%s_Resume_%s.docx" % (stem, when.strftime("%b%Y"))


def build(args):
    src = Path(args.markdown)
    first = next((l for l in src.read_text().splitlines() if l.strip()), "")
    out = src.with_name(resume_file_name(first.strip("*# ")))
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", CONTENT_TYPES)
        z.writestr("_rels/.rels", RELS)
        z.writestr("word/_rels/document.xml.rels", DOC_RELS)
        z.writestr("word/numbering.xml", NUMBERING)
        z.writestr("word/document.xml", to_document_xml(src.read_text()))
    print(out)


def read_back(docx_path):
    """Paragraph texts in order, as a parser that ignores formatting would see them."""
    xml = zipfile.ZipFile(docx_path).read("word/document.xml").decode()
    paragraphs = []
    for p in re.findall(r"<w:p>.*?</w:p>", xml, flags=re.S):
        text = "".join(re.findall(r"<w:t[^>]*>(.*?)</w:t>", p, flags=re.S))
        paragraphs.append(text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">"))
    return paragraphs


EXPECTED_PARTS = {"[Content_Types].xml", "_rels/.rels", "word/_rels/document.xml.rels",
                  "word/numbering.xml", "word/document.xml"}


def hidden_marks(docx_path):
    """Things a reader cannot see but a tool can: invisible characters, file properties, extra parts."""
    z = zipfile.ZipFile(docx_path)
    names = z.namelist()
    body = re.sub(r"<[^>]+>", "", z.read("word/document.xml").decode())
    hidden = sorted({"U+%04X %s" % (ord(c), unicodedata.name(c, "unnamed")) for c in body
                     if unicodedata.category(c) in ("Cf", "Co", "Cn", "Zl", "Zp")
                     or (unicodedata.category(c) == "Zs" and c != " ")})
    metadata = {}
    for name in names:
        if name.startswith("docProps/") or name.startswith("customXml/"):
            xml = z.read(name).decode(errors="replace")
            for tag, value in re.findall(r"<(?:\w+:)?(\w+)[^>]*>([^<]+)</", xml):
                metadata["%s:%s" % (name, tag)] = value.strip()
    return hidden, metadata, sorted(set(names) - EXPECTED_PARTS)


def check(args):
    paragraphs = read_back(args.docx)
    hidden, metadata, extra_parts = hidden_marks(args.docx)
    text = "\n".join(paragraphs)
    words = len(text.split())
    keywords = [k.strip() for k in (args.keywords or "").split(",") if k.strip()]
    missing = [k for k in keywords if not re.search(r"(?<!\w)" + re.escape(k) + r"(?!\w)", text, re.I)]
    report = {
        "name_line": paragraphs[0],
        "email_found": bool(re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", paragraphs[1])),
        "phone_found": bool(re.search(r"\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}", paragraphs[1])),
        "sections_found": [p.title() for p in paragraphs if p.isupper() and len(p) < 30][1:],
        "standard_sections_missing": [s for s in STANDARD_SECTIONS if s.upper() not in paragraphs],
        "date_ranges_found": len(re.findall(r"[A-Z][a-z]{2} \d{4} – (?:[A-Z][a-z]{2} \d{4}|Present)", text)),
        "words": words,
        "likely_one_page": words <= ONE_PAGE_WORDS,
        "keywords_present": [k for k in keywords if k not in missing],
        "keywords_missing": missing,
        "odd_characters": sorted(set(re.findall(r"[^\x00-\x7F–—·•]", text))),
        "hidden_characters": hidden,
        "file_metadata": metadata,
        "unexpected_file_parts": extra_parts,
    }
    print(json.dumps(report, indent=1, ensure_ascii=False))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("build"); s.add_argument("markdown"); s.set_defaults(fn=build)
    s = sub.add_parser("check"); s.add_argument("docx"); s.add_argument("--keywords"); s.set_defaults(fn=check)
    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
