<?php
/**
 * Single Paper Template
 */
get_header();

$meta = mh_get_paper_meta();
?>

<div class="mh-container">
    <div class="mh-layout-sidebar">
        <!-- Main Content -->
        <div class="mh-paper-content">
            <!-- Header -->
            <header class="mh-paper-header">
                <?php mh_paper_badge($meta['citations']); ?>
                
                <h1><?php the_title(); ?></h1>
                
                <?php if ($meta['authors']): ?>
                    <div class="mh-paper-authors">
                        <?php mh_display_clickable_authors($meta['authors'], 8, true); ?>
                    </div>
                    <?php 
                    $last_author = mh_get_last_author($meta['authors']);
                    if ($last_author): 
                    ?>
                    <div class="mh-last-author-note">
                        <strong>Last Author:</strong> 
                        <a href="<?php echo esc_url(mh_author_search_url($last_author)); ?>" class="mh-author-link mh-last-author">
                            <?php echo esc_html($last_author); ?>
                        </a>
                    </div>
                    <?php endif; ?>
                <?php endif; ?>
                
                <?php mh_display_paper_meta($meta); ?>
                <?php mh_display_paper_tags(); ?>
                <?php mh_display_paper_links($meta); ?>
            </header>
            
            <!-- Abstract with Tag Highlighting -->
            <?php mh_display_abstract_with_tags(); ?>
            
            <!-- Techniques -->
            <?php 
            if (taxonomy_exists('mh_technique')) {
                $techniques = get_the_terms(get_the_ID(), 'mh_technique');
                if ($techniques && !is_wp_error($techniques)): 
            ?>
            <section class="mh-paper-section">
                <h2>🔬 Techniques</h2>
                <div class="mh-tags">
                    <?php foreach ($techniques as $term): 
                        $link = get_term_link($term);
                        if (!is_wp_error($link)):
                    ?>
                        <a href="<?php echo esc_url($link); ?>" class="mh-tag mh-tag-technique"><?php echo esc_html($term->name); ?></a>
                    <?php endif; endforeach; ?>
                </div>
            </section>
            <?php endif; 
            }
            
            <!-- Microscope Details -->
            <?php if ($meta['microscope_details']): ?>
            <section class="mh-paper-section">
                <h2>🔭 Microscope Details</h2>
                <p style="color: var(--text-light);"><?php echo nl2br(esc_html($meta['microscope_details'])); ?></p>
            </section>
            <?php endif; ?>
            
            <!-- Protocols -->
            <?php mh_display_protocols($meta['protocols']); ?>
            
            <!-- GitHub -->
            <?php mh_display_github($meta['github_url'], $meta['github_tools']); ?>
            
            <!-- Data Repositories -->
            <?php mh_display_repositories($meta['repositories']); ?>
            
            <!-- RRIDs in Main Content -->
            <?php if (!empty($meta['rrids'])): ?>
            <section class="mh-paper-section">
                <h2>🏷️ Research Resource Identifiers (RRIDs)</h2>
                <p style="color: var(--text-muted); margin-bottom: 16px; font-size: 0.9rem;">Verified research resources used in this paper:</p>
                <?php mh_display_rrids($meta['rrids']); ?>
            </section>
            <?php endif; ?>
            
            <!-- RORs in Main Content -->
            <?php if (!empty($meta['rors'])): ?>
            <section class="mh-paper-section">
                <h2>🏛️ Research Organizations (ROR)</h2>
                <p style="color: var(--text-muted); margin-bottom: 16px; font-size: 0.9rem;">Affiliated research institutions:</p>
                <?php mh_display_rors($meta['rors']); ?>
            </section>
            <?php endif; ?>
            
            <!-- Fluorophores & Dyes -->
            <?php 
            if (!empty($meta['fluorophores'])) {
                mh_display_fluorophores($meta['fluorophores']);
            }
            ?>
            
            <!-- Sample Preparation -->
            <?php 
            if (!empty($meta['sample_preparation'])) {
                mh_display_sample_preparation($meta['sample_preparation']);
            }
            ?>
            
            <!-- Cell Lines -->
            <?php 
            if (!empty($meta['cell_lines'])) {
                mh_display_cell_lines($meta['cell_lines']);
            }
            ?>
            
            <!-- Microscope Equipment -->
            <?php mh_display_equipment($meta); ?>
            
            <!-- Methods Section -->
            <?php 
            if (!empty($meta['methods'])) {
                mh_display_methods($meta['methods']);
            }
            ?>
            
            <!-- Figures -->
            <?php 
            if (!empty($meta['figures'])) {
                mh_display_figures($meta['figures']);
            }
            ?>
            
            <!-- Full Text removed - no longer stored to save space -->
            
            <!-- References -->
            <?php mh_display_references(); ?>
            
            <!-- Research Institutions -->
            <?php mh_display_facility($meta['facility']); ?>
            
            <!-- Comments/Discussion -->
            <section class="mh-paper-section">
                <div class="mh-comments-header">
                    <h2>💬 Discussion</h2>
                    <span class="mh-comments-count"><?php echo get_comments_number(); ?></span>
                </div>
                
                <?php
                $comments = get_comments(array('post_id' => get_the_ID(), 'status' => 'approve'));
                
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
                    <p style="color: var(--text-muted);">No comments yet. Be the first to discuss this paper!</p>
                <?php endif; ?>
                
                <!-- Comment Form -->
                <div class="mh-comment-form">
                    <h4>Add a Comment</h4>
                    <form action="<?php echo esc_url(site_url('/wp-comments-post.php')); ?>" method="post">
                        <?php if (!is_user_logged_in()): ?>
                        <div class="mh-form-row">
                            <div class="mh-form-group">
                                <label>Name <span class="required">*</span></label>
                                <input type="text" name="author" required>
                            </div>
                            <div class="mh-form-group">
                                <label>Email <span style="color: var(--text-muted);">(optional)</span></label>
                                <input type="email" name="email">
                            </div>
                        </div>
                        <?php else: 
                            $current_user = wp_get_current_user();
                        ?>
                        <p style="color: var(--text-muted); margin-bottom: 16px;">Commenting as <strong><?php echo esc_html($current_user->display_name); ?></strong></p>
                        <?php endif; ?>
                        
                        <div class="mh-form-group">
                            <label>Comment <span class="required">*</span></label>
                            <textarea name="comment" rows="4" required placeholder="Share your thoughts on this paper..."></textarea>
                        </div>
                        
                        <input type="hidden" name="comment_post_ID" value="<?php echo get_the_ID(); ?>">
                        <?php wp_nonce_field('unfiltered-html-comment'); ?>
                        <button type="submit" class="mh-submit-btn">Post Comment</button>
                    </form>
                </div>
            </section>
        </div>
        
        <!-- Sidebar -->
        <aside class="mh-sidebar">
            <!-- Paper Info -->
            <div class="mh-sidebar-widget">
                <h3>📊 Paper Info</h3>
                <div class="mh-stats-list">
                    <?php if ($meta['citations']): ?>
                    <div class="mh-stat-row">
                        <span class="mh-stat-label">Citations</span>
                        <span class="mh-stat-value"><?php echo number_format($meta['citations']); ?></span>
                    </div>
                    <?php endif; ?>
                    <?php if ($meta['year']): ?>
                    <div class="mh-stat-row">
                        <span class="mh-stat-label">Year</span>
                        <span class="mh-stat-value"><?php echo esc_html($meta['year']); ?></span>
                    </div>
                    <?php endif; ?>
                    <?php if ($meta['journal']): ?>
                    <div class="mh-stat-row">
                        <span class="mh-stat-label">Journal</span>
                        <span class="mh-stat-value"><?php echo esc_html($meta['journal']); ?></span>
                    </div>
                    <?php endif; ?>
                    <?php if ($meta['doi']): ?>
                    <div class="mh-stat-row">
                        <span class="mh-stat-label">DOI</span>
                        <span class="mh-stat-value" style="font-family: monospace; font-size: 0.8rem;"><?php echo esc_html($meta['doi']); ?></span>
                    </div>
                    <?php endif; ?>
                </div>
            </div>
            
            <!-- Quick Links -->
            <div class="mh-sidebar-widget">
                <h3>🔗 Quick Links</h3>
                <div style="display: flex; flex-direction: column; gap: 8px;">
                    <?php if ($meta['github_url'] || !empty($meta['github_tools'])): ?>
                        <?php 
                        $gh_link = $meta['github_url'];
                        if (!$gh_link && !empty($meta['github_tools'])) {
                            $gh_link = $meta['github_tools'][0]['url'] ?? '';
                        }
                        if ($gh_link):
                        ?>
                        <a href="<?php echo esc_url($gh_link); ?>" class="mh-btn mh-btn-github" target="_blank" style="justify-content: center;">🐙 View Code</a>
                        <?php endif; ?>
                    <?php endif; ?>
                    <?php if ($meta['pdf_url']): ?>
                        <a href="<?php echo esc_url($meta['pdf_url']); ?>" class="mh-btn mh-btn-pdf" target="_blank" style="justify-content: center;">📄 Download PDF</a>
                    <?php endif; ?>
                    <?php if (!empty($meta['protocols'])): ?>
                        <a href="#protocols" class="mh-btn mh-btn-secondary" style="justify-content: center;">📋 <?php echo count($meta['protocols']); ?> Protocol(s)</a>
                    <?php endif; ?>
                </div>
            </div>
            
            <!-- RRIDs -->
            <?php if (!empty($meta['rrids'])): ?>
            <div class="mh-sidebar-widget">
                <h3>🏷️ RRIDs</h3>
                <?php mh_display_rrids($meta['rrids']); ?>
            </div>
            <?php endif; ?>
            
            <!-- RORs -->
            <?php if (!empty($meta['rors'])): ?>
            <div class="mh-sidebar-widget">
                <h3>🏛️ RORs</h3>
                <?php mh_display_rors($meta['rors']); ?>
            </div>
            <?php endif; ?>
            
            <!-- Microscopes -->
            <?php 
            if (taxonomy_exists('mh_microscope')) {
                $microscopes = get_the_terms(get_the_ID(), 'mh_microscope');
                if ($microscopes && !is_wp_error($microscopes)): 
            ?>
            <div class="mh-sidebar-widget">
                <h3>🔬 Microscopes</h3>
                <div class="mh-tags">
                    <?php foreach ($microscopes as $term): 
                        $link = get_term_link($term);
                        if (!is_wp_error($link)):
                    ?>
                        <a href="<?php echo esc_url($link); ?>" class="mh-tag mh-tag-microscope"><?php echo esc_html($term->name); ?></a>
                    <?php endif; endforeach; ?>
                </div>
            </div>
            <?php endif;
            } ?>
            
            <!-- Software -->
            <?php 
            if (taxonomy_exists('mh_software')) {
                $software = get_the_terms(get_the_ID(), 'mh_software');
                if ($software && !is_wp_error($software)): 
            ?>
            <div class="mh-sidebar-widget">
                <h3>💻 Software</h3>
                <div class="mh-tags">
                    <?php foreach ($software as $term): 
                        $link = get_term_link($term);
                        if (!is_wp_error($link)):
                    ?>
                        <a href="<?php echo esc_url($link); ?>" class="mh-tag mh-tag-software"><?php echo esc_html($term->name); ?></a>
                    <?php endif; endforeach; ?>
                </div>
            </div>
            <?php endif;
            } ?>
            
            <!-- Organisms -->
            <?php 
            if (taxonomy_exists('mh_organism')) {
                $organisms = get_the_terms(get_the_ID(), 'mh_organism');
                if ($organisms && !is_wp_error($organisms)): 
            ?>
            <div class="mh-sidebar-widget">
                <h3>🧬 Organisms</h3>
                <div class="mh-tags">
                    <?php foreach ($organisms as $term): 
                        $link = get_term_link($term);
                        if (!is_wp_error($link)):
                    ?>
                        <a href="<?php echo esc_url($link); ?>" class="mh-tag mh-tag-organism"><?php echo esc_html($term->name); ?></a>
                    <?php endif; endforeach; ?>
                </div>
            </div>
            <?php endif;
            } ?>
            
            <!-- Fluorophores (from meta) -->
            <?php 
            $fluorophores = json_decode(get_post_meta(get_the_ID(), '_mh_fluorophores', true), true) ?: array();
            if (!empty($fluorophores)): 
            ?>
            <div class="mh-sidebar-widget">
                <h3>🔬 Fluorophores</h3>
                <div class="mh-tags">
                    <?php foreach ($fluorophores as $fluor): ?>
                        <span class="mh-tag mh-tag-fluorophore"><?php echo esc_html($fluor); ?></span>
                    <?php endforeach; ?>
                </div>
            </div>
            <?php endif; ?>
            
            <!-- Cell Lines (from meta) -->
            <?php 
            $cell_lines = json_decode(get_post_meta(get_the_ID(), '_mh_cell_lines', true), true) ?: array();
            if (!empty($cell_lines)): 
            ?>
            <div class="mh-sidebar-widget">
                <h3>🧫 Cell Lines</h3>
                <div class="mh-tags">
                    <?php foreach ($cell_lines as $cell): ?>
                        <span class="mh-tag mh-tag-cell_line"><?php echo esc_html($cell); ?></span>
                    <?php endforeach; ?>
                </div>
            </div>
            <?php endif; ?>
            
            <!-- Sample Preparation (from meta) -->
            <?php 
            $sample_prep = json_decode(get_post_meta(get_the_ID(), '_mh_sample_preparation', true), true) ?: array();
            if (empty($sample_prep)) {
                $sample_prep = json_decode(get_post_meta(get_the_ID(), '_mh_sample_prep', true), true) ?: array();
            }
            if (!empty($sample_prep)): 
            ?>
            <div class="mh-sidebar-widget">
                <h3>🧪 Sample Preparation</h3>
                <div class="mh-tags">
                    <?php foreach ($sample_prep as $prep): ?>
                        <span class="mh-tag mh-tag-sample_prep"><?php echo esc_html($prep); ?></span>
                    <?php endforeach; ?>
                </div>
            </div>
            <?php endif; ?>
            
            <!-- Microscope Brands (from meta) -->
            <?php 
            $brands = json_decode(get_post_meta(get_the_ID(), '_mh_microscope_brands', true), true) ?: array();
            if (!empty($brands)): 
            ?>
            <div class="mh-sidebar-widget">
                <h3>🏭 Equipment Brands</h3>
                <div class="mh-tags">
                    <?php foreach ($brands as $brand): ?>
                        <span class="mh-tag mh-tag-microscope_brand"><?php echo esc_html($brand); ?></span>
                    <?php endforeach; ?>
                </div>
            </div>
            <?php endif; ?>
            
            <!-- Related Papers -->
            <?php
            $related_terms = array();
            $taxonomies = array('mh_technique', 'mh_microscope', 'mh_organism');
            foreach ($taxonomies as $tax) {
                if (!taxonomy_exists($tax)) continue;
                $terms = get_the_terms(get_the_ID(), $tax);
                if ($terms && !is_wp_error($terms)) {
                    foreach ($terms as $term) {
                        $related_terms[] = $term->term_id;
                    }
                }
            }
            
            if (!empty($related_terms) && mh_plugin_active()):
                $related = new WP_Query(array(
                    'post_type' => 'mh_paper',
                    'posts_per_page' => 5,
                    'post__not_in' => array(get_the_ID()),
                    'tax_query' => array(
                        'relation' => 'OR',
                        array('taxonomy' => 'mh_technique', 'terms' => $related_terms),
                        array('taxonomy' => 'mh_microscope', 'terms' => $related_terms),
                        array('taxonomy' => 'mh_organism', 'terms' => $related_terms)
                    )
                ));
                
                if ($related->have_posts()):
            ?>
            <div class="mh-sidebar-widget">
                <h3>📚 Related Papers</h3>
                <ul style="display: flex; flex-direction: column; gap: 12px;">
                    <?php while ($related->have_posts()): $related->the_post(); ?>
                    <li>
                        <a href="<?php the_permalink(); ?>" style="color: var(--text-light); font-size: 0.9rem; display: block;">
                            <?php the_title(); ?>
                        </a>
                    </li>
                    <?php endwhile; wp_reset_postdata(); ?>
                </ul>
            </div>
            <?php 
                endif;
            endif; 
            ?>
        </aside>
    </div>
</div>

<!-- GitHub Tools Styles (for enriched per-paper tools from scraper v5.1+) -->
<style>
.mh-github-tools-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
}
.mh-github-tool-card {
    display: block;
    padding: 16px;
    background: var(--bg-card, #21262d);
    border: 1px solid var(--border, #30363d);
    border-left: 4px solid var(--border, #30363d);
    border-radius: 8px;
    color: var(--text, #e6edf3);
    text-decoration: none;
    transition: all 0.2s;
}
.mh-github-tool-card:hover {
    background: var(--bg-hover, #30363d);
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
.mh-ght-name {
    font-size: 1rem;
    color: var(--primary, #58a6ff);
    word-break: break-word;
}
.mh-ght-health {
    font-size: 0.68rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    padding: 3px 10px;
    border-radius: 12px;
    white-space: nowrap;
    flex-shrink: 0;
}
.mh-ght-health.active { background: rgba(63, 185, 80, 0.15); color: #3fb950; }
.mh-ght-health.moderate { background: rgba(210, 153, 34, 0.15); color: #d29922; }
.mh-ght-health.low { background: rgba(248, 81, 73, 0.15); color: #f85149; }
.mh-ght-health.archived { background: rgba(110, 118, 129, 0.15); color: #6e7681; }

.mh-ght-desc {
    font-size: 0.85rem;
    color: var(--text-muted, #8b949e);
    margin: 0 0 8px;
    line-height: 1.4;
}
.mh-ght-metrics {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    font-size: 0.8rem;
    color: var(--text-muted, #8b949e);
    margin-bottom: 8px;
}
.mh-ght-rel {
    font-weight: 600;
    padding: 1px 8px;
    border-radius: 8px;
    font-size: 0.72rem;
}
.mh-ght-rel.introduces { background: rgba(163, 113, 247, 0.15); color: #a371f7; }
.mh-ght-rel.uses { background: rgba(88, 166, 255, 0.1); color: #58a6ff; }
.mh-ght-rel.extends { background: rgba(35, 134, 54, 0.15); color: #3fb950; }
.mh-ght-rel.benchmarks { background: rgba(210, 153, 34, 0.1); color: #d29922; }

.mh-ght-topics {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
}
.mh-ght-topic {
    font-size: 0.7rem;
    background: rgba(88, 166, 255, 0.08);
    color: var(--primary, #58a6ff);
    padding: 1px 8px;
    border-radius: 10px;
    border: 1px solid rgba(88, 166, 255, 0.2);
}
</style>

<?php get_footer(); ?>
