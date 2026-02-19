"""
Multi-stage role classifier for preventing over-tagging.

Over-tagging is the most pernicious failure mode in biomedical NLP:
assigning metadata tags to every entity mentioned regardless of whether
it was actually used in the study.

This module implements a 4-stage architecture:
  1. Section-aware weighting (Methods=1.0, Results=0.85, Discussion=0.30)
  2. Linguistic signal detection (verb patterns, citation proximity, negation)
  3. Role classification (USED, REFERENCED, COMPARED, NEGATED)
  4. Document-level consolidation (one USED in Methods outweighs mentions elsewhere)

Usage:
    from pipeline.role_classifier import RoleClassifier
    classifier = RoleClassifier()
    classified = classifier.classify_extractions(extractions, sections)
    filtered = classifier.filter_used_entities(classified)
"""

import re
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class EntityRole(Enum):
    """Role of an entity mention in a paper."""
    USED = "used"               # Actually used in this study
    REFERENCED = "referenced"   # Referenced from other work
    COMPARED = "compared"       # Used as comparison/alternative
    NEGATED = "negated"         # Explicitly not used ("we did not use X")
    AMBIGUOUS = "ambiguous"     # Cannot determine role


@dataclass
class ClassifiedExtraction:
    """An extraction with role classification."""
    text: str
    label: str
    canonical: str
    section: str
    confidence: float
    source_agent: str
    role: EntityRole
    role_confidence: float
    role_signals: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)


# ======================================================================
# Section weights (Stage 1)
# ======================================================================

# Confidence that an entity in this section was actually USED
SECTION_USAGE_WEIGHTS = {
    "methods": 1.0,
    "materials": 1.0,
    "materials_and_methods": 1.0,
    "results": 0.85,
    "abstract": 0.70,
    "title": 0.80,
    "figures": 0.80,
    "data_availability": 0.60,
    "full_text": 0.60,
    "discussion": 0.30,
    "introduction": 0.20,
    "references": 0.0,    # Never tag from references
    "bibliography": 0.0,
}


# ======================================================================
# Linguistic signals (Stage 2)
# ======================================================================

# Past-tense active voice patterns indicating actual usage
_USAGE_VERB_PATTERNS = [
    # "we used X", "we performed X", "images were acquired using X"
    re.compile(
        r"\b(?:we|authors?)\s+"
        r"(?:used|employed|utilized|performed|conducted|acquired|imaged|"
        r"recorded|collected|stained|labeled|labelled|transfected|"
        r"processed|analyzed|analysed|visualized|mounted|incubated|"
        r"fixed|embedded|sectioned|observed|captured|scanned)\b",
        re.I,
    ),
    # Passive: "X was used", "images were acquired using X"
    re.compile(
        r"\b(?:was|were)\s+"
        r"(?:used|employed|utilized|performed|conducted|acquired|imaged|"
        r"recorded|collected|stained|labeled|labelled|processed|"
        r"analyzed|analysed|visualized|observed|captured|carried\s+out)\b",
        re.I,
    ),
    # "using X", "with X software", "on a X microscope"
    re.compile(
        r"\b(?:using|with|on\s+(?:a|an|the))\s+", re.I,
    ),
    # "X was performed", "imaging was done with X"
    re.compile(
        r"\b(?:imaging|microscopy|analysis|processing|acquisition|"
        r"staining|labeling|preparation)\s+(?:was|were)\s+"
        r"(?:performed|done|carried\s+out|conducted)\b",
        re.I,
    ),
]

# Present-tense general statements indicating background reference
_REFERENCE_VERB_PATTERNS = [
    # "X is commonly used for", "X has been shown to"
    re.compile(
        r"\b(?:is|are|has\s+been|have\s+been)\s+"
        r"(?:commonly|widely|frequently|typically|routinely|often|"
        r"generally|traditionally|previously|recently|increasingly)\s+"
        r"(?:used|employed|applied|adopted|utilized)\b",
        re.I,
    ),
    # "X provides", "X allows", "X enables"
    re.compile(
        r"\b(?:provides?|allows?|enables?|offers?|permits?|facilitates?)\b",
        re.I,
    ),
    # "X can be used", "X may be applied"
    re.compile(
        r"\b(?:can|could|may|might|should|would)\s+be\s+"
        r"(?:used|employed|applied|utilized)\b",
        re.I,
    ),
]

# Citation proximity patterns (nearby citation markers → reference to others' work)
_CITATION_PATTERNS = [
    # Numbered citations: [1], [1,2], [1-3]
    re.compile(r"\[\d+(?:[,;\s-]+\d+)*\]"),
    # Author-year: (Smith et al., 2020), (Smith and Jones, 2019)
    re.compile(r"\([A-Z][a-z]+\s+(?:et\s+al\.?,?\s+)?\d{4}[a-z]?\)"),
    re.compile(r"\([A-Z][a-z]+\s+and\s+[A-Z][a-z]+,?\s+\d{4}\)"),
]

# Negation and comparison patterns
_NEGATION_PATTERNS = [
    # "we did not use X", "X was not used"
    re.compile(
        r"\b(?:did\s+not|didn['']t|was\s+not|wasn['']t|were\s+not|weren['']t|"
        r"not\s+(?:used|employed|utilized|applied))\b",
        re.I,
    ),
    # "without X", "in the absence of X"
    re.compile(r"\b(?:without|in\s+the\s+absence\s+of|excluding|except)\b", re.I),
    # "no X was", "neither X nor"
    re.compile(r"\b(?:no\s+\w+\s+was|neither\s+\w+\s+nor)\b", re.I),
]

_COMPARISON_PATTERNS = [
    # "unlike X", "in contrast to X", "compared to X"
    re.compile(
        r"\b(?:unlike|in\s+contrast\s+to|compared\s+(?:to|with)|"
        r"as\s+opposed\s+to|rather\s+than|instead\s+of|"
        r"alternative\s+to|superior\s+to|inferior\s+to)\b",
        re.I,
    ),
]

# Context window (characters around entity to scan for signals)
_CONTEXT_WINDOW = 200


class RoleClassifier:
    """Classify entity mentions as USED, REFERENCED, COMPARED, or NEGATED."""

    def __init__(self, *, min_used_confidence: float = 0.50,
                 auto_tag_threshold: float = 0.85,
                 review_threshold: float = 0.50):
        """
        Parameters
        ----------
        min_used_confidence : float
            Minimum combined confidence to classify as USED.
        auto_tag_threshold : float
            Above this, auto-tag without review.
        review_threshold : float
            Between this and auto_tag_threshold, flag for review.
        """
        self.min_used_confidence = min_used_confidence
        self.auto_tag_threshold = auto_tag_threshold
        self.review_threshold = review_threshold

    # ------------------------------------------------------------------
    # Stage 1: Section-aware weighting
    # ------------------------------------------------------------------

    @staticmethod
    def section_weight(section: str) -> float:
        """Get the usage weight for a section type."""
        section = (section or "full_text").lower()
        if section in ("materials", "materials_and_methods"):
            section = "methods"
        return SECTION_USAGE_WEIGHTS.get(section, 0.50)

    # ------------------------------------------------------------------
    # Stage 2: Linguistic signal detection
    # ------------------------------------------------------------------

    def detect_signals(self, text: str, entity_text: str,
                       entity_start: int, entity_end: int) -> Tuple[
            List[str], float]:
        """Detect linguistic signals around an entity mention.

        Parameters
        ----------
        text : str
            Full section text.
        entity_text : str
            The entity mention text.
        entity_start, entity_end : int
            Character offsets of the entity in text.

        Returns
        -------
        (signals, adjustment) : (list of str, float)
            signals: List of detected signal descriptions.
            adjustment: Score adjustment (-1.0 to +1.0).
        """
        signals: List[str] = []
        adjustment = 0.0

        # Get context window around entity
        ctx_start = max(0, entity_start - _CONTEXT_WINDOW)
        ctx_end = min(len(text), entity_end + _CONTEXT_WINDOW)
        context = text[ctx_start:ctx_end]

        # Check usage verb patterns
        for pattern in _USAGE_VERB_PATTERNS:
            if pattern.search(context):
                signals.append("usage_verb")
                adjustment += 0.15
                break  # one signal is enough

        # Check reference verb patterns
        for pattern in _REFERENCE_VERB_PATTERNS:
            if pattern.search(context):
                signals.append("reference_verb")
                adjustment -= 0.20
                break

        # Check citation proximity
        for pattern in _CITATION_PATTERNS:
            matches = list(pattern.finditer(context))
            for m in matches:
                # Citation within 50 chars of entity
                cite_pos = m.start() + ctx_start
                if abs(cite_pos - entity_start) < 80:
                    signals.append("citation_proximity")
                    adjustment -= 0.25
                    break
            if "citation_proximity" in signals:
                break

        # Check negation
        for pattern in _NEGATION_PATTERNS:
            if pattern.search(context):
                signals.append("negation")
                adjustment -= 0.50
                break

        # Check comparison
        for pattern in _COMPARISON_PATTERNS:
            if pattern.search(context):
                signals.append("comparison")
                adjustment -= 0.15
                break

        return signals, adjustment

    # ------------------------------------------------------------------
    # Stage 3: Role classification
    # ------------------------------------------------------------------

    def classify_extraction(self, text: str, entity_text: str,
                            entity_start: int, entity_end: int,
                            section: str,
                            base_confidence: float) -> Tuple[EntityRole, float, List[str]]:
        """Classify a single entity extraction.

        Returns
        -------
        (role, confidence, signals)
        """
        # Stage 1: section weight
        section_w = self.section_weight(section)

        # Stage 2: linguistic signals
        signals, adjustment = self.detect_signals(
            text, entity_text, entity_start, entity_end
        )

        # Combine
        combined = (section_w * 0.5 + base_confidence * 0.3 + 0.5 + adjustment * 0.2)
        combined = max(0.0, min(1.0, combined))

        # Stage 3: determine role
        if "negation" in signals:
            role = EntityRole.NEGATED
        elif "comparison" in signals:
            role = EntityRole.COMPARED
        elif "citation_proximity" in signals and "usage_verb" not in signals:
            role = EntityRole.REFERENCED
        elif section_w <= 0.30 and "usage_verb" not in signals:
            role = EntityRole.REFERENCED
        elif combined >= self.min_used_confidence:
            role = EntityRole.USED
        else:
            role = EntityRole.AMBIGUOUS

        return role, combined, signals

    # ------------------------------------------------------------------
    # Stage 4: Document-level consolidation
    # ------------------------------------------------------------------

    def consolidate_roles(self,
                          classified: List[ClassifiedExtraction]) -> List[ClassifiedExtraction]:
        """Consolidate roles at document level.

        A single USED mention in Methods outweighs multiple REFERENCED
        mentions elsewhere.
        """
        # Group by canonical form
        groups: Dict[str, List[ClassifiedExtraction]] = {}
        for ext in classified:
            key = f"{ext.label}:{ext.canonical.lower()}"
            groups.setdefault(key, []).append(ext)

        consolidated: List[ClassifiedExtraction] = []

        for key, group in groups.items():
            # Find best role across all mentions
            has_used = any(
                e.role == EntityRole.USED for e in group
            )
            has_negated = any(
                e.role == EntityRole.NEGATED for e in group
            )
            has_methods_mention = any(
                e.section in ("methods", "materials", "materials_and_methods")
                for e in group
            )

            # Pick the best representative
            best = max(group, key=lambda e: (
                e.role == EntityRole.USED,
                e.section in ("methods", "materials"),
                e.role_confidence,
            ))

            # Override role based on consolidation
            if has_negated and not has_used:
                best.role = EntityRole.NEGATED
            elif has_used or has_methods_mention:
                best.role = EntityRole.USED
                # Boost confidence if mentioned in Methods
                best.role_confidence = max(best.role_confidence, 0.85)

            consolidated.append(best)

        return consolidated

    # ------------------------------------------------------------------
    # End-to-end classification
    # ------------------------------------------------------------------

    def classify_extractions(self, extractions: list,
                             section_texts: Dict[str, str]) -> List[ClassifiedExtraction]:
        """Classify a list of Extraction objects from the pipeline.

        Parameters
        ----------
        extractions : list of Extraction
            Extractions from the orchestrator.
        section_texts : dict
            Mapping of section_type -> full text (for signal detection).

        Returns
        -------
        list of ClassifiedExtraction
        """
        classified: List[ClassifiedExtraction] = []

        for ext in extractions:
            section = ext.section or "full_text"
            text = section_texts.get(section, "")

            role, confidence, signals = self.classify_extraction(
                text=text,
                entity_text=ext.text,
                entity_start=max(0, ext.start),
                entity_end=max(0, ext.end),
                section=section,
                base_confidence=ext.confidence,
            )

            classified.append(ClassifiedExtraction(
                text=ext.text,
                label=ext.label,
                canonical=ext.canonical(),
                section=section,
                confidence=ext.confidence,
                source_agent=ext.source_agent,
                role=role,
                role_confidence=confidence,
                role_signals=signals,
                metadata=ext.metadata,
            ))

        # Stage 4: document-level consolidation
        return self.consolidate_roles(classified)

    def filter_used_entities(self,
                             classified: List[ClassifiedExtraction]) -> List[ClassifiedExtraction]:
        """Filter to only entities classified as USED with sufficient confidence.

        Returns entities above auto_tag_threshold as confirmed,
        plus entities between review_threshold and auto_tag_threshold
        (marked with needs_review=True in metadata).
        """
        result: List[ClassifiedExtraction] = []
        for ext in classified:
            if ext.role == EntityRole.USED:
                if ext.role_confidence >= self.auto_tag_threshold:
                    result.append(ext)
                elif ext.role_confidence >= self.review_threshold:
                    ext.metadata["needs_review"] = True
                    result.append(ext)
        return result

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    def validate_tagging_distribution(self,
                                       classified: List[ClassifiedExtraction]) -> Dict[str, Any]:
        """Check for over-tagging by analyzing section distribution of USED tags.

        Expected distribution: ~60-70% from Methods, ~15-20% from Results,
        ~5-10% from Abstracts.

        Returns
        -------
        dict with keys: section_distribution, over_tagging_warning, stats
        """
        used = [e for e in classified if e.role == EntityRole.USED]
        if not used:
            return {
                "section_distribution": {},
                "over_tagging_warning": False,
                "stats": {"total_used": 0},
            }

        section_counts: Dict[str, int] = {}
        for ext in used:
            sec = ext.section or "unknown"
            section_counts[sec] = section_counts.get(sec, 0) + 1

        total = len(used)
        distribution = {
            sec: round(count / total, 3)
            for sec, count in section_counts.items()
        }

        # Check for over-tagging: >30% of USED from intro/discussion
        intro_discussion_pct = (
            section_counts.get("introduction", 0)
            + section_counts.get("discussion", 0)
        ) / total

        methods_pct = (
            section_counts.get("methods", 0)
            + section_counts.get("materials", 0)
        ) / total

        over_tagging = intro_discussion_pct > 0.30
        if over_tagging:
            logger.warning(
                "Possible over-tagging: %.1f%% of USED tags from "
                "Introduction/Discussion (expected <30%%)",
                intro_discussion_pct * 100,
            )

        return {
            "section_distribution": distribution,
            "over_tagging_warning": over_tagging,
            "stats": {
                "total_used": total,
                "methods_pct": round(methods_pct, 3),
                "intro_discussion_pct": round(intro_discussion_pct, 3),
                "total_classified": len(classified),
                "role_counts": {
                    role.value: sum(1 for e in classified if e.role == role)
                    for role in EntityRole
                },
            },
        }
