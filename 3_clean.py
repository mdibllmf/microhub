#!/usr/bin/env python3
"""
Step 3 — Clean and re-tag exported JSON files.

Reads the chunked JSON from step 2, applies protocol classification, syncs
field aliases, sets boolean flags, strips full_text, and writes final
WordPress-ready files.

    python 3_clean.py                                     # defaults (enrichment + API calls)
    python 3_clean.py --input-dir raw_export/             # read from step 2 output
    python 3_clean.py --output-dir cleaned_export/        # write here
    python 3_clean.py --no-enrich                         # skip agent pipeline (NOT recommended)
    python 3_clean.py --skip-api                          # skip all API enrichment
    python 3_clean.py --no-openalex                       # skip OpenAlex enrichment
    python 3_clean.py --no-datacite                       # skip DataCite/OpenAIRE dataset linking
    python 3_clean.py --no-ror                            # skip ROR v2 affiliation matching

Input:  raw_export/*_chunk_*.json   (from step 2)
Output: cleaned_export/*_chunk_*.json (ready for step 4 and WordPress)
"""

import argparse
import glob
import json
import logging
import os
import re
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ======================================================================
# Natural-language data-availability patterns
# ======================================================================
# Match prose like "deposited in Zenodo" / "available from Dryad" etc.
# Used as a fallback when URL-based repository detection finds nothing.

_DEPOSITION_VERBS = (
    r"(?:deposited|available|stored|hosted|uploaded|shared|accessible)"
)
_PREPOSITIONS = r"(?:in|on|at|to|via|through|from)"

_DATA_AVAIL_REPOS = {
    "Zenodo": re.compile(
        _DEPOSITION_VERBS + r"\s+" + _PREPOSITIONS + r"\s+(?:the\s+)?Zenodo\b", re.I),
    "Dryad": re.compile(
        _DEPOSITION_VERBS + r"\s+" + _PREPOSITIONS + r"\s+(?:the\s+)?Dryad\b", re.I),
    "Figshare": re.compile(
        _DEPOSITION_VERBS + r"\s+" + _PREPOSITIONS + r"\s+(?:the\s+)?[Ff]ig[Ss]hare\b", re.I),
    "GEO": re.compile(
        _DEPOSITION_VERBS + r"\s+" + _PREPOSITIONS + r"\s+(?:the\s+)?(?:GEO|Gene Expression Omnibus)\b", re.I),
    "SRA": re.compile(
        _DEPOSITION_VERBS + r"\s+" + _PREPOSITIONS + r"\s+(?:the\s+)?(?:SRA|Sequence Read Archive)\b", re.I),
    "ArrayExpress": re.compile(
        _DEPOSITION_VERBS + r"\s+" + _PREPOSITIONS + r"\s+(?:the\s+)?ArrayExpress\b", re.I),
    "EMPIAR": re.compile(
        _DEPOSITION_VERBS + r"\s+" + _PREPOSITIONS + r"\s+(?:the\s+)?EMPIAR\b", re.I),
    "EMDB": re.compile(
        _DEPOSITION_VERBS + r"\s+" + _PREPOSITIONS + r"\s+(?:the\s+)?(?:EMDB|Electron Microscopy Data Bank)\b", re.I),
    "PDB": re.compile(
        _DEPOSITION_VERBS + r"\s+" + _PREPOSITIONS + r"\s+(?:the\s+)?(?:PDB|Protein Data Bank)\b", re.I),
    "BioImage Archive": re.compile(
        _DEPOSITION_VERBS + r"\s+" + _PREPOSITIONS + r"\s+(?:the\s+)?BioImage Archive\b", re.I),
    "IDR": re.compile(
        _DEPOSITION_VERBS + r"\s+" + _PREPOSITIONS + r"\s+(?:the\s+)?(?:Image Data Resource|IDR)\b", re.I),
    "OMERO": re.compile(
        _DEPOSITION_VERBS + r"\s+" + _PREPOSITIONS + r"\s+(?:an?\s+|and\s+)?OMERO\b", re.I),
    "SSBD": re.compile(
        _DEPOSITION_VERBS + r"\s+" + _PREPOSITIONS + r"\s+(?:the\s+)?SSBD\b", re.I),
    "OSF": re.compile(
        _DEPOSITION_VERBS + r"\s+" + _PREPOSITIONS + r"\s+(?:the\s+)?(?:OSF|Open Science Framework)\b", re.I),
    "PRIDE": re.compile(
        _DEPOSITION_VERBS + r"\s+" + _PREPOSITIONS + r"\s+(?:the\s+)?PRIDE\b", re.I),
    "ENA": re.compile(
        _DEPOSITION_VERBS + r"\s+" + _PREPOSITIONS + r"\s+(?:the\s+)?(?:ENA|European Nucleotide Archive)\b", re.I),
    "BioStudies": re.compile(
        _DEPOSITION_VERBS + r"\s+" + _PREPOSITIONS + r"\s+(?:the\s+)?BioStudies\b", re.I),
}


def _mine_data_availability(paper):
    """Scan text fields for natural-language repository references.

    Used as a fallback when no repositories were found by URL-based
    extraction.  Produces repository entries without URLs (name only) —
    URLs can be filled in later via DOI lookup or manual curation.
    """
    # Gather text to scan (prefer full_text, fall back to abstract)
    text = paper.get("full_text") or paper.get("abstract") or ""
    methods = paper.get("methods") or ""
    if methods:
        text = text + "\n" + methods
    if not text:
        return

    repos = []
    seen = set()
    for repo_name, pattern in _DATA_AVAIL_REPOS.items():
        if pattern.search(text) and repo_name not in seen:
            seen.add(repo_name)
            repos.append({
                "name": repo_name,
                "source": "data_availability_mining",
            })

    if repos:
        paper["repositories"] = repos


def _rescan_repositories(paper, repo_scanner, institution_scanner=None):
    """Re-scan all text fields for repository references missed during step 1.

    Merges newly found repositories into the paper's existing repositories
    list, deduplicating by URL.  This is critical for catching Zenodo DOIs,
    OMERO links, Figshare DOIs, and other repository references that may
    appear only in the full text, data availability statements, or methods
    sections.

    Also re-extracts institutions and RORs from affiliations via the
    institution_scanner (if provided), ensuring ROR IDs are generated even
    when the initial enrichment pass missed them.
    """
    # Gather all text to scan (including data_availability where RRIDs often appear)
    texts_to_scan = []
    for field in ("title", "abstract", "methods", "data_availability", "full_text"):
        val = paper.get(field) or ""
        if val and isinstance(val, str) and len(val) > 10:
            texts_to_scan.append((val, field))

    # Run the protocol agent's repository + RRID + protocol matching
    all_extractions = []
    for text, section in texts_to_scan:
        all_extractions.extend(repo_scanner.analyze(text, section))

    # --- Merge repositories ---
    existing_repos = paper.get("repositories") or []
    if isinstance(existing_repos, str):
        try:
            existing_repos = json.loads(existing_repos)
        except (json.JSONDecodeError, TypeError):
            existing_repos = []

    existing_urls = set()
    existing_names = set()
    existing_accessions = set()
    for r in existing_repos:
        if isinstance(r, dict):
            url = (r.get("url") or "").lower().rstrip("/")
            if url:
                existing_urls.add(url)
            existing_names.add((r.get("name") or "").lower())
            acc = r.get("accession", "")
            if acc:
                existing_accessions.add(acc.lower())

    for ext in all_extractions:
        if ext.label == "REPOSITORY":
            url = ext.metadata.get("url", "")
            name = ext.canonical()
            accession = ext.metadata.get("accession_id", "")
            url_lower = url.lower().rstrip("/") if url else ""
            acc_key = (name + ":" + accession).lower() if accession else ""

            # Skip if we already have this URL
            if url_lower and url_lower in existing_urls:
                continue
            # Skip if we already have this accession ID for the same repo type
            if acc_key and acc_key in existing_accessions:
                continue
            # For non-URL repos (e.g., accession IDs), skip if name+text match
            if not url and not accession and name.lower() in existing_names:
                continue

            entry = {"name": name}
            if url:
                entry["url"] = url
            if accession:
                entry["accession"] = accession
            entry["source"] = "rescan"
            existing_repos.append(entry)
            if url_lower:
                existing_urls.add(url_lower)
            if acc_key:
                existing_accessions.add(acc_key)
            existing_names.add(name.lower())

    paper["repositories"] = existing_repos

    # --- Merge protocols (deduplicate by URL + validate) ---
    existing_protos = paper.get("protocols") or []
    if isinstance(existing_protos, str):
        try:
            existing_protos = json.loads(existing_protos)
        except (json.JSONDecodeError, TypeError):
            existing_protos = []

    def _norm_url(url):
        if not url:
            return ""
        return url.strip().rstrip("/").lower().split("?")[0]

    def _url_looks_corrupted(url):
        """Detect digit sequences injected into URL path segments."""
        if not url:
            return False
        for part in url.split("/"):
            if re.search(r"[a-z]-?\d{2,5}-?[a-z]", part):
                cleaned = re.sub(r"\d{2,5}", "", part)
                if cleaned != part and not re.search(r"\d", cleaned):
                    return True
        return False

    seen_urls = set()
    seen_names = set()
    deduped = []
    for proto in existing_protos:
        if not isinstance(proto, dict):
            continue
        url = _norm_url(proto.get("url"))
        name = (proto.get("name") or "").lower()
        if proto.get("url") and _url_looks_corrupted(proto["url"]):
            continue
        if url and url in seen_urls:
            continue
        if not url and name and name in seen_names:
            continue
        if url:
            seen_urls.add(url)
        if name:
            seen_names.add(name)
        deduped.append(proto)

    for ext in all_extractions:
        if ext.label in ("PROTOCOL", "PROTOCOL_URL"):
            name = ext.canonical()
            url = ext.metadata.get("url", "")
            norm = _norm_url(url)
            if url and _url_looks_corrupted(url):
                continue
            if norm and norm in seen_urls:
                continue
            if not norm and name.lower() in seen_names:
                continue
            entry = {"name": name}
            if url:
                entry["url"] = url
            entry["source"] = ext.section or "rescan"
            deduped.append(entry)
            if norm:
                seen_urls.add(norm)
            seen_names.add(name.lower())

    paper["protocols"] = deduped

    # --- Merge RRIDs ---
    existing_rrids = paper.get("rrids") or []
    if isinstance(existing_rrids, str):
        try:
            existing_rrids = json.loads(existing_rrids)
        except (json.JSONDecodeError, TypeError):
            existing_rrids = []

    existing_rrid_ids = {
        (r.get("id") or "").lower() for r in existing_rrids if isinstance(r, dict)
    }

    for ext in all_extractions:
        if ext.label == "RRID":
            rrid_id = ext.metadata.get("rrid_id", "")
            full_id = f"RRID:{rrid_id}"
            if full_id.lower() not in existing_rrid_ids:
                existing_rrids.append({
                    "id": full_id,
                    "type": ext.metadata.get("rrid_type", ""),
                    "url": ext.metadata.get("url", ""),
                })
                existing_rrid_ids.add(full_id.lower())

    paper["rrids"] = existing_rrids

    # --- Merge GitHub URL ---
    if not paper.get("github_url"):
        for ext in all_extractions:
            if ext.label == "GITHUB_URL":
                paper["github_url"] = ext.metadata.get("url")
                break

    # --- Merge RORs ---
    existing_rors = paper.get("rors") or []
    if isinstance(existing_rors, str):
        try:
            existing_rors = json.loads(existing_rors)
        except (json.JSONDecodeError, TypeError):
            existing_rors = []

    existing_ror_ids = set()
    for r in existing_rors:
        if isinstance(r, dict):
            existing_ror_ids.add((r.get("id") or "").lower())
        elif isinstance(r, str):
            existing_ror_ids.add(r.lower())

    # RORs from explicit ROR URLs/IDs found in text (via ProtocolAgent)
    for ext in all_extractions:
        if ext.label == "ROR":
            ror_id = ext.metadata.get("canonical", "")
            url = ext.metadata.get("url", "")
            if ror_id.lower() not in existing_ror_ids:
                existing_rors.append({
                    "id": ror_id,
                    "url": url,
                })
                existing_ror_ids.add(ror_id.lower())

    # RORs from affiliations (via InstitutionAgent) — critical fallback
    # The orchestrator extracts RORs from affiliations, but if that step
    # was skipped or affiliations were malformed, re-extract here.
    if institution_scanner is not None:
        affiliations = paper.get("affiliations") or []
        if isinstance(affiliations, str):
            try:
                affiliations = json.loads(affiliations)
            except (json.JSONDecodeError, TypeError):
                affiliations = []
        if isinstance(affiliations, list) and affiliations:
            inst_exts = institution_scanner.analyze_affiliations(affiliations)
            for ext in inst_exts:
                ror_id = ext.metadata.get("ror_id", "")
                ror_url = ext.metadata.get("ror_url", "")
                if ror_id and ror_id.lower() not in existing_ror_ids:
                    existing_rors.append({
                        "id": ror_id,
                        "url": ror_url,
                        "source": "affiliation_rescan",
                    })
                    existing_ror_ids.add(ror_id.lower())

                # Also merge institutions list
                inst_name = ext.metadata.get("canonical", ext.text)
                if inst_name:
                    existing_insts = paper.get("institutions") or []
                    if isinstance(existing_insts, str):
                        try:
                            existing_insts = json.loads(existing_insts)
                        except (json.JSONDecodeError, TypeError):
                            existing_insts = []
                    if inst_name not in existing_insts:
                        existing_insts.append(inst_name)
                    paper["institutions"] = existing_insts

    paper["rors"] = existing_rors


def main():
    parser = argparse.ArgumentParser(
        description="Step 3 — Clean and re-tag exported JSON",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--input", "-i", help="Single input JSON file")
    parser.add_argument("--input-dir", help="Input directory (default: raw_export/)")
    parser.add_argument("--output-dir", default="cleaned_export",
                        help="Output directory (default: cleaned_export/)")
    parser.add_argument("--no-enrich", action="store_true",
                        help="Skip agent pipeline enrichment (NOT recommended)")
    parser.add_argument("--skip-api", action="store_true",
                        help="Skip all API enrichment (GitHub/S2/CrossRef)")
    parser.add_argument("--no-github", action="store_true",
                        help="Skip GitHub API calls")
    parser.add_argument("--no-citations", action="store_true",
                        help="Skip Semantic Scholar API calls")
    parser.add_argument("--no-crossref", action="store_true",
                        help="Skip CrossRef API calls")
    parser.add_argument("--no-openalex", action="store_true",
                        help="Skip OpenAlex API enrichment")
    parser.add_argument("--no-datacite", action="store_true",
                        help="Skip DataCite/OpenAIRE dataset link discovery")
    parser.add_argument("--no-ror", action="store_true",
                        help="Skip ROR v2 affiliation matching")
    parser.add_argument("--ollama", action="store_true",
                        help="Use local Ollama LLM to verify Methods section tags")
    parser.add_argument("--ollama-model", default=None,
                        help="Ollama model name (default: llama3.1 or OLLAMA_MODEL env)")
    parser.add_argument("--no-pubtator", action="store_true",
                        help="Skip PubTator NLP extraction")
    parser.add_argument("--no-role-classifier", action="store_true",
                        help="Disable role classifier (over-tagging prevention)")
    parser.add_argument("--three-tier", action="store_true",
                        help="Use three-tier waterfall for papers still missing full text")
    parser.add_argument("--workers", type=int, default=4,
                        help="Number of parallel workers for API enrichment (default: 4)")

    args = parser.parse_args()

    from pipeline.export.json_exporter import is_protocol_paper, get_protocol_type
    from pipeline.normalization import normalize_tags
    from pipeline.orchestrator import PipelineOrchestrator
    from pipeline.validation.identifier_normalizer import IdentifierNormalizer
    from pipeline.agents.protocol_agent import ProtocolAgent
    from pipeline.agents.institution_agent import InstitutionAgent

    id_normalizer = IdentifierNormalizer()
    repo_scanner = ProtocolAgent()
    ror_path = os.path.join(SCRIPT_DIR, "microhub_lookup_tables", "ror")
    institution_scanner = InstitutionAgent(
        ror_local_path=ror_path if os.path.isdir(ror_path) else None
    )

    # --- Resolve input files ---
    if args.input:
        input_path = args.input
        if not os.path.isabs(input_path):
            input_path = os.path.join(SCRIPT_DIR, input_path)
        input_files = [input_path]
    else:
        input_dir = args.input_dir
        if input_dir:
            if not os.path.isabs(input_dir):
                input_dir = os.path.join(SCRIPT_DIR, input_dir)
        else:
            # Auto-detect: prefer raw_export/, fall back to project root
            raw_export_dir = os.path.join(SCRIPT_DIR, "raw_export")
            if os.path.isdir(raw_export_dir) and glob.glob(os.path.join(raw_export_dir, "*.json")):
                input_dir = raw_export_dir
            else:
                input_dir = SCRIPT_DIR
        # Try several naming patterns
        input_files = sorted(glob.glob(os.path.join(input_dir, "*_chunk_*.json")))
        if not input_files:
            input_files = sorted(glob.glob(os.path.join(input_dir, "*.json")))

    if not input_files:
        logger.error("No JSON files found! Run step 2 first.")
        sys.exit(1)

    # --- Resolve output directory ---
    out_dir = args.output_dir
    if not os.path.isabs(out_dir):
        out_dir = os.path.join(SCRIPT_DIR, out_dir)
    os.makedirs(out_dir, exist_ok=True)

    # --- Agent enrichment (always on by default) ---
    enricher = None
    if not args.no_enrich:
        dict_path = os.path.join(SCRIPT_DIR, "MASTER_TAG_DICTIONARY.json")
        lookup_path = os.path.join(SCRIPT_DIR, "microhub_lookup_tables")
        enricher = PipelineOrchestrator(
            tag_dictionary_path=dict_path if os.path.exists(dict_path) else None,
            lookup_tables_path=lookup_path if os.path.isdir(lookup_path) else None,
            use_pubtator=False,  # PubTator files are multi-GB; skip until pre-filtered
            use_api_validation=True,
            use_ollama=args.ollama,
            ollama_model=args.ollama_model,
            use_role_classifier=not args.no_role_classifier,
            use_three_tier_waterfall=args.three_tier,
        )

    # --- API enrichment (GitHub, S2, CrossRef) — on by default ---
    api_enrich = not args.skip_api
    enricher_api = None
    if api_enrich:
        from pipeline.enrichment import Enricher
        ror_path = os.path.join(SCRIPT_DIR, "microhub_lookup_tables", "ror")
        enricher_api = Enricher(
            max_workers=args.workers,
            ror_local_path=ror_path if os.path.isdir(ror_path) else None,
        )

    lt_path = os.path.join(SCRIPT_DIR, "microhub_lookup_tables")
    logger.info("=" * 60)
    logger.info("STEP 3 — CLEAN (re-tag + finalize JSON)")
    logger.info("=" * 60)
    logger.info("Input files: %d", len(input_files))
    logger.info("Output dir:  %s", out_dir)
    logger.info("Lookup tables: %s",
                "found" if os.path.isdir(lt_path) else "NOT FOUND (using API fallback)")
    logger.info("Enrich:      %s", "no (--no-enrich)" if args.no_enrich else "yes")
    logger.info("PubTator:    %s", "no" if args.no_pubtator else "yes")
    logger.info("Role class.: %s", "no" if args.no_role_classifier else "yes")
    logger.info("Three-tier:  %s", "yes" if args.three_tier else "no")
    logger.info("Ollama LLM:  %s", "yes" if args.ollama else "no")
    logger.info("Workers:     %d", args.workers)
    logger.info("API enrich:  %s", "yes" if api_enrich else "no")
    if api_enrich:
        logger.info("  OpenAlex:  %s", "no" if args.no_openalex else "yes")
        logger.info("  DataCite:  %s", "no" if args.no_datacite else "yes")
        logger.info("  ROR v2:    %s", "no" if args.no_ror else "yes")
        logger.info("  GitHub:    %s", "no" if args.no_github else "yes")
        logger.info("  S2 cites:  %s", "no" if args.no_citations else "yes")
        logger.info("  CrossRef:  %s", "no" if args.no_crossref else "yes")
    logger.info("")

    total_papers = 0

    for input_file in input_files:
        logger.info("Processing: %s", os.path.basename(input_file))

        with open(input_file, "r", encoding="utf-8") as f:
            papers = json.load(f)
        if not isinstance(papers, list):
            papers = [papers]

        cleaned = []
        for paper in papers:
            # Ensure ALL tag list fields exist (may be missing from older exports)
            tag_list_fields = [
                "microscopy_techniques", "microscope_brands", "microscope_models",
                "reagent_suppliers", "image_analysis_software",
                "image_acquisition_software", "general_software",
                "fluorophores", "organisms", "antibody_sources",
                "cell_lines", "sample_preparation", "protocols",
                "repositories", "rrids", "rors", "institutions",
                "objectives", "lasers", "detectors", "filters",
                "imaging_modalities", "staining_methods",
                "embedding_methods", "fixation_methods", "mounting_media",
                "antibodies", "figures", "references",
                "supplementary_materials", "affiliations",
            ]
            for field in tag_list_fields:
                if field not in paper:
                    paper[field] = []
                elif isinstance(paper[field], str):
                    try:
                        paper[field] = json.loads(paper[field])
                    except (json.JSONDecodeError, TypeError):
                        paper[field] = []

            # Extract data_availability from full_text if not already present.
            # Step 2 may have stripped full_text but preserved data_availability.
            # If full_text is still here (e.g., running step 3 directly on raw
            # data), extract it now so ALL downstream stages can use it.
            if paper.get("full_text") and not paper.get("data_availability"):
                from pipeline.parsing.section_extractor import _extract_data_availability
                paper["data_availability"] = _extract_data_availability(paper["full_text"])

            # Preserve original RORs in case rescan can't re-derive them
            # (institution lookup depends on affiliations which may be absent in rescan)
            original_rors = list(paper.get("rors") or [])

            # Optionally re-run agents — merge results with existing data
            if enricher is not None:
                agent_results = enricher.process_paper(paper)
                for key, val in agent_results.items():
                    if key.startswith("_"):
                        continue
                    if isinstance(val, list) and val:
                        # Union: combine existing + agent, deduplicate
                        existing = paper.get(key) or []
                        if isinstance(existing, str):
                            try:
                                existing = json.loads(existing)
                            except (json.JSONDecodeError, TypeError):
                                existing = []
                        seen = set()
                        combined = []
                        for item in existing + val:
                            if isinstance(item, dict):
                                k = item.get("canonical") or item.get("id") or item.get("url") or json.dumps(item, sort_keys=True)
                            else:
                                k = str(item)
                            if k not in seen:
                                seen.add(k)
                                combined.append(item)
                        paper[key] = combined
                    elif isinstance(val, dict) and val:
                        paper[key] = val
                    elif isinstance(val, str) and val:
                        # Scalar: only overwrite if paper has no value
                        if not paper.get(key):
                            paper[key] = val

            # Log ROR extraction results for diagnostics
            pmid = paper.get("pmid", "?")
            affs = paper.get("affiliations") or []
            rors_after_enrich = paper.get("rors") or []
            if rors_after_enrich:
                logger.info("  PMID %s: enricher found %d ROR(s) from %d affiliation(s)",
                            pmid, len(rors_after_enrich), len(affs))
            elif affs:
                logger.debug("  PMID %s: no RORs found despite %d affiliation(s)",
                             pmid, len(affs))

            # Safety: never downgrade rors to empty if we had them before
            # (institution lookup depends on affiliations which may be absent in rescan)
            if not paper.get("rors") and original_rors:
                paper["rors"] = original_rors

            # Normalize tag names (scraper variants → canonical forms)
            normalize_tags(paper)

            # Re-scan text fields for repository/protocol references that
            # may have been missed during initial scraping.  This catches
            # Zenodo DOIs, OMERO links, Figshare DOIs, etc. that appear in
            # title, abstract, methods, or full_text.
            _rescan_repositories(paper, repo_scanner, institution_scanner)

            # Mine data-availability sections for unlinked repositories
            # (fallback for papers with "deposited in X" prose but no URLs)
            if not paper.get("repositories"):
                _mine_data_availability(paper)

            # Normalize all identifiers (DOIs, RRIDs, RORs, repo URLs)
            id_normalizer.normalize_paper(paper)

            # Protocol classification
            paper["is_protocol"] = is_protocol_paper(paper) or bool(paper.get("protocols"))
            if is_protocol_paper(paper):
                paper["post_type"] = "mh_protocol"
                paper["protocol_type"] = get_protocol_type(paper)
            else:
                paper["post_type"] = "mh_paper"
                paper["protocol_type"] = None

            # Sync aliases
            paper["techniques"] = paper.get("microscopy_techniques", [])
            paper["tags"] = paper.get("microscopy_techniques", [])
            # software = acquisition software only (microscope control: ZEN, Leica Application Suite X, etc.)
            # Analysis and general software have their own dedicated fields
            paper["software"] = paper.get("image_acquisition_software") or []

            # Boolean flags — preserve has_full_text before stripping
            paper["has_full_text"] = (
                bool(paper.get("has_full_text"))
                or bool(paper.get("full_text"))
            )
            paper["has_protocols"] = bool(paper.get("protocols")) or paper.get("is_protocol", False)
            paper["has_github"] = bool(paper.get("github_url"))
            paper["has_github_tools"] = bool(paper.get("github_tools"))
            paper["has_data"] = bool(paper.get("repositories"))
            paper["has_rrids"] = bool(paper.get("rrids"))
            paper["has_rors"] = bool(paper.get("rors"))
            paper["has_fluorophores"] = bool(paper.get("fluorophores"))
            paper["has_cell_lines"] = bool(paper.get("cell_lines"))
            paper["has_sample_prep"] = bool(paper.get("sample_preparation"))
            paper["has_antibody_sources"] = bool(paper.get("antibody_sources"))
            paper["has_antibodies"] = bool(paper.get("antibodies"))
            paper["has_reagent_suppliers"] = bool(paper.get("reagent_suppliers"))
            paper["has_general_software"] = bool(paper.get("general_software"))
            paper["has_methods"] = bool(paper.get("methods") and len(str(paper.get("methods", ""))) > 100)
            paper["has_institutions"] = bool(paper.get("institutions"))
            paper["has_facility"] = paper["has_institutions"]
            paper["has_affiliations"] = bool(paper.get("affiliations"))
            paper["has_figures"] = bool(paper.get("figures"))
            paper["has_supplementary_materials"] = bool(paper.get("supplementary_materials"))
            paper["has_objectives"] = bool(paper.get("objectives"))
            paper["has_lasers"] = bool(paper.get("lasers"))
            paper["has_detectors"] = bool(paper.get("detectors"))
            paper["has_filters"] = bool(paper.get("filters"))

            # New enrichment boolean flags (v6.1) — derived from actual data
            paper["has_openalex"] = bool(paper.get("openalex_id"))
            paper["has_oa"] = bool(paper.get("oa_status")) and str(paper.get("oa_status", "")).lower() != "closed"
            paper["has_fwci"] = paper.get("fwci") is not None and paper.get("fwci") != ""
            paper["has_datasets"] = bool([
                r for r in paper.get("repositories", [])
                if isinstance(r, dict) and r.get("source") in ("datacite", "openaire", "crossref-relation", "text_pattern")
            ])
            # Derive is_open_access from oa_status, not just pass through
            oa_status = str(paper.get("oa_status", "") or "").lower().strip()
            paper["is_open_access"] = oa_status in ("gold", "green", "hybrid", "bronze") or bool(paper.get("is_open_access"))
            paper["has_openalex_topics"] = bool(paper.get("openalex_topics")) and paper.get("openalex_topics") != "[]"
            paper["has_openalex_institutions"] = bool(paper.get("openalex_institutions")) and paper.get("openalex_institutions") != "[]"
            paper["has_fields_of_study"] = bool(paper.get("fields_of_study")) and paper.get("fields_of_study") != "[]"

            # Remove full_text from output (tags already extracted)
            paper.pop("full_text", None)

            cleaned.append(paper)

        # Batch API enrichment (OpenAlex first, S2 citations, then per-paper GH/CrossRef/DataCite/ROR)
        if enricher_api is not None:
            enricher_api.enrich_batch(
                cleaned,
                fetch_openalex=not args.no_openalex,
                fetch_github=not args.no_github,
                fetch_citations=not args.no_citations,
                fetch_crossref_repos=not args.no_crossref,
                fetch_datacite=not args.no_datacite,
                fetch_ror=not args.no_ror,
            )

        # --- Post-enrichment flag refresh ---
        for paper in cleaned:
            paper["has_openalex"] = bool(paper.get("openalex_id"))
            paper["has_oa"] = bool(paper.get("oa_status"))
            paper["has_fwci"] = paper.get("fwci") is not None and paper.get("fwci") != ""
            paper["has_openalex_topics"] = bool(paper.get("openalex_topics"))
            paper["has_openalex_institutions"] = bool(paper.get("openalex_institutions"))
            paper["has_fields_of_study"] = bool(paper.get("fields_of_study"))
            paper["has_datasets"] = bool([
                r for r in paper.get("repositories", [])
                if isinstance(r, dict) and r.get("source") in (
                    "datacite", "openaire", "crossref-relation", "text_pattern"
                )
            ])
            _oa = str(paper.get("oa_status", "")).lower().strip()
            paper["is_open_access"] = (
                paper.get("is_open_access", False)
                or _oa in ("gold", "green", "hybrid", "bronze")
            )
            paper["has_rors"] = bool(paper.get("rors"))
            paper["has_institutions"] = bool(paper.get("institutions"))
            paper["has_facility"] = paper["has_institutions"]

        # Write output
        out_file = os.path.join(out_dir, os.path.basename(input_file))
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(cleaned, f, indent=2, ensure_ascii=False, default=str)

        total_papers += len(cleaned)
        logger.info("  → %d papers → %s", len(cleaned), os.path.basename(out_file))

    logger.info("")
    logger.info("=" * 60)
    logger.info("STEP 3 COMPLETE: %d papers cleaned", total_papers)
    logger.info("=" * 60)
    logger.info("Next step: python 4_validate.py --input-dir %s", out_dir)


if __name__ == "__main__":
    main()
