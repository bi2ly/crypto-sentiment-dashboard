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

            // Load Phase 4 smart analysis data
            await this.loadSmartData();

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
                this.fetchAPI('/api/v1/sectors').catch(e => ({ error: e.message })),
                this.fetchAPI('/api/v1/whales/analysis').catch(e => ({ error: e.message })),
                this.fetchAPI('/api/v1/analysis/technical/bitcoin').catch(e => ({ error: e.message })),
                this.fetchAPI('/api/v1/development').catch(e => ({ error: e.message })),
                this.fetchAPI('/api/v1/calendar/listings').catch(e => ({ error: e.message })),
                this.fetchAPI('/api/v1/calendar/unlocks').catch(e => ({ error: e.message })),
                this.fetchAPI('/api/v1/calendar/upgrades').catch(e => ({ error: e.message })),
                this.fetchAPI('/api/v1/influencers/activity').catch(e => ({ error: e.message }))
            ]);

            // Update advanced components with error handling
            if (sectorsData?.data) {
                SectorPerformance.update(sectorsData.data);
            } else {
                SectorPerformance.showError(sectorsData?.error || 'Failed to load sector data');
            }

            if (whalesData?.data) {
                WhaleAlerts.update(whalesData.data);
            } else {
                WhaleAlerts.showError(whalesData?.error || 'Failed to load whale data');
            }

            if (technicalData?.data) {
                TechnicalIndicators.update(technicalData.data);
            } else {
                TechnicalIndicators.showError(technicalData?.error || 'Failed to load technical data');
            }

            if (devData?.data) {
                DevActivity.update(devData.data);
            } else {
                DevActivity.showError(devData?.error || 'Failed to load development data');
            }

            if (listingsData?.data) {
                CalendarEvents.updateListings(listingsData.data);
            } else {
                CalendarEvents.showListingsError(listingsData?.error || 'Failed to load listings');
            }

            if (unlocksData?.data) {
                CalendarEvents.updateUnlocks(unlocksData.data);
            } else {
                CalendarEvents.showUnlocksError(unlocksData?.error || 'Failed to load unlocks');
            }

            if (upgradesData?.data) {
                CalendarEvents.updateUpgrades(upgradesData.data);
            } else {
                CalendarEvents.showUpgradesError(upgradesData?.error || 'Failed to load upgrades');
            }

            if (influencerData?.data) {
                InfluencerFeed.update(influencerData.data);
            } else {
                InfluencerFeed.showError(influencerData?.error || 'Failed to load influencer data');
            }
        } catch (error) {
            console.error('Failed to load advanced data:', error);
            // Show error state for all components on total failure
            this.showAllErrors('Connection error');
        }
    },

    showAllErrors(message) {
        SectorPerformance.showError(message);
        WhaleAlerts.showError(message);
        TechnicalIndicators.showError(message);
        DevActivity.showError(message);
        CalendarEvents.showListingsError(message);
        CalendarEvents.showUnlocksError(message);
        CalendarEvents.showUpgradesError(message);
        InfluencerFeed.showError(message);
        // Phase 4 components
        OpportunityScore.showError(message);
        RiskAssessment.showError(message);
        AlertsPanel.showError(message);
    },

    async loadSmartData() {
        try {
            const smartData = await this.fetchAPI('/api/v1/dashboard/smart').catch(e => ({ error: e.message }));

            if (smartData?.data) {
                // Update Phase 4 components
                OpportunityScore.update(smartData.data.opportunity);
                RiskAssessment.update(smartData.data.risk);
                AlertsPanel.update(smartData.data.alerts);

                // Update factors breakdown
                if (smartData.data.opportunity?.factors) {
                    FactorsBreakdown.update(smartData.data.opportunity.factors);
                }

                // Show warnings if any
                if (smartData.data.risk?.warnings?.length > 0) {
                    RiskWarnings.update(smartData.data.risk.warnings);
                }
            } else {
                OpportunityScore.showError(smartData?.error || 'Failed to load smart data');
                RiskAssessment.showError(smartData?.error || 'Failed to load smart data');
                AlertsPanel.showError(smartData?.error || 'Failed to load smart data');
            }
        } catch (error) {
            console.error('Failed to load smart data:', error);
        }
    },

    async fetchAPI(url) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 15000); // 15 second timeout

        try {
            const response = await fetch(url, { signal: controller.signal });
            clearTimeout(timeoutId);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return response.json();
        } catch (error) {
            clearTimeout(timeoutId);
            if (error.name === 'AbortError') {
                throw new Error('Request timeout');
            }
            throw error;
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
    },

    showError(message) {
        const container = document.getElementById('sectorList');
        if (container) {
            container.innerHTML = `<div class="error-state"><span class="error-icon">⚠️</span><span class="error-message">${message}</span></div>`;
        }
    }
};

// ==========================================================================
// Whale Alerts
// ==========================================================================
const WhaleAlerts = {
    update(data) {
        const container = document.getElementById('whaleAlerts');
        if (!container) return;

        // Handle API not configured case
        if (data?.configured === false || data?.status === 'unavailable') {
            container.innerHTML = `<div class="info-state"><span class="info-icon">ℹ️</span><span class="info-message">${data.message || 'Whale Alert API not configured'}</span></div>`;
            return;
        }

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
    },

    showError(message) {
        const container = document.getElementById('whaleAlerts');
        if (container) {
            container.innerHTML = `<div class="error-state"><span class="error-icon">⚠️</span><span class="error-message">${message}</span></div>`;
        }
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
        const summary = data?.recommendation || {};

        // Extract RSI value (can be object {value, signal} or number)
        const rsiData = indicators.rsi || {};
        const rsiValue = typeof rsiData === 'object' ? rsiData.value : rsiData;
        const rsiSignal = typeof rsiData === 'object' ? rsiData.signal : this.getRSISignalFromValue(rsiValue);

        container.innerHTML = `
            ${this.renderRSI(rsiValue, rsiSignal)}
            ${this.renderMACD(indicators.macd)}
            ${this.renderBollinger(indicators.bollinger_bands, data?.current_price)}
            ${this.renderSummary(summary)}
        `;
    },

    renderRSI(value, signal) {
        const signalClass = (signal || '').toLowerCase().includes('buy') || (signal || '').toLowerCase() === 'oversold' ? 'buy' :
                           (signal || '').toLowerCase().includes('sell') || (signal || '').toLowerCase() === 'overbought' ? 'sell' : 'neutral';
        const displayValue = value != null ? Number(value).toFixed(2) : 'N/A';
        const displaySignal = signal || this.getRSISignalFromValue(value);

        return `
            <div class="indicator-item">
                <div>
                    <div class="indicator-label">RSI (14)</div>
                    ${this.renderRSIBar(value)}
                </div>
                <div style="text-align: right;">
                    <div class="indicator-value">${displayValue}</div>
                    <span class="indicator-signal ${signalClass}">${displaySignal}</span>
                </div>
            </div>
        `;
    },

    renderIndicator(label, value, signal) {
        const signalClass = signal === 'Buy' ? 'buy' : signal === 'Sell' ? 'sell' : 'neutral';
        const displayValue = value != null ? Number(value).toFixed(2) : 'N/A';

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
        // Handle both {macd_line, signal_line, histogram} and {macd, signal, histogram, trend} formats
        const macdLine = macd.macd_line ?? macd.macd;
        const signalLine = macd.signal_line ?? macd.signal;
        const histogram = macd.histogram;
        const trend = macd.trend;

        const signalText = trend ? (trend === 'BULLISH' ? 'Buy' : trend === 'BEARISH' ? 'Sell' : 'Neutral') :
                          (histogram > 0 ? 'Buy' : histogram < 0 ? 'Sell' : 'Neutral');
        const signalClass = signalText === 'Buy' ? 'buy' : signalText === 'Sell' ? 'sell' : 'neutral';

        return `
            <div class="indicator-item">
                <div>
                    <div class="indicator-label">MACD</div>
                    <div style="font-size: 0.75rem; color: var(--text-muted);">
                        Line: ${macdLine != null ? Number(macdLine).toFixed(2) : 'N/A'} | Signal: ${signalLine != null ? Number(signalLine).toFixed(2) : 'N/A'}
                    </div>
                </div>
                <div style="text-align: right;">
                    <div class="indicator-value">${histogram != null ? Number(histogram).toFixed(2) : 'N/A'}</div>
                    <span class="indicator-signal ${signalClass}">${signalText}</span>
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
        if (!summary) return '';
        // Handle both {overall_signal} and {action, strength} formats
        const signal = summary.overall_signal || summary.action || 'HOLD';
        const strength = summary.strength || '';
        const signalClass = signal.toLowerCase().includes('buy') ? 'buy' :
                           signal.toLowerCase().includes('sell') ? 'sell' : 'neutral';

        return `
            <div class="indicator-item" style="background: var(--bg-secondary);">
                <div class="indicator-label">Overall Signal ${strength ? `(${strength})` : ''}</div>
                <span class="indicator-signal ${signalClass}" style="font-size: 0.875rem; padding: 0.5rem 1rem;">
                    ${signal}
                </span>
            </div>
        `;
    },

    getRSISignalFromValue(rsi) {
        if (rsi == null) return 'N/A';
        if (rsi <= 30) return 'Buy';
        if (rsi >= 70) return 'Sell';
        return 'Neutral';
    },

    showError(message) {
        const container = document.getElementById('technicalIndicators');
        if (container) {
            container.innerHTML = `<div class="error-state"><span class="error-icon">⚠️</span><span class="error-message">${message}</span></div>`;
        }
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
    },

    showError(message) {
        const container = document.getElementById('devActivity');
        if (container) {
            container.innerHTML = `<div class="error-state"><span class="error-icon">⚠️</span><span class="error-message">${message}</span></div>`;
        }
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
    },

    showListingsError(message) {
        const container = document.getElementById('listingEvents');
        if (container) {
            container.innerHTML = `<div class="error-state"><span class="error-icon">⚠️</span><span class="error-message">${message}</span></div>`;
        }
    },

    showUnlocksError(message) {
        const container = document.getElementById('unlockEvents');
        if (container) {
            container.innerHTML = `<div class="error-state"><span class="error-icon">⚠️</span><span class="error-message">${message}</span></div>`;
        }
    },

    showUpgradesError(message) {
        const container = document.getElementById('upgradeEvents');
        if (container) {
            container.innerHTML = `<div class="error-state"><span class="error-icon">⚠️</span><span class="error-message">${message}</span></div>`;
        }
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
    },

    showError(message) {
        const container = document.getElementById('influencerFeed');
        if (container) {
            container.innerHTML = `<div class="error-state"><span class="error-icon">⚠️</span><span class="error-message">${message}</span></div>`;
        }
    }
};

// ==========================================================================
// Phase 4: Opportunity Score Component
// ==========================================================================
const OpportunityScore = {
    update(data) {
        const container = document.getElementById('opportunityScore');
        if (!container) return;

        if (!data || data.error) {
            this.showError(data?.error || 'No data available');
            return;
        }

        const score = data.score ?? 0;
        const signal = data.signal || 'NEUTRAL';
        const confidence = data.confidence ?? 0;

        const signalClass = this.getSignalClass(signal);
        const scoreColor = this.getScoreColor(score);

        container.innerHTML = `
            <div class="opportunity-score-display">
                <div class="score-circle ${signalClass}" style="--score-color: ${scoreColor}">
                    <span class="score-value">${Math.round(score)}</span>
                    <span class="score-max">/100</span>
                </div>
                <div class="score-signal ${signalClass}">${this.formatSignal(signal)}</div>
                <div class="score-confidence">
                    <span class="confidence-label">Confidence:</span>
                    <span class="confidence-value">${Math.round(confidence * 100)}%</span>
                </div>
            </div>
            ${data.recommendation ? `<p class="score-recommendation">${data.recommendation}</p>` : ''}
        `;
    },

    getSignalClass(signal) {
        const map = {
            'STRONG_BUY': 'signal-strong-buy',
            'BUY': 'signal-buy',
            'NEUTRAL': 'signal-neutral',
            'SELL': 'signal-sell',
            'STRONG_SELL': 'signal-strong-sell'
        };
        return map[signal] || 'signal-neutral';
    },

    getScoreColor(score) {
        if (score >= 80) return '#10b981';
        if (score >= 65) return '#22c55e';
        if (score >= 45) return '#eab308';
        if (score >= 35) return '#f97316';
        return '#ef4444';
    },

    formatSignal(signal) {
        return (signal || '').replace(/_/g, ' ');
    },

    showError(message) {
        const container = document.getElementById('opportunityScore');
        if (container) {
            container.innerHTML = `<div class="error-state"><span class="error-icon">⚠️</span><span class="error-message">${message}</span></div>`;
        }
    }
};

// ==========================================================================
// Phase 4: Risk Assessment Component
// ==========================================================================
const RiskAssessment = {
    update(data) {
        const container = document.getElementById('riskAssessment');
        if (!container) return;

        if (!data || data.error) {
            this.showError(data?.error || 'No data available');
            return;
        }

        const overallRisk = data.overall_risk || 'MODERATE';
        const riskScore = data.risk_score ?? 50;
        const categories = data.categories || {};

        const riskClass = this.getRiskClass(overallRisk);

        container.innerHTML = `
            <div class="risk-overview">
                <div class="risk-level ${riskClass}">
                    <span class="risk-icon">${this.getRiskIcon(overallRisk)}</span>
                    <span class="risk-label">${this.formatRisk(overallRisk)}</span>
                </div>
                <div class="risk-score-bar">
                    <div class="risk-bar-fill" style="width: ${riskScore}%"></div>
                </div>
                <span class="risk-score-value">${Math.round(riskScore)}/100</span>
            </div>
            <div class="risk-categories">
                ${this.renderCategories(categories)}
            </div>
        `;
    },

    renderCategories(categories) {
        const categoryNames = {
            volatility: 'Volatility',
            liquidity: 'Liquidity',
            market: 'Market',
            concentration: 'Concentration',
            technical: 'Technical',
            sentiment: 'Sentiment'
        };

        return Object.entries(categories).map(([key, value]) => {
            const level = value?.level || 'MODERATE';
            const score = value?.score ?? 50;
            return `
                <div class="risk-category">
                    <span class="category-name">${categoryNames[key] || key}</span>
                    <span class="category-level ${this.getRiskClass(level)}">${this.formatRisk(level)}</span>
                </div>
            `;
        }).join('');
    },

    getRiskClass(level) {
        const map = {
            'MINIMAL': 'risk-minimal',
            'LOW': 'risk-low',
            'MODERATE': 'risk-moderate',
            'HIGH': 'risk-high',
            'EXTREME': 'risk-extreme'
        };
        return map[level] || 'risk-moderate';
    },

    getRiskIcon(level) {
        const map = {
            'MINIMAL': '✅',
            'LOW': '🟢',
            'MODERATE': '🟡',
            'HIGH': '🟠',
            'EXTREME': '🔴'
        };
        return map[level] || '🟡';
    },

    formatRisk(level) {
        return (level || '').charAt(0) + (level || '').slice(1).toLowerCase();
    },

    showError(message) {
        const container = document.getElementById('riskAssessment');
        if (container) {
            container.innerHTML = `<div class="error-state"><span class="error-icon">⚠️</span><span class="error-message">${message}</span></div>`;
        }
    }
};

// ==========================================================================
// Phase 4: Alerts Panel Component
// ==========================================================================
const AlertsPanel = {
    update(data) {
        const summaryContainer = document.getElementById('alertsSummary');
        const listContainer = document.getElementById('alertsList');
        const countBadge = document.getElementById('alertCount');

        if (!data || data.error) {
            this.showError(data?.error || 'No data available');
            return;
        }

        const alerts = data.recent_alerts || data.alerts || [];
        const summary = data.summary || {};

        // Update count badge
        if (countBadge) {
            countBadge.textContent = alerts.length;
            countBadge.className = `card-badge alert-count ${alerts.length > 0 ? 'has-alerts' : ''}`;
        }

        // Update summary
        if (summaryContainer) {
            summaryContainer.innerHTML = `
                <div class="alerts-summary-grid">
                    <div class="alert-stat">
                        <span class="alert-stat-value critical">${summary.critical || 0}</span>
                        <span class="alert-stat-label">Critical</span>
                    </div>
                    <div class="alert-stat">
                        <span class="alert-stat-value high">${summary.high || 0}</span>
                        <span class="alert-stat-label">High</span>
                    </div>
                    <div class="alert-stat">
                        <span class="alert-stat-value medium">${summary.medium || 0}</span>
                        <span class="alert-stat-label">Medium</span>
                    </div>
                    <div class="alert-stat">
                        <span class="alert-stat-value low">${summary.low || 0}</span>
                        <span class="alert-stat-label">Low</span>
                    </div>
                </div>
            `;
        }

        // Update alerts list
        if (listContainer) {
            if (alerts.length === 0) {
                listContainer.innerHTML = `<div class="info-state"><span class="info-icon">ℹ️</span><span class="info-message">No alerts in the last 24 hours</span></div>`;
            } else {
                listContainer.innerHTML = alerts.slice(0, 10).map(alert => this.renderAlert(alert)).join('');
            }
        }
    },

    renderAlert(alert) {
        const priorityClass = (alert.priority || 'medium').toLowerCase();
        const time = alert.triggered_at ? this.formatTime(alert.triggered_at) : 'Just now';

        return `
            <div class="alert-item ${priorityClass}">
                <span class="alert-priority-dot ${priorityClass}"></span>
                <div class="alert-content">
                    <div class="alert-message">${this.escapeHtml(alert.message || alert.name || 'Alert triggered')}</div>
                    <div class="alert-meta">
                        <span class="alert-type">${alert.alert_type || 'GENERAL'}</span>
                        <span class="alert-time">${time}</span>
                    </div>
                </div>
            </div>
        `;
    },

    formatTime(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = Math.floor((now - date) / 1000);

        if (diff < 60) return 'Just now';
        if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
        if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
        return date.toLocaleDateString();
    },

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text || '';
        return div.innerHTML;
    },

    showError(message) {
        const summaryContainer = document.getElementById('alertsSummary');
        const listContainer = document.getElementById('alertsList');

        if (summaryContainer) {
            summaryContainer.innerHTML = `<div class="error-state"><span class="error-icon">⚠️</span><span class="error-message">${message}</span></div>`;
        }
        if (listContainer) {
            listContainer.innerHTML = `<div class="error-state"><span class="error-icon">⚠️</span><span class="error-message">${message}</span></div>`;
        }
    }
};

// ==========================================================================
// Phase 4: Factors Breakdown Component
// ==========================================================================
const FactorsBreakdown = {
    update(factors) {
        const container = document.getElementById('factorsBreakdown');
        if (!container) return;

        if (!factors || Object.keys(factors).length === 0) {
            container.innerHTML = `<div class="info-state"><span class="info-icon">ℹ️</span><span class="info-message">No factor data available</span></div>`;
            return;
        }

        const factorConfig = {
            sentiment: { label: 'Sentiment', icon: '😊', weight: 0.20 },
            technical: { label: 'Technical', icon: '📈', weight: 0.25 },
            whale_activity: { label: 'Whale Activity', icon: '🐋', weight: 0.15 },
            development: { label: 'Development', icon: '💻', weight: 0.10 },
            volume: { label: 'Volume', icon: '📊', weight: 0.15 },
            price_action: { label: 'Price Action', icon: '💰', weight: 0.15 }
        };

        container.innerHTML = Object.entries(factors).map(([key, data]) => {
            const config = factorConfig[key] || { label: key, icon: '📌', weight: 0 };
            const score = data?.score ?? data ?? 0;
            const signal = data?.signal || this.getSignalFromScore(score);

            return `
                <div class="factor-card">
                    <div class="factor-header">
                        <span class="factor-icon">${config.icon}</span>
                        <span class="factor-name">${config.label}</span>
                        <span class="factor-weight">${Math.round(config.weight * 100)}%</span>
                    </div>
                    <div class="factor-score-bar">
                        <div class="factor-bar-fill ${this.getScoreClass(score)}" style="width: ${score}%"></div>
                    </div>
                    <div class="factor-footer">
                        <span class="factor-score">${Math.round(score)}/100</span>
                        <span class="factor-signal ${this.getScoreClass(score)}">${signal}</span>
                    </div>
                </div>
            `;
        }).join('');
    },

    getSignalFromScore(score) {
        if (score >= 70) return 'Bullish';
        if (score >= 55) return 'Slightly Bullish';
        if (score >= 45) return 'Neutral';
        if (score >= 30) return 'Slightly Bearish';
        return 'Bearish';
    },

    getScoreClass(score) {
        if (score >= 70) return 'score-high';
        if (score >= 45) return 'score-medium';
        return 'score-low';
    }
};

// ==========================================================================
// Phase 4: Risk Warnings Component
// ==========================================================================
const RiskWarnings = {
    update(warnings) {
        const container = document.getElementById('riskWarnings');
        const card = document.getElementById('riskWarningsCard');

        if (!container || !card) return;

        if (!warnings || warnings.length === 0) {
            card.style.display = 'none';
            return;
        }

        card.style.display = 'block';
        container.innerHTML = warnings.map(warning => this.renderWarning(warning)).join('');
    },

    renderWarning(warning) {
        const severityClass = (warning.severity || 'medium').toLowerCase();

        return `
            <div class="warning-item ${severityClass}">
                <span class="warning-icon">${this.getWarningIcon(severityClass)}</span>
                <div class="warning-content">
                    <div class="warning-title">${this.escapeHtml(warning.title || warning.category || 'Warning')}</div>
                    <div class="warning-message">${this.escapeHtml(warning.message || warning.description || '')}</div>
                </div>
            </div>
        `;
    },

    getWarningIcon(severity) {
        const map = {
            'low': '⚠️',
            'medium': '🟡',
            'high': '🟠',
            'critical': '🔴'
        };
        return map[severity] || '⚠️';
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
