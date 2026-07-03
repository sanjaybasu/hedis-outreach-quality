"""Load extracted HEDIS tables from a local data directory.

The extraction (sql/ run by scripts/00_extract.py) writes parquet files here.
No patient data is bundled with the repository.
"""
from __future__ import annotations
import os
import pandas as pd

DATA_DIR = os.environ.get("HEDIS_DATA_DIR", "data")

TABLES = {
    "gap": "hedis_gap.parquet",        # member x measure-year gap, open/closed status
    "funnel": "funnel.parquet",        # deepest engagement stage per gap
    "over_time": "over_time.parquet",  # daily numerator/denominator by payer x measure x year
    "spans": "spans.parquet",          # attribution-validity spans per member
}


def load(name: str, data_dir: str | None = None) -> pd.DataFrame:
    path = os.path.join(data_dir or DATA_DIR, TABLES[name])
    return pd.read_parquet(path)


def as_bool(s: pd.Series) -> pd.Series:
    # source columns arrive as text; normalize to boolean
    return s.astype(str).str.strip().str.lower().isin(["true", "t", "1", "yes"])
