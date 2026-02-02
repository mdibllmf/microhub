<?php
/**
 * Taxonomy Archive Template
 */
get_header();

$term = get_queried_object();

// Safety check
if (!$term || !isset($term->taxonomy)) {
    echo '<div class="mh-container" style="padding: 48px 0; text-align: center;"><p>Taxonomy not found.</p></div>';
    get_footer();
    return;
}

$taxonomy = get_taxonomy($term->taxonomy);

// Determine tag class based on taxonomy
$tag_classes = array(
    'mh_technique' => 'technique',
    'mh_microscope' => 'microscope',
    'mh_organism' => 'organism',
    'mh_software' => 'software',
    'mh_facility' => 'facility',
);
$tag_class = isset($tag_classes[$term->taxonomy]) ? $tag_classes[$term->taxonomy] : 'technique';

// Special icon for facilities
$taxonomy_icon = '';
if ($term->taxonomy === 'mh_facility') {
    $taxonomy_icon = '🏛️ ';
}

$paged = get_query_var('paged') ? get_query_var('paged') : 1;
?>

<div class="mh-page-header">
    <span class="mh-tag mh-tag-<?php echo $tag_class; ?>" style="font-size: 1rem; padding: 8px 20px; margin-bottom: 16px;">
        <?php echo $taxonomy_icon . esc_html($term->name); ?>
    </span>
    <h1><?php echo $taxonomy_icon . esc_html($term->name); ?></h1>
    <p class="mh-page-subtitle"><?php echo esc_html($taxonomy->labels->singular_name); ?> • <?php echo $term->count; ?> papers</p>
    <?php 
    // Show facility website link if available
    if ($term->taxonomy === 'mh_facility') {
        $website = get_term_meta($term->term_id, 'facility_website', true);
        $location = get_term_meta($term->term_id, 'facility_location', true);
        if ($location || $website) {
            echo '<div style="margin-top: 12px; display: flex; gap: 16px; justify-content: center; flex-wrap: wrap;">';
            if ($location) {
                echo '<span style="color: var(--text-muted);">📍 ' . esc_html($location) . '</span>';
            }
            if ($website) {
                echo '<a href="' . esc_url($website) . '" target="_blank" rel="noopener" style="color: var(--primary);">🔗 Visit Website</a>';
            }
            echo '</div>';
        }
    }
    ?>
</div>

<div class="mh-container">
    <?php if ($term->description): ?>
    <div class="mh-about-section" style="margin-bottom: 32px;">
        <p><?php echo esc_html($term->description); ?></p>
    </div>
    <?php endif; ?>
    
    <?php if (have_posts()): ?>
    <div class="mh-grid mh-grid-3">
        <?php while (have_posts()): the_post(); 
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
            </div>
        </article>
        <?php endwhile; ?>
    </div>
    
    <!-- Pagination -->
    <nav class="mh-pagination">
        <?php
        echo paginate_links(array(
            'prev_text' => '← Previous',
            'next_text' => 'Next →',
            'type' => 'list'
        ));
        ?>
    </nav>
    
    <?php else: ?>
    <p style="text-align: center; color: var(--text-muted); padding: 48px 0;">No papers found for this <?php echo esc_html(strtolower($taxonomy->labels->singular_name)); ?>.</p>
    <?php endif; ?>
</div>

<?php get_footer(); ?>
