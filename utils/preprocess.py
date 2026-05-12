"""
HVAC Fault Detection — Preprocessing Utilities
================================================
Shared helpers for data loading, validation, feature engineering,
label encoding, and train/val/test splitting.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from typing import Tuple, Dict, List, Optional
import os

# ─── Constants ──────────────────────────────────────────────────────────────────

REQUIRED_COLUMNS = [
    "timestamp", "return_temp_C", "supply_temp_C", "outdoor_temp_C",
    "suction_pressure_psi", "discharge_pressure_psi", "compressor_current_A",
    "fan_speed_RPM", "vibration_mm_s", "unit_age", "refrigerant_pressure_psi",
    "filter_health", "airflow_rate", "damper_position_%", "fault",
]

FEATURE_COLUMNS = [
    "return_temp_C", "supply_temp_C", "outdoor_temp_C",
    "suction_pressure_psi", "discharge_pressure_psi", "compressor_current_A",
    "fan_speed_RPM", "vibration_mm_s", "unit_age", "refrigerant_pressure_psi",
    "filter_health", "airflow_rate", "damper_position_%",
]

DROP_COLUMNS = ["timestamp", "fault"]

TARGET_COLUMN = "fault"

# Reasonable sensor ranges (min, max) for input validation
FEATURE_RANGES: Dict[str, Tuple[float, float]] = {
    "return_temp_C":            (10.0, 45.0),
    "supply_temp_C":            (5.0,  30.0),
    "outdoor_temp_C":           (15.0, 50.0),
    "suction_pressure_psi":     (30.0, 90.0),
    "discharge_pressure_psi":   (100.0, 350.0),
    "compressor_current_A":     (5.0, 30.0),
    "fan_speed_RPM":            (800.0, 2200.0),
    "vibration_mm_s":           (0.0, 5.0),
    "unit_age":                 (0.0, 25.0),
    "refrigerant_pressure_psi": (80.0, 250.0),
    "filter_health":            (0.0, 1.0),
    "airflow_rate":             (1.0, 10.0),
    "damper_position_%":        (0.0, 100.0),
}


# ─── Data Loading ───────────────────────────────────────────────────────────────

def load_dataset(path: str) -> pd.DataFrame:
    """
    Load the HVAC dataset from a CSV file with validation.

    Parameters
    ----------
    path : str
        Path to the CSV file.

    Returns
    -------
    pd.DataFrame
        Validated DataFrame.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    ValueError
        If required columns are missing.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Dataset not found at: {path}")

    df = pd.read_csv(path)

    # Validate required columns
    missing_cols = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing_cols:
        raise ValueError(
            f"Dataset missing required columns: {missing_cols}. "
            f"Found columns: {df.columns.tolist()}"
        )

    return df


def get_data_summary(df: pd.DataFrame) -> Dict:
    """
    Generate a summary of the dataset for the dashboard.

    Returns
    -------
    dict
        Keys: shape, dtypes, missing_values, class_distribution, feature_stats
    """
    return {
        "shape": df.shape,
        "dtypes": df.dtypes.astype(str).to_dict(),
        "missing_values": df.isnull().sum().to_dict(),
        "total_missing": int(df.isnull().sum().sum()),
        "class_distribution": df[TARGET_COLUMN].value_counts().to_dict(),
        "feature_stats": df[FEATURE_COLUMNS].describe().to_dict(),
    }


# ─── Feature Engineering ────────────────────────────────────────────────────────

def preprocess_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Separate features (X) and target (y) from the DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Raw dataset with all columns.

    Returns
    -------
    Tuple[pd.DataFrame, pd.Series]
        (X, y) where X has timestamp/fault dropped.
    """
    X = df.drop(columns=DROP_COLUMNS, errors="ignore")
    y = df[TARGET_COLUMN]
    return X, y


def encode_labels(y: pd.Series, encoder: Optional[LabelEncoder] = None) -> Tuple[np.ndarray, LabelEncoder]:
    """
    Label-encode the target variable.

    Parameters
    ----------
    y : pd.Series
        Raw fault labels (strings).
    encoder : LabelEncoder, optional
        Pre-fitted encoder. If None, a new one is fitted.

    Returns
    -------
    Tuple[np.ndarray, LabelEncoder]
        (encoded_labels, fitted_encoder)
    """
    if encoder is None:
        encoder = LabelEncoder()
        y_encoded = encoder.fit_transform(y)
    else:
        y_encoded = encoder.transform(y)
    return y_encoded, encoder


def split_data(
    X: pd.DataFrame,
    y: np.ndarray,
    random_state: int = 42,
) -> Dict[str, np.ndarray]:
    """
    Split data into 80% train, 10% validation, 10% test (stratified).

    Returns
    -------
    dict
        Keys: X_train, X_val, X_test, y_train, y_val, y_test
    """
    # Shuffle
    indices = np.arange(len(X))
    np.random.seed(random_state)
    np.random.shuffle(indices)
    X = X.iloc[indices].reset_index(drop=True)
    y = y[indices]

    # 80/20 split first
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.20, random_state=random_state, stratify=y
    )

    # Then 50/50 on the 20% → 10% val + 10% test
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.50, random_state=random_state, stratify=y_temp
    )

    return {
        "X_train": X_train, "X_val": X_val, "X_test": X_test,
        "y_train": y_train, "y_val": y_val, "y_test": y_test,
    }


# ─── Helpers ────────────────────────────────────────────────────────────────────

def get_feature_names() -> List[str]:
    """Return the ordered list of feature column names."""
    return FEATURE_COLUMNS.copy()


def validate_input(data: Dict[str, float]) -> Tuple[bool, List[str]]:
    """
    Validate a single prediction input against expected ranges.

    Parameters
    ----------
    data : dict
        Sensor feature name → value mapping.

    Returns
    -------
    Tuple[bool, List[str]]
        (is_valid, list_of_warning_messages)
    """
    warnings = []
    for feature in FEATURE_COLUMNS:
        if feature not in data:
            warnings.append(f"Missing feature: {feature}")
            continue

        val = data[feature]
        lo, hi = FEATURE_RANGES.get(feature, (None, None))
        if lo is not None and hi is not None:
            if val < lo or val > hi:
                warnings.append(
                    f"{feature} = {val:.2f} is outside expected range [{lo}, {hi}]"
                )

    is_valid = len([w for w in warnings if w.startswith("Missing")]) == 0
    return is_valid, warnings


def get_feature_ranges_from_data(df: pd.DataFrame) -> Dict[str, Tuple[float, float]]:
    """
    Extract actual min/max ranges from the dataset for building UI sliders.
    """
    ranges = {}
    for col in FEATURE_COLUMNS:
        if col in df.columns:
            ranges[col] = (float(df[col].min()), float(df[col].max()))
    return ranges
