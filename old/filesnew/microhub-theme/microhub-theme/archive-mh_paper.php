<?php
/**
 * Paper Archive Template
 */
get_header();

// Check if plugin is active
if (!function_exists('mh_plugin_active') || !mh_plugin_active()) {
    ?>
    <div class="mh-container" style="padding: 80px 20px; text-align: center;">
        <h1>Papers</h1>
        <p style="color: var(--text-muted); margin: 20px 0;">The MicroHub plugin is required to view papers.</p>
    </div>
    <?php
    get_footer();
    return;
}

$paged = get_query_var('paged') ? get_query_var('paged') : 1;
$orderby = isset($_GET['orderby']) ? sanitize_text_field($_GET['orderby']) : 'citations';

// Build query args
$args = array(
    'post_type' => 'mh_paper',
    'posts_per_page' => 12,
    'paged' => $paged
);

switch ($orderby) {
    case 'date':
        $args['orderby'] = 'date';
        $args['order'] = 'DESC';
        break;
    case 'title':
        $args['orderby'] = 'title';
        $args['order'] = 'ASC';
        break;
    case 'year':
        $args['meta_key'] = '_mh_publication_year';
        $args['orderby'] = 'meta_value_num';
        $args['order'] = 'DESC';
        break;
    default: // citations
        $args['meta_key'] = '_mh_citation_count';
        $args['orderby'] = 'meta_value_num';
        $args['order'] = 'DESC';
        break;
}

$papers = new WP_Query($args);
?>

<div class="mh-page-header">
    <h1>Papers</h1>
    <p class="mh-page-subtitle">Browse our collection of microscopy research</p>
</div>

<div class="mh-container">
    <!-- Filters -->
    <div class="mh-archive-header">
        <span class="mh-results-count">
            <?php echo number_format($papers->found_posts); ?> papers found
        </span>
        
        <div class="mh-archive-filters">
            <form method="get">
                <select name="orderby" onchange="this.form.submit()">
                    <option value="citations" <?php selected($orderby, 'citations'); ?>>Most Cited</option>
                    <option value="date" <?php selected($orderby, 'date'); ?>>Newest</option>
                    <option value="year" <?php selected($orderby, 'year'); ?>>Publication Year</option>
                    <option value="title" <?php selected($orderby, 'title'); ?>>Title A-Z</option>
                </select>
            </form>
        </div>
    </div>
    
    <!-- Papers Grid -->
    <?php if ($papers->have_posts()): ?>
    <div class="mh-grid mh-grid-3">
        <?php while ($papers->have_posts()): $papers->the_post(); 
            $meta = mh_get_paper_meta();
        ?>
        <article class="mh-card">
            <?php mh_paper_badge($meta['citations']); ?>
            
            <h3 class="mh-card-title">
                <a href="<?php the_permalink(); ?>"><?php the_title(); ?></a>
            </h3>
            
            <div class="mh-card-meta">
                <?php if ($meta['journal']): ?>
                    <span><?php echo esc_html($meta['journal']); ?></span>
                <?php endif; ?>
                <?php if ($meta['year']): ?>
                    <span><?php echo esc_html($meta['year']); ?></span>
                <?php endif; ?>
                <?php if ($meta['citations']): ?>
                    <span>📊 <?php echo number_format($meta['citations']); ?></span>
                <?php endif; ?>
            </div>
            
            <?php if ($meta['abstract']): ?>
                <p class="mh-card-excerpt"><?php echo mh_truncate_text($meta['abstract'], 25); ?></p>
            <?php endif; ?>
            
            <?php mh_display_paper_tags(); ?>
            
            <!-- Quick indicators -->
            <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px;">
                <?php if (!empty($meta['protocols'])): ?>
                    <span style="font-size: 0.8rem; color: var(--secondary);">📋 <?php echo count($meta['protocols']); ?></span>
                <?php endif; ?>
                <?php if ($meta['github_url']): ?>
                    <span style="font-size: 0.8rem; color: var(--text-muted);">💻 Code</span>
                <?php endif; ?>
                <?php if (!empty($meta['repositories'])): ?>
                    <span style="font-size: 0.8rem; color: var(--text-muted);">💾 Data</span>
                <?php endif; ?>
                <?php if (!empty($meta['rrids'])): ?>
                    <span style="font-size: 0.8rem; color: #a371f7;">🏷️ <?php echo count($meta['rrids']); ?> RRID<?php echo count($meta['rrids']) > 1 ? 's' : ''; ?></span>
                <?php endif; ?>
                <?php if ($meta['pdf_url']): ?>
                    <span style="font-size: 0.8rem; color: var(--danger);">📄 PDF</span>
                <?php endif; ?>
            </div>
        </article>
        <?php endwhile; ?>
    </div>
    
    <!-- Pagination -->
    <nav class="mh-pagination">
        <?php
        $big = 999999999;
        echo paginate_links(array(
            'base' => str_replace($big, '%#%', esc_url(get_pagenum_link($big))),
            'format' => '?paged=%#%',
            'current' => max(1, $paged),
            'total' => $papers->max_num_pages,
            'prev_text' => '← Previous',
            'next_text' => 'Next →',
            'type' => 'list'
        ));
        ?>
    </nav>
    
    <?php else: ?>
    <p style="text-align: center; color: var(--text-muted); padding: 48px 0;">No papers found.</p>
    <?php endif; wp_reset_postdata(); ?>
</div>

<?php get_footer(); ?>
