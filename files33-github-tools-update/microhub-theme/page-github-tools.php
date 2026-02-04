<?php
/**
 * Page Template for GitHub Tools
 * WordPress automatically uses this for pages with slug "github-tools"
 * Displays the most utilized GitHub repositories across MicroHub papers
 * with health metrics, sorting, and filtering.
 *
 * Structure matches page-protocols.php for visual consistency
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

<!-- Compact Hero -->
<section class="mh-hero-compact">
    <div class="mh-container">
        <h1>💻 GitHub Tools</h1>
        <p>Explore open-source microscopy software tools referenced across MicroHub papers</p>
    </div>
</section>

<!-- Search Section -->
<section class="mh-search-section">
    <div class="mh-container">
        <!-- Main Search Bar -->
        <div class="mh-search-bar">
            <div class="mh-search-input-wrapper">
                <svg class="mh-search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
                </svg>
                <input type="text" id="mh-search-input" placeholder="Search by repository name, language, description, or topic...">
            </div>
            <button type="button" id="mh-search-btn" class="mh-search-button">Search</button>
        </div>

        <!-- Filter Row -->
        <div class="mh-filter-row">
            <div class="mh-filter-item">
                <select id="filter-sort" data-filter="sort">
                    <option value="citations">Most Cited Papers</option>
                    <option value="paper_count">Most Papers</option>
                    <option value="stars">Most Stars</option>
                    <option value="health">Healthiest</option>
                </select>
            </div>
            <div class="mh-filter-item">
                <select id="filter-language" data-filter="language">
                    <option value="">All Languages</option>
                </select>
            </div>
            <div class="mh-filter-item">
                <select id="filter-health" data-filter="health">
                    <option value="">All Health Status</option>
                    <option value="active">Active (70+)</option>
                    <option value="moderate">Moderate (40-69)</option>
                    <option value="low">Low Activity (&lt;40)</option>
                    <option value="archived">Archived</option>
                </select>
            </div>
            <div class="mh-filter-item">
                <select id="filter-min-papers" data-filter="min_papers">
                    <option value="1" selected>Min 1 Paper</option>
                    <option value="2">Min 2 Papers</option>
                    <option value="3">Min 3 Papers</option>
                    <option value="5">Min 5 Papers</option>
                </select>
            </div>
            <div class="mh-filter-item">
                <select id="filter-relationship" data-filter="relationship">
                    <option value="">All Relationships</option>
                    <option value="introduces">Introduced</option>
                    <option value="uses">Used</option>
                    <option value="extends">Extended</option>
                    <option value="benchmarks">Benchmarked</option>
                </select>
            </div>
            <div class="mh-filter-item">
                <select id="filter-license" data-filter="license">
                    <option value="">All Licenses</option>
                </select>
            </div>
        </div>

        <!-- Quick Filters -->
        <div class="mh-quick-filters">
            <span class="mh-quick-label">Quick:</span>
            <button type="button" class="mh-quick-btn" data-filter="active">🟢 Active</button>
            <button type="button" class="mh-quick-btn" data-filter="popular">⭐ Popular (10+ stars)</button>
            <button type="button" class="mh-quick-btn" data-filter="foundational">🏆 Foundational (5+ papers)</button>
            <button type="button" class="mh-quick-btn" data-filter="python">🐍 Python</button>
            <button type="button" class="mh-quick-btn" data-filter="imaging">🔬 Imaging Tools</button>
            <button type="button" id="mh-clear-filters" class="mh-clear-btn">✕ Clear</button>
        </div>
    </div>
</section>

<!-- Results Section -->
<section class="mh-results-section">
    <div class="mh-container">
        <div class="mh-results-header">
            <div class="mh-results-info">
                Showing <strong id="mh-showing">0</strong> of <strong id="mh-total">0</strong> tools
            </div>
            <div class="mh-results-sort">
                <select id="mh-sort">
                    <option value="citations">Most Cited Papers</option>
                    <option value="paper_count">Most Papers</option>
                    <option value="stars">Most Stars</option>
                    <option value="health">Healthiest</option>
                </select>
            </div>
        </div>

        <!-- Stats Bar -->
        <div class="mh-protocol-stats-bar">
            <div class="mh-stat-item">
                <span class="stat-icon">💻</span>
                <span class="stat-num" id="stat-total-tools">0</span>
                <span class="stat-label">Total Tools</span>
            </div>
            <div class="mh-stat-item">
                <span class="stat-icon">🟢</span>
                <span class="stat-num" id="stat-active-tools">0</span>
                <span class="stat-label">Active</span>
            </div>
            <div class="mh-stat-item">
                <span class="stat-icon">📄</span>
                <span class="stat-num" id="stat-total-papers">0</span>
                <span class="stat-label">Papers Using Tools</span>
            </div>
            <div class="mh-stat-item">
                <span class="stat-icon">📊</span>
                <span class="stat-num" id="stat-total-citations">0</span>
                <span class="stat-label">Total Citations</span>
            </div>
        </div>

        <!-- Tools Grid -->
        <div id="mh-tools-grid" class="mh-papers-grid">
            <div class="mh-loading-indicator">
                <div class="mh-spinner"></div>
                <p>Loading GitHub tools...</p>
            </div>
        </div>

        <!-- Pagination -->
        <div id="mh-pagination" class="mh-pagination"></div>
    </div>
</section>

<style>
/* Core Layout - matches protocols page */
.mh-hero-compact { padding: 40px 20px; text-align: center; background: linear-gradient(180deg, var(--bg-card, #161b22) 0%, var(--bg, #0d1117) 100%); border-bottom: 1px solid var(--border, #30363d); }
.mh-hero-compact h1 { font-size: 2rem; margin: 0 0 8px 0; color: var(--text, #c9d1d9); }
.mh-hero-compact p { color: var(--text-muted, #8b949e); margin: 0; font-size: 1.1rem; }
.mh-container { max-width: 1400px; margin: 0 auto; padding: 0 20px; }

/* Search Section */
.mh-search-section { padding: 24px 0; background: var(--bg-card, #161b22); border-bottom: 1px solid var(--border, #30363d); }
.mh-search-bar { display: flex; gap: 12px; margin-bottom: 20px; }
.mh-search-input-wrapper { flex: 1; position: relative; }
.mh-search-icon { position: absolute; left: 14px; top: 50%; transform: translateY(-50%); width: 20px; height: 20px; color: var(--text-muted, #8b949e); }
.mh-search-input-wrapper input { width: 100%; padding: 12px 14px 12px 44px; background: var(--bg, #0d1117); border: 1px solid var(--border, #30363d); border-radius: 8px; color: var(--text, #c9d1d9); font-size: 1rem; }
.mh-search-input-wrapper input:focus { outline: none; border-color: var(--primary, #58a6ff); }
.mh-search-button { padding: 12px 24px; background: var(--primary, #58a6ff); color: #fff; border: none; border-radius: 8px; font-weight: 600; cursor: pointer; }
.mh-search-button:hover { background: var(--primary-hover, #79b8ff); }

/* Filter Rows */
.mh-filter-row { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 12px; }
.mh-filter-item select { padding: 8px 12px; background: var(--bg, #0d1117); border: 1px solid var(--border, #30363d); border-radius: 6px; color: var(--text, #c9d1d9); font-size: 0.85rem; min-width: 140px; cursor: pointer; }
.mh-filter-item select:focus { outline: none; border-color: var(--primary, #58a6ff); }

/* Quick Filters */
.mh-quick-filters { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; }
.mh-quick-label { color: var(--text-muted, #8b949e); font-size: 0.85rem; font-weight: 500; }
.mh-quick-btn { padding: 6px 12px; background: var(--bg, #0d1117); border: 1px solid var(--border, #30363d); border-radius: 20px; color: var(--text-muted, #8b949e); cursor: pointer; font-size: 0.8rem; transition: all 0.2s; }
.mh-quick-btn:hover { border-color: var(--primary, #58a6ff); color: var(--primary, #58a6ff); }
.mh-quick-btn.active { background: var(--primary, #58a6ff); border-color: var(--primary, #58a6ff); color: #fff; }
.mh-clear-btn { padding: 6px 12px; background: transparent; border: 1px solid var(--border, #30363d); border-radius: 20px; color: var(--text-light, #6e7681); cursor: pointer; font-size: 0.8rem; }
.mh-clear-btn:hover { border-color: #f85149; color: #f85149; }

/* Results Section */
.mh-results-section { padding: 24px 0 60px; }
.mh-results-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 12px; }
.mh-results-info { color: var(--text-muted, #8b949e); font-size: 0.9rem; }
.mh-results-info strong { color: var(--text, #c9d1d9); }
.mh-results-sort select { padding: 8px 12px; background: var(--bg-card, #161b22); border: 1px solid var(--border, #30363d); border-radius: 6px; color: var(--text, #c9d1d9); font-size: 0.85rem; }

/* Stats Bar */
.mh-protocol-stats-bar { display: flex; flex-wrap: wrap; gap: 16px; margin-bottom: 24px; padding: 16px; background: var(--bg-card, #161b22); border: 1px solid var(--border, #30363d); border-radius: 8px; }
.mh-stat-item { display: flex; align-items: center; gap: 8px; }
.mh-stat-item .stat-icon { font-size: 1.25rem; }
.mh-stat-item .stat-num { font-weight: 700; color: var(--primary, #58a6ff); font-size: 1.1rem; }
.mh-stat-item .stat-label { color: var(--text-muted, #8b949e); font-size: 0.85rem; }

/* Tools Grid - same as papers grid */
.mh-papers-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 20px; }

/* Loading */
.mh-loading-indicator { grid-column: 1 / -1; text-align: center; padding: 60px 20px; }
.mh-spinner { width: 40px; height: 40px; border: 3px solid var(--border, #30363d); border-top-color: var(--primary, #58a6ff); border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 16px; }
@keyframes spin { to { transform: rotate(360deg); } }

/* No Results */
.mh-no-results { grid-column: 1 / -1; text-align: center; padding: 60px 20px; background: var(--bg-card, #161b22); border-radius: 8px; }
.mh-no-results h3 { margin: 0 0 8px 0; color: var(--text, #c9d1d9); }
.mh-no-results p { color: var(--text-muted, #8b949e); margin: 0; }

/* Tool Card - matches paper card styling */
.mh-paper-card { background: var(--bg-card, #161b22); border: 1px solid var(--border, #30363d); border-radius: 8px; padding: 20px; display: flex; flex-direction: column; transition: border-color 0.2s, transform 0.2s; }
.mh-paper-card:hover { border-color: var(--primary, #58a6ff); transform: translateY(-2px); }
.mh-paper-card.health-active { border-left: 3px solid #3fb950; }
.mh-paper-card.health-moderate { border-left: 3px solid #d29922; }
.mh-paper-card.health-low { border-left: 3px solid #f85149; }
.mh-paper-card.health-archived { border-left: 3px solid #6e7681; opacity: 0.8; }
.mh-paper-card.health-unknown { border-left: 3px solid #8b949e; }

/* Card Header */
.mh-card-header-row { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; gap: 10px; }
.mh-card-badge { font-size: 0.7rem; padding: 4px 8px; border-radius: 4px; font-weight: 600; }
.mh-card-badge.active { background: rgba(63, 185, 80, 0.15); color: #3fb950; }
.mh-card-badge.moderate { background: rgba(210, 153, 34, 0.15); color: #d29922; }
.mh-card-badge.low { background: rgba(248, 81, 73, 0.15); color: #f85149; }
.mh-card-badge.archived { background: rgba(110, 118, 129, 0.15); color: #6e7681; }
.mh-card-badge.unknown { background: rgba(139, 148, 158, 0.1); color: #8b949e; }

/* Card Title */
.mh-card-title { font-size: 1rem; font-weight: 600; line-height: 1.4; margin: 0 0 8px 0; }
.mh-card-title a { color: var(--primary, #58a6ff); text-decoration: none; }
.mh-card-title a:hover { color: var(--accent, #a371f7); }

/* Card Authors */
.mh-card-authors { font-size: 0.85rem; color: var(--text-muted, #8b949e); margin-bottom: 8px; }
.mh-card-authors .mh-author-link { color: var(--text-light, #8b949e); }
.mh-card-authors .mh-last-author { font-weight: 500; }
.mh-card-authors .mh-author-sep { color: var(--text-muted, #6e7681); }
.mh-card-authors .mh-author-note { font-size: 0.75rem; color: var(--accent, #a371f7); font-style: italic; }

/* Card Meta */
.mh-card-meta { font-size: 0.8rem; color: var(--text-muted, #8b949e); margin-bottom: 10px; line-height: 1.4; }
.mh-card-meta span { margin-right: 12px; }

/* Card Abstract/Description */
.mh-card-abstract { font-size: 0.85rem; color: var(--text-light, #8b949e); line-height: 1.5; margin-bottom: 12px; flex: 1; }

/* Card Tags */
.mh-card-tags { display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 12px; }
.mh-card-tag { padding: 3px 8px; border-radius: 12px; font-size: 0.7rem; font-weight: 500; }
.mh-card-tag.language { background: var(--tag-technique, #1e6091); color: white; }
.mh-card-tag.topic { background: rgba(88, 166, 255, 0.1); color: var(--primary, #58a6ff); border: 1px solid rgba(88, 166, 255, 0.2); }
.mh-card-tag.license { background: var(--tag-software, #0891b2); color: white; }
.mh-card-tag.relationship { padding: 2px 6px; font-size: 0.68rem; }
.mh-card-tag.relationship.introduces { background: rgba(163, 113, 247, 0.15); color: var(--accent, #a371f7); }
.mh-card-tag.relationship.uses { background: rgba(88, 166, 255, 0.1); color: var(--primary, #58a6ff); }
.mh-card-tag.relationship.extends { background: rgba(35, 134, 54, 0.15); color: #3fb950; }
.mh-card-tag.relationship.benchmarks { background: rgba(210, 153, 34, 0.1); color: #d29922; }

/* Card Enrichment - metrics */
.mh-card-enrichment { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 12px; font-size: 0.8rem; }
.mh-enrichment-item { color: var(--text-muted, #8b949e); }
.mh-enrichment-item.stars { color: #f0c14b; }
.mh-enrichment-item.forks { color: #8b949e; }
.mh-enrichment-item.papers { color: #3b82f6; font-weight: 600; }
.mh-enrichment-item.citations { color: #22c55e; font-weight: 600; }

/* Card Links */
.mh-card-links { display: flex; flex-wrap: wrap; gap: 8px; padding-top: 12px; border-top: 1px solid var(--border, #30363d); margin-top: auto; }
.mh-card-link { font-size: 0.75rem; padding: 4px 10px; background: var(--bg-hover, #21262d); border-radius: 4px; color: var(--text-muted, #8b949e); text-decoration: none; }
.mh-card-link:hover { background: var(--primary, #58a6ff); color: #fff; }
.mh-card-link.github { color: #a371f7; }
.mh-card-link.papers { color: var(--primary, #58a6ff); }

/* Pagination */
.mh-pagination { display: flex; justify-content: center; gap: 8px; margin-top: 30px; flex-wrap: wrap; }
.mh-pagination button { padding: 8px 14px; background: var(--bg-card, #161b22); border: 1px solid var(--border, #30363d); border-radius: 6px; color: var(--text, #c9d1d9); cursor: pointer; font-size: 0.9rem; }
.mh-pagination button:hover:not(:disabled) { background: var(--primary, #58a6ff); border-color: var(--primary, #58a6ff); color: #fff; }
.mh-pagination button:disabled { opacity: 0.5; cursor: not-allowed; }
.mh-pagination button.active { background: var(--primary, #58a6ff); border-color: var(--primary, #58a6ff); color: #fff; }

/* Responsive */
@media (max-width: 768px) {
    .mh-search-bar { flex-direction: column; }
    .mh-filter-row { flex-direction: column; }
    .mh-filter-item select { width: 100%; }
    .mh-papers-grid { grid-template-columns: 1fr; }
    .mh-protocol-stats-bar { flex-direction: column; gap: 12px; }
    .mh-results-header { flex-direction: column; align-items: flex-start; }
}
</style>

<script>
(function() {
    const apiBase = <?php echo json_encode(esc_url_raw($api_base)); ?>;
    const searchInput = document.getElementById('mh-search-input');
    const searchBtn = document.getElementById('mh-search-btn');
    const sortSelect = document.getElementById('mh-sort');
    const toolsGrid = document.getElementById('mh-tools-grid');
    const paginationEl = document.getElementById('mh-pagination');
    const showingEl = document.getElementById('mh-showing');
    const totalEl = document.getElementById('mh-total');
    const clearBtn = document.getElementById('mh-clear-filters');

    // Stats elements
    const statTotalTools = document.getElementById('stat-total-tools');
    const statActiveTools = document.getElementById('stat-active-tools');
    const statTotalPapers = document.getElementById('stat-total-papers');
    const statTotalCitations = document.getElementById('stat-total-citations');

    let currentPage = 1;
    let perPage = 24;
    let allTools = [];
    let filteredTools = [];
    let activeFilters = {};

    // Initialize
    fetchTools();

    // Event listeners
    searchBtn.addEventListener('click', () => { currentPage = 1; applyFilters(); });
    searchInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') { currentPage = 1; applyFilters(); } });
    sortSelect.addEventListener('change', () => { currentPage = 1; sortTools(); renderTools(); });

    // Filter dropdowns
    document.querySelectorAll('[data-filter]').forEach(select => {
        select.addEventListener('change', () => {
            const filter = select.dataset.filter;
            activeFilters[filter] = select.value;
            currentPage = 1;
            if (filter === 'sort') {
                sortSelect.value = select.value;
            }
            // Re-fetch from API when min_papers changes (server-side filter)
            if (filter === 'min_papers') {
                fetchTools();
            } else {
                applyFilters();
            }
        });
    });

    // Quick filter buttons
    document.querySelectorAll('.mh-quick-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const filter = btn.dataset.filter;
            btn.classList.toggle('active');
            activeFilters[filter] = btn.classList.contains('active');
            currentPage = 1;
            applyFilters();
        });
    });

    // Clear filters
    clearBtn.addEventListener('click', () => {
        searchInput.value = '';
        document.querySelectorAll('[data-filter]').forEach(s => {
            if (s.tagName === 'SELECT') {
                if (s.id === 'filter-sort') s.value = 'citations';
                else if (s.id === 'filter-min-papers') s.value = '1';
                else s.value = '';
            }
        });
        sortSelect.value = 'citations';
        document.querySelectorAll('.mh-quick-btn').forEach(b => b.classList.remove('active'));
        activeFilters = {};
        currentPage = 1;
        fetchTools(); // Re-fetch with reset filters
    });

    // Fetch tools from API
    function fetchTools() {
        toolsGrid.innerHTML = '<div class="mh-loading-indicator"><div class="mh-spinner"></div><p>Loading GitHub tools...</p></div>';

        const minPapers = document.getElementById('filter-min-papers')?.value || 1;

        fetch(apiBase + '/github-tools?limit=1000&min_papers=' + minPapers + '&show_archived=1')
            .then(res => res.json())
            .then(data => {
                allTools = data.tools || [];
                updateStats();
                populateFilterOptions();
                applyFilters();
            })
            .catch(err => {
                console.error('Failed to load tools:', err);
                toolsGrid.innerHTML = '<div class="mh-no-results"><h3>Error loading tools</h3><p>Please try again. Error: ' + err.message + '</p></div>';
            });
    }

    // Update stats
    function updateStats() {
        statTotalTools.textContent = formatNumber(allTools.length);

        const activeCount = allTools.filter(t => (t.health_score || 0) >= 70 && !t.is_archived).length;
        statActiveTools.textContent = formatNumber(activeCount);

        // Count unique papers
        const paperIds = new Set();
        allTools.forEach(t => (t.paper_ids || []).forEach(id => paperIds.add(id)));
        statTotalPapers.textContent = formatNumber(paperIds.size);

        // Sum citations
        const totalCitations = allTools.reduce((sum, t) => sum + (t.total_citations || 0), 0);
        statTotalCitations.textContent = formatNumber(totalCitations);
    }

    // Populate filter dropdowns
    function populateFilterOptions() {
        // Languages
        const langSelect = document.getElementById('filter-language');
        const languages = {};
        allTools.forEach(t => { if (t.language) languages[t.language] = (languages[t.language] || 0) + 1; });
        const sortedLangs = Object.entries(languages).sort((a, b) => b[1] - a[1]);
        langSelect.innerHTML = '<option value="">All Languages</option>';
        sortedLangs.forEach(([lang, count]) => {
            langSelect.innerHTML += `<option value="${escapeHtml(lang)}">${escapeHtml(lang)} (${count})</option>`;
        });

        // Licenses
        const licenseSelect = document.getElementById('filter-license');
        const licenses = {};
        allTools.forEach(t => { if (t.license) licenses[t.license] = (licenses[t.license] || 0) + 1; });
        const sortedLicenses = Object.entries(licenses).sort((a, b) => b[1] - a[1]);
        licenseSelect.innerHTML = '<option value="">All Licenses</option>';
        sortedLicenses.forEach(([lic, count]) => {
            licenseSelect.innerHTML += `<option value="${escapeHtml(lic)}">${escapeHtml(lic)} (${count})</option>`;
        });
    }

    // Apply filters
    function applyFilters() {
        const query = searchInput.value.toLowerCase().trim();
        const lang = activeFilters.language || '';
        const health = activeFilters.health || '';
        const relationship = activeFilters.relationship || '';
        const license = activeFilters.license || '';

        filteredTools = allTools.filter(tool => {
            // Search query
            if (query) {
                const searchable = [
                    tool.full_name || '',
                    tool.description || '',
                    tool.language || '',
                    ...(tool.topics || []),
                    ...(tool.paper_titles || [])
                ].join(' ').toLowerCase();
                if (!searchable.includes(query)) return false;
            }

            // Language filter
            if (lang && tool.language !== lang) return false;

            // License filter
            if (license && tool.license !== license) return false;

            // Health filter
            if (health) {
                const score = tool.health_score || 0;
                const arch = tool.is_archived;
                if (health === 'active' && (score < 70 || arch)) return false;
                if (health === 'moderate' && (score < 40 || score >= 70 || arch)) return false;
                if (health === 'low' && (score >= 40 || arch)) return false;
                if (health === 'archived' && !arch) return false;
            }

            // Relationship filter
            if (relationship) {
                if (relationship === 'introduces' && !tool.papers_introducing) return false;
                if (relationship === 'uses' && !tool.papers_using) return false;
                if (relationship === 'extends' && !tool.papers_extending) return false;
                if (relationship === 'benchmarks' && !tool.papers_benchmarking) return false;
            }

            // Quick filters
            if (activeFilters.active && ((tool.health_score || 0) < 70 || tool.is_archived)) return false;
            if (activeFilters.popular && (tool.stars || 0) < 10) return false;
            if (activeFilters.foundational && (tool.paper_count || 0) < 5) return false;
            if (activeFilters.python && tool.language !== 'Python') return false;
            if (activeFilters.imaging) {
                const topics = (tool.topics || []).join(' ').toLowerCase();
                const desc = (tool.description || '').toLowerCase();
                const name = (tool.full_name || '').toLowerCase();
                if (!topics.includes('imag') && !desc.includes('imag') && !name.includes('imag') &&
                    !topics.includes('microscop') && !desc.includes('microscop')) return false;
            }

            return true;
        });

        sortTools();
        totalEl.textContent = formatNumber(allTools.length);
        showingEl.textContent = filteredTools.length;
        renderTools();
    }

    // Sort tools
    function sortTools() {
        const sort = sortSelect.value;
        filteredTools.sort((a, b) => {
            if (sort === 'citations') return (b.total_citations || 0) - (a.total_citations || 0);
            if (sort === 'stars') return (b.stars || 0) - (a.stars || 0);
            if (sort === 'health') return (b.health_score || 0) - (a.health_score || 0);
            return (b.paper_count || 0) - (a.paper_count || 0); // Default: paper_count
        });
    }

    // Render tools
    function renderTools() {
        if (filteredTools.length === 0) {
            toolsGrid.innerHTML = '<div class="mh-no-results"><h3>No tools found</h3><p>Try adjusting your search or filters.</p></div>';
            paginationEl.innerHTML = '';
            return;
        }

        const start = (currentPage - 1) * perPage;
        const pageTools = filteredTools.slice(start, start + perPage);

        toolsGrid.innerHTML = pageTools.map(createToolCard).join('');
        renderPagination(filteredTools.length, Math.ceil(filteredTools.length / perPage));
    }

    // Create tool card - matches paper card layout
    function createToolCard(tool) {
        const health = tool.health_score || 0;
        const archived = tool.is_archived;
        let healthClass, healthLabel;

        if (archived) { healthClass = 'archived'; healthLabel = 'Archived'; }
        else if (health >= 70) { healthClass = 'active'; healthLabel = 'Active'; }
        else if (health >= 40) { healthClass = 'moderate'; healthLabel = 'Moderate'; }
        else if (health > 0) { healthClass = 'low'; healthLabel = 'Low Activity'; }
        else { healthClass = 'unknown'; healthLabel = 'Unknown'; }

        const stars = tool.stars || 0;
        const forks = tool.forks || 0;
        const paperCount = tool.paper_count || 0;
        const totalCitations = tool.total_citations || 0;

        // Tags
        let tagsHtml = '';
        if (tool.language) {
            tagsHtml += `<span class="mh-card-tag language">${escapeHtml(tool.language)}</span>`;
        }
        if (tool.license) {
            tagsHtml += `<span class="mh-card-tag license">${escapeHtml(tool.license)}</span>`;
        }
        // Relationship badges
        if (tool.papers_introducing > 0) {
            tagsHtml += `<span class="mh-card-tag relationship introduces">🆕 Introduced in ${tool.papers_introducing}</span>`;
        }
        if (tool.papers_extending > 0) {
            tagsHtml += `<span class="mh-card-tag relationship extends">🔀 Extended in ${tool.papers_extending}</span>`;
        }
        // Topics (limit to 3)
        if (tool.topics?.length) {
            tool.topics.slice(0, 3).forEach(t => {
                tagsHtml += `<span class="mh-card-tag topic">${escapeHtml(t)}</span>`;
            });
        }

        // Enrichment/metrics
        let enrichmentHtml = `<div class="mh-card-enrichment">`;
        enrichmentHtml += `<span class="mh-enrichment-item citations">📊 ${formatNumber(totalCitations)} citations</span>`;
        enrichmentHtml += `<span class="mh-enrichment-item papers">📄 ${paperCount} paper${paperCount !== 1 ? 's' : ''}</span>`;
        enrichmentHtml += `<span class="mh-enrichment-item stars">⭐ ${formatNumber(stars)}</span>`;
        if (forks > 0) enrichmentHtml += `<span class="mh-enrichment-item forks">🍴 ${formatNumber(forks)}</span>`;
        if (tool.last_commit_date) enrichmentHtml += `<span class="mh-enrichment-item">🕐 ${formatDate(tool.last_commit_date)}</span>`;
        enrichmentHtml += `</div>`;

        // Links
        let linksHtml = '';
        const repoUrl = tool.url || `https://github.com/${tool.full_name}`;
        linksHtml += `<a href="${escapeHtml(repoUrl)}" class="mh-card-link github" target="_blank" rel="noopener">GitHub</a>`;
        if (paperCount > 0 && tool.paper_ids?.length) {
            linksHtml += `<a href="/?p=${tool.paper_ids[0]}" class="mh-card-link papers">View Paper</a>`;
        }

        // Description
        const desc = tool.description ? truncate(tool.description, 150) : 'No description available.';

        // Authors display
        let authorsHtml = '';
        if (tool.authors?.length) {
            const firstAuthor = tool.authors[0];
            const lastAuthor = tool.authors.length > 1 ? tool.authors[tool.authors.length - 1] : null;
            authorsHtml = `<div class="mh-card-authors">`;
            authorsHtml += `<span class="mh-author-link">${escapeHtml(firstAuthor)}</span>`;
            if (lastAuthor && lastAuthor !== firstAuthor) {
                authorsHtml += tool.authors.length > 2 ? `<span class="mh-author-sep"> ... </span>` : `<span class="mh-author-sep">, </span>`;
                authorsHtml += `<span class="mh-author-link mh-last-author">${escapeHtml(lastAuthor)}</span>`;
            }
            if (tool.papers_introducing > 0) {
                authorsHtml += ` <span class="mh-author-note">(introduced)</span>`;
            }
            authorsHtml += `</div>`;
        }

        return `
            <article class="mh-paper-card health-${healthClass}">
                <div class="mh-card-header-row">
                    <span class="mh-card-badge ${healthClass}">${healthLabel}</span>
                </div>
                <h3 class="mh-card-title"><a href="${escapeHtml(repoUrl)}" target="_blank" rel="noopener">${escapeHtml(tool.full_name)}</a></h3>
                ${authorsHtml}
                <div class="mh-card-meta">
                    ${tool.language ? `<span>📝 ${escapeHtml(tool.language)}</span>` : ''}
                    <span>📊 ${formatNumber(totalCitations)} citations</span>
                    <span>📄 ${paperCount} papers</span>
                </div>
                <p class="mh-card-abstract">${escapeHtml(desc)}</p>
                ${tagsHtml ? `<div class="mh-card-tags">${tagsHtml}</div>` : ''}
                ${enrichmentHtml}
                <div class="mh-card-footer">
                    <div class="mh-card-links">${linksHtml}</div>
                </div>
            </article>
        `;
    }

    // Render pagination
    function renderPagination(total, totalPages) {
        if (totalPages <= 1) {
            paginationEl.innerHTML = '';
            return;
        }

        let html = '';
        html += `<button ${currentPage === 1 ? 'disabled' : ''} data-page="${currentPage - 1}">← Prev</button>`;

        const maxVisible = 5;
        let start = Math.max(1, currentPage - Math.floor(maxVisible / 2));
        let end = Math.min(totalPages, start + maxVisible - 1);
        if (end - start < maxVisible - 1) start = Math.max(1, end - maxVisible + 1);

        if (start > 1) {
            html += `<button data-page="1">1</button>`;
            if (start > 2) html += `<button disabled>...</button>`;
        }

        for (let i = start; i <= end; i++) {
            html += `<button ${i === currentPage ? 'class="active"' : ''} data-page="${i}">${i}</button>`;
        }

        if (end < totalPages) {
            if (end < totalPages - 1) html += `<button disabled>...</button>`;
            html += `<button data-page="${totalPages}">${totalPages}</button>`;
        }

        html += `<button ${currentPage === totalPages ? 'disabled' : ''} data-page="${currentPage + 1}">Next →</button>`;

        paginationEl.innerHTML = html;

        paginationEl.querySelectorAll('button[data-page]').forEach(btn => {
            btn.addEventListener('click', () => {
                currentPage = parseInt(btn.dataset.page);
                renderTools();
                window.scrollTo({ top: 0, behavior: 'smooth' });
            });
        });
    }

    // Utilities
    function escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    function formatNumber(num) {
        return new Intl.NumberFormat().format(num);
    }

    function truncate(str, len) {
        if (!str) return '';
        return str.length > len ? str.substring(0, len) + '...' : str;
    }

    function formatDate(dateStr) {
        if (!dateStr) return '';
        const d = new Date(dateStr);
        if (isNaN(d.getTime())) return dateStr;
        const now = new Date();
        const diff = Math.floor((now - d) / (1000 * 60 * 60 * 24));
        if (diff < 1) return 'today';
        if (diff < 30) return diff + 'd ago';
        if (diff < 365) return Math.floor(diff / 30) + 'mo ago';
        return Math.floor(diff / 365) + 'y ago';
    }
})();
</script>

<?php get_footer(); ?>
