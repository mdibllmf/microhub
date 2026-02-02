<?php
/**
 * MicroHub Post Types
 */

if (!defined('ABSPATH')) {
    exit;
}

class MicroHub_Post_Types {

    public function register_post_types() {
        // Papers
        register_post_type('mh_paper', array(
            'labels' => array(
                'name' => __('Papers', 'microhub'),
                'singular_name' => __('Paper', 'microhub'),
                'add_new' => __('Add New Paper', 'microhub'),
                'add_new_item' => __('Add New Paper', 'microhub'),
                'edit_item' => __('Edit Paper', 'microhub'),
                'new_item' => __('New Paper', 'microhub'),
                'view_item' => __('View Paper', 'microhub'),
                'search_items' => __('Search Papers', 'microhub'),
                'not_found' => __('No papers found', 'microhub'),
                'not_found_in_trash' => __('No papers found in trash', 'microhub'),
                'menu_name' => __('MicroHub Papers', 'microhub'),
            ),
            'public' => true,
            'has_archive' => true,
            'rewrite' => array('slug' => 'papers'),
            'supports' => array('title', 'editor', 'thumbnail', 'comments', 'custom-fields'),
            'menu_icon' => 'dashicons-media-document',
            'show_in_rest' => true,
        ));

        // Protocols
        register_post_type('mh_protocol', array(
            'labels' => array(
                'name' => __('Protocols', 'microhub'),
                'singular_name' => __('Protocol', 'microhub'),
                'add_new' => __('Add New Protocol', 'microhub'),
                'add_new_item' => __('Add New Protocol', 'microhub'),
                'edit_item' => __('Edit Protocol', 'microhub'),
                'new_item' => __('New Protocol', 'microhub'),
                'view_item' => __('View Protocol', 'microhub'),
                'search_items' => __('Search Protocols', 'microhub'),
                'not_found' => __('No protocols found', 'microhub'),
                'menu_name' => __('Protocols', 'microhub'),
            ),
            'public' => true,
            'has_archive' => true,
            'rewrite' => array('slug' => 'protocols'),
            'supports' => array('title', 'editor', 'thumbnail', 'comments', 'author'),
            'menu_icon' => 'dashicons-clipboard',
            'show_in_rest' => true,
        ));
    }
}
