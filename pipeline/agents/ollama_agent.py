"""
Ollama-based verification agent for Methods section cross-checking.

Connects to a local Ollama instance (default: http://localhost:11434) to
verify and supplement the regex-extracted tags by having a local LLM read
the actual Methods section text.

Two modes:
  1. VERIFY:  Check existing tags — flag false positives, confirm true positives
  2. EXTRACT: Find entities the regex agents missed

The agent uses constrained output (JSON mode) and validates all LLM-suggested
tags against the MASTER_TAG_DICTIONARY before accepting them.

Graceful degradation: if Ollama is not running or the model isn't available,
the agent silently returns empty results — it never blocks the pipeline.

Usage:
    agent = OllamaVerificationAgent(model="llama3.1")
    result = agent.verify_and_extract(paper_data, regex_results)

Configuration via environment or .env:
    OLLAMA_URL=http://localhost:11434
    OLLAMA_MODEL=llama3.1
"""

import json
import logging
import os
import time
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)

try:
    import requests as _requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# Project root for loading .env and tag dictionary
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)
)))


def _load_env_key(name: str) -> str:
    """Load a key from environment or .env file."""
    val = os.environ.get(name)
    if val:
        return val
    env_path = os.path.join(_PROJECT_ROOT, ".env")
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith(f"{name}="):
                    return line.split("=", 1)[1].strip().strip("'\"")
    return ""


def _load_valid_tags() -> Dict[str, List[str]]:
    """Load valid tag values from MASTER_TAG_DICTIONARY.json."""
    dict_path = os.path.join(_PROJECT_ROOT, "MASTER_TAG_DICTIONARY.json")
    if not os.path.exists(dict_path):
        return {}
    try:
        with open(dict_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        valid: Dict[str, List[str]] = {}
        for category, info in data.items():
            if category.startswith("_"):
                continue
            values = info.get("all_valid_values") or info.get("sample_values") or []
            if values:
                valid[category] = values
        return valid
    except Exception:
        return {}


class OllamaVerificationAgent:
    """Verify and supplement regex-extracted tags using a local Ollama LLM.

    Parameters
    ----------
    model : str
        Ollama model name (e.g., "llama3.1", "mistral", "gemma2").
    ollama_url : str
        Base URL for the Ollama API.
    timeout : float
        Request timeout in seconds (LLM inference can be slow).
    temperature : float
        Sampling temperature (lower = more deterministic).
    """

    name = "ollama_verification"

    def __init__(
        self,
        model: str = None,
        ollama_url: str = None,
        timeout: float = 120.0,
        temperature: float = 0.1,
    ):
        self.model = model or _load_env_key("OLLAMA_MODEL") or "llama3.1"
        self.ollama_url = (
            ollama_url
            or _load_env_key("OLLAMA_URL")
            or "http://localhost:11434"
        )
        self.timeout = timeout
        self.temperature = temperature

        self._valid_tags = _load_valid_tags()
        self._available: Optional[bool] = None  # lazy check
        self._last_call = 0.0
        self._delay = 0.5  # min delay between calls

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def is_available(self) -> bool:
        """Check if Ollama is running and the model is available."""
        if self._available is not None:
            return self._available
        if not HAS_REQUESTS:
            self._available = False
            return False
        try:
            resp = _requests.get(
                f"{self.ollama_url}/api/tags",
                timeout=5,
            )
            if resp.status_code != 200:
                self._available = False
                return False
            models = resp.json().get("models", [])
            model_names = [m.get("name", "").split(":")[0] for m in models]
            self._available = self.model.split(":")[0] in model_names
            if not self._available:
                logger.info(
                    "Ollama model '%s' not found. Available: %s",
                    self.model, ", ".join(model_names) or "(none)",
                )
            return self._available
        except Exception:
            self._available = False
            return False

    def verify_and_extract(
        self,
        paper: Dict[str, Any],
        regex_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Verify regex results and extract missing entities.

        Parameters
        ----------
        paper : dict
            The paper dict (must have title, abstract, methods or full_text).
        regex_results : dict
            Output from the orchestrator's extraction pass.

        Returns
        -------
        dict with keys:
            "verified"  — tags confirmed by LLM (subset of regex_results)
            "removed"   — tags the LLM flagged as false positives
            "added"     — new tags the LLM found that regex missed
            "raw"       — raw LLM response for debugging
        """
        if not self.is_available():
            return {"verified": {}, "removed": {}, "added": {}, "raw": ""}

        methods = (
            paper.get("methods", "")
            or paper.get("full_text", "")
            or paper.get("abstract", "")
        )
        if not methods or len(methods) < 50:
            return {"verified": {}, "removed": {}, "added": {}, "raw": ""}

        title = paper.get("title", "")

        # Build prompt
        prompt = self._build_prompt(title, methods, regex_results)

        # Call Ollama
        response = self._call_ollama(prompt)
        if not response:
            return {"verified": {}, "removed": {}, "added": {}, "raw": ""}

        # Parse and validate
        return self._parse_response(response, regex_results)

    # ------------------------------------------------------------------
    # Prompt construction
    # ------------------------------------------------------------------

    def _build_prompt(
        self,
        title: str,
        methods: str,
        regex_results: Dict[str, Any],
    ) -> str:
        """Build the verification prompt for the LLM."""

        # Collect existing tags
        existing = {}
        for key in [
            "microscopy_techniques", "microscope_brands", "fluorophores",
            "organisms", "cell_lines", "sample_preparation",
            "image_analysis_software",
        ]:
            vals = regex_results.get(key, [])
            if vals and isinstance(vals, list):
                existing[key] = vals

        # Build valid tag lists (truncated to fit context)
        valid_lists = ""
        for key in [
            "microscopy_techniques", "microscope_brands", "fluorophores",
            "organisms", "cell_lines", "sample_preparation",
            "image_analysis_software",
        ]:
            tags = self._valid_tags.get(key, [])
            if tags:
                # Truncate to keep prompt reasonable
                display = tags[:50]
                valid_lists += f"\nVALID {key.upper()}: {', '.join(display)}"
                if len(tags) > 50:
                    valid_lists += f" ... ({len(tags)} total)"

        # Truncate methods to avoid exceeding context
        methods_text = methods[:4000]
        if len(methods) > 4000:
            methods_text += "\n[... truncated ...]"

        return f"""You are a microscopy expert verifying metadata extracted from a scientific paper.

TASK: Read the Methods section below and verify/correct the extracted tags.

RULES:
1. ONLY include tags for things ACTUALLY USED in THIS paper's experiments
2. DO NOT tag things merely cited, compared against, or mentioned in passing
3. "unlike STED, we used confocal" → tag Confocal, NOT STED
4. "based on previous two-photon work, here we developed..." → only tag the NEW method
5. Only use tags from the VALID TAGS lists below — do NOT invent new tags
6. When uncertain, leave a tag OUT

VALID TAGS (use these exact values only):
{valid_lists}

PAPER TITLE: {title}

METHODS SECTION:
{methods_text}

EXISTING REGEX-EXTRACTED TAGS:
{json.dumps(existing, indent=2)}

INSTRUCTIONS:
1. Check each existing tag — is it actually used in this paper's Methods?
2. If a tag is a false positive (mentioned but not used), put it in "remove"
3. If something was missed by regex, put it in "add" (ONLY from valid tags)
4. Put confirmed tags in "keep"

RESPOND WITH ONLY VALID JSON (no markdown, no explanation):
{{
  "keep": {{
    "microscopy_techniques": ["tag1"],
    "fluorophores": ["tag1", "tag2"],
    "organisms": ["tag1"]
  }},
  "remove": {{
    "microscopy_techniques": ["false_positive_tag"]
  }},
  "add": {{
    "fluorophores": ["missed_tag"],
    "organisms": ["missed_organism"]
  }}
}}

Use empty objects {{}} for sections with no changes. Only include categories that apply."""

    # ------------------------------------------------------------------
    # Ollama API call
    # ------------------------------------------------------------------

    def _call_ollama(self, prompt: str) -> Optional[str]:
        """Call Ollama generate API and return the response text."""
        elapsed = time.time() - self._last_call
        if elapsed < self._delay:
            time.sleep(self._delay - elapsed)

        try:
            resp = _requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": self.temperature,
                        "num_predict": 2048,
                    },
                    "format": "json",
                },
                timeout=self.timeout,
            )
            self._last_call = time.time()

            if resp.status_code != 200:
                logger.warning(
                    "Ollama returned %d: %s", resp.status_code, resp.text[:200]
                )
                return None

            data = resp.json()
            return data.get("response", "")

        except _requests.exceptions.Timeout:
            logger.warning("Ollama timed out after %.0fs", self.timeout)
            return None
        except _requests.exceptions.ConnectionError:
            logger.debug("Ollama not reachable at %s", self.ollama_url)
            self._available = False
            return None
        except Exception as exc:
            logger.warning("Ollama error: %s", exc)
            return None

    # ------------------------------------------------------------------
    # Response parsing and validation
    # ------------------------------------------------------------------

    def _parse_response(
        self,
        response: str,
        regex_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Parse the LLM JSON response and validate against tag dictionary."""
        result = {
            "verified": {},
            "removed": {},
            "added": {},
            "raw": response,
        }

        # Strip markdown fences if present
        text = response.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            lines = [ln for ln in lines if not ln.strip().startswith("```")]
            text = "\n".join(lines)

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            logger.debug("Ollama response was not valid JSON")
            return result

        if not isinstance(parsed, dict):
            return result

        # Process "keep" — tags the LLM confirmed
        keep = parsed.get("keep", {})
        if isinstance(keep, dict):
            for category, tags in keep.items():
                if isinstance(tags, list):
                    validated = self._validate_tags(category, tags)
                    if validated:
                        result["verified"][category] = validated

        # Process "remove" — false positives
        remove = parsed.get("remove", {})
        if isinstance(remove, dict):
            for category, tags in remove.items():
                if isinstance(tags, list):
                    # Only allow removal of tags that were actually extracted
                    existing = set(regex_results.get(category, []))
                    to_remove = [t for t in tags if t in existing]
                    if to_remove:
                        result["removed"][category] = to_remove

        # Process "add" — missed entities
        add = parsed.get("add", {})
        if isinstance(add, dict):
            for category, tags in add.items():
                if isinstance(tags, list):
                    validated = self._validate_tags(category, tags)
                    # Only add tags not already in regex results
                    existing_lower = {
                        t.lower() for t in regex_results.get(category, [])
                    }
                    new_tags = [
                        t for t in validated
                        if t.lower() not in existing_lower
                    ]
                    if new_tags:
                        result["added"][category] = new_tags

        return result

    def _validate_tags(self, category: str, tags: List[str]) -> List[str]:
        """Validate tags against the master dictionary."""
        valid = self._valid_tags.get(category)
        if valid is None:
            return tags  # unknown category — pass through

        valid_set = set(valid)
        valid_lower = {v.lower(): v for v in valid}

        result = []
        for tag in tags:
            if tag in valid_set:
                result.append(tag)
            elif tag.lower() in valid_lower:
                result.append(valid_lower[tag.lower()])
            # else: silently drop — LLM hallucinated a tag
        return result

    # ------------------------------------------------------------------
    # Convenience: apply results to a paper dict
    # ------------------------------------------------------------------

    def apply_results(
        self,
        paper_results: Dict[str, Any],
        llm_results: Dict[str, Any],
        *,
        auto_remove: bool = False,
    ) -> Dict[str, Any]:
        """Apply LLM verification results to the paper's extracted tags.

        Parameters
        ----------
        paper_results : dict
            The orchestrator output dict to modify.
        llm_results : dict
            Output from verify_and_extract().
        auto_remove : bool
            If True, automatically remove false positives. If False (default),
            only add the "llm_flagged" metadata — let the user decide.

        Returns
        -------
        dict — the modified paper_results.
        """
        # Add new entities the LLM found
        for category, tags in llm_results.get("added", {}).items():
            existing = paper_results.get(category, [])
            if not isinstance(existing, list):
                continue
            existing_lower = {t.lower() for t in existing}
            for tag in tags:
                if tag.lower() not in existing_lower:
                    existing.append(tag)
                    existing_lower.add(tag.lower())
            paper_results[category] = existing

        # Handle removals
        if auto_remove:
            for category, tags in llm_results.get("removed", {}).items():
                existing = paper_results.get(category, [])
                if not isinstance(existing, list):
                    continue
                remove_lower = {t.lower() for t in tags}
                paper_results[category] = [
                    t for t in existing if t.lower() not in remove_lower
                ]
        else:
            # Just flag — don't remove
            flagged = llm_results.get("removed", {})
            if flagged:
                paper_results["_llm_flagged_false_positives"] = flagged

        # Store verification metadata
        paper_results["_llm_verified"] = bool(llm_results.get("verified"))
        paper_results["_llm_model"] = self.model

        return paper_results
