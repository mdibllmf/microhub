<?php
/**
 * Register custom taxonomies for MicroHub
 */

class MicroHub_Taxonomies {
    
    public function init() {
        add_action('init', array($this, 'register_taxonomies'));
    }
    
    /**
     * Register custom taxonomies
     */
    public function register_taxonomies() {
        // Register Technique taxonomy (hierarchical)
        register_taxonomy('mh_technique', array('mh_paper', 'mh_protocol'), array(
            'labels' => array(
                'name' => __('Techniques', 'microhub'),
                'singular_name' => __('Technique', 'microhub'),
                'search_items' => __('Search Techniques', 'microhub'),
                'all_items' => __('All Techniques', 'microhub'),
                'parent_item' => __('Parent Technique', 'microhub'),
                'parent_item_colon' => __('Parent Technique:', 'microhub'),
                'edit_item' => __('Edit Technique', 'microhub'),
                'update_item' => __('Update Technique', 'microhub'),
                'add_new_item' => __('Add New Technique', 'microhub'),
                'new_item_name' => __('New Technique Name', 'microhub'),
            ),
            'hierarchical' => true,
            'show_ui' => true,
            'show_admin_column' => true,
            'show_in_rest' => true,
            'rewrite' => array('slug' => 'technique'),
        ));
        
        // Register Microscope taxonomy (hierarchical: Brand > Model)
        register_taxonomy('mh_microscope', array('mh_paper', 'mh_protocol'), array(
            'labels' => array(
                'name' => __('Microscopes', 'microhub'),
                'singular_name' => __('Microscope', 'microhub'),
                'search_items' => __('Search Microscopes', 'microhub'),
                'all_items' => __('All Microscopes', 'microhub'),
                'parent_item' => __('Parent Microscope', 'microhub'),
                'parent_item_colon' => __('Parent Microscope:', 'microhub'),
                'edit_item' => __('Edit Microscope', 'microhub'),
                'update_item' => __('Update Microscope', 'microhub'),
                'add_new_item' => __('Add New Microscope', 'microhub'),
                'new_item_name' => __('New Microscope Name', 'microhub'),
            ),
            'hierarchical' => true,
            'show_ui' => true,
            'show_admin_column' => true,
            'show_in_rest' => true,
            'rewrite' => array('slug' => 'microscope'),
        ));
        
        // Register Organism taxonomy (non-hierarchical)
        register_taxonomy('mh_organism', array('mh_paper', 'mh_protocol'), array(
            'labels' => array(
                'name' => __('Organisms', 'microhub'),
                'singular_name' => __('Organism', 'microhub'),
                'search_items' => __('Search Organisms', 'microhub'),
                'all_items' => __('All Organisms', 'microhub'),
                'edit_item' => __('Edit Organism', 'microhub'),
                'update_item' => __('Update Organism', 'microhub'),
                'add_new_item' => __('Add New Organism', 'microhub'),
                'new_item_name' => __('New Organism Name', 'microhub'),
            ),
            'hierarchical' => false,
            'show_ui' => true,
            'show_admin_column' => true,
            'show_in_rest' => true,
            'rewrite' => array('slug' => 'organism'),
        ));
        
        // Register Software taxonomy (non-hierarchical)
        register_taxonomy('mh_software', array('mh_paper', 'mh_protocol'), array(
            'labels' => array(
                'name' => __('Software', 'microhub'),
                'singular_name' => __('Software', 'microhub'),
                'search_items' => __('Search Software', 'microhub'),
                'all_items' => __('All Software', 'microhub'),
                'edit_item' => __('Edit Software', 'microhub'),
                'update_item' => __('Update Software', 'microhub'),
                'add_new_item' => __('Add New Software', 'microhub'),
                'new_item_name' => __('New Software Name', 'microhub'),
            ),
            'hierarchical' => false,
            'show_ui' => true,
            'show_admin_column' => true,
            'show_in_rest' => true,
            'rewrite' => array('slug' => 'software'),
        ));
        
        // Register Protocol Type taxonomy (hierarchical)
        register_taxonomy('mh_protocol_type', array('mh_protocol'), array(
            'labels' => array(
                'name' => __('Protocol Types', 'microhub'),
                'singular_name' => __('Protocol Type', 'microhub'),
                'search_items' => __('Search Protocol Types', 'microhub'),
                'all_items' => __('All Protocol Types', 'microhub'),
                'parent_item' => __('Parent Protocol Type', 'microhub'),
                'parent_item_colon' => __('Parent Protocol Type:', 'microhub'),
                'edit_item' => __('Edit Protocol Type', 'microhub'),
                'update_item' => __('Update Protocol Type', 'microhub'),
                'add_new_item' => __('Add New Protocol Type', 'microhub'),
                'new_item_name' => __('New Protocol Type Name', 'microhub'),
            ),
            'hierarchical' => true,
            'show_ui' => true,
            'show_admin_column' => true,
            'show_in_rest' => true,
            'rewrite' => array('slug' => 'protocol-type'),
        ));
    }
}
