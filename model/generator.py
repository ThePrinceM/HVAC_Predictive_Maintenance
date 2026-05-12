"""
HVAC Synthetic Data Generator
==============================
Provides pure functions for baseline sensor readings and fault injection.
The CSV generation script is guarded under __main__.
"""

import numpy as np
import pandas as pd


# ─── Pure Functions (importable) ────────────────────────────────────────────

def get_baseline_reading(t: int) -> dict:
    """Generate one Normal baseline sensor reading at time index t."""
    outdoor = 36 + 5 * np.sin(2 * np.pi * t / 1440) + np.random.normal(0, 0.5)
    supply = 16 + 2 * np.sin(2 * np.pi * t / 720) + 0.1 * (outdoor - 36) + np.random.normal(0, 0.3)
    ret = supply + (8 + np.random.normal(0, 0.5))
    suction = 60 + 5 * np.sin(2 * np.pi * t / 1000) + np.random.normal(0, 1)
    discharge = 210 + 10 * np.sin(2 * np.pi * t / 1000 + 0.5) + np.random.normal(0, 2)
    discharge = max(discharge, suction + 10)
    comp_current = 12 + 3 * np.sin(2 * np.pi * t / 1500) + np.random.normal(0, 1.0)
    fan_speed = 1500 + 50 * np.sin(2 * np.pi * t / 800) + np.random.normal(0, 30)
    vibration = 0.2 + 0.05 * np.sin(2 * np.pi * t / 500) + np.random.normal(0, 0.02)
    unit_age = 7.5
    filter_health = 1.0
    airflow = 5.0
    load_proxy = max(ret - supply, 0)
    damper = 20 + 0.8 * (outdoor - 30) + 1.5 * (load_proxy / 10.0) + np.random.normal(0, 3)
    damper = float(np.clip(damper, 0, 100))
    refrig = 0.3 * suction + 0.7 * discharge

    return {
        "return_temp_C": round(ret, 1),
        "supply_temp_C": round(supply, 1),
        "outdoor_temp_C": round(outdoor, 1),
        "suction_pressure_psi": round(suction),
        "discharge_pressure_psi": round(discharge),
        "compressor_current_A": round(comp_current, 1),
        "fan_speed_RPM": round(fan_speed),
        "vibration_mm_s": round(vibration, 2),
        "unit_age": round(unit_age, 1),
        "refrigerant_pressure_psi": round(refrig),
        "filter_health": round(filter_health, 2),
        "airflow_rate": round(airflow, 2),
        "damper_position_%": round(damper, 1),
    }


def apply_fault_profile(reading: dict, fault: str, frac: float = 1.0) -> dict:
    """
    Apply a fault's sensor perturbation to a baseline reading (pure function).
    frac: 0.0 = just started, 1.0 = fully developed fault.
    Returns a NEW dict with modified values.
    """
    r = reading.copy()

    def _lerp(base, target):
        return base + (target - base) * frac

    if fault == "Normal":
        return r

    elif fault == "Filter_Clog":
        r["filter_health"] = _lerp(reading["filter_health"], 0.5)
        r["airflow_rate"] = _lerp(reading["airflow_rate"], reading["airflow_rate"] * 0.55)
        r["supply_temp_C"] = _lerp(reading["supply_temp_C"], reading["supply_temp_C"] + 3.0)
        r["return_temp_C"] = _lerp(reading["return_temp_C"], reading["return_temp_C"] + 1.0)
        r["suction_pressure_psi"] = _lerp(reading["suction_pressure_psi"], reading["suction_pressure_psi"] - 10.0)
        r["discharge_pressure_psi"] = _lerp(reading["discharge_pressure_psi"], reading["discharge_pressure_psi"] + 10.0)
        r["compressor_current_A"] = _lerp(reading["compressor_current_A"], reading["compressor_current_A"] * 1.3)
        r["fan_speed_RPM"] = _lerp(reading["fan_speed_RPM"], reading["fan_speed_RPM"] + 100)
        r["vibration_mm_s"] = _lerp(reading["vibration_mm_s"], reading["vibration_mm_s"] + 0.05)
        r["damper_position_%"] = float(np.clip(reading["damper_position_%"] - (2 + 3 * frac), 0, 100))
        r["refrigerant_pressure_psi"] = round(r["suction_pressure_psi"] * 0.3 + r["discharge_pressure_psi"] * 0.7)

    elif fault == "Refrigerant_Leak":
        r["refrigerant_pressure_psi"] = _lerp(reading["refrigerant_pressure_psi"], reading["refrigerant_pressure_psi"] * 0.7)
        r["suction_pressure_psi"] = _lerp(reading["suction_pressure_psi"], reading["suction_pressure_psi"] * 0.8)
        r["discharge_pressure_psi"] = _lerp(reading["discharge_pressure_psi"], reading["discharge_pressure_psi"] * 0.8)
        r["compressor_current_A"] = _lerp(reading["compressor_current_A"], reading["compressor_current_A"] * 1.2)
        r["supply_temp_C"] = _lerp(reading["supply_temp_C"], reading["supply_temp_C"] + 5.0)
        r["return_temp_C"] = _lerp(reading["return_temp_C"], reading["return_temp_C"] + 1.0)

    elif fault == "Compressor_Fault":
        r["compressor_current_A"] = reading["compressor_current_A"] * 2.0
        r["vibration_mm_s"] = reading["vibration_mm_s"] + 1.0
        r["supply_temp_C"] = reading["outdoor_temp_C"]
        r["suction_pressure_psi"] = 30.0
        r["discharge_pressure_psi"] = 30.0

    elif fault == "Fan_Fault":
        r["fan_speed_RPM"] = _lerp(reading["fan_speed_RPM"], reading["fan_speed_RPM"] * 0.5)
        r["airflow_rate"] = _lerp(reading["airflow_rate"], reading["airflow_rate"] * 0.5)
        r["compressor_current_A"] = _lerp(reading["compressor_current_A"], reading["compressor_current_A"] * 0.5)
        r["supply_temp_C"] = _lerp(reading["supply_temp_C"], reading["supply_temp_C"] + 5.0)
        r["return_temp_C"] = _lerp(reading["return_temp_C"], reading["return_temp_C"] + 1.0)
        r["suction_pressure_psi"] = _lerp(reading["suction_pressure_psi"], reading["suction_pressure_psi"] * 0.8)
        r["discharge_pressure_psi"] = _lerp(reading["discharge_pressure_psi"], reading["discharge_pressure_psi"] * 0.9)

    elif fault == "Electrical_Issue":
        r["fan_speed_RPM"] = _lerp(reading["fan_speed_RPM"], reading["fan_speed_RPM"] * 0.5)
        r["compressor_current_A"] = _lerp(reading["compressor_current_A"], reading["compressor_current_A"] * 0.5)
        r["airflow_rate"] = _lerp(reading["airflow_rate"], reading["airflow_rate"] * 0.5)
        r["supply_temp_C"] = _lerp(reading["supply_temp_C"], reading["supply_temp_C"] + 3.0)
        r["return_temp_C"] = _lerp(reading["return_temp_C"], reading["return_temp_C"] + 1.0)
        r["suction_pressure_psi"] = _lerp(reading["suction_pressure_psi"], reading["suction_pressure_psi"] * 0.8)
        r["discharge_pressure_psi"] = _lerp(reading["discharge_pressure_psi"], reading["discharge_pressure_psi"] * 0.8)

    elif fault == "Control_Sensor_Fault":
        r["supply_temp_C"] = reading["supply_temp_C"] + 15.0 * frac
        r["damper_position_%"] = float(np.clip(reading["damper_position_%"] + np.random.normal(0, 1), 0, 100))

    # Round all numeric values
    for k, v in r.items():
        if isinstance(v, (float, np.floating)):
            r[k] = round(float(v), 2)

    return r


# ─── CSV Generation Script (unchanged) ─────────────────────────────────────

if __name__ == "__main__":
    np.random.seed(42)

    N = 10000
    t = np.arange(N)

    outdoor = 36 + 5 * np.sin(2 * np.pi * t / 1440) + np.random.normal(0, 0.5, N)
    supply = 16 + 2 * np.sin(2 * np.pi * t / 720) + 0.1 * (outdoor - 36) + np.random.normal(0, 0.3, N)
    returnt = supply + (8 + np.random.normal(0, 0.5, N))
    suction = 60 + 5 * np.sin(2 * np.pi * t / 1000) + np.random.normal(0, 1, N)
    discharge = 210 + 10 * np.sin(2 * np.pi * t / 1000 + 0.5) + np.random.normal(0, 2, N)
    discharge = np.maximum(discharge, suction + 10)
    comp_current = 12 + 3 * np.sin(2 * np.pi * t / 1500) + np.random.normal(0, 1.0, N)
    fan_speed = 1500 + 50 * np.sin(2 * np.pi * t / 800) + np.random.normal(0, 30, N)
    vibration = 0.2 + 0.05 * np.sin(2 * np.pi * t / 500) + np.random.normal(0, 0.02, N)
    unit_age = np.random.uniform(0, 15, N)
    filter_health = np.ones(N)
    airflow = np.ones(N) * 5.0
    load_proxy = np.clip((returnt - supply), 0, None)
    damper_position = (20 + 0.8 * (outdoor - 30) + 1.5 * (load_proxy / 10.0) + np.random.normal(0, 3, N))
    damper_position = np.clip(damper_position, 0, 100)
    refrig_pressure = 0.3 * suction + 0.7 * discharge

    df = pd.DataFrame({
        'timestamp': t + 1,
        'return_temp_C': np.round(returnt, 1),
        'supply_temp_C': np.round(supply, 1),
        'outdoor_temp_C': np.round(outdoor, 1),
        'suction_pressure_psi': np.round(suction),
        'discharge_pressure_psi': np.round(discharge),
        'compressor_current_A': np.round(comp_current, 1),
        'fan_speed_RPM': np.round(fan_speed),
        'vibration_mm_s': np.round(vibration, 2),
        'unit_age': np.round(unit_age, 1),
        'refrigerant_pressure_psi': np.round(refrig_pressure),
        'filter_health': np.round(filter_health, 2),
        'airflow_rate': np.round(airflow, 2),
        'damper_position_%': np.round(damper_position, 1),
        'fault': 'Normal'
    })

    event_lengths = {
        'Filter_Clog': 10, 'Refrigerant_Leak': 10, 'Compressor_Fault': 10,
        'Fan_Fault': 10, 'Electrical_Issue': 20, 'Control_Sensor_Fault': 5
    }
    event_counts = {
        'Filter_Clog': 50, 'Refrigerant_Leak': 50, 'Compressor_Fault': 25,
        'Fan_Fault': 25, 'Electrical_Issue': 20, 'Control_Sensor_Fault': 20
    }

    occupied = np.zeros(N, dtype=bool)
    events = []

    for fault, cnt in event_counts.items():
        length = event_lengths[fault]
        for _ in range(cnt):
            while True:
                start = np.random.randint(0, N - length)
                end = start + length
                if start > 0 and occupied[start - 1]:
                    continue
                if end < N and occupied[end]:
                    continue
                if occupied[start:end].any():
                    continue
                occupied[start:end] = True
                events.append((start, end, fault))
                break

    def inject_fault(df_src, df_target, start, end, fault):
        base = df_src.loc[start - 1] if start > 0 else df_src.loc[start]
        length = end - start
        if fault == 'Filter_Clog':
            tgt_filter = 0.5; tgt_airflow = base.airflow_rate * 0.55
            tgt_supply = base.supply_temp_C + 3.0; tgt_return = base.return_temp_C + 1.0
            tgt_suction = base.suction_pressure_psi - 10.0; tgt_discharge = base.discharge_pressure_psi + 10.0
            tgt_current = base.compressor_current_A * 1.3; tgt_fan = base.fan_speed_RPM + 100
            tgt_vib = base.vibration_mm_s + 0.05; tgt_damper = np.clip(base['damper_position_%'] - 5, 0, 100)
        elif fault == 'Refrigerant_Leak':
            tgt_refrig = base.refrigerant_pressure_psi * 0.7; tgt_suction = base.suction_pressure_psi * 0.8
            tgt_discharge = base.discharge_pressure_psi * 0.8; tgt_current = base.compressor_current_A * 1.2
            tgt_supply = base.supply_temp_C + 5.0; tgt_return = base.return_temp_C + 1.0
            tgt_fan = base.fan_speed_RPM; tgt_vib = base.vibration_mm_s
            tgt_filter = base.filter_health; tgt_airflow = base.airflow_rate; tgt_damper = base['damper_position_%']
        elif fault == 'Compressor_Fault':
            tgt_current = base.compressor_current_A * 2.0; tgt_vib = base.vibration_mm_s + 1.0
            tgt_supply = base.outdoor_temp_C; tgt_return = base.return_temp_C
            tgt_suction = 30.0; tgt_discharge = 30.0; tgt_fan = base.fan_speed_RPM
            tgt_filter = base.filter_health; tgt_airflow = base.airflow_rate
            tgt_refrig = base.refrigerant_pressure_psi; tgt_damper = base['damper_position_%']
        elif fault == 'Fan_Fault':
            tgt_fan = base.fan_speed_RPM * 0.5; tgt_airflow = base.airflow_rate * 0.5
            tgt_current = base.compressor_current_A * 0.5; tgt_supply = base.supply_temp_C + 5.0
            tgt_return = base.return_temp_C + 1.0; tgt_suction = base.suction_pressure_psi * 0.8
            tgt_discharge = base.discharge_pressure_psi * 0.9; tgt_vib = base.vibration_mm_s
            tgt_filter = base.filter_health; tgt_refrig = base.refrigerant_pressure_psi; tgt_damper = base['damper_position_%']
        elif fault == 'Electrical_Issue':
            tgt_fan = base.fan_speed_RPM * 0.5; tgt_current = base.compressor_current_A * 0.5
            tgt_airflow = base.airflow_rate * 0.5; tgt_supply = base.supply_temp_C + 3.0
            tgt_return = base.return_temp_C + 1.0; tgt_suction = base.suction_pressure_psi * 0.8
            tgt_discharge = base.discharge_pressure_psi * 0.8; tgt_vib = base.vibration_mm_s
            tgt_filter = base.filter_health; tgt_refrig = base.refrigerant_pressure_psi; tgt_damper = base['damper_position_%']
        for i in range(start, end):
            frac = (i - start) / (length - 1) if length > 1 else 1.0
            if fault == 'Control_Sensor_Fault':
                mid = (start + end - 1) / 2
                frac2 = (i - start) / (mid - start) if i <= mid and mid > start else (1.0 - (i - mid) / (end - mid - 1) if (end - mid - 1) > 0 else 0.0) if i > mid else 1.0
                df_target.at[i, 'supply_temp_C'] = base.supply_temp_C + 15.0 * frac2
                df_target.at[i, 'damper_position_%'] = np.clip(base['damper_position_%'] + np.random.normal(0, 1), 0, 100)
                for c in ['return_temp_C','suction_pressure_psi','discharge_pressure_psi','compressor_current_A','fan_speed_RPM','vibration_mm_s','filter_health','airflow_rate','refrigerant_pressure_psi']:
                    df_target.at[i, c] = getattr(base, c) if hasattr(base, c) else base[c]
            else:
                for col, tgt in [('filter_health', tgt_filter), ('airflow_rate', tgt_airflow), ('supply_temp_C', tgt_supply),
                    ('return_temp_C', tgt_return), ('suction_pressure_psi', tgt_suction), ('discharge_pressure_psi', tgt_discharge),
                    ('compressor_current_A', tgt_current), ('fan_speed_RPM', tgt_fan), ('vibration_mm_s', tgt_vib)]:
                    base_val = getattr(base, col) if hasattr(base, col) else base[col]
                    df_target.at[i, col] = base_val + (tgt - base_val) * frac
                if fault == 'Filter_Clog':
                    df_target.at[i, 'damper_position_%'] = np.clip(base['damper_position_%'] - (2 + 3 * frac), 0, 100)
                    df_target.at[i, 'refrigerant_pressure_psi'] = df_target.at[i, 'suction_pressure_psi'] * 0.3 + df_target.at[i, 'discharge_pressure_psi'] * 0.7
                elif fault in ('Fan_Fault',):
                    df_target.at[i, 'damper_position_%'] = np.clip(base['damper_position_%'] + np.random.normal(0, 2), 0, 100)
                    df_target.at[i, 'refrigerant_pressure_psi'] = base.refrigerant_pressure_psi + (tgt_refrig - base.refrigerant_pressure_psi) * frac
                elif fault == 'Electrical_Issue':
                    df_target.at[i, 'damper_position_%'] = base['damper_position_%']
                    df_target.at[i, 'refrigerant_pressure_psi'] = base.refrigerant_pressure_psi + (tgt_refrig - base.refrigerant_pressure_psi) * frac
                elif fault == 'Refrigerant_Leak':
                    df_target.at[i, 'damper_position_%'] = base['damper_position_%']
                    df_target.at[i, 'refrigerant_pressure_psi'] = base.refrigerant_pressure_psi + (tgt_refrig - base.refrigerant_pressure_psi) * frac
                elif fault == 'Compressor_Fault':
                    df_target.at[i, 'damper_position_%'] = base['damper_position_%']
                    df_target.at[i, 'refrigerant_pressure_psi'] = base.refrigerant_pressure_psi
            df_target.at[i, 'fault'] = fault

    df_final = df.copy()
    for start, end, fault in events:
        inject_fault(df, df_final, start, end, fault)

    assert not df_final.duplicated().any(), "Duplicate rows found!"
    df_final.to_csv("hvac_synthetic_dataset.csv", index=False)
    print("Dataset generated successfully!")
    print(df_final.head())