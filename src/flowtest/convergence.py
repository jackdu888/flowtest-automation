"""The 3 a.m. ladder: what happens when a case will not converge.

Strategies are tried in order, cheapest first. Every case has a hard
attempt budget and a wall-clock cap; a case that exhausts the ladder is
parked with its logs and flagged in the morning report instead of
burning compute until sunrise.
"""
from __future__ import annotations

import dataclasses
import re
from pathlib import Path

MAX_ATTEMPTS = 5
WALL_CLOCK_CAP_S = 90 * 60

# checkMesh gates: beyond these, fix the mesh before touching the solver.
MAX_NON_ORTHO = 70.0
MAX_SKEWNESS = 4.0

_RESIDUAL = re.compile(r"Solving for (\w+), Initial residual = ([\d.eE+-]+)")


@dataclasses.dataclass
class Attempt:
    strategy: str
    detail: str


def parse_residuals(log_text: str) -> dict[str, float]:
    """Last-seen initial residual per field from a solver log."""
    out: dict[str, float] = {}
    for field, value in _RESIDUAL.findall(log_text):
        out[field] = float(value)
    return out


def diverged(log_text: str, tol: float = 1e-4) -> bool:
    res = parse_residuals(log_text)
    if not res:
        return True
    return any(v > tol or v != v for v in res.values())  # NaN counts too


def next_strategy(mesh: dict, attempt_no: int,
                  history: list[Attempt]) -> Attempt | None:
    """Pick the next remediation step, or None when the budget is spent."""
    if attempt_no >= MAX_ATTEMPTS:
        return None
    tried = {a.strategy for a in history}
    if (mesh.get("max_non_ortho", 0) > MAX_NON_ORTHO
            or mesh.get("max_skewness", 0) > MAX_SKEWNESS) \
            and "remesh" not in tried:
        return Attempt("remesh",
                       "tighten snappyHexMesh refinement, re-run checkMesh")
    if "relax" not in tried:
        return Attempt("relax", "under-relaxation 0.7 -> 0.5 -> 0.3")
    if "schemes" not in tried:
        return Attempt("schemes",
                       "fall back: Gauss linearUpwind -> bounded upwind")
    if "deltat" not in tried:
        return Attempt("deltat", "halve deltaT to hold maxCo < 1, "
                                 "restart from last converged time")
    return Attempt("restart-clean", "fresh start from uniform fields")


def park_case(case_dir: str | Path, reason: str) -> Path:
    """Preserve a failed case for the morning report."""
    note = Path(case_dir) / "PARKED.md"
    note.write_text(f"# Parked case\n\nReason: {reason}\n"
                    f"Logs preserved in this directory. "
                    f"Needs a human look before the next sweep.\n")
    return note
