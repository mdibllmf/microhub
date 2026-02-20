"""
Organism / species recognition agent.

STRICT RULE: ONLY Latin names trigger organism extraction.
Common names alone ("mouse", "rat", "zebrafish") are NEVER matched
to eliminate false positives from antibody descriptions (e.g.
"anti-rat", "rabbit polyclonal", "goat secondary").

Canonical names are always the full scientific (Latin) binomial name
(e.g. "Mus musculus", "Danio rerio"), never common names.
"""

import re
from typing import Dict, List, Set

from .base_agent import BaseAgent, Extraction

# ======================================================================
# Latin name → canonical scientific name
# ======================================================================

ORGANISM_LATIN: Dict[str, str] = {
    # Full Latin names → canonical scientific name
    "mus musculus": "Mus musculus",
    "rattus norvegicus": "Rattus norvegicus",
    "homo sapiens": "Homo sapiens",
    "danio rerio": "Danio rerio",
    "drosophila melanogaster": "Drosophila melanogaster",
    "drosophila": "Drosophila melanogaster",
    "caenorhabditis elegans": "Caenorhabditis elegans",
    "c. elegans": "Caenorhabditis elegans",
    "c elegans": "Caenorhabditis elegans",
    "xenopus laevis": "Xenopus laevis",
    "xenopus tropicalis": "Xenopus tropicalis",
    "xenopus": "Xenopus laevis",
    "arabidopsis thaliana": "Arabidopsis thaliana",
    "arabidopsis": "Arabidopsis thaliana",
    "saccharomyces cerevisiae": "Saccharomyces cerevisiae",
    "schizosaccharomyces pombe": "Schizosaccharomyces pombe",
    "escherichia coli": "Escherichia coli",
    "e. coli": "Escherichia coli",
    "e coli": "Escherichia coli",
    "gallus gallus": "Gallus gallus",
    "sus scrofa": "Sus scrofa",
    "canis familiaris": "Canis lupus familiaris",
    "canis lupus familiaris": "Canis lupus familiaris",
    "macaca mulatta": "Macaca mulatta",
    "macaca fascicularis": "Macaca fascicularis",
    "callithrix jacchus": "Callithrix jacchus",
    "zea mays": "Zea mays",
    "nicotiana benthamiana": "Nicotiana benthamiana",
    "nicotiana tabacum": "Nicotiana tabacum",
    "oryctolagus cuniculus": "Oryctolagus cuniculus",
    "oryza sativa": "Oryza sativa",
    # Abbreviated Latin names (e.g., M. musculus)
    "m. musculus": "Mus musculus",
    "h. sapiens": "Homo sapiens",
    "r. norvegicus": "Rattus norvegicus",
    "d. rerio": "Danio rerio",
    "d. melanogaster": "Drosophila melanogaster",
    "x. laevis": "Xenopus laevis",
    "x. tropicalis": "Xenopus tropicalis",
    "g. gallus": "Gallus gallus",
    "s. scrofa": "Sus scrofa",
    "m. mulatta": "Macaca mulatta",
    "m. fascicularis": "Macaca fascicularis",
    "o. cuniculus": "Oryctolagus cuniculus",
    "c. familiaris": "Canis lupus familiaris",
    "s. cerevisiae": "Saccharomyces cerevisiae",
    "s. pombe": "Schizosaccharomyces pombe",
    "a. thaliana": "Arabidopsis thaliana",
    "n. tabacum": "Nicotiana tabacum",
    "n. benthamiana": "Nicotiana benthamiana",
    "z. mays": "Zea mays",
    "o. sativa": "Oryza sativa",
    # New organisms
    "bos taurus": "Bos taurus",
    "ovis aries": "Ovis aries",
    "equus caballus": "Equus caballus",
    "dictyostelium discoideum": "Dictyostelium discoideum",
    "dictyostelium": "Dictyostelium discoideum",
    "d. discoideum": "Dictyostelium discoideum",
    "neurospora crassa": "Neurospora crassa",
    "neurospora": "Neurospora crassa",
    "n. crassa": "Neurospora crassa",
    "chlamydomonas reinhardtii": "Chlamydomonas reinhardtii",
    "chlamydomonas": "Chlamydomonas reinhardtii",
    "c. reinhardtii": "Chlamydomonas reinhardtii",
    "trypanosoma brucei": "Trypanosoma brucei",
    "trypanosoma": "Trypanosoma brucei",
    "t. brucei": "Trypanosoma brucei",
    "plasmodium falciparum": "Plasmodium falciparum",
    "plasmodium": "Plasmodium falciparum",
    "p. falciparum": "Plasmodium falciparum",
    "ciona intestinalis": "Ciona intestinalis",
    "ciona": "Ciona intestinalis",
    "c. intestinalis": "Ciona intestinalis",
    "hydra vulgaris": "Hydra vulgaris",
    "h. vulgaris": "Hydra vulgaris",
    "nematostella vectensis": "Nematostella vectensis",
    "nematostella": "Nematostella vectensis",
    "n. vectensis": "Nematostella vectensis",
    "aedes aegypti": "Aedes aegypti",
    "aedes": "Aedes aegypti",
    "a. aegypti": "Aedes aegypti",
    "apis mellifera": "Apis mellifera",
    "a. mellifera": "Apis mellifera",
    "daphnia magna": "Daphnia magna",
    "daphnia": "Daphnia magna",
    "d. magna": "Daphnia magna",
    "schmidtea mediterranea": "Schmidtea mediterranea",
    "s. mediterranea": "Schmidtea mediterranea",
    "pristionchus pacificus": "Pristionchus pacificus",
    "p. pacificus": "Pristionchus pacificus",
    "b. taurus": "Bos taurus",
    "o. aries": "Ovis aries",
    "e. caballus": "Equus caballus",
    # Bare genus names (only those distinctive enough to be unambiguous)
    "rattus": "Rattus norvegicus",
    "saccharomyces": "Saccharomyces cerevisiae",
    "escherichia": "Escherichia coli",
    "nicotiana": "Nicotiana tabacum",
    "oryctolagus": "Oryctolagus cuniculus",
    "pristionchus": "Pristionchus pacificus",
    "schmidtea": "Schmidtea mediterranea",
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
