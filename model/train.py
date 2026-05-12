"""
HVAC Fault Detection — Training Pipeline
==========================================
Refactored training script that:
  - Uses shared preprocessing utilities
  - Trains an XGBClassifier (80/10/10 stratified split)
  - Saves model, encoder, and feature names via joblib
  - Logs run metadata to SQLite for metrics history
  - Returns comprehensive metrics dict for dashboard display
"""

import os
import sys
import json
import datetime
import joblib
import numpy as np
import pandas as pd
from xgboost import XGBClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)

# ─── Path Setup ─────────────────────────────────────────────────────────────────

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from utils.preprocess import (
    load_dataset,
    preprocess_features,
    encode_labels,
    split_data,
    get_feature_names,
)

# ─── Constants ──────────────────────────────────────────────────────────────────

MODEL_DIR = os.path.join(ROOT_DIR, "model")
DATA_DIR = os.path.join(ROOT_DIR, "data")
DEFAULT_DATA_PATH = os.path.join(DATA_DIR, "hvac_synthetic_dataset.csv")

MODEL_PATH = os.path.join(MODEL_DIR, "model.pkl")
ENCODER_PATH = os.path.join(MODEL_DIR, "label_encoder.pkl")
FEATURES_PATH = os.path.join(MODEL_DIR, "feature_names.pkl")
METRICS_DB_PATH = os.path.join(ROOT_DIR, "metrics_history.db")

# Default hyperparameters
DEFAULT_HYPERPARAMS = {
    "n_estimators": 150,
    "learning_rate": 0.1,
    "max_depth": 6,
    "random_state": 42,
    "eval_metric": "mlogloss",
}


# ─── Metrics Logging ────────────────────────────────────────────────────────────

def _init_metrics_db():
    """Initialize the SQLite database for metrics history."""
    import sqlite3

    conn = sqlite3.connect(METRICS_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS training_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            train_accuracy REAL NOT NULL,
            val_accuracy REAL NOT NULL,
            test_accuracy REAL NOT NULL,
            train_size INTEGER,
            val_size INTEGER,
            test_size INTEGER,
            hyperparams TEXT,
            num_classes INTEGER,
            duration_seconds REAL
        )
    """)
    conn.commit()
    conn.close()


def _log_run(metrics: dict):
    """Log a training run to the SQLite database."""
    import sqlite3

    _init_metrics_db()
    conn = sqlite3.connect(METRICS_DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO training_runs
            (timestamp, train_accuracy, val_accuracy, test_accuracy,
             train_size, val_size, test_size, hyperparams,
             num_classes, duration_seconds)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            metrics["timestamp"],
            metrics["train_accuracy"],
            metrics["val_accuracy"],
            metrics["test_accuracy"],
            metrics["train_size"],
            metrics["val_size"],
            metrics["test_size"],
            json.dumps(metrics["hyperparams"]),
            metrics["num_classes"],
            metrics.get("duration_seconds", 0),
        ),
    )
    conn.commit()
    conn.close()


def get_metrics_history() -> pd.DataFrame:
    """Retrieve all training run logs from the database."""
    import sqlite3

    _init_metrics_db()
    conn = sqlite3.connect(METRICS_DB_PATH)
    df = pd.read_sql_query("SELECT * FROM training_runs ORDER BY id ASC", conn)
    conn.close()
    return df


# ─── Training Pipeline ──────────────────────────────────────────────────────────

def train_model(
    data_path: str = None,
    hyperparams: dict = None,
    progress_callback=None,
) -> dict:
    """
    Full training pipeline: load → preprocess → split → train → evaluate → save.

    Parameters
    ----------
    data_path : str, optional
        Path to CSV dataset. Defaults to data/hvac_synthetic_dataset.csv.
    hyperparams : dict, optional
        XGBClassifier hyperparameters. Defaults to DEFAULT_HYPERPARAMS.
    progress_callback : callable, optional
        Function(progress_float, status_string) for UI updates.

    Returns
    -------
    dict
        Comprehensive metrics including accuracies, confusion matrix,
        classification report, split sizes, class names, etc.
    """
    import time

    start_time = time.time()

    if data_path is None:
        data_path = DEFAULT_DATA_PATH
    if hyperparams is None:
        hyperparams = DEFAULT_HYPERPARAMS.copy()

    def _progress(pct, msg):
        if progress_callback:
            progress_callback(pct, msg)

    # ── Step 1: Load data ───────────────────────────────────────────────────
    _progress(0.05, "Loading dataset...")
    df = load_dataset(data_path)

    # ── Step 2: Preprocess ──────────────────────────────────────────────────
    _progress(0.15, "Preprocessing features...")
    X, y = preprocess_features(df)
    y_encoded, label_encoder = encode_labels(y)
    class_names = list(label_encoder.classes_)

    # ── Step 3: Split (80/10/10) ────────────────────────────────────────────
    _progress(0.25, "Splitting data (80/10/10)...")
    splits = split_data(X, y_encoded, random_state=hyperparams.get("random_state", 42))
    X_train, X_val, X_test = splits["X_train"], splits["X_val"], splits["X_test"]
    y_train, y_val, y_test = splits["y_train"], splits["y_val"], splits["y_test"]

    # ── Step 4: Train XGBoost ───────────────────────────────────────────────
    _progress(0.40, "Training XGBoost model...")
    model = XGBClassifier(**hyperparams)
    model.fit(X_train, y_train)

    # ── Step 5: Evaluate ────────────────────────────────────────────────────
    _progress(0.70, "Evaluating model...")
    y_train_pred = model.predict(X_train)
    y_val_pred = model.predict(X_val)
    y_test_pred = model.predict(X_test)

    train_acc = accuracy_score(y_train, y_train_pred)
    val_acc = accuracy_score(y_val, y_val_pred)
    test_acc = accuracy_score(y_test, y_test_pred)

    cm = confusion_matrix(y_test, y_test_pred)
    report = classification_report(y_test, y_test_pred, target_names=class_names, output_dict=True)

    # ── Step 6: Save artifacts ──────────────────────────────────────────────
    _progress(0.85, "Saving model artifacts...")
    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    joblib.dump(label_encoder, ENCODER_PATH)
    joblib.dump(get_feature_names(), FEATURES_PATH)

    # ── Step 7: Log run ─────────────────────────────────────────────────────
    duration = time.time() - start_time
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    metrics = {
        "timestamp": timestamp,
        "train_accuracy": round(train_acc, 4),
        "val_accuracy": round(val_acc, 4),
        "test_accuracy": round(test_acc, 4),
        "train_size": len(X_train),
        "val_size": len(X_val),
        "test_size": len(X_test),
        "num_classes": len(class_names),
        "class_names": class_names,
        "confusion_matrix": cm.tolist(),
        "classification_report": report,
        "hyperparams": hyperparams,
        "duration_seconds": round(duration, 2),
        "feature_importances": dict(
            zip(get_feature_names(), model.feature_importances_.tolist())
        ),
    }

    _progress(0.95, "Logging metrics...")
    _log_run(metrics)

    _progress(1.0, "Training complete!")
    return metrics


# ─── CLI Entrypoint ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("  HVAC Fault Detection — Training Pipeline")
    print("=" * 60)

    def cli_progress(pct, msg):
        bar_len = 30
        filled = int(bar_len * pct)
        bar = "#" * filled + "-" * (bar_len - filled)
        print(f"\r  [{bar}] {pct*100:5.1f}% - {msg}", end="", flush=True)
        if pct >= 1.0:
            print()

    results = train_model(progress_callback=cli_progress)

    print(f"\n  Train Accuracy:      {results['train_accuracy']*100:.2f}%")
    print(f"  Validation Accuracy: {results['val_accuracy']*100:.2f}%")
    print(f"  Test Accuracy:       {results['test_accuracy']*100:.2f}%")
    print(f"  Duration:            {results['duration_seconds']:.1f}s")
    print(f"  Classes:             {results['class_names']}")
    print(f"\n  Model saved to: {MODEL_PATH}")
    print("=" * 60)
