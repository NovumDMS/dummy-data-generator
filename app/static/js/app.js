/**
 * Main Application Script
 * Initialize and manage the frontend application
 */

document.addEventListener('DOMContentLoaded', () => {
    // Update navigation based on authentication status
    updateNavigation();
});

/**
 * Update navigation menu based on authentication
 */
function updateNavigation() {
    const token = localStorage.getItem('access_token');
    const navLinks = document.querySelector('.nav-links');
    
    if (!navLinks) return;
    
    if (token) {
        // User is logged in - show logout option
        navLinks.innerHTML = `
            <li><a href="/">Home</a></li>
            <li><a href="#" id="logoutBtn">Logout</a></li>
        `;
        
        document.getElementById('logoutBtn').addEventListener('click', (e) => {
            e.preventDefault();
            API.logout();
            window.location.href = '/';
        });
    } else {
        // User is not logged in
        navLinks.innerHTML = `
            <li><a href="/">Home</a></li>
            <li><a href="/login">Login</a></li>
            <li><a href="/register">Register</a></li>
        `;
    }
}

/**
 * Check if user is authenticated
 */
function isAuthenticated() {
    return localStorage.getItem('access_token') !== null;
}

/**
 * Redirect to login if not authenticated
 */
function requireAuth() {
    if (!isAuthenticated()) {
        window.location.href = '/login';
    }
}
