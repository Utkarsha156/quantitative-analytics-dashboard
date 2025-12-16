"""
Alert system for custom rule-based notifications.
"""
import logging
from typing import Dict, List, Callable, Optional
from datetime import datetime
import threading
import time

logger = logging.getLogger(__name__)


class AlertRule:
    """Represents a single alert rule."""
    
    def __init__(self, rule_id: str, name: str, condition: str, 
                 symbol: Optional[str] = None, enabled: bool = True):
        """
        Initialize alert rule.
        
        Args:
            rule_id: Unique identifier
            name: Human-readable name
            condition: Python expression to evaluate (e.g., "zscore > 2")
            symbol: Symbol to monitor (None for all symbols)
            enabled: Whether rule is active
        """
        self.rule_id = rule_id
        self.name = name
        self.condition = condition
        self.symbol = symbol
        self.enabled = enabled
        self.last_triggered = None
        self.trigger_count = 0
    
    def evaluate(self, context: Dict) -> bool:
        """
        Evaluate the alert condition.
        
        Args:
            context: Dictionary with variables available for condition evaluation
                    (e.g., {'zscore': 2.5, 'price': 50000, 'symbol': 'btcusdt'})
        
        Returns:
            True if condition is met, False otherwise
        """
        if not self.enabled:
            return False
        
        if self.symbol and context.get('symbol') != self.symbol:
            return False
        
        try:
            # Safe evaluation of condition
            result = eval(self.condition, {"__builtins__": {}}, context)
            return bool(result)
        except Exception as e:
            logger.error(f"Error evaluating alert rule {self.rule_id}: {e}")
            return False
    
    def trigger(self):
        """Mark rule as triggered."""
        self.last_triggered = datetime.now()
        self.trigger_count += 1


class AlertManager:
    """
    Manages alert rules and triggers notifications.
    """
    
    def __init__(self, callback: Optional[Callable] = None):
        """
        Initialize alert manager.
        
        Args:
            callback: Function to call when alert is triggered: callback(alert_rule, context)
        """
        self.rules: Dict[str, AlertRule] = {}
        self.callback = callback
        self._lock = threading.Lock()
        self.active_alerts: List[Dict] = []  # Store recent alerts
    
    def add_rule(self, rule: AlertRule):
        """Add an alert rule."""
        with self._lock:
            self.rules[rule.rule_id] = rule
            logger.info(f"Added alert rule: {rule.name} ({rule.rule_id})")
    
    def remove_rule(self, rule_id: str):
        """Remove an alert rule."""
        with self._lock:
            if rule_id in self.rules:
                del self.rules[rule_id]
                logger.info(f"Removed alert rule: {rule_id}")
    
    def update_rule(self, rule_id: str, **kwargs):
        """Update an alert rule."""
        with self._lock:
            if rule_id in self.rules:
                rule = self.rules[rule_id]
                for key, value in kwargs.items():
                    if hasattr(rule, key):
                        setattr(rule, key, value)
    
    def get_rules(self) -> List[AlertRule]:
        """Get all alert rules."""
        with self._lock:
            return list(self.rules.values())
    
    def check_alerts(self, context: Dict):
        """
        Check all alert rules against the given context.
        
        Args:
            context: Dictionary with variables for condition evaluation
        """
        with self._lock:
            for rule in self.rules.values():
                if rule.evaluate(context):
                    rule.trigger()
                    alert_info = {
                        'rule_id': rule.rule_id,
                        'name': rule.name,
                        'symbol': context.get('symbol', 'N/A'),
                        'timestamp': datetime.now().isoformat(),
                        'context': context.copy()
                    }
                    self.active_alerts.append(alert_info)
                    
                    # Keep only last 100 alerts
                    if len(self.active_alerts) > 100:
                        self.active_alerts.pop(0)
                    
                    if self.callback:
                        try:
                            self.callback(rule, context)
                        except Exception as e:
                            logger.error(f"Error in alert callback: {e}")
    
    def get_active_alerts(self, limit: int = 50) -> List[Dict]:
        """Get recent active alerts."""
        with self._lock:
            return self.active_alerts[-limit:]

