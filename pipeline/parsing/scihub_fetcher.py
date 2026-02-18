"""
SciHub full-text fetcher — last-resort fallback for papers with DOI but no
available full text from PMC.

The retrieved text is used ONLY for tag extraction.  It is NOT stored,
displayed, or linked anywhere in the output.

If SciHub is unreachable or the paper is not available, this silently
returns None so the pipeline continues with title+abstract extraction.
"""

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# SciHub mirrors (tried in order)
_SCIHUB_URLS = [
    "https://sci-hub.se",
    "https://sci-hub.st",
    "https://sci-hub.ru",
]

_TIMEOUT = 15  # seconds


def fetch_fulltext_via_scihub(doi: str) -> Optional[str]:
    """Attempt to retrieve full-text content for a DOI via SciHub.

    Returns plain text extracted from the HTML page, or None if
    unavailable.  This function is intentionally best-effort and
    will never raise an exception.

    Parameters
    ----------
    doi : str
        The DOI of the paper (e.g. "10.1038/s41586-023-06789-5").

    Returns
    -------
    str or None
        Plain text of the paper body, or None if not retrievable.
    """
    if not HAS_REQUESTS or not doi:
        return None

    for base_url in _SCIHUB_URLS:
        try:
            url = f"{base_url}/{doi}"
            resp = requests.get(url, timeout=_TIMEOUT, allow_redirects=True)
            if resp.status_code != 200:
                continue

            # Extract text from HTML (simple approach — strip tags)
            text = _html_to_text(resp.text)
            if text and len(text) > 500:
                logger.debug(
                    "SciHub: retrieved %d chars for DOI %s from %s",
                    len(text), doi, base_url,
                )
                return text

        except Exception:
            continue

    logger.debug("SciHub: no full text available for DOI %s", doi)
    return None


def _html_to_text(html: str) -> str:
    """Very basic HTML-to-text conversion for extracting paper content."""
    # Remove script and style elements
    html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.S | re.I)
    html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.S | re.I)
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", " ", html)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    # Decode common HTML entities
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&nbsp;", " ").replace("&quot;", '"')
    return text
