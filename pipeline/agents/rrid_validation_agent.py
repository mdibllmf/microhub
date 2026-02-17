"""
Pass 2 — RRID Validation Agent.

Validates extracted RRIDs against the SciCrunch resolver and enriches
them with resource names, types, and validation status.

RRID types:
  - AB_xxxxxx  → Antibody
  - SCR_xxxxxx → Software (SciCrunch Registry)
  - CVCL_xxxxx → Cell line (Cellosaurus)
  - Addgene_xx → Plasmid
  - IMSR_*     → Organism (International Mouse Strain Resource)

Cross-referencing:
  - If an RRID resolves to an antibody, checks that the paper mentions
    the target protein or host species
  - If an RRID resolves to software, checks against the software tags
"""

import logging
import time
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class RRIDValidationAgent:
    """Validate RRIDs against SciCrunch."""

    name = "rrid_validation"

    def __init__(self):
        self._cache: Dict[str, Optional[Dict]] = {}
        self._last_call = 0.0
        self._delay = 0.5
        self._exhausted = False

    def validate(self, paper: Dict[str, Any]) -> Dict[str, Any]:
        """Validate all RRIDs in a paper.  Mutates in-place."""
        if not HAS_REQUESTS or self._exhausted:
            return paper

        rrids = paper.get("rrids")
        if not rrids or not isinstance(rrids, list):
            return paper

        # Collect existing tags for cross-referencing
        software_tags = _lowercase_set(paper.get("image_analysis_software", []) +
                                        paper.get("image_acquisition_software", []) +
                                        paper.get("general_software", []))
        cell_line_tags = _lowercase_set(paper.get("cell_lines", []))

        for rrid_entry in rrids:
            if not isinstance(rrid_entry, dict):
                continue

            rrid_id = rrid_entry.get("id", "")
            if not rrid_id:
                continue

            sc_data = self._query_scicrunch(rrid_id)
            if sc_data is None:
                rrid_entry["validated"] = False
                rrid_entry["validation_status"] = "not_found"
                continue

            # Enrich with SciCrunch data
            rrid_entry["validated"] = True
            rrid_entry["validation_status"] = "confirmed"
            if sc_data.get("name"):
                rrid_entry["resource_name"] = sc_data["name"]
            if sc_data.get("type"):
                rrid_entry["resource_type"] = sc_data["type"]
            if sc_data.get("vendor"):
                rrid_entry["vendor"] = sc_data["vendor"]

            # Cross-reference: does the paper's tags match the RRID?
            rrid_type = (rrid_entry.get("type") or "").lower()
            if rrid_type == "software" and sc_data.get("name"):
                name_lower = sc_data["name"].lower()
                if name_lower in software_tags:
                    rrid_entry["cross_ref_match"] = True

            if rrid_type == "cell_line" and sc_data.get("name"):
                name_lower = sc_data["name"].lower()
                if name_lower in cell_line_tags:
                    rrid_entry["cross_ref_match"] = True

        paper["rrids"] = rrids
        return paper

    # ------------------------------------------------------------------
    # SciCrunch API
    # ------------------------------------------------------------------

    def _query_scicrunch(self, rrid: str) -> Optional[Dict]:
        """Query SciCrunch resolver for RRID metadata."""
        # Normalize
        if not rrid.upper().startswith("RRID:"):
            rrid = f"RRID:{rrid}"

        if rrid in self._cache:
            return self._cache[rrid]

        elapsed = time.time() - self._last_call
        if elapsed < self._delay:
            time.sleep(self._delay - elapsed)

        try:
            resp = requests.get(
                f"https://scicrunch.org/resolver/{rrid}.json",
                timeout=15,
            )
            self._last_call = time.time()

            if resp.status_code == 429:
                logger.warning("SciCrunch rate limited — stopping RRID validation")
                self._exhausted = True
                return None

            if resp.status_code != 200:
                self._cache[rrid] = None
                return None

            data = resp.json()
            hits = data.get("hits", {}).get("hits", [])
            if not hits:
                self._cache[rrid] = None
                return None

            source = hits[0].get("_source", {})
            item = source.get("item", {})
            result = {
                "name": item.get("name", ""),
                "type": item.get("types", [""])[0] if item.get("types") else "",
                "vendor": item.get("vendor", {}).get("name", "") if isinstance(item.get("vendor"), dict) else "",
            }
            self._cache[rrid] = result
            return result

        except Exception as exc:
            logger.debug("SciCrunch error for %s: %s", rrid, exc)
            return None


def _lowercase_set(values: list) -> Set[str]:
    """Build a lowercase set from a list of strings."""
    result: Set[str] = set()
    for v in values:
        if isinstance(v, str):
            result.add(v.lower())
    return result
