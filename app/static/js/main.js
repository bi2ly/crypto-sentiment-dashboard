/**
 * Crypto Sentiment Dashboard - Main JavaScript
 */

// ==========================================================================
// Theme Management
// ==========================================================================
const ThemeManager = {
    STORAGE_KEY: 'crypto-dashboard-theme',

    init() {
        // Load saved theme or detect system preference
        const savedTheme = localStorage.getItem(this.STORAGE_KEY);
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        const theme = savedTheme || (prefersDark ? 'dark' : 'light');

        this.setTheme(theme);
        this.bindEvents();
    },

    setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem(this.STORAGE_KEY, theme);
    },

    toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        this.setTheme(newTheme);
    },

    bindEvents() {
        const themeToggle = document.getElementById('themeToggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => this.toggleTheme());
        }

        // Listen for system theme changes
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            if (!localStorage.getItem(this.STORAGE_KEY)) {
                this.setTheme(e.matches ? 'dark' : 'light');
            }
        });
    }
};

// ==========================================================================
// Mobile Navigation
// ==========================================================================
const MobileNav = {
    init() {
        const toggle = document.getElementById('mobileMenuToggle');
        const nav = document.getElementById('mobileNav');

        if (toggle && nav) {
            toggle.addEventListener('click', () => {
                nav.classList.toggle('active');
            });

            // Close on outside click
            document.addEventListener('click', (e) => {
                if (!toggle.contains(e.target) && !nav.contains(e.target)) {
                    nav.classList.remove('active');
                }
            });
        }
    }
};

// ==========================================================================
// API Client
// ==========================================================================
const API = {
    BASE_URL: '/api/v1',

    async fetch(endpoint, options = {}) {
        try {
            const response = await fetch(`${this.BASE_URL}${endpoint}`, {
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'API request failed');
            }

            return data;
        } catch (error) {
            console.error(`API Error (${endpoint}):`, error);
            throw error;
        }
    },

    // Market Data
    getTrending() {
        return this.fetch('/market/trending');
    },

    getPrices(coins = ['bitcoin', 'ethereum']) {
        return this.fetch(`/market/prices?coins=${coins.join(',')}`);
    },

    getCoinDetails(coinId) {
        return this.fetch(`/market/coin/${coinId}`);
    },

    // Sentiment
    getFearGreed(limit = 1) {
        return this.fetch(`/sentiment/fear-greed?limit=${limit}`);
    },

    getFearGreedSignal() {
        return this.fetch('/sentiment/fear-greed/signal');
    },

    // Dashboard Summary
    getDashboardSummary() {
        return this.fetch('/dashboard/summary');
    }
};

// ==========================================================================
// Utility Functions
// ==========================================================================
const Utils = {
    // Format currency
    formatCurrency(value, currency = 'USD', compact = false) {
        const options = {
            style: 'currency',
            currency: currency,
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        };

        if (compact && value >= 1e9) {
            return (value / 1e9).toFixed(2) + 'B';
        } else if (compact && value >= 1e6) {
            return (value / 1e6).toFixed(2) + 'M';
        }

        return new Intl.NumberFormat('en-US', options).format(value);
    },

    // Format percentage
    formatPercent(value, decimals = 2) {
        const sign = value >= 0 ? '+' : '';
        return `${sign}${value.toFixed(decimals)}%`;
    },

    // Format number
    formatNumber(value, decimals = 0) {
        return new Intl.NumberFormat('en-US', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        }).format(value);
    },

    // Format time ago
    timeAgo(timestamp) {
        const now = new Date();
        const time = new Date(timestamp);
        const diff = Math.floor((now - time) / 1000);

        if (diff < 60) return 'just now';
        if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
        if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
        return `${Math.floor(diff / 86400)}d ago`;
    },

    // Debounce function
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    // Get Fear & Greed color class
    getFearGreedClass(value) {
        if (value <= 25) return 'gauge-extreme-fear';
        if (value <= 45) return 'gauge-fear';
        if (value <= 55) return 'gauge-neutral';
        if (value <= 75) return 'gauge-greed';
        return 'gauge-extreme-greed';
    },

    // Get Fear & Greed color
    getFearGreedColor(value) {
        if (value <= 25) return '#ef4444'; // Extreme Fear
        if (value <= 45) return '#f97316'; // Fear
        if (value <= 55) return '#eab308'; // Neutral
        if (value <= 75) return '#84cc16'; // Greed
        return '#22c55e'; // Extreme Greed
    }
};

// ==========================================================================
// Initialize
// ==========================================================================
document.addEventListener('DOMContentLoaded', () => {
    ThemeManager.init();
    MobileNav.init();
});

// Export for use in other scripts
window.CryptoDashboard = {
    API,
    Utils,
    ThemeManager
};
