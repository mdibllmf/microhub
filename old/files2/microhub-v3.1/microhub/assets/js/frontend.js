/**
 * MicroHub Frontend JavaScript v2.1
 * Enhanced with Microsoft Copilot, GitHub, discussions
 */
(function($) {
    'use strict';

    if (typeof microhubData === 'undefined') {
        console.warn('MicroHub: Configuration not found');
        return;
    }

    var MicroHub = {
        apiBase: microhubData.apiBase || '/wp-json/microhub/v1',
        copilotUrl: microhubData.copilotUrl || '',
        copilotName: microhubData.copilotName || 'MicroHub Assistant',
        perPage: 24,
        currentPage: 1,
        activeFilters: {},
        isLoading: false,
        searchTimeout: null,
        currentPaperContext: null
    };

    /**
     * Initialize
     */
    MicroHub.init = function() {
        console.log('MicroHub v2.1 initialized');
        this.bindEvents();
        this.loadFilterOptions();
        this.loadEnrichmentCounts();
        this.loadSidebarWidgets();
        this.searchPapers();
        this.initAIChat();
    };

    /**
     * Bind all events
     */
    MicroHub.bindEvents = function() {
        var self = this;

        // Search input - debounced
        $(document).on('input', '#mh-search-input', function() {
            clearTimeout(self.searchTimeout);
            self.searchTimeout = setTimeout(function() {
                self.currentPage = 1;
                self.searchPapers();
            }, 400);
        });

        // Search button
        $(document).on('click', '#mh-search-btn', function() {
            clearTimeout(self.searchTimeout);
            self.currentPage = 1;
            self.searchPapers();
        });

        // Enter key
        $(document).on('keypress', '#mh-search-input', function(e) {
            if (e.which === 13) {
                e.preventDefault();
                clearTimeout(self.searchTimeout);
                self.currentPage = 1;
                self.searchPapers();
            }
        });

        // Filter dropdowns
        $(document).on('change', '[data-filter]', function() {
            var filter = $(this).data('filter');
            var value = $(this).val();
            
            if (value) {
                self.activeFilters[filter] = value;
            } else {
                delete self.activeFilters[filter];
            }
            
            self.currentPage = 1;
            self.searchPapers();
        });

        // Quick filter buttons
        $(document).on('click', '.mh-quick-btn', function(e) {
            e.preventDefault();
            var $btn = $(this);
            var filter = $btn.data('filter');

            if ($btn.hasClass('active')) {
                $btn.removeClass('active');
                delete self.activeFilters[filter];
            } else {
                $('.mh-quick-btn').removeClass('active');
                $btn.addClass('active');

                // Clear quick filters
                delete self.activeFilters.foundational;
                delete self.activeFilters.high_impact;
                delete self.activeFilters.has_protocols;
                delete self.activeFilters.has_github;
                delete self.activeFilters.has_repositories;

                self.activeFilters[filter] = true;
            }

            self.currentPage = 1;
            self.searchPapers();
        });

        // Sort dropdown
        $(document).on('change', '#mh-sort', function() {
            self.currentPage = 1;
            self.searchPapers();
        });

        // Clear all filters
        $(document).on('click', '#mh-clear-filters', function(e) {
            e.preventDefault();
            self.clearAllFilters();
        });

        // Pagination
        $(document).on('click', '.mh-pagination button:not(:disabled)', function() {
            var page = $(this).data('page');
            if (page && page !== self.currentPage) {
                self.currentPage = parseInt(page);
                self.searchPapers();
                $('html, body').animate({
                    scrollTop: $('.mh-results-section').offset().top - 100
                }, 400);
            }
        });

        // AI Discuss button on cards
        $(document).on('click', '.mh-ai-discuss', function() {
            var title = $(this).data('title');
            self.currentPaperContext = title;
            $('#mh-ai-context').text('Context: ' + title);
            $('#mh-ai-panel').addClass('open');
            $('#mh-ai-input').val('Tell me about this paper: ' + title);
        });
    };

    /**
     * Initialize AI Chat Widget (Microsoft Copilot Studio)
     */
    MicroHub.initAIChat = function() {
        var self = this;

        // Only init if Copilot is configured
        if (!this.copilotUrl) {
            console.log('MicroHub: Copilot not configured');
            return;
        }

        // Toggle chat panel
        $(document).on('click', '#mh-ai-toggle', function() {
            var $panel = $('#mh-ai-panel');
            $panel.toggleClass('open');
            
            // Load iframe if not already loaded
            if ($panel.hasClass('open')) {
                var $iframe = $('#mh-copilot-iframe');
                if ($iframe.length && !$iframe.attr('src')) {
                    $iframe.attr('src', self.copilotUrl);
                }
            }
        });

        // Close chat
        $(document).on('click', '#mh-ai-close', function() {
            $('#mh-ai-panel').removeClass('open');
        });

        // Ask AI button on paper pages
        $(document).on('click', '.mh-ask-ai-btn', function() {
            var title = $(this).data('paper-title');
            self.currentPaperContext = title;
            $('#mh-ai-panel').addClass('open');
            
            // Load iframe if needed
            var $iframe = $('#mh-copilot-iframe');
            if ($iframe.length && !$iframe.attr('src')) {
                $iframe.attr('src', self.copilotUrl);
            }
        });
    };

    /**
     * Format AI response (convert markdown to HTML)
     */
    MicroHub.formatAIResponse = function(text) {
        if (!text) return '';
        return text
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.+?)\*/g, '<em>$1</em>')
            .replace(/`(.+?)`/g, '<code>$1</code>')
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br>')
            .replace(/^/, '<p>')
            .replace(/$/, '</p>');
    };

    /**
     * Fallback AI Response - used when no API key (kept for reference)
     */
    MicroHub.getSmartAIResponse = function(message) {
        var msg = message.toLowerCase();
        var response = '';
        
        // CONFOCAL
        if (msg.includes('confocal') && (msg.includes('how') || msg.includes('what') || msg.includes('work'))) {
            response = '<strong>Confocal Microscopy</strong><br><br>' +
                'Uses a pinhole aperture to eliminate out-of-focus light, creating sharp optical sections.<br><br>' +
                '<strong>Key features:</strong><br>• Point-by-point laser scanning<br>• Pinhole blocks out-of-focus light<br>• Z-stacking for 3D reconstruction<br>• ~200nm lateral, ~500nm axial resolution<br><br>' +
                '<strong>Best for:</strong> Fixed samples, 3D imaging up to ~100μm, colocalization<br><br>' +
                '<strong>Systems:</strong> Zeiss LSM 880/980, Leica SP8, Nikon A1, Olympus FV3000<br><br>' +
                '💡 <em>Tip: Use #1.5 coverslips and match immersion oil to objective.</em>';
        }
        else if (msg.includes('confocal')) {
            response = 'Confocal microscopy uses point illumination and a pinhole to eliminate out-of-focus light, producing sharp optical sections. Ideal for 3D imaging up to ~100μm. Common systems: Zeiss LSM, Leica SP8, Nikon A1. Want more details on how it works?';
        }
        
        // TWO-PHOTON
        else if (msg.includes('two-photon') || msg.includes('2-photon') || msg.includes('multiphoton')) {
            response = '<strong>Two-Photon Microscopy</strong><br><br>' +
                'Uses near-infrared light (~700-1000nm) where two photons excite fluorophores simultaneously.<br><br>' +
                '<strong>Advantages:</strong><br>• Deep tissue penetration (up to 1mm)<br>• Reduced photobleaching<br>• Intrinsic optical sectioning<br>• Less scattering<br><br>' +
                '<strong>Best for:</strong> Live tissue, intravital imaging, neuroscience, developmental biology<br><br>' +
                '💡 <em>Tip: Use red-shifted indicators (GCaMP6/8, jRGECO) for deeper imaging.</em>';
        }
        
        // LIGHT SHEET
        else if (msg.includes('light sheet') || msg.includes('lightsheet') || msg.includes('spim')) {
            response = '<strong>Light Sheet Microscopy (SPIM)</strong><br><br>' +
                'Illuminates sample from the side with thin light sheet, detects perpendicular.<br><br>' +
                '<strong>Advantages:</strong><br>• 100-1000x less photobleaching than confocal<br>• Fast (entire plane at once)<br>• Excellent for long-term live imaging<br><br>' +
                '<strong>Best for:</strong> Developmental biology, cleared tissues, organoids<br><br>' +
                '<strong>Systems:</strong> Zeiss Lightsheet 7, custom OpenSPIM<br><br>' +
                '💡 <em>Tip: Sample mounting is critical - use FEP tubes or low-melting agarose.</em>';
        }
        
        // TIRF
        else if (msg.includes('tirf') || msg.includes('total internal reflection')) {
            response = '<strong>TIRF Microscopy</strong><br><br>' +
                'Uses evanescent wave to illuminate only ~100nm above the coverslip.<br><br>' +
                '<strong>How it works:</strong><br>• Light hits glass/water at critical angle<br>• Creates decaying evanescent field<br>• Only near-membrane fluorophores excited<br><br>' +
                '<strong>Best for:</strong> Single molecules, membrane dynamics, vesicle fusion, receptor trafficking<br><br>' +
                '💡 <em>Tip: Clean coverslips are essential - use plasma cleaning.</em>';
        }
        
        // STED
        else if (msg.includes('sted')) {
            response = '<strong>STED Microscopy</strong><br><br>' +
                'Stimulated Emission Depletion uses donut-shaped beam to shrink effective PSF to ~20-50nm.<br><br>' +
                '<strong>How it works:</strong><br>1. Excitation laser excites fluorophores<br>2. Donut STED beam depletes edges<br>3. Only center molecules fluoresce<br><br>' +
                '<strong>Best for:</strong> Fixed samples, synapses, cytoskeleton, nuclear pores<br><br>' +
                '<strong>Dyes:</strong> ATTO 647N, Abberior STAR dyes (very photostable)<br><br>' +
                '🏆 <em>2014 Nobel Prize (Stefan Hell)</em>';
        }
        
        // STORM/PALM
        else if (msg.includes('storm') || msg.includes('palm') || msg.includes('single molecule localization')) {
            response = '<strong>STORM/PALM (~20nm resolution)</strong><br><br>' +
                'Single molecule localization over thousands of frames.<br><br>' +
                '<strong>STORM:</strong> Photoswitchable dyes (Alexa 647, Cy5) + thiol buffer<br>' +
                '<strong>PALM:</strong> Photoactivatable proteins (mEos, Dendra2) - better for live cells<br><br>' +
                '<strong>Requirements:</strong><br>• TIRF/HILO illumination<br>• High-power lasers<br>• EMCCD/sCMOS camera<br>• 10,000-50,000 frames<br><br>' +
                '💡 <em>Tip: Use fiducial markers for drift correction.</em>';
        }
        
        // SIM
        else if (msg.includes('sim') && (msg.includes('structur') || msg.includes('microscop'))) {
            response = '<strong>SIM (Structured Illumination)</strong><br><br>' +
                'Doubles resolution (~100nm) using patterned illumination + computation.<br><br>' +
                '<strong>How it works:</strong><br>• Project stripe pattern on sample<br>• Rotate pattern (3-5 angles)<br>• Computationally extract high frequencies<br><br>' +
                '<strong>Advantages:</strong><br>• Works with standard dyes<br>• Relatively fast<br>• Good for live cells<br><br>' +
                '<strong>Systems:</strong> Zeiss Elyra, Nikon N-SIM, GE OMX';
        }
        
        // SUPER-RESOLUTION OVERVIEW
        else if (msg.includes('super-resolution') || msg.includes('super resolution') || msg.includes('nanoscopy')) {
            response = '<strong>Super-Resolution Overview</strong><br><br>' +
                'Techniques breaking the ~200nm diffraction limit:<br><br>' +
                '<strong>STED</strong> (~50nm): Depletion beam, fast but high light<br>' +
                '<strong>STORM/PALM</strong> (~20nm): Best resolution, slow (minutes)<br>' +
                '<strong>SIM</strong> (~100nm): Fast, gentle, standard dyes<br>' +
                '<strong>Expansion</strong> (~70nm): Physical expansion, standard confocal<br>' +
                '<strong>Airyscan</strong> (~140nm): Easy, live-cell friendly<br><br>' +
                'Which would you like to know more about?';
        }
        
        // CRYO-EM
        else if (msg.includes('cryo-em') || msg.includes('cryo em') || msg.includes('cryoem')) {
            response = '<strong>Cryo-Electron Microscopy</strong><br><br>' +
                'Images samples in vitreous ice at near-atomic resolution.<br><br>' +
                '<strong>Single Particle:</strong> Purified proteins, 2-4Å possible<br>' +
                '<strong>Cryo-ET:</strong> Cells/tissues, tilt series, 3D tomograms<br><br>' +
                '<strong>Sample prep:</strong> Plunge freezing (Vitrobot)<br><br>' +
                '🏆 <em>2017 Nobel Prize - revolutionized structural biology!</em>';
        }
        
        // FRET
        else if (msg.includes('fret')) {
            response = '<strong>FRET (Förster Resonance Energy Transfer)</strong><br><br>' +
                'Non-radiative energy transfer when donor/acceptor are 1-10nm apart.<br><br>' +
                '<strong>Methods:</strong><br>• Sensitized emission<br>• Acceptor photobleaching<br>• FLIM-FRET (most quantitative)<br><br>' +
                '<strong>Pairs:</strong> CFP-YFP, GFP-mCherry, Alexa488-555<br><br>' +
                '<strong>Applications:</strong> Protein interactions, conformational changes, biosensors<br><br>' +
                '💡 <em>Use FLIM-FRET to avoid concentration artifacts.</em>';
        }
        
        // FLIM
        else if (msg.includes('flim')) {
            response = '<strong>FLIM (Fluorescence Lifetime Imaging)</strong><br><br>' +
                'Measures how long fluorophores stay excited (1-10ns).<br><br>' +
                '<strong>Why lifetime?</strong><br>• Independent of concentration<br>• Sensitive to environment (pH, ions)<br>• Distinguishes overlapping spectra<br>• Quantitative FRET<br><br>' +
                '<strong>Applications:</strong> FRET, metabolic imaging (NAD(P)H), biosensors<br><br>' +
                '💡 <em>NAD(P)H lifetime reports on metabolic state.</em>';
        }
        
        // FRAP
        else if (msg.includes('frap')) {
            response = '<strong>FRAP (Fluorescence Recovery After Photobleaching)</strong><br><br>' +
                'Measures molecular mobility by bleaching and watching recovery.<br><br>' +
                '<strong>Protocol:</strong><br>1. Image pre-bleach<br>2. Bleach ROI with high power<br>3. Image recovery<br>4. Fit curve<br><br>' +
                '<strong>Parameters:</strong> Mobile fraction, half-time, diffusion coefficient<br><br>' +
                '💡 <em>Include reference region to correct for acquisition bleaching.</em>';
        }
        
        // CALCIUM IMAGING
        else if (msg.includes('calcium') || msg.includes('gcamp')) {
            response = '<strong>Calcium Imaging</strong><br><br>' +
                '<strong>Genetic indicators:</strong><br>• GCaMP6/7/8 (green, most popular)<br>• jRGECO/jRCaMP (red)<br><br>' +
                '<strong>Chemical dyes:</strong><br>• Fura-2 (ratiometric)<br>• Fluo-4, Cal-520 (green)<br><br>' +
                '<strong>Imaging:</strong> Two-photon for deep tissue, widefield for speed<br><br>' +
                '💡 <em>GCaMP8 has faster kinetics for resolving individual spikes.</em>';
        }
        
        // IMAGEJ/FIJI
        else if (msg.includes('imagej') || msg.includes('fiji')) {
            response = '<strong>ImageJ / Fiji</strong><br><br>' +
                'Most widely used open-source image analysis software.<br><br>' +
                '<strong>Capabilities:</strong><br>• Measurements, segmentation<br>• Colocalization analysis<br>• 3D visualization<br>• Macro scripting<br><br>' +
                '<strong>Essential plugins:</strong><br>• Bio-Formats, TrackMate<br>• StarDist, Cellpose<br>• MorphoLibJ<br><br>' +
                '🔗 Download: <a href="https://fiji.sc" target="_blank">fiji.sc</a>';
        }
        
        // CELLPOSE
        else if (msg.includes('cellpose')) {
            response = '<strong>Cellpose</strong><br><br>' +
                'Deep learning cell segmentation - works great with minimal training!<br><br>' +
                '<strong>Features:</strong><br>• Pre-trained for cells/nuclei<br>• Works on diverse cell types<br>• GUI + Python + Fiji + Napari<br>• Custom training possible<br><br>' +
                '💡 <em>Cellpose 2.0 has improved models and human-in-the-loop training.</em><br><br>' +
                '🔗 <a href="https://www.cellpose.org" target="_blank">cellpose.org</a>';
        }
        
        // CELLPROFILER
        else if (msg.includes('cellprofiler')) {
            response = '<strong>CellProfiler</strong><br><br>' +
                'Free software for automated image analysis pipelines.<br><br>' +
                '<strong>Strengths:</strong><br>• No coding required<br>• Reproducible pipelines<br>• Hundreds of measurements<br>• High-content screening<br><br>' +
                '🔗 <a href="https://cellprofiler.org" target="_blank">cellprofiler.org</a>';
        }
        
        // NAPARI
        else if (msg.includes('napari')) {
            response = '<strong>Napari</strong><br><br>' +
                'Fast Python viewer for multi-dimensional images.<br><br>' +
                '<strong>Features:</strong><br>• GPU-accelerated<br>• Layer-based (images, labels, points)<br>• Great plugin ecosystem<br><br>' +
                '<strong>Install:</strong> <code>pip install napari[all]</code><br><br>' +
                '🔗 <a href="https://napari.org" target="_blank">napari.org</a>';
        }
        
        // SAMPLE PREP
        else if (msg.includes('sample prep') || msg.includes('fixation') || msg.includes('fix')) {
            response = '<strong>Sample Preparation</strong><br><br>' +
                '<strong>Fixation:</strong><br>• PFA (4%): Standard, good morphology<br>• Methanol: Good for cytoskeleton<br>• Glutaraldehyde: Best ultrastructure<br><br>' +
                '<strong>Permeabilization:</strong><br>• Triton X-100 (0.1-0.5%): Strong<br>• Saponin (0.1%): Gentle<br><br>' +
                '<strong>Mounting:</strong> ProLong Gold/Diamond, Vectashield<br><br>' +
                '💡 <em>Always use #1.5 coverslips (170μm) for high-NA objectives!</em>';
        }
        
        // FLUOROPHORES
        else if (msg.includes('fluorophore') || msg.includes('dye') || msg.includes('alexa')) {
            response = '<strong>Fluorophore Selection</strong><br><br>' +
                '<strong>By color:</strong><br>• Blue: DAPI, Hoechst (DNA)<br>• Green: Alexa 488, GFP, ATTO 488<br>• Orange: Alexa 555, Cy3, mOrange<br>• Red: Alexa 594/647, mCherry<br><br>' +
                '<strong>For super-resolution:</strong><br>• STED: ATTO 647N, Abberior STAR<br>• STORM: Alexa 647 + thiol buffer<br><br>' +
                '💡 <em>Alexa Fluor dyes are brighter and more photostable than Cy dyes.</em>';
        }
        
        // RESOLUTION
        else if (msg.includes('resolution') || msg.includes('diffraction')) {
            response = '<strong>Resolution in Microscopy</strong><br><br>' +
                '<strong>Diffraction limit:</strong> d = λ/(2×NA)<br>• ~200nm lateral, ~500nm axial<br><br>' +
                '<strong>Improve with:</strong><br>• Higher NA objective<br>• Shorter wavelength<br>• Deconvolution (~1.4x)<br>• Super-resolution<br><br>' +
                '<strong>Nyquist:</strong> Pixel size ≤ resolution/2.3<br><br>' +
                '<strong>Super-res comparison:</strong> Airyscan 140nm → SIM 100nm → STED 50nm → STORM 20nm';
        }
        
        // PROTOCOLS - MICROHUB FEATURE
        else if (msg.includes('protocol') && (msg.includes('find') || msg.includes('search') || msg.includes('where'))) {
            response = 'To find protocols in MicroHub:<br><br>' +
                '1. Use <strong>"Has Protocols"</strong> quick filter<br>' +
                '2. Check <strong>Recent Protocols</strong> sidebar<br>' +
                '3. On paper pages, see "📋 Protocols" section<br><br>' +
                'Sources: protocols.io, Bio-protocol, JoVE, Nature Protocols<br><br>' +
                'You can also <strong>upload your own protocol</strong> to share!';
        }
        else if (msg.includes('protocol')) {
            response = 'You can find protocols using the "Has Protocols" filter. Papers link to protocols.io, Bio-protocol, JoVE, and more. Check the Recent Protocols sidebar, or upload your own to share with the community!';
        }
        
        // GITHUB
        else if (msg.includes('github') || msg.includes('code')) {
            response = 'To find code repositories:<br><br>' +
                '1. Use <strong>"GitHub"</strong> quick filter<br>' +
                '2. Check <strong>GitHub Workflows</strong> sidebar<br>' +
                '3. On paper pages, see "💻 Code & Data" section<br><br>' +
                'Papers with code are marked with GitHub icon.';
        }
        
        // SEARCH/FILTER
        else if (msg.includes('search') || msg.includes('filter') || msg.includes('find paper')) {
            response = '<strong>MicroHub Search Tips</strong><br><br>' +
                '<strong>Filters:</strong> Technique, Microscope, Organism, Year, Citations<br><br>' +
                '<strong>Quick filters:</strong><br>' +
                '• 🏆 Foundational (100+ citations)<br>' +
                '• ⭐ High Impact (50+)<br>' +
                '• 📋 Has Protocols<br>' +
                '• 💻 Has GitHub<br>' +
                '• 💾 Has Data<br><br>' +
                'Combine filters to narrow results!';
        }
        
        // GREETINGS
        else if (msg.includes('hello') || msg.includes('hi') || msg === 'hi' || msg === 'hello' || msg === 'hey') {
            response = 'Hello! 👋 I\'m the MicroHub assistant.<br><br>' +
                'I can help with:<br>' +
                '• <strong>Techniques:</strong> confocal, STED, STORM, light sheet...<br>' +
                '• <strong>Software:</strong> ImageJ, Cellpose, CellProfiler...<br>' +
                '• <strong>Practical tips:</strong> sample prep, dyes, objectives...<br>' +
                '• <strong>Finding papers:</strong> with protocols or code<br><br>' +
                'What would you like to know?';
        }
        
        else if (msg.includes('thank')) {
            response = 'You\'re welcome! Let me know if you have more questions. 🔬';
        }
        
        else if (msg.includes('help') || msg.includes('what can you')) {
            response = '<strong>I can help with:</strong><br><br>' +
                '🔬 <strong>Techniques:</strong> Confocal, two-photon, STED, STORM, PALM, SIM, light sheet, TIRF, FRET, FLIM, FRAP, cryo-EM<br><br>' +
                '💻 <strong>Software:</strong> ImageJ/Fiji, CellProfiler, Cellpose, Napari, ilastik, QuPath<br><br>' +
                '🧪 <strong>Practical:</strong> Sample prep, fluorophores, objectives, resolution<br><br>' +
                '📚 <strong>Resources:</strong> Finding papers with protocols, GitHub code, data<br><br>' +
                'Just ask!';
        }
        
        // DEFAULT
        else {
            response = 'I can help with microscopy research! Try asking about:<br><br>' +
                '• <strong>Techniques:</strong> "How does confocal work?" or "Compare STED vs STORM"<br>' +
                '• <strong>Software:</strong> "What is Cellpose?" or "How to use ImageJ"<br>' +
                '• <strong>Tips:</strong> "Best dyes for STED" or "Sample preparation"<br>' +
                '• <strong>Resources:</strong> "Find papers with protocols"<br><br>' +
                'What would you like to know?';
        }
        
        return response;
    };

    /**
     * Format AI response (kept for compatibility)
     */
    MicroHub.formatAIResponse = function(text) {
        return text;
    };

    /**
     * Load sidebar widgets
     */
    MicroHub.loadSidebarWidgets = function() {
        this.loadGitHubRepos();
        this.loadDataRepos();
        this.loadRecentProtocols();
        this.loadFacilities();
    };

    /**
     * Load GitHub code repositories
     */
    MicroHub.loadGitHubRepos = function() {
        var self = this;
        console.log('Loading GitHub repos from:', this.apiBase + '/github-repos');
        $.get(this.apiBase + '/github-repos', function(repos) {
            console.log('GitHub repos response:', repos);
            var $list = $('#mh-github-workflows');
            if (repos && repos.length > 0) {
                var html = repos.slice(0, 8).map(function(repo) {
                    var shortTitle = repo.paper_title.length > 40 ? repo.paper_title.substring(0, 40) + '...' : repo.paper_title;
                    return '<li class="mh-repo-item">' +
                        '<a href="' + self.escapeHtml(repo.url) + '" target="_blank" class="repo-link" title="' + self.escapeHtml(repo.name) + '">' +
                        '<svg class="github-icon" viewBox="0 0 16 16" fill="currentColor"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"></path></svg>' +
                        self.escapeHtml(repo.name) + '</a>' +
                        '<span class="paper-ref">' + self.escapeHtml(shortTitle) + '</span>' +
                        '</li>';
                }).join('');
                $list.html(html);
                // Update stat
                $('#stat-github').text(repos.length + '+');
            } else {
                $list.html('<li class="mh-empty-item">No code repositories found</li>');
                $('#stat-github').text('0');
            }
        }).fail(function(xhr, status, error) {
            console.log('GitHub repos API error:', status, error);
            $('#mh-github-workflows').html('<li class="mh-empty-item">Loading code repos...</li>');
        });
    };

    /**
     * Load data repositories (Zenodo, Figshare, IDR, etc.)
     */
    MicroHub.loadDataRepos = function() {
        var self = this;
        console.log('Loading data repos from:', this.apiBase + '/data-repos');
        $.get(this.apiBase + '/data-repos', function(repos) {
            console.log('Data repos response:', repos);
            var $list = $('#mh-data-repos');
            if (repos && repos.length > 0) {
                var html = repos.slice(0, 8).map(function(repo) {
                    var iconClass = 'data-icon';
                    var repoType = repo.name.toLowerCase();
                    if (repoType.includes('zenodo')) iconClass = 'zenodo-icon';
                    else if (repoType.includes('figshare')) iconClass = 'figshare-icon';
                    else if (repoType.includes('empiar')) iconClass = 'empiar-icon';
                    else if (repoType.includes('mendeley')) iconClass = 'mendeley-icon';
                    else if (repoType.includes('osf') || repoType.includes('open science')) iconClass = 'osf-icon';
                    else if (repoType.includes('gitlab')) iconClass = 'gitlab-icon';
                    else if (repoType.includes('idr')) iconClass = 'idr-icon';
                    else if (repoType.includes('dryad')) iconClass = 'dryad-icon';
                    
                    var label = repo.accession_id ? repo.name + ': ' + repo.accession_id : repo.name;
                    var shortTitle = repo.paper_title.length > 35 ? repo.paper_title.substring(0, 35) + '...' : repo.paper_title;
                    
                    return '<li class="mh-data-repo-item">' +
                        '<a href="' + self.escapeHtml(repo.url) + '" target="_blank" class="repo-link ' + iconClass + '" title="' + self.escapeHtml(repo.url) + '">' +
                        '<span class="repo-icon"></span>' +
                        self.escapeHtml(label) + '</a>' +
                        '<span class="paper-ref">' + self.escapeHtml(shortTitle) + '</span>' +
                        '</li>';
                }).join('');
                $list.html(html);
                // Update stat
                $('#stat-repos').text(repos.length + '+');
            } else {
                $list.html('<li class="mh-empty-item">No data repositories found</li>');
                $('#stat-repos').text('0');
            }
        }).fail(function(xhr, status, error) {
            console.log('Data repos API error:', status, error);
            $('#mh-data-repos').html('<li class="mh-empty-item">Loading data repos...</li>');
        });
    };

    /**
     * Load recent protocols (from both uploaded protocols and paper-linked protocols)
     */
    MicroHub.loadRecentProtocols = function() {
        var self = this;
        console.log('Loading protocols from:', this.apiBase + '/protocols');
        $.get(this.apiBase + '/protocols', { per_page: 10 }, function(protocols) {
            console.log('Protocols response:', protocols);
            var $list = $('#mh-recent-protocols');
            if (protocols && protocols.length > 0) {
                var html = protocols.map(function(p) {
                    var shortTitle = p.title.length > 40 ? p.title.substring(0, 40) + '...' : p.title;
                    // Use protocol_url for external protocols, permalink for uploaded ones
                    var linkUrl = p.protocol_url || p.permalink;
                    var isExternal = p.protocol_url ? ' target="_blank"' : '';
                    
                    return '<li class="mh-protocol-item">' +
                        '<a href="' + self.escapeHtml(linkUrl) + '" class="protocol-link"' + isExternal + '>' + 
                        '<span class="protocol-icon"></span>' +
                        self.escapeHtml(shortTitle) + '</a>' +
                        '<span class="source">' + self.escapeHtml(p.source) + '</span>' +
                        '</li>';
                }).join('');
                $list.html(html);
                // Update stat
                $('#stat-protocols').text(protocols.length + '+');
            } else {
                $list.html('<li class="mh-empty-item">No protocols found</li>');
            }
        }).fail(function(xhr, status, error) {
            console.log('Protocols API error:', status, error);
            $('#mh-recent-protocols').html('<li class="mh-empty-item">Loading protocols...</li>');
        });
    };

    /**
     * Load facilities
     */
    MicroHub.loadFacilities = function() {
        var self = this;
        console.log('Loading facilities from:', this.apiBase + '/facilities');
        $.get(this.apiBase + '/facilities', function(facilities) {
            console.log('Facilities response:', facilities);
            var $list = $('#mh-facilities');
            if (facilities && facilities.length > 0) {
                var html = facilities.slice(0, 8).map(function(f) {
                    var searchUrl = f.search_url || ('?s=' + encodeURIComponent(f.name));
                    return '<li class="mh-facility-item">' +
                        '<a href="' + self.escapeHtml(searchUrl) + '" class="facility-link">' +
                        self.escapeHtml(f.name) + '</a>' +
                        (f.paper_count ? '<span class="count">(' + f.paper_count + ' papers)</span>' : '') +
                        '</li>';
                }).join('');
                $list.html(html);
                // Update stat
                $('#stat-facilities').text(facilities.length + '+');
            } else {
                $list.html('<li class="mh-empty-item">No facilities listed yet</li>');
                $('#stat-facilities').text('0');
            }
        }).fail(function(xhr, status, error) {
            console.log('Facilities API error:', status, error, xhr.responseText);
            $('#mh-facilities').html('<li class="mh-empty-item">Loading facilities...</li>');
        });
    };

    /**
     * Load filter options from API (supplements hardcoded options)
     * Only adds options that aren't already in the dropdown
     */
    MicroHub.loadFilterOptions = function() {
        // Filter options are now hardcoded in the HTML for consistency
        // This function can be used to add paper counts to options if needed
        
        // Optional: Update option counts from API
        var self = this;
        
        // Get actual term counts from database
        $.get(this.apiBase + '/taxonomies/mh_technique', function(terms) {
            if (terms && terms.length) {
                var counts = {};
                terms.forEach(function(term) {
                    counts[term.slug] = term.count || 0;
                });
                
                // Update existing options with counts
                $('#mh-filter-technique option').each(function() {
                    var slug = $(this).val();
                    if (slug && counts[slug]) {
                        var text = $(this).text().replace(/\s*\(\d+\)$/, '');
                        $(this).text(text + ' (' + counts[slug] + ')');
                    }
                });
            }
        }).fail(function() {
            // API not available, use hardcoded options as-is
        });
        
        $.get(this.apiBase + '/taxonomies/mh_microscope', function(terms) {
            if (terms && terms.length) {
                var counts = {};
                terms.forEach(function(term) {
                    counts[term.slug] = term.count || 0;
                });
                
                $('#mh-filter-microscope option').each(function() {
                    var slug = $(this).val();
                    if (slug && counts[slug]) {
                        var text = $(this).text().replace(/\s*\(\d+\)$/, '');
                        $(this).text(text + ' (' + counts[slug] + ')');
                    }
                });
            }
        }).fail(function() {});
        
        $.get(this.apiBase + '/taxonomies/mh_organism', function(terms) {
            if (terms && terms.length) {
                var counts = {};
                terms.forEach(function(term) {
                    counts[term.slug] = term.count || 0;
                });
                
                $('#mh-filter-organism option').each(function() {
                    var slug = $(this).val();
                    if (slug && counts[slug]) {
                        var text = $(this).text().replace(/\s*\(\d+\)$/, '');
                        $(this).text(text + ' (' + counts[slug] + ')');
                    }
                });
            }
        }).fail(function() {});
        
        // Load software counts
        $.get(this.apiBase + '/taxonomies/mh_software', function(terms) {
            if (terms && terms.length) {
                var counts = {};
                terms.forEach(function(term) {
                    counts[term.slug] = term.count || 0;
                });
                
                $('#mh-filter-software option').each(function() {
                    var slug = $(this).val();
                    if (slug && counts[slug]) {
                        var text = $(this).text().replace(/\s*\(\d+\)$/, '');
                        $(this).text(text + ' (' + counts[slug] + ')');
                    }
                });
            }
        }).fail(function() {});
    };

    /**
     * Load enrichment counts
     */
    MicroHub.loadEnrichmentCounts = function() {
        var self = this;
        
        $.get(this.apiBase + '/enrichment-stats', function(stats) {
            console.log('Enrichment stats:', stats);
            var protocols = stats.papers_with_protocols || 0;
            var repos = stats.papers_with_repositories || 0;
            var github = stats.papers_with_github || 0;
            var facilities = stats.papers_with_facilities || 0;
            
            $('#count-protocols').text(self.formatNumber(protocols));
            $('#count-repos').text(self.formatNumber(repos));
            $('#count-github').text(self.formatNumber(github));
            
            $('#stat-protocols').text(self.formatNumber(protocols));
            $('#stat-repos').text(self.formatNumber(repos));
            $('#stat-github').text(self.formatNumber(github));
            $('#stat-facilities').text(self.formatNumber(facilities));
        }).fail(function(xhr, status, error) {
            console.log('Enrichment stats error:', status, error);
        });
    };

    /**
     * Search papers
     */
    MicroHub.searchPapers = function() {
        if (this.isLoading) return;
        
        var self = this;
        this.isLoading = true;

        var $grid = $('#mh-papers-grid');
        $grid.html('<div class="mh-loading"><div class="mh-spinner"></div><p>Loading papers...</p></div>');

        var params = {
            page: this.currentPage,
            per_page: this.perPage
        };

        var searchQuery = $('#mh-search-input').val();
        if (searchQuery && searchQuery.trim()) {
            params.search = searchQuery.trim();
        }

        if (this.activeFilters.technique) params.technique = this.activeFilters.technique;
        if (this.activeFilters.microscope) params.microscope = this.activeFilters.microscope;
        if (this.activeFilters.organism) params.organism = this.activeFilters.organism;
        if (this.activeFilters.software) params.software = this.activeFilters.software;

        var yearFilter = this.activeFilters.year;
        if (yearFilter) {
            if (yearFilter === '2024-2025') params.year_min = 2024;
            else if (yearFilter === '2020-2023') { params.year_min = 2020; params.year_max = 2023; }
            else if (yearFilter === '2015-2019') { params.year_min = 2015; params.year_max = 2019; }
            else if (yearFilter === '2010-2014') { params.year_min = 2010; params.year_max = 2014; }
            else if (yearFilter === 'before-2010') params.year_max = 2009;
        }

        if (this.activeFilters.citations) params.citations_min = parseInt(this.activeFilters.citations);
        if (this.activeFilters.foundational) params.citations_min = 100;
        if (this.activeFilters.high_impact) params.citations_min = 50;
        if (this.activeFilters.has_protocols) params.has_protocols = true;
        if (this.activeFilters.has_github) params.has_github = true;
        if (this.activeFilters.has_repositories) params.has_repositories = true;

        $.ajax({
            url: this.apiBase + '/papers',
            method: 'GET',
            data: params,
            success: function(response) {
                self.renderPapers(response.papers || []);
                self.renderPagination(response.total || 0, response.pages || 1);
                self.updateResultsCount((response.papers || []).length, response.total || 0);
                self.isLoading = false;
            },
            error: function() {
                $grid.html('<div class="mh-no-results"><h3>Error loading papers</h3><p>Please try again.</p></div>');
                self.isLoading = false;
            }
        });
    };

    /**
     * Render papers
     */
    MicroHub.renderPapers = function(papers) {
        var $grid = $('#mh-papers-grid');

        if (!papers || papers.length === 0) {
            $grid.html('<div class="mh-no-results"><h3>No papers found</h3><p>Try adjusting your search or filters.</p></div>');
            return;
        }

        var self = this;
        var html = papers.map(function(paper) {
            return self.createPaperCard(paper);
        }).join('');

        $grid.html(html);
    };

    /**
     * Create paper card HTML
     */
    MicroHub.createPaperCard = function(paper) {
        var citations = parseInt(paper.citations) || 0;
        
        var badgeClass = 'standard';
        var badgeText = this.formatNumber(citations) + ' citations';
        if (citations >= 100) { badgeClass = 'foundational'; badgeText = '🏆 Foundational'; }
        else if (citations >= 50) { badgeClass = 'high-impact'; badgeText = '⭐ High Impact'; }

        var tagsHtml = '';
        if (paper.techniques && paper.techniques.length > 0) {
            tagsHtml = paper.techniques.slice(0, 2).map(function(t) {
                return '<span class="mh-card-tag technique">' + MicroHub.escapeHtml(t) + '</span>';
            }).join('');
        }
        if (paper.microscopes && paper.microscopes.length > 0) {
            tagsHtml += '<span class="mh-card-tag microscope">🔬 ' + this.escapeHtml(paper.microscopes[0]) + '</span>';
        }
        if (paper.software && paper.software.length > 0) {
            tagsHtml += paper.software.slice(0, 2).map(function(s) {
                return '<span class="mh-card-tag software">💻 ' + MicroHub.escapeHtml(s) + '</span>';
            }).join('');
        }

        var enrichmentHtml = '';
        var items = [];
        if (paper.protocols && paper.protocols.length) items.push('<span class="mh-enrichment-item protocols">📋 ' + paper.protocols.length + '</span>');
        if (paper.github_url) items.push('<span class="mh-enrichment-item github">💻 GitHub</span>');
        if (paper.repositories && paper.repositories.length) items.push('<span class="mh-enrichment-item repositories">💾 Data</span>');
        if (paper.facility) items.push('<span class="mh-enrichment-item facility">🏛️ Facility</span>');
        if (items.length) enrichmentHtml = '<div class="mh-card-enrichment">' + items.join('') + '</div>';

        var linksHtml = '';
        if (paper.doi) linksHtml += '<a href="https://doi.org/' + this.escapeHtml(paper.doi) + '" class="mh-card-link doi" target="_blank">DOI</a>';
        if (paper.pubmed_id) linksHtml += '<a href="https://pubmed.ncbi.nlm.nih.gov/' + this.escapeHtml(paper.pubmed_id) + '/" class="mh-card-link pubmed" target="_blank">PubMed</a>';
        if (paper.github_url) linksHtml += '<a href="' + this.escapeHtml(paper.github_url) + '" class="mh-card-link github" target="_blank">GitHub</a>';

        var abstract = paper.abstract ? paper.abstract.substring(0, 150) + '...' : '';
        var authors = paper.authors ? paper.authors.substring(0, 60) + (paper.authors.length > 60 ? '...' : '') : '';
        var commentsCount = paper.comments_count || 0;
        
        // Paper thumbnail
        var thumbnailHtml = '';
        if (paper.thumbnail_url) {
            thumbnailHtml = '<div class="mh-card-thumbnail">' +
                '<img src="' + this.escapeHtml(paper.thumbnail_url) + '" alt="" loading="lazy" onerror="this.parentElement.style.display=\'none\'">' +
                '</div>';
        }

        return '<article class="mh-paper-card' + (paper.thumbnail_url ? ' has-thumbnail' : '') + '">' +
            thumbnailHtml +
            '<div class="mh-card-content">' +
            '<div class="mh-card-top">' +
                '<span class="mh-card-badge ' + badgeClass + '">' + badgeText + '</span>' +
                '<span class="mh-card-citations"><strong>' + this.formatNumber(citations) + '</strong> citations</span>' +
            '</div>' +
            '<h3 class="mh-card-title"><a href="' + this.escapeHtml(paper.permalink) + '">' + this.escapeHtml(paper.title) + '</a></h3>' +
            '<div class="mh-card-meta">' +
                (authors ? '<div class="mh-card-authors">' + this.escapeHtml(authors) + '</div>' : '') +
                '<div class="mh-card-publication">' +
                    (paper.journal ? '<span>' + this.escapeHtml(paper.journal) + '</span>' : '') +
                    (paper.year ? '<span>' + paper.year + '</span>' : '') +
                '</div>' +
            '</div>' +
            (abstract ? '<p class="mh-card-abstract">' + this.escapeHtml(abstract) + '</p>' : '') +
            (tagsHtml ? '<div class="mh-card-tags">' + tagsHtml + '</div>' : '') +
            enrichmentHtml +
            '<div class="mh-card-footer">' +
                '<div class="mh-card-links">' + linksHtml + '</div>' +
                '<div class="mh-card-actions">' +
                    '<span class="mh-card-action">💬 ' + commentsCount + '</span>' +
                    '<span class="mh-card-action mh-ai-discuss" data-title="' + this.escapeHtml(paper.title) + '">🤖 Ask AI</span>' +
                '</div>' +
            '</div>' +
            '</div>' +
        '</article>';
    };

    /**
     * Render pagination
     */
    MicroHub.renderPagination = function(total, totalPages) {
        var $pagination = $('#mh-pagination');
        if (totalPages <= 1) { $pagination.html(''); return; }

        var html = '';
        var current = this.currentPage;

        html += '<button data-page="' + (current - 1) + '" ' + (current === 1 ? 'disabled' : '') + '>← Prev</button>';

        var pages = [];
        if (totalPages <= 7) {
            for (var i = 1; i <= totalPages; i++) pages.push(i);
        } else {
            if (current <= 4) pages = [1, 2, 3, 4, 5, '...', totalPages];
            else if (current >= totalPages - 3) pages = [1, '...', totalPages - 4, totalPages - 3, totalPages - 2, totalPages - 1, totalPages];
            else pages = [1, '...', current - 1, current, current + 1, '...', totalPages];
        }

        pages.forEach(function(page) {
            if (page === '...') html += '<span style="padding: 8px; color: #8b949e;">...</span>';
            else html += '<button data-page="' + page + '" class="' + (page === current ? 'active' : '') + '">' + page + '</button>';
        });

        html += '<button data-page="' + (current + 1) + '" ' + (current === totalPages ? 'disabled' : '') + '>Next →</button>';

        $pagination.html(html);
    };

    MicroHub.updateResultsCount = function(showing, total) {
        $('#mh-showing').text(showing);
        $('#mh-total').text(this.formatNumber(total));
    };

    MicroHub.clearAllFilters = function() {
        $('#mh-search-input').val('');
        $('[data-filter]').val('');
        $('.mh-quick-btn').removeClass('active');
        this.activeFilters = {};
        this.currentPage = 1;
        this.searchPapers();
    };

    MicroHub.formatNumber = function(num) {
        if (!num) return '0';
        num = parseInt(num);
        if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
        if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
        return num.toLocaleString();
    };

    MicroHub.escapeHtml = function(text) {
        if (!text) return '';
        var div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    };

    // Initialize
    $(document).ready(function() {
        if ($('.microhub-wrapper').length || $('#mh-papers-grid').length) {
            MicroHub.init();
        }
    });

    window.MicroHub = MicroHub;

})(jQuery);
