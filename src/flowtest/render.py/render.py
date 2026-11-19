"""Render OpenFOAM dictionaries from a spec via the Jinja templates."""
from __future__ import annotations

from pathlib import Path

import jinja2

TEMPLATE_DIR = Path(__file__).resolve().parents[2] / "templates"


def render_case(spec, out_dir: str | Path) -> Path:
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(TEMPLATE_DIR),
        keep_trailing_newline=True,
    )
    main = max(spec.raw["pipes"], key=lambda p: p["length_m"])
    ctx = {
        "spec": spec.raw,
        "main_length": main["length_m"],
        "diameter": main["dn"] / 1000.0,
        "cells_x": max(20, int(main["length_m"] * 4)),
        "refine_level": 2,
        "end_time": 2000,
        "delta_t": 1.0,
        "max_co": 1.0,
    }
    out = Path(out_dir)
    (out / "system").mkdir(parents=True, exist_ok=True)
    for name in ("blockMeshDict", "snappyHexMeshDict", "controlDict"):
        text = env.get_template(f"{name}.j2").render(**ctx)
        (out / "system" / name).write_text(text)
    return out
