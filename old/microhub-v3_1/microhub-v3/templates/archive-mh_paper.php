<?php
/**
 * Archive Papers Template
 */

if (!defined('ABSPATH')) {
    exit;
}

get_header();
?>

<div class="microhub-wrapper">
    <?php if (function_exists('mh_render_nav')) echo mh_render_nav(); ?>
    
    <div class="mh-archive">
        <h1>Microscopy Papers</h1>
        
        <div class="mh-papers-grid">
            <?php if (have_posts()) : ?>
                <?php while (have_posts()) : the_post(); ?>
                    <?php
                    $post_id = get_the_ID();
                    $doi = get_post_meta($post_id, '_mh_doi', true);
                    $journal = get_post_meta($post_id, '_mh_journal', true);
                    $year = get_post_meta($post_id, '_mh_publication_year', true);
                    $citations = get_post_meta($post_id, '_mh_citation_count', true);
                    $has_full_text = get_post_meta($post_id, '_mh_has_full_text', true);
                    ?>
                    <article class="mh-paper-card">
                        <div class="mh-card-badges">
                            <?php if ($has_full_text) : ?>
                                <span class="mh-badge">📄</span>
                            <?php endif; ?>
                            <?php if ($citations >= 50) : ?>
                                <span class="mh-badge">⭐</span>
                            <?php endif; ?>
                        </div>
                        
                        <h2><a href="<?php the_permalink(); ?>"><?php the_title(); ?></a></h2>
                        
                        <div class="mh-card-meta">
                            <?php if ($journal) : ?>
                                <span><?php echo esc_html($journal); ?></span>
                            <?php endif; ?>
                            <?php if ($year) : ?>
                                <span><?php echo esc_html($year); ?></span>
                            <?php endif; ?>
                            <?php if ($citations) : ?>
                                <span><?php echo number_format($citations); ?> citations</span>
                            <?php endif; ?>
                        </div>
                    </article>
                <?php endwhile; ?>
            <?php else : ?>
                <p>No papers found.</p>
            <?php endif; ?>
        </div>
        
        <div class="mh-pagination">
            <?php the_posts_pagination(); ?>
        </div>
    </div>
</div>

<style>
.microhub-wrapper { max-width: 1200px; margin: 0 auto; padding: 20px; }
.mh-archive h1 { color: #e6edf3; margin-bottom: 30px; }
.mh-papers-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 20px; }
.mh-paper-card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 20px; position: relative; }
.mh-card-badges { position: absolute; top: 15px; right: 15px; display: flex; gap: 5px; }
.mh-badge { font-size: 0.9rem; }
.mh-paper-card h2 { font-size: 1rem; margin: 0 0 10px 0; line-height: 1.4; }
.mh-paper-card h2 a { color: #58a6ff; text-decoration: none; }
.mh-paper-card h2 a:hover { text-decoration: underline; }
.mh-card-meta { display: flex; gap: 15px; flex-wrap: wrap; color: #8b949e; font-size: 0.85rem; }
.mh-pagination { margin-top: 30px; text-align: center; }
.mh-pagination a, .mh-pagination span { display: inline-block; padding: 8px 12px; margin: 0 3px; background: #21262d; border-radius: 4px; color: #e6edf3; text-decoration: none; }
.mh-pagination a:hover { background: #30363d; }
.mh-pagination .current { background: #58a6ff; }
</style>

<?php get_footer(); ?>
