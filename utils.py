import sqlite3
from fpdf import FPDF
import re
import json

DB_FILE = "reports.db"

# ------------------ Safe Text ------------------
def safe_text(text):
    """Convert input to string and remove unsupported characters for Latin-1 PDF."""
    if not isinstance(text, str):
        text = str(text)
    # Replace problematic Unicode characters with safe equivalents
    replacements = {
        "\u2013": "-",  # en dash
        "\u2014": "-",  # em dash
        "\u2018": "'",  # left single quote
        "\u2019": "'",  # right single quote
        "\u201c": '"',  # left double quote
        "\u201d": '"',  # right double quote
        "\xa0": " ",    # non-breaking space
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    # Remove any remaining non-Latin-1 characters
    text = text.encode("latin-1", errors="replace").decode("latin-1")
    return text

def get_reports():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, query, timestamp FROM reports ORDER BY timestamp DESC")
    reports = c.fetchall()
    conn.close()
    return reports

def get_report_by_id(report_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM reports WHERE id=?", (report_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {
            "id": row[0],
            "query": row[1],
            "summary": json.loads(row[2]) if row[2] else [],
            "titles": json.loads(row[3]) if row[3] else [],
            "urls": json.loads(row[4]) if row[4] else [],
            "timestamp": row[5]
        }
    return None

# ------------------ PDF Generation ------------------
def generate_pdf(summary_list, filename="AI_Research_Report.pdf"):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, safe_text("AI Research Report"), ln=True, align="C")
    pdf.ln(5)

    for idx, source in enumerate(summary_list, 1):
        url = safe_text(source.get("url", ""))
        bullets = source.get("bullets", [])

        # --- SOURCE line with grey background ---
        pdf.set_font("Arial", "B", 14)
        pdf.set_fill_color(220, 220, 220)  # light grey
        pdf.cell(0, 10, f"SOURCE {idx}:", ln=True, fill=True)
        pdf.ln(2)

        for b in bullets:
            text = safe_text(b).replace("—", "-")

            # Strip leading dash if exists
            if text.startswith("- "):
                text = text[2:]

            # Parse **bold markers**
            parts = re.split(r"(\*\*.*?\*\*)", text)

            pdf.set_font("Arial", "", 12)
            pdf.cell(5)  # indent
            pdf.write(8, "- ")  
            for part in parts:
                if part.startswith("**") and part.endswith("**"):
                    bold_text = part.strip("*")
                    pdf.set_font("Arial", "B", 12)
                    pdf.write(8, bold_text)
                    pdf.set_font("Arial", "", 12)
                else:
                    pdf.write(8, part)

            pdf.ln(8)

        pdf.ln(2)

        # --- URL at bottom ---
        if url:
            pdf.set_font("Arial", "U", 11)
            pdf.set_text_color(0, 0, 255)
            pdf.multi_cell(0, 8, f"URL: {url}")
            pdf.set_text_color(0, 0, 0)

        pdf.ln(5)

    pdf.output(filename)
    return filename

# ------------------ Format Summary for Streamlit ------------------
def format_summary(summary_list):
    html = ""
    for idx, source in enumerate(summary_list, 1):
        url = source.get("url", "")
        bullets = source.get("bullets", [])

        # SOURCE line with grey background
        html += f"<div style='background-color:#e0e0e0; padding:4px;'><b>SOURCE {idx}:</b></div>"

        for b in bullets:
            text = safe_text(b).replace("—", "-")
            # Convert **bold** markers to <b>...</b>
            text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)
            html += f"• {text}<br>"

        # URL at bottom
        if url:
            html += f"<a href='{url}' target='_blank'>URL: {url}</a><br><br>"
    return html
