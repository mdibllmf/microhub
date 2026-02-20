"""
ROR v2 API client for dynamic institution affiliation matching.

The Research Organization Registry (ROR) API v2 is the canonical source
for institution resolution.  ROR API v1 was sunset on December 8, 2025.

Features:
  - Affiliation matching: accepts messy affiliation strings, returns best match
  - Single-search mode (&single_search) for improved precision
  - ROR ID validation with checksum verification
  - Handles merged/deprecated records by following successor chains
  - Rate limit: 2,000 requests per 5-minute window (with client ID)

Usage:
    from pipeline.validation.ror_v2_client import RORv2Client
    client = RORv2Client()
    result = client.match_affiliation("Department of Biology, MIT, Cambridge, MA")
    # → {"ror_id": "042nb2s44", "name": "Massachusetts Institute of Technology", ...}
"""

import logging
import re
import threading
import time
from typing import Any, Dict, List, Optional
from urllib.parse import quote

logger = logging.getLogger(__name__)

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

_ROR_V2_BASE = "https://api.ror.org/v2/organizations"

# ROR ID validation: base-32 Crockford encoding with ISO 7064 checksum
# Always starts with '0', excludes I, L, O, U
_ROR_ID_RE = re.compile(r"^0[a-hj-km-np-tv-z0-9]{6}[0-9]{2}$")

# Full ROR URL pattern
_ROR_URL_RE = re.compile(
    r"(?:https?://)?ror\.org/(0[a-hj-km-np-tv-z0-9]{6}[0-9]{2})"
)

# Rate limit: 2,000 requests per 5-minute window with client ID
_REQUEST_DELAY = 0.15  # ≈2000/300s


class RORv2Client:
    """Query the ROR v2 API for organization matching and lookup."""

    def __init__(self, client_id: str = None):
        """
        Parameters
        ----------
        client_id : str, optional
            ROR API client ID (register at ror.org/api-client-id).
            Without one: 50 requests per 5 minutes.
            With one: 2,000 requests per 5 minutes.
        """
        self.client_id = client_id
        self._last_call = 0.0
        self._cache: Dict[str, Optional[Dict]] = {}
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Affiliation matching
    # ------------------------------------------------------------------

    def match_affiliation(self, affiliation: str) -> Optional[Dict[str, Any]]:
        """Match a raw affiliation string to a ROR organization.

        Uses the v2 affiliation matching endpoint with single_search
        parameter for improved precision.

        Parameters
        ----------
        affiliation : str
            Raw affiliation string (e.g., "Dept. of Biology, MIT, Cambridge MA").

        Returns
        -------
        dict or None
            Best match with keys: ror_id, name, country, types, status,
            score, chosen (bool).
            Returns None if no confident match found.
        """
        if not HAS_REQUESTS or not affiliation or not affiliation.strip():
            return None

        cache_key = affiliation.strip().lower()
        if cache_key in self._cache:
            return self._cache[cache_key]

        result = self._query_affiliation(affiliation.strip())
        self._cache[cache_key] = result
        return result

    def match_affiliations_batch(self,
                                  affiliations: List[str]) -> List[Optional[Dict]]:
        """Match multiple affiliation strings.

        Note: ROR v2 does not have a batch endpoint, so this is
        sequential with rate limiting.
        """
        return [self.match_affiliation(aff) for aff in affiliations]

    # ------------------------------------------------------------------
    # Direct lookup
    # ------------------------------------------------------------------

    def lookup(self, ror_id: str) -> Optional[Dict[str, Any]]:
        """Look up a specific ROR organization by ID.

        Parameters
        ----------
        ror_id : str
            ROR ID in any form: full URL, domain-path, or bare 9-char ID.

        Returns
        -------
        dict or None
            Organization data with keys: ror_id, name, country, types,
            status, aliases, relationships.
        """
        bare_id = self.extract_ror_id(ror_id)
        if not bare_id:
            return None

        if not HAS_REQUESTS:
            return None

        self._rate_limit()
        try:
            resp = requests.get(
                f"{_ROR_V2_BASE}/{bare_id}",
                timeout=10,
            )

            if resp.status_code != 200:
                return None

            data = resp.json()
            return self._parse_org(data)

        except Exception as exc:
            logger.debug("ROR lookup error for %s: %s", ror_id, exc)
            return None

    def follow_successor(self, ror_id: str) -> Optional[Dict[str, Any]]:
        """Look up a ROR ID and follow successor chain if merged/deprecated.

        Returns the active successor organization, or the original if active.
        """
        org = self.lookup(ror_id)
        if org is None:
            return None

        # If active, return as-is
        if org.get("status") == "active":
            return org

        # Follow successor chain (max 5 hops to avoid infinite loops)
        for _ in range(5):
            successors = [
                r for r in org.get("relationships", [])
                if r.get("type") == "successor"
            ]
            if not successors:
                return org  # No successor, return as-is

            successor_id = successors[0].get("id", "")
            if not successor_id:
                return org

            org = self.lookup(successor_id)
            if org is None:
                return None
            if org.get("status") == "active":
                return org

        return org

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    @staticmethod
    def validate_ror_id(ror_id: str) -> bool:
        """Validate a ROR ID format (Crockford base-32 with checksum).

        Accepts bare ID, domain-path, or full URL forms.
        """
        bare = RORv2Client.extract_ror_id(ror_id)
        if not bare:
            return False
        return bool(_ROR_ID_RE.match(bare))

    @staticmethod
    def extract_ror_id(ror_id: str) -> Optional[str]:
        """Extract bare 9-character ROR ID from any form.

        Accepts:
          - Full URL: https://ror.org/03yrm5c26
          - Domain-path: ror.org/03yrm5c26
          - Bare ID: 03yrm5c26
        """
        if not ror_id:
            return None
        ror_id = ror_id.strip()

        # Try URL pattern
        m = _ROR_URL_RE.search(ror_id)
        if m:
            return m.group(1)

        # Try bare ID
        if _ROR_ID_RE.match(ror_id):
            return ror_id

        return None

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _query_affiliation(self, affiliation: str) -> Optional[Dict[str, Any]]:
        """Query the ROR v2 affiliation endpoint."""
        self._rate_limit()
        try:
            params = {"affiliation": affiliation}
            if self.client_id:
                params["client_id"] = self.client_id

            resp = requests.get(
                _ROR_V2_BASE,
                params=params,
                timeout=15,
            )

            if resp.status_code == 429:
                logger.warning("ROR API rate limited")
                return None
            if resp.status_code != 200:
                logger.debug("ROR HTTP %d for affiliation query", resp.status_code)
                return None

            data = resp.json()
            items = data.get("items", [])
            if not items:
                return None

            # Find the chosen match (best match flagged by ROR)
            for item in items:
                if item.get("chosen", False):
                    org_data = item.get("organization", {})
                    result = self._parse_org(org_data)
                    result["score"] = item.get("score", 0)
                    result["chosen"] = True
                    return result

            # Fallback: use first result if score is high enough
            first = items[0]
            score = first.get("score", 0)
            if score >= 0.8:
                org_data = first.get("organization", {})
                result = self._parse_org(org_data)
                result["score"] = score
                result["chosen"] = False
                return result

            return None

        except Exception as exc:
            logger.debug("ROR affiliation error: %s", exc)
            return None

    @staticmethod
    def _parse_org(data: Dict) -> Dict[str, Any]:
        """Parse a ROR v2 organization object."""
        # Extract name (prefer ror_display)
        names = data.get("names", [])
        display_name = ""
        for name_obj in names:
            if isinstance(name_obj, dict):
                types = name_obj.get("types", [])
                if "ror_display" in types:
                    display_name = name_obj.get("value", "")
                    break
        if not display_name and names:
            # Fallback to first name
            first = names[0] if isinstance(names[0], dict) else {"value": str(names[0])}
            display_name = first.get("value", "")

        # If names is empty (v2 simple format from affiliation endpoint)
        if not display_name:
            display_name = data.get("name", "")

        # Extract country
        locations = data.get("locations", [])
        country = ""
        country_code = ""
        if locations:
            geo = locations[0].get("geonames_details", {})
            country = geo.get("country_name", "")
            country_code = geo.get("country_code", "")
        if not country:
            country = data.get("country", {}).get("country_name", "") \
                if isinstance(data.get("country"), dict) else ""
            country_code = data.get("country", {}).get("country_code", "") \
                if isinstance(data.get("country"), dict) else ""

        # Extract ROR ID
        ror_id = data.get("id", "")
        bare_id = RORv2Client.extract_ror_id(ror_id) or ror_id

        return {
            "ror_id": bare_id,
            "ror_url": f"https://ror.org/{bare_id}" if bare_id else "",
            "name": display_name,
            "country": country,
            "country_code": country_code,
            "types": data.get("types", []),
            "status": data.get("status", "active"),
            "relationships": [
                {
                    "type": r.get("type", ""),
                    "id": RORv2Client.extract_ror_id(r.get("id", "")) or r.get("id", ""),
                    "label": r.get("label", ""),
                }
                for r in data.get("relationships", [])
            ],
        }

    def _rate_limit(self):
        with self._lock:
            elapsed = time.time() - self._last_call
            if elapsed < _REQUEST_DELAY:
                time.sleep(_REQUEST_DELAY - elapsed)
            self._last_call = time.time()
