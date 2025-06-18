// Collapsible header logic for CodeForge
// This script collapses the header to one line when scrolling down, and expands when scrolling up or at the top.
// Collapse/expand can only happen at most once per second.

document.addEventListener('DOMContentLoaded', function () {
    const header = document.querySelector('.site-header');
    const headerContent = document.querySelector('.header-content');
    let lastScrollY = window.scrollY;
    let collapsed = false;
    let lastToggle = 0;
    const COLLAPSE_CLASS = 'collapsed';
    const THROTTLE_MS = 1000;

    function setCollapsed(state) {
        if (collapsed === state) return;
        const now = Date.now();
        if (now - lastToggle < THROTTLE_MS) return;
        collapsed = state;
        lastToggle = now;
        if (collapsed) {
            header.classList.add(COLLAPSE_CLASS);
        } else {
            header.classList.remove(COLLAPSE_CLASS);
        }
    }

    window.addEventListener('scroll', function () {
        const currentY = window.scrollY;
        if (currentY > 60) {
            setCollapsed(true);
        } else {
            setCollapsed(false);
        }
        lastScrollY = currentY;
    });
});
