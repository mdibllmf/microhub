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
        
        // Register Microscope Model taxonomy (v3)
        register_taxonomy('mh_microscope_model', array('mh_paper', 'mh_protocol'), array(
            'labels' => array(
                'name' => __('Microscope Models', 'microhub'),
                'singular_name' => __('Microscope Model', 'microhub'),
                'search_items' => __('Search Microscope Models', 'microhub'),
                'all_items' => __('All Microscope Models', 'microhub'),
                'edit_item' => __('Edit Microscope Model', 'microhub'),
                'update_item' => __('Update Microscope Model', 'microhub'),
                'add_new_item' => __('Add New Microscope Model', 'microhub'),
                'new_item_name' => __('New Microscope Model Name', 'microhub'),
            ),
            'hierarchical' => false,
            'show_ui' => true,
            'show_admin_column' => false,
            'show_in_rest' => true,
            'rewrite' => array('slug' => 'microscope-model'),
        ));
        
        // Register Analysis Software taxonomy (v3)
        register_taxonomy('mh_analysis_software', array('mh_paper', 'mh_protocol'), array(
            'labels' => array(
                'name' => __('Analysis Software', 'microhub'),
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
        
        // Register Acquisition Software taxonomy (v3)
        register_taxonomy('mh_acquisition_software', array('mh_paper', 'mh_protocol'), array(
            'labels' => array(
                'name' => __('Acquisition Software', 'microhub'),
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
            'show_admin_column' => false,
            'show_in_rest' => true,
            'rewrite' => array('slug' => 'acquisition-software'),
        ));
        
        // Register Sample Preparation taxonomy (v3)
        register_taxonomy('mh_sample_prep', array('mh_paper', 'mh_protocol'), array(
            'labels' => array(
                'name' => __('Sample Preparation', 'microhub'),
                'singular_name' => __('Sample Preparation', 'microhub'),
                'search_items' => __('Search Sample Preparation', 'microhub'),
                'all_items' => __('All Sample Preparation', 'microhub'),
                'edit_item' => __('Edit Sample Preparation', 'microhub'),
                'update_item' => __('Update Sample Preparation', 'microhub'),
                'add_new_item' => __('Add New Sample Preparation', 'microhub'),
                'new_item_name' => __('New Sample Preparation Name', 'microhub'),
            ),
            'hierarchical' => false,
            'show_ui' => true,
            'show_admin_column' => false,
            'show_in_rest' => true,
            'rewrite' => array('slug' => 'sample-prep'),
        ));
        
        // Register Fluorophore taxonomy (v3)
        register_taxonomy('mh_fluorophore', array('mh_paper', 'mh_protocol'), array(
            'labels' => array(
                'name' => __('Fluorophores', 'microhub'),
                'singular_name' => __('Fluorophore', 'microhub'),
                'search_items' => __('Search Fluorophores', 'microhub'),
                'all_items' => __('All Fluorophores', 'microhub'),
                'edit_item' => __('Edit Fluorophore', 'microhub'),
                'update_item' => __('Update Fluorophore', 'microhub'),
                'add_new_item' => __('Add New Fluorophore', 'microhub'),
                'new_item_name' => __('New Fluorophore Name', 'microhub'),
            ),
            'hierarchical' => false,
            'show_ui' => true,
            'show_admin_column' => false,
            'show_in_rest' => true,
            'rewrite' => array('slug' => 'fluorophore'),
        ));
        
        // Register Cell Line taxonomy (v4)
        register_taxonomy('mh_cell_line', array('mh_paper', 'mh_protocol'), array(
            'labels' => array(
                'name' => __('Cell Lines', 'microhub'),
                'singular_name' => __('Cell Line', 'microhub'),
                'search_items' => __('Search Cell Lines', 'microhub'),
                'all_items' => __('All Cell Lines', 'microhub'),
                'edit_item' => __('Edit Cell Line', 'microhub'),
                'update_item' => __('Update Cell Line', 'microhub'),
                'add_new_item' => __('Add New Cell Line', 'microhub'),
                'new_item_name' => __('New Cell Line Name', 'microhub'),
            ),
            'hierarchical' => false,
            'show_ui' => true,
            'show_admin_column' => false,
            'show_in_rest' => true,
            'rewrite' => array('slug' => 'cell-line'),
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
