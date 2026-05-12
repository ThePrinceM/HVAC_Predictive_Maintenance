"""
HVAC Fault Detection — Inference Module
=========================================
Load the trained XGBoost model and run predictions on
single inputs or DataFrames.
"""

import os
import sys
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Tuple, List, Optional

# ─── Path Setup ─────────────────────────────────────────────────────────────────

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

MODEL_DIR = os.path.join(ROOT_DIR, "model")
MODEL_PATH = os.path.join(MODEL_DIR, "model.pkl")
ENCODER_PATH = os.path.join(MODEL_DIR, "label_encoder.pkl")
FEATURES_PATH = os.path.join(MODEL_DIR, "feature_names.pkl")


# ─── Model Loading ──────────────────────────────────────────────────────────────

_model_cache = {}


def load_model():
    """
    Load the trained model, label encoder, and feature names from disk.
    Uses in-memory caching to avoid repeated disk reads.

    Returns
    -------
    tuple
        (model, label_encoder, feature_names)

    Raises
    ------
    FileNotFoundError
        If any required artifact is missing.
    """
    if "model" in _model_cache:
        return _model_cache["model"], _model_cache["encoder"], _model_cache["features"]

    for path, name in [
        (MODEL_PATH, "model.pkl"),
        (ENCODER_PATH, "label_encoder.pkl"),
        (FEATURES_PATH, "feature_names.pkl"),
    ]:
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"Model artifact '{name}' not found at {path}. "
                "Please train the model first (Page: Model Training)."
            )

    model = joblib.load(MODEL_PATH)
    encoder = joblib.load(ENCODER_PATH)
    features = joblib.load(FEATURES_PATH)

    _model_cache["model"] = model
    _model_cache["encoder"] = encoder
    _model_cache["features"] = features

    return model, encoder, features


def clear_model_cache():
    """Clear the model cache (call after re-training)."""
    _model_cache.clear()


# ─── Single Prediction ──────────────────────────────────────────────────────────

def predict_fault(input_data: Dict[str, float]) -> Dict:
    """
    Predict the fault class for a single set of sensor readings.

    Parameters
    ----------
    input_data : dict
        Feature name → sensor value mapping.

    Returns
    -------
    dict
        predicted_class: str — The predicted fault label.
        confidence: float — Probability of the predicted class.
        probabilities: dict — {class_name: probability} for all classes.
        predicted_index: int — Encoded label index.
    """
    model, encoder, feature_names = load_model()

    # Build feature vector in correct order
    feature_vector = np.array(
        [[input_data.get(f, 0.0) for f in feature_names]]
    )
    input_df = pd.DataFrame(feature_vector, columns=feature_names)

    # Predict
    prediction = model.predict(input_df)[0]
    probabilities = model.predict_proba(input_df)[0]

    predicted_class = encoder.inverse_transform([prediction])[0]
    confidence = float(probabilities[prediction])

    prob_dict = {
        encoder.inverse_transform([i])[0]: round(float(p), 4)
        for i, p in enumerate(probabilities)
    }

    return {
        "predicted_class": predicted_class,
        "confidence": round(confidence, 4),
        "probabilities": prob_dict,
        "predicted_index": int(prediction),
    }


# ─── Batch Prediction ───────────────────────────────────────────────────────────

def predict_batch(df: pd.DataFrame) -> pd.DataFrame:
    """
    Run predictions on a DataFrame of sensor readings.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with feature columns.

    Returns
    -------
    pd.DataFrame
        Original DataFrame with added columns:
        - predicted_fault: Predicted fault label
        - confidence: Max prediction probability
    """
    model, encoder, feature_names = load_model()

    # Ensure correct column order
    X = df[feature_names].copy()

    predictions = model.predict(X)
    probabilities = model.predict_proba(X)

    result = df.copy()
    result["predicted_fault"] = encoder.inverse_transform(predictions)
    result["confidence"] = probabilities.max(axis=1).round(4)

    return result


# ─── CLI Entrypoint ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Quick test with sample values
    sample_input = {
        "return_temp_C": 24.0,
        "supply_temp_C": 15.8,
        "outdoor_temp_C": 36.2,
        "suction_pressure_psi": 58.0,
        "discharge_pressure_psi": 214.0,
        "compressor_current_A": 12.1,
        "fan_speed_RPM": 1502.0,
        "vibration_mm_s": 0.21,
        "unit_age": 4.8,
        "refrigerant_pressure_psi": 167.0,
        "filter_health": 1.0,
        "airflow_rate": 5.0,
        "damper_position_%": 31.7,
    }

    print("=" * 50)
    print("  HVAC Fault Detection — Sample Prediction")
    print("=" * 50)

    try:
        result = predict_fault(sample_input)
        print(f"\n  Predicted Fault:  {result['predicted_class']}")
        print(f"  Confidence:       {result['confidence']*100:.1f}%")
        print(f"\n  Class Probabilities:")
        for cls, prob in sorted(result["probabilities"].items(), key=lambda x: -x[1]):
            bar = "█" * int(prob * 30)
            print(f"    {cls:25s} {prob*100:5.1f}%  {bar}")
    except FileNotFoundError as e:
        print(f"\n  Error: {e}")
    print("=" * 50)
