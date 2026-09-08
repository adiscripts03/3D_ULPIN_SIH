import os
import re
import subprocess
import markdown

MD_PATH = "docs/master_technical_document.md"
HTML_PATH = "docs/master_technical_document_temp.html"
PDF_PATH = "docs/master_technical_document.pdf"

if not os.path.exists(MD_PATH):
    raise FileNotFoundError(f"Markdown file not found: {MD_PATH}")

with open(MD_PATH, "r", encoding="utf-8") as f:
    raw_md = f.read()

# Preprocess GitHub-style alerts like > [!NOTE], > [!WARNING], > [!IMPORTANT]
def format_alerts(text):
    alert_pattern = re.compile(
        r'^(?:>\s*)?\[\!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*\n((?:>.*(?:\n|$))*)',
        re.MULTILINE
    )
    def replace_alert(m):
        alert_type = m.group(1).upper()
        content = m.group(2)
        lines = [re.sub(r'^>\s?', '', line) for line in content.strip().split('\n')]
        body = '\n'.join(lines)
        return f'<div class="alert alert-{alert_type.lower()}"><div class="alert-title">{alert_type}</div><div class="alert-body">{body}</div></div>\n'
    return alert_pattern.sub(replace_alert, text)

processed_md = format_alerts(raw_md)

# Convert Markdown to HTML
html_body = markdown.markdown(
    processed_md,
    extensions=["tables", "fenced_code", "nl2br", "sane_lists", "def_list", "attr_list"]
)

# Convert mermaid code blocks to <div class="mermaid">
html_body = re.sub(
    r'<pre><code class="language-mermaid">([\s\S]*?)</code></pre>',
    r'<div class="mermaid-container"><div class="mermaid">\1</div></div>',
    html_body
)

# Wrap HTTP methods in clean badges
html_body = re.sub(r'<td><code>GET</code></td>', r'<td><span class="badge badge-get">GET</span></td>', html_body)
html_body = re.sub(r'<td><code>POST</code></td>', r'<td><span class="badge badge-post">POST</span></td>', html_body)
html_body = re.sub(r'<td>GET</td>', r'<td><span class="badge badge-get">GET</span></td>', html_body)
html_body = re.sub(r'<td>POST</td>', r'<td><span class="badge badge-post">POST</span></td>', html_body)

# Strip out duplicate top-level title in markdown body
html_body = re.sub(r'<h1>3D ULPIN.*?</h1>\s*<hr\s*/?>', '', html_body, flags=re.DOTALL)

# Complete HTML Document
html_document = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>3D ULPIN — Master Technical Document</title>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<script>
  document.addEventListener("DOMContentLoaded", function() {{
    mermaid.initialize({{
      startOnLoad: true,
      theme: 'neutral',
      securityLevel: 'loose',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
    }});
  }});
</script>
<style>
    @page {{
        size: A4;
        margin: 14mm 14mm 14mm 14mm;
        @bottom-right {{
            content: "Page " counter(page);
            font-size: 8pt;
            color: #64748b;
        }}
    }}
    
    * {{
        box-sizing: border-box;
    }}

    body {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        color: #0f172a;
        line-height: 1.48;
        font-size: 8.8pt;
        background-color: #ffffff;
        margin: 0;
        padding: 0;
    }}

    .header-banner {{
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
        color: #ffffff;
        padding: 22px 26px;
        border-radius: 8px;
        margin-bottom: 20px;
        page-break-after: avoid;
        break-after: avoid;
    }}

    .header-banner h1 {{
        color: #ffffff;
        border-bottom: none;
        margin: 0 0 6px 0;
        padding: 0;
        font-size: 19pt;
        letter-spacing: -0.02em;
    }}

    .header-banner .subtitle {{
        font-size: 9.5pt;
        color: #93c5fd;
        margin: 0;
        font-weight: 500;
    }}

    .header-banner .meta {{
        font-size: 8pt;
        color: #cbd5e1;
        margin-top: 10px;
        display: flex;
        gap: 20px;
    }}

    h1, h2, h3, h4 {{
        color: #0f172a;
        font-weight: 700;
        page-break-after: avoid;
        break-after: avoid;
    }}

    h1 {{
        font-size: 15pt;
        color: #1e3a8a;
        border-bottom: 2px solid #3b82f6;
        padding-bottom: 4px;
        margin-top: 1.5em;
        margin-bottom: 0.5em;
    }}

    h2 {{
        font-size: 12pt;
        color: #0f172a;
        border-bottom: 1.5px solid #e2e8f0;
        padding-bottom: 3px;
        margin-top: 1.3em;
        margin-bottom: 0.4em;
    }}

    h3 {{
        font-size: 9.8pt;
        color: #1e293b;
        margin-top: 1em;
        margin-bottom: 0.3em;
    }}

    p, ul, ol {{
        margin-top: 0.3em;
        margin-bottom: 0.45em;
    }}

    li {{
        margin-bottom: 0.2em;
    }}

    hr {{
        border: none;
        border-top: 1px solid #e2e8f0;
        margin: 1.1em 0;
    }}

    /* Tables */
    table {{
        width: 100%;
        border-collapse: collapse;
        margin: 0.7em 0 1em 0;
        font-size: 7.8pt;
        page-break-inside: auto;
    }}

    tr {{
        page-break-inside: avoid;
        break-inside: avoid;
    }}

    th, td {{
        border: 1px solid #cbd5e1;
        padding: 5px 7px;
        text-align: left;
        vertical-align: top;
        word-break: break-word;
    }}

    th {{
        background-color: #0f172a;
        color: #ffffff;
        font-weight: 600;
        font-size: 7.8pt;
        letter-spacing: 0.02em;
    }}

    tr:nth-child(even) {{
        background-color: #f8fafc;
    }}

    /* Specific column optimizations */
    th:first-child, td:first-child {{
        white-space: nowrap !important;
        font-weight: 600;
        width: 70px;
    }}

    th:nth-child(4), td:nth-child(4) {{
        white-space: nowrap !important;
        width: 55px;
    }}

    /* HTTP method badges */
    .badge {{
        display: inline-block;
        padding: 2px 6px;
        border-radius: 4px;
        font-weight: 700;
        font-size: 7.5pt;
        letter-spacing: 0.03em;
        text-align: center;
    }}
    .badge-get {{
        background-color: #ecfdf5;
        color: #047857;
        border: 1px solid #a7f3d0;
    }}
    .badge-post {{
        background-color: #eff6ff;
        color: #1d4ed8;
        border: 1px solid #bfdbfe;
    }}

    /* Code Blocks */
    pre {{
        background-color: #0f172a;
        color: #f1f5f9;
        padding: 8px 10px;
        border-radius: 6px;
        font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
        font-size: 7.2pt;
        line-height: 1.35;
        overflow-x: auto;
        white-space: pre-wrap;
        word-break: break-all;
        margin: 0.6em 0;
        page-break-inside: avoid;
        break-inside: avoid;
        border: 1px solid #1e293b;
    }}

    code {{
        font-family: "SFMono-Regular", Consolas, Menlo, monospace;
        font-size: 7.8pt;
        background-color: #f1f5f9;
        color: #0f172a;
        padding: 1px 3px;
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

    /* GitHub-style Alerts */
    .alert {{
        border-radius: 6px;
        padding: 7px 11px;
        margin: 0.7em 0;
        page-break-inside: avoid;
        break-inside: avoid;
        border-left: 4px solid;
    }}

    .alert-title {{
        font-weight: 700;
        font-size: 7.8pt;
        margin-bottom: 2px;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }}

    .alert-body {{
        font-size: 7.8pt;
        line-height: 1.38;
    }}

    .alert-note {{
        background-color: #eff6ff;
        border-color: #3b82f6;
        color: #1e40af;
    }}
    .alert-note .alert-title {{ color: #1d4ed8; }}

    .alert-warning {{
        background-color: #fffbeb;
        border-color: #f59e0b;
        color: #92400e;
    }}
    .alert-warning .alert-title {{ color: #b45309; }}

    .alert-important {{
        background-color: #f5f3ff;
        border-color: #8b5cf6;
        color: #5b21b6;
    }}
    .alert-important .alert-title {{ color: #6d28d9; }}

    /* Mermaid Diagrams */
    .mermaid-container {{
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 12px;
        margin: 0.8em 0;
        text-align: center;
        page-break-inside: avoid;
        break-inside: avoid;
        max-width: 100%;
        overflow: hidden;
    }}

    .mermaid svg {{
        max-width: 100% !important;
        max-height: 420px !important;
        height: auto !important;
        margin: 0 auto;
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

<div class="header-banner">
    <h1>3D ULPIN — Master Technical Document</h1>
    <div class="subtitle">Architectural Reference, System Specifications, Machine Learning Pipeline & Data Models</div>
    <div class="meta">
        <span>Standard: <strong>ISO 19152 LADM v2</strong></span>
        <span>Version: <strong>2.0.0</strong></span>
        <span>Target: <strong>Smart India Hackathon (SIH) — PS 26011</strong></span>
    </div>
</div>

{html_body}

</body>
</html>
"""

with open(HTML_PATH, "w", encoding="utf-8") as f:
    f.write(html_document)

chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
cmd = [
    chrome_path,
    "--headless",
    "--disable-gpu",
    "--no-pdf-header-footer",
    "--run-all-compositor-stages-before-draw",
    "--virtual-time-budget=6000",
    f"--print-to-pdf={PDF_PATH}",
    HTML_PATH
]

print(f"Converting '{MD_PATH}' to '{PDF_PATH}' via Headless Chrome...")
res = subprocess.run(cmd, capture_output=True, text=True)

if res.returncode == 0:
    print(f"✅ PDF successfully generated at: {PDF_PATH}")
    size_kb = os.path.getsize(PDF_PATH) / 1024
    print(f"   Size: {size_kb:.1f} KB")
    if os.path.exists(HTML_PATH):
        os.remove(HTML_PATH)
else:
    print(f"❌ Error generating PDF: {res.stderr}")
