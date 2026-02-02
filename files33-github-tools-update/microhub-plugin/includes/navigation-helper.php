<?php
/**
 * MicroHub Navigation & Link Helper
 * Provides reliable page URL functions for all MicroHub pages
 */

/**
 * Get MicroHub page URL by slug
 * Tries to find the actual page first, falls back to constructed URL
 */
if (!function_exists('mh_get_page_url')) {
    function mh_get_page_url($slug) {
        // Try to find the page by slug
        $page = get_page_by_path($slug);
        if ($page && $page->post_status === 'publish') {
            return get_permalink($page->ID);
        }
        
        // Fallback to constructed URL
        return home_url('/' . $slug . '/');
    }
}

/**
 * Get all MicroHub page URLs as an array
 */
if (!function_exists('mh_get_all_urls')) {
    function mh_get_all_urls() {
        return array(
            'home'            => mh_get_page_url('microhub'),
            'microhub'        => mh_get_page_url('microhub'),
            'search'          => mh_get_page_url('microhub'),
            'discussions'     => mh_get_page_url('discussions'),
            'protocols'       => mh_get_page_url('protocols'),
            'github-tools'    => mh_get_page_url('github-tools'),
            'upload-protocol' => mh_get_page_url('upload-protocol'),
            'upload-paper'    => mh_get_page_url('upload-paper'),
            'about'           => mh_get_page_url('about'),
            'contact'         => mh_get_page_url('contact'),
        );
    }
}

/**
 * Render the main navigation bar
 */
if (!function_exists('mh_render_nav')) {
    function mh_render_nav() {
        $urls = mh_get_all_urls();
        
        $nav_items = array(
            array('url' => $urls['microhub'], 'label' => '🔬 Search', 'slug' => 'microhub'),
            array('url' => $urls['protocols'], 'label' => '📋 Protocols', 'slug' => 'protocols'),
            array('url' => $urls['github-tools'], 'label' => '💻 GitHub Tools', 'slug' => 'github-tools'),
            array('url' => $urls['discussions'], 'label' => '💬 Discussions', 'slug' => 'discussions'),
            array('url' => $urls['upload-protocol'], 'label' => '📤 Upload', 'slug' => 'upload'),
            array('url' => $urls['about'], 'label' => 'ℹ️ About', 'slug' => 'about'),
            array('url' => $urls['contact'], 'label' => '📧 Contact', 'slug' => 'contact'),
        );
        
        $current_url = isset($_SERVER['REQUEST_URI']) ? $_SERVER['REQUEST_URI'] : '';
        
        $html = '<nav class="mh-main-nav"><div class="mh-nav-inner">';
        $html .= '<a href="' . esc_url($urls['microhub']) . '" class="mh-nav-logo">🔬 MicroHub</a>';
        $html .= '<ul class="mh-nav-links">';
        
        foreach ($nav_items as $item) {
            $is_active = '';
            // Check if current URL contains the slug
            if (strpos($current_url, '/' . $item['slug']) !== false) {
                $is_active = ' active';
            }
            $html .= '<li><a href="' . esc_url($item['url']) . '" class="mh-nav-link' . $is_active . '">' . esc_html($item['label']) . '</a></li>';
        }
        
        $html .= '</ul></div></nav>';
        return $html;
    }
}
