"""Tests for the role classifier (over-tagging prevention)."""

import pytest

from pipeline.role_classifier import (
    EntityRole,
    RoleClassifier,
    ClassifiedExtraction,
    SECTION_USAGE_WEIGHTS,
)
from pipeline.agents.base_agent import Extraction


class TestSectionWeights:
    """Test section-aware weighting."""

    def test_methods_has_highest_weight(self):
        classifier = RoleClassifier()
        assert classifier.section_weight("methods") == 1.0
        assert classifier.section_weight("materials") == 1.0

    def test_discussion_has_low_weight(self):
        classifier = RoleClassifier()
        assert classifier.section_weight("discussion") == 0.30

    def test_introduction_has_low_weight(self):
        classifier = RoleClassifier()
        assert classifier.section_weight("introduction") == 0.20

    def test_results_has_high_weight(self):
        classifier = RoleClassifier()
        assert classifier.section_weight("results") == 0.85

    def test_references_excluded(self):
        classifier = RoleClassifier()
        assert classifier.section_weight("references") == 0.0

    def test_unknown_section_gets_default(self):
        classifier = RoleClassifier()
        weight = classifier.section_weight("unknown_section")
        assert 0.0 < weight < 1.0


class TestLinguisticSignals:
    """Test linguistic signal detection."""

    def setup_method(self):
        self.classifier = RoleClassifier()

    def test_usage_verb_detected(self):
        text = "We used a Leica SP8 STED microscope for all imaging experiments."
        signals, adj = self.classifier.detect_signals(text, "Leica SP8", 10, 19)
        assert "usage_verb" in signals
        assert adj > 0

    def test_passive_usage_verb_detected(self):
        text = "Images were acquired using a Zeiss LSM 880 confocal microscope."
        signals, adj = self.classifier.detect_signals(text, "Zeiss LSM 880", 30, 43)
        assert "usage_verb" in signals

    def test_reference_verb_detected(self):
        text = "Confocal microscopy is commonly used for live cell imaging."
        signals, adj = self.classifier.detect_signals(text, "Confocal microscopy", 0, 20)
        assert "reference_verb" in signals
        assert adj < 0

    def test_citation_proximity_detected(self):
        text = "STED microscopy was developed by Hell et al. [1] in 1994."
        signals, adj = self.classifier.detect_signals(text, "STED microscopy", 0, 15)
        assert "citation_proximity" in signals
        assert adj < 0

    def test_author_year_citation_detected(self):
        text = "Two-photon microscopy (Denk et al., 1990) enables deep tissue imaging."
        signals, adj = self.classifier.detect_signals(text, "Two-photon microscopy", 0, 21)
        assert "citation_proximity" in signals

    def test_negation_detected(self):
        text = "We did not use electron microscopy in this study."
        signals, adj = self.classifier.detect_signals(text, "electron microscopy", 19, 38)
        assert "negation" in signals
        assert adj < -0.3

    def test_comparison_detected(self):
        text = "Unlike confocal microscopy, STED provides superior resolution."
        signals, adj = self.classifier.detect_signals(text, "confocal microscopy", 7, 26)
        assert "comparison" in signals
        assert adj < 0

    def test_no_signals_plain_mention(self):
        text = "STED microscopy reveals nanoscale details."
        signals, adj = self.classifier.detect_signals(text, "STED microscopy", 0, 15)
        # No strong signals in this neutral sentence
        assert "negation" not in signals
        assert "comparison" not in signals


class TestRoleClassification:
    """Test entity role classification."""

    def setup_method(self):
        self.classifier = RoleClassifier()

    def test_methods_usage_classified_as_used(self):
        text = "We used a Leica SP8 STED microscope."
        role, conf, signals = self.classifier.classify_extraction(
            text, "Leica SP8", 10, 19, "methods", 0.95
        )
        assert role == EntityRole.USED

    def test_discussion_reference_classified(self):
        text = "Confocal microscopy is commonly used for such experiments."
        role, conf, signals = self.classifier.classify_extraction(
            text, "Confocal microscopy", 0, 20, "discussion", 0.30
        )
        assert role == EntityRole.REFERENCED

    def test_negation_classified(self):
        text = "We did not use electron microscopy in this study."
        role, conf, signals = self.classifier.classify_extraction(
            text, "electron microscopy", 19, 38, "methods", 0.95
        )
        assert role == EntityRole.NEGATED

    def test_comparison_classified(self):
        text = "Unlike confocal microscopy, we chose STED for better resolution."
        role, conf, signals = self.classifier.classify_extraction(
            text, "confocal microscopy", 7, 26, "methods", 0.80
        )
        assert role == EntityRole.COMPARED


class TestDocumentConsolidation:
    """Test document-level role consolidation."""

    def setup_method(self):
        self.classifier = RoleClassifier()

    def test_methods_used_overrides_discussion_reference(self):
        classified = [
            ClassifiedExtraction(
                text="STED", label="TECHNIQUE", canonical="STED",
                section="methods", confidence=0.95,
                source_agent="technique",
                role=EntityRole.USED, role_confidence=0.90,
            ),
            ClassifiedExtraction(
                text="STED", label="TECHNIQUE", canonical="STED",
                section="discussion", confidence=0.30,
                source_agent="technique",
                role=EntityRole.REFERENCED, role_confidence=0.30,
            ),
        ]
        consolidated = self.classifier.consolidate_roles(classified)
        assert len(consolidated) == 1
        assert consolidated[0].role == EntityRole.USED

    def test_negation_without_usage_stays_negated(self):
        classified = [
            ClassifiedExtraction(
                text="EM", label="TECHNIQUE", canonical="Electron Microscopy",
                section="methods", confidence=0.95,
                source_agent="technique",
                role=EntityRole.NEGATED, role_confidence=0.40,
            ),
        ]
        consolidated = self.classifier.consolidate_roles(classified)
        assert len(consolidated) == 1
        assert consolidated[0].role == EntityRole.NEGATED


class TestOverTaggingValidation:
    """Test over-tagging distribution validation."""

    def setup_method(self):
        self.classifier = RoleClassifier()

    def test_healthy_distribution(self):
        classified = (
            [ClassifiedExtraction(
                text=f"tech{i}", label="TECHNIQUE", canonical=f"tech{i}",
                section="methods", confidence=0.95,
                source_agent="technique",
                role=EntityRole.USED, role_confidence=0.90,
            ) for i in range(7)] +
            [ClassifiedExtraction(
                text=f"tech{i}", label="TECHNIQUE", canonical=f"tech{i}",
                section="results", confidence=0.85,
                source_agent="technique",
                role=EntityRole.USED, role_confidence=0.85,
            ) for i in range(7, 9)] +
            [ClassifiedExtraction(
                text="tech9", label="TECHNIQUE", canonical="tech9",
                section="abstract", confidence=0.70,
                source_agent="technique",
                role=EntityRole.USED, role_confidence=0.70,
            )]
        )
        report = self.classifier.validate_tagging_distribution(classified)
        assert report["over_tagging_warning"] is False
        assert report["stats"]["methods_pct"] >= 0.60

    def test_over_tagging_detected(self):
        classified = (
            [ClassifiedExtraction(
                text=f"tech{i}", label="TECHNIQUE", canonical=f"tech{i}",
                section="methods", confidence=0.95,
                source_agent="technique",
                role=EntityRole.USED, role_confidence=0.90,
            ) for i in range(3)] +
            [ClassifiedExtraction(
                text=f"tech{i}", label="TECHNIQUE", canonical=f"tech{i}",
                section="introduction", confidence=0.30,
                source_agent="technique",
                role=EntityRole.USED, role_confidence=0.50,
            ) for i in range(3, 7)] +
            [ClassifiedExtraction(
                text=f"tech{i}", label="TECHNIQUE", canonical=f"tech{i}",
                section="discussion", confidence=0.30,
                source_agent="technique",
                role=EntityRole.USED, role_confidence=0.50,
            ) for i in range(7, 10)]
        )
        report = self.classifier.validate_tagging_distribution(classified)
        assert report["over_tagging_warning"] is True
        assert report["stats"]["intro_discussion_pct"] > 0.30

    def test_empty_extractions(self):
        report = self.classifier.validate_tagging_distribution([])
        assert report["over_tagging_warning"] is False
        assert report["stats"]["total_used"] == 0


class TestFilterUsedEntities:
    """Test filtering to only USED entities."""

    def setup_method(self):
        self.classifier = RoleClassifier()

    def test_filters_to_used_only(self):
        classified = [
            ClassifiedExtraction(
                text="STED", label="TECHNIQUE", canonical="STED",
                section="methods", confidence=0.95,
                source_agent="technique",
                role=EntityRole.USED, role_confidence=0.90,
            ),
            ClassifiedExtraction(
                text="Confocal", label="TECHNIQUE", canonical="Confocal",
                section="introduction", confidence=0.30,
                source_agent="technique",
                role=EntityRole.REFERENCED, role_confidence=0.30,
            ),
            ClassifiedExtraction(
                text="EM", label="TECHNIQUE", canonical="EM",
                section="methods", confidence=0.95,
                source_agent="technique",
                role=EntityRole.NEGATED, role_confidence=0.40,
            ),
        ]
        filtered = self.classifier.filter_used_entities(classified)
        assert len(filtered) == 1
        assert filtered[0].canonical == "STED"

    def test_review_threshold(self):
        classified = [
            ClassifiedExtraction(
                text="SIM", label="TECHNIQUE", canonical="SIM",
                section="abstract", confidence=0.70,
                source_agent="technique",
                role=EntityRole.USED, role_confidence=0.65,
            ),
        ]
        filtered = self.classifier.filter_used_entities(classified)
        assert len(filtered) == 1
        assert filtered[0].metadata.get("needs_review") is True
