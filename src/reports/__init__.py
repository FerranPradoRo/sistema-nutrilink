"""Exportación de pacientes a PDF (horizontal)."""
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

def export_patients_pdf(rows, output_path: str):
    doc = SimpleDocTemplate(output_path, pagesize=landscape(A4))
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("NutriLink - Lista de pacientes", styles["Title"]))
    story.append(Spacer(1, 12))

    data = [[
        "#", "Nombre", "Apellidos", "Sexo", "Edad", "Peso",
        "Altura", "Teléfono", "Correo", "IMC", "TMB",
        "% Grasa", "Peso Ideal"
    ]]

    for idx, row in enumerate(rows, start=1):
        data.append([
            idx, row[1], row[2], row[3], row[4], row[5], row[6],
            row[7] or "", row[8] or "", row[9], row[10], row[11], row[12]
        ])

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#20b2a6")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.HexColor("#eef9f8")]),
    ]))

    story.append(table)
    doc.build(story)