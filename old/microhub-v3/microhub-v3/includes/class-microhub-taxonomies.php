<?php
/**
 * MicroHub Taxonomies v3.0
 * Register all custom taxonomies including new categories from v3 scraper
 */

class MicroHub_Taxonomies {
    
    public function init() {
        add_action('init', array($this, 'register_taxonomies'));
    }
    
    /**
     * Register all custom taxonomies
     */
    public function register_taxonomies() {
        
        // ============================================================
        // MICROSCOPY TECHNIQUES (hierarchical - can have parent/child)
        // ============================================================
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
        
        // ============================================================
        // MICROSCOPE BRANDS (hierarchical - Brand > Model)
        // ============================================================
        register_taxonomy('mh_microscope_brand', array('mh_paper', 'mh_protocol'), array(
            'labels' => array(
                'name' => __('Microscope Brands', 'microhub'),
                'singular_name' => __('Brand', 'microhub'),
                'search_items' => __('Search Brands', 'microhub'),
                'all_items' => __('All Brands', 'microhub'),
                'parent_item' => __('Parent Brand', 'microhub'),
                'edit_item' => __('Edit Brand', 'microhub'),
                'update_item' => __('Update Brand', 'microhub'),
                'add_new_item' => __('Add New Brand', 'microhub'),
            ),
            'hierarchical' => true,
            'show_ui' => true,
            'show_admin_column' => true,
            'show_in_rest' => true,
            'rewrite' => array('slug' => 'microscope-brand'),
        ));
        
        // ============================================================
        // MICROSCOPE MODELS
        // ============================================================
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
        
        // ============================================================
        // IMAGE ANALYSIS SOFTWARE
        // ============================================================
        register_taxonomy('mh_analysis_software', array('mh_paper', 'mh_protocol'), array(
            'labels' => array(
                'name' => __('Analysis Software', 'microhub'),
                'singular_name' => __('Analysis Software', 'microhub'),
                'search_items' => __('Search Analysis Software', 'microhub'),
                'all_items' => __('All Analysis Software', 'microhub'),
                'edit_item' => __('Edit Software', 'microhub'),
                'add_new_item' => __('Add New Software', 'microhub'),
            ),
            'hierarchical' => false,
            'show_ui' => true,
            'show_admin_column' => true,
            'show_in_rest' => true,
            'rewrite' => array('slug' => 'analysis-software'),
        ));
        
        // ============================================================
        // IMAGE ACQUISITION SOFTWARE
        // ============================================================
        register_taxonomy('mh_acquisition_software', array('mh_paper', 'mh_protocol'), array(
            'labels' => array(
                'name' => __('Acquisition Software', 'microhub'),
                'singular_name' => __('Acquisition Software', 'microhub'),
                'search_items' => __('Search Acquisition Software', 'microhub'),
                'all_items' => __('All Acquisition Software', 'microhub'),
                'edit_item' => __('Edit Software', 'microhub'),
                'add_new_item' => __('Add New Software', 'microhub'),
            ),
            'hierarchical' => false,
            'show_ui' => true,
            'show_admin_column' => false,
            'show_in_rest' => true,
            'rewrite' => array('slug' => 'acquisition-software'),
        ));
        
        // ============================================================
        // SAMPLE PREPARATION
        // ============================================================
        register_taxonomy('mh_sample_prep', array('mh_paper', 'mh_protocol'), array(
            'labels' => array(
                'name' => __('Sample Preparation', 'microhub'),
                'singular_name' => __('Preparation Method', 'microhub'),
                'search_items' => __('Search Preparation Methods', 'microhub'),
                'all_items' => __('All Preparation Methods', 'microhub'),
                'edit_item' => __('Edit Method', 'microhub'),
                'add_new_item' => __('Add New Method', 'microhub'),
            ),
            'hierarchical' => false,
            'show_ui' => true,
            'show_admin_column' => false,
            'show_in_rest' => true,
            'rewrite' => array('slug' => 'sample-preparation'),
        ));
        
        // ============================================================
        // FLUOROPHORES & DYES
        // ============================================================
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
        
        // ============================================================
        // ORGANISMS
        // ============================================================
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
        
        // ============================================================
        // PROTOCOL SOURCES
        // ============================================================
        register_taxonomy('mh_protocol_source', array('mh_paper', 'mh_protocol'), array(
            'labels' => array(
                'name' => __('Protocol Sources', 'microhub'),
                'singular_name' => __('Protocol Source', 'microhub'),
                'search_items' => __('Search Sources', 'microhub'),
                'all_items' => __('All Protocol Sources', 'microhub'),
                'edit_item' => __('Edit Source', 'microhub'),
            ),
            'hierarchical' => false,
            'show_ui' => true,
            'show_admin_column' => false,
            'show_in_rest' => true,
            'rewrite' => array('slug' => 'protocol-source'),
        ));
        
        // ============================================================
        // DATA REPOSITORIES
        // ============================================================
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
        
        // ============================================================
        // JOURNAL (for filtering by journal)
        // ============================================================
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
        
        // ============================================================
        // LEGACY: Software (combined - for backward compatibility)
        // ============================================================
        register_taxonomy('mh_software', array('mh_paper', 'mh_protocol'), array(
            'labels' => array(
                'name' => __('Software (All)', 'microhub'),
                'singular_name' => __('Software', 'microhub'),
            ),
            'hierarchical' => false,
            'show_ui' => true,
            'show_admin_column' => false,
            'show_in_rest' => true,
            'rewrite' => array('slug' => 'software'),
        ));
        
        // ============================================================
        // LEGACY: Microscope (combined - for backward compatibility)
        // ============================================================
        register_taxonomy('mh_microscope', array('mh_paper', 'mh_protocol'), array(
            'labels' => array(
                'name' => __('Microscopes (All)', 'microhub'),
                'singular_name' => __('Microscope', 'microhub'),
            ),
            'hierarchical' => true,
            'show_ui' => true,
            'show_admin_column' => false,
            'show_in_rest' => true,
            'rewrite' => array('slug' => 'microscope'),
        ));
        
        // ============================================================
        // PROTOCOL TYPE (for protocol post type)
        // ============================================================
        register_taxonomy('mh_protocol_type', array('mh_protocol'), array(
            'labels' => array(
                'name' => __('Protocol Types', 'microhub'),
                'singular_name' => __('Protocol Type', 'microhub'),
            ),
            'hierarchical' => true,
            'show_ui' => true,
            'show_admin_column' => true,
            'show_in_rest' => true,
            'rewrite' => array('slug' => 'protocol-type'),
        ));
    }
    
    /**
     * Get all taxonomy slugs for a post type
     */
    public static function get_paper_taxonomies() {
        return array(
            'mh_technique',
            'mh_microscope_brand',
            'mh_microscope_model',
            'mh_analysis_software',
            'mh_acquisition_software',
            'mh_sample_prep',
            'mh_fluorophore',
            'mh_organism',
            'mh_protocol_source',
            'mh_repository',
            'mh_journal',
            'mh_software',
            'mh_microscope',
        );
    }
}
