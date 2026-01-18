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
            // Load core data in parallel
            const [summaryData, trendingData] = await Promise.all([
                CryptoDashboard.API.getDashboardSummary().catch(e => null),
                CryptoDashboard.API.getTrending().catch(e => null)
            ]);

            // Update core components
            if (summaryData?.data) {
                this.updateFearGreed(summaryData.data.fear_greed);
                this.updateSignal(summaryData.data.market_signal);
            }

            if (trendingData?.data?.coins) {
                this.updateTrendingCoins(trendingData.data.coins);
            }

            // Load advanced features data in parallel
            await this.loadAdvancedData();

            // Update timestamp
            this.updateLastUpdated();

        } catch (error) {
            console.error('Failed to load dashboard data:', error);
        } finally {
            this.isLoading = false;
        }
    },

    async loadAdvancedData() {
        try {
            const [
                sectorsData,
                whalesData,
                technicalData,
                devData,
                listingsData,
                unlocksData,
                upgradesData,
                influencerData
            ] = await Promise.all([
                this.fetchAPI('/api/v1/sectors').catch(e => null),
                this.fetchAPI('/api/v1/whales/analysis').catch(e => null),
                this.fetchAPI('/api/v1/analysis/technical/bitcoin').catch(e => null),
                this.fetchAPI('/api/v1/development').catch(e => null),
                this.fetchAPI('/api/v1/calendar/listings').catch(e => null),
                this.fetchAPI('/api/v1/calendar/unlocks').catch(e => null),
                this.fetchAPI('/api/v1/calendar/upgrades').catch(e => null),
                this.fetchAPI('/api/v1/influencers/activity').catch(e => null)
            ]);

            // Update advanced components
            if (sectorsData?.data) {
                SectorPerformance.update(sectorsData.data);
            }
            if (whalesData?.data) {
                WhaleAlerts.update(whalesData.data);
            }
            if (technicalData?.data) {
                TechnicalIndicators.update(technicalData.data);
            }
            if (devData?.data) {
                DevActivity.update(devData.data);
            }
            if (listingsData?.data) {
                CalendarEvents.updateListings(listingsData.data);
            }
            if (unlocksData?.data) {
                CalendarEvents.updateUnlocks(unlocksData.data);
            }
            if (upgradesData?.data) {
                CalendarEvents.updateUpgrades(upgradesData.data);
            }
            if (influencerData?.data) {
                InfluencerFeed.update(influencerData.data);
            }
        } catch (error) {
            console.error('Failed to load advanced data:', error);
        }
    },

    async fetchAPI(url) {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json();
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
// Sector Performance
// ==========================================================================
const SectorPerformance = {
    update(data) {
        const container = document.getElementById('sectorList');
        if (!container || !data?.sectors) return;

        const sectors = Object.entries(data.sectors).slice(0, 8);

        if (sectors.length === 0) {
            container.innerHTML = '<div class="event-empty">No sector data available</div>';
            return;
        }

        container.innerHTML = sectors.map(([id, sector]) => this.renderSector(sector)).join('');
    },

    renderSector(sector) {
        const change = sector.avg_change_24h || 0;
        const changeClass = change >= 0 ? 'positive' : 'negative';
        const sentimentClass = (sector.sentiment || 'neutral').toLowerCase().includes('bull') ? 'bullish' :
                               (sector.sentiment || 'neutral').toLowerCase().includes('bear') ? 'bearish' : 'neutral';

        return `
            <div class="sector-item">
                <div class="sector-info">
                    <div class="sector-name">${this.escapeHtml(sector.name)}</div>
                    <div class="sector-coins">${sector.coin_count || 0} coins</div>
                </div>
                <span class="sector-change ${changeClass}">${change >= 0 ? '+' : ''}${change.toFixed(2)}%</span>
                <span class="sector-sentiment ${sentimentClass}">${sector.sentiment || 'N/A'}</span>
            </div>
        `;
    },

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text || '';
        return div.innerHTML;
    }
};

// ==========================================================================
// Whale Alerts
// ==========================================================================
const WhaleAlerts = {
    update(data) {
        const container = document.getElementById('whaleAlerts');
        if (!container) return;

        const transactions = data?.recent_transactions || data?.transactions || [];

        if (transactions.length === 0) {
            container.innerHTML = '<div class="event-empty">No whale alerts available</div>';
            return;
        }

        container.innerHTML = transactions.slice(0, 5).map(tx => this.renderAlert(tx)).join('');
    },

    renderAlert(tx) {
        const flowType = (tx.from_exchange && !tx.to_exchange) ? 'outflow' :
                         (!tx.from_exchange && tx.to_exchange) ? 'inflow' : 'transfer';
        const flowLabel = flowType === 'outflow' ? 'Exchange Outflow' :
                          flowType === 'inflow' ? 'Exchange Inflow' : 'Transfer';

        return `
            <div class="whale-alert-item">
                <span class="whale-icon">🐋</span>
                <div class="whale-details">
                    <div class="whale-amount">$${this.formatNumber(tx.amount_usd || 0)}</div>
                    <div class="whale-flow">
                        ${this.formatNumber(tx.amount || 0)} ${tx.symbol || 'BTC'}
                        ${tx.from_exchange ? `from <span class="exchange">${tx.from_exchange}</span>` : ''}
                        ${tx.to_exchange ? `to <span class="exchange">${tx.to_exchange}</span>` : ''}
                    </div>
                    <div class="whale-time">${this.formatTime(tx.timestamp)}</div>
                </div>
                <span class="whale-type ${flowType}">${flowLabel}</span>
            </div>
        `;
    },

    formatNumber(num) {
        if (num >= 1e9) return (num / 1e9).toFixed(2) + 'B';
        if (num >= 1e6) return (num / 1e6).toFixed(2) + 'M';
        if (num >= 1e3) return (num / 1e3).toFixed(2) + 'K';
        return num.toFixed(2);
    },

    formatTime(timestamp) {
        if (!timestamp) return 'Recently';
        const date = new Date(timestamp);
        return date.toLocaleTimeString();
    }
};

// ==========================================================================
// Technical Indicators
// ==========================================================================
const TechnicalIndicators = {
    update(data) {
        const container = document.getElementById('technicalIndicators');
        if (!container) return;

        const indicators = data?.indicators || {};
        const summary = data?.summary || {};

        container.innerHTML = `
            ${this.renderIndicator('RSI (14)', indicators.rsi, this.getRSISignal(indicators.rsi))}
            ${this.renderMACD(indicators.macd)}
            ${this.renderBollinger(indicators.bollinger_bands, data?.current_price)}
            ${this.renderSummary(summary)}
        `;
    },

    renderIndicator(label, value, signal) {
        const signalClass = signal === 'Buy' ? 'buy' : signal === 'Sell' ? 'sell' : 'neutral';
        const displayValue = value != null ? value.toFixed(2) : 'N/A';

        return `
            <div class="indicator-item">
                <div>
                    <div class="indicator-label">${label}</div>
                    ${label.includes('RSI') ? this.renderRSIBar(value) : ''}
                </div>
                <div style="text-align: right;">
                    <div class="indicator-value">${displayValue}</div>
                    <span class="indicator-signal ${signalClass}">${signal}</span>
                </div>
            </div>
        `;
    },

    renderRSIBar(value) {
        if (value == null) return '';
        const fillClass = value <= 30 ? 'oversold' : value >= 70 ? 'overbought' : 'neutral';
        return `
            <div class="indicator-bar">
                <div class="indicator-bar-fill ${fillClass}" style="width: ${value}%;"></div>
            </div>
        `;
    },

    renderMACD(macd) {
        if (!macd) return '';
        const signal = macd.histogram > 0 ? 'Buy' : macd.histogram < 0 ? 'Sell' : 'Neutral';
        const signalClass = signal === 'Buy' ? 'buy' : signal === 'Sell' ? 'sell' : 'neutral';

        return `
            <div class="indicator-item">
                <div>
                    <div class="indicator-label">MACD</div>
                    <div style="font-size: 0.75rem; color: var(--text-muted);">
                        Line: ${macd.macd_line?.toFixed(2) || 'N/A'} | Signal: ${macd.signal_line?.toFixed(2) || 'N/A'}
                    </div>
                </div>
                <div style="text-align: right;">
                    <div class="indicator-value">${macd.histogram?.toFixed(2) || 'N/A'}</div>
                    <span class="indicator-signal ${signalClass}">${signal}</span>
                </div>
            </div>
        `;
    },

    renderBollinger(bands, price) {
        if (!bands) return '';
        const position = price < bands.lower ? 'Oversold' : price > bands.upper ? 'Overbought' : 'Normal';
        const signalClass = position === 'Oversold' ? 'buy' : position === 'Overbought' ? 'sell' : 'neutral';

        return `
            <div class="indicator-item">
                <div>
                    <div class="indicator-label">Bollinger Bands</div>
                    <div style="font-size: 0.75rem; color: var(--text-muted);">
                        Upper: $${bands.upper?.toFixed(0) || 'N/A'} | Lower: $${bands.lower?.toFixed(0) || 'N/A'}
                    </div>
                </div>
                <div style="text-align: right;">
                    <div class="indicator-value">$${bands.middle?.toFixed(0) || 'N/A'}</div>
                    <span class="indicator-signal ${signalClass}">${position}</span>
                </div>
            </div>
        `;
    },

    renderSummary(summary) {
        if (!summary?.overall_signal) return '';
        const signal = summary.overall_signal;
        const signalClass = signal.toLowerCase().includes('buy') ? 'buy' :
                           signal.toLowerCase().includes('sell') ? 'sell' : 'neutral';

        return `
            <div class="indicator-item" style="background: var(--bg-secondary);">
                <div class="indicator-label">Overall Signal</div>
                <span class="indicator-signal ${signalClass}" style="font-size: 0.875rem; padding: 0.5rem 1rem;">
                    ${signal}
                </span>
            </div>
        `;
    },

    getRSISignal(rsi) {
        if (rsi == null) return 'N/A';
        if (rsi <= 30) return 'Buy';
        if (rsi >= 70) return 'Sell';
        return 'Neutral';
    }
};

// ==========================================================================
// Development Activity
// ==========================================================================
const DevActivity = {
    update(data) {
        const container = document.getElementById('devActivity');
        if (!container) return;

        const projects = data?.projects || [];

        if (projects.length === 0) {
            container.innerHTML = '<div class="event-empty">No development data available</div>';
            return;
        }

        container.innerHTML = projects.slice(0, 6).map(project => this.renderProject(project)).join('');
    },

    renderProject(project) {
        return `
            <div class="dev-project">
                <div class="dev-project-icon">💻</div>
                <div class="dev-project-info">
                    <div class="dev-project-name">${this.escapeHtml(project.name)}</div>
                    <div class="dev-project-commits">
                        ${project.commits_last_week || 0} commits/week | ${project.contributors || 0} contributors
                    </div>
                </div>
                <div class="dev-activity-score">
                    <div class="dev-score-value">${project.activity_score || 0}</div>
                    <div class="dev-score-label">${project.activity_level || 'N/A'}</div>
                </div>
            </div>
        `;
    },

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text || '';
        return div.innerHTML;
    }
};

// ==========================================================================
// Calendar Events
// ==========================================================================
const CalendarEvents = {
    updateListings(data) {
        const container = document.getElementById('listingEvents');
        if (!container) return;

        const listings = data?.listings || [];

        if (listings.length === 0) {
            container.innerHTML = '<div class="event-empty">No upcoming listings</div>';
            return;
        }

        container.innerHTML = listings.slice(0, 5).map(event => this.renderListing(event)).join('');
    },

    updateUnlocks(data) {
        const container = document.getElementById('unlockEvents');
        if (!container) return;

        const unlocks = data?.unlocks || [];

        if (unlocks.length === 0) {
            container.innerHTML = '<div class="event-empty">No upcoming unlocks</div>';
            return;
        }

        container.innerHTML = unlocks.slice(0, 5).map(event => this.renderUnlock(event)).join('');
    },

    updateUpgrades(data) {
        const container = document.getElementById('upgradeEvents');
        if (!container) return;

        const upgrades = data?.upgrades || [];

        if (upgrades.length === 0) {
            container.innerHTML = '<div class="event-empty">No upcoming upgrades</div>';
            return;
        }

        container.innerHTML = upgrades.slice(0, 5).map(event => this.renderUpgrade(event)).join('');
    },

    renderListing(event) {
        const impactClass = (event.impact || '').toLowerCase();

        return `
            <div class="event-item">
                <div class="event-header">
                    <div>
                        <span class="event-coin">${this.escapeHtml(event.coin_name || event.symbol)}</span>
                        <span class="event-symbol">${event.symbol || ''}</span>
                    </div>
                    <span class="event-days">${event.days_until || 0}d</span>
                </div>
                <div class="event-details">
                    Listed on <span class="event-exchange">${event.exchange || 'Unknown'}</span>
                    <span class="event-impact ${impactClass}">${event.impact || 'N/A'}</span>
                </div>
            </div>
        `;
    },

    renderUnlock(event) {
        const impactClass = (event.impact || '').toLowerCase();

        return `
            <div class="event-item">
                <div class="event-header">
                    <div>
                        <span class="event-coin">${this.escapeHtml(event.coin_name || event.symbol)}</span>
                        <span class="event-symbol">${event.symbol || ''}</span>
                    </div>
                    <span class="event-days">${event.days_until || 0}d</span>
                </div>
                <div class="event-details">
                    <span class="event-amount">${this.formatNumber(event.unlock_amount || 0)}</span> tokens
                    (${event.unlock_percentage || 0}%)
                    <span class="event-impact ${impactClass}">${event.impact || 'N/A'}</span>
                </div>
            </div>
        `;
    },

    renderUpgrade(event) {
        return `
            <div class="event-item">
                <div class="event-header">
                    <div>
                        <span class="event-coin">${this.escapeHtml(event.coin_name || event.symbol)}</span>
                        <span class="event-symbol">${event.symbol || ''}</span>
                    </div>
                    <span class="event-days">${event.days_until || 0}d</span>
                </div>
                <div class="event-details">
                    <span class="event-upgrade-name">${event.upgrade_name || 'Upgrade'}</span>
                    ${event.description ? `<div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.25rem;">${this.escapeHtml(event.description)}</div>` : ''}
                </div>
            </div>
        `;
    },

    formatNumber(num) {
        if (num >= 1e9) return (num / 1e9).toFixed(2) + 'B';
        if (num >= 1e6) return (num / 1e6).toFixed(2) + 'M';
        if (num >= 1e3) return (num / 1e3).toFixed(2) + 'K';
        return num.toString();
    },

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text || '';
        return div.innerHTML;
    }
};

// ==========================================================================
// Influencer Feed
// ==========================================================================
const InfluencerFeed = {
    update(data) {
        const container = document.getElementById('influencerFeed');
        if (!container) return;

        const mentions = data?.mentions || [];

        if (mentions.length === 0) {
            container.innerHTML = '<div class="event-empty">No recent influencer activity</div>';
            return;
        }

        container.innerHTML = mentions.slice(0, 6).map(mention => this.renderMention(mention)).join('');
    },

    renderMention(mention) {
        const influencer = mention.influencer || {};
        const sentimentClass = (mention.sentiment || '').toLowerCase().includes('bull') ? 'bullish' :
                               (mention.sentiment || '').toLowerCase().includes('bear') ? 'bearish' : 'neutral';
        const initials = (influencer.name || 'U').split(' ').map(n => n[0]).join('').substring(0, 2);

        return `
            <div class="influencer-mention">
                <div class="influencer-avatar">${initials}</div>
                <div class="influencer-content">
                    <div class="influencer-header">
                        <div>
                            <span class="influencer-name">${this.escapeHtml(influencer.name || 'Unknown')}</span>
                            <span class="influencer-handle">${influencer.handle || ''}</span>
                        </div>
                        <span class="influencer-sentiment ${sentimentClass}">${mention.sentiment || 'N/A'}</span>
                    </div>
                    <div class="influencer-text">${this.escapeHtml(mention.text || '')}</div>
                    <div class="influencer-meta">
                        <div class="influencer-coins">
                            ${(mention.coins_mentioned || []).map(coin =>
                                `<span class="influencer-coin-tag">${coin}</span>`
                            ).join('')}
                        </div>
                        <span>${this.formatEngagement(mention.engagement)}</span>
                    </div>
                </div>
            </div>
        `;
    },

    formatEngagement(engagement) {
        if (!engagement) return '';
        const total = (engagement.likes || 0) + (engagement.retweets || 0);
        if (total >= 1e6) return (total / 1e6).toFixed(1) + 'M engagements';
        if (total >= 1e3) return (total / 1e3).toFixed(1) + 'K engagements';
        return total + ' engagements';
    },

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text || '';
        return div.innerHTML;
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
