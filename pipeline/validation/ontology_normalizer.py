"""
FBbi ontology normalizer for microscopy technique standardization.

Uses the EBI Ontology Lookup Service (OLS4) API to map microscopy
technique names to FBbi (Biological Imaging methods) ontology term IDs.

FBbi (http://www.ebi.ac.uk/ols4/ontologies/fbbi) provides standardized
identifiers for biological imaging methods:
  - Confocal Laser Scanning Microscopy → FBbi:00000332
  - Two-Photon Excitation Microscopy   → FBbi:00000246
  - Structured Illumination Microscopy → FBbi:00000332
  etc.

This normalizer:
  1. Maintains a pre-built mapping of common technique names to FBbi IDs
  2. Falls back to OLS4 API search for techniques not in the static map
  3. Caches all lookups to minimize API calls

OLS4 API: https://www.ebi.ac.uk/ols4/api
  - No authentication required
  - Rate limit: ~10 req/sec (we use 0.2s delay)

Usage:
    from pipeline.validation.ontology_normalizer import OntologyNormalizer
    normalizer = OntologyNormalizer()
    result = normalizer.normalize_technique("Confocal Laser Scanning Microscopy")
    # {'fbbi_id': 'FBbi:00000332', 'fbbi_label': 'confocal microscopy',
    #  'ontology_iri': 'http://purl.obolibrary.org/obo/FBbi_00000332'}
"""

import json
import logging
import os
import re
import time
from typing import Any, Dict, List, Optional
from urllib.parse import quote

logger = logging.getLogger(__name__)

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

_OLS4_BASE = "https://www.ebi.ac.uk/ols4/api"

# ======================================================================
# Static mapping: common technique canonical names → FBbi IDs
#
# These are pre-mapped to avoid unnecessary API calls for the most
# common techniques.  FBbi IDs from the OBO Foundry:
# http://purl.obolibrary.org/obo/FBbi_NNNNN
# ======================================================================

_TECHNIQUE_TO_FBBI: Dict[str, Dict[str, str]] = {
    # --- Confocal and widefield ---
    "Confocal Laser Scanning Microscopy": {
        "fbbi_id": "FBbi:00000332",
        "fbbi_label": "confocal microscopy",
    },
    "Spinning Disk Confocal Microscopy": {
        "fbbi_id": "FBbi:00000253",
        "fbbi_label": "spinning disk confocal microscopy",
    },
    "Fluorescence Microscopy": {
        "fbbi_id": "FBbi:00000246",
        "fbbi_label": "fluorescence microscopy",
    },
    "Widefield Fluorescence Microscopy": {
        "fbbi_id": "FBbi:00000274",
        "fbbi_label": "wide-field fluorescence microscopy",
    },
    "Epifluorescence Microscopy": {
        "fbbi_id": "FBbi:00000274",
        "fbbi_label": "wide-field fluorescence microscopy",
    },
    "Brightfield Microscopy": {
        "fbbi_id": "FBbi:00000243",
        "fbbi_label": "bright-field microscopy",
    },
    "Phase Contrast Microscopy": {
        "fbbi_id": "FBbi:00000248",
        "fbbi_label": "phase contrast microscopy",
    },
    "Differential Interference Contrast Microscopy": {
        "fbbi_id": "FBbi:00000245",
        "fbbi_label": "differential interference contrast (DIC) microscopy",
    },
    "Darkfield Microscopy": {
        "fbbi_id": "FBbi:00000269",
        "fbbi_label": "dark-field microscopy",
    },
    "Polarization Microscopy": {
        "fbbi_id": "FBbi:00000270",
        "fbbi_label": "polarization microscopy",
    },

    # --- Super-resolution ---
    "Stimulated Emission Depletion Microscopy": {
        "fbbi_id": "FBbi:00000414",
        "fbbi_label": "STED microscopy",
    },
    "Structured Illumination Microscopy": {
        "fbbi_id": "FBbi:00000336",
        "fbbi_label": "structured illumination microscopy (SIM)",
    },
    "Stochastic Optical Reconstruction Microscopy": {
        "fbbi_id": "FBbi:00000335",
        "fbbi_label": "stochastic optical reconstruction microscopy (STORM)",
    },
    "Direct Stochastic Optical Reconstruction Microscopy": {
        "fbbi_id": "FBbi:00000335",
        "fbbi_label": "stochastic optical reconstruction microscopy (STORM)",
    },
    "Photoactivated Localization Microscopy": {
        "fbbi_id": "FBbi:00000334",
        "fbbi_label": "photoactivated localization microscopy (PALM)",
    },
    "Single-Molecule Localization Microscopy": {
        "fbbi_id": "FBbi:00000333",
        "fbbi_label": "single-molecule localization microscopy",
    },
    "Super-Resolution Microscopy": {
        "fbbi_id": "FBbi:00000330",
        "fbbi_label": "super-resolution microscopy",
    },
    "Expansion Microscopy": {
        "fbbi_id": "FBbi:00000586",
        "fbbi_label": "expansion microscopy",
    },

    # --- Multiphoton ---
    "Two-Photon Excitation Microscopy": {
        "fbbi_id": "FBbi:00000254",
        "fbbi_label": "two-photon laser-scanning microscopy",
    },
    "Multiphoton Microscopy": {
        "fbbi_id": "FBbi:00000255",
        "fbbi_label": "multi-photon microscopy",
    },
    "Three-Photon Microscopy": {
        "fbbi_id": "FBbi:00000255",
        "fbbi_label": "multi-photon microscopy",
    },

    # --- Light sheet ---
    "Light Sheet Fluorescence Microscopy": {
        "fbbi_id": "FBbi:00000369",
        "fbbi_label": "light sheet fluorescence microscopy (LSFM)",
    },
    "Lattice Light Sheet Microscopy": {
        "fbbi_id": "FBbi:00000369",
        "fbbi_label": "light sheet fluorescence microscopy (LSFM)",
    },

    # --- TIRF ---
    "Total Internal Reflection Fluorescence Microscopy": {
        "fbbi_id": "FBbi:00000275",
        "fbbi_label": "total internal reflection fluorescence microscopy (TIRF)",
    },

    # --- Spectroscopy / functional ---
    "Fluorescence Lifetime Imaging Microscopy": {
        "fbbi_id": "FBbi:00000276",
        "fbbi_label": "fluorescence lifetime imaging microscopy (FLIM)",
    },
    "Fluorescence Recovery After Photobleaching": {
        "fbbi_id": "FBbi:00000285",
        "fbbi_label": "fluorescence recovery after photobleaching (FRAP)",
    },
    "Förster Resonance Energy Transfer": {
        "fbbi_id": "FBbi:00000280",
        "fbbi_label": "Förster resonance energy transfer (FRET)",
    },
    "Fluorescence Correlation Spectroscopy": {
        "fbbi_id": "FBbi:00000282",
        "fbbi_label": "fluorescence correlation spectroscopy (FCS)",
    },
    "Fluorescence Cross-Correlation Spectroscopy": {
        "fbbi_id": "FBbi:00000283",
        "fbbi_label": "fluorescence cross-correlation spectroscopy (FCCS)",
    },
    "Fluorescence Loss in Photobleaching": {
        "fbbi_id": "FBbi:00000287",
        "fbbi_label": "fluorescence loss in photobleaching (FLIP)",
    },

    # --- Electron microscopy ---
    "Transmission Electron Microscopy": {
        "fbbi_id": "FBbi:00000258",
        "fbbi_label": "transmission electron microscopy (TEM)",
    },
    "Scanning Electron Microscopy": {
        "fbbi_id": "FBbi:00000257",
        "fbbi_label": "scanning electron microscopy (SEM)",
    },
    "Cryo-Electron Microscopy": {
        "fbbi_id": "FBbi:00000371",
        "fbbi_label": "cryo-electron microscopy",
    },
    "Cryo-Electron Tomography": {
        "fbbi_id": "FBbi:00000372",
        "fbbi_label": "cryo-electron tomography",
    },
    "Focused Ion Beam Scanning Electron Microscopy": {
        "fbbi_id": "FBbi:00000404",
        "fbbi_label": "focused ion beam scanning electron microscopy (FIB-SEM)",
    },
    "Serial Block-Face Scanning Electron Microscopy": {
        "fbbi_id": "FBbi:00000389",
        "fbbi_label": "serial block-face scanning electron microscopy (SBF-SEM)",
    },
    "Correlative Light and Electron Microscopy": {
        "fbbi_id": "FBbi:00000417",
        "fbbi_label": "correlative light and electron microscopy (CLEM)",
    },
    "Immuno-Electron Microscopy": {
        "fbbi_id": "FBbi:00000416",
        "fbbi_label": "immuno-electron microscopy",
    },

    # --- AFM / SPM ---
    "Atomic Force Microscopy": {
        "fbbi_id": "FBbi:00000259",
        "fbbi_label": "atomic force microscopy (AFM)",
    },

    # --- Nonlinear / Raman ---
    "Coherent Anti-Stokes Raman Scattering": {
        "fbbi_id": "FBbi:00000368",
        "fbbi_label": "coherent anti-Stokes Raman scattering (CARS) microscopy",
    },
    "Stimulated Raman Scattering": {
        "fbbi_id": "FBbi:00000586",
        "fbbi_label": "stimulated Raman scattering (SRS) microscopy",
    },
    "Second Harmonic Generation": {
        "fbbi_id": "FBbi:00000340",
        "fbbi_label": "second harmonic generation (SHG) microscopy",
    },
    "Raman Microscopy": {
        "fbbi_id": "FBbi:00000366",
        "fbbi_label": "Raman microscopy",
    },

    # --- Other optical ---
    "Optical Coherence Tomography": {
        "fbbi_id": "FBbi:00000381",
        "fbbi_label": "optical coherence tomography (OCT)",
    },
    "Holographic Microscopy": {
        "fbbi_id": "FBbi:00000383",
        "fbbi_label": "digital holographic microscopy",
    },
    "Photoacoustic Microscopy": {
        "fbbi_id": "FBbi:00000580",
        "fbbi_label": "photoacoustic microscopy",
    },

    # --- Intravital / in vivo ---
    "Intravital Microscopy": {
        "fbbi_id": "FBbi:00000342",
        "fbbi_label": "intravital microscopy",
    },

    # --- Bioluminescence ---
    "Bioluminescence Imaging": {
        "fbbi_id": "FBbi:00000341",
        "fbbi_label": "bioluminescence microscopy",
    },
}


class OntologyNormalizer:
    """Normalize microscopy technique names to FBbi ontology IDs.

    Uses a three-tier approach:
      1. Static pre-built mapping for common techniques (fast, no API call)
      2. Local fbbi_name_lookup.json from downloaded OBO file (comprehensive)
      3. OLS4 API search for unmapped techniques (cached)
    """

    def __init__(self, delay: float = 0.2, local_path: str = None):
        self._cache: Dict[str, Optional[Dict[str, str]]] = {}
        self._last_call = 0.0
        self._delay = delay
        self._exhausted = False
        self._local_lookup: Dict[str, Dict] = {}
        self._local_loaded = False

        # Pre-populate cache from static mapping
        for name, mapping in _TECHNIQUE_TO_FBBI.items():
            self._cache[name.lower()] = mapping

        if local_path:
            self._load_local(local_path)

    def _load_local(self, path: str):
        """Load fbbi_name_lookup.json for comprehensive ontology matching."""
        json_path = path
        if os.path.isdir(path):
            json_path = os.path.join(path, "fbbi_name_lookup.json")

        if not os.path.exists(json_path):
            logger.warning("FBbi lookup not found at %s", json_path)
            return

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                self._local_lookup = json.load(f)
            self._local_loaded = True
            logger.info("FBbi local lookup loaded: %d entries",
                        len(self._local_lookup))
        except Exception as exc:
            logger.warning("Failed to load FBbi lookup: %s", exc)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def normalize_technique(
        self, technique_name: str
    ) -> Optional[Dict[str, str]]:
        """Map a microscopy technique name to its FBbi ontology term.

        Parameters
        ----------
        technique_name : str
            The canonical technique name (e.g., "Confocal Laser Scanning Microscopy").

        Returns
        -------
        dict or None
            If found, returns a dict with keys:
              - fbbi_id: FBbi term ID (e.g., "FBbi:00000332")
              - fbbi_label: The FBbi preferred label
              - ontology_iri: Full IRI (only set for API lookups)
            Returns None if no FBbi mapping exists.
        """
        if not technique_name:
            return None

        cache_key = technique_name.strip().lower()

        # Check cache (includes static mappings)
        if cache_key in self._cache:
            return self._cache[cache_key]

        # LOCAL LOOKUP (comprehensive, from downloaded OBO)
        if self._local_loaded:
            entry = self._local_lookup.get(cache_key)
            if entry and isinstance(entry, dict):
                fbbi_id = entry.get("id", "")
                result = {
                    "fbbi_id": fbbi_id,
                    "fbbi_label": entry.get("canonical_name", ""),
                    "ontology_iri": (
                        f"http://purl.obolibrary.org/obo/"
                        f"{fbbi_id.replace(':', '_')}"
                    ) if fbbi_id else "",
                }
                if entry.get("definition"):
                    result["definition"] = entry["definition"]
                self._cache[cache_key] = result
                return result

        # FALLBACK: OLS4 API search
        result = self._search_ols4(technique_name.strip())
        self._cache[cache_key] = result
        return result

    def normalize_techniques(
        self, technique_names: List[str]
    ) -> Dict[str, Optional[Dict[str, str]]]:
        """Normalize a list of technique names to FBbi IDs.

        Parameters
        ----------
        technique_names : list of str
            Canonical technique names.

        Returns
        -------
        dict mapping technique name -> FBbi mapping (or None)
        """
        results: Dict[str, Optional[Dict[str, str]]] = {}
        for name in technique_names:
            if not name:
                continue
            results[name] = self.normalize_technique(name)
        return results

    def enrich_techniques(
        self, technique_names: List[str]
    ) -> List[Dict[str, Any]]:
        """Enrich technique names with FBbi ontology IDs.

        Returns a list of dicts with the original name plus ontology metadata.
        """
        enriched: List[Dict[str, Any]] = []
        for name in technique_names:
            if not name:
                continue
            mapping = self.normalize_technique(name)
            entry: Dict[str, Any] = {"name": name}
            if mapping:
                entry["fbbi_id"] = mapping["fbbi_id"]
                entry["fbbi_label"] = mapping["fbbi_label"]
                if "ontology_iri" in mapping:
                    entry["ontology_iri"] = mapping["ontology_iri"]
            enriched.append(entry)
        return enriched

    # ------------------------------------------------------------------
    # OLS4 API search
    # ------------------------------------------------------------------

    def _search_ols4(self, name: str) -> Optional[Dict[str, str]]:
        """Search the OLS4 API for a FBbi term matching the technique name."""
        if not HAS_REQUESTS or self._exhausted:
            return None

        self._rate_limit()
        try:
            # Search within the FBbi ontology specifically
            resp = requests.get(
                f"{_OLS4_BASE}/search",
                params={
                    "q": name,
                    "ontology": "fbbi",
                    "type": "class",
                    "exact": "false",
                    "rows": 10,
                },
                timeout=15,
                headers={"Accept": "application/json"},
            )
            self._last_call = time.time()

            if resp.status_code == 429:
                logger.warning("OLS4 rate limited")
                self._exhausted = True
                return None

            if resp.status_code != 200:
                logger.debug("OLS4 HTTP %d for '%s'", resp.status_code, name)
                return None

            data = resp.json()
            return self._find_best_ols_match(data, name)

        except Exception as exc:
            logger.debug("OLS4 search error for '%s': %s", name, exc)
            return None

    def _find_best_ols_match(
        self, data: Dict[str, Any], query: str
    ) -> Optional[Dict[str, str]]:
        """Find the best FBbi match from OLS4 search results."""
        response = data.get("response", {})
        docs = response.get("docs", [])

        if not docs:
            return None

        query_lower = query.lower()

        # First pass: exact label match
        for doc in docs:
            label = doc.get("label", "")
            if label.lower() == query_lower:
                return self._parse_ols_doc(doc)

        # Second pass: label contains query or query contains label
        for doc in docs:
            label = doc.get("label", "").lower()
            synonyms = [s.lower() for s in doc.get("synonyms", [])]

            if query_lower in label or label in query_lower:
                return self._parse_ols_doc(doc)

            for syn in synonyms:
                if query_lower in syn or syn in query_lower:
                    return self._parse_ols_doc(doc)

        # Third pass: check for keyword overlap
        query_words = set(query_lower.split())
        # Remove common words that are not discriminative
        stop_words = {"microscopy", "microscope", "imaging", "the", "and", "of", "a"}
        query_keywords = query_words - stop_words

        if not query_keywords:
            return None

        best_score = 0
        best_doc = None
        for doc in docs:
            label = doc.get("label", "").lower()
            label_words = set(label.split()) - stop_words
            overlap = len(query_keywords & label_words)
            score = overlap / max(len(query_keywords), 1)
            if score > best_score and score >= 0.5:
                best_score = score
                best_doc = doc

        if best_doc:
            return self._parse_ols_doc(best_doc)

        return None

    @staticmethod
    def _parse_ols_doc(doc: Dict[str, Any]) -> Dict[str, str]:
        """Parse an OLS4 search result document into our mapping format."""
        iri = doc.get("iri", "")
        obo_id = doc.get("obo_id", "")
        short_form = doc.get("short_form", "")

        # Extract FBbi ID from various fields
        fbbi_id = ""
        if obo_id and obo_id.startswith("FBbi:"):
            fbbi_id = obo_id
        elif short_form and short_form.startswith("FBbi_"):
            fbbi_id = short_form.replace("FBbi_", "FBbi:")
        elif "FBbi_" in iri:
            # Extract from IRI like http://purl.obolibrary.org/obo/FBbi_00000332
            m = re.search(r"FBbi_(\d+)", iri)
            if m:
                fbbi_id = f"FBbi:{m.group(1)}"

        label = doc.get("label", "")

        result = {
            "fbbi_id": fbbi_id,
            "fbbi_label": label,
        }
        if iri:
            result["ontology_iri"] = iri

        return result

    # ------------------------------------------------------------------
    # Rate limiting
    # ------------------------------------------------------------------

    def _rate_limit(self) -> None:
        elapsed = time.time() - self._last_call
        if elapsed < self._delay:
            time.sleep(self._delay - elapsed)
