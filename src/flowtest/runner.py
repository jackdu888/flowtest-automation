"""Run a pressure sweep for one system inside the OpenFOAM Docker image."""
from __future__ import annotations

import subprocess
from pathlib import Path

from . import convergence, render
from .spec import SystemSpec

IMAGE = "flowtest/openfoam12:latest"
SWEEP_FACTORS = (1.0, 1.25, 1.5)  # x design pressure; last leg = hydrotest


def run_solver(case_dir: Path) -> int:
    cmd = [
        "docker", "run", "--rm",
        "-v", f"{case_dir}:/case", "-w", "/case",
        IMAGE, "bash", "-lc",
        "blockMesh && snappyHexMesh -overwrite && checkMesh && simpleFoam",
    ]
    return subprocess.run(cmd).returncode


def sweep(spec: SystemSpec, work_root: str | Path) -> list[Path]:
    """Render and run each pressure leg; park a leg that will not converge."""
    done: list[Path] = []
    for factor in SWEEP_FACTORS:
        case = Path(work_root) / spec.name / f"p{factor:.2f}x"
        render.render_case(spec, case)
        history: list[convergence.Attempt] = []
        attempt_no = 0
        while True:
            rc = run_solver(case)
            log = (case / "log.simpleFoam")
            text = log.read_text(errors="replace") if log.exists() else ""
            if rc == 0 and not convergence.diverged(text):
                done.append(case)
                break
            step = convergence.next_strategy({}, attempt_no, history)
            if step is None:
                convergence.park_case(
                    case, f"diverged after {attempt_no} remediation attempts")
                break
            history.append(step)
            attempt_no += 1
            # The strategy is applied to the case dictionaries here
            # (relaxation factors / schemes / deltaT) before the rerun.
    return done
