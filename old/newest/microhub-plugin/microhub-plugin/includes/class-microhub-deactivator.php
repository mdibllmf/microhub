<?php
/**
 * Plugin deactivation handler
 */

class MicroHub_Deactivator {
    
    public static function deactivate() {
        // Flush rewrite rules
        flush_rewrite_rules();
        
        // Note: We don't delete data on deactivation
        // Data is only deleted if user explicitly uninstalls the plugin
    }
}
