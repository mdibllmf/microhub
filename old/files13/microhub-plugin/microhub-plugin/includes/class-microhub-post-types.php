<?php
/**
 * MicroHub Post Types v2.1
 * Papers, Protocols, and Discussions
 */

class MicroHub_Post_Types {

    public function init() {
        add_action('init', array($this, 'register_post_types'));
    }

    public function register_post_types() {
        // Papers
        register_post_type('mh_paper', array(
            'labels' => array(
                'name' => 'Papers',
                'singular_name' => 'Paper',
                'add_new' => 'Add New Paper',
                'add_new_item' => 'Add New Paper',
                'edit_item' => 'Edit Paper',
                'new_item' => 'New Paper',
                'view_item' => 'View Paper',
                'search_items' => 'Search Papers',
                'not_found' => 'No papers found',
                'not_found_in_trash' => 'No papers found in trash',
                'menu_name' => 'MicroHub Papers',
            ),
            'public' => true,
            'has_archive' => true,
            'rewrite' => array('slug' => 'papers'),
            'supports' => array('title', 'editor', 'thumbnail', 'comments', 'custom-fields'),
            'menu_icon' => 'dashicons-media-document',
            'show_in_rest' => true,
            'taxonomies' => array('mh_technique', 'mh_microscope', 'mh_organism'),
        ));

        // Protocols
        register_post_type('mh_protocol', array(
            'labels' => array(
                'name' => 'Protocols',
                'singular_name' => 'Protocol',
                'add_new' => 'Add New Protocol',
                'add_new_item' => 'Add New Protocol',
                'edit_item' => 'Edit Protocol',
                'new_item' => 'New Protocol',
                'view_item' => 'View Protocol',
                'search_items' => 'Search Protocols',
                'not_found' => 'No protocols found',
                'menu_name' => 'Protocols',
            ),
            'public' => true,
            'has_archive' => false, // Disabled - use WordPress page with [microhub_protocols] shortcode
            'rewrite' => array('slug' => 'protocol'), // Singular for individual posts
            'supports' => array('title', 'editor', 'thumbnail', 'comments', 'author'),
            'menu_icon' => 'dashicons-clipboard',
            'show_in_rest' => true,
            'taxonomies' => array('mh_technique', 'mh_microscope', 'mh_organism', 'mh_protocol_type'),
        ));

        // Discussions
        register_post_type('mh_discussion', array(
            'labels' => array(
                'name' => 'Discussions',
                'singular_name' => 'Discussion',
                'add_new' => 'New Discussion',
                'add_new_item' => 'Start New Discussion',
                'edit_item' => 'Edit Discussion',
                'new_item' => 'New Discussion',
                'view_item' => 'View Discussion',
                'search_items' => 'Search Discussions',
                'not_found' => 'No discussions found',
                'menu_name' => 'Discussions',
            ),
            'public' => true,
            'has_archive' => false, // Disabled - use WordPress page with [microhub_discussions] shortcode
            'rewrite' => array('slug' => 'discussion'), // Singular for individual posts
            'supports' => array('title', 'editor', 'comments', 'author'),
            'menu_icon' => 'dashicons-format-chat',
            'show_in_rest' => true,
        ));

        // Facilities
        register_post_type('mh_facility', array(
            'labels' => array(
                'name' => 'Facilities',
                'singular_name' => 'Facility',
                'add_new' => 'Add Facility',
                'menu_name' => 'Facilities',
            ),
            'public' => true,
            'has_archive' => false, // Disabled - use WordPress page with page-facilities.php template
            'rewrite' => array('slug' => 'imaging-facility'), // Different slug to avoid conflict with mh_facility taxonomy
            'supports' => array('title', 'editor', 'thumbnail'),
            'menu_icon' => 'dashicons-building',
            'show_in_rest' => true,
        ));

        // Contact submissions (private)
        register_post_type('mh_contact', array(
            'labels' => array(
                'name' => 'Contact Messages',
                'singular_name' => 'Contact Message',
                'menu_name' => 'Contact Messages',
            ),
            'public' => false,
            'show_ui' => true,
            'show_in_menu' => 'microhub-settings',
            'supports' => array('title', 'editor', 'custom-fields'),
            'menu_icon' => 'dashicons-email',
            'capability_type' => 'post',
            'capabilities' => array(
                'create_posts' => false,
            ),
            'map_meta_cap' => true,
        ));
    }
}
