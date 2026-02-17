"""
Pass 2 — GitHub Health Agent.

Fetches repository metadata from the GitHub API for all extracted GitHub URLs.
Delegates to the existing enrichment logic but wraps it as a proper agent.

This agent:
  - Checks if repos exist (flags 404s)
  - Fetches stars, forks, last commit, license, archived status
  - Computes health scores
  - Detects dead/archived repos

Designed to run during Pass 2 (post-scraping validation).
"""

import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Re-use the existing enrichment logic rather than duplicating it
try:
    from ..enrichment import Enricher, compute_github_health_score
    HAS_ENRICHER = True
except ImportError:
    HAS_ENRICHER = False


class GitHubHealthAgent:
    """Validate and enrich GitHub repository metadata."""

    name = "github_health"

    def __init__(self, github_token: str = None):
        self._token = github_token
        self._enricher = None
        if HAS_ENRICHER:
            self._enricher = Enricher()
            if github_token:
                self._enricher.github_token = github_token

    def validate(self, paper: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch/update GitHub metadata for all github_tools entries.

        Mutates paper in-place.  Adds health_score, exists, is_archived
        to each github_tools entry.
        """
        if not self._enricher:
            return paper

        tools = paper.get("github_tools")
        if not tools or not isinstance(tools, list):
            return paper

        # Use enricher's existing GitHub metadata fetcher
        self._enricher._enrich_github_tools(paper)

        # Also flag dead repos explicitly
        for tool in paper.get("github_tools", []):
            if isinstance(tool, dict):
                if tool.get("exists") is False:
                    tool["validation_status"] = "dead"
                elif tool.get("is_archived"):
                    tool["validation_status"] = "archived"
                elif tool.get("health_score", 0) > 0:
                    tool["validation_status"] = "active"

        return paper
