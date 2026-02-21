"""
FPbase API validation for fluorescent proteins.

Validates fluorophore names against the FPbase database and retrieves
spectral properties (excitation/emission maxima, quantum yield).
Results are cached to avoid repeated API calls.

Supports local-first validation via fpbase_name_lookup.json (downloaded
by download_lookup_tables.sh).  Falls back to live API if local lookup
misses or is not loaded.
"""

import json
import logging
import os
from typing import Dict, Optional

logger = logging.getLogger(__name__)

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

_FPBASE_API = "https://www.fpbase.org/api/proteins/"


class FPbaseValidator:
    """Validate fluorescent protein names against FPbase."""

    def __init__(self, lookup_path: str = None):
        self._cache: Dict[str, Optional[Dict]] = {}
        self._name_set: Optional[set] = None
        self._local_lookup: Dict[str, Dict] = {}
        self._local_loaded = False

        if lookup_path:
            self._load_local(lookup_path)

    def _load_local(self, path: str):
        """Load fpbase_name_lookup.json for instant local validation."""
        json_path = path
        if os.path.isdir(path):
            json_path = os.path.join(path, "fpbase_name_lookup.json")

        if not os.path.exists(json_path):
            logger.warning("FPbase lookup not found at %s", json_path)
            return

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                self._local_lookup = json.load(f)
            self._local_loaded = True
            logger.info("FPbase local lookup loaded: %d entries",
                        len(self._local_lookup))
        except Exception as exc:
            logger.warning("Failed to load FPbase lookup: %s", exc)

    def load_gazetteer(self) -> set:
        """Return set of all known FP names.  Uses local file first."""
        if self._name_set is not None:
            return self._name_set

        # LOCAL FIRST: build from downloaded lookup
        if self._local_loaded:
            names = set()
            for key, entry in self._local_lookup.items():
                names.add(key)
                if isinstance(entry, dict) and entry.get("name"):
                    names.add(entry["name"])
                    names.add(entry["name"].lower())
            names.discard("")
            self._name_set = names
            logger.info("FPbase gazetteer from local: %d names", len(names))
            return self._name_set

        # FALLBACK: original API-based loading
        if not HAS_REQUESTS:
            self._name_set = set()
            return self._name_set

        names = set()
        url = _FPBASE_API
        params = {"format": "json", "limit": 1000}
        try:
            while url:
                resp = requests.get(url, params=params, timeout=15)
                if resp.status_code != 200:
                    break
                data = resp.json()
                for protein in data.get("results", []):
                    names.add(protein.get("name", ""))
                    for alias in protein.get("aliases", []):
                        names.add(alias)
                url = data.get("next")
                params = {}  # next URL already has params
        except Exception as exc:
            logger.warning("FPbase gazetteer fetch failed: %s", exc)

        names.discard("")
        self._name_set = names
        logger.info("FPbase gazetteer loaded: %d names", len(names))
        return names

    def validate(self, name: str) -> Optional[Dict]:
        """Check if *name* is a known fluorescent protein on FPbase.

        Returns protein info dict on match, None otherwise.
        Local lookup is checked first, then falls back to the API.
        """
        if name in self._cache:
            return self._cache[name]

        # LOCAL FIRST
        if self._local_loaded:
            entry = self._local_lookup.get(name.lower())
            if entry and isinstance(entry, dict):
                info = {
                    "name": entry.get("name", name),
                    "ex_max": entry.get("ex_max"),
                    "em_max": entry.get("em_max"),
                    "qy": entry.get("qy"),
                    "ext_coeff": entry.get("ext_coeff"),
                }
                self._cache[name] = info
                return info

        # FALLBACK: original API call
        if not HAS_REQUESTS:
            return None

        try:
            resp = requests.get(
                _FPBASE_API,
                params={"name__iexact": name, "format": "json"},
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get("count", 0) > 0:
                    result = data["results"][0]
                    info = {
                        "name": result.get("name"),
                        "ex_max": result.get("default_state", {}).get("ex_max"),
                        "em_max": result.get("default_state", {}).get("em_max"),
                        "qy": result.get("default_state", {}).get("qy"),
                        "ext_coeff": result.get("default_state", {}).get("ext_coeff"),
                    }
                    self._cache[name] = info
                    return info
        except Exception as exc:
            logger.debug("FPbase validation error for '%s': %s", name, exc)

        self._cache[name] = None
        return None
