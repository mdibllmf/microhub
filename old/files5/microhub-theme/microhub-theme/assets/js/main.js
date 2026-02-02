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
    
    // Section box toggle (click header to expand/collapse)
    document.querySelectorAll('.mh-text-section-header').forEach(header => {
        header.addEventListener('click', function() {
            const section = this.closest('.mh-text-section');
            if (section) {
                section.classList.toggle('collapsed');
            }
        });
    });
    
    // Full text highlight toggle
    const highlightToggle = document.getElementById('mh-toggle-highlights');
    const sectionsWrapper = document.getElementById('mh-full-text-content');
    
    if (highlightToggle && sectionsWrapper) {
        highlightToggle.addEventListener('click', function() {
            sectionsWrapper.classList.toggle('hide-highlights');
            const highlightOn = this.querySelector('.highlight-on');
            const highlightOff = this.querySelector('.highlight-off');
            
            if (sectionsWrapper.classList.contains('hide-highlights')) {
                highlightOn.style.display = 'none';
                highlightOff.style.display = 'inline';
            } else {
                highlightOn.style.display = 'inline';
                highlightOff.style.display = 'none';
            }
        });
    }
    
    // Expand/Collapse all sections
    const expandAllToggle = document.getElementById('mh-expand-all');
    
    if (expandAllToggle) {
        expandAllToggle.addEventListener('click', function() {
            const sections = document.querySelectorAll('.mh-text-section');
            const expandText = this.querySelector('.expand-text');
            const collapseText = this.querySelector('.collapse-text');
            
            // Check if most sections are collapsed
            const collapsedCount = document.querySelectorAll('.mh-text-section.collapsed').length;
            const shouldExpand = collapsedCount > sections.length / 2;
            
            sections.forEach(section => {
                if (shouldExpand) {
                    section.classList.remove('collapsed');
                } else {
                    section.classList.add('collapsed');
                }
            });
            
            if (shouldExpand) {
                expandText.style.display = 'none';
                collapseText.style.display = 'inline';
            } else {
                expandText.style.display = 'inline';
                collapseText.style.display = 'none';
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
                    target.classList.add('mh-ref-flash');
                    setTimeout(() => {
                        target.classList.remove('mh-ref-flash');
                    }, 2000);
                }
            }
        });
    });
});
