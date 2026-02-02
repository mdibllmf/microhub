<?php
/**
 * Default Page Template
 * 
 * This template is used for pages without a specific template.
 * Content is fully editable via WordPress editor.
 */
get_header();
?>

<div class="mh-page-header">
    <h1><?php the_title(); ?></h1>
    <?php if (has_excerpt()): ?>
        <p class="mh-page-subtitle"><?php echo get_the_excerpt(); ?></p>
    <?php endif; ?>
</div>

<div class="mh-container">
    <?php while (have_posts()): the_post(); ?>
    <article class="mh-page-article">
        <div class="mh-page-content">
            <?php the_content(); ?>
        </div>
        
        <?php
        // Show child pages if any
        $children = get_pages(array('child_of' => get_the_ID(), 'sort_column' => 'menu_order'));
        if ($children):
        ?>
        <div class="mh-child-pages" style="margin-top: 48px;">
            <h2>Related Pages</h2>
            <div class="mh-grid mh-grid-3" style="margin-top: 16px;">
                <?php foreach ($children as $child): ?>
                <a href="<?php echo get_permalink($child); ?>" class="mh-card" style="text-decoration: none;">
                    <h3 class="mh-card-title"><?php echo esc_html($child->post_title); ?></h3>
                    <?php if ($child->post_excerpt): ?>
                    <p class="mh-card-excerpt"><?php echo esc_html($child->post_excerpt); ?></p>
                    <?php endif; ?>
                </a>
                <?php endforeach; ?>
            </div>
        </div>
        <?php endif; ?>
    </article>
    <?php endwhile; ?>
</div>

<style>
.mh-page-article { max-width: 900px; margin: 0 auto; }
.mh-page-content { background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 32px; }
.mh-page-content h2 { font-size: 1.5rem; margin-top: 32px; margin-bottom: 16px; }
.mh-page-content h2:first-child { margin-top: 0; }
.mh-page-content h3 { font-size: 1.25rem; margin-top: 24px; margin-bottom: 12px; }
.mh-page-content h4 { font-size: 1.1rem; margin-top: 20px; margin-bottom: 8px; }
.mh-page-content p { color: var(--text-light); line-height: 1.8; margin-bottom: 16px; }
.mh-page-content ul, .mh-page-content ol { margin: 16px 0; padding-left: 24px; }
.mh-page-content li { color: var(--text-light); margin-bottom: 8px; line-height: 1.7; }
.mh-page-content a { color: var(--primary); }
.mh-page-content a:hover { color: var(--accent); text-decoration: underline; }
.mh-page-content img { max-width: 100%; height: auto; border-radius: 8px; margin: 16px 0; }
.mh-page-content blockquote { border-left: 4px solid var(--primary); padding-left: 16px; margin: 24px 0; color: var(--text-muted); font-style: italic; }
.mh-page-content pre { background: var(--bg-dark); padding: 16px; border-radius: 8px; overflow-x: auto; font-family: 'JetBrains Mono', monospace; font-size: 0.9rem; }
.mh-page-content code { background: var(--bg-dark); padding: 2px 6px; border-radius: 4px; font-family: 'JetBrains Mono', monospace; font-size: 0.9rem; }
.mh-page-content pre code { background: none; padding: 0; }
.mh-page-content table { width: 100%; border-collapse: collapse; margin: 16px 0; }
.mh-page-content th, .mh-page-content td { padding: 12px; border: 1px solid var(--border); text-align: left; }
.mh-page-content th { background: var(--bg-hover); font-weight: 600; }
.mh-page-content hr { border: none; border-top: 1px solid var(--border); margin: 32px 0; }

/* WordPress blocks support */
.mh-page-content .wp-block-columns { display: flex; gap: 24px; flex-wrap: wrap; margin: 24px 0; }
.mh-page-content .wp-block-column { flex: 1; min-width: 250px; }
.mh-page-content .wp-block-button__link { display: inline-block; padding: 12px 24px; background: var(--primary); color: white; border-radius: 8px; text-decoration: none; font-weight: 600; }
.mh-page-content .wp-block-button__link:hover { background: var(--accent); color: white; }
.mh-page-content .wp-block-image { margin: 24px 0; }
.mh-page-content .wp-block-image figcaption { text-align: center; color: var(--text-muted); font-size: 0.9rem; margin-top: 8px; }
</style>

<?php get_footer(); ?>

