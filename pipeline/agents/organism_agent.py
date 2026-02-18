"""
Organism / species recognition agent.

Following v3.7 rules: ONLY Latin names trigger organism extraction.
Common names alone ("mouse", "rat", "zebrafish") are NOT matched to
eliminate false positives from antibody descriptions.

Additional heuristics:
  - Title presence is the strongest signal for focal species
  - Co-occurrence with experimental terms boosts confidence
  - Antibody-source species (rabbit, goat, donkey) are filtered out
    unless they appear in a non-antibody context
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
    # Bare genus names
    "rattus": "Rat",
    "saccharomyces": "Yeast",
    "escherichia": "E. coli",
    "nicotiana": "Tobacco",
    "oryctolagus": "Rabbit",
    "gallus": "Chicken",
}

# Common-name patterns that require EXPERIMENTAL context
# (not just antibody mentions) to be extracted
_COMMON_WITH_CONTEXT: Dict[str, str] = {
    "mouse": "Mouse",
    "mice": "Mouse",
    "murine": "Mouse",
    "rat": "Rat",
    "rats": "Rat",
    "zebrafish": "Zebrafish",
    "fruit fly": "Drosophila",
    "fruit flies": "Drosophila",
    "nematode": "C. elegans",
    "worm": "C. elegans",
    "human": "Human",
    "patient": "Human",
    "frog": "Xenopus",
    "yeast": "Yeast",
    "chicken": "Chicken",
    "pig": "Pig",
    "porcine": "Pig",
    "canine": "Dog",
    "dog": "Dog",
    "primate": "Monkey",
    "macaque": "Monkey",
    "monkey": "Monkey",
    "chick": "Chicken",
    "rice": "Rice",
    "corn": "Maize",
    # NOTE: "plant", "organoid", "spheroid", "bacteria" are NOT organisms
    # and should not be extracted as tags — they are too generic.
}

# Experimental context terms -- when a common name co-occurs with these,
# the organism is likely a study subject
_EXPERIMENTAL_CONTEXT = re.compile(
    r"\b(?:cultured?|sacrificed?|anestheti[sz]ed|perfused?|injected?"
    r"|transfected?|dissected?|wild[- ]?type|knockout|transgenic"
    r"|mutant|embryo\w*|larva[el]?|pup|neonate|adult|juvenile"
    r"|male|female|bred|housed|maintained|strain|line\b)",
    re.IGNORECASE,
)

# Antibody-source patterns -- these species names often appear only in
# the context of antibody descriptions
_ANTIBODY_SOURCE_PATTERN = re.compile(
    r"\b(?:rabbit|goat|donkey|sheep|guinea\s+pig|hamster|chicken|rat|mouse)"
    r"\s+(?:anti[- ]|polyclonal|monoclonal|IgG|secondary|primary)",
    re.IGNORECASE,
)

_ANTIBODY_PREFIX_PATTERN = re.compile(
    r"(?:anti[- ]|polyclonal|monoclonal|secondary|primary)\s+"
    r"(?:rabbit|goat|donkey|sheep|guinea\s+pig|hamster)",
    re.IGNORECASE,
)

# Species that are almost always antibody sources
_COMMON_ANTIBODY_SPECIES: Set[str] = {
    "rabbit", "goat", "donkey", "sheep", "guinea pig", "hamster",
}


class OrganismAgent(BaseAgent):
    """Extract study organisms using Latin names and contextual common names."""

    name = "organism"

    def analyze(self, text: str, section: str = None) -> List[Extraction]:
        results: List[Extraction] = []
        antibody_species = self._find_antibody_species(text)

        # 1. Latin name matching (always high confidence)
        results.extend(self._latin_match(text, section))

        # 2. Common name matching with experimental context
        results.extend(
            self._common_match(text, section, antibody_species)
        )

        return self._deduplicate(results)

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
    def _common_match(self, text: str, section: str = None,
                      antibody_species: Set[str] = None) -> List[Extraction]:
        """Match common names only when experimental context is nearby."""
        extractions: List[Extraction] = []
        antibody_species = antibody_species or set()

        for common, canonical in _COMMON_WITH_CONTEXT.items():
            # Skip if this species only appears as an antibody source
            if common.lower() in antibody_species:
                continue

            pattern = re.compile(r"\b" + re.escape(common) + r"\b", re.I)
            for m in pattern.finditer(text):
                # Check for experimental context within +-200 chars
                window_start = max(0, m.start() - 200)
                window_end = min(len(text), m.end() + 200)
                window = text[window_start:window_end]

                if _EXPERIMENTAL_CONTEXT.search(window):
                    conf = 0.8 if section in ("methods", "results") else 0.6
                    extractions.append(Extraction(
                        text=m.group(0),
                        label="ORGANISM",
                        start=m.start(),
                        end=m.end(),
                        confidence=conf,
                        source_agent=self.name,
                        section=section or "",
                        metadata={"canonical": canonical, "match_type": "common_with_context"},
                    ))

        return extractions

    # ------------------------------------------------------------------
    def _find_antibody_species(self, text: str) -> Set[str]:
        """Identify species that appear ONLY as antibody sources."""
        antibody_mentions: Set[str] = set()
        for m in _ANTIBODY_SOURCE_PATTERN.finditer(text):
            first_word = m.group(0).split()[0].lower()
            antibody_mentions.add(first_word)
        for m in _ANTIBODY_PREFIX_PATTERN.finditer(text):
            last_word = m.group(0).split()[-1].lower()
            antibody_mentions.add(last_word)

        # Only filter species that are COMMON antibody sources
        return antibody_mentions & _COMMON_ANTIBODY_SPECIES

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
