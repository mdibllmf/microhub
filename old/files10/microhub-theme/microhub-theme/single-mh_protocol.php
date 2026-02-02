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
            </div>
            
            <h1 class="mh-protocol-title"><?php the_title(); ?></h1>
            
            <?php if (!empty($authors)): ?>
                <div class="mh-protocol-authors">
                    <?php 
                    $author_names = array_column($authors, 'name');
                    echo esc_html(implode(', ', $author_names));
                    ?>
                </div>
            <?php endif; ?>
            
            <?php if ($journal): ?>
                <div class="mh-protocol-journal">
                    📰 <?php echo esc_html($journal); ?>
                </div>
            <?php endif; ?>
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
                    📄 DOI: <?php echo esc_html($doi); ?>
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

/* Sections */
.mh-protocol-section {
    margin-bottom: 24px;
    padding-bottom: 24px;
    border-bottom: 1px solid var(--border, #30363d);
}
.mh-protocol-section:last-child {
    border-bottom: none;
    margin-bottom: 0;
    padding-bottom: 0;
}
.mh-protocol-section h2 {
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
.mh-tag:hover {
    filter: brightness(1.2);
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
}
</style>

<?php endwhile; ?>

<?php get_footer(); ?>
