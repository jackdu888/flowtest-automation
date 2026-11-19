# flowtest-automation

Automated pressure-testing pipeline for piping system design. A system is
described once as a YAML spec; the pipeline renders an OpenFOAM case from
Jinja templates, sweeps test pressures in Docker, post-processes the results,
and emits a pressure-test pack (pressure distribution, per-component safety
margins, water-hammer risk, pass/fail against the hydrostatic test plan).

Test pressures follow the usual design rule of 1.5x design pressure
(ASME B31.3 style hydrotest), corrected per component rating.

## The loop

```
systems/*.yaml            -- what the system is (pipes, valves, pump, fluid)
        |
        v
flowtest render           -- Jinja -> blockMeshDict / snappyHexMeshDict / controlDict
        |
        v
flowtest sweep            -- Docker (OpenFOAM v12), pressures 1.0x / 1.25x / 1.5x design
        |
        v
convergence ladder        -- if a case diverges: remesh, relax, fall back schemes,
                             cut deltaT, restart from last converged step.
                             Hard retry budget per case; failures are parked
                             with logs, never left burning compute overnight.
        |
        v
results/<date>/<system>/  -- residual CSVs + PDF test pack
        |
        v
data/hydrotest/*.csv      -- physical hydrotest readings dropped in after a
                             real test; pipeline diffs sim vs. measured and
                             recalibrates safety factors before the next run
```

## Layout

- `systems/` — one YAML per piping system (the only file a new system needs)
- `templates/` — OpenFOAM dictionary templates (Jinja2)
- `src/flowtest/` — spec loading, rendering, sweep runner, convergence
  ladder, report generation
- `docker/` — solver image (OpenFOAM v12 + this package)
- `deploy/` — systemd service + timer for the nightly sweep (02:00)
- `data/` — physical hydrotest readings (CSV) for the feedback loop
- `results/` — run output, one folder per night per system

## Quickstart

```bash
pip install .
flowtest inspect systems/chilled-water-loop.yaml   # validate spec + ratings
flowtest sweep   systems/chilled-water-loop.yaml   # render, run, report
```

## Status

In daily use across several client systems (chilled water, process water,
compressed air), different pressure classes. Nightly sweeps run unattended;
the morning deliverable is one test pack per system plus a short list of
parked cases that need a human look.
