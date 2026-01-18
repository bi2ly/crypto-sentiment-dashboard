/**
 * Crypto Sentiment Dashboard - Dashboard JavaScript
 */

// ==========================================================================
// Dashboard Controller
// ==========================================================================
const Dashboard = {
    updateInterval: 60000, // 1 minute
    intervalId: null,
    isLoading: false,

    async init() {
        console.log('Initializing dashboard...');

        // Initial data load
        await this.loadAllData();

        // Start auto-refresh
        this.startAutoRefresh();

        // Bind events
        this.bindEvents();
    },

    bindEvents() {
        const refreshBtn = document.getElementById('refreshBtn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.refresh());
        }
    },

    startAutoRefresh() {
        this.intervalId = setInterval(() => {
            this.loadAllData();
        }, this.updateInterval);
    },

    stopAutoRefresh() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
    },

    async refresh() {
        const refreshBtn = document.getElementById('refreshBtn');
        if (refreshBtn) {
            refreshBtn.classList.add('loading');
        }

        await this.loadAllData();

        if (refreshBtn) {
            refreshBtn.classList.remove('loading');
        }
    },

    async loadAllData() {
        if (this.isLoading) return;
        this.isLoading = true;

        try {
            // Load data in parallel
            const [summaryData, trendingData] = await Promise.all([
                CryptoDashboard.API.getDashboardSummary().catch(e => null),
                CryptoDashboard.API.getTrending().catch(e => null)
            ]);

            // Update components
            if (summaryData?.data) {
                this.updateFearGreed(summaryData.data.fear_greed);
                this.updateSignal(summaryData.data.market_signal);
            }

            if (trendingData?.data?.coins) {
                this.updateTrendingCoins(trendingData.data.coins);
            }

            // Update timestamp
            this.updateLastUpdated();

        } catch (error) {
            console.error('Failed to load dashboard data:', error);
        } finally {
            this.isLoading = false;
        }
    },

    updateLastUpdated() {
        const el = document.getElementById('lastUpdated');
        if (el) {
            const now = new Date();
            el.textContent = `Last updated: ${now.toLocaleTimeString()}`;
        }
    }
};

// ==========================================================================
// Fear & Greed Gauge
// ==========================================================================
const FearGreedGauge = {
    update(data) {
        if (!data) return;

        const value = data.value;
        const classification = data.classification;

        // Update value display
        const valueEl = document.getElementById('fearGreedValue');
        if (valueEl) {
            this.animateValue(valueEl, parseInt(valueEl.textContent) || 0, value, 1000);
        }

        // Update label
        const labelEl = document.getElementById('fearGreedLabel');
        if (labelEl) {
            labelEl.textContent = classification;
        }

        // Update gauge visual
        this.updateGaugeVisual(value);

        // Update color class
        const container = document.querySelector('.gauge-container');
        if (container) {
            container.className = 'gauge-container ' + CryptoDashboard.Utils.getFearGreedClass(value);
        }
    },

    updateGaugeVisual(value) {
        // Update needle rotation (-90 to 90 degrees)
        const needle = document.getElementById('gaugeNeedle');
        if (needle) {
            const rotation = (value / 100) * 180 - 90;
            needle.style.transform = `translateX(-50%) rotate(${rotation}deg)`;
        }

        // Update arc
        const arc = document.getElementById('gaugeArc');
        if (arc) {
            // Arc length is approximately 251.2 (half circle with radius 80)
            const maxOffset = 251.2;
            const offset = maxOffset - (value / 100) * maxOffset;
            arc.style.strokeDashoffset = offset;
            arc.style.stroke = CryptoDashboard.Utils.getFearGreedColor(value);
        }
    },

    animateValue(element, start, end, duration) {
        const range = end - start;
        const startTime = performance.now();

        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);

            // Ease out cubic
            const easeOut = 1 - Math.pow(1 - progress, 3);
            const current = Math.round(start + range * easeOut);

            element.textContent = current;

            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };

        requestAnimationFrame(animate);
    }
};

// Connect to Dashboard
Dashboard.updateFearGreed = function(data) {
    FearGreedGauge.update(data);
};

// ==========================================================================
// Signal Card
// ==========================================================================
const SignalCard = {
    update(data) {
        if (!data) return;

        const signal = data.signal;
        const strength = data.strength;
        const reasoning = data.reasoning;

        // Update signal icon
        const iconEl = document.querySelector('.signal-icon');
        if (iconEl) {
            iconEl.className = 'signal-icon ' + signal.toLowerCase();
            iconEl.textContent = this.getSignalEmoji(signal);
        }

        // Update signal action text
        const actionEl = document.querySelector('.signal-action');
        if (actionEl) {
            actionEl.className = 'signal-action ' + signal.toLowerCase();
            actionEl.textContent = signal;
        }

        // Update strength
        const strengthEl = document.querySelector('.signal-strength');
        if (strengthEl) {
            strengthEl.textContent = `${strength} Signal`;
        }

        // Update reasoning
        const reasoningEl = document.querySelector('.signal-reasoning');
        if (reasoningEl) {
            reasoningEl.textContent = reasoning;
        }
    },

    getSignalEmoji(signal) {
        switch (signal.toUpperCase()) {
            case 'BUY': return '📈';
            case 'SELL': return '📉';
            case 'HOLD': return '⏸️';
            default: return '❓';
        }
    }
};

// Connect to Dashboard
Dashboard.updateSignal = function(data) {
    SignalCard.update(data);
};

// ==========================================================================
// Trending Coins Table
// ==========================================================================
const TrendingCoins = {
    update(coins) {
        const tbody = document.getElementById('trendingTableBody');
        if (!tbody || !coins) return;

        tbody.innerHTML = coins.map((coin, index) => this.renderRow(coin, index)).join('');
    },

    renderRow(coin, index) {
        const rankClass = index < 3 ? 'top-3' : '';

        return `
            <tr>
                <td>
                    <span class="coin-rank ${rankClass}">${index + 1}</span>
                </td>
                <td>
                    <div class="coin-row">
                        <img
                            src="${coin.thumb || '/static/img/coin-placeholder.svg'}"
                            alt="${coin.name}"
                            class="coin-icon"
                            onerror="this.src='/static/img/coin-placeholder.svg'"
                        >
                        <div class="coin-info">
                            <div class="coin-name">${this.escapeHtml(coin.name)}</div>
                            <div class="coin-symbol">${this.escapeHtml(coin.symbol)}</div>
                        </div>
                    </div>
                </td>
                <td class="text-right">
                    <span class="coin-market-cap">
                        ${coin.market_cap_rank ? `#${coin.market_cap_rank}` : '-'}
                    </span>
                </td>
                <td class="text-right">
                    <span class="badge badge-info">Trending</span>
                </td>
            </tr>
        `;
    },

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};

// Connect to Dashboard
Dashboard.updateTrendingCoins = function(coins) {
    TrendingCoins.update(coins);
};

// ==========================================================================
// API Status
// ==========================================================================
const APIStatus = {
    async check() {
        try {
            const response = await fetch('/health');
            const data = await response.json();

            if (data.api_status) {
                this.updateDisplay(data.api_status);
            }
        } catch (error) {
            console.error('Failed to check API status:', error);
        }
    },

    updateDisplay(status) {
        const apis = ['coingecko', 'fear_greed', 'whale_alert', 'reddit', 'news_api'];

        apis.forEach(api => {
            const el = document.getElementById(`status-${api}`);
            if (el) {
                const isOnline = status[api];
                el.className = `api-status-dot ${isOnline ? 'online' : 'offline'}`;
            }
        });
    }
};

// ==========================================================================
// Initialize Dashboard
// ==========================================================================
document.addEventListener('DOMContentLoaded', () => {
    Dashboard.init();
    APIStatus.check();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    Dashboard.stopAutoRefresh();
});
