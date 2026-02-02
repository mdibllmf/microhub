<?php
/**
 * MicroHub Taxonomies v3.0
 */

if (!defined('ABSPATH')) {
    exit;
}

class MicroHub_Taxonomies {
    
    public function register_taxonomies() {
        
        // Microscopy Techniques
        register_taxonomy('mh_technique', array('mh_paper', 'mh_protocol'), array(
            'labels' => array(
                'name' => __('Microscopy Techniques', 'microhub'),
                'singular_name' => __('Technique', 'microhub'),
                'search_items' => __('Search Techniques', 'microhub'),
                'all_items' => __('All Techniques', 'microhub'),
                'edit_item' => __('Edit Technique', 'microhub'),
                'add_new_item' => __('Add New Technique', 'microhub'),
            ),
            'hierarchical' => true,
            'show_ui' => true,
            'show_admin_column' => true,
            'show_in_rest' => true,
            'rewrite' => array('slug' => 'technique'),
        ));
        
        // Microscope Brands
        register_taxonomy('mh_microscope_brand', array('mh_paper', 'mh_protocol'), array(
            'labels' => array(
                'name' => __('Microscope Brands', 'microhub'),
                'singular_name' => __('Brand', 'microhub'),
                'search_items' => __('Search Brands', 'microhub'),
                'all_items' => __('All Brands', 'microhub'),
                'edit_item' => __('Edit Brand', 'microhub'),
                'add_new_item' => __('Add New Brand', 'microhub'),
            ),
            'hierarchical' => true,
            'show_ui' => true,
            'show_admin_column' => true,
            'show_in_rest' => true,
            'rewrite' => array('slug' => 'microscope-brand'),
        ));
        
        // Microscope Models
        register_taxonomy('mh_microscope_model', array('mh_paper', 'mh_protocol'), array(
            'labels' => array(
                'name' => __('Microscope Models', 'microhub'),
                'singular_name' => __('Model', 'microhub'),
                'search_items' => __('Search Models', 'microhub'),
                'all_items' => __('All Models', 'microhub'),
                'edit_item' => __('Edit Model', 'microhub'),
            ),
            'hierarchical' => false,
            'show_ui' => true,
            'show_admin_column' => true,
            'show_in_rest' => true,
            'rewrite' => array('slug' => 'microscope-model'),
        ));
        
        // Analysis Software
        register_taxonomy('mh_analysis_software', array('mh_paper', 'mh_protocol'), array(
            'labels' => array(
                'name' => __('Analysis Software', 'microhub'),
                'singular_name' => __('Software', 'microhub'),
                'search_items' => __('Search Software', 'microhub'),
                'all_items' => __('All Software', 'microhub'),
                'edit_item' => __('Edit Software', 'microhub'),
                'add_new_item' => __('Add New Software', 'microhub'),
            ),
            'hierarchical' => false,
            'show_ui' => true,
            'show_admin_column' => true,
            'show_in_rest' => true,
            'rewrite' => array('slug' => 'analysis-software'),
        ));
        
        // Sample Preparation
        register_taxonomy('mh_sample_prep', array('mh_paper', 'mh_protocol'), array(
            'labels' => array(
                'name' => __('Sample Preparation', 'microhub'),
                'singular_name' => __('Preparation Method', 'microhub'),
                'search_items' => __('Search Methods', 'microhub'),
                'all_items' => __('All Methods', 'microhub'),
                'edit_item' => __('Edit Method', 'microhub'),
                'add_new_item' => __('Add New Method', 'microhub'),
            ),
            'hierarchical' => false,
            'show_ui' => true,
            'show_admin_column' => false,
            'show_in_rest' => true,
            'rewrite' => array('slug' => 'sample-preparation'),
        ));
        
        // Fluorophores
        register_taxonomy('mh_fluorophore', array('mh_paper', 'mh_protocol'), array(
            'labels' => array(
                'name' => __('Fluorophores', 'microhub'),
                'singular_name' => __('Fluorophore', 'microhub'),
                'search_items' => __('Search Fluorophores', 'microhub'),
                'all_items' => __('All Fluorophores', 'microhub'),
                'edit_item' => __('Edit Fluorophore', 'microhub'),
                'add_new_item' => __('Add New Fluorophore', 'microhub'),
            ),
            'hierarchical' => false,
            'show_ui' => true,
            'show_admin_column' => false,
            'show_in_rest' => true,
            'rewrite' => array('slug' => 'fluorophore'),
        ));
        
        // Organisms
        register_taxonomy('mh_organism', array('mh_paper', 'mh_protocol'), array(
            'labels' => array(
                'name' => __('Organisms', 'microhub'),
                'singular_name' => __('Organism', 'microhub'),
                'search_items' => __('Search Organisms', 'microhub'),
                'all_items' => __('All Organisms', 'microhub'),
                'edit_item' => __('Edit Organism', 'microhub'),
                'add_new_item' => __('Add New Organism', 'microhub'),
            ),
            'hierarchical' => false,
            'show_ui' => true,
            'show_admin_column' => true,
            'show_in_rest' => true,
            'rewrite' => array('slug' => 'organism'),
        ));
        
        // Protocol Sources
        register_taxonomy('mh_protocol_source', array('mh_paper', 'mh_protocol'), array(
            'labels' => array(
                'name' => __('Protocol Sources', 'microhub'),
                'singular_name' => __('Protocol Source', 'microhub'),
                'search_items' => __('Search Sources', 'microhub'),
                'all_items' => __('All Sources', 'microhub'),
                'edit_item' => __('Edit Source', 'microhub'),
            ),
            'hierarchical' => false,
            'show_ui' => true,
            'show_admin_column' => false,
            'show_in_rest' => true,
            'rewrite' => array('slug' => 'protocol-source'),
        ));
        
        // Data Repositories
        register_taxonomy('mh_repository', array('mh_paper', 'mh_protocol'), array(
            'labels' => array(
                'name' => __('Data Repositories', 'microhub'),
                'singular_name' => __('Repository', 'microhub'),
                'search_items' => __('Search Repositories', 'microhub'),
                'all_items' => __('All Repositories', 'microhub'),
                'edit_item' => __('Edit Repository', 'microhub'),
            ),
            'hierarchical' => false,
            'show_ui' => true,
            'show_admin_column' => false,
            'show_in_rest' => true,
            'rewrite' => array('slug' => 'repository'),
        ));
        
        // Journals
        register_taxonomy('mh_journal', array('mh_paper'), array(
            'labels' => array(
                'name' => __('Journals', 'microhub'),
                'singular_name' => __('Journal', 'microhub'),
                'search_items' => __('Search Journals', 'microhub'),
                'all_items' => __('All Journals', 'microhub'),
                'edit_item' => __('Edit Journal', 'microhub'),
            ),
            'hierarchical' => false,
            'show_ui' => true,
            'show_admin_column' => true,
            'show_in_rest' => true,
            'rewrite' => array('slug' => 'journal'),
        ));
    }
}
