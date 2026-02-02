<?php
/**
 * Protocols Page Template for MicroHub
 * Browse and search protocols from papers and community uploads
 */

// Get filter parameters
$search = isset($_GET['search']) ? sanitize_text_field($_GET['search']) : '';
$source_filter = isset($_GET['source']) ? sanitize_text_field($_GET['source']) : '';
$paged = max(1, get_query_var('paged'));

// Get protocols URL
$protocols_url = mh_get_page_url('protocols');

global $wpdb;

// Get all protocols
$protocols = array();

// 1. Get user-uploaded protocols (mh_protocol post type)
$uploaded_args = array(
    'post_type' => 'mh_protocol',
    'posts_per_page' => -1,
    'post_status' => 'publish',
);

if ($search) {
    $uploaded_args['s'] = $search;
}

$uploaded_protocols = get_posts($uploaded_args);

foreach ($uploaded_protocols as $post) {
    $source = get_post_meta($post->ID, '_mh_protocol_source', true);
    if (empty($source)) {
        $source = 'Community';
    }
    
    if ($source_filter && strtolower($source) !== strtolower($source_filter)) {
        continue;
    }
    
    $proto_url = get_post_meta($post->ID, '_mh_protocol_url', true);
    if (empty($proto_url)) {
        $proto_url = get_permalink($post->ID);
    }
    
    $protocols[] = array(
        'id' => $post->ID,
        'title' => $post->post_title,
        'url' => $proto_url,
        'source' => $source,
        'paper_id' => null,
        'paper_title' => null,
        'date' => $post->post_date,
        'type' => 'uploaded',
    );
}

// 2. Get protocols linked from papers (_mh_protocols meta)
$paper_protocols_query = "
    SELECT p.ID, p.post_title, pm.meta_value 
    FROM {$wpdb->postmeta} pm
    JOIN {$wpdb->posts} p ON pm.post_id = p.ID
    WHERE pm.meta_key = '_mh_protocols' 
    AND pm.meta_value != '' 
    AND pm.meta_value != '[]'
    AND p.post_status = 'publish'
    AND p.post_type = 'mh_paper'
";

$paper_results = $wpdb->get_results($paper_protocols_query);

foreach ($paper_results as $paper) {
    $paper_protos = json_decode($paper->meta_value, true);
    if (!is_array($paper_protos)) continue;
    
    foreach ($paper_protos as $proto) {
        $proto_name = isset($proto['name']) ? $proto['name'] : 'Protocol';
        $proto_url = isset($proto['url']) ? $proto['url'] : '';
        
        if (empty($proto_url)) continue;
        
        // Detect source from URL or name
        $source = 'Other';
        $url_lower = strtolower($proto_url);
        $name_lower = strtolower($proto_name);
        
        if (strpos($url_lower, 'protocols.io') !== false || strpos($name_lower, 'protocols.io') !== false) {
            $source = 'protocols.io';
        } elseif (strpos($url_lower, 'bio-protocol') !== false || strpos($name_lower, 'bio-protocol') !== false) {
            $source = 'Bio-protocol';
        } elseif (strpos($url_lower, 'jove.com') !== false || strpos($name_lower, 'jove') !== false) {
            $source = 'JoVE';
        } elseif (strpos($url_lower, 'nature.com/nprot') !== false || strpos($name_lower, 'nature protocol') !== false) {
            $source = 'Nature Protocols';
        } elseif (strpos($url_lower, 'star-protocols') !== false || strpos($name_lower, 'star') !== false) {
            $source = 'STAR Protocols';
        }
        
        // Apply source filter
        if ($source_filter && strtolower($source) !== strtolower($source_filter)) {
            continue;
        }
        
        // Apply search filter
        if ($search) {
            $search_lower = strtolower($search);
            if (strpos(strtolower($proto_name), $search_lower) === false && 
                strpos(strtolower($paper->post_title), $search_lower) === false) {
                continue;
            }
        }
        
        $protocols[] = array(
            'id' => null,
            'title' => $proto_name,
            'url' => $proto_url,
            'source' => $source,
            'paper_id' => $paper->ID,
            'paper_title' => $paper->post_title,
            'date' => null,
            'type' => 'paper_linked',
        );
    }
}

// Sort by source then title
usort($protocols, function($a, $b) {
    $source_cmp = strcmp($a['source'], $b['source']);
    if ($source_cmp !== 0) return $source_cmp;
    return strcmp($a['title'], $b['title']);
});

// Get unique sources for filter
$sources = array_unique(array_column($protocols, 'source'));
sort($sources);

// Pagination
$per_page = 24;
$total = count($protocols);
$total_pages = ceil($total / $per_page);
$offset = ($paged - 1) * $per_page;
$protocols_page = array_slice($protocols, $offset, $per_page);

// Helper function for source class (check if exists first)
if (!function_exists('mh_protocol_source_class')) {
    function mh_protocol_source_class($source) {
        $source_lower = strtolower($source);
        if (strpos($source_lower, 'protocols.io') !== false) return 'protocols-io';
        if (strpos($source_lower, 'bio-protocol') !== false) return 'bio-protocol';
        if (strpos($source_lower, 'jove') !== false) return 'jove';
        if (strpos($source_lower, 'nature') !== false) return 'nature';
        if (strpos($source_lower, 'community') !== false) return 'community';
        return 'other';
    }
}
?>
<div class="microhub-wrapper">
    <?php echo mh_render_nav(); ?>
    <div class="mh-page-container mh-protocols-page">
        <header class="mh-page-header">
            <h1>Protocols</h1>
            <p class="mh-subtitle">Browse <?php echo number_format($total); ?> microscopy protocols from papers and the community</p>
        </header>

        <!-- Filters -->
        <div class="mh-protocols-filters">
            <form method="get" action="<?php echo esc_url($protocols_url); ?>" style="display: flex; gap: 15px; flex-wrap: wrap; width: 100%;">
                <input type="text" name="search" placeholder="Search protocols..." value="<?php echo esc_attr($search); ?>">
                
                <select name="source">
                    <option value="">All Sources</option>
                    <?php foreach ($sources as $src) : ?>
                        <option value="<?php echo esc_attr($src); ?>" <?php selected($source_filter, $src); ?>><?php echo esc_html($src); ?></option>
                    <?php endforeach; ?>
                </select>
                
                <button type="submit" class="mh-submit-btn" style="width: auto; padding: 10px 20px;">Search</button>
                
                <?php if ($search || $source_filter) : ?>
                    <a href="<?php echo esc_url($protocols_url); ?>" style="padding: 10px 15px; color: #8b949e;">Clear</a>
                <?php endif; ?>
            </form>
        </div>

        <?php if (empty($protocols_page)) : ?>
            <div class="mh-no-topics">
                <span class="icon">No Results</span>
                <h3>No protocols found</h3>
                <p>Try adjusting your search or filter criteria.</p>
            </div>
        <?php else : ?>
            <!-- Protocols Grid -->
            <div class="mh-protocols-grid">
                <?php foreach ($protocols_page as $proto) : ?>
                    <div class="mh-protocol-card">
                        <span class="mh-protocol-source <?php echo esc_attr(mh_protocol_source_class($proto['source'])); ?>">
                            <?php echo esc_html($proto['source']); ?>
                        </span>
                        
                        <h3>
                            <a href="<?php echo esc_url($proto['url']); ?>" target="_blank" rel="noopener">
                                <?php echo esc_html($proto['title']); ?>
                            </a>
                        </h3>
                        
                        <?php if ($proto['paper_title']) : ?>
                            <div class="mh-protocol-meta">
                                From paper:
                            </div>
                            <a href="<?php echo get_permalink($proto['paper_id']); ?>" class="mh-protocol-paper-link">
                                <?php echo esc_html(wp_trim_words($proto['paper_title'], 10)); ?>
                            </a>
                        <?php elseif ($proto['type'] === 'uploaded') : ?>
                            <div class="mh-protocol-meta">
                                Community upload
                            </div>
                        <?php endif; ?>
                    </div>
                <?php endforeach; ?>
            </div>

            <!-- Pagination -->
            <?php if ($total_pages > 1) : ?>
                <div class="mh-pagination" style="margin-top: 30px; text-align: center;">
                    <?php
                    $base_url = $protocols_url;
                    if ($search) $base_url = add_query_arg('search', $search, $base_url);
                    if ($source_filter) $base_url = add_query_arg('source', $source_filter, $base_url);
                    
                    echo paginate_links(array(
                        'base' => add_query_arg('paged', '%#%', $base_url),
                        'format' => '',
                        'current' => $paged,
                        'total' => $total_pages,
                        'prev_text' => 'Previous',
                        'next_text' => 'Next',
                    ));
                    ?>
                </div>
            <?php endif; ?>
        <?php endif; ?>
    </div>
</div>
