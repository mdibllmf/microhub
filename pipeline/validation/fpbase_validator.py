"""
FPbase API validation for fluorescent proteins.

Validates fluorophore names against the FPbase database and retrieves
spectral properties (excitation/emission maxima, quantum yield).
Results are cached to avoid repeated API calls.
"""

import logging
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

    def __init__(self):
        self._cache: Dict[str, Optional[Dict]] = {}
        self._name_set: Optional[set] = None

    def load_gazetteer(self) -> set:
        """Fetch all known FP names from FPbase (for dictionary matching)."""
        if self._name_set is not None:
            return self._name_set

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
        """
        if name in self._cache:
            return self._cache[name]

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
