<?php
/**
 * Single Paper Template v4.3
 * Clean PHP syntax - properly balanced if/endif
 */
get_header();

$post_id = get_the_ID();

// Basic meta
$doi = get_post_meta($post_id, '_mh_doi', true);
$pubmed_id = get_post_meta($post_id, '_mh_pubmed_id', true);
$pmc_id = get_post_meta($post_id, '_mh_pmc_id', true);
$authors = get_post_meta($post_id, '_mh_authors', true);
$journal = get_post_meta($post_id, '_mh_journal', true);
$year = get_post_meta($post_id, '_mh_publication_year', true);
$citations = intval(get_post_meta($post_id, '_mh_citation_count', true));
$abstract = get_post_meta($post_id, '_mh_abstract', true);
$pdf_url = get_post_meta($post_id, '_mh_pdf_url', true);
$github_url = get_post_meta($post_id, '_mh_github_url', true);
$facility = get_post_meta($post_id, '_mh_facility', true);

// URL meta fields - use stored or generate
$doi_url = get_post_meta($post_id, '_mh_doi_url', true);
$pubmed_url = get_post_meta($post_id, '_mh_pubmed_url', true);
$pmc_url = get_post_meta($post_id, '_mh_pmc_url', true);

if ($doi && !$doi_url) {
    $doi_url = 'https://doi.org/' . $doi;
}
if ($pubmed_id && !$pubmed_url) {
    $pubmed_url = 'https://pubmed.ncbi.nlm.nih.gov/' . $pubmed_id . '/';
}
if ($pmc_id && !$pmc_url) {
    $pmc_clean = str_replace('PMC', '', strtoupper($pmc_id));
    $pmc_url = 'https://www.ncbi.nlm.nih.gov/pmc/articles/PMC' . $pmc_clean . '/';
}

// Protocol detection
$is_protocol = get_post_meta($post_id, '_mh_is_protocol', true);
$protocol_type = get_post_meta($post_id, '_mh_protocol_type', true);

// JSON data
$protocols = json_decode(get_post_meta($post_id, '_mh_protocols', true), true);
if (!is_array($protocols)) $protocols = array();

$repos = json_decode(get_post_meta($post_id, '_mh_repositories', true), true);
if (!is_array($repos)) $repos = array();

$rrids = json_decode(get_post_meta($post_id, '_mh_rrids', true), true);
if (!is_array($rrids)) $rrids = array();

$rors = json_decode(get_post_meta($post_id, '_mh_rors', true), true);
if (!is_array($rors)) $rors = array();

$references = json_decode(get_post_meta($post_id, '_mh_references', true), true);
if (!is_array($references)) $references = array();

$fluorophores_meta = json_decode(get_post_meta($post_id, '_mh_fluorophores', true), true);
if (!is_array($fluorophores_meta)) $fluorophores_meta = array();

$cell_lines_meta = json_decode(get_post_meta($post_id, '_mh_cell_lines', true), true);
if (!is_array($cell_lines_meta)) $cell_lines_meta = array();

$sample_prep_meta = json_decode(get_post_meta($post_id, '_mh_sample_preparation', true), true);
if (!is_array($sample_prep_meta)) $sample_prep_meta = array();

$microscope_brands = json_decode(get_post_meta($post_id, '_mh_microscope_brands', true), true);
if (!is_array($microscope_brands)) $microscope_brands = array();

$microscope_models = json_decode(get_post_meta($post_id, '_mh_microscope_models', true), true);
if (!is_array($microscope_models)) $microscope_models = array();

$institutions = json_decode(get_post_meta($post_id, '_mh_institutions', true), true);
if (!is_array($institutions)) $institutions = array();

// Taxonomies
$techniques = wp_get_post_terms($post_id, 'mh_technique', array('fields' => 'all'));
if (is_wp_error($techniques)) $techniques = array();

$microscopes = wp_get_post_terms($post_id, 'mh_microscope', array('fields' => 'all'));
if (is_wp_error($microscopes)) $microscopes = array();

$organisms = wp_get_post_terms($post_id, 'mh_organism', array('fields' => 'all'));
if (is_wp_error($organisms)) $organisms = array();

$software_tax = wp_get_post_terms($post_id, 'mh_software', array('fields' => 'all'));
if (is_wp_error($software_tax)) $software_tax = array();

$facilities_tax = wp_get_post_terms($post_id, 'mh_facility', array('fields' => 'all'));
if (is_wp_error($facilities_tax)) $facilities_tax = array();
?>

<div class="microhub-wrapper">
    <?php if (function_exists('mh_render_nav')) { echo mh_render_nav(); } ?>

    <article class="mh-single-paper">
        <!-- Paper Header -->
        <header class="mh-paper-header">
            <div class="mh-paper-header-inner">
                <?php if ($is_protocol && $protocol_type) { ?>
                    <span class="mh-badge protocol-type"><?php echo esc_html($protocol_type); ?></span>
                <?php } ?>

                <?php if ($citations >= 100) { ?>
                    <span class="mh-badge foundational">Foundational Paper</span>
                <?php } elseif ($citations >= 50) { ?>
                    <span class="mh-badge high-impact">High Impact</span>
                <?php } ?>

                <h1><?php the_title(); ?></h1>

                <?php if ($authors) { ?>
                    <p class="mh-paper-authors"><?php echo esc_html($authors); ?></p>
                <?php } ?>

                <div class="mh-paper-meta">
                    <?php if ($journal) { ?>
                        <span class="mh-meta-item"><?php echo esc_html($journal); ?></span>
                    <?php } ?>
                    <?php if ($year) { ?>
                        <span class="mh-meta-item"><?php echo esc_html($year); ?></span>
                    <?php } ?>
                    <?php if ($citations) { ?>
                        <span class="mh-meta-item"><?php echo number_format($citations); ?> citations</span>
                    <?php } ?>
                </div>

                <div class="mh-paper-links">
                    <?php if ($doi_url) { ?>
                        <a href="<?php echo esc_url($doi_url); ?>" class="mh-btn doi" target="_blank">DOI</a>
                    <?php } ?>
                    <?php if ($pubmed_url) { ?>
                        <a href="<?php echo esc_url($pubmed_url); ?>" class="mh-btn pubmed" target="_blank">PubMed</a>
                    <?php } ?>
                    <?php if ($pmc_url) { ?>
                        <a href="<?php echo esc_url($pmc_url); ?>" class="mh-btn pmc" target="_blank">PMC</a>
                    <?php } ?>
                    <?php if ($pdf_url) { ?>
                        <a href="<?php echo esc_url($pdf_url); ?>" class="mh-btn pdf" target="_blank">PDF</a>
                    <?php } ?>
                    <?php if ($github_url) { ?>
                        <a href="<?php echo esc_url($github_url); ?>" class="mh-btn github" target="_blank">GitHub</a>
                    <?php } ?>
                </div>
            </div>
        </header>

        <div class="mh-paper-content">
            <!-- Main Content -->
            <div class="mh-paper-main">
                <!-- Abstract -->
                <?php if ($abstract) { ?>
                <section class="mh-paper-section">
                    <h2>Abstract</h2>
                    <p><?php echo esc_html($abstract); ?></p>
                </section>
                <?php } ?>

                <!-- Techniques -->
                <?php if (!empty($techniques)) { ?>
                <section class="mh-paper-section">
                    <h2>Techniques & Methods</h2>
                    <div class="mh-tags-grid">
                        <?php foreach ($techniques as $term) { ?>
                            <a href="<?php echo esc_url(get_term_link($term)); ?>" class="mh-tag technique"><?php echo esc_html($term->name); ?></a>
                        <?php } ?>
                        <?php foreach ($microscopes as $term) { ?>
                            <a href="<?php echo esc_url(get_term_link($term)); ?>" class="mh-tag microscope"><?php echo esc_html($term->name); ?></a>
                        <?php } ?>
                    </div>
                </section>
                <?php } ?>

                <!-- Protocols -->
                <?php if (!empty($protocols)) { ?>
                <section class="mh-paper-section" id="protocols">
                    <h2>Protocols</h2>
                    <div class="mh-protocol-list">
                        <?php foreach ($protocols as $protocol) { ?>
                            <a href="<?php echo esc_url($protocol['url'] ?? ''); ?>" class="mh-protocol-item" target="_blank">
                                <span class="protocol-icon">📋</span>
                                <span class="protocol-name"><?php echo esc_html($protocol['name'] ?? 'Protocol'); ?></span>
                                <span class="source"><?php echo esc_html($protocol['source'] ?? ''); ?></span>
                            </a>
                        <?php } ?>
                    </div>
                </section>
                <?php } ?>

                <!-- GitHub -->
                <?php if ($github_url) { ?>
                <section class="mh-paper-section">
                    <h2>Code & Data</h2>
                    <a href="<?php echo esc_url($github_url); ?>" class="mh-github-card" target="_blank">
                        <svg viewBox="0 0 16 16" width="32" height="32" fill="currentColor">
                            <path fill-rule="evenodd" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"></path>
                        </svg>
                        <div class="info">
                            <strong>View on GitHub</strong>
                            <span>Code and data repository</span>
                        </div>
                    </a>
                </section>
                <?php } ?>

                <!-- Data Repositories -->
                <?php if (!empty($repos)) { ?>
                <section class="mh-paper-section">
                    <h2>Data Repositories</h2>
                    <div class="mh-repo-list">
                        <?php foreach ($repos as $repo) { ?>
                            <a href="<?php echo esc_url($repo['url'] ?? ''); ?>" class="mh-repo-item" target="_blank">
                                <span class="repo-icon">💾</span>
                                <span class="repo-name"><?php echo esc_html($repo['name'] ?? $repo['type'] ?? 'Data'); ?></span>
                                <span class="mh-repo-id"><?php echo esc_html($repo['id'] ?? ''); ?></span>
                            </a>
                        <?php } ?>
                    </div>
                </section>
                <?php } ?>

                <!-- RRIDs -->
                <?php if (!empty($rrids)) { ?>
                <section class="mh-paper-section">
                    <h2>Research Resource Identifiers (RRIDs)</h2>
                    <div class="mh-rrid-list-main">
                        <?php foreach ($rrids as $rrid) {
                            $rrid_id = is_array($rrid) ? ($rrid['id'] ?? '') : $rrid;
                            $rrid_name = is_array($rrid) ? ($rrid['name'] ?? '') : '';
                        ?>
                            <div class="mh-rrid-item-main">
                                <a href="https://scicrunch.org/resolver/<?php echo esc_attr($rrid_id); ?>" class="mh-rrid-link" target="_blank"><?php echo esc_html($rrid_id); ?></a>
                                <?php if ($rrid_name) { ?>
                                    <span class="mh-rrid-name"><?php echo esc_html($rrid_name); ?></span>
                                <?php } ?>
                            </div>
                        <?php } ?>
                    </div>
                </section>
                <?php } ?>

                <!-- RORs -->
                <?php if (!empty($rors)) { ?>
                <section class="mh-paper-section">
                    <h2>Research Organizations (ROR)</h2>
                    <div class="mh-ror-list-main">
                        <?php foreach ($rors as $ror) {
                            $ror_id = is_array($ror) ? ($ror['id'] ?? '') : $ror;
                            $ror_name = is_array($ror) ? ($ror['name'] ?? '') : '';
                            $ror_url = strpos($ror_id, 'http') === 0 ? $ror_id : 'https://ror.org/' . $ror_id;
                        ?>
                            <a href="<?php echo esc_url($ror_url); ?>" class="mh-ror-item-main" target="_blank">
                                <span class="ror-id"><?php echo esc_html($ror_id); ?></span>
                                <?php if ($ror_name) { ?>
                                    <span class="ror-name"><?php echo esc_html($ror_name); ?></span>
                                <?php } ?>
                            </a>
                        <?php } ?>
                    </div>
                </section>
                <?php } ?>

                <!-- Fluorophores -->
                <?php if (!empty($fluorophores_meta)) { ?>
                <section class="mh-paper-section">
                    <h2>Fluorophores & Dyes</h2>
                    <div class="mh-tags-grid">
                        <?php foreach ($fluorophores_meta as $fluor) { ?>
                            <span class="mh-tag fluorophore"><?php echo esc_html($fluor); ?></span>
                        <?php } ?>
                    </div>
                </section>
                <?php } ?>

                <!-- Sample Preparation -->
                <?php if (!empty($sample_prep_meta)) { ?>
                <section class="mh-paper-section">
                    <h2>Sample Preparation</h2>
                    <div class="mh-tags-grid">
                        <?php foreach ($sample_prep_meta as $prep) { ?>
                            <span class="mh-tag sample-prep"><?php echo esc_html($prep); ?></span>
                        <?php } ?>
                    </div>
                </section>
                <?php } ?>

                <!-- Cell Lines -->
                <?php if (!empty($cell_lines_meta)) { ?>
                <section class="mh-paper-section">
                    <h2>Cell Lines</h2>
                    <div class="mh-tags-grid">
                        <?php foreach ($cell_lines_meta as $cell) { ?>
                            <span class="mh-tag cell-line"><?php echo esc_html($cell); ?></span>
                        <?php } ?>
                    </div>
                </section>
                <?php } ?>

                <!-- Equipment -->
                <?php if (!empty($microscope_brands) || !empty($microscope_models)) { ?>
                <section class="mh-paper-section">
                    <h2>Microscope Equipment</h2>
                    <div class="mh-tags-grid">
                        <?php foreach ($microscope_brands as $brand) { ?>
                            <span class="mh-tag brand"><?php echo esc_html($brand); ?></span>
                        <?php } ?>
                        <?php foreach ($microscope_models as $model) { ?>
                            <span class="mh-tag model"><?php echo esc_html($model); ?></span>
                        <?php } ?>
                    </div>
                </section>
                <?php } ?>

                <!-- References -->
                <?php if (!empty($references)) { ?>
                <section class="mh-paper-section">
                    <h2>References</h2>
                    <div class="mh-reference-list">
                        <?php foreach (array_slice($references, 0, 10) as $ref) { ?>
                            <div class="mh-reference-item">
                                <?php echo esc_html(is_array($ref) ? ($ref['citation'] ?? json_encode($ref)) : $ref); ?>
                            </div>
                        <?php } ?>
                    </div>
                </section>
                <?php } ?>

                <!-- Facility -->
                <?php if ($facility) { ?>
                <section class="mh-paper-section">
                    <h2>Imaging Facility</h2>
                    <div class="mh-facility-card">
                        <span class="facility-icon">🏛️</span>
                        <span class="facility-name"><?php echo esc_html($facility); ?></span>
                    </div>
                </section>
                <?php } ?>

                <!-- Comments -->
                <section class="mh-paper-section mh-comments-section">
                    <div class="mh-comments-header">
                        <h2>Discussion</h2>
                        <span class="mh-comments-count"><?php echo get_comments_number(); ?></span>
                    </div>

                    <div class="mh-comments-list">
                        <?php
                        $comments = get_comments(array('post_id' => $post_id, 'status' => 'approve'));
                        if ($comments) {
                            foreach ($comments as $comment) {
                                $initials = strtoupper(substr($comment->comment_author, 0, 2));
                        ?>
                            <div class="mh-comment">
                                <div class="mh-comment-avatar"><?php echo esc_html($initials); ?></div>
                                <div class="mh-comment-content">
                                    <div class="mh-comment-meta">
                                        <span class="mh-comment-author"><?php echo esc_html($comment->comment_author); ?></span>
                                        <span class="mh-comment-date"><?php echo human_time_diff(strtotime($comment->comment_date), current_time('timestamp')); ?> ago</span>
                                    </div>
                                    <div class="mh-comment-text"><?php echo esc_html($comment->comment_content); ?></div>
                                </div>
                            </div>
                        <?php
                            }
                        } else {
                        ?>
                            <p class="mh-no-comments">No comments yet. Be the first to discuss this paper!</p>
                        <?php } ?>
                    </div>

                    <div class="mh-comment-form">
                        <h4>Add a Comment</h4>
                        <form action="<?php echo esc_url(site_url('/wp-comments-post.php')); ?>" method="post">
                            <?php if (!is_user_logged_in()) { ?>
                            <div class="mh-form-row">
                                <div class="mh-form-group">
                                    <label>Name <span class="required">*</span></label>
                                    <input type="text" name="author" required>
                                </div>
                                <div class="mh-form-group">
                                    <label>Email <span style="color: #8b949e;">(optional)</span></label>
                                    <input type="email" name="email">
                                </div>
                            </div>
                            <?php } else {
                                $current_user = wp_get_current_user();
                            ?>
                            <p class="mh-logged-in-as">Commenting as <strong><?php echo esc_html($current_user->display_name); ?></strong></p>
                            <?php } ?>

                            <div class="mh-form-group">
                                <label>Comment <span class="required">*</span></label>
                                <textarea name="comment" rows="4" required placeholder="Share your thoughts..."></textarea>
                            </div>

                            <input type="hidden" name="comment_post_ID" value="<?php echo $post_id; ?>">
                            <?php wp_nonce_field('unfiltered-html-comment'); ?>
                            <button type="submit" class="mh-submit-btn">Post Comment</button>
                        </form>
                    </div>
                </section>
            </div>

            <!-- Sidebar -->
            <aside class="mh-paper-sidebar">
                <!-- Paper Info -->
                <div class="mh-sidebar-widget">
                    <h3>Paper Info</h3>
                    <div class="mh-stats-list">
                        <?php if ($citations) { ?>
                        <div class="mh-stat-row">
                            <span>Citations</span>
                            <span><?php echo number_format($citations); ?></span>
                        </div>
                        <?php } ?>
                        <?php if ($year) { ?>
                        <div class="mh-stat-row">
                            <span>Year</span>
                            <span><?php echo esc_html($year); ?></span>
                        </div>
                        <?php } ?>
                        <?php if ($journal) { ?>
                        <div class="mh-stat-row">
                            <span>Journal</span>
                            <span><?php echo esc_html($journal); ?></span>
                        </div>
                        <?php } ?>
                        <?php if ($doi) { ?>
                        <div class="mh-stat-row">
                            <span>DOI</span>
                            <span style="font-family: monospace; font-size: 0.8rem;"><?php echo esc_html($doi); ?></span>
                        </div>
                        <?php } ?>
                    </div>
                </div>

                <!-- Techniques -->
                <?php if (!empty($techniques)) { ?>
                <div class="mh-sidebar-widget">
                    <h3>Techniques</h3>
                    <div class="mh-tag-list">
                        <?php foreach ($techniques as $term) { ?>
                            <a href="<?php echo esc_url(get_term_link($term)); ?>" class="mh-tag technique"><?php echo esc_html($term->name); ?></a>
                        <?php } ?>
                    </div>
                </div>
                <?php } ?>

                <!-- Microscopes -->
                <?php if (!empty($microscopes)) { ?>
                <div class="mh-sidebar-widget">
                    <h3>Microscopes</h3>
                    <div class="mh-tag-list">
                        <?php foreach ($microscopes as $term) { ?>
                            <a href="<?php echo esc_url(get_term_link($term)); ?>" class="mh-tag microscope"><?php echo esc_html($term->name); ?></a>
                        <?php } ?>
                    </div>
                </div>
                <?php } ?>

                <!-- Software -->
                <?php if (!empty($software_tax)) { ?>
                <div class="mh-sidebar-widget">
                    <h3>Software</h3>
                    <div class="mh-tag-list">
                        <?php foreach ($software_tax as $term) { ?>
                            <a href="<?php echo esc_url(get_term_link($term)); ?>" class="mh-tag software"><?php echo esc_html($term->name); ?></a>
                        <?php } ?>
                    </div>
                </div>
                <?php } ?>

                <!-- Organisms -->
                <?php if (!empty($organisms)) { ?>
                <div class="mh-sidebar-widget">
                    <h3>Organisms</h3>
                    <div class="mh-tag-list">
                        <?php foreach ($organisms as $term) { ?>
                            <a href="<?php echo esc_url(get_term_link($term)); ?>" class="mh-tag organism"><?php echo esc_html($term->name); ?></a>
                        <?php } ?>
                    </div>
                </div>
                <?php } ?>

                <!-- Fluorophores -->
                <?php if (!empty($fluorophores_meta)) { ?>
                <div class="mh-sidebar-widget">
                    <h3>Fluorophores</h3>
                    <div class="mh-tag-list">
                        <?php foreach ($fluorophores_meta as $fluor) { ?>
                            <span class="mh-tag fluorophore"><?php echo esc_html($fluor); ?></span>
                        <?php } ?>
                    </div>
                </div>
                <?php } ?>

                <!-- Cell Lines -->
                <?php if (!empty($cell_lines_meta)) { ?>
                <div class="mh-sidebar-widget">
                    <h3>Cell Lines</h3>
                    <div class="mh-tag-list">
                        <?php foreach ($cell_lines_meta as $cell) { ?>
                            <span class="mh-tag cell-line"><?php echo esc_html($cell); ?></span>
                        <?php } ?>
                    </div>
                </div>
                <?php } ?>

                <!-- Sample Prep -->
                <?php if (!empty($sample_prep_meta)) { ?>
                <div class="mh-sidebar-widget">
                    <h3>Sample Preparation</h3>
                    <div class="mh-tag-list">
                        <?php foreach ($sample_prep_meta as $prep) { ?>
                            <span class="mh-tag sample-prep"><?php echo esc_html($prep); ?></span>
                        <?php } ?>
                    </div>
                </div>
                <?php } ?>

                <!-- RRIDs -->
                <?php if (!empty($rrids)) { ?>
                <div class="mh-sidebar-widget">
                    <h3>RRIDs</h3>
                    <div class="mh-rrid-list">
                        <?php foreach (array_slice($rrids, 0, 5) as $rrid) {
                            $rrid_id = is_array($rrid) ? ($rrid['id'] ?? '') : $rrid;
                        ?>
                            <a href="https://scicrunch.org/resolver/<?php echo esc_attr($rrid_id); ?>" class="mh-rrid-item" target="_blank">
                                <?php echo esc_html($rrid_id); ?>
                            </a>
                        <?php } ?>
                    </div>
                </div>
                <?php } ?>

                <!-- RORs -->
                <?php if (!empty($rors)) { ?>
                <div class="mh-sidebar-widget">
                    <h3>RORs</h3>
                    <div class="mh-ror-list">
                        <?php foreach (array_slice($rors, 0, 5) as $ror) {
                            $ror_id = is_array($ror) ? ($ror['id'] ?? '') : $ror;
                            $ror_name = is_array($ror) ? ($ror['name'] ?? '') : '';
                            $ror_url = strpos($ror_id, 'http') === 0 ? $ror_id : 'https://ror.org/' . $ror_id;
                        ?>
                            <a href="<?php echo esc_url($ror_url); ?>" class="mh-ror-item" target="_blank">
                                <?php echo esc_html($ror_name ?: $ror_id); ?>
                            </a>
                        <?php } ?>
                    </div>
                </div>
                <?php } ?>

                <!-- Facilities -->
                <?php if (!empty($facilities_tax)) { ?>
                <div class="mh-sidebar-widget">
                    <h3>Facilities</h3>
                    <div class="mh-tag-list">
                        <?php foreach ($facilities_tax as $term) { ?>
                            <a href="<?php echo esc_url(get_term_link($term)); ?>" class="mh-tag facility"><?php echo esc_html($term->name); ?></a>
                        <?php } ?>
                    </div>
                </div>
                <?php } ?>

                <!-- Institutions -->
                <?php if (!empty($institutions)) { ?>
                <div class="mh-sidebar-widget">
                    <h3>Institutions</h3>
                    <div class="mh-tag-list">
                        <?php foreach ($institutions as $inst) { ?>
                            <span class="mh-tag institution"><?php echo esc_html($inst); ?></span>
                        <?php } ?>
                    </div>
                </div>
                <?php } ?>

                <!-- Related Papers -->
                <?php
                $related_terms = array();
                foreach ($techniques as $term) {
                    $related_terms[] = $term->term_id;
                }
                foreach ($microscopes as $term) {
                    $related_terms[] = $term->term_id;
                }
                foreach ($organisms as $term) {
                    $related_terms[] = $term->term_id;
                }

                if (!empty($related_terms)) {
                    $related = new WP_Query(array(
                        'post_type' => 'mh_paper',
                        'posts_per_page' => 5,
                        'post__not_in' => array($post_id),
                        'tax_query' => array(
                            'relation' => 'OR',
                            array('taxonomy' => 'mh_technique', 'terms' => $related_terms),
                            array('taxonomy' => 'mh_microscope', 'terms' => $related_terms),
                            array('taxonomy' => 'mh_organism', 'terms' => $related_terms)
                        )
                    ));

                    if ($related->have_posts()) {
                ?>
                <div class="mh-sidebar-widget">
                    <h3>Related Papers</h3>
                    <?php while ($related->have_posts()) { $related->the_post(); ?>
                        <a href="<?php the_permalink(); ?>" class="mh-related-item"><?php the_title(); ?></a>
                    <?php } ?>
                    <?php wp_reset_postdata(); ?>
                </div>
                <?php
                    }
                }
                ?>
            </aside>
        </div>
    </article>
</div>

<style>
/* Single Paper Styles v4.3 */
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

.mh-tags-grid, .mh-tag-list {
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

.mh-facility-card {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px;
    background: #21262d;
    border-radius: 6px;
    color: #e6edf3;
}

.mh-reference-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.mh-reference-item {
    padding: 10px;
    background: #21262d;
    border-radius: 6px;
    color: #8b949e;
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
    color: #a371f7;
    font-family: monospace;
    text-decoration: none;
}

.mh-ror-item {
    padding: 8px;
    background: linear-gradient(135deg, #1a365d 0%, #2c5282 100%);
    border-radius: 6px;
    color: #bee3f8;
    text-decoration: none;
    font-size: 0.85rem;
    border: 1px solid #2b6cb0;
}

.mh-ror-item:hover {
    background: linear-gradient(135deg, #2c5282 0%, #3182ce 100%);
    color: #fff;
}

@media (max-width: 900px) {
    .mh-paper-content {
        grid-template-columns: 1fr;
    }
    .mh-form-row {
        grid-template-columns: 1fr;
    }
}
</style>

<?php get_footer(); ?>
