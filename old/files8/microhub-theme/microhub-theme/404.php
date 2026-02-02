<?php
/**
 * 404 Error Template
 */
get_header();
?>

<div class="mh-container" style="text-align: center; padding: 80px 0;">
    <h1 style="font-size: 4rem; margin-bottom: 16px;">404</h1>
    <p style="font-size: 1.25rem; color: var(--text-muted); margin-bottom: 32px;">Page not found</p>
    <p style="color: var(--text-light); margin-bottom: 32px;">The page you're looking for doesn't exist or has been moved.</p>
    
    <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
        <a href="<?php echo esc_url(home_url('/')); ?>" class="mh-btn mh-btn-primary">Go Home</a>
        <a href="<?php echo get_post_type_archive_link('mh_paper'); ?>" class="mh-btn mh-btn-outline">Browse Papers</a>
    </div>
    
    <div class="mh-search-box" style="margin-top: 48px;">
        <form class="mh-search-form" action="<?php echo esc_url(home_url('/')); ?>" method="get">
            <input type="search" name="s" placeholder="Search for papers...">
            <input type="hidden" name="post_type" value="mh_paper">
            <button type="submit">Search</button>
        </form>
    </div>
</div>

<?php get_footer(); ?>
