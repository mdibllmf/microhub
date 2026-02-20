#!/usr/bin/env python3
"""
Step 5 — Validate repositories, RRIDs, and cross-references (Pass 2).

Runs the Pass 2 validation agents on already-cleaned papers:
  - DOI-Repository Linker: confirms repo URLs belong to the paper
  - GitHub Health: fetches repo metadata, flags dead/archived repos
  - RRID Validation: validates RRIDs against SciCrunch
  - CrossRef Validation: fills metadata gaps via DOI lookups

This step is OPTIONAL and can be run independently after step 3 or step 4.
It mutates JSON files in-place (or writes to a separate output directory).

Usage:
    python 5_validate_repos.py                                # defaults
    python 5_validate_repos.py --input-dir cleaned_export/    # read from step 3
    python 5_validate_repos.py --output-dir validated_export/ # write here
    python 5_validate_repos.py --skip-github                  # skip GitHub API
    python 5_validate_repos.py --skip-crossref                # skip CrossRef/S2
    python 5_validate_repos.py --skip-rrids                   # skip RRID validation
    python 5_validate_repos.py --skip-doi-link                # skip DOI-repo linking
    python 5_validate_repos.py --limit 50                     # only process 50 papers
"""

import argparse
import glob
import json
import logging
import os
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def _load_env_key(name: str) -> str:
    """Load API key from environment or .env file."""
    val = os.environ.get(name)
    if val:
        return val
    env_path = os.path.join(SCRIPT_DIR, ".env")
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith(f"{name}="):
                    return line.split("=", 1)[1].strip().strip("'\"")
    return ""


def main():
    parser = argparse.ArgumentParser(
        description="Step 5 — Validate repositories, RRIDs, and cross-references",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--input-dir", default="cleaned_export",
                        help="Input directory (default: cleaned_export/)")
    parser.add_argument("--output-dir",
                        help="Output directory (default: same as input, in-place)")
    parser.add_argument("--skip-github", action="store_true",
                        help="Skip GitHub Health agent")
    parser.add_argument("--skip-crossref", action="store_true",
                        help="Skip CrossRef/Semantic Scholar validation")
    parser.add_argument("--skip-rrids", action="store_true",
                        help="Skip RRID validation against SciCrunch")
    parser.add_argument("--skip-doi-link", action="store_true",
                        help="Skip DOI-repository linking")
    parser.add_argument("--limit", type=int, default=0,
                        help="Limit number of papers to process (0 = all)")

    args = parser.parse_args()

    # Lazy imports — only load what we need
    from pipeline.agents.doi_linker_agent import DOILinkerAgent
    from pipeline.agents.github_health_agent import GitHubHealthAgent
    from pipeline.agents.rrid_validation_agent import RRIDValidationAgent
    from pipeline.agents.crossref_agent import CrossRefValidationAgent
    from pipeline.agents.datacite_linker_agent import DataCiteLinkerAgent

    # --- Resolve input ---
    input_dir = args.input_dir
    if not os.path.isabs(input_dir):
        input_dir = os.path.join(SCRIPT_DIR, input_dir)

    input_files = sorted(glob.glob(os.path.join(input_dir, "*.json")))
    if not input_files:
        logger.error("No JSON files found in %s", input_dir)
        sys.exit(1)

    # --- Resolve output ---
    out_dir = args.output_dir
    if out_dir:
        if not os.path.isabs(out_dir):
            out_dir = os.path.join(SCRIPT_DIR, out_dir)
        os.makedirs(out_dir, exist_ok=True)
    else:
        out_dir = input_dir  # in-place

    # --- Initialize agents ---
    github_token = _load_env_key("GITHUB_TOKEN")
    s2_key = _load_env_key("SEMANTIC_SCHOLAR_API_KEY")

    agents = []
    agent_names = []

    if not args.skip_doi_link:
        agents.append(DOILinkerAgent(github_token=github_token))
        agent_names.append("DOI-Repository Linker")

    if not args.skip_github:
        agents.append(GitHubHealthAgent(github_token=github_token))
        agent_names.append("GitHub Health")

    if not args.skip_rrids:
        rrid_cache_path = os.path.join(SCRIPT_DIR, ".rrid_cache.json")
        rrid_agent = RRIDValidationAgent(cache_path=rrid_cache_path)
        agents.append(rrid_agent)
        agent_names.append("RRID Validation")

    if not args.skip_crossref:
        agents.append(CrossRefValidationAgent(s2_api_key=s2_key))
        agent_names.append("CrossRef Validation")

    # Dataset linking is always on (cheap API calls, high value)
    dataset_linker = DataCiteLinkerAgent()

    if not agents:
        logger.warning("All agents skipped — nothing to do!")
        return

    logger.info("=" * 60)
    logger.info("STEP 5 — VALIDATE REPOSITORIES & CROSS-REFERENCES (Pass 2)")
    logger.info("=" * 60)
    logger.info("Input dir:  %s", input_dir)
    logger.info("Output dir: %s", out_dir)
    logger.info("Agents:     %s", ", ".join(agent_names))
    if args.limit:
        logger.info("Limit:      %d papers", args.limit)
    logger.info("")

    total = 0
    validated_count = 0
    repos_confirmed = 0
    repos_dead = 0
    rrids_validated = 0

    for input_file in input_files:
        logger.info("Processing: %s", os.path.basename(input_file))

        with open(input_file, "r", encoding="utf-8") as f:
            papers = json.load(f)
        if not isinstance(papers, list):
            papers = [papers]

        for paper in papers:
            if args.limit and total >= args.limit:
                break

            for agent in agents:
                agent.validate(paper)

            # Also run dataset linker to discover linked datasets
            doi = paper.get("doi", "")
            text = paper.get("data_availability", "") or paper.get("full_text", "")
            if doi or text:
                ds_links = dataset_linker.find_dataset_links(doi=doi, text=text)
                if ds_links:
                    existing_repos = paper.get("repositories") or []
                    if not isinstance(existing_repos, list):
                        existing_repos = []
                    existing_urls = {
                        (r.get("url") or "").lower().rstrip("/")
                        for r in existing_repos if isinstance(r, dict)
                    }
                    for link in ds_links:
                        url = (link.get("url") or "").lower().rstrip("/")
                        if url and url not in existing_urls:
                            existing_repos.append({
                                "url": link.get("url", ""),
                                "name": link.get("repository", "Linked Dataset"),
                                "source": link.get("source", "datacite"),
                            })
                            existing_urls.add(url)
                    paper["repositories"] = existing_repos

            # Count stats
            for repo in paper.get("repositories", []):
                if isinstance(repo, dict):
                    status = repo.get("validation_status", "")
                    if status == "confirmed":
                        repos_confirmed += 1
                    elif status == "dead":
                        repos_dead += 1

            for rrid in paper.get("rrids", []):
                if isinstance(rrid, dict) and rrid.get("validated"):
                    rrids_validated += 1

            validated_count += 1
            total += 1

            if total % 50 == 0:
                logger.info("  ... processed %d papers", total)

        if args.limit and total >= args.limit:
            logger.info("  Reached limit of %d papers", args.limit)

        # Write output
        out_file = os.path.join(out_dir, os.path.basename(input_file))
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(papers, f, indent=2, ensure_ascii=False, default=str)

        logger.info("  → %d papers → %s", len(papers), os.path.basename(out_file))

    # Save RRID cache for future runs
    if not args.skip_rrids:
        try:
            rrid_agent.save_cache()
        except Exception:
            pass

    logger.info("")
    logger.info("=" * 60)
    logger.info("STEP 5 COMPLETE: %d papers validated", validated_count)
    logger.info("  Repos confirmed: %d", repos_confirmed)
    logger.info("  Repos dead:      %d", repos_dead)
    logger.info("  RRIDs validated:  %d", rrids_validated)
    logger.info("  Datasets linked:  (see repositories with source=datacite/openaire)")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
