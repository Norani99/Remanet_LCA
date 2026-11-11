"""GWP calculation from a resolved sector match plus a reported quantity."""
from __future__ import annotations

from dataclasses import dataclass

from .background_db import SectorMatch


@dataclass
class GWPResult:
    sector_code: str
    quantity: float
    unit: str
    gwp_kg_co2e: float
    source: str


def compute_gwp(sector: SectorMatch, quantity: float) -> GWPResult:
    return GWPResult(
        sector_code=sector.sector_code,
        quantity=quantity,
        unit=sector.unit,
        gwp_kg_co2e=round(sector.gwp_kg_co2e_per_unit * quantity, 4),
        source=sector.source,
    )
