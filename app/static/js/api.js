/**
 * API Client
 * Handles all communication with the FastAPI backend
 */

const API = {
    BASE_URL: '/api',
    /**
     * Register a new user
     */
    async registerUser(username, email, password) {
        const response = await fetch(`${this.BASE_URL}/auth/register`, {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                username,
                email,
                password
            })
        });

        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || 'Registration failed');
        }
        
        return data.message || 'Registration successful';
    },
    
    /**
     * Log in a user
     */
    async login(username, password) {
        const response = await fetch(`${this.BASE_URL}/auth/login`, {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                username,
                password
            })
        });
        
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail);
        }

        window.location.href = '/dashboard';
    },
    
    /**
     * Get current user info
     */
    async getCurrentUser() {
        const response = await fetch(`${this.BASE_URL}/auth/me`, {
            method: 'GET',
            credentials: 'include'
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
        window.location.href = '/api/auth/logout';
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
    },

    /**
     * 
     */
    async getClients() {
        const response = await fetch(`${this.BASE_URL}/clients`, {
            method: 'GET',
            credentials: 'include',
            headers: this.getAuthHeaders(),
        });
        
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail);
        }

        return data;
    },

    async registerClient(id, name, email, db_url) {
        const response = await fetch(`${this.BASE_URL}/clients/register`, {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                id,
                name,
                email,
                db_url
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail);
        }

        return data;

    }
};
