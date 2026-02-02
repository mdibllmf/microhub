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
    
    // Full text expand/collapse toggle
    const expandToggle = document.getElementById('mh-expand-text');
    
    if (expandToggle && fullTextContent) {
        expandToggle.addEventListener('click', function() {
            fullTextContent.classList.toggle('expanded');
            const expandText = this.querySelector('.expand-text');
            const collapseText = this.querySelector('.collapse-text');
            
            if (fullTextContent.classList.contains('expanded')) {
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
