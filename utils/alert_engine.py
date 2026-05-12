"""
HVAC Fault Detection — Alert Engine
======================================
Rule-based alert triggers, AI explanations, and recommended actions.
"""

import datetime
from typing import Dict, List

# ─── Alert Rules ────────────────────────────────────────────────────────────

ALERT_RULES = [
    {"id": "high_comp_current", "label": "High Compressor Current", "condition": lambda r: r.get("compressor_current_A", 0) > 22, "severity": "critical", "message": "Current is above normal range"},
    {"id": "low_comp_current", "label": "Low Compressor Current", "condition": lambda r: r.get("compressor_current_A", 99) < 6, "severity": "warning", "message": "Current is below normal range"},
    {"id": "high_discharge_psi", "label": "High Discharge Pressure", "condition": lambda r: r.get("discharge_pressure_psi", 0) > 300, "severity": "warning", "message": "Discharge pressure is elevated"},
    {"id": "low_suction_psi", "label": "Low Suction Pressure", "condition": lambda r: r.get("suction_pressure_psi", 99) < 35, "severity": "warning", "message": "Suction pressure is critically low"},
    {"id": "high_supply_temp", "label": "High Supply Temperature", "condition": lambda r: r.get("supply_temp_C", 0) > 25, "severity": "warning", "message": "Supply air temp is above setpoint"},
    {"id": "high_outdoor_temp", "label": "High Outdoor Temperature", "condition": lambda r: r.get("outdoor_temp_C", 0) > 45, "severity": "info", "message": "Outdoor temperature is extreme"},
    {"id": "low_fan_speed", "label": "Low Fan Speed", "condition": lambda r: r.get("fan_speed_RPM", 9999) < 900, "severity": "critical", "message": "Fan speed below minimum threshold"},
    {"id": "high_vibration", "label": "High Vibration Level", "condition": lambda r: r.get("vibration_mm_s", 0) > 1.0, "severity": "critical", "message": "Vibration exceeds safe operating limit"},
    {"id": "low_filter_health", "label": "Filter Health Degraded", "condition": lambda r: r.get("filter_health", 1) < 0.6, "severity": "warning", "message": "Air filter needs replacement"},
    {"id": "low_airflow", "label": "Airflow Dropping", "condition": lambda r: r.get("airflow_rate", 99) < 2.5, "severity": "warning", "message": "Possible filter clogging"},
    {"id": "high_return_temp", "label": "High Return Temperature", "condition": lambda r: r.get("return_temp_C", 0) > 30, "severity": "warning", "message": "Return air temp is elevated"},
    {"id": "low_refrig_psi", "label": "Low Refrigerant Pressure", "condition": lambda r: r.get("refrigerant_pressure_psi", 999) < 100, "severity": "critical", "message": "Possible refrigerant leak detected"},
    {"id": "extreme_damper", "label": "Damper Position Abnormal", "condition": lambda r: r.get("damper_position_%", 50) > 95 or r.get("damper_position_%", 50) < 5, "severity": "info", "message": "Damper at extreme position"},
]

SEVERITY_ICONS = {"critical": "\U0001f534", "warning": "\u26a0\ufe0f", "info": "\u2139\ufe0f"}


def evaluate_alerts(reading: dict) -> List[dict]:
    """Check all rules against a sensor reading. Return list of triggered alerts."""
    triggered = []
    now = datetime.datetime.now().strftime("%I:%M %p")
    for rule in ALERT_RULES:
        try:
            if rule["condition"](reading):
                sensor_key = rule["id"].split("_", 1)[-1] if "_" in rule["id"] else ""
                triggered.append({
                    "id": rule["id"],
                    "label": rule["label"],
                    "message": rule["message"],
                    "severity": rule["severity"],
                    "value": reading.get(sensor_key, ""),
                    "timestamp": now,
                })
        except Exception:
            pass
    return triggered


# ─── AI Explanations (keyed by fault class) ────────────────────────────────

AI_EXPLANATIONS: Dict[str, List[tuple]] = {
    "Normal": [
        ("#22d46b", "All sensor readings are within normal operating parameters."),
        ("#22d46b", "Compressor current and pressures are stable and balanced."),
        ("#22d46b", "Airflow rate and filter health are at optimal levels."),
    ],
    "Compressor_Fault": [
        ("#e84040", "Compressor current is higher than normal, indicating possible overload."),
        ("#f5a623", "Discharge temperature is high due to increased compressor load."),
        ("#f5a623", "Airflow rate is decreasing, possibly caused by a dirty filter."),
    ],
    "Filter_Clog": [
        ("#e84040", "Filter health has degraded significantly, restricting airflow."),
        ("#f5a623", "Supply air temperature is rising due to reduced air circulation."),
        ("#f5a623", "Compressor is working harder to compensate for restricted airflow."),
    ],
    "Refrigerant_Leak": [
        ("#e84040", "Refrigerant pressure is dropping below normal operating range."),
        ("#f5a623", "Suction and discharge pressures are both declining steadily."),
        ("#f5a623", "Supply temperature is rising as cooling capacity decreases."),
    ],
    "Fan_Fault": [
        ("#e84040", "Fan speed has dropped significantly below normal RPM."),
        ("#f5a623", "Airflow rate is decreasing proportionally with fan speed."),
        ("#f5a623", "Supply temperature rising due to inadequate air movement."),
    ],
    "Electrical_Issue": [
        ("#e84040", "Electrical supply to fan and compressor is intermittent."),
        ("#f5a623", "Compressor current is fluctuating below normal operating range."),
        ("#f5a623", "Multiple components showing reduced performance simultaneously."),
    ],
    "Control_Sensor_Fault": [
        ("#e84040", "Supply temperature sensor reporting abnormal spike readings."),
        ("#f5a623", "Sensor readings inconsistent with other system parameters."),
        ("#f5a623", "Control system may be receiving erroneous feedback signals."),
    ],
}

# ─── Recommended Actions (keyed by fault class) ────────────────────────────

RECOMMENDED_ACTIONS: Dict[str, List[str]] = {
    "Normal": [
        "Continue regular preventive maintenance schedule.",
        "Monitor sensor trends for early anomaly detection.",
        "Check refrigerant level and pressure monthly.",
        "Ensure proper airflow and ventilation around the unit.",
    ],
    "Compressor_Fault": [
        "Inspect compressor and check for any overload condition.",
        "Clean or replace air filter immediately.",
        "Check refrigerant level and pressure.",
        "Ensure proper airflow and ventilation around the unit.",
    ],
    "Filter_Clog": [
        "Replace or clean the air filter immediately.",
        "Check ductwork for additional obstructions.",
        "Monitor supply temperature after filter change.",
        "Schedule preventive filter replacement every 30 days.",
    ],
    "Refrigerant_Leak": [
        "Perform refrigerant leak detection test immediately.",
        "Check all refrigerant line connections and fittings.",
        "Inspect evaporator and condenser coils for damage.",
        "Do not operate system until leak is repaired.",
    ],
    "Fan_Fault": [
        "Inspect fan motor bearings and belt tension.",
        "Check fan blade for damage or imbalance.",
        "Verify electrical connections to fan motor.",
        "Test fan motor capacitor and starter relay.",
    ],
    "Electrical_Issue": [
        "Check main electrical supply and circuit breakers.",
        "Inspect all wiring connections for loose contacts.",
        "Test voltage and current at component terminals.",
        "Verify control board and relay functionality.",
    ],
    "Control_Sensor_Fault": [
        "Calibrate or replace the supply temperature sensor.",
        "Check sensor wiring for damage or interference.",
        "Verify sensor readings against manual measurements.",
        "Update control system firmware if available.",
    ],
}

# ─── Fault-to-component mapping ────────────────────────────────────────────

FAULT_COMPONENT = {
    "Normal": "ALL SYSTEMS",
    "Compressor_Fault": "COMPRESSOR",
    "Filter_Clog": "AIR FILTER",
    "Refrigerant_Leak": "REFRIGERANT",
    "Fan_Fault": "SUPPLY FAN",
    "Electrical_Issue": "ELECTRICAL",
    "Control_Sensor_Fault": "SENSOR",
}

FAULT_EMOJI = {
    "Normal": "\u2705",
    "Compressor_Fault": "\U0001f6a8",
    "Filter_Clog": "\U0001fa78",
    "Refrigerant_Leak": "\U0001f4a7",
    "Fan_Fault": "\U0001f32c\ufe0f",
    "Electrical_Issue": "\u26a1",
    "Control_Sensor_Fault": "\U0001f4e1",
}


if __name__ == "__main__":
    sample = {"compressor_current_A": 25, "discharge_pressure_psi": 310,
              "suction_pressure_psi": 55, "supply_temp_C": 16, "outdoor_temp_C": 36,
              "fan_speed_RPM": 1500, "vibration_mm_s": 0.2, "filter_health": 1.0,
              "airflow_rate": 5.0, "return_temp_C": 24, "refrigerant_pressure_psi": 170,
              "damper_position_%": 30}
    alerts = evaluate_alerts(sample)
    print(f"{len(ALERT_RULES)} rules loaded, {len(alerts)} triggered")
    for a in alerts:
        print(f"  [{a['severity']}] {a['label']}: {a['message']}")
