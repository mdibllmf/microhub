<?php
/**
 * Single Protocol Template v4.2
 * Matches the paper template structure exactly
 */
get_header();

$post_id = get_the_ID();
$doi = get_post_meta($post_id, '_mh_doi', true);
$pubmed_id = get_post_meta($post_id, '_mh_pubmed_id', true);
$pmc_id = get_post_meta($post_id, '_mh_pmc_id', true);
$authors = get_post_meta($post_id, '_mh_authors', true);
$journal = get_post_meta($post_id, '_mh_journal', true);
$year = get_post_meta($post_id, '_mh_publication_year', true);
if (!$year) $year = get_post_meta($post_id, '_mh_year', true);
$citations = get_post_meta($post_id, '_mh_citation_count', true);
$abstract = get_post_meta($post_id, '_mh_abstract', true);
$pdf_url = get_post_meta($post_id, '_mh_pdf_url', true);
$github_url = get_post_meta($post_id, '_mh_github_url', true);
$facility = get_post_meta($post_id, '_mh_facility', true);

// URL meta fields
$doi_url = get_post_meta($post_id, '_mh_doi_url', true);
$pubmed_url = get_post_meta($post_id, '_mh_pubmed_url', true);
$pmc_url = get_post_meta($post_id, '_mh_pmc_url', true);

// Generate URLs if not stored
if ($doi && !$doi_url) $doi_url = 'https://doi.org/' . $doi;
if ($pubmed_id && !$pubmed_url) $pubmed_url = 'https://pubmed.ncbi.nlm.nih.gov/' . $pubmed_id . '/';
if ($pmc_id && !$pmc_url) {
    $pmc_clean = str_replace('PMC', '', strtoupper($pmc_id));
    $pmc_url = 'https://www.ncbi.nlm.nih.gov/pmc/articles/PMC' . $pmc_clean . '/';
}

// Protocol-specific fields
$protocol_type = get_post_meta($post_id, '_mh_protocol_type', true);
if (empty($protocol_type)) {
    $protocol_type_terms = wp_get_object_terms($post_id, 'mh_protocol_type', array('fields' => 'names'));
    if (!is_wp_error($protocol_type_terms) && !empty($protocol_type_terms)) {
        $protocol_type = $protocol_type_terms[0];
    }
}
$protocol_url = get_post_meta($post_id, '_mh_protocol_url', true);

// JSON data
$protocols = json_decode(get_post_meta($post_id, '_mh_protocols', true), true) ?: array();
$repos = json_decode(get_post_meta($post_id, '_mh_repositories', true), true) ?: array();
$rrids = json_decode(get_post_meta($post_id, '_mh_rrids', true), true) ?: array();
$rors = json_decode(get_post_meta($post_id, '_mh_rors', true), true) ?: array();
$references = json_decode(get_post_meta($post_id, '_mh_references', true), true) ?: array();
$fluorophores = json_decode(get_post_meta($post_id, '_mh_fluorophores', true), true) ?: array();
$cell_lines = json_decode(get_post_meta($post_id, '_mh_cell_lines', true), true) ?: array();
$sample_prep = json_decode(get_post_meta($post_id, '_mh_sample_preparation', true), true) ?: array();
$microscope_brands = json_decode(get_post_meta($post_id, '_mh_microscope_brands', true), true) ?: array();
$microscope_models = json_decode(get_post_meta($post_id, '_mh_microscope_models', true), true) ?: array();
$institutions = json_decode(get_post_meta($post_id, '_mh_institutions', true), true) ?: array();
$image_analysis_sw = json_decode(get_post_meta($post_id, '_mh_image_analysis_software', true), true) ?: array();
$image_acquisition_sw = json_decode(get_post_meta($post_id, '_mh_image_acquisition_software', true), true) ?: array();

// Taxonomies
$techniques = wp_get_post_terms($post_id, 'mh_technique', array('fields' => 'all'));
$microscopes = wp_get_post_terms($post_id, 'mh_microscope', array('fields' => 'all'));
$organisms = wp_get_post_terms($post_id, 'mh_organism', array('fields' => 'all'));
$software_tax = wp_get_post_terms($post_id, 'mh_software', array('fields' => 'all'));
$analysis_sw_tax = wp_get_post_terms($post_id, 'mh_analysis_software', array('fields' => 'all'));
$acquisition_sw_tax = wp_get_post_terms($post_id, 'mh_acquisition_software', array('fields' => 'all'));
$fluorophores_tax = wp_get_post_terms($post_id, 'mh_fluorophore', array('fields' => 'all'));
$cell_lines_tax = wp_get_post_terms($post_id, 'mh_cell_line', array('fields' => 'all'));
$sample_prep_tax = wp_get_post_terms($post_id, 'mh_sample_prep', array('fields' => 'all'));
$facilities_tax = wp_get_post_terms($post_id, 'mh_facility', array('fields' => 'all'));
?>

<div class="microhub-wrapper">
    <?php if (function_exists('mh_render_nav')) echo mh_render_nav(); ?>
    <article class="mh-single-paper mh-single-protocol">
        <!-- Header -->
        <header class="mh-paper-header">
            <div class="mh-paper-header-inner">
                <?php if ($protocol_type): ?>
                    <span class="mh-badge protocol-type"><?php echo esc_html($protocol_type); ?></span>
                <?php endif; ?>

                <?php if ($citations >= 100) : ?>
                    <span class="mh-badge foundational">Foundational</span>
                <?php elseif ($citations >= 50) : ?>
                    <span class="mh-badge high-impact">High Impact</span>
                <?php endif; ?>

                <h1><?php the_title(); ?></h1>

                <?php if ($authors) : ?>
                    <p class="mh-paper-authors"><?php echo esc_html($authors); ?></p>
                <?php endif; ?>

                <div class="mh-paper-meta">
                    <?php if ($journal) : ?>
                        <span class="mh-meta-item"><?php echo esc_html($journal); ?></span>
                    <?php endif; ?>
                    <?php if ($year) : ?>
                        <span class="mh-meta-item"><?php echo esc_html($year); ?></span>
                    <?php endif; ?>
                    <?php if ($citations) : ?>
                        <span class="mh-meta-item"><?php echo number_format($citations); ?> citations</span>
                    <?php endif; ?>
                </div>

                <div class="mh-paper-links">
                    <?php if ($doi_url) : ?>
                        <a href="<?php echo esc_url($doi_url); ?>" class="mh-btn doi" target="_blank">DOI</a>
                    <?php endif; ?>
                    <?php if ($pubmed_url) : ?>
                        <a href="<?php echo esc_url($pubmed_url); ?>" class="mh-btn pubmed" target="_blank">PubMed</a>
                    <?php endif; ?>
                    <?php if ($pmc_url) : ?>
                        <a href="<?php echo esc_url($pmc_url); ?>" class="mh-btn pmc" target="_blank">PMC</a>
                    <?php endif; ?>
                    <?php if ($pdf_url) : ?>
                        <a href="<?php echo esc_url($pdf_url); ?>" class="mh-btn pdf" target="_blank">PDF</a>
                    <?php endif; ?>
                    <?php if ($github_url) : ?>
                        <a href="<?php echo esc_url($github_url); ?>" class="mh-btn github" target="_blank">GitHub</a>
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
                <?php elseif (get_the_content()) : ?>
                <section class="mh-paper-section">
                    <h2>Description</h2>
                    <div><?php the_content(); ?></div>
                </section>
                <?php endif; ?>

                <!-- Techniques -->
                <?php if (!empty($techniques) && !is_wp_error($techniques)) : ?>
                <section class="mh-paper-section">
                    <h2>Techniques</h2>
                    <div class="mh-tags-grid">
                        <?php foreach ($techniques as $term) : ?>
                            <a href="<?php echo esc_url(get_term_link($term)); ?>" class="mh-tag technique"><?php echo esc_html($term->name); ?></a>
                        <?php endforeach; ?>
                    </div>
                </section>
                <?php endif; ?>

                <!-- Protocols -->
                <?php if (!empty($protocols)) : ?>
                <section class="mh-paper-section" id="protocols">
                    <h2>Protocols</h2>
                    <div class="mh-protocol-list">
                        <?php foreach ($protocols as $protocol) : ?>
                            <a href="<?php echo esc_url($protocol['url'] ?? '#'); ?>" class="mh-protocol-item" target="_blank">
                                <span class="name"><?php echo esc_html($protocol['name'] ?? 'View Protocol'); ?></span>
                                <span class="source"><?php echo esc_html($protocol['source'] ?? ''); ?></span>
                            </a>
                        <?php endforeach; ?>
                    </div>
                </section>
                <?php endif; ?>

                <!-- GitHub -->
                <?php if ($github_url) : ?>
                <section class="mh-paper-section">
                    <h2>Code & Data</h2>
                    <a href="<?php echo esc_url($github_url); ?>" class="mh-github-card" target="_blank">
                        <div class="info">
                            <strong>GitHub Repository</strong>
                            <span><?php echo esc_html(preg_replace('/^https?:\/\/(www\.)?github\.com\//', '', $github_url)); ?></span>
                        </div>
                    </a>
                </section>
                <?php endif; ?>

                <!-- Repositories -->
                <?php if (!empty($repos)) : ?>
                <section class="mh-paper-section">
                    <h2>Data Repositories</h2>
                    <div class="mh-repo-list">
                        <?php foreach ($repos as $repo) :
                            $url = $repo['url'] ?? '#';
                            $repo_name = $repo['name'] ?? $repo['type'] ?? '';
                            if (empty($repo_name) && $url !== '#') {
                                if (strpos($url, 'zenodo') !== false) $repo_name = 'Zenodo';
                                elseif (strpos($url, 'figshare') !== false) $repo_name = 'Figshare';
                                elseif (strpos($url, 'github') !== false) $repo_name = 'GitHub';
                                elseif (strpos($url, 'dryad') !== false) $repo_name = 'Dryad';
                                elseif (strpos($url, 'osf.io') !== false) $repo_name = 'OSF';
                                else $repo_name = 'Data Repository';
                            }
                            $repo_id = $repo['identifier'] ?? $repo['accession_id'] ?? $repo['id'] ?? '';
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

                <!-- RRIDs -->
                <?php if (!empty($rrids)) : ?>
                <section class="mh-paper-section">
                    <h2>Research Resource Identifiers (RRIDs)</h2>
                    <p class="section-note">Verified research resources used in this protocol:</p>
                    <div class="mh-rrid-list-main">
                        <?php foreach ($rrids as $rrid) :
                            $rrid_id = is_array($rrid) ? ($rrid['id'] ?? '') : $rrid;
                            $rrid_name = is_array($rrid) ? ($rrid['name'] ?? '') : '';
                            if ($rrid_id) :
                        ?>
                            <div class="mh-rrid-item-main">
                                <a href="https://scicrunch.org/resolver/<?php echo esc_attr($rrid_id); ?>" target="_blank" rel="noopener" class="mh-rrid-link">
                                    <?php echo esc_html($rrid_id); ?>
                                </a>
                                <?php if ($rrid_name) : ?>
                                    <span class="mh-rrid-name"><?php echo esc_html($rrid_name); ?></span>
                                <?php endif; ?>
                            </div>
                        <?php endif; endforeach; ?>
                    </div>
                </section>
                <?php endif; ?>

                <!-- RORs -->
                <?php if (!empty($rors)) : ?>
                <section class="mh-paper-section">
                    <h2>Research Organizations (ROR)</h2>
                    <p class="section-note">Affiliated research institutions:</p>
                    <div class="mh-ror-list-main">
                        <?php foreach ($rors as $ror) :
                            $ror_id = is_array($ror) ? ($ror['id'] ?? '') : $ror;
                            $ror_name = is_array($ror) ? ($ror['name'] ?? '') : '';
                            $ror_url = is_array($ror) ? ($ror['url'] ?? '') : '';
                            if (empty($ror_url) && $ror_id) {
                                $ror_url = 'https://ror.org/' . $ror_id;
                            }
                            if ($ror_id) :
                        ?>
                            <a href="<?php echo esc_url($ror_url); ?>" class="mh-ror-item-main" target="_blank" rel="noopener">
                                <span class="ror-id"><?php echo esc_html($ror_id); ?></span>
                                <?php if ($ror_name) : ?>
                                    <span class="ror-name"><?php echo esc_html($ror_name); ?></span>
                                <?php endif; ?>
                            </a>
                        <?php endif; endforeach; ?>
                    </div>
                </section>
                <?php endif; ?>

                <!-- Fluorophores -->
                <?php if (!empty($fluorophores)) : ?>
                <section class="mh-paper-section">
                    <h2>Fluorophores & Dyes</h2>
                    <div class="mh-tags-grid">
                        <?php foreach ($fluorophores as $fluor) : ?>
                            <span class="mh-tag fluorophore"><?php echo esc_html($fluor); ?></span>
                        <?php endforeach; ?>
                    </div>
                </section>
                <?php endif; ?>

                <!-- Sample Preparation -->
                <?php if (!empty($sample_prep)) : ?>
                <section class="mh-paper-section">
                    <h2>Sample Preparation</h2>
                    <div class="mh-tags-grid">
                        <?php foreach ($sample_prep as $prep) : ?>
                            <span class="mh-tag sample-prep"><?php echo esc_html($prep); ?></span>
                        <?php endforeach; ?>
                    </div>
                </section>
                <?php endif; ?>

                <!-- Cell Lines -->
                <?php if (!empty($cell_lines)) : ?>
                <section class="mh-paper-section">
                    <h2>Cell Lines</h2>
                    <div class="mh-tags-grid">
                        <?php foreach ($cell_lines as $cell) : ?>
                            <span class="mh-tag cell-line"><?php echo esc_html($cell); ?></span>
                        <?php endforeach; ?>
                    </div>
                </section>
                <?php endif; ?>

                <!-- Microscope Equipment -->
                <?php if (!empty($microscope_brands) || !empty($microscope_models)) : ?>
                <section class="mh-paper-section">
                    <h2>Microscope Equipment</h2>
                    <div class="mh-tags-grid">
                        <?php foreach ($microscope_brands as $brand) : ?>
                            <span class="mh-tag brand"><?php echo esc_html($brand); ?></span>
                        <?php endforeach; ?>
                        <?php foreach ($microscope_models as $model) : ?>
                            <span class="mh-tag model"><?php echo esc_html($model); ?></span>
                        <?php endforeach; ?>
                    </div>
                </section>
                <?php endif; ?>

                <!-- References -->
                <?php if (!empty($references)) : ?>
                <section class="mh-paper-section mh-references-section">
                    <h2>References</h2>
                    <ol class="mh-reference-list">
                        <?php foreach ($references as $idx => $ref) :
                            $num = isset($ref['num']) ? $ref['num'] : ($idx + 1);
                            $text = isset($ref['text']) ? $ref['text'] : '';
                            $ref_doi = isset($ref['doi']) ? $ref['doi'] : '';
                            $pmid = isset($ref['pmid']) ? $ref['pmid'] : '';
                            $url = isset($ref['url']) ? $ref['url'] : '';

                            $link = '';
                            if ($ref_doi) $link = 'https://doi.org/' . $ref_doi;
                            elseif ($pmid) $link = 'https://pubmed.ncbi.nlm.nih.gov/' . $pmid;
                            elseif ($url) $link = $url;
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
                                            <span>Link</span>
                                        <?php endif; ?>
                                    </a>
                                <?php endif; ?>
                            </li>
                        <?php endforeach; ?>
                    </ol>
                </section>
                <?php endif; ?>

                <!-- Facility -->
                <?php if ($facility || !empty($facilities_tax)) : ?>
                <section class="mh-paper-section">
                    <h2>Imaging Facility</h2>
                    <?php if ($facility) : ?>
                        <div class="mh-facility-card">
                            <span class="name"><?php echo esc_html($facility); ?></span>
                        </div>
                    <?php endif; ?>
                    <?php if (!empty($facilities_tax) && !is_wp_error($facilities_tax)) : ?>
                        <div class="mh-tags-grid">
                            <?php foreach ($facilities_tax as $term) : ?>
                                <a href="<?php echo esc_url(get_term_link($term)); ?>" class="mh-tag facility"><?php echo esc_html($term->name); ?></a>
                            <?php endforeach; ?>
                        </div>
                    <?php endif; ?>
                </section>
                <?php endif; ?>

                <!-- Comments Section -->
                <section class="mh-paper-section mh-comments-section">
                    <div class="mh-comments-header">
                        <h2>Discussion</h2>
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

                        <!-- Comment Form -->
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
                                    <textarea name="comment" id="comment" rows="4" required placeholder="Share your thoughts about this protocol..."></textarea>
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
                <!-- Protocol Info -->
                <div class="mh-sidebar-widget">
                    <h3>Protocol Info</h3>
                    <div class="mh-stats-list">
                        <?php if ($protocol_type) : ?>
                            <div class="mh-stat-row"><span>Type</span><span><?php echo esc_html($protocol_type); ?></span></div>
                        <?php endif; ?>
                        <?php if ($citations) : ?>
                            <div class="mh-stat-row"><span>Citations</span><span><?php echo number_format($citations); ?></span></div>
                        <?php endif; ?>
                        <?php if ($year) : ?>
                            <div class="mh-stat-row"><span>Year</span><span><?php echo esc_html($year); ?></span></div>
                        <?php endif; ?>
                        <?php if ($journal) : ?>
                            <div class="mh-stat-row"><span>Journal</span><span><?php echo esc_html($journal); ?></span></div>
                        <?php endif; ?>
                    </div>
                </div>

                <!-- Microscopes (taxonomy) -->
                <?php if (!empty($microscopes) && !is_wp_error($microscopes)) : ?>
                <div class="mh-sidebar-widget">
                    <h3>Microscopes</h3>
                    <div class="mh-tag-list">
                        <?php foreach ($microscopes as $term) : ?>
                            <a href="<?php echo esc_url(get_term_link($term)); ?>" class="mh-tag microscope"><?php echo esc_html($term->name); ?></a>
                        <?php endforeach; ?>
                    </div>
                </div>
                <?php endif; ?>

                <!-- Software (taxonomy) -->
                <?php if (!empty($software_tax) && !is_wp_error($software_tax)) : ?>
                <div class="mh-sidebar-widget">
                    <h3>Software</h3>
                    <div class="mh-tag-list">
                        <?php foreach ($software_tax as $term) : ?>
                            <a href="<?php echo esc_url(get_term_link($term)); ?>" class="mh-tag software"><?php echo esc_html($term->name); ?></a>
                        <?php endforeach; ?>
                    </div>
                </div>
                <?php endif; ?>

                <!-- Analysis Software (taxonomy) -->
                <?php if (!empty($analysis_sw_tax) && !is_wp_error($analysis_sw_tax)) : ?>
                <div class="mh-sidebar-widget">
                    <h3>Analysis Software</h3>
                    <div class="mh-tag-list">
                        <?php foreach ($analysis_sw_tax as $term) : ?>
                            <a href="<?php echo esc_url(get_term_link($term)); ?>" class="mh-tag software"><?php echo esc_html($term->name); ?></a>
                        <?php endforeach; ?>
                    </div>
                </div>
                <?php endif; ?>

                <!-- Acquisition Software (taxonomy) -->
                <?php if (!empty($acquisition_sw_tax) && !is_wp_error($acquisition_sw_tax)) : ?>
                <div class="mh-sidebar-widget">
                    <h3>Acquisition Software</h3>
                    <div class="mh-tag-list">
                        <?php foreach ($acquisition_sw_tax as $term) : ?>
                            <a href="<?php echo esc_url(get_term_link($term)); ?>" class="mh-tag software"><?php echo esc_html($term->name); ?></a>
                        <?php endforeach; ?>
                    </div>
                </div>
                <?php endif; ?>

                <!-- Analysis Software (meta) -->
                <?php if (!empty($image_analysis_sw)) : ?>
                <div class="mh-sidebar-widget">
                    <h3>Analysis Software</h3>
                    <div class="mh-tag-list">
                        <?php foreach ($image_analysis_sw as $sw) : ?>
                            <span class="mh-tag software"><?php echo esc_html($sw); ?></span>
                        <?php endforeach; ?>
                    </div>
                </div>
                <?php endif; ?>

                <!-- Acquisition Software (meta) -->
                <?php if (!empty($image_acquisition_sw)) : ?>
                <div class="mh-sidebar-widget">
                    <h3>Acquisition Software</h3>
                    <div class="mh-tag-list">
                        <?php foreach ($image_acquisition_sw as $sw) : ?>
                            <span class="mh-tag software"><?php echo esc_html($sw); ?></span>
                        <?php endforeach; ?>
                    </div>
                </div>
                <?php endif; ?>

                <!-- Organisms -->
                <?php if (!empty($organisms) && !is_wp_error($organisms)) : ?>
                <div class="mh-sidebar-widget">
                    <h3>Organisms</h3>
                    <div class="mh-tag-list">
                        <?php foreach ($organisms as $term) : ?>
                            <a href="<?php echo esc_url(get_term_link($term)); ?>" class="mh-tag organism"><?php echo esc_html($term->name); ?></a>
                        <?php endforeach; ?>
                    </div>
                </div>
                <?php endif; ?>

                <!-- Fluorophores (taxonomy) -->
                <?php if (!empty($fluorophores_tax) && !is_wp_error($fluorophores_tax)) : ?>
                <div class="mh-sidebar-widget">
                    <h3>Fluorophores</h3>
                    <div class="mh-tag-list">
                        <?php foreach ($fluorophores_tax as $term) : ?>
                            <a href="<?php echo esc_url(get_term_link($term)); ?>" class="mh-tag fluorophore"><?php echo esc_html($term->name); ?></a>
                        <?php endforeach; ?>
                    </div>
                </div>
                <?php endif; ?>

                <!-- Cell Lines (taxonomy) -->
                <?php if (!empty($cell_lines_tax) && !is_wp_error($cell_lines_tax)) : ?>
                <div class="mh-sidebar-widget">
                    <h3>Cell Lines</h3>
                    <div class="mh-tag-list">
                        <?php foreach ($cell_lines_tax as $term) : ?>
                            <a href="<?php echo esc_url(get_term_link($term)); ?>" class="mh-tag cell-line"><?php echo esc_html($term->name); ?></a>
                        <?php endforeach; ?>
                    </div>
                </div>
                <?php endif; ?>

                <!-- Sample Preparation (taxonomy) -->
                <?php if (!empty($sample_prep_tax) && !is_wp_error($sample_prep_tax)) : ?>
                <div class="mh-sidebar-widget">
                    <h3>Sample Preparation</h3>
                    <div class="mh-tag-list">
                        <?php foreach ($sample_prep_tax as $term) : ?>
                            <a href="<?php echo esc_url(get_term_link($term)); ?>" class="mh-tag sample-prep"><?php echo esc_html($term->name); ?></a>
                        <?php endforeach; ?>
                    </div>
                </div>
                <?php endif; ?>

                <!-- RRIDs -->
                <?php if (!empty($rrids)) : ?>
                <div class="mh-sidebar-widget">
                    <h3>RRIDs</h3>
                    <div class="mh-rrid-list">
                        <?php foreach ($rrids as $rrid) :
                            $rrid_id = is_array($rrid) ? ($rrid['id'] ?? '') : $rrid;
                            if ($rrid_id) :
                        ?>
                            <a href="https://scicrunch.org/resolver/<?php echo esc_attr($rrid_id); ?>" class="mh-rrid-item" target="_blank">
                                <?php echo esc_html($rrid_id); ?>
                            </a>
                        <?php endif; endforeach; ?>
                    </div>
                </div>
                <?php endif; ?>

                <!-- RORs -->
                <?php if (!empty($rors)) : ?>
                <div class="mh-sidebar-widget">
                    <h3>RORs</h3>
                    <div class="mh-ror-list">
                        <?php foreach ($rors as $ror) :
                            $ror_id = is_array($ror) ? ($ror['id'] ?? '') : $ror;
                            $ror_url = is_array($ror) ? ($ror['url'] ?? 'https://ror.org/' . $ror_id) : 'https://ror.org/' . $ror;
                            if ($ror_id) :
                        ?>
                            <a href="<?php echo esc_url($ror_url); ?>" class="mh-ror-item" target="_blank" rel="noopener">
                                <?php echo esc_html($ror_id); ?>
                            </a>
                        <?php endif; endforeach; ?>
                    </div>
                </div>
                <?php endif; ?>

                <!-- Facilities -->
                <?php if (!empty($facilities_tax) && !is_wp_error($facilities_tax)) : ?>
                <div class="mh-sidebar-widget">
                    <h3>Facilities</h3>
                    <div class="mh-tag-list">
                        <?php foreach ($facilities_tax as $term) : ?>
                            <a href="<?php echo esc_url(get_term_link($term)); ?>" class="mh-tag facility"><?php echo esc_html($term->name); ?></a>
                        <?php endforeach; ?>
                    </div>
                </div>
                <?php endif; ?>

                <!-- Institutions -->
                <?php if (!empty($institutions)) : ?>
                <div class="mh-sidebar-widget">
                    <h3>Institutions</h3>
                    <div class="mh-tag-list">
                        <?php foreach ($institutions as $inst) : ?>
                            <span class="mh-tag institution"><?php echo esc_html($inst); ?></span>
                        <?php endforeach; ?>
                    </div>
                </div>
                <?php endif; ?>

                <!-- Related -->
                <div class="mh-sidebar-widget">
                    <h3>Related</h3>
                    <?php
                    $related = get_posts(array(
                        'post_type' => array('mh_paper', 'mh_protocol'),
                        'posts_per_page' => 5,
                        'post__not_in' => array($post_id),
                        'tax_query' => array(
                            'relation' => 'OR',
                            array(
                                'taxonomy' => 'mh_technique',
                                'field' => 'slug',
                                'terms' => wp_get_post_terms($post_id, 'mh_technique', array('fields' => 'slugs')),
                            ),
                        ),
                    ));

                    if ($related) :
                        foreach ($related as $paper) :
                    ?>
                        <a href="<?php echo get_permalink($paper->ID); ?>" class="mh-related-item">
                            <?php echo esc_html(wp_trim_words($paper->post_title, 10)); ?>
                        </a>
                    <?php
                        endforeach;
                    else :
                    ?>
                        <p style="color: #8b949e; font-size: 0.85rem;">No related items found.</p>
                    <?php endif; ?>
                </div>
            </aside>
        </div>
    </article>
</div>

<style>
/* Single Paper Styles v4.2 */
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

.mh-badge {
    display: inline-block;
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 600;
    margin-right: 8px;
    margin-bottom: 12px;
}

.mh-badge.foundational { background: linear-gradient(135deg, #ffd700, #ff8c00); color: #000; }
.mh-badge.high-impact { background: linear-gradient(135deg, #58a6ff, #a371f7); color: #fff; }
.mh-badge.protocol-type { background: linear-gradient(135deg, #3b82f6, #8b5cf6); color: #fff; }

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
    text-decoration: none;
}

.mh-btn.doi { background: rgba(63, 185, 80, 0.15); color: #3fb950; }
.mh-btn.pubmed { background: rgba(88, 166, 255, 0.15); color: #58a6ff; }
.mh-btn.pmc { background: rgba(46, 125, 50, 0.15); color: #4caf50; }
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

.section-note {
    color: #8b949e;
    font-size: 0.9rem;
    margin-bottom: 16px;
}

.mh-tags-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}

.mh-tag {
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 0.8rem;
    font-weight: 500;
    text-decoration: none;
}

.mh-tag.technique { background: rgba(88, 166, 255, 0.15); color: #58a6ff; }
.mh-tag.microscope { background: rgba(163, 113, 247, 0.15); color: #a371f7; }
.mh-tag.organism { background: rgba(63, 185, 80, 0.15); color: #3fb950; }
.mh-tag.software { background: rgba(163, 113, 247, 0.15); color: #a371f7; }
.mh-tag.fluorophore { background: rgba(247, 120, 186, 0.15); color: #f778ba; }
.mh-tag.sample-prep { background: rgba(165, 214, 167, 0.15); color: #a5d6a7; }
.mh-tag.cell-line { background: rgba(212, 167, 44, 0.15); color: #d4a72c; }
.mh-tag.brand { background: rgba(71, 85, 105, 0.15); color: #e2e8f0; }
.mh-tag.model { background: rgba(100, 116, 139, 0.15); color: #cbd5e1; }
.mh-tag.facility { background: rgba(59, 130, 246, 0.15); color: #60a5fa; }
.mh-tag.institution { background: rgba(139, 92, 246, 0.15); color: #a78bfa; }

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
    text-decoration: none;
    transition: all 0.2s;
}

.mh-protocol-item:hover, .mh-repo-item:hover {
    background: #30363d;
}

.mh-protocol-item .source, .mh-repo-id {
    color: #8b949e;
    font-size: 0.8rem;
    margin-left: auto;
}

.mh-github-card {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 16px;
    background: #21262d;
    border-radius: 8px;
    color: #e6edf3;
    text-decoration: none;
    transition: all 0.2s;
}

.mh-github-card:hover {
    background: #30363d;
}

.mh-github-card .info strong {
    display: block;
    margin-bottom: 4px;
}

.mh-github-card .info span {
    color: #8b949e;
    font-size: 0.85rem;
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

/* RRID and ROR lists in main content */
.mh-rrid-list-main, .mh-ror-list-main {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.mh-rrid-item-main, .mh-ror-item-main {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px;
    background: #21262d;
    border-radius: 6px;
}

.mh-rrid-link {
    color: #a371f7;
    font-family: monospace;
    text-decoration: none;
}

.mh-rrid-link:hover {
    text-decoration: underline;
}

.mh-rrid-type {
    color: #58a6ff;
    font-size: 0.8rem;
    padding: 2px 8px;
    background: rgba(88, 166, 255, 0.15);
    border-radius: 4px;
}

.mh-rrid-name, .ror-name {
    color: #8b949e;
    font-size: 0.9rem;
}

.mh-ror-item-main {
    color: #bee3f8;
    text-decoration: none;
    background: linear-gradient(135deg, #1a365d 0%, #2c5282 100%);
    border: 1px solid #2b6cb0;
}

.mh-ror-item-main:hover {
    background: linear-gradient(135deg, #2c5282 0%, #3182ce 100%);
    color: #fff;
}

.ror-id {
    font-family: monospace;
    font-size: 0.85rem;
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

.mh-comment-content { flex: 1; }

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

.mh-no-comments {
    color: #8b949e;
    font-size: 0.9rem;
    text-align: center;
    padding: 20px;
}

.mh-comment-form {
    background: #0d1117;
    border-radius: 8px;
    padding: 20px;
    margin-top: 20px;
}

.mh-comment-form h4 {
    margin: 0 0 16px 0;
    color: #e6edf3;
}

.mh-form-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin-bottom: 12px;
}

.mh-form-group {
    margin-bottom: 12px;
}

.mh-form-group label {
    display: block;
    margin-bottom: 4px;
    font-size: 0.85rem;
    color: #8b949e;
}

.mh-form-group input,
.mh-form-group textarea {
    width: 100%;
    padding: 10px 12px;
    border: 1px solid #30363d;
    border-radius: 6px;
    background: #161b22;
    color: #e6edf3;
    font-size: 0.9rem;
}

.mh-form-group textarea {
    resize: vertical;
    min-height: 80px;
}

.mh-submit-btn {
    padding: 10px 20px;
    background: #58a6ff;
    border: none;
    border-radius: 6px;
    color: white;
    font-weight: 600;
    cursor: pointer;
}

.mh-submit-btn:hover {
    background: #79b8ff;
}

.mh-logged-in-as {
    color: #8b949e;
    font-size: 0.9rem;
    margin-bottom: 12px;
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

.mh-stats-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.mh-stat-row {
    display: flex;
    justify-content: space-between;
    font-size: 0.85rem;
    color: #8b949e;
}

.mh-stat-row span:last-child {
    color: #e6edf3;
}

.mh-related-item {
    display: block;
    padding: 8px;
    color: #58a6ff;
    font-size: 0.85rem;
    border-bottom: 1px solid #21262d;
    text-decoration: none;
}

.mh-related-item:hover {
    background: #21262d;
}

.mh-tag-list {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
}

.mh-rrid-list, .mh-ror-list {
    display: flex;
    flex-direction: column;
    gap: 6px;
}

.mh-rrid-item {
    padding: 8px;
    background: #21262d;
    border-radius: 6px;
    font-size: 0.85rem;
}

.mh-rrid-item .type {
    color: #8b949e;
    display: block;
    font-size: 0.75rem;
}

.mh-rrid-item .id {
    color: #a371f7;
    font-family: monospace;
    text-decoration: none;
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
}

.mh-ror-item .ror-id {
    font-family: monospace;
    font-size: 0.8rem;
}

@media (max-width: 900px) {
    .mh-paper-content {
        grid-template-columns: 1fr;
    }
    .mh-form-row {
        grid-template-columns: 1fr;
    }
}


/* Protocol-specific styles */
.mh-single-protocol {
    /* Inherits from mh-single-paper */
}

.mh-badge.protocol-type {
    background: linear-gradient(135deg, #3b82f6, #8b5cf6);
    color: white;
}

.mh-btn.pmc {
    background: rgba(46, 125, 50, 0.15);
    color: #4caf50;
}

.section-note {
    color: #8b949e;
    font-size: 0.9rem;
    margin-bottom: 16px;
}

.mh-rrid-list-main, .mh-ror-list-main {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.mh-rrid-item-main, .mh-ror-item-main {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px;
    background: #21262d;
    border-radius: 6px;
}

.mh-rrid-link {
    color: #a371f7;
    font-family: monospace;
    text-decoration: none;
}

.mh-rrid-link:hover {
    text-decoration: underline;
}

.mh-rrid-name, .ror-name {
    color: #8b949e;
    font-size: 0.9rem;
}

.mh-ror-item-main {
    color: #bee3f8;
    text-decoration: none;
    background: linear-gradient(135deg, #1a365d 0%, #2c5282 100%);
    border: 1px solid #2b6cb0;
}

.mh-ror-item-main:hover {
    background: linear-gradient(135deg, #2c5282 0%, #3182ce 100%);
}

.ror-id {
    font-family: monospace;
    font-size: 0.85rem;
}
</style>

<?php get_footer(); ?>
