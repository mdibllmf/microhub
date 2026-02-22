#!/usr/bin/env python3
"""
Step 1 — Scrape papers from PubMed / PMC into SQLite,
then acquire missing full text.

Phase A (scraper):
    Runs the existing scraper (backup/microhub_scraper.py) to collect papers
    from PubMed/PMC and store them in SQLite with initial regex-extracted tags.

Phase B (full-text acquisition):
    Fetches missing full text (and methods when available) using a combined
    strategy: three-tier waterfall (Europe PMC → Unpaywall+GROBID → abstract)
    first, then SciHub DOI fallback for any papers still without full text.

    This phase does NOT run tagging agents. Authoritative tagging happens in
    step 3 (`3_clean.py`).

Usage:
    python 1_scrape.py                        # scrape + full-text acquisition
    python 1_scrape.py --skip-fulltext        # scrape only
    python 1_scrape.py --fulltext-only        # skip scraping, fetch full text only
    python 1_scrape.py --fulltext-limit 500   # only fetch full text for 500 papers
    python 1_scrape.py --no-scihub             # disable SciHub DOI fallback

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
"""

import argparse
import logging
import os
import sqlite3
import subprocess
import sys
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def acquire_fulltext(
    db_path: str,
    limit: Optional[int] = None,
    use_scihub_fallback: bool = True,
) -> int:
    """Acquire full text for papers that do not have it yet.

    Uses a combined strategy: three-tier waterfall (Europe PMC →
    Unpaywall+GROBID → abstract) first, then SciHub DOI fallback for
    any papers the waterfall couldn't resolve.

    This phase does NOT run tagging agents. Tagging happens in step 3.
    """
    from pipeline.parsing.section_extractor import three_tier_waterfall
    from pipeline.parsing.scihub_fetcher import fetch_fulltext_via_scihub

    conn = sqlite3.connect(db_path, timeout=120.0)
    conn.row_factory = sqlite3.Row

    columns = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(papers)").fetchall()
    }
    has_text_acquired = "text_acquired" in columns

    query = """
        SELECT id, pmid, doi, title, full_text
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
    logger.info(
        "Strategy: three-tier waterfall%s",
        " + SciHub DOI fallback" if use_scihub_fallback else "",
    )
    logger.info("")

    acquired = 0
    acquired_scihub = 0
    errors = 0

    for i, row in enumerate(rows):
        paper = dict(row)
        doi = paper.get("doi", "")
        pmid = paper.get("pmid", "?")

        try:
            # ---- Tier 1-3: three-tier waterfall ----
            sections = three_tier_waterfall(paper)
            if sections and sections.full_text:
                updates_sql = "UPDATE papers SET full_text = ?"
                params_sql = [sections.full_text]
                if sections.methods:
                    updates_sql += ", methods = ?"
                    params_sql.append(sections.methods)
                if has_text_acquired:
                    updates_sql += ", text_acquired = datetime('now')"
                updates_sql += " WHERE id = ?"
                params_sql.append(paper["id"])
                conn.execute(updates_sql, params_sql)
                conn.commit()
                acquired += 1
                logger.info(
                    "  [%d/%d] PMID %s: full text acquired (%d chars, source=%s)",
                    i + 1,
                    total,
                    pmid,
                    len(sections.full_text),
                    getattr(sections, "source", "unknown") or "unknown",
                )
                continue

            # ---- SciHub DOI fallback ----
            if use_scihub_fallback and doi:
                scihub_text = fetch_fulltext_via_scihub(doi)
                if scihub_text:
                    if has_text_acquired:
                        conn.execute(
                            "UPDATE papers SET full_text = ?, text_acquired = datetime('now') WHERE id = ?",
                            (scihub_text, paper["id"]),
                        )
                    else:
                        conn.execute(
                            "UPDATE papers SET full_text = ? WHERE id = ?",
                            (scihub_text, paper["id"]),
                        )
                    conn.commit()
                    acquired += 1
                    acquired_scihub += 1
                    logger.info(
                        "  [%d/%d] PMID %s: full text via SciHub fallback (%d chars)",
                        i + 1,
                        total,
                        pmid,
                        len(scihub_text),
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
    logger.info(
        "PHASE B COMPLETE: %d papers acquired full text (%d via SciHub fallback, %d errors)",
        acquired,
        acquired_scihub,
        errors,
    )
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
    parser.add_argument("--no-scihub", action="store_true",
                        help="Disable SciHub DOI fallback (only use three-tier waterfall)")
    parser.add_argument("--db", default="microhub.db",
                        help="Database path (default: microhub.db)")

    known, remaining = parser.parse_known_args()

    db_path = known.db
    if not os.path.isabs(db_path):
        db_path = os.path.join(SCRIPT_DIR, db_path)

    def ensure_db_file(path: str) -> None:
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        if not os.path.exists(path):
            conn = sqlite3.connect(path)
            conn.close()
            logger.info("Created database file: %s", path)

    # ---- Phase A: Run the scraper (unless --fulltext-only) ----
    if not known.fulltext_only:
        ensure_db_file(db_path)

        scraper_candidates = [
            os.path.join(SCRIPT_DIR, "backup", "microhub_scraper.py"),
            os.path.join(SCRIPT_DIR, "microhub_scraper.py"),
        ]
        scraper_path = next((path for path in scraper_candidates if os.path.exists(path)), None)

        if not scraper_path:
            logger.error("Scraper not found. Checked: %s", ", ".join(scraper_candidates))
            return 1

        # Forward remaining CLI args + --db to the scraper
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
            if not known.skip_fulltext:
                logger.info("Continuing to full-text acquisition despite scraper error...")

    # ---- Phase B: Full-text acquisition (unless --skip-fulltext) ----
    if not known.skip_fulltext:
        if not os.path.exists(db_path):
            logger.error("Database not found at %s — nothing to fetch.", db_path)
            return 1

        acquire_fulltext(
            db_path=db_path,
            limit=known.fulltext_limit,
            use_scihub_fallback=not known.no_scihub,
        )

    logger.info("")
    logger.info("Done. Next step: python 2_export.py")
    return 0


if __name__ == "__main__":
    main()
