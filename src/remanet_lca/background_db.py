"""Background LCA database interface.

Ships synthetic stand-ins for EXIOBASE 3 and BAFU:2026 so the pipeline runs
without a licensed database. Swap these loaders for real database access in
your own deployment.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "background_db"


@dataclass
class SectorMatch:
    sector_code: str
    sector_name: str
    unit: str
    gwp_kg_co2e_per_unit: float
    source: str


class BackgroundDatabase:
    """Loads and queries the (synthetic) background sector tables."""

    def __init__(self, data_dir: Path = DATA_DIR):
        self._tables = {
            "exiobase3": pd.read_csv(data_dir / "exiobase3_synthetic.csv"),
            "bafu2026": pd.read_csv(data_dir / "bafu2026_synthetic.csv"),
        }

    def get(self, sector_code: str) -> SectorMatch:
        for source, table in self._tables.items():
            row = table.loc[table["sector_code"] == sector_code]
            if not row.empty:
                r = row.iloc[0]
                return SectorMatch(
                    sector_code=r["sector_code"],
                    sector_name=r["sector_name"],
                    unit=r["unit"],
                    gwp_kg_co2e_per_unit=float(r["gwp_kg_co2e_per_unit"]),
                    source=source,
                )
        raise KeyError(f"Unknown sector code: {sector_code}")

    def all_sectors(self) -> list[SectorMatch]:
        out = []
        for source, table in self._tables.items():
            for _, r in table.iterrows():
                out.append(
                    SectorMatch(
                        sector_code=r["sector_code"],
                        sector_name=r["sector_name"],
                        unit=r["unit"],
                        gwp_kg_co2e_per_unit=float(r["gwp_kg_co2e_per_unit"]),
                        source=source,
                    )
                )
        return out
