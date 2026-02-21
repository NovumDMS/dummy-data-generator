/**
 * API Client
 * Handles all communication with the FastAPI backend
 */

const API = {
    BASE_URL: 'http://localhost:8000/api',
    
    /**
     * Register a new user
     */
    async register(username, email, password) {
        const response = await fetch(`${this.BASE_URL}/auth/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                username,
                email,
                password
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Registration failed');
        }
        
        return await response.json();
    },
    
    /**
     * Log in a user
     */
    async login(username, password) {
        const response = await fetch(`${this.BASE_URL}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                username,
                password
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Login failed');
        }
        
        return await response.json();
    },
    
    /**
     * Get current user info
     */
    async getCurrentUser() {
        const token = localStorage.getItem('access_token');
        
        if (!token) {
            throw new Error('Not authenticated');
        }
        
        const response = await fetch(`${this.BASE_URL}/auth/me`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to get user info');
        }
        
        return await response.json();
    },
    
    /**
     * Log out user
     */
    logout() {
        localStorage.removeItem('access_token');
    },
    
    /**
     * Get authorization headers
     */
    getAuthHeaders() {
        const token = localStorage.getItem('access_token');
        
        const headers = {
            'Content-Type': 'application/json',
        };
        
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        
        return headers;
    }
};
