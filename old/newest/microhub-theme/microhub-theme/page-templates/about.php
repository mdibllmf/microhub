<?php
/**
 * Template Name: About Page
 * 
 * This template displays the page content from WordPress editor
 * with optional stats and techniques sections.
 * 
 * Edit the page content in WordPress: Pages → About → Edit
 */
get_header();

$stats = mh_get_stats();

// Get techniques for display
$techniques = array();
if (taxonomy_exists('mh_technique')) {
    $techniques = get_terms(array(
        'taxonomy' => 'mh_technique',
        'number' => 20,
        'orderby' => 'count',
        'order' => 'DESC',
        'hide_empty' => true
    ));
    if (is_wp_error($techniques)) {
        $techniques = array();
    }
}
?>

<div class="mh-page-header">
    <h1><?php the_title(); ?></h1>
    <?php if (has_excerpt()): ?>
        <p class="mh-page-subtitle"><?php echo get_the_excerpt(); ?></p>
    <?php else: ?>
        <p class="mh-page-subtitle">The open platform for microscopy research</p>
    <?php endif; ?>
</div>

<div class="mh-container">
    <!-- Page Content from WordPress Editor -->
    <?php if (have_posts()): while (have_posts()): the_post(); ?>
        <?php if (get_the_content()): ?>
        <section class="mh-about-section mh-page-content">
            <?php the_content(); ?>
        </section>
        <?php endif; ?>
    <?php endwhile; endif; ?>
    
    <!-- Stats Section (Auto-generated) -->
    <?php if ($stats['papers'] > 0): ?>
    <section class="mh-about-section">
        <h2>📊 Database Statistics</h2>
        <div class="mh-stats-grid" style="margin-top: 24px;">
            <div class="mh-stat-card">
                <span class="number"><?php echo mh_format_number($stats['papers']); ?></span>
                <span class="label">Papers</span>
            </div>
            <div class="mh-stat-card">
                <span class="number"><?php echo mh_format_number($stats['with_protocols']); ?></span>
                <span class="label">With Protocols</span>
            </div>
            <div class="mh-stat-card">
                <span class="number"><?php echo mh_format_number($stats['techniques']); ?></span>
                <span class="label">Techniques</span>
            </div>
            <div class="mh-stat-card">
                <span class="number"><?php echo mh_format_number($stats['with_github']); ?></span>
                <span class="label">With Code</span>
            </div>
            <div class="mh-stat-card">
                <span class="number"><?php echo mh_format_number($stats['microscopes']); ?></span>
                <span class="label">Microscopes</span>
            </div>
            <div class="mh-stat-card">
                <span class="number"><?php echo mh_format_number($stats['organisms']); ?></span>
                <span class="label">Organisms</span>
            </div>
        </div>
    </section>
    <?php endif; ?>
    
    <!-- Techniques Section (Auto-generated) -->
    <?php if (!empty($techniques)): ?>
    <section class="mh-about-section">
        <h2>🔬 Techniques Covered</h2>
        <div class="mh-tag-cloud" style="margin-top: 16px;">
            <?php foreach ($techniques as $term): 
                $link = get_term_link($term);
                if (!is_wp_error($link)):
            ?>
                <a href="<?php echo esc_url($link); ?>" class="mh-tag mh-tag-technique mh-tag-lg">
                    <?php echo esc_html($term->name); ?>
                    <small><?php echo $term->count; ?></small>
                </a>
            <?php endif; endforeach; ?>
        </div>
    </section>
    <?php endif; ?>
    
    <!-- Contact CTA -->
    <section class="mh-about-section" style="text-align: center;">
        <h2>📬 Get in Touch</h2>
        <p>Have questions, suggestions, or want to contribute?</p>
        <a href="<?php echo esc_url(mh_get_page_urls()['contact']); ?>" class="mh-btn mh-btn-primary" style="margin-top: 16px;">Contact Us</a>
    </section>
</div>

<style>
/* Allow WordPress editor content to style properly */
.mh-page-content h2 { font-size: 1.25rem; margin-top: 24px; margin-bottom: 16px; }
.mh-page-content h3 { font-size: 1.1rem; margin-top: 20px; margin-bottom: 12px; }
.mh-page-content p { color: var(--text-light); line-height: 1.7; }
.mh-page-content ul, .mh-page-content ol { margin: 16px 0; padding-left: 24px; }
.mh-page-content li { color: var(--text-light); margin-bottom: 8px; }
.mh-page-content a { color: var(--primary); }
.mh-page-content a:hover { color: var(--accent); }
.mh-page-content img { max-width: 100%; height: auto; border-radius: 8px; margin: 16px 0; }
.mh-page-content blockquote { border-left: 4px solid var(--primary); padding-left: 16px; margin: 16px 0; color: var(--text-muted); font-style: italic; }

/* WordPress blocks support */
.mh-page-content .wp-block-columns { display: flex; gap: 24px; flex-wrap: wrap; }
.mh-page-content .wp-block-column { flex: 1; min-width: 250px; }
.mh-page-content .wp-block-button__link { display: inline-block; padding: 10px 20px; background: var(--primary); color: white; border-radius: 8px; text-decoration: none; }
.mh-page-content .wp-block-button__link:hover { background: var(--accent); color: white; }
</style>

<?php get_footer(); ?>
