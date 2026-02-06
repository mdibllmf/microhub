<?php
/**
 * Single Protocol Template
 * Displays a single protocol with all metadata and links
 */
get_header();

while (have_posts()) : the_post();
    $post_id = get_the_ID();
    
    // Get protocol metadata
    $doi = get_post_meta($post_id, '_mh_doi', true);
    $protocol_type = get_post_meta($post_id, '_mh_protocol_type', true);
    $protocol_url = get_post_meta($post_id, '_mh_protocol_url', true);
    $year = get_post_meta($post_id, '_mh_year', true);
    $journal = get_post_meta($post_id, '_mh_journal', true);
    $abstract = get_post_meta($post_id, '_mh_abstract', true);
    $citations = intval(get_post_meta($post_id, '_mh_citation_count', true));
    $pubmed_id = get_post_meta($post_id, '_mh_pubmed_id', true);
    
    // Get source - try multiple locations
    $source = $protocol_type;
    if (empty($source)) {
        $protocol_type_terms = wp_get_object_terms($post_id, 'mh_protocol_type', array('fields' => 'names'));
        if (!is_wp_error($protocol_type_terms) && !empty($protocol_type_terms)) {
            $source = $protocol_type_terms[0];
        }
    }
    if (empty($source)) {
        $source = get_post_meta($post_id, '_mh_protocol_source', true);
    }
    if (empty($source)) {
        $source = 'Protocol';
    }
    
    // Get authors
    $authors_json = get_post_meta($post_id, '_mh_authors', true);
    $authors = array();
    if ($authors_json) {
        $authors = json_decode($authors_json, true);
        if (!is_array($authors)) $authors = array();
    }
    
    // Get taxonomies
    $techniques = wp_get_object_terms($post_id, 'mh_technique', array('fields' => 'all'));
    $microscopes = wp_get_object_terms($post_id, 'mh_microscope', array('fields' => 'all'));
    $organisms = wp_get_object_terms($post_id, 'mh_organism', array('fields' => 'all'));
    $software = wp_get_object_terms($post_id, 'mh_software', array('fields' => 'all'));
    $fluorophores = wp_get_object_terms($post_id, 'mh_fluorophore', array('fields' => 'all'));
    
    // Get enrichment data
    $github_url = get_post_meta($post_id, '_mh_github_url', true);
    $github_tools = json_decode(get_post_meta($post_id, '_mh_github_tools', true), true) ?: array();
    $repositories = json_decode(get_post_meta($post_id, '_mh_repositories', true), true) ?: array();
    $rrids = json_decode(get_post_meta($post_id, '_mh_rrids', true), true) ?: array();
    $rors = json_decode(get_post_meta($post_id, '_mh_rors', true), true) ?: array();
    $protocols_linked = json_decode(get_post_meta($post_id, '_mh_protocols', true), true) ?: array();
    $sample_preparation = json_decode(get_post_meta($post_id, '_mh_sample_preparation', true), true) ?: array();
    $cell_lines = json_decode(get_post_meta($post_id, '_mh_cell_lines', true), true) ?: array();
    $microscope_brands = json_decode(get_post_meta($post_id, '_mh_microscope_brands', true), true) ?: array();
    $fluorophores_meta = json_decode(get_post_meta($post_id, '_mh_fluorophores', true), true) ?: array();
    $methods = get_post_meta($post_id, '_mh_methods', true);
    $facility = get_post_meta($post_id, '_mh_facility', true);
    $institutions = json_decode(get_post_meta($post_id, '_mh_institutions', true), true) ?: array();
    
    // Get external URL
    $external_url = '';
    if (!empty($doi)) {
        $external_url = "https://doi.org/{$doi}";
    } elseif (!empty($protocol_url)) {
        $external_url = $protocol_url;
    }
    
    // Get linked paper if exists
    $linked_paper_id = get_post_meta($post_id, '_mh_linked_paper', true);
    $linked_paper = null;
    if ($linked_paper_id) {
        $linked_paper = get_post($linked_paper_id);
    }
    
    // Get figures
    $figures = get_post_meta($post_id, '_mh_figures', true);
    if ($figures) {
        $figures = json_decode($figures, true);
    }
    
    // Source class for styling
    $source_class = 'other';
    $source_lower = strtolower($source);
    if (strpos($source_lower, 'jove') !== false) $source_class = 'jove';
    elseif (strpos($source_lower, 'nature') !== false) $source_class = 'nature';
    elseif (strpos($source_lower, 'star') !== false) $source_class = 'star';
    elseif (strpos($source_lower, 'protocols.io') !== false) $source_class = 'protocols-io';
    elseif (strpos($source_lower, 'bio-protocol') !== false) $source_class = 'bio-protocol';
    
    // Citation badge class
    $citation_badge_class = 'standard';
    if ($citations >= 100) $citation_badge_class = 'foundational';
    elseif ($citations >= 50) $citation_badge_class = 'high-impact';
?>

<div class="mh-single-protocol">
    <div class="mh-protocol-nav">
        <a href="<?php echo esc_url(mh_get_page_url('protocols')); ?>" class="mh-back-link">
            ← Back to Protocols
        </a>
    </div>

    <article class="mh-protocol-article">
        <!-- Header -->
        <header class="mh-protocol-header">
            <div class="mh-protocol-badges">
                <span class="mh-protocol-source-badge <?php echo esc_attr($source_class); ?>">
                    <?php echo esc_html($source); ?>
                </span>
                <?php if ($year): ?>
                    <span class="mh-protocol-year-badge"><?php echo esc_html($year); ?></span>
                <?php endif; ?>
                <span class="mh-protocol-citation-badge <?php echo esc_attr($citation_badge_class); ?>">
                    <?php 
                    if ($citations >= 100) echo '🏆 Foundational';
                    elseif ($citations >= 50) echo '⭐ High Impact';
                    else echo number_format($citations) . ' citations';
                    ?>
                </span>
            </div>
            
            <h1 class="mh-protocol-title"><?php the_title(); ?></h1>
            
            <?php if (!empty($authors)): ?>
                <div class="mh-protocol-authors">
                    <?php 
                    $author_names = is_array($authors) ? (isset($authors[0]['name']) ? array_column($authors, 'name') : $authors) : array();
                    $total_authors = count($author_names);
                    $display_limit = 8;
                    
                    foreach (array_slice($author_names, 0, $display_limit) as $i => $name): 
                        $is_last = ($i === $total_authors - 1) || ($i === $display_limit - 1 && $total_authors > $display_limit);
                        $author_class = ($i === $total_authors - 1) ? 'mh-author-link mh-last-author' : 'mh-author-link';
                    ?>
                        <a href="<?php echo esc_url(home_url('/?author=' . urlencode($name))); ?>" class="<?php echo esc_attr($author_class); ?>">
                            <?php echo esc_html($name); ?></a><?php echo ($i < min($display_limit, $total_authors) - 1) ? ', ' : ''; ?>
                    <?php endforeach; 
                    
                    if ($total_authors > $display_limit): ?>
                        <span class="mh-author-more">... and <?php echo $total_authors - $display_limit; ?> more</span>
                    <?php endif; ?>
                </div>
                <?php if ($total_authors > 1): 
                    $last_author = end($author_names);
                ?>
                <div class="mh-last-author-note">
                    <strong>Last Author:</strong> 
                    <a href="<?php echo esc_url(home_url('/?author=' . urlencode($last_author))); ?>" class="mh-author-link mh-last-author">
                        <?php echo esc_html($last_author); ?>
                    </a>
                </div>
                <?php endif; ?>
            <?php endif; ?>
            
            <div class="mh-protocol-meta">
                <?php if ($journal): ?>
                    <span class="mh-meta-item">📰 <?php echo esc_html($journal); ?></span>
                <?php endif; ?>
                <?php if ($year): ?>
                    <span class="mh-meta-item">📅 <?php echo esc_html($year); ?></span>
                <?php endif; ?>
                <?php if ($citations > 0): ?>
                    <span class="mh-meta-item">📊 <?php echo number_format($citations); ?> citations</span>
                <?php endif; ?>
            </div>
        </header>

        <!-- Action Buttons -->
        <div class="mh-protocol-actions">
            <?php if ($external_url): ?>
                <a href="<?php echo esc_url($external_url); ?>" target="_blank" rel="noopener" class="mh-action-btn primary">
                    🔗 View Protocol
                </a>
            <?php endif; ?>
            
            <?php if ($doi): ?>
                <a href="https://doi.org/<?php echo esc_attr($doi); ?>" target="_blank" rel="noopener" class="mh-action-btn">
                    📄 DOI
                </a>
            <?php endif; ?>
            
            <?php if ($pubmed_id): ?>
                <a href="https://pubmed.ncbi.nlm.nih.gov/<?php echo esc_attr($pubmed_id); ?>/" target="_blank" rel="noopener" class="mh-action-btn pubmed">
                    🔬 PubMed
                </a>
            <?php endif; ?>
            
            <?php if ($github_url || !empty($github_tools)): ?>
                <a href="<?php echo esc_url($github_url ?: ($github_tools[0]['url'] ?? '#')); ?>" target="_blank" rel="noopener" class="mh-action-btn github">
                    💻 GitHub
                </a>
            <?php endif; ?>
            
            <?php if ($linked_paper): ?>
                <a href="<?php echo get_permalink($linked_paper->ID); ?>" class="mh-action-btn">
                    📑 View Related Paper
                </a>
            <?php endif; ?>
        </div>

        <!-- Abstract -->
        <?php if (!empty($abstract)): ?>
            <section class="mh-protocol-section">
                <h2>Abstract</h2>
                <div class="mh-protocol-abstract">
                    <?php echo wp_kses_post(nl2br($abstract)); ?>
                </div>
            </section>
        <?php elseif (get_the_content()): ?>
            <section class="mh-protocol-section">
                <h2>Description</h2>
                <div class="mh-protocol-abstract">
                    <?php the_content(); ?>
                </div>
            </section>
        <?php endif; ?>

        <!-- Taxonomy Tags -->
        <?php if (!is_wp_error($techniques) && !empty($techniques)): ?>
            <section class="mh-protocol-section">
                <h2>🔬 Techniques</h2>
                <div class="mh-tag-list">
                    <?php foreach ($techniques as $term): ?>
                        <a href="<?php echo get_term_link($term); ?>" class="mh-tag technique">
                            <?php echo esc_html($term->name); ?>
                        </a>
                    <?php endforeach; ?>
                </div>
            </section>
        <?php endif; ?>

        <?php if (!is_wp_error($microscopes) && !empty($microscopes)): ?>
            <section class="mh-protocol-section">
                <h2>🔭 Microscopes</h2>
                <div class="mh-tag-list">
                    <?php foreach ($microscopes as $term): ?>
                        <a href="<?php echo get_term_link($term); ?>" class="mh-tag microscope">
                            <?php echo esc_html($term->name); ?>
                        </a>
                    <?php endforeach; ?>
                </div>
            </section>
        <?php endif; ?>

        <?php if (!is_wp_error($organisms) && !empty($organisms)): ?>
            <section class="mh-protocol-section">
                <h2>🧬 Organisms</h2>
                <div class="mh-tag-list">
                    <?php foreach ($organisms as $term): ?>
                        <a href="<?php echo get_term_link($term); ?>" class="mh-tag organism">
                            <?php echo esc_html($term->name); ?>
                        </a>
                    <?php endforeach; ?>
                </div>
            </section>
        <?php endif; ?>

        <?php if (!is_wp_error($software) && !empty($software)): ?>
            <section class="mh-protocol-section">
                <h2>💻 Software</h2>
                <div class="mh-tag-list">
                    <?php foreach ($software as $term): ?>
                        <a href="<?php echo get_term_link($term); ?>" class="mh-tag software">
                            <?php echo esc_html($term->name); ?>
                        </a>
                    <?php endforeach; ?>
                </div>
            </section>
        <?php endif; ?>

        <?php if (!is_wp_error($fluorophores) && !empty($fluorophores)): ?>
            <section class="mh-protocol-section">
                <h2>✨ Fluorophores</h2>
                <div class="mh-tag-list">
                    <?php foreach ($fluorophores as $term): ?>
                        <a href="<?php echo get_term_link($term); ?>" class="mh-tag fluorophore">
                            <?php echo esc_html($term->name); ?>
                        </a>
                    <?php endforeach; ?>
                </div>
            </section>
        <?php endif; ?>

        <?php if (!empty($sample_preparation)): ?>
            <section class="mh-protocol-section">
                <h2>🧫 Sample Preparation</h2>
                <div class="mh-tag-list">
                    <?php foreach ($sample_preparation as $prep): ?>
                        <span class="mh-tag sample-prep"><?php echo esc_html($prep); ?></span>
                    <?php endforeach; ?>
                </div>
            </section>
        <?php endif; ?>

        <?php if (!empty($cell_lines)): ?>
            <section class="mh-protocol-section">
                <h2>🔬 Cell Lines</h2>
                <div class="mh-tag-list">
                    <?php foreach ($cell_lines as $cell): ?>
                        <span class="mh-tag cell-line"><?php echo esc_html($cell); ?></span>
                    <?php endforeach; ?>
                </div>
            </section>
        <?php endif; ?>

        <?php if (!empty($microscope_brands)): ?>
            <section class="mh-protocol-section">
                <h2>🏭 Microscope Brands</h2>
                <div class="mh-tag-list">
                    <?php foreach ($microscope_brands as $brand): ?>
                        <span class="mh-tag brand"><?php echo esc_html($brand); ?></span>
                    <?php endforeach; ?>
                </div>
            </section>
        <?php endif; ?>

        <!-- GitHub Code & Software - using same helper function as papers -->
        <?php mh_display_github($github_url, $github_tools); ?>

        <!-- Data Repositories - using same helper function as papers -->
        <?php mh_display_repositories($repositories); ?>

        <!-- RRIDs - using same display as papers -->
        <?php if (function_exists('mh_display_rrids') && !empty($rrids)): ?>
            <section class="mh-protocol-section">
                <h2>🏷️ Research Resource Identifiers (RRIDs)</h2>
                <p class="mh-section-note">Verified research resources used in this protocol:</p>
                <?php mh_display_rrids($rrids); ?>
            </section>
        <?php elseif (!empty($rrids)): ?>
            <section class="mh-protocol-section">
                <h2>🏷️ Research Resource Identifiers (RRIDs)</h2>
                <p class="mh-section-note">Verified research resources used in this protocol:</p>
                <div class="mh-rrids-list">
                    <?php foreach ($rrids as $rrid):
                        $rrid_id = isset($rrid['id']) ? $rrid['id'] : (is_string($rrid) ? $rrid : '');
                        $rrid_name = isset($rrid['name']) ? $rrid['name'] : '';
                        if (empty($rrid_id)) continue;
                    ?>
                        <div class="mh-rrid-item">
                            <a href="https://scicrunch.org/resolver/<?php echo esc_attr($rrid_id); ?>" target="_blank" rel="noopener" class="mh-rrid-link">
                                <?php echo esc_html($rrid_id); ?>
                            </a>
                            <?php if ($rrid_name): ?>
                                <span class="mh-rrid-name"><?php echo esc_html($rrid_name); ?></span>
                            <?php endif; ?>
                        </div>
                    <?php endforeach; ?>
                </div>
            </section>
        <?php endif; ?>

        <!-- RORs - using same display as papers -->
        <?php if (function_exists('mh_display_rors') && !empty($rors)): ?>
            <section class="mh-protocol-section">
                <h2>🏛️ Research Organizations (ROR)</h2>
                <p class="mh-section-note">Affiliated research institutions:</p>
                <?php mh_display_rors($rors); ?>
            </section>
        <?php endif; ?>

        <?php if (!empty($protocols_linked)): ?>
            <section class="mh-protocol-section">
                <h2>📋 Linked Protocols</h2>
                <div class="mh-protocols-list">
                    <?php foreach ($protocols_linked as $proto): 
                        $proto_url = isset($proto['url']) ? $proto['url'] : (is_string($proto) ? $proto : '');
                        $proto_name = isset($proto['name']) ? $proto['name'] : 'Protocol';
                        if (empty($proto_url)) continue;
                    ?>
                        <a href="<?php echo esc_url($proto_url); ?>" class="mh-protocol-link-item" target="_blank" rel="noopener">
                            📋 <?php echo esc_html($proto_name); ?>
                        </a>
                    <?php endforeach; ?>
                </div>
            </section>
        <?php endif; ?>

        <!-- Figures -->
        <?php if (!empty($figures) && is_array($figures)): ?>
            <section class="mh-protocol-section">
                <h2>📊 Figures</h2>
                <div class="mh-figures-grid">
                    <?php foreach ($figures as $fig): 
                        $fig_url = isset($fig['url']) ? $fig['url'] : '';
                        $fig_caption = isset($fig['caption']) ? $fig['caption'] : '';
                        if (empty($fig_url)) continue;
                    ?>
                        <div class="mh-figure-card">
                            <a href="<?php echo esc_url($fig_url); ?>" target="_blank" rel="noopener">
                                <img src="<?php echo esc_url($fig_url); ?>" alt="<?php echo esc_attr($fig_caption); ?>" loading="lazy">
                            </a>
                            <?php if ($fig_caption): ?>
                                <p class="mh-figure-caption"><?php echo esc_html(wp_trim_words($fig_caption, 15)); ?></p>
                            <?php endif; ?>
                        </div>
                    <?php endforeach; ?>
                </div>
            </section>
        <?php endif; ?>

        <!-- Comments -->
        <section class="mh-protocol-section mh-comments-section">
            <div class="mh-comments-header">
                <h2>💬 Discussion</h2>
                <span class="mh-comments-count"><?php echo get_comments_number(); ?></span>
            </div>
            
            <?php
            $comments = get_comments(array('post_id' => $post_id, 'status' => 'approve'));
            if ($comments):
                foreach ($comments as $comment):
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
                endforeach;
            else:
            ?>
                <p style="color: var(--text-muted);">No comments yet. Be the first to discuss this protocol!</p>
            <?php endif; ?>

            <?php if (comments_open()): ?>
                <div class="mh-comment-form">
                    <h3>Add a Comment</h3>
                    <form action="<?php echo esc_url(site_url('/wp-comments-post.php')); ?>" method="post">
                        <div class="mh-form-row-inline">
                            <div class="mh-form-row">
                                <label for="author">Name *</label>
                                <input type="text" name="author" id="author" required placeholder="Your name">
                            </div>
                            <div class="mh-form-row">
                                <label for="email">Email *</label>
                                <input type="email" name="email" id="email" required placeholder="your@email.com">
                            </div>
                        </div>
                        <div class="mh-form-row">
                            <label for="comment">Comment *</label>
                            <textarea name="comment" id="comment" rows="4" required placeholder="Share your thoughts..."></textarea>
                        </div>
                        <input type="hidden" name="comment_post_ID" value="<?php echo $post_id; ?>">
                        <?php wp_nonce_field('unfiltered-html-comment'); ?>
                        <button type="submit" class="mh-btn mh-btn-primary">Post Comment</button>
                    </form>
                </div>
            <?php endif; ?>
        </section>
    </article>
</div>

<style>
.mh-single-protocol {
    max-width: 900px;
    margin: 0 auto;
    padding: 24px;
}

/* Navigation */
.mh-protocol-nav {
    margin-bottom: 24px;
}
.mh-back-link {
    color: var(--text-muted, #8b949e);
    text-decoration: none;
    font-size: 0.9rem;
}
.mh-back-link:hover {
    color: var(--primary, #58a6ff);
}

/* Article */
.mh-protocol-article {
    background: var(--bg-card, #161b22);
    border: 1px solid var(--border, #30363d);
    border-radius: 12px;
    padding: 32px;
}

/* Header */
.mh-protocol-header {
    margin-bottom: 24px;
    padding-bottom: 24px;
    border-bottom: 1px solid var(--border, #30363d);
}
.mh-protocol-badges {
    display: flex;
    gap: 10px;
    margin-bottom: 16px;
    flex-wrap: wrap;
}
.mh-protocol-source-badge {
    display: inline-block;
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 600;
    text-transform: uppercase;
}
.mh-protocol-source-badge.jove { background: #1e3a5f; color: #58a6ff; }
.mh-protocol-source-badge.nature { background: #2d1f3d; color: #a371f7; }
.mh-protocol-source-badge.star { background: #3d2f1f; color: #f0883e; }
.mh-protocol-source-badge.protocols-io { background: #1f3d2d; color: #56d364; }
.mh-protocol-source-badge.bio-protocol { background: #3d1f2d; color: #f778ba; }
.mh-protocol-source-badge.other { background: #2d2d2d; color: #8b949e; }

.mh-protocol-year-badge {
    display: inline-block;
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 0.85rem;
    background: var(--bg-hover, #21262d);
    color: var(--text-muted, #8b949e);
}

.mh-protocol-citation-badge {
    display: inline-block;
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 600;
}
.mh-protocol-citation-badge.foundational {
    background: linear-gradient(135deg, #ffd700, #ff8c00);
    color: #000;
}
.mh-protocol-citation-badge.high-impact {
    background: linear-gradient(135deg, #58a6ff, #a371f7);
    color: #fff;
}
.mh-protocol-citation-badge.standard {
    background: var(--bg-hover, #21262d);
    color: var(--text-muted, #8b949e);
}

.mh-protocol-title {
    font-size: 1.75rem;
    margin: 0 0 16px 0;
    color: var(--text, #c9d1d9);
    line-height: 1.3;
}
.mh-protocol-authors {
    color: var(--text-muted, #8b949e);
    font-size: 0.95rem;
    margin-bottom: 8px;
    line-height: 1.6;
}
.mh-protocol-authors .mh-author-link {
    color: var(--text-muted, #8b949e);
    text-decoration: none;
    transition: color 0.2s;
}
.mh-protocol-authors .mh-author-link:hover {
    color: var(--primary, #58a6ff);
    text-decoration: underline;
}
.mh-protocol-authors .mh-last-author {
    color: var(--primary, #58a6ff);
    font-weight: 500;
}
.mh-author-more {
    color: var(--text-light, #6e7681);
    font-style: italic;
}
.mh-last-author-note {
    color: var(--text-muted, #8b949e);
    font-size: 0.9rem;
    margin-top: 8px;
    padding: 8px 12px;
    background: var(--bg-hover, #21262d);
    border-radius: 6px;
    display: inline-block;
}
.mh-protocol-meta {
    display: flex;
    gap: 16px;
    flex-wrap: wrap;
    margin-top: 12px;
    color: var(--text-light, #6e7681);
    font-size: 0.9rem;
}
.mh-protocol-journal {
    color: var(--text-light, #6e7681);
    font-size: 0.9rem;
}

/* Actions */
.mh-protocol-actions {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    margin-bottom: 24px;
}
.mh-action-btn {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 10px 18px;
    border-radius: 6px;
    text-decoration: none;
    font-size: 0.9rem;
    font-weight: 500;
    background: var(--bg-hover, #21262d);
    color: var(--text, #c9d1d9);
    border: 1px solid var(--border, #30363d);
    transition: all 0.2s;
}
.mh-action-btn:hover {
    background: var(--border, #30363d);
}
.mh-action-btn.primary {
    background: var(--primary, #58a6ff);
    border-color: var(--primary, #58a6ff);
    color: #fff;
}
.mh-action-btn.primary:hover {
    background: var(--primary-hover, #79b8ff);
}

/* Sections - support both protocol-section and paper-section (from helper functions) */
.mh-protocol-section,
.mh-paper-section {
    margin-bottom: 24px;
    padding-bottom: 24px;
    border-bottom: 1px solid var(--border, #30363d);
}
.mh-protocol-section:last-child,
.mh-paper-section:last-child {
    border-bottom: none;
    margin-bottom: 0;
    padding-bottom: 0;
}
.mh-protocol-section h2,
.mh-paper-section h2 {
    font-size: 1.1rem;
    margin: 0 0 16px 0;
    color: var(--text, #c9d1d9);
}
.mh-protocol-abstract {
    color: var(--text-light, #8b949e);
    line-height: 1.7;
}

/* Tags */
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
.mh-tag:hover {
    filter: brightness(1.2);
}

/* Section Notes */
.mh-section-note {
    color: var(--text-muted, #8b949e);
    font-size: 0.9rem;
    margin-bottom: 12px;
}

/* Repositories List */
.mh-repositories-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
}
.mh-repository-link {
    display: inline-flex;
    align-items: center;
    padding: 10px 14px;
    background: var(--bg-hover, #21262d);
    border-radius: 6px;
    color: var(--text, #c9d1d9);
    text-decoration: none;
    transition: all 0.2s;
}
.mh-repository-link:hover {
    background: var(--primary, #58a6ff);
    color: white;
}

/* RRIDs List */
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
    background: var(--bg-hover, #21262d);
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
.mh-rrid-name {
    color: var(--text-muted, #8b949e);
}

/* Protocols List */
.mh-protocols-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
}
.mh-protocol-link-item {
    display: inline-flex;
    align-items: center;
    padding: 10px 14px;
    background: var(--bg-hover, #21262d);
    border-radius: 6px;
    color: var(--secondary, #3b82f6);
    text-decoration: none;
    transition: all 0.2s;
}
.mh-protocol-link-item:hover {
    background: var(--secondary, #3b82f6);
    color: white;
}

/* Figures */
.mh-figures-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 16px;
}
.mh-figure-card {
    background: var(--bg-hover, #21262d);
    border-radius: 8px;
    overflow: hidden;
}
.mh-figure-card img {
    width: 100%;
    height: 150px;
    object-fit: cover;
}
.mh-figure-caption {
    padding: 10px;
    font-size: 0.8rem;
    color: var(--text-muted, #8b949e);
    margin: 0;
}

/* Comments */
.mh-comments-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 16px;
}
.mh-comments-header h2 {
    margin: 0;
}
.mh-comments-count {
    background: var(--primary, #58a6ff);
    color: #fff;
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 0.85rem;
}
.mh-comment {
    display: flex;
    gap: 12px;
    padding: 16px;
    background: var(--bg-hover, #21262d);
    border-radius: 8px;
    margin-bottom: 12px;
}
.mh-comment-avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: linear-gradient(135deg, var(--primary, #58a6ff), #a371f7);
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 0.85rem;
    color: #fff;
    flex-shrink: 0;
}
.mh-comment-content {
    flex: 1;
}
.mh-comment-meta {
    display: flex;
    gap: 12px;
    margin-bottom: 6px;
}
.mh-comment-author {
    font-weight: 600;
    color: var(--text, #c9d1d9);
}
.mh-comment-date {
    color: var(--text-light, #6e7681);
    font-size: 0.85rem;
}
.mh-comment-text {
    color: var(--text-light, #8b949e);
    line-height: 1.5;
}

/* Comment Form */
.mh-comment-form {
    background: var(--bg-hover, #21262d);
    border-radius: 8px;
    padding: 20px;
    margin-top: 20px;
}
.mh-comment-form h3 {
    margin: 0 0 16px 0;
    font-size: 1rem;
    color: var(--text, #c9d1d9);
}
.mh-form-row {
    margin-bottom: 12px;
}
.mh-form-row label {
    display: block;
    margin-bottom: 4px;
    font-size: 0.85rem;
    color: var(--text-muted, #8b949e);
}
.mh-form-row input,
.mh-form-row textarea {
    width: 100%;
    padding: 10px 12px;
    background: var(--bg-card, #161b22);
    border: 1px solid var(--border, #30363d);
    border-radius: 6px;
    color: var(--text, #c9d1d9);
    font-family: inherit;
}
.mh-form-row input:focus,
.mh-form-row textarea:focus {
    outline: none;
    border-color: var(--primary, #58a6ff);
}
.mh-form-row-inline {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
}
.mh-btn {
    padding: 10px 20px;
    border-radius: 6px;
    font-weight: 500;
    cursor: pointer;
    border: none;
}
.mh-btn-primary {
    background: var(--primary, #58a6ff);
    color: #fff;
}
.mh-btn-primary:hover {
    background: var(--primary-hover, #79b8ff);
}

/* GitHub Tools List */
.mh-github-tools-list {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 16px;
}

/* GitHub Tool Card */
.mh-github-tool-card {
    display: block;
    padding: 16px;
    background: var(--bg-hover, #21262d);
    border: 1px solid var(--border, #30363d);
    border-radius: 8px;
    text-decoration: none;
    transition: all 0.2s;
}
.mh-github-tool-card:hover {
    border-color: var(--primary, #58a6ff);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
}
.mh-github-tool-card.health-active { border-left: 3px solid #56d364; }
.mh-github-tool-card.health-moderate { border-left: 3px solid #f0883e; }
.mh-github-tool-card.health-low { border-left: 3px solid #f85149; }
.mh-github-tool-card.health-archived { border-left: 3px solid #8b949e; opacity: 0.7; }
.mh-github-tool-card.health-unknown { border-left: 3px solid #30363d; }

.mh-ght-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 8px;
    margin-bottom: 8px;
}
.mh-ght-name {
    color: var(--primary, #58a6ff);
    font-size: 0.95rem;
    word-break: break-word;
}
.mh-ght-health {
    flex-shrink: 0;
    font-size: 0.7rem;
    padding: 2px 8px;
    border-radius: 10px;
    font-weight: 600;
}
.mh-ght-health.active { background: #1f3d2d; color: #56d364; }
.mh-ght-health.moderate { background: #3d2f1f; color: #f0883e; }
.mh-ght-health.low { background: #3d1f1f; color: #f85149; }
.mh-ght-health.archived { background: #2d2d2d; color: #8b949e; }
.mh-ght-health.unknown { background: #21262d; color: #6e7681; }

.mh-ght-desc {
    color: var(--text-muted, #8b949e);
    font-size: 0.85rem;
    line-height: 1.4;
    margin: 8px 0;
}

.mh-ght-metrics {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    font-size: 0.8rem;
    color: var(--text-light, #6e7681);
    margin-bottom: 8px;
}
.mh-ght-rel {
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.75rem;
}
.mh-ght-rel.introduces { background: #1f3d2d; color: #56d364; }
.mh-ght-rel.uses { background: #1e3a5f; color: #58a6ff; }
.mh-ght-rel.extends { background: #2d1f3d; color: #a371f7; }
.mh-ght-rel.benchmarks { background: #3d2f1f; color: #f0883e; }

.mh-ght-topics {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    margin-top: 8px;
}
.mh-ght-topic {
    font-size: 0.7rem;
    padding: 2px 6px;
    background: var(--bg-card, #161b22);
    border-radius: 4px;
    color: var(--text-muted, #8b949e);
}

/* Simple GitHub Card (fallback) */
.mh-github-card {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 16px;
    background: var(--bg-hover, #21262d);
    border: 1px solid var(--border, #30363d);
    border-radius: 8px;
    text-decoration: none;
    transition: all 0.2s;
}
.mh-github-card:hover {
    border-color: var(--primary, #58a6ff);
    background: #161b22;
}
.mh-github-icon {
    font-size: 1.5rem;
}
.mh-github-info {
    flex: 1;
}
.mh-github-info strong {
    display: block;
    color: var(--text, #c9d1d9);
    margin-bottom: 2px;
}
.mh-github-info span {
    color: var(--text-muted, #8b949e);
    font-size: 0.85rem;
}
.mh-github-arrow {
    color: var(--text-muted, #8b949e);
    font-size: 1.2rem;
}

/* Data Repository List */
.mh-repo-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
}
.mh-repo-card {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 14px 16px;
    background: var(--bg-hover, #21262d);
    border: 1px solid var(--border, #30363d);
    border-radius: 8px;
    text-decoration: none;
    transition: all 0.2s;
}
.mh-repo-card:hover {
    border-color: var(--primary, #58a6ff);
    background: #161b22;
}
.mh-repo-icon {
    font-size: 1.3rem;
}
.mh-repo-info {
    flex: 1;
}
.mh-repo-info strong {
    display: block;
    color: var(--text, #c9d1d9);
    margin-bottom: 2px;
}
.mh-repo-info span {
    color: var(--text-muted, #8b949e);
    font-size: 0.85rem;
    font-family: monospace;
}
.mh-repo-arrow {
    color: var(--text-muted, #8b949e);
    font-size: 1.2rem;
}

/* Responsive */
@media (max-width: 768px) {
    .mh-single-protocol {
        padding: 16px;
    }
    .mh-protocol-article {
        padding: 20px;
    }
    .mh-protocol-title {
        font-size: 1.4rem;
    }
    .mh-form-row-inline {
        grid-template-columns: 1fr;
    }
    .mh-protocol-actions {
        flex-direction: column;
    }
    .mh-action-btn {
        justify-content: center;
    }
    .mh-github-tools-list {
        grid-template-columns: 1fr;
    }
}
</style>

<?php endwhile; ?>

<?php get_footer(); ?>
