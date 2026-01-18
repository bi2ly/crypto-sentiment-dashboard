"""
Crypto Sentiment Dashboard - Smart Alert System

Custom alert system for price, volume, whale activity, and sentiment alerts
with multi-factor logic support.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

from app.utils.cache import get_cache

logger = logging.getLogger(__name__)


class AlertType(Enum):
    """Types of alerts."""
    PRICE = 'price'
    VOLUME = 'volume'
    WHALE = 'whale'
    SENTIMENT = 'sentiment'
    TECHNICAL = 'technical'
    OPPORTUNITY = 'opportunity'
    COMPOSITE = 'composite'


class AlertCondition(Enum):
    """Alert condition operators."""
    ABOVE = 'above'
    BELOW = 'below'
    CROSSES_ABOVE = 'crosses_above'
    CROSSES_BELOW = 'crosses_below'
    PERCENT_CHANGE = 'percent_change'
    EQUALS = 'equals'


class AlertPriority(Enum):
    """Alert priority levels."""
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    CRITICAL = 'critical'


@dataclass
class AlertRule:
    """Definition of an alert rule."""
    id: str
    name: str
    alert_type: AlertType
    coin_id: str
    conditions: List[Dict]  # Multiple conditions for multi-factor alerts
    logic: str = 'AND'  # AND or OR
    priority: AlertPriority = AlertPriority.MEDIUM
    enabled: bool = True
    cooldown_minutes: int = 60  # Prevent repeated triggers
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_triggered: Optional[str] = None
    trigger_count: int = 0


@dataclass
class Alert:
    """A triggered alert."""
    id: str
    rule_id: str
    rule_name: str
    alert_type: str
    coin_id: str
    priority: str
    message: str
    details: Dict
    triggered_at: str
    acknowledged: bool = False


class AlertSystem:
    """
    Smart alert system with multi-factor logic.

    Features:
    - Price alerts (threshold, % change)
    - Volume alerts (unusual activity)
    - Whale alerts (large transactions)
    - Sentiment alerts (fear/greed extremes)
    - Technical alerts (RSI, MACD signals)
    - Composite alerts (multi-factor)
    """

    def __init__(self):
        self._cache = get_cache()
        self._rules: Dict[str, AlertRule] = {}
        self._alerts: List[Alert] = []
        self._initialize_default_rules()

    def _initialize_default_rules(self):
        """Set up default alert rules."""
        # Default price alert rules
        self.add_rule(AlertRule(
            id='default-extreme-fear',
            name='Extreme Fear Alert',
            alert_type=AlertType.SENTIMENT,
            coin_id='*',  # All coins
            conditions=[
                {'metric': 'fear_greed', 'condition': AlertCondition.BELOW.value, 'value': 20}
            ],
            priority=AlertPriority.HIGH,
            cooldown_minutes=240
        ))

        self.add_rule(AlertRule(
            id='default-extreme-greed',
            name='Extreme Greed Warning',
            alert_type=AlertType.SENTIMENT,
            coin_id='*',
            conditions=[
                {'metric': 'fear_greed', 'condition': AlertCondition.ABOVE.value, 'value': 80}
            ],
            priority=AlertPriority.HIGH,
            cooldown_minutes=240
        ))

        # RSI oversold alert
        self.add_rule(AlertRule(
            id='default-rsi-oversold',
            name='RSI Oversold',
            alert_type=AlertType.TECHNICAL,
            coin_id='bitcoin',
            conditions=[
                {'metric': 'rsi', 'condition': AlertCondition.BELOW.value, 'value': 30}
            ],
            priority=AlertPriority.MEDIUM,
            cooldown_minutes=120
        ))

        # RSI overbought alert
        self.add_rule(AlertRule(
            id='default-rsi-overbought',
            name='RSI Overbought',
            alert_type=AlertType.TECHNICAL,
            coin_id='bitcoin',
            conditions=[
                {'metric': 'rsi', 'condition': AlertCondition.ABOVE.value, 'value': 70}
            ],
            priority=AlertPriority.MEDIUM,
            cooldown_minutes=120
        ))

        # High opportunity score alert
        self.add_rule(AlertRule(
            id='default-high-opportunity',
            name='High Opportunity Score',
            alert_type=AlertType.OPPORTUNITY,
            coin_id='*',
            conditions=[
                {'metric': 'opportunity_score', 'condition': AlertCondition.ABOVE.value, 'value': 75}
            ],
            priority=AlertPriority.HIGH,
            cooldown_minutes=180
        ))

        # Whale accumulation alert
        self.add_rule(AlertRule(
            id='default-whale-accumulation',
            name='Whale Accumulation Detected',
            alert_type=AlertType.WHALE,
            coin_id='*',
            conditions=[
                {'metric': 'exchange_outflow_ratio', 'condition': AlertCondition.ABOVE.value, 'value': 1.5}
            ],
            priority=AlertPriority.MEDIUM,
            cooldown_minutes=360
        ))

        # Multi-factor buy signal
        self.add_rule(AlertRule(
            id='default-multi-factor-buy',
            name='Multi-Factor Buy Signal',
            alert_type=AlertType.COMPOSITE,
            coin_id='bitcoin',
            conditions=[
                {'metric': 'fear_greed', 'condition': AlertCondition.BELOW.value, 'value': 35},
                {'metric': 'rsi', 'condition': AlertCondition.BELOW.value, 'value': 40},
                {'metric': 'macd_histogram', 'condition': AlertCondition.ABOVE.value, 'value': 0}
            ],
            logic='AND',
            priority=AlertPriority.CRITICAL,
            cooldown_minutes=480
        ))

    def add_rule(self, rule: AlertRule) -> bool:
        """Add a new alert rule."""
        self._rules[rule.id] = rule
        logger.info(f"Added alert rule: {rule.name}")
        return True

    def remove_rule(self, rule_id: str) -> bool:
        """Remove an alert rule."""
        if rule_id in self._rules:
            del self._rules[rule_id]
            return True
        return False

    def get_rules(self, alert_type: Optional[AlertType] = None) -> List[Dict]:
        """Get all alert rules, optionally filtered by type."""
        rules = []
        for rule in self._rules.values():
            if alert_type is None or rule.alert_type == alert_type:
                rules.append({
                    'id': rule.id,
                    'name': rule.name,
                    'type': rule.alert_type.value,
                    'coin_id': rule.coin_id,
                    'conditions': rule.conditions,
                    'logic': rule.logic,
                    'priority': rule.priority.value,
                    'enabled': rule.enabled,
                    'cooldown_minutes': rule.cooldown_minutes,
                    'last_triggered': rule.last_triggered,
                    'trigger_count': rule.trigger_count
                })
        return rules

    def evaluate_rules(self, market_data: Dict) -> List[Alert]:
        """
        Evaluate all rules against current market data.

        Args:
            market_data: Dictionary containing all relevant metrics

        Returns:
            List of triggered alerts
        """
        triggered_alerts = []
        now = datetime.utcnow()

        for rule in self._rules.values():
            if not rule.enabled:
                continue

            # Check cooldown
            if rule.last_triggered:
                last_trigger = datetime.fromisoformat(rule.last_triggered)
                if now - last_trigger < timedelta(minutes=rule.cooldown_minutes):
                    continue

            # Evaluate conditions
            if self._evaluate_conditions(rule, market_data):
                alert = self._create_alert(rule, market_data)
                triggered_alerts.append(alert)
                self._alerts.append(alert)

                # Update rule
                rule.last_triggered = now.isoformat()
                rule.trigger_count += 1

                logger.info(f"Alert triggered: {rule.name}")

        return triggered_alerts

    def _evaluate_conditions(self, rule: AlertRule, data: Dict) -> bool:
        """Evaluate rule conditions against data."""
        results = []

        for condition in rule.conditions:
            metric = condition.get('metric')
            operator = condition.get('condition')
            threshold = condition.get('value')

            # Get actual value from data
            actual_value = self._get_metric_value(metric, data)

            if actual_value is None:
                results.append(False)
                continue

            # Evaluate condition
            if operator == AlertCondition.ABOVE.value:
                results.append(actual_value > threshold)
            elif operator == AlertCondition.BELOW.value:
                results.append(actual_value < threshold)
            elif operator == AlertCondition.EQUALS.value:
                results.append(actual_value == threshold)
            elif operator == AlertCondition.PERCENT_CHANGE.value:
                results.append(abs(actual_value) >= threshold)
            else:
                results.append(False)

        # Apply logic
        if rule.logic == 'AND':
            return all(results) and len(results) > 0
        else:  # OR
            return any(results)

    def _get_metric_value(self, metric: str, data: Dict) -> Optional[float]:
        """Extract metric value from data dictionary."""
        # Navigate nested structure
        parts = metric.split('.')
        value = data

        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None

        # Handle direct keys
        if value is None:
            value = data.get(metric)

        # Handle common metrics
        if metric == 'fear_greed':
            fg = data.get('fear_greed', {})
            return fg.get('value') if isinstance(fg, dict) else fg
        elif metric == 'rsi':
            rsi = data.get('rsi', {})
            return rsi.get('value') if isinstance(rsi, dict) else rsi
        elif metric == 'macd_histogram':
            macd = data.get('macd', {})
            return macd.get('histogram')
        elif metric == 'opportunity_score':
            return data.get('opportunity_score') or data.get('composite_score')
        elif metric == 'exchange_outflow_ratio':
            inflow = data.get('exchange_inflow', 1)
            outflow = data.get('exchange_outflow', 1)
            return outflow / inflow if inflow > 0 else 1

        return value if isinstance(value, (int, float)) else None

    def _create_alert(self, rule: AlertRule, data: Dict) -> Alert:
        """Create an alert instance from a triggered rule."""
        return Alert(
            id=str(uuid.uuid4()),
            rule_id=rule.id,
            rule_name=rule.name,
            alert_type=rule.alert_type.value,
            coin_id=rule.coin_id,
            priority=rule.priority.value,
            message=self._generate_alert_message(rule, data),
            details={
                'conditions': rule.conditions,
                'relevant_data': self._extract_relevant_data(rule, data)
            },
            triggered_at=datetime.utcnow().isoformat()
        )

    def _generate_alert_message(self, rule: AlertRule, data: Dict) -> str:
        """Generate human-readable alert message."""
        messages = {
            AlertType.SENTIMENT: self._sentiment_message,
            AlertType.TECHNICAL: self._technical_message,
            AlertType.WHALE: self._whale_message,
            AlertType.OPPORTUNITY: self._opportunity_message,
            AlertType.COMPOSITE: self._composite_message,
            AlertType.PRICE: self._price_message,
            AlertType.VOLUME: self._volume_message
        }

        generator = messages.get(rule.alert_type, lambda r, d: rule.name)
        return generator(rule, data)

    def _sentiment_message(self, rule: AlertRule, data: Dict) -> str:
        fg = data.get('fear_greed', {})
        value = fg.get('value', 'N/A') if isinstance(fg, dict) else fg
        classification = fg.get('classification', '') if isinstance(fg, dict) else ''
        return f"Market sentiment alert: Fear & Greed Index at {value} ({classification})"

    def _technical_message(self, rule: AlertRule, data: Dict) -> str:
        rsi = data.get('rsi', {})
        rsi_value = rsi.get('value', 'N/A') if isinstance(rsi, dict) else rsi
        return f"Technical alert: {rule.name} - RSI at {rsi_value}"

    def _whale_message(self, rule: AlertRule, data: Dict) -> str:
        return f"Whale activity detected: {rule.name}"

    def _opportunity_message(self, rule: AlertRule, data: Dict) -> str:
        score = data.get('opportunity_score') or data.get('composite_score', 'N/A')
        return f"Opportunity alert: Score reached {score}/100"

    def _composite_message(self, rule: AlertRule, data: Dict) -> str:
        return f"Multi-factor alert: {rule.name} - All conditions met"

    def _price_message(self, rule: AlertRule, data: Dict) -> str:
        price = data.get('current_price', 'N/A')
        return f"Price alert for {rule.coin_id}: ${price}"

    def _volume_message(self, rule: AlertRule, data: Dict) -> str:
        volume_change = data.get('volume_change_24h', 0)
        return f"Volume alert: {volume_change:+.1f}% change detected"

    def _extract_relevant_data(self, rule: AlertRule, data: Dict) -> Dict:
        """Extract relevant data for the alert."""
        relevant = {}
        for condition in rule.conditions:
            metric = condition.get('metric')
            value = self._get_metric_value(metric, data)
            relevant[metric] = value
        return relevant

    def get_recent_alerts(self, hours: int = 24, acknowledged: Optional[bool] = None) -> List[Dict]:
        """Get recent alerts."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)

        alerts = []
        for alert in reversed(self._alerts):  # Most recent first
            alert_time = datetime.fromisoformat(alert.triggered_at)
            if alert_time < cutoff:
                break

            if acknowledged is not None and alert.acknowledged != acknowledged:
                continue

            alerts.append({
                'id': alert.id,
                'rule_id': alert.rule_id,
                'rule_name': alert.rule_name,
                'type': alert.alert_type,
                'coin_id': alert.coin_id,
                'priority': alert.priority,
                'message': alert.message,
                'details': alert.details,
                'triggered_at': alert.triggered_at,
                'acknowledged': alert.acknowledged
            })

        return alerts[:50]  # Limit to 50 most recent

    def acknowledge_alert(self, alert_id: str) -> bool:
        """Mark an alert as acknowledged."""
        for alert in self._alerts:
            if alert.id == alert_id:
                alert.acknowledged = True
                return True
        return False

    def get_alert_summary(self) -> Dict:
        """Get summary of alert activity."""
        now = datetime.utcnow()
        last_24h = now - timedelta(hours=24)

        recent_alerts = [
            a for a in self._alerts
            if datetime.fromisoformat(a.triggered_at) >= last_24h
        ]

        by_type = {}
        by_priority = {}

        for alert in recent_alerts:
            by_type[alert.alert_type] = by_type.get(alert.alert_type, 0) + 1
            by_priority[alert.priority] = by_priority.get(alert.priority, 0) + 1

        unacknowledged = sum(1 for a in recent_alerts if not a.acknowledged)

        return {
            'timestamp': now.isoformat(),
            'total_24h': len(recent_alerts),
            'unacknowledged': unacknowledged,
            'by_type': by_type,
            'by_priority': by_priority,
            'active_rules': sum(1 for r in self._rules.values() if r.enabled),
            'total_rules': len(self._rules)
        }

    def create_custom_rule(
        self,
        name: str,
        alert_type: str,
        coin_id: str,
        conditions: List[Dict],
        logic: str = 'AND',
        priority: str = 'medium',
        cooldown_minutes: int = 60
    ) -> Dict:
        """Create a custom alert rule."""
        rule_id = f"custom-{uuid.uuid4().hex[:8]}"

        rule = AlertRule(
            id=rule_id,
            name=name,
            alert_type=AlertType(alert_type),
            coin_id=coin_id,
            conditions=conditions,
            logic=logic.upper(),
            priority=AlertPriority(priority),
            cooldown_minutes=cooldown_minutes
        )

        self.add_rule(rule)

        return {
            'id': rule_id,
            'name': name,
            'created': True
        }


# Global alert system instance
_system: Optional[AlertSystem] = None


def get_alert_system() -> AlertSystem:
    """Get or create the global alert system."""
    global _system
    if _system is None:
        _system = AlertSystem()
    return _system


# Convenience functions
def get_alert_rules() -> List[Dict]:
    """Get all alert rules."""
    return get_alert_system().get_rules()


def get_recent_alerts(hours: int = 24) -> List[Dict]:
    """Get recent alerts."""
    return get_alert_system().get_recent_alerts(hours)


def evaluate_alerts(market_data: Dict) -> List[Dict]:
    """Evaluate alert rules against market data."""
    alerts = get_alert_system().evaluate_rules(market_data)
    return [
        {
            'id': a.id,
            'rule_name': a.rule_name,
            'type': a.alert_type,
            'priority': a.priority,
            'message': a.message,
            'triggered_at': a.triggered_at
        }
        for a in alerts
    ]


def get_alert_summary() -> Dict:
    """Get alert system summary."""
    return get_alert_system().get_alert_summary()
