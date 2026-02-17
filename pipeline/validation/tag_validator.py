"""
Tag validation against MASTER_TAG_DICTIONARY.json.

Ensures all extracted values are valid members of their respective
taxonomy before export.  Also provides fuzzy matching for near-misses.
"""

import json
import logging
import os
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class TagValidator:
    """Validate extraction results against the master tag dictionary."""

    def __init__(self, dictionary_path: str = None):
        if dictionary_path is None:
            # Default: MASTER_TAG_DICTIONARY.json next to the repo root
            dictionary_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(
                    os.path.abspath(__file__)
                ))),
                "MASTER_TAG_DICTIONARY.json",
            )
        self.valid_values: Dict[str, Set[str]] = {}
        self._load(dictionary_path)

    def _load(self, path: str):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            logger.warning("Could not load tag dictionary from %s: %s", path, exc)
            return

        for category, info in data.items():
            if category.startswith("_"):
                continue
            values = info.get("all_valid_values") or info.get("sample_values") or []
            if values:
                self.valid_values[category] = set(values)

        # Also handle repository types and protocol sources
        repos = data.get("repositories", {})
        if "all_valid_types" in repos:
            self.valid_values["repository_types"] = set(repos["all_valid_types"])
        protos = data.get("protocols", {})
        if "all_valid_sources" in protos:
            self.valid_values["protocol_sources"] = set(protos["all_valid_sources"])

        logger.info(
            "Loaded tag dictionary: %d categories, %d total values",
            len(self.valid_values),
            sum(len(v) for v in self.valid_values.values()),
        )

    # ------------------------------------------------------------------
    def is_valid(self, category: str, value: str) -> bool:
        """Check if *value* is a valid member of *category*."""
        valid = self.valid_values.get(category)
        if valid is None:
            return True  # unknown category → pass through
        return value in valid

    def filter_valid(self, category: str, values: List[str]) -> List[str]:
        """Return only valid values for the given category."""
        valid = self.valid_values.get(category)
        if valid is None:
            return values
        result = []
        for v in values:
            if v in valid:
                result.append(v)
            else:
                # Try case-insensitive match
                match = self._case_insensitive_match(v, valid)
                if match:
                    result.append(match)
                else:
                    logger.debug("Dropping invalid %s value: %s", category, v)
        return result

    def suggest(self, category: str, value: str) -> Optional[str]:
        """Suggest the closest valid value (simple case-insensitive match)."""
        valid = self.valid_values.get(category)
        if valid is None:
            return None
        return self._case_insensitive_match(value, valid)

    # ------------------------------------------------------------------
    @staticmethod
    def _case_insensitive_match(value: str, valid: Set[str]) -> Optional[str]:
        lower = value.lower()
        for v in valid:
            if v.lower() == lower:
                return v
        return None
