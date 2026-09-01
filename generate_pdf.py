import os
import subprocess
import markdown

MD_PATH = "docs/SIH_PS26011_Tech_Alignment_Report.md"
HTML_PATH = "docs/report_temp.html"
PDF_PATH = "docs/SIH_PS26011_Tech_Alignment_Report.pdf"

with open(MD_PATH, "r", encoding="utf-8") as f:
    md_content = f.read()

# Convert Markdown to HTML with extra extensions (tables, fenced code, etc.)
html_body = markdown.markdown(
    md_content,
    extensions=["tables", "fenced_code", "nl2br", "sane_lists", "def_list"]
)

# Custom High-Quality CSS for PDF Printing
html_document = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>SIH PS 26011 Technical Analysis & Alignment Report</title>
<script>
MathJax = {{
  tex: {{
    inlineMath: [['$', '$'], ['\\\\(', '\\\\)']]
  }},
  svg: {{
    fontCache: 'global'
  }}
}};
</script>
<script type="text/javascript" id="MathJax-script" async
  src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js">
</script>
<style>
    @page {{
        size: A4;
        margin: 18mm 16mm 18mm 16mm;
    }}
    
    body {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        color: #1e293b;
        line-height: 1.55;
        font-size: 10pt;
        background-color: #ffffff;
        margin: 0;
        padding: 0;
    }}

    h1, h2, h3, h4, h5, h6 {{
        color: #0f172a;
        font-weight: 700;
        margin-top: 1.4em;
        margin-bottom: 0.5em;
        page-break-after: avoid;
    }}

    h1 {{
        font-size: 18pt;
        color: #1e3a8a;
        border-bottom: 2.5px solid #2563eb;
        padding-bottom: 6px;
        margin-top: 0;
    }}

    h2 {{
        font-size: 13pt;
        color: #1e293b;
        border-bottom: 1.5px solid #cbd5e1;
        padding-bottom: 4px;
        margin-top: 1.5em;
    }}

    h3 {{
        font-size: 11pt;
        color: #334155;
        margin-top: 1.2em;
    }}

    p, ul, ol {{
        margin-top: 0.4em;
        margin-bottom: 0.6em;
    }}

    li {{
        margin-bottom: 0.3em;
    }}

    hr {{
        border: none;
        border-top: 1px solid #e2e8f0;
        margin: 1.2em 0;
    }}

    table {{
        width: 100%;
        border-collapse: collapse;
        margin: 1em 0;
        font-size: 8.5pt;
        page-break-inside: avoid;
    }}

    th, td {{
        border: 1px solid #cbd5e1;
        padding: 6px 8px;
        text-align: left;
        vertical-align: top;
    }}

    th {{
        background-color: #0f172a;
        color: #ffffff;
        font-weight: 600;
    }}

    tr:nth-child(even) {{
        background-color: #f8fafc;
    }}

    pre {{
        background-color: #0f172a;
        color: #e2e8f0;
        padding: 10px 12px;
        border-radius: 6px;
        font-family: "SFMono-Regular", Menlo, Monaco, Consolas, "Liberation Mono", monospace;
        font-size: 7.5pt;
        line-height: 1.35;
        overflow-x: auto;
        white-space: pre-wrap;
        word-break: break-all;
        margin: 0.8em 0;
        page-break-inside: avoid;
    }}

    code {{
        font-family: "SFMono-Regular", Menlo, Monaco, Consolas, monospace;
        font-size: 8.5pt;
        background-color: #f1f5f9;
        color: #0f172a;
        padding: 1px 4px;
        border-radius: 3px;
        border: 1px solid #e2e8f0;
    }}

    pre code {{
        background-color: transparent;
        color: inherit;
        padding: 0;
        border: none;
        font-size: inherit;
    }}

    blockquote {{
        border-left: 4px solid #2563eb;
        background-color: #eff6ff;
        color: #1e3a8a;
        margin: 0.8em 0;
        padding: 8px 12px;
        border-radius: 0 5px 5px 0;
        page-break-inside: avoid;
    }}

    blockquote p {{
        margin: 0;
    }}

    @media print {{
        body {{
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
        }}
    }}
</style>
</head>
<body>
{html_body}
</body>
</html>
"""

with open(HTML_PATH, "w", encoding="utf-8") as f:
    f.write(html_document)

# Use headless Chrome to generate the PDF
chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
cmd = [
    chrome_path,
    "--headless",
    "--disable-gpu",
    "--no-pdf-header-footer",
    "--run-all-compositor-stages-before-draw",
    "--virtual-time-budget=2000",
    f"--print-to-pdf={PDF_PATH}",
    HTML_PATH
]

print("Converting HTML to PDF via Headless Chrome...")
res = subprocess.run(cmd, capture_output=True, text=True)

if res.returncode == 0:
    print(f"✅ PDF successfully generated at: {PDF_PATH}")
    if os.path.exists(HTML_PATH):
        os.remove(HTML_PATH)
else:
    print(f"❌ Error generating PDF: {res.stderr}")
