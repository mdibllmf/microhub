#!/usr/bin/env python3
"""
Step 1 — Scrape papers from PubMed / PMC into the SQLite database.

This is the *long-running* step that hits external APIs.  Run it on its own
while steps 2-4 work on previously scraped data:

    python 1_scrape.py                   # default: scrape all, no limit
    python 1_scrape.py --limit 200       # scrape up to 200 papers
    python 1_scrape.py --priority-only   # only high-priority sources
    python 1_scrape.py --llm-enrich --llm-api-key sk-...  # Claude Haiku enrichment

Full flag list (forwarded to the scraper):
    --db PATH               Database path (default: microhub.db)
    --email EMAIL            Email for NCBI API
    --limit N                Cap total papers
    --priority-only          Only high-priority sources
    --full-text-only         Only save papers with full text
    --no-citations           Skip citation fetching
    --update-citations       Update citations for existing papers
    --llm-enrich             Enable LLM enrichment (Claude Haiku)
    --llm-api-key KEY        Anthropic API key
    --update-github-tools    Refresh GitHub tool metrics
    --github-token TOKEN     GitHub PAT
    --github-limit N         Max tools to update (default: 100)
"""

import logging
import os
import subprocess
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def main():
    scraper_path = os.path.join(SCRIPT_DIR, "backup", "microhub_scraper.py")

    if not os.path.exists(scraper_path):
        logger.error("Scraper not found at: %s", scraper_path)
        sys.exit(1)

    # Forward every CLI argument straight to the scraper
    cmd = [sys.executable, scraper_path] + sys.argv[1:]

    logger.info("=" * 60)
    logger.info("STEP 1 — SCRAPE (runs independently)")
    logger.info("=" * 60)
    logger.info("Scraper: %s", scraper_path)
    logger.info("Args:    %s", " ".join(sys.argv[1:]) or "(defaults)")
    logger.info("")

    result = subprocess.run(cmd)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
