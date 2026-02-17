#!/usr/bin/env python3
"""
Step 1 — Scrape papers from PubMed / PMC into the SQLite database,
then enrich with NLP pipeline agents.

Phase A (scraper):
    Runs the existing scraper (backup/microhub_scraper.py) to collect papers
    from PubMed/PMC and store them in SQLite with regex-extracted tags.

Phase B (agent enrichment — runs automatically after scraping):
    Reads newly-scraped papers from the DB, runs the pipeline agents
    (technique, equipment, fluorophore, organism, software, sample-prep,
    cell-line, protocol, institution + PubTator + optional Ollama), and
    merges agent results back into the DB.  This fills gaps the scraper's
    regex patterns miss and normalises identifiers.

Usage:
    python 1_scrape.py                       # scrape + enrich
    python 1_scrape.py --limit 200           # scrape 200 then enrich
    python 1_scrape.py --skip-enrich         # scrape only (no agents)
    python 1_scrape.py --enrich-only         # skip scrape, run agents on DB
    python 1_scrape.py --enrich-limit 500    # only enrich 500 papers
    python 1_scrape.py --ollama              # include Ollama LLM verification
    python 1_scrape.py --no-pubtator         # skip PubTator NLP extraction

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
import json
import logging
import os
import sqlite3
import subprocess
import sys
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


# ======================================================================
# Phase B — Agent enrichment
# ======================================================================

def enrich_papers(
    db_path: str,
    limit: int = None,
    use_pubtator: bool = True,
    use_ollama: bool = False,
    ollama_model: str = None,
) -> int:
    """Run pipeline agents on papers in the DB and update with results.

    Parameters
    ----------
    db_path : str
        Path to the SQLite database.
    limit : int, optional
        Maximum number of papers to enrich.
    use_pubtator : bool
        Enable PubTator NLP-based supplemental extraction.
    use_ollama : bool
        Enable Ollama LLM verification of Methods sections.
    ollama_model : str, optional
        Ollama model name override.

    Returns
    -------
    int
        Number of papers enriched.
    """
    from pipeline.orchestrator import PipelineOrchestrator
    from pipeline.normalization import normalize_tags
    from pipeline.validation.identifier_normalizer import IdentifierNormalizer

    dict_path = os.path.join(SCRIPT_DIR, "MASTER_TAG_DICTIONARY.json")
    orchestrator = PipelineOrchestrator(
        tag_dictionary_path=dict_path if os.path.exists(dict_path) else None,
        use_pubtator=use_pubtator,
        use_api_validation=True,
        use_ollama=use_ollama,
        ollama_model=ollama_model,
    )
    id_normalizer = IdentifierNormalizer()

    conn = sqlite3.connect(db_path, timeout=120.0)
    conn.row_factory = sqlite3.Row

    # Enrich papers that haven't been agent-enriched yet (enriched_at IS NULL)
    # OR were scraped more recently than they were enriched.
    query = """
        SELECT * FROM papers
        WHERE enriched_at IS NULL
           OR updated_at > enriched_at
        ORDER BY priority_score DESC, year DESC
    """
    if limit:
        query += f" LIMIT {limit}"

    rows = conn.execute(query).fetchall()
    total = len(rows)

    if total == 0:
        logger.info("No papers need agent enrichment.")
        conn.close()
        return 0

    logger.info("")
    logger.info("=" * 60)
    logger.info("PHASE B — AGENT ENRICHMENT")
    logger.info("=" * 60)
    logger.info("Papers to enrich: %d", total)
    logger.info("PubTator:  %s", "yes" if use_pubtator else "no")
    logger.info("Ollama:    %s", "yes" if use_ollama else "no")
    logger.info("")

    enriched_count = 0
    errors = 0

    # JSON fields that the agents produce as lists
    list_fields = [
        "microscopy_techniques", "microscope_brands", "microscope_models",
        "reagent_suppliers", "image_analysis_software",
        "image_acquisition_software", "general_software",
        "fluorophores", "organisms", "antibody_sources",
        "cell_lines", "sample_preparation", "protocols",
        "repositories", "rrids", "rors", "institutions",
        "objectives", "lasers", "detectors", "filters",
    ]
    scalar_fields = ["github_url", "tag_source"]

    for i, row in enumerate(rows):
        paper = dict(row)
        pmid = paper.get("pmid", "?")

        try:
            # Parse JSON fields so the orchestrator gets proper lists
            for field in list_fields:
                raw = paper.get(field)
                if isinstance(raw, str):
                    try:
                        paper[field] = json.loads(raw)
                    except (json.JSONDecodeError, TypeError):
                        paper[field] = []

            # Run pipeline agents
            agent_results = orchestrator.process_paper(paper)

            # Merge agent results into paper (union lists, keep DB scalars)
            updates = {}
            for field in list_fields:
                if field not in agent_results:
                    continue
                agent_val = agent_results[field]
                if not isinstance(agent_val, list) or not agent_val:
                    continue

                existing = paper.get(field) or []
                if isinstance(existing, str):
                    try:
                        existing = json.loads(existing)
                    except (json.JSONDecodeError, TypeError):
                        existing = []

                # Deduplicated union
                seen = set()
                combined = []
                for item in existing + agent_val:
                    if isinstance(item, dict):
                        key = (
                            item.get("canonical")
                            or item.get("id")
                            or item.get("url")
                            or item.get("name")
                            or json.dumps(item, sort_keys=True)
                        )
                    else:
                        key = str(item).lower()
                    if key not in seen:
                        seen.add(key)
                        combined.append(item)

                updates[field] = json.dumps(combined, ensure_ascii=False)

            for field in scalar_fields:
                if field not in agent_results:
                    continue
                agent_val = agent_results[field]
                # Only overwrite if agent has a value and DB is empty
                if agent_val and not paper.get(field):
                    updates[field] = agent_val

            # Normalize tags on the merged result
            merged_for_norm = dict(paper)
            for field in list_fields:
                if field in updates:
                    try:
                        merged_for_norm[field] = json.loads(updates[field])
                    except (json.JSONDecodeError, TypeError):
                        pass
            normalize_tags(merged_for_norm)
            id_normalizer.normalize_paper(merged_for_norm)

            # Write normalized values back
            for field in list_fields:
                val = merged_for_norm.get(field)
                if isinstance(val, list):
                    updates[field] = json.dumps(val, ensure_ascii=False)

            if updates:
                set_clauses = [f"{f} = ?" for f in updates]
                set_clauses.append("enriched_at = datetime('now')")
                values = list(updates.values())
                values.append(paper["id"])

                conn.execute(
                    f"UPDATE papers SET {', '.join(set_clauses)} WHERE id = ?",
                    values,
                )
                conn.commit()

            enriched_count += 1

            if (i + 1) % 100 == 0:
                logger.info("  Enriched %d / %d papers...", i + 1, total)

        except Exception as exc:
            errors += 1
            logger.debug("Error enriching paper PMID %s: %s", pmid, exc)
            continue

    conn.close()

    logger.info("")
    logger.info("=" * 60)
    logger.info("PHASE B COMPLETE: %d papers enriched (%d errors)", enriched_count, errors)
    logger.info("=" * 60)

    return enriched_count


# ======================================================================
# Main
# ======================================================================

def main():
    # ---- Parse our own flags (enrichment control) ----
    # We intercept enrichment-related flags and forward the rest to the scraper.
    parser = argparse.ArgumentParser(
        description="Step 1 — Scrape + Agent Enrichment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,  # We'll forward --help to scraper if not ours
    )
    parser.add_argument("--skip-enrich", action="store_true",
                        help="Skip agent enrichment after scraping")
    parser.add_argument("--enrich-only", action="store_true",
                        help="Skip scraping, only run agent enrichment on DB")
    parser.add_argument("--enrich-limit", type=int, default=None,
                        help="Max papers to enrich (default: all pending)")
    parser.add_argument("--ollama", action="store_true",
                        help="Enable Ollama LLM verification during enrichment")
    parser.add_argument("--ollama-model", default=None,
                        help="Ollama model name (default: llama3.1)")
    parser.add_argument("--no-pubtator", action="store_true",
                        help="Skip PubTator NLP extraction during enrichment")
    parser.add_argument("--db", default="microhub.db",
                        help="Database path (default: microhub.db)")

    known, remaining = parser.parse_known_args()

    db_path = known.db
    if not os.path.isabs(db_path):
        db_path = os.path.join(SCRIPT_DIR, db_path)

    # ---- Phase A: Run the scraper (unless --enrich-only) ----
    if not known.enrich_only:
        scraper_path = os.path.join(SCRIPT_DIR, "backup", "microhub_scraper.py")

        if not os.path.exists(scraper_path):
            logger.error("Scraper not found at: %s", scraper_path)
            sys.exit(1)

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
            if not known.skip_enrich:
                logger.info("Continuing to agent enrichment despite scraper error...")

    # ---- Phase B: Agent enrichment (unless --skip-enrich) ----
    if not known.skip_enrich:
        if not os.path.exists(db_path):
            logger.error("Database not found at %s — nothing to enrich.", db_path)
            sys.exit(1)

        enrich_papers(
            db_path=db_path,
            limit=known.enrich_limit,
            use_pubtator=not known.no_pubtator,
            use_ollama=known.ollama,
            ollama_model=known.ollama_model,
        )

    logger.info("")
    logger.info("Done. Next step: python 2_export.py")


if __name__ == "__main__":
    main()
