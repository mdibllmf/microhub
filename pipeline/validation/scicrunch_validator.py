"""
SciCrunch RRID validation.

Validates Research Resource Identifiers (RRIDs) against the SciCrunch
registry and retrieves associated metadata (instrument names, antibody
targets, software names).
"""

import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

_SCICRUNCH_API = "https://scicrunch.org/api/1/dataservices/federation/data"


class SciCrunchValidator:
    """Validate RRIDs against the SciCrunch registry."""

    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self._cache: Dict[str, Optional[Dict]] = {}

    def validate(self, rrid: str) -> Optional[Dict]:
        """Validate an RRID and return metadata if valid.

        Parameters
        ----------
        rrid : str
            Full RRID string, e.g. ``"RRID:AB_123456"``.

        Returns
        -------
        dict or None
            Metadata dict on success, None if invalid.
        """
        if rrid in self._cache:
            return self._cache[rrid]

        if not HAS_REQUESTS:
            return None

        result = self._query(rrid)
        self._cache[rrid] = result
        return result

    def _query(self, rrid: str) -> Optional[Dict]:
        try:
            # SciCrunch resolver
            url = f"https://scicrunch.org/resolver/{rrid}.json"
            params = {}
            if self.api_key:
                params["key"] = self.api_key

            resp = requests.get(url, params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data:
                    return {
                        "rrid": rrid,
                        "valid": True,
                        "name": data.get("name", ""),
                        "type": data.get("type", ""),
                    }
        except Exception as exc:
            logger.debug("SciCrunch validation failed for %s: %s", rrid, exc)

        return None
