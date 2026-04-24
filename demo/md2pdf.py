#!/usr/bin/env python3
"""Convert wechat-article.md to styled HTML and PDF"""
import re
import os
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MD_FILE = os.path.join(SCRIPT_DIR, "wechat-article.md")
HTML_FILE = os.path.join(SCRIPT_DIR, "wechat-article.html")
PDF_FILE = os.path.join(SCRIPT_DIR, "wechat-article.pdf")

# Read markdown
with open(MD_FILE, "r") as f:
    md = f.read()

# Simple markdown → HTML conversion (no external deps)
def md_to_html(text):
    lines = text.split("\n")
    html_lines = []
    in_code = False
    in_list = False

    for line in lines:
        # Code blocks
        if line.strip().startswith("```"):
            if in_code:
                html_lines.append("</code></pre>")
                in_code = False
            else:
                html_lines.append('<pre style="background:#1e1e2e;color:#cdd6f4;padding:16px;border-radius:8px;font-size:13px;line-height:1.5;overflow-x:auto;"><code>')
                in_code = True
            continue
        if in_code:
            html_lines.append(line.replace("<", "&lt;").replace(">", "&gt;"))
            continue

        # Headings
        if line.startswith("# "):
            html_lines.append(f'<h1 style="font-size:28px;font-weight:700;margin:40px 0 16px;color:#1a1a2e;">{line[2:]}</h1>')
            continue
        if line.startswith("## "):
            html_lines.append(f'<h2 style="font-size:22px;font-weight:700;margin:36px 0 12px;color:#1a1a2e;border-bottom:2px solid #6c63ff;padding-bottom:8px;">{line[3:]}</h2>')
            continue
        if line.startswith("### "):
            html_lines.append(f'<h3 style="font-size:18px;font-weight:700;margin:28px 0 10px;color:#2d2d44;">{line[4:]}</h3>')
            continue

        # Horizontal rule
        if line.strip() == "---":
            html_lines.append('<hr style="border:none;border-top:1px solid #e0e0e0;margin:32px 0;">')
            continue

        # Bold
        line = re.sub(r'\*\*(.+?)\*\*', r'<strong style="color:#1a1a2e;">\1</strong>', line)

        # Images
        line = re.sub(r'!\[(.+?)\]\((.+?)\)', r'<p style="text-align:center;margin:20px 0;"><img src="\2" style="max-width:100%;border-radius:8px;box-shadow:0 2px 12px rgba(0,0,0,0.1);" alt="\1"></p>', line)

        # Links
        line = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2" style="color:#6c63ff;text-decoration:none;border-bottom:1px solid #6c63ff;">\1</a>', line)

        # Italic
        line = re.sub(r'\*(.+?)\*', r'<em>\1</em>', line)

        # Empty line
        if line.strip() == "":
            if in_list:
                in_list = False
            html_lines.append("")
            continue

        # Regular paragraph
        html_lines.append(f'<p style="font-size:16px;line-height:1.8;color:#333;margin:12px 0;">{line}</p>')

    return "\n".join(html_lines)

body = md_to_html(md)

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>VOC AI — Analyze Amazon Competitor Reviews in 5 Seconds</title>
<style>
@page {{
    size: A4;
    margin: 2cm 2.5cm;
}}
body {{
    font-family: -apple-system, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
    max-width: 680px;
    margin: 0 auto;
    padding: 40px 20px;
    color: #333;
    background: #fff;
}}
h1 {{ page-break-after: avoid; }}
h2 {{ page-break-after: avoid; }}
pre {{ page-break-inside: avoid; }}
</style>
</head>
<body>
{body}
</body>
</html>"""

# Write HTML
with open(HTML_FILE, "w") as f:
    f.write(html)
print(f"HTML saved: {HTML_FILE}")

# Try to convert to PDF using weasyprint
try:
    from weasyprint import HTML as WHTML
    WHTML(filename=HTML_FILE).write_pdf(PDF_FILE)
    print(f"PDF saved: {PDF_FILE}")
except ImportError:
    # Fallback: try cupsfilter or wkhtmltopdf
    try:
        subprocess.run(
            ["/usr/sbin/cupsfilter", "-o", "media=A4", HTML_FILE],
            stdout=open(PDF_FILE, "wb"),
            stderr=subprocess.DEVNULL,
            check=True
        )
        print(f"PDF saved (via cupsfilter): {PDF_FILE}")
    except Exception:
        print("PDF generation requires weasyprint. Install: pip3 install weasyprint")
        print(f"HTML is ready at: {HTML_FILE}")
        print("You can open it in Chrome and Print → Save as PDF")
