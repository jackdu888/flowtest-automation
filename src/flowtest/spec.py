"""Load and validate a piping-system YAML spec."""
from __future__ import annotations

import dataclasses
from pathlib import Path

import yaml


@dataclasses.dataclass
class Component:
    id: str
    rated_pressure_bar: float


@dataclasses.dataclass
class SystemSpec:
    name: str
    design_pressure_bar: float
    test_factor: float
    raw: dict

    @property
    def test_pressure_bar(self) -> float:
        return self.design_pressure_bar * self.test_factor

    def components(self) -> list[Component]:
        out: list[Component] = []
        pump = self.raw.get("pump") or {}
        if pump:
            out.append(Component("pump", float(pump["rated_pressure_bar"])))
        for section in ("pipes", "valves"):
            for item in self.raw.get(section, []):
                out.append(Component(item["id"], float(item["rated_pressure_bar"])))
        return out

    def underrated(self) -> list[Component]:
        """Components whose rating is below the hydrotest pressure.

        These are warnings, not hard failures: a relief valve, for example,
        is *supposed* to lift during the 1.5x leg. The report flags them so
        a human confirms each one is intentional.
        """
        return [c for c in self.components()
                if c.rated_pressure_bar < self.test_pressure_bar]


def load_spec(path: str | Path) -> SystemSpec:
    raw = yaml.safe_load(Path(path).read_text())
    for key in ("name", "design_pressure_bar"):
        if key not in raw:
            raise ValueError(f"spec {path}: missing required key {key!r}")
    return SystemSpec(
        name=raw["name"],
        design_pressure_bar=float(raw["design_pressure_bar"]),
        test_factor=float(raw.get("test_factor", 1.5)),
        raw=raw,
    )
