"""
Base agent interface and shared data structures for the extraction pipeline.

Every specialized agent inherits from BaseAgent and implements analyze().
Extractions carry confidence scores and provenance so the orchestrator can
resolve conflicts when multiple agents tag the same span.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Extraction:
    """A single entity extraction produced by an agent."""
    text: str
    label: str
    start: int = -1
    end: int = -1
    confidence: float = 1.0
    source_agent: str = ""
    section: str = ""
    metadata: Dict = field(default_factory=dict)

    def canonical(self) -> str:
        """Return the canonical (normalized) form stored in metadata, or raw text."""
        return self.metadata.get("canonical", self.text)


class BaseAgent(ABC):
    """Abstract base for all extraction agents.

    Subclasses must implement ``analyze`` which receives raw text and an
    optional section hint (e.g. ``"methods"``, ``"abstract"``).
    """

    name: str = "base"

    @abstractmethod
    def analyze(self, text: str, section: str = None) -> List[Extraction]:
        """Extract entities from *text*.

        Parameters
        ----------
        text : str
            Raw text (may contain multiple sentences/paragraphs).
        section : str, optional
            Section of the paper the text came from (``"title"``,
            ``"abstract"``, ``"methods"``, ``"results"``, etc.).

        Returns
        -------
        list[Extraction]
        """

    # ------------------------------------------------------------------
    # Convenience helpers available to every agent
    # ------------------------------------------------------------------

    @staticmethod
    def _deduplicate(extractions: List[Extraction]) -> List[Extraction]:
        """Remove duplicate canonical forms, keeping highest-confidence."""
        seen: Dict[str, Extraction] = {}
        for ext in extractions:
            key = (ext.label, ext.canonical())
            if key not in seen or ext.confidence > seen[key].confidence:
                seen[key] = ext
        return list(seen.values())
