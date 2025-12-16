"""
Main application entry point.
Single-command execution for the analytics application.

Usage: python app.py

This script starts both the backend data processor and the Streamlit frontend.
"""
import logging
import subprocess
import sys
import time
import threading
from pathlib import Path

from backend.storage import DataStorage
from backend.data_processor import DataProcessor
from backend.alerts import AlertManager, AlertRule
from config import DEFAULT_SYMBOLS, DB_PATH

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('analytics.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Global processor instance
processor = None


def alert_callback(rule, context):
    """Callback function for triggered alerts."""
    logger.info(f"ALERT TRIGGERED: {rule.name} - Symbol: {context.get('symbol')} - Condition: {rule.condition}")


def start_backend():
    """Start the backend data processing pipeline in a background thread."""
    global processor
    
    logger.info("Initializing backend components...")
    
    # Initialize components
    storage = DataStorage(DB_PATH)
    alert_manager = AlertManager(callback=alert_callback)
    
    # Add some default alert rules as examples
    default_rules = [
        AlertRule(
            rule_id="default_zscore_high",
            name="High Z-Score",
            condition="zscore > 2",
            enabled=True
        ),
        AlertRule(
            rule_id="default_zscore_low",
            name="Low Z-Score",
            condition="zscore < -2",
            enabled=True
        ),
    ]
    
    for rule in default_rules:
        alert_manager.add_rule(rule)
    
    # Initialize data processor
    symbols = DEFAULT_SYMBOLS
    processor = DataProcessor(symbols, storage, alert_manager)
    
    # Start data processing
    processor.start()
    logger.info(f"Backend started for symbols: {symbols}")
    
    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down backend...")
        if processor:
            processor.stop()


def main():
    """Main application entry point."""
    logger.info("Starting Analytics Application...")
    
    # Start backend in background thread
    backend_thread = threading.Thread(target=start_backend, daemon=True)
    backend_thread.start()
    
    # Wait a moment for backend to initialize
    logger.info("Waiting for backend initialization...")
    time.sleep(3)
    
    # Launch Streamlit dashboard
    logger.info("Launching Streamlit dashboard...")
    logger.info("Dashboard will be available at http://localhost:8501")
    
    dashboard_path = Path(__file__).parent / "frontend" / "dashboard.py"
    
    # Run Streamlit (this will block)
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", str(dashboard_path),
            "--server.port=8501"
        ])
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        if processor:
            processor.stop()
        sys.exit(0)


if __name__ == "__main__":
    main()
