<?php
/**
 * Theme Header
 */
$urls = mh_get_page_urls();
?>
<!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
    <meta charset="<?php bloginfo('charset'); ?>">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <?php wp_head(); ?>
</head>
<body <?php body_class('mh-wrapper'); ?>>
<?php wp_body_open(); ?>

<nav class="mh-nav">
    <div class="mh-container mh-nav-inner">
        <a href="<?php echo esc_url(home_url('/')); ?>" class="mh-logo">
            🔬 MicroHub
        </a>
        
        <button class="mh-nav-toggle" aria-label="Toggle menu">☰</button>
        
        <div class="mh-nav-menu">
            <a href="<?php echo esc_url($urls['protocols']); ?>">Protocols</a>
            <a href="<?php echo esc_url(home_url('/github-tools/')); ?>">GitHub Tools</a>
            <a href="<?php echo esc_url($urls['discussions']); ?>">Discussions</a>
            <a href="<?php echo esc_url($urls['about']); ?>">About</a>
            <a href="<?php echo esc_url($urls['contact']); ?>">Contact</a>
        </div>
    </div>
</nav>

<main class="mh-main">
