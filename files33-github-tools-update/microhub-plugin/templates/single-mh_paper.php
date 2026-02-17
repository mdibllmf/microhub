<?php
/**
 * Single Paper Template v2.2
 * With all taxonomy tags (matching protocol page), RRID links, and tag-based recommendations
 */
get_header();

$post_id = get_the_ID();
$doi = get_post_meta($post_id, '_mh_doi', true);
$pubmed_id = get_post_meta($post_id, '_mh_pubmed_id', true);
$authors = get_post_meta($post_id, '_mh_authors', true);
$journal = get_post_meta($post_id, '_mh_journal', true);
$year = get_post_meta($post_id, '_mh_publication_year', true);
$citations = get_post_meta($post_id, '_mh_citation_count', true);
$abstract = get_post_meta($post_id, '_mh_abstract', true);
$pdf_url = get_post_meta($post_id, '_mh_pdf_url', true);
$github_url = get_post_meta($post_id, '_mh_github_url', true);
$facility = get_post_meta($post_id, '_mh_facility', true);

$protocols = json_decode(get_post_meta($post_id, '_mh_protocols', true), true) ?: array();
$repos = json_decode(get_post_meta($post_id, '_mh_repositories', true), true) ?: array();
$rrids = json_decode(get_post_meta($post_id, '_mh_rrids', true), true) ?: array();
$rors = json_decode(get_post_meta($post_id, '_mh_rors', true), true) ?: array();
$references = json_decode(get_post_meta($post_id, '_mh_references', true), true) ?: array();
$github_tools = json_decode(get_post_meta($post_id, '_mh_github_tools', true), true) ?: array();

// Meta-based arrays (used as fallback if taxonomy terms are empty)
$fluorophores_meta = json_decode(get_post_meta($post_id, '_mh_fluorophores', true), true) ?: array();
$sample_preparation_meta = json_decode(get_post_meta($post_id, '_mh_sample_preparation', true), true) ?: array();
if (empty($sample_preparation_meta)) {
    $sample_preparation_meta = json_decode(get_post_meta($post_id, '_mh_sample_prep', true), true) ?: array();
}
$cell_lines_meta = json_decode(get_post_meta($post_id, '_mh_cell_lines', true), true) ?: array();
$microscope_brands_meta = json_decode(get_post_meta($post_id, '_mh_microscope_brands', true), true) ?: array();
$reagent_suppliers_meta = json_decode(get_post_meta($post_id, '_mh_reagent_suppliers', true), true) ?: array();
$image_analysis_software_meta = json_decode(get_post_meta($post_id, '_mh_image_analysis_software', true), true) ?: array();
$image_acquisition_software_meta = json_decode(get_post_meta($post_id, '_mh_image_acquisition_software', true), true) ?: array();
$general_software_meta = json_decode(get_post_meta($post_id, '_mh_general_software', true), true) ?: array();

// Get all taxonomy terms
$techniques = wp_get_post_terms($post_id, 'mh_technique', array('fields' => 'all'));
$microscopes = wp_get_post_terms($post_id, 'mh_microscope', array('fields' => 'all'));
$organisms = wp_get_post_terms($post_id, 'mh_organism', array('fields' => 'all'));
$software = wp_get_post_terms($post_id, 'mh_software', array('fields' => 'all'));
$fluorophores_tax = wp_get_post_terms($post_id, 'mh_fluorophore', array('fields' => 'all'));
$sample_prep_tax = wp_get_post_terms($post_id, 'mh_sample_prep', array('fields' => 'all'));
$cell_lines_tax = wp_get_post_terms($post_id, 'mh_cell_line', array('fields' => 'all'));
$microscope_models = wp_get_post_terms($post_id, 'mh_microscope_model', array('fields' => 'all'));
$analysis_software = wp_get_post_terms($post_id, 'mh_analysis_software', array('fields' => 'all'));
$acquisition_software = wp_get_post_terms($post_id, 'mh_acquisition_software', array('fields' => 'all'));
$facilities_tax = wp_get_post_terms($post_id, 'mh_facility', array('fields' => 'all'));

// Normalize WP_Error to empty arrays
if (is_wp_error($techniques)) $techniques = array();
if (is_wp_error($microscopes)) $microscopes = array();
if (is_wp_error($organisms)) $organisms = array();
if (is_wp_error($software)) $software = array();
if (is_wp_error($fluorophores_tax)) $fluorophores_tax = array();
if (is_wp_error($sample_prep_tax)) $sample_prep_tax = array();
if (is_wp_error($cell_lines_tax)) $cell_lines_tax = array();
if (is_wp_error($microscope_models)) $microscope_models = array();
if (is_wp_error($analysis_software)) $analysis_software = array();
if (is_wp_error($acquisition_software)) $acquisition_software = array();
if (is_wp_error($facilities_tax)) $facilities_tax = array();
?>

<article class="mh-single-paper">
        <!-- Paper Header -->
        <header class="mh-paper-header">
            <div class="mh-paper-header-inner">
                <?php if ($citations >= 100) : ?>
                    <span class="mh-badge foundational">&#127942; Foundational Paper</span>
                <?php elseif ($citations >= 50) : ?>
                    <span class="mh-badge high-impact">&#11088; High Impact</span>
                <?php endif; ?>

                <h1><?php the_title(); ?></h1>

                <?php if ($authors) : ?>
                    <p class="mh-paper-authors"><?php echo esc_html($authors); ?></p>
                <?php endif; ?>

                <div class="mh-paper-meta">
                    <?php if ($journal) : ?>
                        <span class="mh-meta-item">&#128240; <?php echo esc_html($journal); ?></span>
                    <?php endif; ?>
                    <?php if ($year) : ?>
                        <span class="mh-meta-item">&#128197; <?php echo esc_html($year); ?></span>
                    <?php endif; ?>
                    <?php if ($citations) : ?>
                        <span class="mh-meta-item">&#128202; <?php echo number_format($citations); ?> citations</span>
                    <?php endif; ?>
                </div>

                <div class="mh-paper-links">
                    <?php if ($doi) : ?>
                        <a href="https://doi.org/<?php echo esc_attr($doi); ?>" class="mh-btn doi" target="_blank">DOI</a>
                    <?php endif; ?>
                    <?php if ($pubmed_id) : ?>
                        <a href="https://pubmed.ncbi.nlm.nih.gov/<?php echo esc_attr($pubmed_id); ?>/" class="mh-btn pubmed" target="_blank">PubMed</a>
                    <?php endif; ?>
                    <?php if ($pdf_url) : ?>
                        <a href="<?php echo esc_url($pdf_url); ?>" class="mh-btn pdf" target="_blank">PDF</a>
                    <?php endif; ?>
                    <?php if ($github_url) : ?>
                        <a href="<?php echo esc_url($github_url); ?>" class="mh-btn github" target="_blank">&#128187; GitHub</a>
                    <?php endif; ?>
                </div>
            </div>
        </header>

        <div class="mh-paper-content">
            <div class="mh-paper-main">
                <!-- Abstract -->
                <?php if ($abstract) : ?>
                <section class="mh-paper-section">
                    <h2>Abstract</h2>
                    <p><?php echo esc_html($abstract); ?></p>
                </section>
                <?php endif; ?>

                <!-- Techniques -->
                <?php if (!empty($techniques)) : ?>
                <section class="mh-paper-section">
                    <h2>&#128300; Techniques</h2>
                    <div class="mh-tag-list">
                        <?php foreach ($techniques as $term) : ?>
                            <a href="<?php echo esc_url(get_term_link($term)); ?>" class="mh-tag technique"><?php echo esc_html($term->name); ?></a>
                        <?php endforeach; ?>
                    </div>
                </section>
                <?php endif; ?>

                <!-- Microscopes -->
                <?php if (!empty($microscopes)) : ?>
                <section class="mh-paper-section">
                    <h2>&#128301; Microscopes</h2>
                    <div class="mh-tag-list">
                        <?php foreach ($microscopes as $term) : ?>
                            <a href="<?php echo esc_url(get_term_link($term)); ?>" class="mh-tag microscope"><?php echo esc_html($term->name); ?></a>
                        <?php endforeach; ?>
                    </div>
                </section>
                <?php endif; ?>

                <!-- Organisms -->
                <?php if (!empty($organisms)) : ?>
                <section class="mh-paper-section">
                    <h2>&#129516; Organisms</h2>
                    <div class="mh-tag-list">
                        <?php foreach ($organisms as $term) : ?>
                            <a href="<?php echo esc_url(get_term_link($term)); ?>" class="mh-tag organism"><?php echo esc_html($term->name); ?></a>
                        <?php endforeach; ?>
                    </div>
                </section>
                <?php endif; ?>

                <!-- Software (taxonomy) -->
                <?php if (!empty($software)) : ?>
                <section class="mh-paper-section">
                    <h2>&#128187; Software</h2>
                    <div class="mh-tag-list">
                        <?php foreach ($software as $term) : ?>
                            <a href="<?php echo esc_url(get_term_link($term)); ?>" class="mh-tag software"><?php echo esc_html($term->name); ?></a>
                        <?php endforeach; ?>
                    </div>
                </section>
                <?php endif; ?>

                <!-- Fluorophores (taxonomy, then meta fallback) -->
                <?php if (!empty($fluorophores_tax)) : ?>
                <section class="mh-paper-section">
                    <h2>&#10024; Fluorophores</h2>
                    <div class="mh-tag-list">
                        <?php foreach ($fluorophores_tax as $term) : ?>
                            <a href="<?php echo esc_url(get_term_link($term)); ?>" class="mh-tag fluorophore"><?php echo esc_html($term->name); ?></a>
                        <?php endforeach; ?>
                    </div>
                </section>
                <?php elseif (!empty($fluorophores_meta)) : ?>
                <section class="mh-paper-section">
                    <h2>&#10024; Fluorophores</h2>
                    <div class="mh-tag-list">
                        <?php foreach ($fluorophores_meta as $fluor) : ?>
                            <span class="mh-tag fluorophore"><?php echo esc_html($fluor); ?></span>
                        <?php endforeach; ?>
                    </div>
                </section>
                <?php endif; ?>

                <!-- Sample Preparation (taxonomy, then meta fallback) -->
                <?php if (!empty($sample_prep_tax)) : ?>
                <section class="mh-paper-section">
                    <h2>&#129514; Sample Preparation</h2>
                    <div class="mh-tag-list">
                        <?php foreach ($sample_prep_tax as $term) : ?>
                            <a href="<?php echo esc_url(get_term_link($term)); ?>" class="mh-tag sample-prep"><?php echo esc_html($term->name); ?></a>
                        <?php endforeach; ?>
                    </div>
                </section>
                <?php elseif (!empty($sample_preparation_meta)) : ?>
                <section class="mh-paper-section">
                    <h2>&#129514; Sample Preparation</h2>
                    <div class="mh-tag-list">
                        <?php foreach ($sample_preparation_meta as $prep) : ?>
                            <span class="mh-tag sample-prep"><?php echo esc_html($prep); ?></span>
                        <?php endforeach; ?>
                    </div>
                </section>
                <?php endif; ?>

                <!-- Cell Lines (taxonomy, then meta fallback) -->
                <?php if (!empty($cell_lines_tax)) : ?>
                <section class="mh-paper-section">
                    <h2>&#128300; Cell Lines</h2>
                    <div class="mh-tag-list">
                        <?php foreach ($cell_lines_tax as $term) : ?>
                            <a href="<?php echo esc_url(get_term_link($term)); ?>" class="mh-tag cell-line"><?php echo esc_html($term->name); ?></a>
                        <?php endforeach; ?>
                    </div>
                </section>
                <?php elseif (!empty($cell_lines_meta)) : ?>
                <section class="mh-paper-section">
                    <h2>&#128300; Cell Lines</h2>
                    <div class="mh-tag-list">
                        <?php foreach ($cell_lines_meta as $cell) : ?>
                            <span class="mh-tag cell-line"><?php echo esc_html($cell); ?></span>
                        <?php endforeach; ?>
                    </div>
                </section>
                <?php endif; ?>

                <!-- Microscope Brands (from meta) -->
                <?php if (!empty($microscope_brands_meta)) : ?>
                <section class="mh-paper-section">
                    <h2>&#127981; Microscope Brands</h2>
                    <div class="mh-tag-list">
                        <?php foreach ($microscope_brands_meta as $brand) : ?>
                            <span class="mh-tag brand"><?php echo esc_html($brand); ?></span>
                        <?php endforeach; ?>
                    </div>
                </section>
                <?php endif; ?>

                <!-- Reagent Suppliers (from meta) -->
                <?php if (!empty($reagent_suppliers_meta)) : ?>
                <section class="mh-paper-section">
                    <h2>&#129514; Reagent Suppliers</h2>
                    <div class="mh-tag-list">
                        <?php foreach ($reagent_suppliers_meta as $supplier) : ?>
                            <span class="mh-tag supplier"><?php echo esc_html($supplier); ?></span>
                        <?php endforeach; ?>
                    </div>
                </section>
                <?php endif; ?>

                <!-- Software from meta (analysis, acquisition, general) -->
                <?php
                $has_meta_software = !empty($image_analysis_software_meta) || !empty($image_acquisition_software_meta) || !empty($general_software_meta);
                if ($has_meta_software) :
                ?>
                <section class="mh-paper-section">
                    <h2>&#128187; Software Details</h2>
                    <?php if (!empty($image_acquisition_software_meta)) : ?>
                        <div class="mh-software-subsection">
                            <strong>Image Acquisition:</strong>
                            <div class="mh-tag-list">
                                <?php foreach ($image_acquisition_software_meta as $sw) : ?>
                                    <span class="mh-tag software"><?php echo esc_html($sw); ?></span>
                                <?php endforeach; ?>
                            </div>
                        </div>
                    <?php endif; ?>
                    <?php if (!empty($image_analysis_software_meta)) : ?>
                        <div class="mh-software-subsection">
                            <strong>Image Analysis:</strong>
                            <div class="mh-tag-list">
                                <?php foreach ($image_analysis_software_meta as $sw) : ?>
                                    <span class="mh-tag software"><?php echo esc_html($sw); ?></span>
                                <?php endforeach; ?>
                            </div>
                        </div>
                    <?php endif; ?>
                    <?php if (!empty($general_software_meta)) : ?>
                        <div class="mh-software-subsection">
                            <strong>General:</strong>
                            <div class="mh-tag-list">
                                <?php foreach ($general_software_meta as $sw) : ?>
                                    <span class="mh-tag general-software"><?php echo esc_html($sw); ?></span>
                                <?php endforeach; ?>
                            </div>
                        </div>
                    <?php endif; ?>
                </section>
                <?php endif; ?>

                <!-- Protocols -->
                <?php if (!empty($protocols)) : ?>
                <section class="mh-paper-section">
                    <h2>&#128203; Protocols</h2>
                    <div class="mh-protocol-list">
                        <?php foreach ($protocols as $protocol) : ?>
                            <a href="<?php echo esc_url($protocol['url'] ?? '#'); ?>" class="mh-protocol-item" target="_blank">
                                <span class="icon">&#128196;</span>
                                <span class="name"><?php echo esc_html($protocol['name'] ?? 'View Protocol'); ?></span>
                                <span class="source"><?php echo esc_html($protocol['source'] ?? 'protocols.io'); ?></span>
                            </a>
                        <?php endforeach; ?>
                    </div>
                </section>
                <?php endif; ?>

                <!-- GitHub / Code -->
                <?php if (!empty($github_tools) || $github_url) : ?>
                <section class="mh-paper-section">
                    <h2>&#128187; Code & Software</h2>

                    <?php if (!empty($github_tools)) : ?>
                    <div class="mh-github-tools-list">
                        <?php foreach ($github_tools as $tool) :
                            $tool_url = !empty($tool['url']) ? $tool['url'] : 'https://github.com/' . $tool['full_name'];
                            $health = intval($tool['health_score'] ?? 0);
                            $is_archived = !empty($tool['is_archived']);
                            if ($is_archived) { $health_class = 'archived'; $health_label = 'Archived'; }
                            elseif ($health >= 70) { $health_class = 'active'; $health_label = 'Active'; }
                            elseif ($health >= 40) { $health_class = 'moderate'; $health_label = 'Moderate'; }
                            elseif ($health > 0) { $health_class = 'low'; $health_label = 'Low Activity'; }
                            else { $health_class = 'unknown'; $health_label = ''; }

                            $rel = $tool['relationship'] ?? 'uses';
                            $rel_labels = array('introduces' => '&#127381; Introduced here', 'uses' => '&#128295; Used', 'extends' => '&#128256; Extended', 'benchmarks' => '&#128202; Benchmarked');
                            $rel_label = $rel_labels[$rel] ?? '&#128295; Used';
                        ?>
                        <a href="<?php echo esc_url($tool_url); ?>" class="mh-github-tool-card health-<?php echo $health_class; ?>" target="_blank" rel="noopener">
                            <div class="mh-ght-header">
                                <strong class="mh-ght-name"><?php echo esc_html($tool['full_name']); ?></strong>
                                <?php if ($health_label) : ?>
                                    <span class="mh-ght-health <?php echo $health_class; ?>"><?php echo $health_label; ?></span>
                                <?php endif; ?>
                            </div>
                            <?php if (!empty($tool['description'])) : ?>
                                <p class="mh-ght-desc"><?php echo esc_html(wp_trim_words($tool['description'], 20, '...')); ?></p>
                            <?php endif; ?>
                            <div class="mh-ght-metrics">
                                <span class="mh-ght-rel <?php echo esc_attr($rel); ?>"><?php echo $rel_label; ?></span>
                                <?php if (!empty($tool['stars'])) : ?>
                                    <span>&#11088; <?php echo number_format(intval($tool['stars'])); ?></span>
                                <?php endif; ?>
                                <?php if (!empty($tool['forks'])) : ?>
                                    <span>&#127860; <?php echo number_format(intval($tool['forks'])); ?></span>
                                <?php endif; ?>
                                <?php if (!empty($tool['language'])) : ?>
                                    <span>&#128221; <?php echo esc_html($tool['language']); ?></span>
                                <?php endif; ?>
                            </div>
                            <?php if (!empty($tool['topics']) && is_array($tool['topics'])) : ?>
                                <div class="mh-ght-topics">
                                    <?php foreach (array_slice($tool['topics'], 0, 5) as $topic) : ?>
                                        <span class="mh-ght-topic"><?php echo esc_html($topic); ?></span>
                                    <?php endforeach; ?>
                                </div>
                            <?php endif; ?>
                        </a>
                        <?php endforeach; ?>
                    </div>
                    <?php elseif ($github_url) : ?>
                    <a href="<?php echo esc_url($github_url); ?>" class="mh-github-card" target="_blank">
                        <span class="icon">&#128194;</span>
                        <div class="info">
                            <strong>GitHub Repository</strong>
                            <span><?php echo esc_html(preg_replace('/^https?:\/\/(www\.)?github\.com\//', '', $github_url)); ?></span>
                        </div>
                        <span class="arrow">&#8594;</span>
                    </a>
                    <?php endif; ?>
                </section>
                <?php endif; ?>

                <!-- Repositories -->
                <?php if (!empty($repos)) : ?>
                <section class="mh-paper-section">
                    <h2>&#128190; Data Repositories</h2>
                    <div class="mh-repo-list">
                        <?php foreach ($repos as $repo) :
                            $url = $repo['url'] ?? '#';

                            $repo_name = '';
                            if (!empty($repo['name']) && strtolower($repo['name']) !== 'unknown') {
                                $repo_name = $repo['name'];
                            } elseif (!empty($repo['type']) && strtolower($repo['type']) !== 'unknown') {
                                $repo_name = $repo['type'];
                            }

                            if (empty($repo_name) && $url && $url !== '#') {
                                if (strpos($url, 'zenodo') !== false) $repo_name = 'Zenodo';
                                elseif (strpos($url, 'figshare') !== false) $repo_name = 'Figshare';
                                elseif (strpos($url, 'github') !== false) $repo_name = 'GitHub';
                                elseif (strpos($url, 'dryad') !== false) $repo_name = 'Dryad';
                                elseif (strpos($url, 'osf.io') !== false) $repo_name = 'OSF';
                                elseif (strpos($url, 'dataverse') !== false) $repo_name = 'Dataverse';
                                elseif (strpos($url, 'mendeley') !== false) $repo_name = 'Mendeley Data';
                                elseif (strpos($url, 'synapse') !== false) $repo_name = 'Synapse';
                                elseif (strpos($url, 'ebi.ac.uk') !== false || strpos($url, 'empiar') !== false) $repo_name = 'EMPIAR';
                                elseif (strpos($url, 'ncbi') !== false || strpos($url, 'geo') !== false) $repo_name = 'GEO/NCBI';
                                else $repo_name = 'Data Repository';
                            }
                            if (empty($repo_name)) $repo_name = 'Data Repository';

                            $repo_id = '';
                            if (!empty($repo['identifier'])) $repo_id = $repo['identifier'];
                            elseif (!empty($repo['accession_id'])) $repo_id = $repo['accession_id'];
                            elseif (!empty($repo['id'])) $repo_id = $repo['id'];
                        ?>
                            <a href="<?php echo esc_url($url); ?>" class="mh-repo-item" target="_blank">
                                <span><?php echo esc_html($repo_name); ?></span>
                                <?php if ($repo_id) : ?>
                                    <span class="mh-repo-id"><?php echo esc_html($repo_id); ?></span>
                                <?php endif; ?>
                            </a>
                        <?php endforeach; ?>
                    </div>
                </section>
                <?php endif; ?>

                <!-- RRIDs with Links -->
                <?php if (!empty($rrids)) : ?>
                <section class="mh-paper-section">
                    <h2>&#127991;&#65039; Research Resource Identifiers (RRIDs)</h2>
                    <p class="mh-section-note">Verified research resources used in this paper:</p>
                    <div class="mh-rrids-list">
                        <?php foreach ($rrids as $rrid) :
                            $rrid_id = isset($rrid['id']) ? $rrid['id'] : (is_string($rrid) ? $rrid : '');
                            $rrid_name = isset($rrid['name']) ? $rrid['name'] : '';
                            $rrid_type = isset($rrid['type']) ? $rrid['type'] : '';
                            if (empty($rrid_id)) continue;
                        ?>
                            <div class="mh-rrid-item">
                                <a href="https://scicrunch.org/resolver/<?php echo esc_attr($rrid_id); ?>" target="_blank" rel="noopener" class="mh-rrid-link">
                                    <?php echo esc_html($rrid_id); ?>
                                </a>
                                <?php if ($rrid_name) : ?>
                                    <span class="mh-rrid-name"><?php echo esc_html($rrid_name); ?></span>
                                <?php elseif ($rrid_type) : ?>
                                    <span class="mh-rrid-name"><?php echo esc_html($rrid_type); ?></span>
                                <?php endif; ?>
                            </div>
                        <?php endforeach; ?>
                    </div>
                </section>
                <?php endif; ?>

                <!-- RORs with Links -->
                <?php if (!empty($rors)) : ?>
                <section class="mh-paper-section">
                    <h2>&#127963;&#65039; Research Organizations (ROR)</h2>
                    <p class="mh-section-note">Affiliated research institutions:</p>
                    <div class="mh-ror-list">
                        <?php foreach ($rors as $ror) :
                            $ror_id = is_array($ror) ? ($ror['id'] ?? '') : $ror;
                            $ror_name = is_array($ror) ? ($ror['name'] ?? '') : '';
                            $ror_url = is_array($ror) ? ($ror['url'] ?? 'https://ror.org/' . $ror_id) : 'https://ror.org/' . $ror;
                            if (empty($ror_id)) continue;
                        ?>
                            <a href="<?php echo esc_url($ror_url); ?>" class="mh-ror-item" target="_blank" rel="noopener">
                                <span class="ror-icon">&#127963;</span>
                                <span class="ror-id"><?php echo esc_html($ror_name ? $ror_name : $ror_id); ?></span>
                            </a>
                        <?php endforeach; ?>
                    </div>
                </section>
                <?php endif; ?>

                <!-- References -->
                <?php if (!empty($references)) : ?>
                <section class="mh-paper-section mh-references-section">
                    <h2>&#128218; References</h2>
                    <ol class="mh-reference-list">
                        <?php foreach ($references as $idx => $ref) :
                            $num = isset($ref['num']) ? $ref['num'] : ($idx + 1);
                            $text = isset($ref['text']) ? $ref['text'] : '';
                            $ref_doi = isset($ref['doi']) ? $ref['doi'] : '';
                            $pmid = isset($ref['pmid']) ? $ref['pmid'] : '';
                            $url = isset($ref['url']) ? $ref['url'] : '';

                            $link = '';
                            if ($ref_doi) {
                                $link = 'https://doi.org/' . $ref_doi;
                            } elseif ($pmid) {
                                $link = 'https://pubmed.ncbi.nlm.nih.gov/' . $pmid;
                            } elseif ($url) {
                                $link = $url;
                            }
                        ?>
                            <li id="ref-<?php echo esc_attr($num); ?>" class="mh-reference-item">
                                <span class="mh-ref-text"><?php echo esc_html($text); ?></span>
                                <?php if ($link) : ?>
                                    <a href="<?php echo esc_url($link); ?>" class="mh-ref-external-link" target="_blank" rel="noopener">
                                        <?php if ($ref_doi) : ?>
                                            <span class="mh-ref-doi">DOI</span>
                                        <?php elseif ($pmid) : ?>
                                            <span class="mh-ref-pmid">PubMed</span>
                                        <?php else : ?>
                                            <span>&#128279;</span>
                                        <?php endif; ?>
                                    </a>
                                <?php endif; ?>
                            </li>
                        <?php endforeach; ?>
                    </ol>
                </section>
                <?php endif; ?>

                <!-- Facility -->
                <?php if ($facility) : ?>
                <section class="mh-paper-section">
                    <h2>&#127963;&#65039; Imaging Facility</h2>
                    <div class="mh-facility-card">
                        <span class="icon">&#127963;&#65039;</span>
                        <span class="name"><?php echo esc_html($facility); ?></span>
                    </div>
                </section>
                <?php endif; ?>

                <!-- Comments Section -->
                <section class="mh-paper-section mh-comments-section">
                    <div class="mh-comments-header">
                        <h2>&#128172; Discussion</h2>
                        <span class="mh-comments-count"><?php echo get_comments_number(); ?> comments</span>
                    </div>

                    <?php if (comments_open()) : ?>
                        <div class="mh-comments-list">
                            <?php
                            $comments = get_comments(array(
                                'post_id' => $post_id,
                                'status' => 'approve',
                                'order' => 'ASC',
                            ));

                            if ($comments) :
                                foreach ($comments as $comment) :
                                    $initials = strtoupper(substr($comment->comment_author, 0, 2));
                            ?>
                                <div class="mh-comment">
                                    <div class="mh-comment-avatar"><?php echo $initials; ?></div>
                                    <div class="mh-comment-content">
                                        <div class="mh-comment-meta">
                                            <span class="mh-comment-author"><?php echo esc_html($comment->comment_author); ?></span>
                                            <span class="mh-comment-date"><?php echo human_time_diff(strtotime($comment->comment_date), current_time('timestamp')); ?> ago</span>
                                        </div>
                                        <div class="mh-comment-text"><?php echo wpautop(esc_html($comment->comment_content)); ?></div>
                                    </div>
                                </div>
                            <?php
                                endforeach;
                            else :
                            ?>
                                <p class="mh-no-comments">No comments yet. Be the first to start a discussion!</p>
                            <?php endif; ?>
                        </div>

                        <div class="mh-comment-form">
                            <h4>Leave a Comment</h4>
                            <form method="post" action="<?php echo site_url('/wp-comments-post.php'); ?>">
                                <?php if (!is_user_logged_in()) : ?>
                                    <div class="mh-form-row">
                                        <div class="mh-form-group">
                                            <label for="author">Your Name <span class="required">*</span></label>
                                            <input type="text" name="author" id="author" required placeholder="Enter your name">
                                        </div>
                                        <div class="mh-form-group">
                                            <label for="email">Email <span class="optional">(optional)</span></label>
                                            <input type="email" name="email" id="email" placeholder="For notifications only">
                                        </div>
                                    </div>
                                <?php else :
                                    $current_user = wp_get_current_user();
                                ?>
                                    <p class="mh-logged-in-as">
                                        Commenting as <strong><?php echo esc_html($current_user->display_name); ?></strong>
                                    </p>
                                <?php endif; ?>

                                <div class="mh-form-group">
                                    <label for="comment">Your Comment <span class="required">*</span></label>
                                    <textarea name="comment" id="comment" rows="4" required placeholder="Share your thoughts about this paper..."></textarea>
                                </div>

                                <input type="hidden" name="comment_post_ID" value="<?php echo $post_id; ?>" />
                                <?php wp_nonce_field('unfiltered-html-comment'); ?>
                                <button type="submit" class="mh-submit-btn">Post Comment</button>
                            </form>
                        </div>
                    <?php endif; ?>
                </section>
            </div>

            <!-- Sidebar -->
            <aside class="mh-paper-sidebar">
                <!-- Related Papers - scored by shared tag count across ALL taxonomies -->
                <div class="mh-sidebar-widget">
                    <h3>Related Papers</h3>
                    <?php
                    // Collect all term IDs across ALL taxonomies for scoring
                    $all_taxonomies_for_related = array(
                        'mh_technique', 'mh_microscope', 'mh_organism', 'mh_software',
                        'mh_fluorophore', 'mh_sample_prep', 'mh_cell_line',
                        'mh_microscope_model', 'mh_analysis_software', 'mh_acquisition_software',
                        'mh_facility',
                    );
                    $current_term_ids = array();
                    $tax_queries = array();
                    foreach ($all_taxonomies_for_related as $tax_name) {
                        $t = wp_get_post_terms($post_id, $tax_name, array('fields' => 'ids'));
                        if (!is_wp_error($t) && !empty($t)) {
                            $current_term_ids[$tax_name] = $t;
                            $tax_queries[] = array(
                                'taxonomy' => $tax_name,
                                'terms' => $t,
                            );
                        }
                    }

                    if (!empty($tax_queries)) :
                        // Query candidate related papers (any shared taxonomy)
                        $tax_queries['relation'] = 'OR';
                        $candidates = new WP_Query(array(
                            'post_type' => array('mh_paper', 'mh_protocol'),
                            'posts_per_page' => 30,
                            'post__not_in' => array($post_id),
                            'tax_query' => $tax_queries,
                            'fields' => 'ids',
                        ));

                        // Score each candidate by counting shared terms
                        $scored = array();
                        if ($candidates->have_posts()) {
                            foreach ($candidates->posts as $cand_id) {
                                $score = 0;
                                foreach ($current_term_ids as $tax_name => $term_ids) {
                                    $cand_terms = wp_get_post_terms($cand_id, $tax_name, array('fields' => 'ids'));
                                    if (!is_wp_error($cand_terms)) {
                                        $score += count(array_intersect($term_ids, $cand_terms));
                                    }
                                }
                                $scored[$cand_id] = $score;
                            }
                            arsort($scored);
                        }
                        wp_reset_postdata();

                        // Display top 5
                        $top_ids = array_slice(array_keys($scored), 0, 5, true);
                        if (!empty($top_ids)) :
                            foreach ($top_ids as $rel_id) :
                                $rel_post = get_post($rel_id);
                                if (!$rel_post) continue;
                                $match_count = $scored[$rel_id];
                    ?>
                        <a href="<?php echo get_permalink($rel_id); ?>" class="mh-related-item">
                            <?php echo esc_html(wp_trim_words($rel_post->post_title, 10)); ?>
                            <span class="mh-related-score"><?php echo intval($match_count); ?> shared tags</span>
                        </a>
                    <?php
                            endforeach;
                        else :
                    ?>
                        <p style="color: #8b949e; font-size: 0.85rem;">No related papers found.</p>
                    <?php
                        endif;
                    else :
                    ?>
                        <p style="color: #8b949e; font-size: 0.85rem;">No related papers found.</p>
                    <?php endif; ?>
                </div>

                <!-- Organisms sidebar -->
                <?php if (!empty($organisms)) : ?>
                <div class="mh-sidebar-widget">
                    <h3>&#129516; Organisms</h3>
                    <div class="mh-tag-list">
                        <?php foreach ($organisms as $term) : ?>
                            <a href="<?php echo esc_url(get_term_link($term)); ?>" class="mh-tag organism"><?php echo esc_html($term->name); ?></a>
                        <?php endforeach; ?>
                    </div>
                </div>
                <?php endif; ?>

                <!-- Microscopes sidebar -->
                <?php if (!empty($microscopes)) : ?>
                <div class="mh-sidebar-widget">
                    <h3>&#128301; Microscopes</h3>
                    <div class="mh-tag-list">
                        <?php foreach ($microscopes as $term) : ?>
                            <a href="<?php echo esc_url(get_term_link($term)); ?>" class="mh-tag microscope"><?php echo esc_html($term->name); ?></a>
                        <?php endforeach; ?>
                    </div>
                </div>
                <?php endif; ?>

                <!-- Software sidebar -->
                <?php if (!empty($software)) : ?>
                <div class="mh-sidebar-widget">
                    <h3>&#128187; Software</h3>
                    <div class="mh-tag-list">
                        <?php foreach ($software as $term) : ?>
                            <a href="<?php echo esc_url(get_term_link($term)); ?>" class="mh-tag software"><?php echo esc_html($term->name); ?></a>
                        <?php endforeach; ?>
                    </div>
                </div>
                <?php endif; ?>

                <!-- RRIDs sidebar with links -->
                <?php if (!empty($rrids)) : ?>
                <div class="mh-sidebar-widget">
                    <h3>&#127991;&#65039; Resources (RRIDs)</h3>
                    <div class="mh-rrid-list">
                        <?php foreach ($rrids as $rrid) :
                            $rrid_id = isset($rrid['id']) ? $rrid['id'] : (is_string($rrid) ? $rrid : '');
                            $rrid_type = isset($rrid['type']) ? $rrid['type'] : '';
                            $rrid_name = isset($rrid['name']) ? $rrid['name'] : '';
                            if (empty($rrid_id)) continue;
                        ?>
                            <div class="mh-rrid-item">
                                <span class="type"><?php echo esc_html($rrid_type ? $rrid_type : 'Resource'); ?></span>
                                <a href="https://scicrunch.org/resolver/<?php echo esc_attr($rrid_id); ?>" target="_blank" rel="noopener" class="mh-rrid-link">
                                    <?php echo esc_html($rrid_id); ?>
                                </a>
                                <?php if ($rrid_name) : ?>
                                    <span class="mh-rrid-name"><?php echo esc_html($rrid_name); ?></span>
                                <?php endif; ?>
                            </div>
                        <?php endforeach; ?>
                    </div>
                </div>
                <?php endif; ?>

                <!-- RORs sidebar -->
                <?php if (!empty($rors)) : ?>
                <div class="mh-sidebar-widget">
                    <h3>&#127963;&#65039; Research Organizations (ROR)</h3>
                    <div class="mh-ror-list">
                        <?php foreach ($rors as $ror) :
                            $ror_id = is_array($ror) ? ($ror['id'] ?? '') : $ror;
                            $ror_name = is_array($ror) ? ($ror['name'] ?? '') : '';
                            $ror_url = is_array($ror) ? ($ror['url'] ?? 'https://ror.org/' . $ror_id) : 'https://ror.org/' . $ror;
                            if ($ror_id) :
                        ?>
                            <a href="<?php echo esc_url($ror_url); ?>" class="mh-ror-item" target="_blank" rel="noopener">
                                <span class="ror-icon">&#127963;</span>
                                <span class="ror-id"><?php echo esc_html($ror_name ? $ror_name : $ror_id); ?></span>
                            </a>
                        <?php endif; endforeach; ?>
                    </div>
                </div>
                <?php endif; ?>

                <!-- Fluorophores sidebar -->
                <?php
                $sidebar_fluorophores = !empty($fluorophores_tax) ? $fluorophores_tax : null;
                if ($sidebar_fluorophores) :
                ?>
                <div class="mh-sidebar-widget">
                    <h3>&#10024; Fluorophores</h3>
                    <div class="mh-tag-list">
                        <?php foreach ($sidebar_fluorophores as $term) : ?>
                            <a href="<?php echo esc_url(get_term_link($term)); ?>" class="mh-tag fluorophore"><?php echo esc_html($term->name); ?></a>
                        <?php endforeach; ?>
                    </div>
                </div>
                <?php elseif (!empty($fluorophores_meta)) : ?>
                <div class="mh-sidebar-widget">
                    <h3>&#10024; Fluorophores</h3>
                    <div class="mh-tag-list">
                        <?php foreach ($fluorophores_meta as $fluor) : ?>
                            <span class="mh-tag fluorophore"><?php echo esc_html($fluor); ?></span>
                        <?php endforeach; ?>
                    </div>
                </div>
                <?php endif; ?>

                <!-- Cell Lines sidebar -->
                <?php if (!empty($cell_lines_tax)) : ?>
                <div class="mh-sidebar-widget">
                    <h3>&#129514; Cell Lines</h3>
                    <div class="mh-tag-list">
                        <?php foreach ($cell_lines_tax as $term) : ?>
                            <a href="<?php echo esc_url(get_term_link($term)); ?>" class="mh-tag cell-line"><?php echo esc_html($term->name); ?></a>
                        <?php endforeach; ?>
                    </div>
                </div>
                <?php elseif (!empty($cell_lines_meta)) : ?>
                <div class="mh-sidebar-widget">
                    <h3>&#129514; Cell Lines</h3>
                    <div class="mh-tag-list">
                        <?php foreach ($cell_lines_meta as $cell) : ?>
                            <span class="mh-tag cell-line"><?php echo esc_html($cell); ?></span>
                        <?php endforeach; ?>
                    </div>
                </div>
                <?php endif; ?>

                <!-- Sample Preparation sidebar -->
                <?php if (!empty($sample_prep_tax)) : ?>
                <div class="mh-sidebar-widget">
                    <h3>&#129514; Sample Preparation</h3>
                    <div class="mh-tag-list">
                        <?php foreach ($sample_prep_tax as $term) : ?>
                            <a href="<?php echo esc_url(get_term_link($term)); ?>" class="mh-tag sample-prep"><?php echo esc_html($term->name); ?></a>
                        <?php endforeach; ?>
                    </div>
                </div>
                <?php elseif (!empty($sample_preparation_meta)) : ?>
                <div class="mh-sidebar-widget">
                    <h3>&#129514; Sample Preparation</h3>
                    <div class="mh-tag-list">
                        <?php foreach ($sample_preparation_meta as $prep) : ?>
                            <span class="mh-tag sample-prep"><?php echo esc_html($prep); ?></span>
                        <?php endforeach; ?>
                    </div>
                </div>
                <?php endif; ?>
            </aside>
        </div>
    </article>

<style>
/* Single Paper Styles */
.mh-single-paper {
    max-width: 1400px;
    margin: 0 auto;
}

.mh-paper-header {
    background: linear-gradient(135deg, #161b22 0%, #0d1117 100%);
    padding: 40px 24px;
    border-bottom: 1px solid #30363d;
}

.mh-paper-header-inner {
    max-width: 900px;
}

.mh-paper-header h1 {
    color: #e6edf3;
    font-size: 1.75rem;
    line-height: 1.3;
    margin: 10px 0;
}

.mh-paper-authors {
    color: #8b949e;
    font-size: 0.95rem;
    margin-bottom: 16px;
}

.mh-paper-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 16px;
    margin-bottom: 20px;
}

.mh-meta-item {
    color: #8b949e;
    font-size: 0.9rem;
}

.mh-paper-links {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
}

.mh-btn {
    padding: 8px 16px;
    border-radius: 6px;
    font-size: 0.85rem;
    font-weight: 600;
    text-transform: uppercase;
}

.mh-btn.doi { background: rgba(63, 185, 80, 0.15); color: #3fb950; }
.mh-btn.pubmed { background: rgba(88, 166, 255, 0.15); color: #58a6ff; }
.mh-btn.pdf { background: rgba(247, 129, 102, 0.15); color: #f78166; }
.mh-btn.github { background: rgba(110, 118, 129, 0.15); color: #e6edf3; }

.mh-paper-content {
    display: grid;
    grid-template-columns: 1fr 320px;
    gap: 24px;
    padding: 24px;
    background: #0d1117;
}

.mh-paper-section {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 20px;
}

.mh-paper-section h2 {
    color: #e6edf3;
    font-size: 1.1rem;
    margin: 0 0 16px 0;
    padding-bottom: 10px;
    border-bottom: 1px solid #30363d;
}

.mh-paper-section p {
    color: #8b949e;
    line-height: 1.6;
}

.mh-section-note {
    color: #8b949e;
    font-size: 0.9rem;
    margin-bottom: 12px;
}

.mh-tag-list {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}

.mh-tag {
    display: inline-block;
    padding: 6px 12px;
    border-radius: 6px;
    font-size: 0.85rem;
    text-decoration: none;
    transition: all 0.2s;
}

.mh-tag.technique { background: #1e3a5f; color: #58a6ff; }
.mh-tag.microscope { background: #3d2f1f; color: #f0883e; }
.mh-tag.organism { background: #1f3d2d; color: #56d364; }
.mh-tag.software { background: #2d1f3d; color: #a371f7; }
.mh-tag.fluorophore { background: #3d1f2d; color: #f778ba; }
.mh-tag.sample-prep { background: #2d3d1f; color: #a5d6a7; }
.mh-tag.cell-line { background: #3d3d1f; color: #d4a72c; }
.mh-tag.brand { background: #475569; color: #e2e8f0; }
.mh-tag.supplier { background: #4a3728; color: #ffb86c; }
.mh-tag.general-software { background: #2d2d3d; color: #bd93f9; }
.mh-tag:hover {
    filter: brightness(1.2);
}

.mh-software-subsection {
    margin-bottom: 0.75rem;
}
.mh-software-subsection:last-child {
    margin-bottom: 0;
}
.mh-software-subsection strong {
    display: block;
    margin-bottom: 0.5rem;
    color: #8b949e;
    font-size: 0.85rem;
}

.mh-protocol-list, .mh-repo-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.mh-protocol-item, .mh-repo-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px;
    background: #21262d;
    border-radius: 6px;
    color: #e6edf3;
    transition: all 0.2s;
}

.mh-protocol-item:hover, .mh-repo-item:hover {
    background: #30363d;
}

.mh-github-card {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 16px;
    background: #21262d;
    border-radius: 8px;
    color: #e6edf3;
    transition: all 0.2s;
}

.mh-github-card:hover {
    background: #30363d;
}

.mh-github-card .icon {
    font-size: 2rem;
}

.mh-github-card .info {
    flex: 1;
}

.mh-github-card .info strong {
    display: block;
    margin-bottom: 4px;
}

.mh-github-card .info span {
    color: #8b949e;
    font-size: 0.85rem;
}

/* GitHub Tools Cards */
.mh-github-tools-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
}
.mh-github-tool-card {
    display: block;
    padding: 16px;
    background: #21262d;
    border: 1px solid #30363d;
    border-left: 4px solid #30363d;
    border-radius: 8px;
    color: #e6edf3;
    text-decoration: none;
    transition: all 0.2s;
}
.mh-github-tool-card:hover {
    background: #30363d;
    border-color: var(--primary, #58a6ff);
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
}
.mh-github-tool-card.health-active { border-left-color: #3fb950; }
.mh-github-tool-card.health-moderate { border-left-color: #d29922; }
.mh-github-tool-card.health-low { border-left-color: #f85149; }
.mh-github-tool-card.health-archived { border-left-color: #6e7681; opacity: 0.8; }
.mh-ght-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    margin-bottom: 6px;
}
.mh-ght-name { font-size: 1rem; color: #58a6ff; word-break: break-word; }
.mh-ght-health {
    font-size: 0.68rem; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.5px; padding: 3px 10px; border-radius: 12px;
    white-space: nowrap; flex-shrink: 0;
}
.mh-ght-health.active { background: rgba(63, 185, 80, 0.15); color: #3fb950; }
.mh-ght-health.moderate { background: rgba(210, 153, 34, 0.15); color: #d29922; }
.mh-ght-health.low { background: rgba(248, 81, 73, 0.15); color: #f85149; }
.mh-ght-health.archived { background: rgba(110, 118, 129, 0.15); color: #6e7681; }
.mh-ght-desc { font-size: 0.85rem; color: #8b949e; margin: 0 0 8px; line-height: 1.4; }
.mh-ght-metrics { display: flex; flex-wrap: wrap; gap: 10px; font-size: 0.8rem; color: #8b949e; margin-bottom: 8px; }
.mh-ght-rel { font-weight: 600; padding: 1px 8px; border-radius: 8px; font-size: 0.72rem; }
.mh-ght-rel.introduces { background: rgba(163, 113, 247, 0.15); color: #a371f7; }
.mh-ght-rel.uses { background: rgba(88, 166, 255, 0.1); color: #58a6ff; }
.mh-ght-rel.extends { background: rgba(35, 134, 54, 0.15); color: #3fb950; }
.mh-ght-rel.benchmarks { background: rgba(210, 153, 34, 0.1); color: #d29922; }
.mh-ght-topics { display: flex; flex-wrap: wrap; gap: 4px; }
.mh-ght-topic {
    font-size: 0.7rem; background: rgba(88, 166, 255, 0.08); color: #58a6ff;
    padding: 1px 8px; border-radius: 10px; border: 1px solid rgba(88, 166, 255, 0.2);
}

.mh-facility-card {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px;
    background: #21262d;
    border-radius: 6px;
    color: #e6edf3;
}

/* RRIDs */
.mh-rrids-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
}
.mh-rrid-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 14px;
    background: #21262d;
    border-radius: 6px;
}
.mh-rrid-link {
    color: #a371f7;
    font-family: 'SFMono-Regular', Consolas, monospace;
    font-size: 0.85rem;
    text-decoration: none;
}
.mh-rrid-link:hover {
    text-decoration: underline;
    color: #c9a0ff;
}
.mh-rrid-name {
    color: #8b949e;
    font-size: 0.85rem;
}
.mh-rrid-item .type {
    color: #8b949e;
    display: block;
    font-size: 0.75rem;
}

/* RORs */
.mh-ror-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
}
.mh-ror-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 12px;
    background: linear-gradient(135deg, #1a365d 0%, #2c5282 100%);
    border-radius: 8px;
    color: #bee3f8;
    text-decoration: none;
    font-size: 0.85rem;
    transition: all 0.2s ease;
    border: 1px solid #2b6cb0;
}
.mh-ror-item:hover {
    background: linear-gradient(135deg, #2c5282 0%, #3182ce 100%);
    color: #fff;
    transform: translateX(4px);
}
.mh-ror-item .ror-icon {
    font-size: 1rem;
}
.mh-ror-item .ror-id {
    font-family: 'SFMono-Regular', Consolas, monospace;
    font-size: 0.8rem;
}

/* Comments */
.mh-comments-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    padding-bottom: 10px;
    border-bottom: 1px solid #30363d;
}

.mh-comments-count {
    background: #58a6ff;
    color: white;
    padding: 2px 10px;
    border-radius: 10px;
    font-size: 0.8rem;
}

.mh-comment {
    display: flex;
    gap: 12px;
    padding: 16px;
    background: #0d1117;
    border-radius: 8px;
    margin-bottom: 12px;
}

.mh-comment-avatar {
    width: 40px;
    height: 40px;
    background: linear-gradient(135deg, #58a6ff, #a371f7);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: 600;
    font-size: 0.85rem;
    flex-shrink: 0;
}

.mh-comment-content {
    flex: 1;
}

.mh-comment-meta {
    display: flex;
    gap: 10px;
    margin-bottom: 6px;
}

.mh-comment-author {
    font-weight: 600;
    color: #e6edf3;
    font-size: 0.9rem;
}

.mh-comment-date {
    font-size: 0.8rem;
    color: #8b949e;
}

.mh-comment-text {
    color: #8b949e;
    font-size: 0.9rem;
    line-height: 1.5;
}

.mh-comment-form textarea {
    width: 100%;
    padding: 12px;
    border: 1px solid #30363d;
    border-radius: 8px;
    background: #0d1117;
    color: #e6edf3;
    font-size: 0.9rem;
    resize: vertical;
    min-height: 80px;
    margin-bottom: 10px;
}

.mh-comment-form button {
    padding: 8px 20px;
    background: #58a6ff;
    border: none;
    border-radius: 6px;
    color: white;
    font-weight: 600;
    cursor: pointer;
}

.mh-no-comments {
    color: #8b949e;
    font-size: 0.9rem;
    text-align: center;
    padding: 20px;
}

/* Sidebar */
.mh-paper-sidebar {
    display: flex;
    flex-direction: column;
    gap: 16px;
}

.mh-sidebar-widget {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 16px;
}

.mh-sidebar-widget h3 {
    color: #e6edf3;
    font-size: 0.9rem;
    margin: 0 0 12px 0;
    padding-bottom: 8px;
    border-bottom: 1px solid #30363d;
}

.mh-related-item {
    display: block;
    padding: 8px;
    color: #58a6ff;
    font-size: 0.85rem;
    border-bottom: 1px solid #21262d;
}

.mh-related-item:hover {
    background: #21262d;
}

.mh-related-score {
    display: block;
    font-size: 0.7rem;
    color: #8b949e;
    margin-top: 2px;
}

.mh-rrid-list .mh-rrid-item {
    padding: 8px;
    background: #21262d;
    border-radius: 6px;
    margin-bottom: 8px;
    font-size: 0.85rem;
}

@media (max-width: 900px) {
    .mh-paper-content {
        grid-template-columns: 1fr;
    }
}
</style>

<?php get_footer(); ?>
