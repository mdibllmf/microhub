"""
Taxonomy validation using NCBI Taxonomy and PubTator APIs.

Validates organism names against NCBI Taxonomy IDs and enriches
extractions with taxonomic identifiers.
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# Common organisms pre-mapped to NCBI Taxonomy IDs
NCBI_TAXIDS: Dict[str, int] = {
    "Human": 9606,
    "Mouse": 10090,
    "Rat": 10116,
    "Zebrafish": 7955,
    "Drosophila": 7227,
    "C. elegans": 6239,
    "Xenopus": 8355,
    "Arabidopsis": 3702,
    "Yeast": 4932,
    "E. coli": 562,
    "Chicken": 9031,
    "Pig": 9823,
    "Dog": 9615,
    "Monkey": 9544,
    "Rabbit": 9986,
    "Maize": 4577,
    "Tobacco": 4097,
}

_PUBTATOR_API = "https://www.ncbi.nlm.nih.gov/research/pubtator3-api"


class TaxonomyValidator:
    """Validate organism names against NCBI Taxonomy."""

    def __init__(self):
        self._cache: Dict[str, Optional[int]] = {}

    def get_taxid(self, organism: str) -> Optional[int]:
        """Return NCBI Taxonomy ID for a canonical organism name."""
        # Check local mapping first
        taxid = NCBI_TAXIDS.get(organism)
        if taxid is not None:
            return taxid

        # Check cache
        if organism in self._cache:
            return self._cache[organism]

        # Query NCBI Taxonomy search
        taxid = self._query_ncbi(organism)
        self._cache[organism] = taxid
        return taxid

    def validate(self, organism: str) -> bool:
        """Check if organism is a valid taxonomic name."""
        return self.get_taxid(organism) is not None

    def annotate_with_pubtator(self, pmid: str) -> List[Dict]:
        """Get species annotations from PubTator for a given PMID."""
        if not HAS_REQUESTS:
            return []

        url = f"{_PUBTATOR_API}/publications/export/biocjson"
        try:
            resp = requests.get(url, params={"pmids": pmid}, timeout=15)
            if resp.status_code != 200:
                return []

            data = resp.json()
            species = []
            for passage in data.get("passages", []):
                for ann in passage.get("annotations", []):
                    if ann.get("infons", {}).get("type") == "Species":
                        species.append({
                            "text": ann.get("text"),
                            "ncbi_taxid": ann.get("infons", {}).get("identifier"),
                            "section": passage.get("infons", {}).get("type"),
                        })
            return species
        except Exception as exc:
            logger.debug("PubTator query failed for PMID %s: %s", pmid, exc)
            return []

    # ------------------------------------------------------------------
    def _query_ncbi(self, name: str) -> Optional[int]:
        """Query NCBI Taxonomy for a name."""
        if not HAS_REQUESTS:
            return None

        try:
            url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
            resp = requests.get(
                url,
                params={
                    "db": "taxonomy",
                    "term": f'"{name}"[Scientific Name]',
                    "retmode": "json",
                },
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                ids = data.get("esearchresult", {}).get("idlist", [])
                if ids:
                    return int(ids[0])
        except Exception as exc:
            logger.debug("NCBI Taxonomy lookup failed for '%s': %s", name, exc)

        return None
