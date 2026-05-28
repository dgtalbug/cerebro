"""Framework-aware extractors.

Each extractor consumes a framework-native model file and returns a
canonical `CerebroArtifact`. Only this package (and its sub-modules)
imports the underlying ML framework; downstream consumers operate on
the artifact exclusively.
"""

from cerebro.extractors.base import Extractor
from cerebro.extractors.lightgbm import LGBExtractor

__all__ = ["Extractor", "LGBExtractor"]
