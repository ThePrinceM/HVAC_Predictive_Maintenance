"""
HVAC Fault Detection — Sensor Simulator
=========================================
Wraps generator.py physics into a streaming API for the live dashboard.
"""

import collections
import datetime
import random
import pandas as pd
import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from model.generator import get_baseline_reading, apply_fault_profile

FAULT_TYPES = [
    "Filter_Clog", "Refrigerant_Leak", "Compressor_Fault",
    "Fan_Fault", "Electrical_Issue", "Control_Sensor_Fault",
]


class SensorSimulator:
    """Real-time HVAC sensor simulator with fault injection."""

    def __init__(self, mode: str = "auto"):
        self._mode = mode
        self._fault_override = None
        self._tick = 0
        self._buffer = collections.deque(maxlen=200)
        # Auto-mode state
        self._fault_active = None
        self._fault_start = 0
        self._fault_duration = 0
        self._next_fault_tick = random.randint(50, 200)
        
        # Random manual mode state
        self._current_random_fault = None
        self._random_fault_interval = random.randint(8, 25)


    # ── Properties ──────────────────────────────────────────────────────────

    @property
    def mode(self) -> str:
        return self._mode

    @mode.setter
    def mode(self, value: str):
        if value not in ("normal", "auto", "manual"):
            raise ValueError(f"Invalid mode: {value}")
        self._mode = value
        if value != "manual":
            self._fault_override = None

    @property
    def fault_override(self):
        return self._fault_override

    @fault_override.setter
    def fault_override(self, value):
        self._fault_override = value

    # ── Core Methods ────────────────────────────────────────────────────────

    def next_reading(self, fault_override: str = None) -> dict:
        """Return one sensor reading dict with optional fault injection."""
        reading = get_baseline_reading(self._tick)
        fault_label = "Normal"

        fo = fault_override or self._fault_override

        if fo == "random":
            # Pick a new random fault every self._random_fault_interval ticks
            if self._tick % self._random_fault_interval == 0:
                self._current_random_fault = random.choice(FAULT_TYPES)
                self._random_fault_interval = random.randint(8, 25)
            fault = self._current_random_fault
            frac = min(1.0, (self._tick % self._random_fault_interval) / 5.0)
            reading = apply_fault_profile(reading, fault, frac)
            fault_label = fault
        elif fo and fo != "Normal":
            reading = apply_fault_profile(reading, fo, frac=1.0)
            fault_label = fo
        elif self._mode == "auto":
            reading, fault_label = self._auto_step(reading)
        elif self._mode == "normal":
            pass  # pure baseline

        # Add metadata
        reading["fault"] = fault_label
        reading["timestamp_str"] = datetime.datetime.now().strftime("%I:%M:%S %p")
        reading["tick"] = self._tick

        self._buffer.append(reading)
        self._tick += 1
        return reading

    def _auto_step(self, reading: dict):
        """Handle auto-mode fault scheduling."""
        if self._fault_active:
            elapsed = self._tick - self._fault_start
            if elapsed >= self._fault_duration:
                # Fault period ended
                self._fault_active = None
                self._next_fault_tick = self._tick + random.randint(50, 200)
                return reading, "Normal"
            else:
                frac = min(elapsed / max(self._fault_duration - 1, 1), 1.0)
                return apply_fault_profile(reading, self._fault_active, frac), self._fault_active
        else:
            if self._tick >= self._next_fault_tick:
                self._fault_active = random.choice(FAULT_TYPES)
                self._fault_start = self._tick
                self._fault_duration = random.randint(10, 30)
                return apply_fault_profile(reading, self._fault_active, 0.0), self._fault_active
            return reading, "Normal"

    def get_buffer(self, n: int = 100) -> pd.DataFrame:
        """Return last n readings as DataFrame."""
        data = list(self._buffer)
        if len(data) > n:
            data = data[-n:]
        if not data:
            return pd.DataFrame()
        return pd.DataFrame(data)

    def reset(self):
        """Clear buffer and reset state."""
        self._buffer.clear()
        self._tick = 0
        self._fault_active = None
        self._fault_start = 0
        self._fault_duration = 0
        self._next_fault_tick = random.randint(50, 200)


if __name__ == "__main__":
    sim = SensorSimulator(mode="auto")
    for i in range(10):
        r = sim.next_reading()
        print(f"Tick {r['tick']:3d} | {r['fault']:22s} | supply={r['supply_temp_C']:.1f} | current={r['compressor_current_A']:.1f}")
