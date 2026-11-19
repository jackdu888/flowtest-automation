"""Generate the PDF pressure-test pack for one system."""
from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.platypus import (Paragraph, SimpleDocTemplate, Spacer,
                                Table, TableStyle)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

from .spec import SystemSpec


def build_report(spec: SystemSpec, peaks: dict[str, float],
                 out_path: str | Path) -> Path:
    """peaks: component id -> peak simulated pressure (bar) at the 1.5x leg."""
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(str(out_path), pagesize=A4)
    story = [
        Paragraph(f"Pressure test pack — {spec.name}", styles["Title"]),
        Paragraph(
            f"Design pressure {spec.design_pressure_bar:.1f} bar · "
            f"hydrotest at {spec.test_pressure_bar:.1f} bar "
            f"({spec.test_factor:.2f}x design)", styles["Normal"]),
        Spacer(1, 12),
    ]
    rows = [["Component", "Rated (bar)", "Peak sim (bar)", "Margin", "Verdict"]]
    for comp in spec.components():
        peak = peaks.get(comp.id, 0.0)
        margin = comp.rated_pressure_bar - peak
        verdict = "PASS" if margin >= 0 else "REVIEW"
        rows.append([comp.id, f"{comp.rated_pressure_bar:.0f}",
                     f"{peak:.1f}", f"{margin:+.1f}", verdict])
    table = Table(rows, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    story += [table, Spacer(1, 12),
              Paragraph("REVIEW rows are components modelled as lifting or "
                        "isolated during the hydrotest leg (e.g. relief "
                        "valves) — confirm each against the test plan "
                        "before sign-off.", styles["Normal"])]
    doc.build(story)
    return Path(out_path)
