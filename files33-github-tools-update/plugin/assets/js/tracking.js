/**
 * MicroHub Visitor Tracking
 *
 * Tracks: page views, time on page, tag/filter clicks, link clicks, searches.
 * Privacy-friendly: no personal data collected, session-based only.
 */
(function($) {
    'use strict';

    if (typeof mhTracking === 'undefined') return;

    var T = {
        ajaxurl: mhTracking.ajaxurl,
        nonce: mhTracking.nonce,
        sessionId: mhTracking.sessionId,
        postId: mhTracking.postId || 0,
        postType: mhTracking.postType || '',
        startTime: Date.now(),
        heartbeatInterval: null,
        pageUrl: window.location.pathname + window.location.search
    };

    /**
     * Send a tracking event
     */
    T.trackEvent = function(eventType, eventTarget, eventValue) {
        $.post(T.ajaxurl, {
            action: 'mh_track_event',
            nonce: T.nonce,
            session_id: T.sessionId,
            event_type: eventType,
            event_target: eventTarget || '',
            event_value: eventValue || '',
            post_id: T.postId
        });
    };

    /**
     * Send duration update
     */
    T.updateDuration = function() {
        var duration = Math.round((Date.now() - T.startTime) / 1000);
        if (duration < 1 || duration > 1800) return;

        // Use sendBeacon for reliability on page unload
        if (navigator.sendBeacon) {
            var data = new FormData();
            data.append('action', 'mh_track_duration');
            data.append('nonce', T.nonce);
            data.append('session_id', T.sessionId);
            data.append('duration', duration);
            data.append('page_url', T.pageUrl);
            navigator.sendBeacon(T.ajaxurl, data);
        } else {
            $.post(T.ajaxurl, {
                action: 'mh_track_duration',
                nonce: T.nonce,
                session_id: T.sessionId,
                duration: duration,
                page_url: T.pageUrl
            });
        }
    };

    /**
     * Track tag/taxonomy clicks
     */
    T.bindTagClicks = function() {
        // Taxonomy term links (tags in paper cards, filter tags, etc.)
        $(document).on('click', [
            'a[href*="/mh_technique/"]',
            'a[href*="/mh_microscope/"]',
            'a[href*="/mh_organism/"]',
            'a[href*="/mh_software/"]',
            'a[href*="/mh_fluorophore/"]',
            'a[href*="/mh_cell_line/"]',
            'a[href*="/mh_sample_prep/"]',
            'a[href*="/mh_facility/"]',
            '.mh-tag',
            '.mh-taxonomy-tag',
            '.mh-technique-tag',
            '.mh-microscope-tag',
            '.mh-organism-tag',
            '.mh-filter-tag',
            '.tag-link'
        ].join(', '), function() {
            var tagText = $(this).text().trim();
            var href = $(this).attr('href') || '';
            T.trackEvent('tag_click', href, tagText);
        });
    };

    /**
     * Track link clicks (internal and outbound)
     */
    T.bindLinkClicks = function() {
        $(document).on('click', 'a[href]', function() {
            var href = $(this).attr('href');
            if (!href || href === '#' || href.indexOf('javascript:') === 0) return;

            var linkText = $(this).text().trim().substring(0, 100);
            var currentHost = window.location.hostname;

            try {
                var url = new URL(href, window.location.origin);
                if (url.hostname !== currentHost) {
                    // Outbound link
                    T.trackEvent('outbound_link', href, linkText);
                } else {
                    // Internal link (skip tracking ajax/api calls)
                    if (href.indexOf('admin-ajax') === -1 && href.indexOf('wp-json') === -1) {
                        T.trackEvent('link_click', href, linkText);
                    }
                }
            } catch(e) {
                // Relative URL - internal link
                if (href.indexOf('admin-ajax') === -1) {
                    T.trackEvent('link_click', href, linkText);
                }
            }
        });
    };

    /**
     * Track search queries
     */
    T.bindSearchTracking = function() {
        var searchTimer = null;
        $(document).on('input', '#mh-search-input, .mh-search-input, input[name="s"]', function() {
            var val = $(this).val().trim();
            if (val.length < 3) return;

            clearTimeout(searchTimer);
            searchTimer = setTimeout(function() {
                T.trackEvent('search', '', val);
            }, 2000); // Only track after 2s pause
        });
    };

    /**
     * Track filter changes
     */
    T.bindFilterTracking = function() {
        $(document).on('change', '[data-filter], .mh-filter-select, select[name^="mh_"]', function() {
            var filterName = $(this).data('filter') || $(this).attr('name') || 'unknown';
            var filterValue = $(this).find('option:selected').text().trim() || $(this).val();
            if (filterValue) {
                T.trackEvent('filter_change', filterName, filterValue);
            }
        });

        // Quick filter buttons
        $(document).on('click', '.mh-quick-btn', function() {
            var filterName = $(this).data('filter') || 'quick_filter';
            var filterValue = $(this).text().trim();
            T.trackEvent('filter_change', filterName, filterValue);
        });
    };

    /**
     * Heartbeat - update duration every 30 seconds
     */
    T.startHeartbeat = function() {
        T.heartbeatInterval = setInterval(function() {
            T.updateDuration();
        }, 30000);
    };

    /**
     * Track page visibility changes
     */
    T.bindVisibility = function() {
        document.addEventListener('visibilitychange', function() {
            if (document.visibilityState === 'hidden') {
                T.updateDuration();
            }
        });

        // Also update on page unload
        window.addEventListener('beforeunload', function() {
            T.updateDuration();
        });
    };

    /**
     * Initialize all tracking
     */
    T.init = function() {
        T.bindTagClicks();
        T.bindLinkClicks();
        T.bindSearchTracking();
        T.bindFilterTracking();
        T.startHeartbeat();
        T.bindVisibility();
    };

    // Initialize when DOM is ready
    $(document).ready(function() {
        // Small delay to not interfere with page load
        setTimeout(T.init, 500);
    });

})(jQuery);
