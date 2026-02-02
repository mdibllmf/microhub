/**
 * MicroHub Admin Scripts
 */

(function($) {
    'use strict';
    
    $(document).ready(function() {
        // Handle import form submission
        $('#microhub-import-form').on('submit', function() {
            // Show progress indicator
            $('.microhub-import-progress').show();
        });
    });
    
})(jQuery);
