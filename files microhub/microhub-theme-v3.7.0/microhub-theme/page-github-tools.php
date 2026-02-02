<?php
/**
 * Page Template for GitHub Tools
 * WordPress automatically uses this for pages with slug "github-tools"
 * Displays the most utilized GitHub repositories across MicroHub papers
 * with health metrics, sorting, and filtering.
 */
get_header();

// Check if plugin is active
if (!function_exists('mh_plugin_active') || !mh_plugin_active()) {
    ?>
    <div class="mh-container" style="padding: 80px 20px; text-align: center;">
        <h1>💻 GitHub Tools</h1>
        <p style="color: var(--text-muted); margin: 20px 0;">The MicroHub plugin is required for full functionality.</p>
    </div>
    <?php
    get_footer();
    return;
}

$api_base = rest_url('microhub/v1');
?>

<div class="microhub-wrapper">
    <?php echo mh_render_nav(); ?>

<!-- Compact Hero -->
<section class="mh-hero-compact">
    <div class="mh-container">
        <h1>💻 GitHub Tools</h1>
        <p>Explore open-source microscopy software tools referenced across MicroHub papers</p>
    </div>
</section>

<!-- Search & Sort Section -->
<section class="mh-search-section">
    <div class="mh-container">
        <!-- Search Bar -->
        <div class="mh-search-bar">
            <div class="mh-search-input-wrapper">
                <svg class="mh-search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
                </svg>
                <input type="text" id="mh-gh-search" placeholder="Search by repository name, language, or description...">
            </div>
            <button type="button" id="mh-gh-search-btn" class="mh-search-button">Search</button>
        </div>

        <!-- Sort & Filter Controls -->
        <div class="mh-filter-row">
            <div class="mh-filter-item">
                <select id="gh-sort">
                    <option value="paper_count">Most Referenced</option>
                    <option value="stars">Most Stars</option>
                    <option value="health">Healthiest</option>
                </select>
            </div>
            <div class="mh-filter-item">
                <select id="gh-min-papers">
                    <option value="1">Min 1 Paper</option>
                    <option value="2" selected>Min 2 Papers</option>
                    <option value="3">Min 3 Papers</option>
                    <option value="5">Min 5 Papers</option>
                    <option value="10">Min 10 Papers</option>
                </select>
            </div>
            <div class="mh-filter-item">
                <select id="gh-language">
                    <option value="">All Languages</option>
                </select>
            </div>
            <div class="mh-filter-item">
                <select id="gh-health-filter">
                    <option value="">All Health</option>
                    <option value="active">Active (70+)</option>
                    <option value="moderate">Moderate (40-69)</option>
                    <option value="low">Low Activity (&lt;40)</option>
                </select>
            </div>
            <div class="mh-filter-item">
                <label class="mh-checkbox-label">
                    <input type="checkbox" id="gh-show-archived">
                    Include Archived
                </label>
            </div>
        </div>
    </div>
</section>

<!-- Stats Row -->
<section class="mh-gh-stats-section">
    <div class="mh-container">
        <div class="mh-gh-stats-row">
            <div class="mh-gh-stat">
                <span class="mh-gh-stat-value" id="gh-stat-total">&mdash;</span>
                <span class="mh-gh-stat-label">Total Tools</span>
            </div>
            <div class="mh-gh-stat">
                <span class="mh-gh-stat-value" id="gh-stat-shown">&mdash;</span>
                <span class="mh-gh-stat-label">Showing</span>
            </div>
            <div class="mh-gh-stat">
                <span class="mh-gh-stat-value" id="gh-stat-active">&mdash;</span>
                <span class="mh-gh-stat-label">Active</span>
            </div>
            <div class="mh-gh-stat">
                <span class="mh-gh-stat-value" id="gh-stat-total-stars">&mdash;</span>
                <span class="mh-gh-stat-label">Total Stars</span>
            </div>
        </div>
    </div>
</section>

<!-- Tools Grid -->
<section class="mh-gh-tools-section">
    <div class="mh-container">
        <div id="mh-gh-loading" class="mh-loading-indicator">
            <div class="mh-spinner"></div>
            <p>Loading GitHub tools...</p>
        </div>
        <div id="mh-gh-tools-grid" class="mh-gh-tools-grid" style="display: none;"></div>
        <div id="mh-gh-empty" class="mh-empty-state" style="display: none;">
            <p>No GitHub tools found matching your criteria.</p>
        </div>
    </div>
</section>

</div><!-- .microhub-wrapper -->

<!-- Page Styles -->
<style>
/* Hero - reuse compact hero from theme */
.mh-hero-compact {
    background: linear-gradient(135deg, var(--bg-card), var(--bg-dark));
    padding: 28px 0 20px;
    text-align: center;
    border-bottom: 1px solid var(--border);
}
.mh-hero-compact h1 { font-size: 1.75rem; margin-bottom: 4px; }
.mh-hero-compact p { color: var(--text-muted); margin: 0; }

/* Checkbox label */
.mh-checkbox-label {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.85rem;
    color: var(--text-muted);
    cursor: pointer;
    white-space: nowrap;
    height: 40px;
}
.mh-checkbox-label input[type="checkbox"] {
    accent-color: var(--primary);
    width: 16px;
    height: 16px;
}

/* Stats Row */
.mh-gh-stats-section {
    padding: 16px 0;
    border-bottom: 1px solid var(--border);
}
.mh-gh-stats-row {
    display: flex;
    gap: 32px;
    justify-content: center;
    flex-wrap: wrap;
}
.mh-gh-stat {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 2px;
}
.mh-gh-stat-value {
    font-size: 1.4rem;
    font-weight: 700;
    color: var(--text);
}
.mh-gh-stat-label {
    font-size: 0.75rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* Tools Section */
.mh-gh-tools-section {
    padding: 24px 0 60px;
}
.mh-gh-tools-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
    gap: 16px;
}

/* Tool Card */
.mh-gh-tool-card {
    display: block;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
    text-decoration: none;
    color: var(--text);
    transition: all 0.2s;
    border-left: 4px solid var(--border);
    position: relative;
}
.mh-gh-tool-card:hover {
    border-color: var(--primary);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
}
.mh-gh-tool-card.health-active { border-left-color: #3fb950; }
.mh-gh-tool-card.health-moderate { border-left-color: #d29922; }
.mh-gh-tool-card.health-low { border-left-color: #f85149; }
.mh-gh-tool-card.health-archived { border-left-color: #6e7681; opacity: 0.75; }
.mh-gh-tool-card.health-unknown { border-left-color: #8b949e; }

/* Card Header */
.mh-gh-card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 8px;
    gap: 12px;
}
.mh-gh-card-name {
    font-size: 1rem;
    font-weight: 600;
    color: var(--primary);
    word-break: break-word;
}
.mh-gh-card-name:hover { color: var(--accent); }

/* Health Badge */
.mh-gh-health-badge {
    font-size: 0.68rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    padding: 3px 10px;
    border-radius: 12px;
    white-space: nowrap;
    flex-shrink: 0;
}
.mh-gh-health-badge.active { background: rgba(63, 185, 80, 0.15); color: #3fb950; }
.mh-gh-health-badge.moderate { background: rgba(210, 153, 34, 0.15); color: #d29922; }
.mh-gh-health-badge.low { background: rgba(248, 81, 73, 0.15); color: #f85149; }
.mh-gh-health-badge.archived { background: rgba(110, 118, 129, 0.15); color: #6e7681; }
.mh-gh-health-badge.unknown { background: rgba(139, 148, 158, 0.1); color: #8b949e; }

/* Card Description */
.mh-gh-card-desc {
    font-size: 0.85rem;
    color: var(--text-muted);
    margin: 0 0 12px;
    line-height: 1.5;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}

/* Metrics Row */
.mh-gh-metrics {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    font-size: 0.8rem;
    color: var(--text-muted);
    margin-bottom: 12px;
}
.mh-gh-metric {
    display: flex;
    align-items: center;
    gap: 4px;
    white-space: nowrap;
}
.mh-gh-metric .icon { font-size: 0.9rem; }
.mh-gh-metric-highlight {
    color: var(--text-light);
    font-weight: 600;
}

/* Relationship Badges */
.mh-gh-relationships {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-bottom: 12px;
}
.mh-gh-rel-badge {
    font-size: 0.72rem;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 8px;
    white-space: nowrap;
}
.mh-gh-rel-badge.introduces { background: rgba(163, 113, 247, 0.15); color: var(--accent); }
.mh-gh-rel-badge.uses { background: rgba(88, 166, 255, 0.1); color: var(--primary); }
.mh-gh-rel-badge.extends { background: rgba(35, 134, 54, 0.15); color: var(--secondary); }
.mh-gh-rel-badge.benchmarks { background: rgba(210, 153, 34, 0.1); color: var(--warning); }

/* Paper Links */
.mh-gh-papers {
    border-top: 1px solid var(--border);
    padding-top: 10px;
    margin-top: 4px;
}
.mh-gh-papers-label {
    font-size: 0.72rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 6px;
}
.mh-gh-paper-list {
    display: flex;
    flex-direction: column;
    gap: 4px;
}
.mh-gh-paper-link {
    font-size: 0.8rem;
    color: var(--text-light);
    display: -webkit-box;
    -webkit-line-clamp: 1;
    -webkit-box-orient: vertical;
    overflow: hidden;
    text-decoration: none;
}
.mh-gh-paper-link:hover { color: var(--primary); }

/* Topics */
.mh-gh-topics {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    margin-bottom: 10px;
}
.mh-gh-topic {
    font-size: 0.7rem;
    background: rgba(88, 166, 255, 0.08);
    color: var(--primary);
    padding: 1px 8px;
    border-radius: 10px;
    border: 1px solid rgba(88, 166, 255, 0.2);
}

/* Loading */
.mh-loading-indicator {
    text-align: center;
    padding: 60px 20px;
    color: var(--text-muted);
}
.mh-spinner {
    width: 36px;
    height: 36px;
    border: 3px solid var(--border);
    border-top-color: var(--primary);
    border-radius: 50%;
    animation: mh-spin 0.8s linear infinite;
    margin: 0 auto 16px;
}
@keyframes mh-spin { to { transform: rotate(360deg); } }

/* Empty */
.mh-empty-state {
    text-align: center;
    padding: 60px 20px;
    color: var(--text-muted);
    font-size: 1.1rem;
}

/* Responsive */
@media (max-width: 768px) {
    .mh-gh-tools-grid { grid-template-columns: 1fr; }
    .mh-gh-stats-row { gap: 16px; }
    .mh-gh-stat-value { font-size: 1.1rem; }
}
</style>

<!-- Page Script -->
<script>
(function() {
    var API_BASE = <?php echo json_encode(esc_url_raw($api_base)); ?>;
    var allTools = [];
    var filteredTools = [];

    var grid = document.getElementById('mh-gh-tools-grid');
    var loading = document.getElementById('mh-gh-loading');
    var empty = document.getElementById('mh-gh-empty');
    var searchInput = document.getElementById('mh-gh-search');
    var searchBtn = document.getElementById('mh-gh-search-btn');
    var sortSelect = document.getElementById('gh-sort');
    var minPapersSelect = document.getElementById('gh-min-papers');
    var languageSelect = document.getElementById('gh-language');
    var healthFilter = document.getElementById('gh-health-filter');
    var showArchived = document.getElementById('gh-show-archived');

    var statTotal = document.getElementById('gh-stat-total');
    var statShown = document.getElementById('gh-stat-shown');
    var statActive = document.getElementById('gh-stat-active');
    var statTotalStars = document.getElementById('gh-stat-total-stars');

    function fetchTools() {
        var sort = sortSelect.value;
        var minPapers = minPapersSelect.value;
        var archived = showArchived.checked ? '1' : '';

        var url = API_BASE + '/github-tools?sort=' + sort + '&limit=100&min_papers=' + minPapers;
        if (archived) url += '&show_archived=1';

        loading.style.display = 'block';
        grid.style.display = 'none';
        empty.style.display = 'none';

        fetch(url)
            .then(function(resp) { return resp.json(); })
            .then(function(data) {
                allTools = data.tools || [];
                statTotal.textContent = data.total || allTools.length;
                populateLanguageFilter();
                applyFilters();
            })
            .catch(function(err) {
                console.error('Failed to load GitHub tools:', err);
                loading.style.display = 'none';
                empty.style.display = 'block';
                empty.querySelector('p').textContent = 'Failed to load GitHub tools. Please try again.';
            });
    }

    function populateLanguageFilter() {
        var languages = {};
        allTools.forEach(function(t) {
            if (t.language) languages[t.language] = (languages[t.language] || 0) + 1;
        });

        var sorted = Object.entries(languages).sort(function(a, b) { return b[1] - a[1]; });
        var current = languageSelect.value;

        languageSelect.innerHTML = '<option value="">All Languages</option>';
        sorted.forEach(function(item) {
            var opt = document.createElement('option');
            opt.value = item[0];
            opt.textContent = item[0] + ' (' + item[1] + ')';
            if (item[0] === current) opt.selected = true;
            languageSelect.appendChild(opt);
        });
    }

    function applyFilters() {
        var query = searchInput.value.toLowerCase().trim();
        var lang = languageSelect.value;
        var health = healthFilter.value;

        filteredTools = allTools.filter(function(t) {
            if (query) {
                var searchable = [
                    t.full_name || '', t.description || '', t.language || ''
                ].concat(t.topics || []).concat(t.paper_titles || []).join(' ').toLowerCase();
                if (searchable.indexOf(query) === -1) return false;
            }
            if (lang && t.language !== lang) return false;
            if (health) {
                var score = t.health_score || 0;
                var arch = t.is_archived;
                if (health === 'active' && (score < 70 || arch)) return false;
                if (health === 'moderate' && (score < 40 || score >= 70 || arch)) return false;
                if (health === 'low' && (score >= 40 || arch)) return false;
            }
            return true;
        });

        statShown.textContent = filteredTools.length;
        var activeCount = filteredTools.filter(function(t) { return (t.health_score || 0) >= 70 && !t.is_archived; }).length;
        statActive.textContent = activeCount;
        var totalStars = filteredTools.reduce(function(sum, t) { return sum + (t.stars || 0); }, 0);
        statTotalStars.textContent = totalStars.toLocaleString();

        renderTools();
    }

    function renderTools() {
        loading.style.display = 'none';
        if (filteredTools.length === 0) {
            grid.style.display = 'none';
            empty.style.display = 'block';
            return;
        }
        empty.style.display = 'none';
        grid.style.display = 'grid';
        grid.innerHTML = filteredTools.map(renderToolCard).join('');
    }

    function renderToolCard(tool) {
        var health = tool.health_score || 0;
        var archived = tool.is_archived;
        var healthClass, healthLabel;

        if (archived) { healthClass = 'archived'; healthLabel = 'Archived'; }
        else if (health >= 70) { healthClass = 'active'; healthLabel = 'Active'; }
        else if (health >= 40) { healthClass = 'moderate'; healthLabel = 'Moderate'; }
        else if (health > 0) { healthClass = 'low'; healthLabel = 'Low Activity'; }
        else { healthClass = 'unknown'; healthLabel = 'Unknown'; }

        var stars = tool.stars || 0;
        var forks = tool.forks || 0;
        var paperCount = tool.paper_count || 0;
        var desc = tool.description ? escapeHtml(truncate(tool.description, 120)) : '';
        var language = tool.language || '';
        var topics = (tool.topics || []).slice(0, 5);
        var license = tool.license || '';
        var lastCommit = tool.last_commit_date ? formatDate(tool.last_commit_date) : '';

        // Relationship badges
        var relBadges = '';
        if (tool.papers_introducing > 0) relBadges += '<span class="mh-gh-rel-badge introduces">Introduced in ' + tool.papers_introducing + ' paper' + (tool.papers_introducing > 1 ? 's' : '') + '</span>';
        if (tool.papers_using > 0) relBadges += '<span class="mh-gh-rel-badge uses">Used in ' + tool.papers_using + ' paper' + (tool.papers_using > 1 ? 's' : '') + '</span>';
        if (tool.papers_extending > 0) relBadges += '<span class="mh-gh-rel-badge extends">Extended in ' + tool.papers_extending + ' paper' + (tool.papers_extending > 1 ? 's' : '') + '</span>';
        if (tool.papers_benchmarking > 0) relBadges += '<span class="mh-gh-rel-badge benchmarks">Benchmarked in ' + tool.papers_benchmarking + ' paper' + (tool.papers_benchmarking > 1 ? 's' : '') + '</span>';

        // Paper links
        var paperLinks = '';
        if (tool.paper_titles && tool.paper_ids && paperCount > 0) {
            var links = '';
            for (var i = 0; i < Math.min(3, tool.paper_titles.length); i++) {
                var title = tool.paper_titles[i];
                var pid = tool.paper_ids[i];
                links += '<a href="/?p=' + pid + '" class="mh-gh-paper-link" title="' + escapeAttr(title) + '">' + escapeHtml(truncate(title, 80)) + '</a>';
            }
            var extra = paperCount > 3 ? '<span class="mh-gh-paper-link" style="color: var(--text-muted); font-style: italic;">+' + (paperCount - 3) + ' more</span>' : '';
            paperLinks = '<div class="mh-gh-papers"><div class="mh-gh-papers-label">Referenced in ' + paperCount + ' paper' + (paperCount > 1 ? 's' : '') + '</div><div class="mh-gh-paper-list">' + links + extra + '</div></div>';
        }

        // Topics
        var topicsHtml = '';
        if (topics.length > 0) {
            topicsHtml = '<div class="mh-gh-topics">';
            topics.forEach(function(t) { topicsHtml += '<span class="mh-gh-topic">' + escapeHtml(t) + '</span>'; });
            topicsHtml += '</div>';
        }

        // Metrics
        var metrics = '<span class="mh-gh-metric"><span class="icon">&#11088;</span> <span class="mh-gh-metric-highlight">' + stars.toLocaleString() + '</span></span>';
        if (forks) metrics += '<span class="mh-gh-metric"><span class="icon">&#127860;</span> ' + forks.toLocaleString() + '</span>';
        if (language) metrics += '<span class="mh-gh-metric"><span class="icon">&#128221;</span> ' + escapeHtml(language) + '</span>';
        if (license) metrics += '<span class="mh-gh-metric"><span class="icon">&#128196;</span> ' + escapeHtml(license) + '</span>';
        if (lastCommit) metrics += '<span class="mh-gh-metric"><span class="icon">&#128336;</span> ' + lastCommit + '</span>';
        metrics += '<span class="mh-gh-metric mh-gh-metric-highlight"><span class="icon">&#128202;</span> ' + paperCount + ' paper' + (paperCount > 1 ? 's' : '') + '</span>';

        return '<div class="mh-gh-tool-card health-' + healthClass + '">' +
            '<div class="mh-gh-card-header">' +
                '<a href="' + escapeAttr(tool.url || ('https://github.com/' + tool.full_name)) + '" class="mh-gh-card-name" target="_blank" rel="noopener">' + escapeHtml(tool.full_name) + '</a>' +
                '<span class="mh-gh-health-badge ' + healthClass + '">' + healthLabel + '</span>' +
            '</div>' +
            (desc ? '<p class="mh-gh-card-desc">' + desc + '</p>' : '') +
            topicsHtml +
            '<div class="mh-gh-metrics">' + metrics + '</div>' +
            (relBadges ? '<div class="mh-gh-relationships">' + relBadges + '</div>' : '') +
            paperLinks +
        '</div>';
    }

    function escapeHtml(str) {
        var d = document.createElement('div');
        d.textContent = str;
        return d.innerHTML;
    }

    function escapeAttr(str) {
        return String(str).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/'/g, '&#39;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    function truncate(str, len) {
        if (!str) return '';
        return str.length > len ? str.substring(0, len) + '...' : str;
    }

    function formatDate(dateStr) {
        if (!dateStr) return '';
        var d = new Date(dateStr);
        if (isNaN(d.getTime())) return dateStr;
        var now = new Date();
        var diff = Math.floor((now - d) / (1000 * 60 * 60 * 24));
        if (diff < 1) return 'today';
        if (diff < 30) return diff + 'd ago';
        if (diff < 365) return Math.floor(diff / 30) + 'mo ago';
        return Math.floor(diff / 365) + 'y ago';
    }

    searchBtn.addEventListener('click', applyFilters);
    searchInput.addEventListener('keypress', function(e) { if (e.key === 'Enter') applyFilters(); });
    sortSelect.addEventListener('change', fetchTools);
    minPapersSelect.addEventListener('change', fetchTools);
    languageSelect.addEventListener('change', applyFilters);
    healthFilter.addEventListener('change', applyFilters);
    showArchived.addEventListener('change', fetchTools);

    fetchTools();
})();
</script>

<?php get_footer(); ?>
