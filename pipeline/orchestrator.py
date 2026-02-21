"""
Pipeline orchestrator -- wires all agents together.

Processes papers through section-aware parsing → agent extraction →
validation → conflict resolution → output assembly.

Produces a dict per paper whose keys exactly match the existing
WordPress JSON export format to prevent upload issues.
"""

import logging
import os
import re
from typing import Any, Dict, List, Optional, Set

from .agents.base_agent import Extraction
from .agents.technique_agent import TechniqueAgent
from .agents.equipment_agent import EquipmentAgent
from .agents.fluorophore_agent import FluorophoreAgent
from .agents.organism_agent import OrganismAgent
from .agents.software_agent import SoftwareAgent
from .agents.sample_prep_agent import SamplePrepAgent
from .agents.cell_line_agent import CellLineAgent
from .agents.protocol_agent import ProtocolAgent
from .agents.institution_agent import InstitutionAgent
from .agents.pubtator_agent import PubTatorAgent
from .agents.ollama_agent import OllamaVerificationAgent
from .agents.openalex_agent import OpenAlexAgent
from .agents.datacite_linker_agent import DataCiteLinkerAgent
from .parsing.section_extractor import PaperSections, from_pubmed_dict, three_tier_waterfall
from .validation.tag_validator import TagValidator
from .validation.api_validator import ApiValidator
from .validation.identifier_normalizer import IdentifierNormalizer
from .validation.ror_v2_client import RORv2Client
from .validation.ontology_normalizer import OntologyNormalizer
from .role_classifier import RoleClassifier, EntityRole

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """Main orchestrator that runs all agents on a paper and assembles output."""

    def __init__(self, tag_dictionary_path: str = None, *,
                 lookup_tables_path: str = None,
                 use_pubtator: bool = True,
                 use_api_validation: bool = True,
                 use_ollama: bool = False,
                 ollama_model: str = None,
                 use_role_classifier: bool = True,
                 use_three_tier_waterfall: bool = False):

        # Resolve lookup table subdirectories
        lt = lookup_tables_path or ""
        fpbase_path = os.path.join(lt, "fpbase") if lt else None
        cellosaurus_path = os.path.join(lt, "cellosaurus") if lt else None
        taxonomy_path = os.path.join(lt, "ncbi_taxonomy") if lt else None
        ror_path = os.path.join(lt, "ror") if lt else None
        fbbi_path = os.path.join(lt, "fbbi_ontology") if lt else None
        pubtator_path = os.path.join(lt, "pubtator3") if lt else None

        # Extraction agents
        self.technique_agent = TechniqueAgent()
        self.equipment_agent = EquipmentAgent()
        self.fluorophore_agent = FluorophoreAgent()
        self.organism_agent = OrganismAgent()
        self.software_agent = SoftwareAgent()
        self.sample_prep_agent = SamplePrepAgent()
        self.cell_line_agent = CellLineAgent()
        self.protocol_agent = ProtocolAgent()
        self.institution_agent = InstitutionAgent(ror_local_path=ror_path)

        # Supplemental: PubTator NLP-based extraction (with local lookup)
        self.pubtator_agent = PubTatorAgent(
            local_path=pubtator_path
        ) if use_pubtator else None

        # Ollama LLM verification (reads Methods, cross-checks regex results)
        self.ollama_agent = None
        if use_ollama:
            self.ollama_agent = OllamaVerificationAgent(
                model=ollama_model or None
            )

        # Role classifier for over-tagging prevention
        self.role_classifier = RoleClassifier() if use_role_classifier else None

        # Three-tier waterfall for full-text acquisition
        self.use_three_tier_waterfall = use_three_tier_waterfall

        # Validation (with local lookups)
        self.tag_validator = TagValidator(tag_dictionary_path)
        self.api_validator = ApiValidator(
            fpbase_path=fpbase_path,
            cellosaurus_path=cellosaurus_path,
            taxonomy_path=taxonomy_path,
        ) if use_api_validation else None
        self.id_normalizer = IdentifierNormalizer()

        # ROR client (with local lookup)
        self.ror_client = RORv2Client(local_path=ror_path)

        # FBbi ontology normalization (with local lookup)
        self.ontology_normalizer = OntologyNormalizer(local_path=fbbi_path)

    # ------------------------------------------------------------------
    def process_paper(self, paper: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single paper dict and return agent-enriched results.

        Parameters
        ----------
        paper : dict
            A paper dict from the database (or existing JSON export).
            Must contain at least ``title`` and ``abstract``.

        Returns
        -------
        dict
            Extraction results keyed by category, ready for the exporter.
        """
        # Full-text acquisition: use three-tier waterfall if enabled
        if self.use_three_tier_waterfall:
            sections = three_tier_waterfall(paper)
        else:
            sections = from_pubmed_dict(paper)

        results = self._run_agents(sections, paper)

        # Supplemental: PubTator NLP-based extraction for papers with PMIDs
        pmid = paper.get("pmid")
        if self.pubtator_agent and pmid:
            self._merge_pubtator(results, pmid)

        # Post-PubTator: re-validate tags to ensure PubTator additions
        # conform to the master dictionary (prevents over-tagging with
        # organisms, cell lines, or fluorophores not in our taxonomy)
        for category in ("organisms", "fluorophores", "cell_lines"):
            if category in results and results[category]:
                results[category] = self.tag_validator.filter_valid(
                    category, results[category]
                )

        # Post-extraction: validate tags against authoritative APIs
        if self.api_validator:
            self.api_validator.validate_paper(results)

        # Post-extraction: Ollama LLM verification of Methods section
        if self.ollama_agent and self.ollama_agent.is_available():
            llm_results = self.ollama_agent.verify_and_extract(paper, results)
            if llm_results.get("added") or llm_results.get("removed"):
                self.ollama_agent.apply_results(results, llm_results)
                logger.debug(
                    "Ollama verification: added=%s, flagged=%s",
                    llm_results.get("added", {}),
                    llm_results.get("removed", {}),
                )

        # Role classification is now applied inside _run_agents() where
        # raw extractions with position data are still available.
        # The _role_classification report is already in results if enabled.

        # Post-extraction: FBbi ontology normalization for techniques
        if self.ontology_normalizer and results.get("microscopy_techniques"):
            results["_technique_ontology"] = (
                self.ontology_normalizer.enrich_techniques(
                    results["microscopy_techniques"]
                )
            )

        # Post-extraction: normalize all identifiers
        self.id_normalizer.normalize_paper(results)

        return results

    def process_sections(self, sections: PaperSections) -> Dict[str, Any]:
        """Process pre-parsed PaperSections."""
        return self._run_agents(sections, sections.metadata)

    # ------------------------------------------------------------------
    def _run_agents(self, sections: PaperSections,
                    metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Run all agents over each relevant section and assemble results."""

        # Determine which text to extract from
        # Priority: methods > full_text > title+abstract
        primary_text = sections.methods_or_fallback()
        title = sections.title
        abstract = sections.abstract

        # Decide tag_source
        tag_source = sections.tag_source

        # ---- Run agents on the appropriate text ----

        # For most agents, run on the primary text (methods preferred)
        technique_exts = self._run_on_sections(
            self.technique_agent, sections
        )
        equipment_exts = self._run_on_sections(
            self.equipment_agent, sections
        )
        fluorophore_exts = self._run_on_sections(
            self.fluorophore_agent, sections
        )
        organism_exts = self._run_on_sections(
            self.organism_agent, sections
        )
        software_exts = self._run_on_sections(
            self.software_agent, sections
        )
        sample_prep_exts = self._run_on_sections(
            self.sample_prep_agent, sections
        )
        cell_line_exts = self._run_on_sections(
            self.cell_line_agent, sections
        )
        protocol_exts = self._run_on_sections(
            self.protocol_agent, sections
        )

        # Antibody sources (from organism agent)
        antibody_exts = []
        for text, sec in self._section_texts(sections):
            antibody_exts.extend(
                self.organism_agent.extract_antibody_sources(text, sec)
            )

        # Institutions from affiliations (NOT from paper body)
        institution_exts = []
        affiliations = metadata.get("affiliations", [])
        if isinstance(affiliations, list) and affiliations:
            institution_exts = self.institution_agent.analyze_affiliations(affiliations)
        elif isinstance(affiliations, str) and affiliations:
            institution_exts = self.institution_agent.analyze(affiliations, "affiliation")

        # ---- Role classification: filter REFERENCED entities ----
        if self.role_classifier:
            section_texts = {}
            for text, sec_type in self._section_texts(sections):
                section_texts[sec_type] = text

            # Classify all classifiable extractions (not protocols/institutions)
            all_classifiable = (
                technique_exts + equipment_exts + fluorophore_exts +
                organism_exts + software_exts + sample_prep_exts +
                cell_line_exts
            )

            classified = self.role_classifier.classify_extractions(
                all_classifiable, section_texts
            )
            filtered = self.role_classifier.filter_used_entities(classified)

            # Build per-label sets of canonicals that passed role classification
            filtered_by_label = {}
            for c in filtered:
                filtered_by_label.setdefault(c.label, set()).add(c.canonical.lower())

            # Filter ALL entity types through the role classifier
            # (prevents over-tagging from Introduction/Discussion references)
            def _role_filter(exts, label):
                allowed = filtered_by_label.get(label)
                if allowed is None:
                    return exts  # label not classified → pass through
                return [e for e in exts if e.canonical().lower() in allowed]

            technique_exts = _role_filter(technique_exts, "MICROSCOPY_TECHNIQUE")
            # Equipment has multiple sub-labels — filter each independently
            equipment_exts = [
                e for e in equipment_exts
                if e.canonical().lower() in filtered_by_label.get(
                    e.label, {e.canonical().lower()}  # pass through if label not classified
                )
            ]
            fluorophore_exts = _role_filter(fluorophore_exts, "FLUOROPHORE")
            organism_exts = _role_filter(organism_exts, "ORGANISM")
            # Software has multiple sub-labels — filter each independently
            software_exts = [
                e for e in software_exts
                if e.canonical().lower() in filtered_by_label.get(
                    e.label, {e.canonical().lower()}  # pass through if label not classified
                )
            ]
            sample_prep_exts = _role_filter(sample_prep_exts, "SAMPLE_PREPARATION")
            cell_line_exts = _role_filter(cell_line_exts, "CELL_LINE")

            # Store role classification stats in results
            role_report = self.role_classifier.validate_tagging_distribution(classified)
        else:
            role_report = None

        # ---- Collect canonical values by category ----
        results: Dict[str, Any] = {}

        results["microscopy_techniques"] = self._canonicals(
            technique_exts, "microscopy_techniques"
        )
        results["microscope_brands"] = self._canonicals(
            [e for e in equipment_exts if e.label == "MICROSCOPE_BRAND"],
            "microscope_brands",
        )
        results["microscope_models"] = self._canonicals(
            [e for e in equipment_exts if e.label == "MICROSCOPE_MODEL"],
            "microscope_models",
        )
        results["reagent_suppliers"] = self._canonicals(
            [e for e in equipment_exts if e.label == "REAGENT_SUPPLIER"],
        )
        results["objectives"] = self._structured_equipment(
            [e for e in equipment_exts if e.label == "OBJECTIVE"],
        )
        results["lasers"] = self._structured_equipment(
            [e for e in equipment_exts if e.label == "LASER"],
        )
        results["detectors"] = self._structured_equipment(
            [e for e in equipment_exts if e.label == "DETECTOR"],
        )
        results["filters"] = self._structured_equipment(
            [e for e in equipment_exts if e.label == "FILTER"],
        )
        results["image_analysis_software"] = self._canonicals(
            [e for e in software_exts if e.label == "IMAGE_ANALYSIS_SOFTWARE"],
            "image_analysis_software",
        )
        results["image_acquisition_software"] = self._canonicals(
            [e for e in software_exts if e.label == "IMAGE_ACQUISITION_SOFTWARE"],
            "image_acquisition_software",
        )
        results["general_software"] = self._canonicals(
            [e for e in software_exts if e.label == "GENERAL_SOFTWARE"],
        )
        results["fluorophores"] = self._canonicals(
            fluorophore_exts, "fluorophores"
        )
        results["organisms"] = self._canonicals(
            organism_exts, "organisms"
        )
        results["antibody_sources"] = self._canonicals(antibody_exts)
        results["cell_lines"] = self._canonicals(
            cell_line_exts, "cell_lines"
        )
        results["sample_preparation"] = self._canonicals(
            sample_prep_exts, "sample_preparation"
        )

        # Protocols and repositories (structured)
        results["protocols"] = self._structured_protocols(protocol_exts)
        results["repositories"] = self._structured_repositories(protocol_exts)
        results["rrids"] = self._structured_rrids(protocol_exts)
        results["rors"] = self._structured_rors(
            protocol_exts, institution_exts
        )
        results["institutions"] = self._canonicals(institution_exts)

        # GitHub URL (first one found)
        github_exts = [e for e in protocol_exts if e.label == "GITHUB_URL"]
        results["github_url"] = (
            github_exts[0].metadata.get("url") if github_exts else None
        )

        # Tag source
        results["tag_source"] = tag_source

        # Confidence scores for debugging
        results["_confidence"] = self._confidence_summary(
            technique_exts + equipment_exts + fluorophore_exts +
            organism_exts + software_exts + sample_prep_exts +
            cell_line_exts + protocol_exts + institution_exts
        )

        # Role classification report (if classifier was used)
        if role_report:
            results["_role_classification"] = role_report

        return results

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _run_on_sections(self, agent, sections: PaperSections) -> List[Extraction]:
        """Run an agent over all available sections and merge results."""
        all_exts: List[Extraction] = []
        for text, sec_type in self._section_texts(sections):
            all_exts.extend(agent.analyze(text, sec_type))
        return agent._deduplicate(all_exts)

    @staticmethod
    def _section_texts(sections: PaperSections):
        """Yield (text, section_type) pairs for each available section."""
        if sections.title:
            yield sections.title, "title"
        if sections.abstract:
            yield sections.abstract, "abstract"
        if sections.methods:
            yield sections.methods, "methods"
        if sections.results:
            yield sections.results, "results"
        if sections.introduction:
            yield sections.introduction, "introduction"
        if sections.discussion:
            yield sections.discussion, "discussion"
        if sections.figures:
            yield sections.figures, "figures"
        if sections.data_availability:
            yield sections.data_availability, "data_availability"
        # If we only have full_text (no section segmentation),
        # yield it as "full_text" to give agents something to work with
        if (not sections.methods and not sections.results
                and sections.full_text
                and sections.full_text != sections.abstract):
            yield sections.full_text, "full_text"

    def _canonicals(self, extractions: List[Extraction],
                    validation_category: str = None) -> List[str]:
        """Extract unique canonical values, optionally validated."""
        seen: Set[str] = set()
        result: List[str] = []
        for ext in extractions:
            canonical = ext.canonical()
            if canonical not in seen:
                seen.add(canonical)
                result.append(canonical)

        if validation_category:
            result = self.tag_validator.filter_valid(
                validation_category, result
            )
        return result

    @staticmethod
    def _structured_equipment(extractions: List[Extraction]) -> List[Dict]:
        """Build structured equipment dicts with brand/vendor metadata.

        Returns a list of dicts, each containing at minimum 'canonical' and
        'brand' keys, plus any additional metadata from the extraction
        (e.g., magnification, na, immersion for objectives; wavelength_nm
        for lasers; type for detectors/filters).
        """
        seen: Set[str] = set()
        result: List[Dict] = []
        for ext in extractions:
            canonical = ext.canonical()
            if canonical.lower() in seen:
                continue
            seen.add(canonical.lower())

            entry = {"canonical": canonical}
            # Copy all metadata keys except 'canonical' (already set)
            for key, val in ext.metadata.items():
                if key != "canonical" and val:
                    entry[key] = val
            result.append(entry)
        return result

    @staticmethod
    def _structured_protocols(exts: List[Extraction]) -> List[Dict]:
        """Build structured protocol list."""
        protocols = []
        seen: Set[str] = set()
        for ext in exts:
            if ext.label not in ("PROTOCOL", "PROTOCOL_URL"):
                continue
            name = ext.canonical()
            if name in seen:
                continue
            seen.add(name)
            entry = {"name": name}
            if ext.metadata.get("url"):
                entry["url"] = ext.metadata["url"]
            entry["source"] = ext.section
            protocols.append(entry)
        return protocols

    @staticmethod
    def _structured_repositories(exts: List[Extraction]) -> List[Dict]:
        """Build structured repository list, deduplicating by URL and accession ID."""
        repos = []
        seen_urls: Set[str] = set()
        seen_accessions: Set[str] = set()
        for ext in exts:
            if ext.label != "REPOSITORY":
                continue
            url = ext.metadata.get("url", "")
            url_key = url.lower().rstrip("/") if url else ""
            accession = ext.metadata.get("accession_id", "")
            acc_key = (ext.canonical() + ":" + accession).lower() if accession else ""

            # Skip if we already have this URL or accession
            if url_key and url_key in seen_urls:
                continue
            if acc_key and acc_key in seen_accessions:
                continue

            if url_key:
                seen_urls.add(url_key)
            if acc_key:
                seen_accessions.add(acc_key)

            entry = {"name": ext.canonical()}
            if url:
                entry["url"] = url
            if accession:
                entry["accession"] = accession
            repos.append(entry)
        return repos

    @staticmethod
    def _structured_rrids(exts: List[Extraction]) -> List[Dict]:
        """Build structured RRID list."""
        rrids = []
        seen: Set[str] = set()
        for ext in exts:
            if ext.label != "RRID":
                continue
            rrid_id = ext.metadata.get("rrid_id", "")
            if rrid_id in seen:
                continue
            seen.add(rrid_id)
            rrids.append({
                "id": f"RRID:{rrid_id}",
                "type": ext.metadata.get("rrid_type", ""),
                "url": ext.metadata.get("url", ""),
            })
        return rrids

    @staticmethod
    def _structured_rors(protocol_exts: List[Extraction],
                         institution_exts: List[Extraction]) -> List[Dict]:
        """Build structured ROR list from both protocol and institution agents."""
        rors = []
        seen: Set[str] = set()

        # From protocol agent (ROR URLs found in text)
        for ext in protocol_exts:
            if ext.label != "ROR":
                continue
            ror_id = ext.canonical()
            if ror_id.lower() in seen:
                continue
            seen.add(ror_id.lower())
            rors.append({
                "id": ror_id,
                "url": ext.metadata.get("url", ""),
                "source": "text",
            })

        # From institution agent (ROR IDs looked up from institution names)
        for ext in institution_exts:
            ror_id = ext.metadata.get("ror_id")
            if ror_id and ror_id.lower() not in seen:
                seen.add(ror_id.lower())
                rors.append({
                    "id": ror_id,
                    "url": ext.metadata.get("ror_url", ""),
                    "source": "institution_lookup",
                })

        return rors

    def _merge_pubtator(self, results: Dict[str, Any], pmid: str) -> None:
        """Merge PubTator NLP extractions into results.

        Only adds entities not already found by regex agents.
        This fills gaps — PubTator catches entities our patterns miss.
        """
        pt_exts = self.pubtator_agent.analyze_pmid(pmid)
        if not pt_exts:
            return

        # Build sets of what we already have (lowercased for comparison)
        existing = {
            "organisms": {v.lower() for v in results.get("organisms", [])},
            "fluorophores": {v.lower() for v in results.get("fluorophores", [])},
            "cell_lines": {v.lower() for v in results.get("cell_lines", [])},
        }

        added = 0
        for ext in pt_exts:
            canonical = ext.canonical()
            canonical_lower = canonical.lower()

            if ext.label == "ORGANISM":
                if canonical_lower not in existing["organisms"]:
                    results.setdefault("organisms", []).append(canonical)
                    existing["organisms"].add(canonical_lower)
                    added += 1

            elif ext.label == "FLUOROPHORE":
                if canonical_lower not in existing["fluorophores"]:
                    results.setdefault("fluorophores", []).append(canonical)
                    existing["fluorophores"].add(canonical_lower)
                    added += 1

            elif ext.label == "CELL_LINE":
                if canonical_lower not in existing["cell_lines"]:
                    results.setdefault("cell_lines", []).append(canonical)
                    existing["cell_lines"].add(canonical_lower)
                    added += 1

        if added:
            logger.debug("PubTator added %d supplemental entities for PMID %s",
                         added, pmid)

    @staticmethod
    def _confidence_summary(exts: List[Extraction]) -> Dict:
        """Summarise average confidence by label for diagnostics."""
        from collections import defaultdict
        sums: Dict[str, float] = defaultdict(float)
        counts: Dict[str, int] = defaultdict(int)
        for ext in exts:
            sums[ext.label] += ext.confidence
            counts[ext.label] += 1
        return {
            label: round(sums[label] / counts[label], 3)
            for label in counts
        }
