"""Builds exportable review reports as Markdown, HTML, or PDF (ReportLab)."""
import io
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


def build_markdown(review, findings) -> str:
    lines = [
        f"# Code Review Report — {review.project.project_name}",
        "",
        f"**Score:** {review.review_score}/100  ",
        f"**Generated:** {review.created_at.isoformat()}",
        "",
        "## Summary",
        review.summary or "_No summary available._",
        "",
        "## Complexity Metrics",
    ]
    for key, value in review.metrics.items():
        if key in ("complexity_blocks", "files"):
            continue
        lines.append(f"- **{key.replace('_', ' ').title()}:** {value}")

    lines += ["", "## Findings", ""]
    if not findings:
        lines.append("_No findings reported._")
    for f in findings:
        lines.append(f"### [{f.severity.upper()}] {f.issue}")
        lines.append(f"- **Category:** {f.category}")
        lines.append(f"- **File:** {f.file_name or 'n/a'}  **Line:** {f.line_number or 'n/a'}")
        lines.append(f"- **Explanation:** {f.explanation}")
        lines.append(f"- **Suggestion:** {f.suggestion}")
        lines.append("")
    return "\n".join(lines)


def build_html(review, findings) -> str:
    rows = "".join(
        f"<tr><td>{f.severity}</td><td>{f.category}</td><td>{f.issue}</td>"
        f"<td>{f.file_name or ''}:{f.line_number or ''}</td>"
        f"<td>{f.explanation}</td><td>{f.suggestion}</td></tr>"
        for f in findings
    )
    metrics_rows = "".join(
        f"<tr><td>{k.replace('_', ' ').title()}</td><td>{v}</td></tr>"
        for k, v in review.metrics.items() if k not in ("complexity_blocks", "files")
    )
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>Code Review Report — {review.project.project_name}</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 40px; color: #1f2937; }}
h1 {{ color: #111827; }}
table {{ border-collapse: collapse; width: 100%; margin-top: 16px; }}
th, td {{ border: 1px solid #d1d5db; padding: 8px; text-align: left; font-size: 14px; }}
th {{ background: #f3f4f6; }}
.score {{ font-size: 28px; font-weight: bold; color: #2563eb; }}
</style></head>
<body>
<h1>Code Review Report — {review.project.project_name}</h1>
<p class="score">Score: {review.review_score}/100</p>
<p><strong>Generated:</strong> {review.created_at.isoformat()}</p>
<h2>Summary</h2>
<p>{review.summary or 'No summary available.'}</p>
<h2>Complexity Metrics</h2>
<table><tr><th>Metric</th><th>Value</th></tr>{metrics_rows}</table>
<h2>Findings</h2>
<table>
<tr><th>Severity</th><th>Category</th><th>Issue</th><th>Location</th><th>Explanation</th><th>Suggestion</th></tr>
{rows}
</table>
</body></html>"""


def build_pdf(review, findings) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                             topMargin=0.6 * inch, bottomMargin=0.6 * inch)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleX", parent=styles["Title"], fontSize=18)
    story = [
        Paragraph(f"Code Review Report — {review.project.project_name}", title_style),
        Spacer(1, 8),
        Paragraph(f"<b>Score:</b> {review.review_score}/100", styles["Normal"]),
        Paragraph(f"<b>Generated:</b> {review.created_at.isoformat()}", styles["Normal"]),
        Spacer(1, 12),
        Paragraph("Summary", styles["Heading2"]),
        Paragraph(review.summary or "No summary available.", styles["Normal"]),
        Spacer(1, 12),
        Paragraph("Complexity Metrics", styles["Heading2"]),
    ]

    metrics_data = [["Metric", "Value"]] + [
        [k.replace("_", " ").title(), str(v)]
        for k, v in review.metrics.items() if k not in ("complexity_blocks", "files")
    ]
    story.append(_table(metrics_data))
    story.append(Spacer(1, 12))
    story.append(Paragraph("Findings", styles["Heading2"]))

    if not findings:
        story.append(Paragraph("No findings reported.", styles["Normal"]))
    else:
        findings_data = [["Severity", "Category", "Issue", "Location", "Suggestion"]]
        for f in findings:
            findings_data.append([
                f.severity, f.category, f.issue,
                f"{f.file_name or ''}:{f.line_number or ''}",
                f.suggestion[:120],
            ])
        story.append(_table(findings_data, col_widths=[60, 70, 110, 70, 160]))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()


def _table(data, col_widths=None):
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f3f4f6")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ]))
    return t
