"""
Organism / species recognition agent.

STRICT RULE: ONLY Latin names trigger organism extraction.
Common names alone ("mouse", "rat", "zebrafish") are NEVER matched
to eliminate false positives from antibody descriptions (e.g.
"anti-rat", "rabbit polyclonal", "goat secondary").

Latin names are then normalised to a single canonical display name
(e.g. "Mus musculus" → "Mouse") in the normalization step.
"""

import re
from typing import Dict, List, Set

from .base_agent import BaseAgent, Extraction

# ======================================================================
# Latin name → canonical display name
# ======================================================================

ORGANISM_LATIN: Dict[str, str] = {
    # Full Latin names
    "mus musculus": "Mouse",
    "rattus norvegicus": "Rat",
    "homo sapiens": "Human",
    "danio rerio": "Zebrafish",
    "drosophila melanogaster": "Drosophila",
    "drosophila": "Drosophila",
    "caenorhabditis elegans": "C. elegans",
    "c. elegans": "C. elegans",
    "c elegans": "C. elegans",
    "xenopus laevis": "Xenopus",
    "xenopus tropicalis": "Xenopus",
    "xenopus": "Xenopus",
    "arabidopsis thaliana": "Arabidopsis",
    "arabidopsis": "Arabidopsis",
    "saccharomyces cerevisiae": "Yeast",
    "schizosaccharomyces pombe": "Yeast",
    "escherichia coli": "E. coli",
    "e. coli": "E. coli",
    "e coli": "E. coli",
    "gallus gallus": "Chicken",
    "sus scrofa": "Pig",
    "canis familiaris": "Dog",
    "canis lupus familiaris": "Dog",
    "macaca mulatta": "Monkey",
    "macaca fascicularis": "Monkey",
    "callithrix jacchus": "Monkey",
    "zea mays": "Maize",
    "nicotiana benthamiana": "Tobacco",
    "nicotiana tabacum": "Tobacco",
    "oryctolagus cuniculus": "Rabbit",
    "oryza sativa": "Rice",
    # Abbreviated Latin names (e.g., M. musculus)
    "m. musculus": "Mouse",
    "h. sapiens": "Human",
    "r. norvegicus": "Rat",
    "d. rerio": "Zebrafish",
    "d. melanogaster": "Drosophila",
    "x. laevis": "Xenopus",
    "x. tropicalis": "Xenopus",
    "g. gallus": "Chicken",
    "s. scrofa": "Pig",
    "m. mulatta": "Monkey",
    "m. fascicularis": "Monkey",
    "o. cuniculus": "Rabbit",
    "c. familiaris": "Dog",
    "s. cerevisiae": "Yeast",
    "s. pombe": "Yeast",
    "a. thaliana": "Arabidopsis",
    "n. tabacum": "Tobacco",
    "n. benthamiana": "Tobacco",
    "z. mays": "Maize",
    "o. sativa": "Rice",
    # Bare genus names (only those distinctive enough to be unambiguous)
    "rattus": "Rat",
    "saccharomyces": "Yeast",
    "escherichia": "E. coli",
    "nicotiana": "Tobacco",
    "oryctolagus": "Rabbit",
}

# Antibody-source patterns -- these species names often appear only in
# the context of antibody descriptions
_ANTIBODY_SOURCE_PATTERN = re.compile(
    r"\b(?:rabbit|goat|donkey|sheep|guinea\s+pig|hamster|chicken|rat|mouse)"
    r"\s+(?:anti[- ]|polyclonal|monoclonal|IgG|secondary|primary)",
    re.IGNORECASE,
)


class OrganismAgent(BaseAgent):
    """Extract study organisms using Latin names ONLY."""

    name = "organism"

    def analyze(self, text: str, section: str = None) -> List[Extraction]:
        # Latin name matching only — no common names
        return self._deduplicate(self._latin_match(text, section))

    # ------------------------------------------------------------------
    def _latin_match(self, text: str, section: str = None) -> List[Extraction]:
        extractions: List[Extraction] = []
        for latin, canonical in ORGANISM_LATIN.items():
            pattern = re.compile(r"\b" + re.escape(latin) + r"\b", re.I)
            for m in pattern.finditer(text):
                extractions.append(Extraction(
                    text=m.group(0),
                    label="ORGANISM",
                    start=m.start(),
                    end=m.end(),
                    confidence=0.95,
                    source_agent=self.name,
                    section=section or "",
                    metadata={"canonical": canonical, "match_type": "latin"},
                ))
        return extractions

    # ------------------------------------------------------------------
    def extract_antibody_sources(self, text: str,
                                 section: str = None) -> List[Extraction]:
        """Separately extract antibody source species for the antibody_sources field."""
        extractions: List[Extraction] = []
        for m in _ANTIBODY_SOURCE_PATTERN.finditer(text):
            species = m.group(0).split()[0]
            extractions.append(Extraction(
                text=species,
                label="ANTIBODY_SOURCE",
                start=m.start(),
                end=m.start() + len(species),
                confidence=0.85,
                source_agent=self.name,
                section=section or "",
                metadata={"canonical": species.capitalize()},
            ))
        return self._deduplicate(extractions)
