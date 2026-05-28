"""Training data ingestion and profiling via DuckDB."""

from cerebro.data.loader import load_table
from cerebro.data.profiler import profile_table

__all__ = ["load_table", "profile_table"]
