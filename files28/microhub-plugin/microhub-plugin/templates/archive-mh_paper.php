<?php
/**
 * Archive Template for Papers
 */
get_header();
?>
<div class="microhub-wrapper">
    <section class="mh-archive-header">
        <h1><?php post_type_archive_title(); ?></h1>
        <p>Browse all microscopy research papers</p>
    </section>
    
    <section class="mh-archive-content">
        <?php echo do_shortcode('[microhub_search_page]'); ?>
    </section>
</div>
<?php get_footer(); ?>
