<?php
/**
 * Search Results Template
 */
get_header();

global $wp_query;

$is_author_search = isset($_GET['search_field']) && $_GET['search_field'] === 'author';
$search_query = get_search_query();
?>

<div class="mh-page-header">
    <?php if ($is_author_search): ?>
        <h1>Papers by Author</h1>
        <p class="mh-page-subtitle">
            <?php echo $wp_query->found_posts; ?> papers by "<?php echo esc_html($search_query); ?>"
        </p>
    <?php else: ?>
        <h1>Search Results</h1>
        <p class="mh-page-subtitle">
            <?php echo $wp_query->found_posts; ?> results for "<?php echo esc_html($search_query); ?>"
        </p>
    <?php endif; ?>
</div>

<div class="mh-container">
    <?php if ($is_author_search && $wp_query->found_posts > 0): ?>
    <!-- Author Summary Card -->
    <div class="mh-author-header">
        <h2>👤 <?php echo esc_html($search_query); ?></h2>
        <div class="mh-author-stats">
            <span>📚 <?php echo $wp_query->found_posts; ?> paper<?php echo $wp_query->found_posts !== 1 ? 's' : ''; ?></span>
            <?php
            // Calculate total citations for this author
            $total_citations = 0;
            $temp_query = new WP_Query(array(
                'post_type' => 'mh_paper',
                'posts_per_page' => -1,
                'fields' => 'ids',
                'meta_query' => array(
                    array(
                        'key' => '_mh_authors',
                        'value' => $search_query,
                        'compare' => 'LIKE'
                    )
                )
            ));
            if ($temp_query->have_posts()) {
                foreach ($temp_query->posts as $post_id) {
                    $total_citations += intval(get_post_meta($post_id, '_mh_citation_count', true));
                }
            }
            wp_reset_postdata();
            ?>
            <span>📊 <?php echo number_format($total_citations); ?> total citations</span>
        </div>
    </div>
    <?php endif; ?>

    <!-- Search Form -->
    <div class="mh-search-box" style="margin-bottom: 32px;">
        <form class="mh-search-form" action="<?php echo esc_url(home_url('/')); ?>" method="get">
            <input type="search" name="s" value="<?php echo esc_attr($search_query); ?>" placeholder="Search papers, authors, techniques...">
            <input type="hidden" name="post_type" value="mh_paper">
            <?php if ($is_author_search): ?>
            <input type="hidden" name="search_field" value="author">
            <?php endif; ?>
            <button type="submit">Search</button>
        </form>
        <?php if ($is_author_search): ?>
        <p style="margin-top: 8px; font-size: 0.85rem; color: var(--text-muted);">
            Showing papers where "<?php echo esc_html($search_query); ?>" is an author. 
            <a href="<?php echo esc_url(add_query_arg(array('s' => $search_query, 'post_type' => 'mh_paper'), home_url('/'))); ?>">Search all fields instead</a>
        </p>
        <?php endif; ?>
    </div>
    
    <?php if (have_posts()): ?>
    <div class="mh-grid mh-grid-3">
        <?php while (have_posts()): the_post(); 
            $meta = array();
            if (get_post_type() === 'mh_paper') {
                $meta = mh_get_paper_meta();
            }
        ?>
        <article class="mh-card">
            <?php if (get_post_type() === 'mh_paper'): ?>
                <?php mh_paper_badge($meta['citations'] ?? 0); ?>
            <?php endif; ?>
            
            <h3 class="mh-card-title">
                <a href="<?php the_permalink(); ?>"><?php the_title(); ?></a>
            </h3>
            
            <?php if (get_post_type() === 'mh_paper' && !empty($meta)): ?>
                <?php if (!empty($meta['authors'])): ?>
                <div class="mh-card-authors-small">
                    <?php 
                    $last_author = mh_get_last_author($meta['authors']);
                    $first_author = mh_get_first_author($meta['authors']);
                    if ($first_author): 
                    ?>
                        <a href="<?php echo esc_url(mh_author_search_url($first_author)); ?>" class="mh-author-link"><?php echo esc_html($first_author); ?></a>
                        <?php if ($last_author && $last_author !== $first_author): ?>
                            <span class="mh-author-sep">... </span>
                            <a href="<?php echo esc_url(mh_author_search_url($last_author)); ?>" class="mh-author-link mh-last-author"><?php echo esc_html($last_author); ?></a>
                        <?php endif; ?>
                    <?php endif; ?>
                </div>
                <?php endif; ?>
                
                <div class="mh-card-meta">
                    <?php if (!empty($meta['journal'])): ?>
                        <span><?php echo esc_html($meta['journal']); ?></span>
                    <?php endif; ?>
                    <?php if (!empty($meta['year'])): ?>
                        <span><?php echo esc_html($meta['year']); ?></span>
                    <?php endif; ?>
                    <?php if (!empty($meta['citations'])): ?>
                        <span>📊 <?php echo number_format($meta['citations']); ?></span>
                    <?php endif; ?>
                </div>
                
                <?php if (!empty($meta['abstract'])): ?>
                    <p class="mh-card-excerpt"><?php echo mh_truncate_text($meta['abstract'], 20); ?></p>
                <?php endif; ?>
                
                <?php mh_display_paper_tags(); ?>
                
                <!-- Quick indicators -->
                <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px;">
                    <?php if (!empty($meta['protocols'])): ?>
                        <span style="font-size: 0.8rem; color: var(--secondary);">📋 <?php echo count($meta['protocols']); ?></span>
                    <?php endif; ?>
                    <?php if (!empty($meta['github_url'])): ?>
                        <span style="font-size: 0.8rem; color: var(--text-muted);">💻 Code</span>
                    <?php endif; ?>
                    <?php if (!empty($meta['rrids'])): ?>
                        <span style="font-size: 0.8rem; color: #a371f7;">🏷️ <?php echo count($meta['rrids']); ?></span>
                    <?php endif; ?>
                </div>
            <?php else: ?>
                <div class="mh-card-meta">
                    <span><?php echo get_post_type_object(get_post_type())->labels->singular_name; ?></span>
                    <span><?php echo get_the_date(); ?></span>
                </div>
                <div class="mh-card-excerpt">
                    <?php the_excerpt(); ?>
                </div>
            <?php endif; ?>
        </article>
        <?php endwhile; ?>
    </div>
    
    <nav class="mh-pagination">
        <?php echo paginate_links(array('type' => 'list')); ?>
    </nav>
    
    <?php else: ?>
    <div style="text-align: center; padding: 48px 0;">
        <p style="color: var(--text-muted); margin-bottom: 24px;">No results found for your search.</p>
        <p style="color: var(--text-muted);">Try different keywords or browse by:</p>
        <div style="display: flex; justify-content: center; gap: 12px; margin-top: 16px;">
            <a href="<?php echo get_post_type_archive_link('mh_paper'); ?>" class="mh-btn mh-btn-outline">All Papers</a>
            <a href="<?php echo home_url('/'); ?>" class="mh-btn mh-btn-outline">Search Papers</a>
        </div>
    </div>
    <?php endif; ?>
</div>

<style>
.mh-card-authors-small {
    font-size: 0.85rem;
    margin-bottom: 8px;
    color: var(--text-muted);
}
.mh-card-authors-small .mh-author-link {
    color: var(--text-muted);
}
.mh-card-authors-small .mh-author-link:hover {
    color: var(--primary);
}
.mh-card-authors-small .mh-last-author {
    color: var(--primary);
    font-weight: 500;
}
</style>

<?php get_footer(); ?>
