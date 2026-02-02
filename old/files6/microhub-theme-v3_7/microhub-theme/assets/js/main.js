/**
 * MicroHub Theme JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    // Mobile menu toggle
    const menuToggle = document.querySelector('.mh-nav-toggle');
    const navMenu = document.querySelector('.mh-nav-menu');
    
    if (menuToggle && navMenu) {
        menuToggle.addEventListener('click', function() {
            navMenu.classList.toggle('active');
            menuToggle.textContent = navMenu.classList.contains('active') ? '✕' : '☰';
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', function(e) {
            if (!menuToggle.contains(e.target) && !navMenu.contains(e.target)) {
                navMenu.classList.remove('active');
                menuToggle.textContent = '☰';
            }
        });
    }
    
    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                e.preventDefault();
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });
    
    // Card hover effects
    document.querySelectorAll('.mh-card').forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-4px)';
        });
        card.addEventListener('mouseleave', function() {
            this.style.transform = '';
        });
    });
    
    // Full text highlight toggle
    const highlightToggle = document.getElementById('mh-toggle-highlights');
    const fullTextContent = document.getElementById('mh-full-text-content');
    
    if (highlightToggle && fullTextContent) {
        highlightToggle.addEventListener('click', function() {
            fullTextContent.classList.toggle('hide-highlights');
            const highlightOn = this.querySelector('.highlight-on');
            const highlightOff = this.querySelector('.highlight-off');
            
            if (fullTextContent.classList.contains('hide-highlights')) {
                highlightOn.style.display = 'none';
                highlightOff.style.display = 'inline';
            } else {
                highlightOn.style.display = 'inline';
                highlightOff.style.display = 'none';
            }
        });
    }
    
    // Expand/collapse all sections
    const expandAllToggle = document.getElementById('mh-expand-all-sections');
    
    if (expandAllToggle) {
        expandAllToggle.addEventListener('click', function() {
            const sections = document.querySelectorAll('.mh-section-block');
            const expandAll = this.querySelector('.expand-all');
            const collapseAll = this.querySelector('.collapse-all');
            
            const allExpanded = Array.from(sections).every(s => s.classList.contains('mh-section-expanded'));
            
            sections.forEach(section => {
                if (allExpanded) {
                    section.classList.remove('mh-section-expanded');
                    section.classList.add('mh-section-collapsed');
                } else {
                    section.classList.remove('mh-section-collapsed');
                    section.classList.add('mh-section-expanded');
                }
            });
            
            if (allExpanded) {
                expandAll.style.display = 'inline';
                collapseAll.style.display = 'none';
            } else {
                expandAll.style.display = 'none';
                collapseAll.style.display = 'inline';
            }
        });
    }
    
    // Highlight reference when jumping to it
    document.querySelectorAll('.mh-ref-link').forEach(link => {
        link.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href');
            if (targetId && targetId.startsWith('#ref-')) {
                const target = document.querySelector(targetId);
                if (target) {
                    // Add flash animation
                    target.classList.add('mh-ref-flash');
                    setTimeout(() => {
                        target.classList.remove('mh-ref-flash');
                    }, 2000);
                }
            }
        });
    });
});

// Global MicroHub object for section toggling
window.MicroHub = window.MicroHub || {};

MicroHub.toggleSection = function(header) {
    const block = header.closest('.mh-section-block');
    if (block) {
        block.classList.toggle('mh-section-collapsed');
        block.classList.toggle('mh-section-expanded');
    }
};
