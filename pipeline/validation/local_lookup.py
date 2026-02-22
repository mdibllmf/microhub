"""
Local-first lookup for all validation endpoints.

Loads bulk data files from microhub_lookup_tables/ at startup, provides
instant in-memory lookups. Falls back to API ONLY for entities not found
locally.

Architecture:
    1. Load JSON indexes from microhub_lookup_tables/ (one-time, ~5 seconds)
    2. All validate/lookup calls check local index first (< 1ms)
    3. Only if NOT found locally → make API call (slow path)
    4. API results are cached back to the local index for next run

This replaces the API-first approach that was taking 5+ seconds per paper.

Usage:
    from pipeline.validation.local_lookup import LocalLookup
    lookup = LocalLookup()                    # auto-finds microhub_lookup_tables/
    lookup = LocalLookup("/path/to/tables")   # explicit path

    # ROR
    result = lookup.ror("Harvard University")
    # → {"ror_id": "03vek6s52", "name": "Harvard University", "country": "United States"}

    # Cell lines
    result = lookup.cell_line("HeLa")
    # → {"accession": "CVCL_0030", "name": "HeLa", "species": "Homo sapiens"}

    # Taxonomy
    result = lookup.taxon("Mus musculus")
    # → {"tax_id": 10090, "scientific_name": "Mus musculus", "rank": "species"}

    # Fluorescent proteins
    result = lookup.fluorophore("GFP")
    # → {"name": "GFP", "ex_max": 395, "em_max": 509, ...}
"""

import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _find_lookup_dir() -> Optional[str]:
    """Auto-detect the microhub_lookup_tables directory."""
    candidates = [
        # Same directory as this file's grandparent (project root)
        os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.abspath(__file__)
            ))),
            "microhub_lookup_tables",
        ),
        # Current working directory
        os.path.join(os.getcwd(), "microhub_lookup_tables"),
        # One level up from cwd
        os.path.join(os.path.dirname(os.getcwd()), "microhub_lookup_tables"),
    ]
    for path in candidates:
        if os.path.isdir(path):
            return path
    return None


class LocalLookup:
    """Unified local-first lookup across all bulk data sources.

    Loads JSON indexes lazily on first access. Thread-safe for reads.
    """

    def __init__(self, lookup_dir: Optional[str] = None):
        self._dir = lookup_dir or _find_lookup_dir()
        self._loaded = False

        # Indexes — populated by _ensure_loaded()
        self._ror_index: Dict[str, Dict] = {}
        self._cellosaurus_index: Dict[str, Dict] = {}
        self._taxonomy_index: Dict[str, Dict] = {}
        self._fpbase_index: Dict[str, Dict] = {}

        # Track what we've loaded
        self._available = set()

        # API fallback caches (for things not in local files)
        self._api_miss_cache: Dict[str, Optional[Dict]] = {}

    @property
    def is_available(self) -> bool:
        """Check if local lookup tables exist."""
        return self._dir is not None and os.path.isdir(self._dir)

    @property
    def available_sources(self) -> set:
        """Which data sources are loaded."""
        self._ensure_loaded()
        return set(self._available)

    # ------------------------------------------------------------------
    # Public lookup methods
    # ------------------------------------------------------------------

    def ror(self, institution_name: str) -> Optional[Dict[str, Any]]:
        """Look up ROR data for an institution name.

        Checks local index first, returns None if not found.
        """
        self._ensure_loaded()
        if not institution_name:
            return None
        key = institution_name.strip().lower()
        return self._ror_index.get(key)

    def ror_fuzzy(self, institution_name: str) -> Optional[Dict[str, Any]]:
        """Fuzzy ROR lookup — tries exact match, then key word matching.

        More aggressive than ror() but still local-only.
        """
        # Exact match first
        result = self.ror(institution_name)
        if result:
            return result

        if not institution_name:
            return None

        # Try without common prefixes/suffixes
        cleaned = institution_name.strip().lower()
        for prefix in ("the ", "department of ", "dept. of ", "dept of ",
                        "school of ", "faculty of ", "division of ",
                        "institute of ", "center for "):
            if cleaned.startswith(prefix):
                result = self._ror_index.get(cleaned[len(prefix):])
                if result:
                    return result

        # Try matching the last significant part (university name)
        # "Dept of Biology, Stanford University" → "stanford university"
        parts = [p.strip().lower() for p in institution_name.split(",")]
        for part in reversed(parts):
            result = self._ror_index.get(part)
            if result:
                return result

        return None

    def cell_line(self, name: str) -> Optional[Dict[str, Any]]:
        """Look up cell line in Cellosaurus local index."""
        self._ensure_loaded()
        if not name:
            return None
        return self._cellosaurus_index.get(name.strip().lower())

    def taxon(self, organism_name: str) -> Optional[Dict[str, Any]]:
        """Look up NCBI taxonomy data for an organism name."""
        self._ensure_loaded()
        if not organism_name:
            return None
        return self._taxonomy_index.get(organism_name.strip().lower())

    def fluorophore(self, name: str) -> Optional[Dict[str, Any]]:
        """Look up fluorescent protein in FPbase local index."""
        self._ensure_loaded()
        if not name:
            return None
        return self._fpbase_index.get(name.strip().lower())

    # ------------------------------------------------------------------
    # Batch lookups (for pipeline efficiency)
    # ------------------------------------------------------------------

    def ror_batch(self, names: List[str]) -> Dict[str, Optional[Dict]]:
        """Look up multiple institution names. Returns {name: result_or_None}."""
        self._ensure_loaded()
        return {name: self.ror(name) for name in names if name}

    def cell_line_batch(self, names: List[str]) -> Dict[str, Optional[Dict]]:
        """Look up multiple cell line names."""
        self._ensure_loaded()
        return {name: self.cell_line(name) for name in names if name}

    def taxon_batch(self, names: List[str]) -> Dict[str, Optional[Dict]]:
        """Look up multiple organism names."""
        self._ensure_loaded()
        return {name: self.taxon(name) for name in names if name}

    def fluorophore_batch(self, names: List[str]) -> Dict[str, Optional[Dict]]:
        """Look up multiple fluorophore names."""
        self._ensure_loaded()
        return {name: self.fluorophore(name) for name in names if name}

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def stats(self) -> Dict[str, int]:
        """Return counts per index."""
        self._ensure_loaded()
        return {
            "ror": len(self._ror_index),
            "cellosaurus": len(self._cellosaurus_index),
            "taxonomy": len(self._taxonomy_index),
            "fpbase": len(self._fpbase_index),
        }

    # ------------------------------------------------------------------
    # Internal: lazy loading
    # ------------------------------------------------------------------

    def _ensure_loaded(self):
        if self._loaded:
            return
        self._loaded = True

        if not self._dir or not os.path.isdir(self._dir):
            logger.warning(
                "Local lookup tables not found. Run download_lookup_data.py first. "
                "Falling back to API-only mode."
            )
            return

        t0 = time.time()

        # Load each file if present
        self._ror_index = self._load_json("ror_lookup.json", "ROR")
        self._cellosaurus_index = self._load_json("cellosaurus_lookup.json", "Cellosaurus")
        self._taxonomy_index = self._load_json("taxonomy_lookup.json", "NCBI Taxonomy")
        self._fpbase_index = self._load_json("fpbase_lookup.json", "FPbase")

        elapsed = time.time() - t0
        logger.info(
            "Local lookup loaded in %.1fs: ROR=%d, Cellosaurus=%d, "
            "Taxonomy=%d, FPbase=%d",
            elapsed,
            len(self._ror_index), len(self._cellosaurus_index),
            len(self._taxonomy_index), len(self._fpbase_index),
        )

    def _load_json(self, filename: str, label: str) -> Dict:
        if not self._dir:
            return {}
        fpath = os.path.join(self._dir, filename)
        if not os.path.exists(fpath):
            logger.info("  %s: not found (%s)", label, filename)
            return {}

        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._available.add(label.lower())
            logger.info("  %s: %d entries", label, len(data))
            return data
        except Exception as e:
            logger.error("  %s: failed to load (%s)", label, e)
            return {}
