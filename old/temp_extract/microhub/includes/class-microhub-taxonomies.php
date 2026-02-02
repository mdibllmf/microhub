<?php
/**
 * Register custom taxonomies for MicroHub
 * Updated to support new category structure from scraper v2.0
 */

class MicroHub_Taxonomies {

    public function init() {
        add_action('init', array($this, 'register_taxonomies'));
    }

    /**
     * Register custom taxonomies
     */
    public function register_taxonomies() {
        // Register Microscopy Techniques taxonomy (hierarchical)
        // These are LAB TECHNIQUES - the methods used to do microscopy
        register_taxonomy('mh_technique', array('mh_paper', 'mh_protocol'), array(
            'labels' => array(
                'name' => __('Microscopy Techniques', 'microhub'),
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

        // Register Microscope Brands taxonomy (hierarchical)
        // These are MANUFACTURERS - Zeiss, Leica, Nikon, etc.
        register_taxonomy('mh_microscope_brand', array('mh_paper', 'mh_protocol'), array(
            'labels' => array(
                'name' => __('Microscope Brands', 'microhub'),
                'singular_name' => __('Microscope Brand', 'microhub'),
                'search_items' => __('Search Brands', 'microhub'),
                'all_items' => __('All Brands', 'microhub'),
                'parent_item' => __('Parent Brand', 'microhub'),
                'parent_item_colon' => __('Parent Brand:', 'microhub'),
                'edit_item' => __('Edit Brand', 'microhub'),
                'update_item' => __('Update Brand', 'microhub'),
                'add_new_item' => __('Add New Brand', 'microhub'),
                'new_item_name' => __('New Brand Name', 'microhub'),
            ),
            'hierarchical' => true,
            'show_ui' => true,
            'show_admin_column' => true,
            'show_in_rest' => true,
            'rewrite' => array('slug' => 'microscope-brand'),
        ));

        // Register Microscope Models taxonomy (hierarchical)
        // These are SPECIFIC MODELS - LSM 880, SP8, A1R, etc.
        register_taxonomy('mh_microscope_model', array('mh_paper', 'mh_protocol'), array(
            'labels' => array(
                'name' => __('Microscope Models', 'microhub'),
                'singular_name' => __('Microscope Model', 'microhub'),
                'search_items' => __('Search Models', 'microhub'),
                'all_items' => __('All Models', 'microhub'),
                'parent_item' => __('Parent Model', 'microhub'),
                'parent_item_colon' => __('Parent Model:', 'microhub'),
                'edit_item' => __('Edit Model', 'microhub'),
                'update_item' => __('Update Model', 'microhub'),
                'add_new_item' => __('Add New Model', 'microhub'),
                'new_item_name' => __('New Model Name', 'microhub'),
            ),
            'hierarchical' => true,
            'show_ui' => true,
            'show_admin_column' => true,
            'show_in_rest' => true,
            'rewrite' => array('slug' => 'microscope-model'),
        ));

        // Legacy microscope taxonomy (keep for backward compatibility)
        register_taxonomy('mh_microscope', array('mh_paper', 'mh_protocol'), array(
            'labels' => array(
                'name' => __('Microscopes (Legacy)', 'microhub'),
                'singular_name' => __('Microscope', 'microhub'),
            ),
            'hierarchical' => true,
            'show_ui' => true,
            'show_admin_column' => false,
            'show_in_rest' => true,
            'rewrite' => array('slug' => 'microscope'),
        ));

        // Register Image Analysis Software taxonomy (non-hierarchical)
        // These are SOFTWARE FOR ANALYSIS - ImageJ, Fiji, CellProfiler, etc.
        register_taxonomy('mh_analysis_software', array('mh_paper', 'mh_protocol'), array(
            'labels' => array(
                'name' => __('Image Analysis Software', 'microhub'),
                'singular_name' => __('Analysis Software', 'microhub'),
                'search_items' => __('Search Analysis Software', 'microhub'),
                'all_items' => __('All Analysis Software', 'microhub'),
                'edit_item' => __('Edit Analysis Software', 'microhub'),
                'update_item' => __('Update Analysis Software', 'microhub'),
                'add_new_item' => __('Add New Analysis Software', 'microhub'),
                'new_item_name' => __('New Analysis Software Name', 'microhub'),
            ),
            'hierarchical' => false,
            'show_ui' => true,
            'show_admin_column' => true,
            'show_in_rest' => true,
            'rewrite' => array('slug' => 'analysis-software'),
        ));

        // Register Image Acquisition Software taxonomy (non-hierarchical)
        // These are SOFTWARE FOR COLLECTING IMAGES - ZEN, NIS-Elements, LAS X, etc.
        register_taxonomy('mh_acquisition_software', array('mh_paper', 'mh_protocol'), array(
            'labels' => array(
                'name' => __('Image Acquisition Software', 'microhub'),
                'singular_name' => __('Acquisition Software', 'microhub'),
                'search_items' => __('Search Acquisition Software', 'microhub'),
                'all_items' => __('All Acquisition Software', 'microhub'),
                'edit_item' => __('Edit Acquisition Software', 'microhub'),
                'update_item' => __('Update Acquisition Software', 'microhub'),
                'add_new_item' => __('Add New Acquisition Software', 'microhub'),
                'new_item_name' => __('New Acquisition Software Name', 'microhub'),
            ),
            'hierarchical' => false,
            'show_ui' => true,
            'show_admin_column' => true,
            'show_in_rest' => true,
            'rewrite' => array('slug' => 'acquisition-software'),
        ));

        // Legacy software taxonomy (keep for backward compatibility)
        register_taxonomy('mh_software', array('mh_paper', 'mh_protocol'), array(
            'labels' => array(
                'name' => __('Software (Legacy)', 'microhub'),
                'singular_name' => __('Software', 'microhub'),
            ),
            'hierarchical' => false,
            'show_ui' => true,
            'show_admin_column' => false,
            'show_in_rest' => true,
            'rewrite' => array('slug' => 'software'),
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

        // Register Protocol Sources taxonomy (non-hierarchical)
        // protocols.io, Bio-protocol, JoVE, etc.
        register_taxonomy('mh_protocol_source', array('mh_paper', 'mh_protocol'), array(
            'labels' => array(
                'name' => __('Protocol Sources', 'microhub'),
                'singular_name' => __('Protocol Source', 'microhub'),
                'search_items' => __('Search Protocol Sources', 'microhub'),
                'all_items' => __('All Protocol Sources', 'microhub'),
                'edit_item' => __('Edit Protocol Source', 'microhub'),
                'update_item' => __('Update Protocol Source', 'microhub'),
                'add_new_item' => __('Add New Protocol Source', 'microhub'),
                'new_item_name' => __('New Protocol Source Name', 'microhub'),
            ),
            'hierarchical' => false,
            'show_ui' => true,
            'show_admin_column' => true,
            'show_in_rest' => true,
            'rewrite' => array('slug' => 'protocol-source'),
        ));

        // Register Data Repository taxonomy (non-hierarchical)
        // GitHub, Zenodo, Figshare, IDR, etc.
        register_taxonomy('mh_repository', array('mh_paper', 'mh_protocol'), array(
            'labels' => array(
                'name' => __('Data Repositories', 'microhub'),
                'singular_name' => __('Data Repository', 'microhub'),
                'search_items' => __('Search Repositories', 'microhub'),
                'all_items' => __('All Repositories', 'microhub'),
                'edit_item' => __('Edit Repository', 'microhub'),
                'update_item' => __('Update Repository', 'microhub'),
                'add_new_item' => __('Add New Repository', 'microhub'),
                'new_item_name' => __('New Repository Name', 'microhub'),
            ),
            'hierarchical' => false,
            'show_ui' => true,
            'show_admin_column' => true,
            'show_in_rest' => true,
            'rewrite' => array('slug' => 'repository'),
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
