<?php
/**
 * Default Index Template
 */
get_header();
?>

<div class="mh-container">
    <?php if (have_posts()): ?>
        <div class="mh-grid mh-grid-2">
            <?php while (have_posts()): the_post(); ?>
            <article class="mh-card">
                <h2 class="mh-card-title">
                    <a href="<?php the_permalink(); ?>"><?php the_title(); ?></a>
                </h2>
                <div class="mh-card-meta">
                    <span><?php echo get_the_date(); ?></span>
                </div>
                <div class="mh-card-excerpt">
                    <?php the_excerpt(); ?>
                </div>
            </article>
            <?php endwhile; ?>
        </div>
        
        <nav class="mh-pagination">
            <?php echo paginate_links(array('type' => 'list')); ?>
        </nav>
    <?php else: ?>
        <p style="text-align: center; color: var(--text-muted); padding: 48px 0;">No content found.</p>
    <?php endif; ?>
</div>

<?php get_footer(); ?>
