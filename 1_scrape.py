#!/usr/bin/env python3
"""
Step 1 — Scrape papers from PubMed / PMC into the SQLite database,
then acquire full text for papers that don't have it yet.

Phase A (scraper):
    Runs the existing scraper (backup/microhub_scraper.py) to collect papers
    from PubMed/PMC and store them in SQLite with regex-extracted tags.

Phase B (full-text acquisition — runs automatically after scraping):
    For papers missing full_text: tries three-tier waterfall
    (Europe PMC → Unpaywall+GROBID → abstract) or SciHub fallback.
    Saves full_text + methods back to DB.
    NO agent enrichment, NO PubTator, NO normalization.
    Tagging happens in step 3 (3_clean.py).

Usage:
    python 1_scrape.py                       # scrape + acquire full text
    python 1_scrape.py --limit 200           # scrape 200 then acquire text
    python 1_scrape.py --skip-fulltext       # scrape only (no full-text fetch)
    python 1_scrape.py --fulltext-only       # skip scrape, only fetch full text
    python 1_scrape.py --fulltext-limit 500  # only fetch text for 500 papers
    python 1_scrape.py --three-tier          # use Europe PMC → Unpaywall+GROBID → abstract waterfall

Scraper flags (forwarded to backup/microhub_scraper.py):
    --db PATH               Database path (default: microhub.db)
    --email EMAIL            Email for NCBI API
    --ncbi-api-key KEY       NCBI API key (or set NCBI_API_KEY env var)
                             Increases PubMed rate limit from 3 to 10 req/sec
                             Get one free: https://www.ncbi.nlm.nih.gov/account/settings/
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

Note: Agent enrichment flags (--ollama, --no-pubtator, --no-role-classifier)
have moved to 3_clean.py, which is now the sole tagger.
"""

import argparse
import logging
import os
import sqlite3
import subprocess
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


# ======================================================================
# Phase B — Full-text acquisition
# ======================================================================

def acquire_fulltext(
    db_path: str,
    limit: int = None,
    use_three_tier_waterfall: bool = False,
) -> int:
    """Acquire full text for papers that don't have it yet.

    This does NOT run any tagging agents. Tagging happens in step 3.

    Parameters
    ----------
    db_path : str
        Path to the SQLite database.
    limit : int, optional
        Maximum number of papers to process.
    use_three_tier_waterfall : bool
        Use Europe PMC -> Unpaywall+GROBID -> abstract waterfall.

    Returns
    -------
    int
        Number of papers where full text was acquired.
    """
    conn = sqlite3.connect(db_path, timeout=120.0)
    conn.row_factory = sqlite3.Row

    # Papers without full text that have a DOI
    query = """
        SELECT id, pmid, doi, title
        FROM papers
        WHERE (full_text IS NULL OR full_text = '')
          AND doi IS NOT NULL AND doi != ''
        ORDER BY priority_score DESC, year DESC
    """
    if limit:
        query += f" LIMIT {limit}"

    rows = conn.execute(query).fetchall()
    total = len(rows)

    if total == 0:
        logger.info("All papers already have full text (or no DOIs to fetch).")
        conn.close()
        return 0

    logger.info("")
    logger.info("=" * 60)
    logger.info("PHASE B — FULL-TEXT ACQUISITION")
    logger.info("=" * 60)
    logger.info("Papers needing full text: %d", total)
    logger.info("Strategy: %s",
                "three-tier waterfall" if use_three_tier_waterfall
                else "SciHub fallback")
    logger.info("")

    acquired = 0
    errors = 0

    for i, row in enumerate(rows):
        paper = dict(row)
        doi = paper.get("doi", "")
        pmid = paper.get("pmid", "?")

        try:
            if use_three_tier_waterfall:
                from pipeline.parsing.section_extractor import three_tier_waterfall
                sections = three_tier_waterfall(paper)
                if sections and sections.full_text:
                    updates_sql = "UPDATE papers SET full_text = ?"
                    params_sql = [sections.full_text]
                    if sections.methods:
                        updates_sql += ", methods = ?"
                        params_sql.append(sections.methods)
                    updates_sql += " WHERE id = ?"
                    params_sql.append(paper["id"])
                    conn.execute(updates_sql, params_sql)
                    conn.commit()
                    acquired += 1
                    logger.info(
                        "  [%d/%d] PMID %s: full text acquired (%d chars, source=%s)",
                        i + 1, total, pmid, len(sections.full_text),
                        sections.source or "unknown",
                    )
            else:
                from pipeline.parsing.scihub_fetcher import fetch_fulltext_via_scihub
                scihub_text = fetch_fulltext_via_scihub(doi)
                if scihub_text:
                    conn.execute(
                        "UPDATE papers SET full_text = ? WHERE id = ?",
                        (scihub_text, paper["id"]),
                    )
                    conn.commit()
                    acquired += 1
                    logger.info(
                        "  [%d/%d] PMID %s: full text via SciHub (%d chars)",
                        i + 1, total, pmid, len(scihub_text),
                    )

        except Exception as exc:
            errors += 1
            logger.debug("Error fetching full text for PMID %s: %s", pmid, exc)
            continue

        if (i + 1) % 100 == 0:
            logger.info("  Progress: %d / %d papers processed...", i + 1, total)

    conn.close()

    logger.info("")
    logger.info("=" * 60)
    logger.info("PHASE B COMPLETE: %d papers acquired full text (%d errors)",
                acquired, errors)
    logger.info("=" * 60)

    return acquired


# ======================================================================
# Main
# ======================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Step 1 — Scrape + Full-Text Acquisition",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,
    )
    parser.add_argument("--skip-fulltext", action="store_true",
                        help="Skip full-text acquisition after scraping")
    parser.add_argument("--fulltext-only", action="store_true",
                        help="Skip scraping, only acquire full text for DB papers")
    parser.add_argument("--fulltext-limit", type=int, default=None,
                        help="Max papers to fetch full text for (default: all)")
    parser.add_argument("--three-tier", action="store_true",
                        help="Use three-tier waterfall (Europe PMC -> Unpaywall+GROBID -> abstract)")
    parser.add_argument("--db", default="microhub.db",
                        help="Database path (default: microhub.db)")

    known, remaining = parser.parse_known_args()

    db_path = known.db
    if not os.path.isabs(db_path):
        db_path = os.path.join(SCRIPT_DIR, db_path)

    # ---- Phase A: Run the scraper (unless --fulltext-only) ----
    if not known.fulltext_only:
        scraper_path = os.path.join(SCRIPT_DIR, "backup", "microhub_scraper.py")
        if not os.path.exists(scraper_path):
            logger.error("Scraper not found at: %s", scraper_path)
            sys.exit(1)

        scraper_args = ["--db", db_path] + remaining
        cmd = [sys.executable, scraper_path] + scraper_args

        logger.info("=" * 60)
        logger.info("STEP 1 — PHASE A: SCRAPE")
        logger.info("=" * 60)
        logger.info("Scraper: %s", scraper_path)
        logger.info("Args:    %s", " ".join(scraper_args) or "(defaults)")
        logger.info("")

        result = subprocess.run(cmd)
        if result.returncode != 0:
            logger.error("Scraper exited with code %d", result.returncode)

    # ---- Phase B: Full-text acquisition (unless --skip-fulltext) ----
    if not known.skip_fulltext:
        if not os.path.exists(db_path):
            logger.error("Database not found at %s — nothing to fetch.", db_path)
            sys.exit(1)

        acquire_fulltext(
            db_path=db_path,
            limit=known.fulltext_limit,
            use_three_tier_waterfall=known.three_tier,
        )

    logger.info("")
    logger.info("Done. Next step: python 2_export.py")


if __name__ == "__main__":
    main()
