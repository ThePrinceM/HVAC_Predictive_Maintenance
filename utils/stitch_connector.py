"""
HVAC Fault Detection — Stitch Connector (Mock)
================================================
Simulated Stitch MCP integration layer for data refresh
and prediction logging. Replace with real Stitch SDK calls
when a production connector is available.
"""

import os
import time
import random
import datetime
import json
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# ─── Configuration ──────────────────────────────────────────────────────────────

STITCH_CONFIG = {
    "source_name": "hvac_sensor_feed",
    "destination": "prediction_warehouse",
    "max_retries": 3,
    "retry_delay_seconds": 2,
    "connection_timeout": 10,
}

# Simulated connection state
_connection_state = {
    "connected": False,
    "last_refresh": None,
    "last_error": None,
}


# ─── Connection Management ──────────────────────────────────────────────────────

class StitchConnectionError(Exception):
    """Raised when Stitch connection fails."""
    pass


def connect(config: Optional[Dict] = None) -> bool:
    """
    Establish connection to Stitch data source.
    (Simulated — always succeeds after brief delay)
    """
    cfg = config or STITCH_CONFIG
    time.sleep(0.5)  # Simulate connection handshake

    # Simulate occasional connection failure (10% chance)
    if random.random() < 0.1:
        _connection_state["connected"] = False
        _connection_state["last_error"] = "Connection timeout — Stitch source unreachable"
        raise StitchConnectionError(_connection_state["last_error"])

    _connection_state["connected"] = True
    _connection_state["last_error"] = None
    logger.info(f"Connected to Stitch source: {cfg['source_name']}")
    return True


def is_connected() -> bool:
    """Check if currently connected to Stitch."""
    return _connection_state.get("connected", False)


# ─── Data Refresh ───────────────────────────────────────────────────────────────

def refresh_data(
    target_path: str,
    source_path: Optional[str] = None,
    max_retries: int = 3,
    progress_callback=None,
) -> Dict:
    """
    Refresh HVAC dataset from Stitch source.

    In this mock implementation, copies from source_path to target_path
    with simulated network delay and retry logic.

    Parameters
    ----------
    target_path : str
        Where to save the refreshed data.
    source_path : str, optional
        Local fallback source (used in mock mode).
    max_retries : int
        Number of retry attempts on failure.
    progress_callback : callable, optional
        Function(status_string) for UI updates.

    Returns
    -------
    dict
        status: "success" or "error"
        message: Description of result
        timestamp: When refresh completed
        rows_fetched: Number of rows in refreshed data
    """
    def _status(msg):
        if progress_callback:
            progress_callback(msg)

    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            _status(f"Connecting to Stitch (attempt {attempt}/{max_retries})...")

            # Attempt connection
            connect()

            _status("Fetching data from HVAC sensor feed...")
            time.sleep(1.0)  # Simulate data transfer

            # In mock mode, copy from source if different from target
            if source_path and source_path != target_path and os.path.exists(source_path):
                import shutil
                shutil.copy2(source_path, target_path)
            elif not os.path.exists(target_path):
                raise FileNotFoundError(f"No data source available at {target_path}")

            # Count rows
            row_count = sum(1 for _ in open(target_path, encoding="utf-8")) - 1

            refresh_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            _connection_state["last_refresh"] = refresh_time

            _status("Data refresh complete!")
            return {
                "status": "success",
                "message": f"Successfully refreshed {row_count:,} rows from Stitch",
                "timestamp": refresh_time,
                "rows_fetched": row_count,
                "attempts": attempt,
            }

        except StitchConnectionError as e:
            last_error = str(e)
            _status(f"Connection failed (attempt {attempt}). Retrying in {STITCH_CONFIG['retry_delay_seconds']}s...")
            if attempt < max_retries:
                time.sleep(STITCH_CONFIG["retry_delay_seconds"])
            continue

        except Exception as e:
            last_error = str(e)
            _status(f"Error: {e}")
            break

    return {
        "status": "error",
        "message": f"Data refresh failed after {max_retries} attempts: {last_error}",
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "rows_fetched": 0,
        "attempts": max_retries,
    }


# ─── Prediction Logging ────────────────────────────────────────────────────────

_prediction_log = []


def log_prediction(prediction_data: Dict) -> Dict:
    """
    Log a prediction event to the Stitch destination warehouse.

    In this mock implementation, appends to an in-memory list
    and optionally to a local JSON file.

    Parameters
    ----------
    prediction_data : dict
        Must include: predicted_class, confidence, input_features, timestamp

    Returns
    -------
    dict
        status, message, event_id
    """
    try:
        event = {
            "event_id": f"pred_{int(time.time() * 1000)}_{random.randint(100, 999)}",
            "timestamp": datetime.datetime.now().isoformat(),
            "predicted_class": prediction_data.get("predicted_class", "unknown"),
            "confidence": prediction_data.get("confidence", 0.0),
            "input_features": prediction_data.get("input_features", {}),
            "model_version": prediction_data.get("model_version", "v1"),
        }

        _prediction_log.append(event)

        # Persist to local file as backup
        log_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        log_file = os.path.join(log_dir, "prediction_log.json")

        existing = []
        if os.path.exists(log_file):
            try:
                with open(log_file, "r") as f:
                    existing = json.load(f)
            except (json.JSONDecodeError, IOError):
                existing = []

        existing.append(event)

        # Keep last 1000 events
        if len(existing) > 1000:
            existing = existing[-1000:]

        with open(log_file, "w") as f:
            json.dump(existing, f, indent=2)

        return {
            "status": "success",
            "message": "Prediction logged to Stitch destination",
            "event_id": event["event_id"],
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to log prediction: {e}",
            "event_id": None,
        }


def get_prediction_log() -> list:
    """Return the in-memory prediction log."""
    return _prediction_log.copy()


def get_connection_status() -> Dict:
    """Return current Stitch connection state."""
    return {
        "connected": _connection_state.get("connected", False),
        "last_refresh": _connection_state.get("last_refresh"),
        "last_error": _connection_state.get("last_error"),
        "source": STITCH_CONFIG["source_name"],
        "destination": STITCH_CONFIG["destination"],
    }
