"""Exportación de pacientes a PDF con ReportLab."""
from __future__ import annotations
from typing import Iterable, Sequence

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
    from reportlab.lib.styles import getSampleStyleSheet
except Exception:  # pragma: no cover
    A4 = None

HEADERS = ["Nombre","Apellidos","Sexo","Edad","Peso (kg)","Altura (cm)","Teléfono","Correo","IMC","TMB","%Grasa","Peso Ideal"]

def export_patients_pdf(rows: Iterable[Sequence], path: str) -> None:
    if not A4:
        raise RuntimeError("ReportLab no está instalado. Ejecuta: pip install reportlab")
    data = [HEADERS]
    for r in rows:
        data.append(list(r[1:]))  # omite ID

    doc = SimpleDocTemplate(path, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = [Paragraph("NutriLink - Lista de Pacientes", styles["Title"])]
    t = Table(data, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#E8EEF9")),
        ("GRID",(0,0),(-1,-1),0.25,colors.grey),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
        ("ALIGN",(0,0),(-1,-1),"CENTER"),
    ]))
    elements.append(t)
    doc.build(elements)