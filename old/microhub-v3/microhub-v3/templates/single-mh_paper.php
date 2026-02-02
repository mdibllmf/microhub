<?php
/**
 * Single Paper Template v3.0
 * With figures, full methods, sample prep, fluorophores, and all enrichment data
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
$citations = get_post_meta($post_id, '_mh_citation_count', true);
$abstract = get_post_meta($post_id, '_mh_abstract', true);
$methods = get_post_meta($post_id, '_mh_methods', true);
$pdf_url = get_post_meta($post_id, '_mh_pdf_url', true);
$github_url = get_post_meta($post_id, '_mh_github_url', true);
$facility = get_post_meta($post_id, '_mh_facility', true);
$pmc_url = get_post_meta($post_id, '_mh_pmc_url', true);

// Flags
$has_full_text = get_post_meta($post_id, '_mh_has_full_text', true);
$has_figures = get_post_meta($post_id, '_mh_has_figures', true);

// Resources (JSON)
$protocols = json_decode(get_post_meta($post_id, '_mh_protocols', true), true) ?: array();
$repos = json_decode(get_post_meta($post_id, '_mh_repositories', true), true) ?: array();
$rrids = json_decode(get_post_meta($post_id, '_mh_rrids', true), true) ?: array();
$figures = json_decode(get_post_meta($post_id, '_mh_figures', true), true) ?: array();
$supplementary = json_decode(get_post_meta($post_id, '_mh_supplementary_materials', true), true) ?: array();

// Taxonomies
$techniques = wp_get_post_terms($post_id, 'mh_technique', array('fields' => 'names'));
$microscope_brands = wp_get_post_terms($post_id, 'mh_microscope_brand', array('fields' => 'names'));
$microscope_models = wp_get_post_terms($post_id, 'mh_microscope_model', array('fields' => 'names'));
$analysis_software = wp_get_post_terms($post_id, 'mh_analysis_software', array('fields' => 'names'));
$acquisition_software = wp_get_post_terms($post_id, 'mh_acquisition_software', array('fields' => 'names'));
$sample_prep = wp_get_post_terms($post_id, 'mh_sample_prep', array('fields' => 'names'));
$fluorophores = wp_get_post_terms($post_id, 'mh_fluorophore', array('fields' => 'names'));
$organisms = wp_get_post_terms($post_id, 'mh_organism', array('fields' => 'names'));

// Combine microscopes for display
$microscopes = array_merge(
    is_array($microscope_brands) ? $microscope_brands : array(),
    is_array($microscope_models) ? $microscope_models : array()
);

// Combine all software
$all_software = array_merge(
    is_array($analysis_software) ? $analysis_software : array(),
    is_array($acquisition_software) ? $acquisition_software : array()
);
?>

<div class="microhub-wrapper">
    <?php if (function_exists('mh_render_nav')) echo mh_render_nav(); ?>
    
    <article class="mh-single-paper">
        <!-- Paper Header -->
        <header class="mh-paper-header">
            <div class="mh-paper-header-inner">
                <!-- Badges -->
                <div class="mh-badges">
                    <?php if ($citations >= 100) : ?>
                        <span class="mh-badge foundational">🏆 Foundational Paper</span>
                    <?php elseif ($citations >= 50) : ?>
                        <span class="mh-badge high-impact">⭐ High Impact</span>
                    <?php endif; ?>
                    
                    <?php if ($has_full_text) : ?>
                        <span class="mh-badge full-text">📄 Full Text</span>
                    <?php endif; ?>
                    
                    <?php if (!empty($figures)) : ?>
                        <span class="mh-badge has-figures">🖼️ <?php echo count($figures); ?> Figures</span>
                    <?php endif; ?>
                    
                    <?php if (!empty($protocols)) : ?>
                        <span class="mh-badge has-protocols">📋 Protocols</span>
                    <?php endif; ?>
                    
                    <?php if ($github_url) : ?>
                        <span class="mh-badge has-code">💻 Code</span>
                    <?php endif; ?>
                </div>
                
                <h1><?php the_title(); ?></h1>
                
                <?php if ($authors) : ?>
                    <p class="mh-paper-authors"><?php echo esc_html($authors); ?></p>
                <?php endif; ?>
                
                <div class="mh-paper-meta">
                    <?php if ($journal) : ?>
                        <span class="mh-meta-item">📰 <?php echo esc_html($journal); ?></span>
                    <?php endif; ?>
                    <?php if ($year) : ?>
                        <span class="mh-meta-item">📅 <?php echo esc_html($year); ?></span>
                    <?php endif; ?>
                    <?php if ($citations) : ?>
                        <span class="mh-meta-item">📊 <?php echo number_format($citations); ?> citations</span>
                    <?php endif; ?>
                </div>
                
                <div class="mh-paper-links">
                    <?php if ($doi) : ?>
                        <a href="https://doi.org/<?php echo esc_attr($doi); ?>" class="mh-btn doi" target="_blank">DOI</a>
                    <?php endif; ?>
                    <?php if ($pubmed_id) : ?>
                        <a href="https://pubmed.ncbi.nlm.nih.gov/<?php echo esc_attr($pubmed_id); ?>/" class="mh-btn pubmed" target="_blank">PubMed</a>
                    <?php endif; ?>
                    <?php if ($pmc_id) : ?>
                        <a href="https://www.ncbi.nlm.nih.gov/pmc/articles/<?php echo esc_attr($pmc_id); ?>/" class="mh-btn pmc" target="_blank">PMC (Free)</a>
                    <?php endif; ?>
                    <?php if ($pdf_url) : ?>
                        <a href="<?php echo esc_url($pdf_url); ?>" class="mh-btn pdf" target="_blank">PDF</a>
                    <?php endif; ?>
                    <?php if ($github_url) : ?>
                        <a href="<?php echo esc_url($github_url); ?>" class="mh-btn github" target="_blank">💻 GitHub</a>
                    <?php endif; ?>
                </div>
            </div>
        </header>
        
        <div class="mh-paper-content">
            <div class="mh-paper-main">
                
                <!-- Figures Gallery (if available) -->
                <?php if (!empty($figures)) : ?>
                <section class="mh-paper-section mh-figures-section">
                    <h2>🖼️ Figures</h2>
                    <div class="mh-figures-gallery">
                        <?php foreach ($figures as $i => $fig) : ?>
                            <div class="mh-figure-item">
                                <?php if (!empty($fig['image_url'])) : ?>
                                    <a href="<?php echo esc_url($fig['image_url']); ?>" target="_blank" class="mh-figure-link">
                                        <img src="<?php echo esc_url($fig['image_url']); ?>" 
                                             alt="<?php echo esc_attr($fig['label'] ?? 'Figure ' . ($i + 1)); ?>"
                                             loading="lazy" />
                                    </a>
                                <?php endif; ?>
                                <div class="mh-figure-caption">
                                    <strong><?php echo esc_html($fig['label'] ?? 'Figure ' . ($i + 1)); ?></strong>
                                    <?php if (!empty($fig['title'])) : ?>
                                        <span class="mh-figure-title"><?php echo esc_html($fig['title']); ?></span>
                                    <?php endif; ?>
                                    <?php if (!empty($fig['caption'])) : ?>
                                        <p><?php echo esc_html(wp_trim_words($fig['caption'], 30)); ?></p>
                                    <?php endif; ?>
                                </div>
                            </div>
                        <?php endforeach; ?>
                    </div>
                </section>
                <?php endif; ?>
                
                <!-- Abstract -->
                <?php if ($abstract) : ?>
                <section class="mh-paper-section">
                    <h2>Abstract</h2>
                    <p><?php echo nl2br(esc_html($abstract)); ?></p>
                </section>
                <?php endif; ?>
                
                <!-- Methods Section (Full Text) -->
                <?php if ($methods) : ?>
                <section class="mh-paper-section mh-methods-section">
                    <h2>📝 Methods</h2>
                    <div class="mh-methods-content">
                        <?php echo wpautop(esc_html($methods)); ?>
                    </div>
                    <?php if (strlen($methods) > 2000) : ?>
                        <button class="mh-expand-btn" onclick="this.previousElementSibling.classList.toggle('expanded'); this.textContent = this.textContent === 'Show More' ? 'Show Less' : 'Show More';">Show More</button>
                    <?php endif; ?>
                </section>
                <?php endif; ?>
                
                <!-- Microscopy Techniques -->
                <?php if (!empty($techniques)) : ?>
                <section class="mh-paper-section">
                    <h2>🔬 Microscopy Techniques</h2>
                    <div class="mh-tags-grid">
                        <?php foreach ($techniques as $tech) : ?>
                            <a href="<?php echo esc_url(get_term_link($tech, 'mh_technique')); ?>" class="mh-tag technique"><?php echo esc_html($tech); ?></a>
                        <?php endforeach; ?>
                    </div>
                </section>
                <?php endif; ?>
                
                <!-- Microscopes Used -->
                <?php if (!empty($microscopes)) : ?>
                <section class="mh-paper-section">
                    <h2>🔭 Microscopes</h2>
                    <div class="mh-tags-grid">
                        <?php foreach ($microscope_brands as $brand) : ?>
                            <a href="<?php echo esc_url(get_term_link($brand, 'mh_microscope_brand')); ?>" class="mh-tag microscope-brand">🏭 <?php echo esc_html($brand); ?></a>
                        <?php endforeach; ?>
                        <?php foreach ($microscope_models as $model) : ?>
                            <a href="<?php echo esc_url(get_term_link($model, 'mh_microscope_model')); ?>" class="mh-tag microscope-model">📷 <?php echo esc_html($model); ?></a>
                        <?php endforeach; ?>
                    </div>
                </section>
                <?php endif; ?>
                
                <!-- Software -->
                <?php if (!empty($all_software)) : ?>
                <section class="mh-paper-section">
                    <h2>💻 Software</h2>
                    <div class="mh-software-grid">
                        <?php if (!empty($analysis_software)) : ?>
                            <div class="mh-software-category">
                                <h4>Analysis Software</h4>
                                <div class="mh-tags-grid">
                                    <?php foreach ($analysis_software as $sw) : ?>
                                        <a href="<?php echo esc_url(get_term_link($sw, 'mh_analysis_software')); ?>" class="mh-tag software-analysis"><?php echo esc_html($sw); ?></a>
                                    <?php endforeach; ?>
                                </div>
                            </div>
                        <?php endif; ?>
                        <?php if (!empty($acquisition_software)) : ?>
                            <div class="mh-software-category">
                                <h4>Acquisition Software</h4>
                                <div class="mh-tags-grid">
                                    <?php foreach ($acquisition_software as $sw) : ?>
                                        <a href="<?php echo esc_url(get_term_link($sw, 'mh_acquisition_software')); ?>" class="mh-tag software-acquisition"><?php echo esc_html($sw); ?></a>
                                    <?php endforeach; ?>
                                </div>
                            </div>
                        <?php endif; ?>
                    </div>
                </section>
                <?php endif; ?>
                
                <!-- Sample Preparation -->
                <?php if (!empty($sample_prep)) : ?>
                <section class="mh-paper-section">
                    <h2>🧪 Sample Preparation</h2>
                    <div class="mh-tags-grid">
                        <?php foreach ($sample_prep as $prep) : ?>
                            <a href="<?php echo esc_url(get_term_link($prep, 'mh_sample_prep')); ?>" class="mh-tag sample-prep"><?php echo esc_html($prep); ?></a>
                        <?php endforeach; ?>
                    </div>
                </section>
                <?php endif; ?>
                
                <!-- Fluorophores -->
                <?php if (!empty($fluorophores)) : ?>
                <section class="mh-paper-section">
                    <h2>🌈 Fluorophores & Dyes</h2>
                    <div class="mh-tags-grid">
                        <?php foreach ($fluorophores as $fluor) : ?>
                            <a href="<?php echo esc_url(get_term_link($fluor, 'mh_fluorophore')); ?>" class="mh-tag fluorophore"><?php echo esc_html($fluor); ?></a>
                        <?php endforeach; ?>
                    </div>
                </section>
                <?php endif; ?>
                
                <!-- Organisms -->
                <?php if (!empty($organisms)) : ?>
                <section class="mh-paper-section">
                    <h2>🧬 Organisms</h2>
                    <div class="mh-tags-grid">
                        <?php foreach ($organisms as $org) : ?>
                            <a href="<?php echo esc_url(get_term_link($org, 'mh_organism')); ?>" class="mh-tag organism"><?php echo esc_html($org); ?></a>
                        <?php endforeach; ?>
                    </div>
                </section>
                <?php endif; ?>
                
                <!-- Protocols -->
                <?php if (!empty($protocols)) : ?>
                <section class="mh-paper-section">
                    <h2>📋 Protocols</h2>
                    <div class="mh-protocol-list">
                        <?php foreach ($protocols as $protocol) : ?>
                            <a href="<?php echo esc_url($protocol['url'] ?? '#'); ?>" class="mh-protocol-item" target="_blank">
                                <span class="icon">📄</span>
                                <span class="name"><?php echo esc_html($protocol['source'] ?? $protocol['name'] ?? 'View Protocol'); ?></span>
                                <?php if (!empty($protocol['url'])) : ?>
                                    <span class="url"><?php echo esc_html(parse_url($protocol['url'], PHP_URL_HOST)); ?></span>
                                <?php endif; ?>
                            </a>
                        <?php endforeach; ?>
                    </div>
                </section>
                <?php endif; ?>
                
                <!-- GitHub / Code Repository -->
                <?php if ($github_url) : ?>
                <section class="mh-paper-section">
                    <h2>💻 Code Repository</h2>
                    <a href="<?php echo esc_url($github_url); ?>" class="mh-github-card" target="_blank">
                        <span class="icon">📂</span>
                        <div class="info">
                            <strong>GitHub Repository</strong>
                            <span><?php echo esc_html(preg_replace('/^https?:\/\/(www\.)?github\.com\//', '', $github_url)); ?></span>
                        </div>
                        <span class="arrow">→</span>
                    </a>
                </section>
                <?php endif; ?>
                
                <!-- Data Repositories -->
                <?php if (!empty($repos)) : ?>
                <section class="mh-paper-section">
                    <h2>💾 Data Repositories</h2>
                    <div class="mh-repo-list">
                        <?php foreach ($repos as $repo) : ?>
                            <a href="<?php echo esc_url($repo['url'] ?? '#'); ?>" class="mh-repo-item" target="_blank">
                                <span class="repo-name"><?php echo esc_html($repo['name'] ?? 'View Data'); ?></span>
                                <?php if (!empty($repo['accession_id'])) : ?>
                                    <span class="repo-id"><?php echo esc_html($repo['accession_id']); ?></span>
                                <?php endif; ?>
                            </a>
                        <?php endforeach; ?>
                    </div>
                </section>
                <?php endif; ?>
                
                <!-- Supplementary Materials -->
                <?php if (!empty($supplementary)) : ?>
                <section class="mh-paper-section">
                    <h2>📎 Supplementary Materials</h2>
                    <div class="mh-supplementary-list">
                        <?php foreach ($supplementary as $supp) : ?>
                            <div class="mh-supplementary-item">
                                <?php if (!empty($supp['url'])) : ?>
                                    <a href="<?php echo esc_url($supp['url']); ?>" target="_blank">
                                        <?php echo esc_html($supp['label'] ?? 'Supplementary Material'); ?>
                                    </a>
                                <?php else : ?>
                                    <span><?php echo esc_html($supp['label'] ?? 'Supplementary Material'); ?></span>
                                <?php endif; ?>
                            </div>
                        <?php endforeach; ?>
                    </div>
                </section>
                <?php endif; ?>
                
                <!-- Facility -->
                <?php if ($facility) : ?>
                <section class="mh-paper-section">
                    <h2>🏛️ Imaging Facility</h2>
                    <div class="mh-facility-card">
                        <span class="icon">🏛️</span>
                        <span class="name"><?php echo esc_html($facility); ?></span>
                    </div>
                </section>
                <?php endif; ?>
                
                <!-- Comments Section -->
                <section class="mh-paper-section mh-comments-section">
                    <div class="mh-comments-header">
                        <h2>💬 Discussion</h2>
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
                                    <textarea name="comment" id="comment" rows="4" required placeholder="Share your thoughts about this paper..."></textarea>
                                </div>
                                
                                <input type="hidden" name="comment_post_ID" value="<?php echo $post_id; ?>" />
                                <?php wp_nonce_field('unfiltered-html-comment'); ?>
                                <button type="submit" class="mh-submit-btn">Post Comment</button>
                            </form>
                        </div>
                    <?php else : ?>
                        <p class="mh-comments-closed">Comments are closed for this paper.</p>
                    <?php endif; ?>
                </section>
                
            </div>
            
            <!-- Sidebar -->
            <aside class="mh-paper-sidebar">
                
                <!-- Quick Stats Widget -->
                <div class="mh-sidebar-widget mh-quick-stats">
                    <h3>📊 Quick Stats</h3>
                    <ul>
                        <?php if ($citations) : ?>
                            <li><strong><?php echo number_format($citations); ?></strong> Citations</li>
                        <?php endif; ?>
                        <?php if (!empty($figures)) : ?>
                            <li><strong><?php echo count($figures); ?></strong> Figures</li>
                        <?php endif; ?>
                        <?php if (!empty($protocols)) : ?>
                            <li><strong><?php echo count($protocols); ?></strong> Protocols</li>
                        <?php endif; ?>
                        <?php if (!empty($repos)) : ?>
                            <li><strong><?php echo count($repos); ?></strong> Data Repositories</li>
                        <?php endif; ?>
                    </ul>
                </div>
                
                <!-- RRIDs Widget -->
                <?php if (!empty($rrids)) : ?>
                <div class="mh-sidebar-widget">
                    <h3>🔗 RRIDs</h3>
                    <?php 
                    // Group RRIDs by type
                    $rrid_groups = array();
                    foreach ($rrids as $rrid) {
                        $type = $rrid['type'] ?? 'other';
                        $rrid_groups[$type][] = $rrid;
                    }
                    ?>
                    <?php foreach ($rrid_groups as $type => $type_rrids) : ?>
                        <div class="mh-rrid-group">
                            <h4><?php echo esc_html(ucfirst(str_replace('_', ' ', $type))); ?></h4>
                            <?php foreach ($type_rrids as $rrid) : ?>
                                <a href="<?php echo esc_url($rrid['url'] ?? '#'); ?>" class="mh-rrid-item" target="_blank">
                                    <span class="id"><?php echo esc_html($rrid['id']); ?></span>
                                </a>
                            <?php endforeach; ?>
                        </div>
                    <?php endforeach; ?>
                </div>
                <?php endif; ?>
                
                <!-- Related Papers Widget -->
                <div class="mh-sidebar-widget">
                    <h3>📚 Related Papers</h3>
                    <?php
                    // Get related papers by shared techniques
                    $related_args = array(
                        'post_type' => 'mh_paper',
                        'posts_per_page' => 5,
                        'post__not_in' => array($post_id),
                        'orderby' => 'meta_value_num',
                        'order' => 'DESC',
                        'meta_key' => '_mh_citation_count',
                    );
                    
                    if (!empty($techniques)) {
                        $related_args['tax_query'] = array(
                            array(
                                'taxonomy' => 'mh_technique',
                                'field' => 'name',
                                'terms' => array_slice($techniques, 0, 3),
                            ),
                        );
                    }
                    
                    $related_papers = new WP_Query($related_args);
                    
                    if ($related_papers->have_posts()) :
                        while ($related_papers->have_posts()) : $related_papers->the_post();
                    ?>
                        <a href="<?php the_permalink(); ?>" class="mh-related-item">
                            <?php echo wp_trim_words(get_the_title(), 10); ?>
                        </a>
                    <?php
                        endwhile;
                        wp_reset_postdata();
                    else :
                    ?>
                        <p class="mh-no-related">No related papers found.</p>
                    <?php endif; ?>
                </div>
                
                <!-- All Tags Widget -->
                <div class="mh-sidebar-widget">
                    <h3>🏷️ All Tags</h3>
                    <div class="mh-tag-list">
                        <?php 
                        $all_tags = array_merge(
                            is_array($techniques) ? $techniques : array(),
                            is_array($microscopes) ? $microscopes : array(),
                            is_array($all_software) ? $all_software : array(),
                            is_array($organisms) ? $organisms : array()
                        );
                        foreach (array_slice($all_tags, 0, 15) as $tag) : 
                        ?>
                            <span class="mh-mini-tag"><?php echo esc_html($tag); ?></span>
                        <?php endforeach; ?>
                    </div>
                </div>
                
            </aside>
        </div>
    </article>
</div>

<style>
/* Single Paper Styles v3.0 */
.microhub-wrapper {
    max-width: 1400px;
    margin: 0 auto;
    padding: 20px;
}

.mh-single-paper {
    background: #0d1117;
    color: #e6edf3;
    min-height: 100vh;
}

/* Header */
.mh-paper-header {
    background: linear-gradient(135deg, #161b22 0%, #0d1117 100%);
    padding: 40px;
    border-bottom: 1px solid #30363d;
}

.mh-badges {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 16px;
}

.mh-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
}

.mh-badge.foundational { background: linear-gradient(135deg, #ffd700, #ff8c00); color: #000; }
.mh-badge.high-impact { background: linear-gradient(135deg, #58a6ff, #a371f7); color: #fff; }
.mh-badge.full-text { background: #238636; color: #fff; }
.mh-badge.has-figures { background: #8957e5; color: #fff; }
.mh-badge.has-protocols { background: #f78166; color: #fff; }
.mh-badge.has-code { background: #21262d; color: #e6edf3; border: 1px solid #30363d; }

.mh-paper-header h1 {
    font-size: 2rem;
    margin: 0 0 16px 0;
    line-height: 1.3;
    color: #e6edf3;
}

.mh-paper-authors {
    color: #8b949e;
    font-size: 0.95rem;
    margin-bottom: 16px;
}

.mh-paper-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 20px;
    margin-bottom: 20px;
}

.mh-meta-item {
    color: #8b949e;
    font-size: 0.9rem;
}

.mh-paper-links {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
}

.mh-btn {
    display: inline-block;
    padding: 8px 16px;
    border-radius: 6px;
    font-size: 0.85rem;
    font-weight: 600;
    text-decoration: none;
    transition: all 0.2s;
}

.mh-btn.doi { background: #238636; color: #fff; }
.mh-btn.pubmed { background: #1f6feb; color: #fff; }
.mh-btn.pmc { background: #388bfd; color: #fff; }
.mh-btn.pdf { background: #da3633; color: #fff; }
.mh-btn.github { background: #21262d; color: #e6edf3; border: 1px solid #30363d; }

.mh-btn:hover { opacity: 0.9; transform: translateY(-1px); }

/* Content Layout */
.mh-paper-content {
    display: grid;
    grid-template-columns: 1fr 320px;
    gap: 30px;
    padding: 30px;
}

.mh-paper-section {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 24px;
    margin-bottom: 20px;
}

.mh-paper-section h2 {
    font-size: 1.2rem;
    margin: 0 0 16px 0;
    color: #e6edf3;
    padding-bottom: 10px;
    border-bottom: 1px solid #30363d;
}

/* Figures Gallery */
.mh-figures-gallery {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 16px;
}

.mh-figure-item {
    background: #0d1117;
    border-radius: 8px;
    overflow: hidden;
}

.mh-figure-link img {
    width: 100%;
    height: 150px;
    object-fit: cover;
    transition: transform 0.2s;
}

.mh-figure-link:hover img {
    transform: scale(1.05);
}

.mh-figure-caption {
    padding: 12px;
}

.mh-figure-caption strong {
    color: #58a6ff;
    font-size: 0.85rem;
}

.mh-figure-caption p {
    color: #8b949e;
    font-size: 0.8rem;
    margin: 8px 0 0 0;
}

/* Methods Section */
.mh-methods-content {
    max-height: 400px;
    overflow: hidden;
    position: relative;
}

.mh-methods-content.expanded {
    max-height: none;
}

.mh-methods-content::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 80px;
    background: linear-gradient(transparent, #161b22);
    pointer-events: none;
}

.mh-methods-content.expanded::after {
    display: none;
}

.mh-expand-btn {
    display: block;
    width: 100%;
    padding: 10px;
    margin-top: 10px;
    background: #21262d;
    border: 1px solid #30363d;
    color: #58a6ff;
    border-radius: 6px;
    cursor: pointer;
}

/* Tags Grid */
.mh-tags-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}

.mh-tag {
    display: inline-block;
    padding: 6px 12px;
    background: #21262d;
    border: 1px solid #30363d;
    border-radius: 20px;
    color: #e6edf3;
    font-size: 0.85rem;
    text-decoration: none;
    transition: all 0.2s;
}

.mh-tag:hover {
    background: #30363d;
    border-color: #58a6ff;
}

.mh-tag.technique { border-color: #58a6ff; }
.mh-tag.microscope-brand { border-color: #f78166; }
.mh-tag.microscope-model { border-color: #d29922; }
.mh-tag.software-analysis { border-color: #a371f7; }
.mh-tag.software-acquisition { border-color: #8957e5; }
.mh-tag.sample-prep { border-color: #238636; }
.mh-tag.fluorophore { border-color: #db61a2; }
.mh-tag.organism { border-color: #3fb950; }

/* Protocol List */
.mh-protocol-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.mh-protocol-item {
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

.mh-protocol-item:hover {
    background: #30363d;
}

.mh-protocol-item .icon { font-size: 1.5rem; }
.mh-protocol-item .name { flex: 1; font-weight: 600; }
.mh-protocol-item .url { color: #8b949e; font-size: 0.8rem; }

/* GitHub Card */
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

.mh-github-card:hover { background: #30363d; }
.mh-github-card .icon { font-size: 2rem; }
.mh-github-card .info { flex: 1; }
.mh-github-card .info strong { display: block; margin-bottom: 4px; }
.mh-github-card .info span { color: #8b949e; font-size: 0.85rem; }

/* Repository List */
.mh-repo-list {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
}

.mh-repo-item {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 8px 16px;
    background: #21262d;
    border-radius: 6px;
    color: #e6edf3;
    text-decoration: none;
}

.mh-repo-item:hover { background: #30363d; }
.mh-repo-item .repo-id { color: #8b949e; font-size: 0.8rem; }

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

.mh-quick-stats ul {
    list-style: none;
    padding: 0;
    margin: 0;
}

.mh-quick-stats li {
    padding: 8px 0;
    border-bottom: 1px solid #21262d;
    color: #8b949e;
}

.mh-quick-stats li strong {
    color: #58a6ff;
    margin-right: 8px;
}

.mh-related-item {
    display: block;
    padding: 8px;
    color: #58a6ff;
    font-size: 0.85rem;
    border-bottom: 1px solid #21262d;
    text-decoration: none;
}

.mh-related-item:hover { background: #21262d; }

.mh-tag-list {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
}

.mh-mini-tag {
    display: inline-block;
    padding: 2px 8px;
    background: #21262d;
    border-radius: 10px;
    font-size: 0.75rem;
    color: #8b949e;
}

.mh-rrid-item {
    display: block;
    padding: 6px 8px;
    background: #21262d;
    border-radius: 4px;
    margin-bottom: 6px;
    font-size: 0.8rem;
    color: #58a6ff;
    text-decoration: none;
}

.mh-rrid-group h4 {
    font-size: 0.75rem;
    color: #8b949e;
    margin: 12px 0 6px 0;
    text-transform: uppercase;
}

/* Comments */
.mh-comments-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
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

.mh-comment-form input,
.mh-comment-form textarea {
    width: 100%;
    padding: 12px;
    border: 1px solid #30363d;
    border-radius: 8px;
    background: #0d1117;
    color: #e6edf3;
    font-size: 0.9rem;
    margin-bottom: 10px;
}

.mh-submit-btn {
    padding: 10px 24px;
    background: #238636;
    border: none;
    border-radius: 6px;
    color: white;
    font-weight: 600;
    cursor: pointer;
}

.mh-submit-btn:hover { background: #2ea043; }

/* Responsive */
@media (max-width: 1024px) {
    .mh-paper-content {
        grid-template-columns: 1fr;
    }
    
    .mh-paper-sidebar {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
    }
}

@media (max-width: 600px) {
    .mh-paper-header { padding: 20px; }
    .mh-paper-header h1 { font-size: 1.5rem; }
    .mh-paper-content { padding: 15px; }
    .mh-paper-sidebar { grid-template-columns: 1fr; }
    .mh-figures-gallery { grid-template-columns: 1fr; }
}
</style>

<?php get_footer(); ?>
