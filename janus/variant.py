from dataclasses import dataclass


@dataclass
class Variant:
    name: str
    impressions: int
    conversions: int
    revenue: int
