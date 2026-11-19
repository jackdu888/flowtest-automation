"""flowtest command line: inspect a spec, or run a full sweep."""
from __future__ import annotations

import argparse
from pathlib import Path

from . import report, runner
from .spec import load_spec


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="flowtest")
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("inspect", "sweep"):
        p = sub.add_parser(name)
        p.add_argument("spec")
    p = sub.add_parser("report")
    p.add_argument("spec")
    p.add_argument("--out", default="test-pack.pdf")
    args = parser.parse_args(argv)

    spec = load_spec(args.spec)
    if args.cmd == "inspect":
        print(f"{spec.name}: design {spec.design_pressure_bar} bar, "
              f"test {spec.test_pressure_bar} bar")
        for c in spec.underrated():
            print(f"  note: {c.id} rated {c.rated_pressure_bar} bar "
                  f"< test pressure — confirm it lifts/isolates in the plan")
        return 0
    if args.cmd == "sweep":
        done = runner.sweep(spec, Path("results"))
        print(f"{spec.name}: {len(done)} pressure legs completed")
        return 0
    if args.cmd == "report":
        out = report.build_report(spec, {}, args.out)
        print(f"wrote {out}")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
