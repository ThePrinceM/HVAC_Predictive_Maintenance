# 🔧 HVAC Fault Detection System

AI-powered predictive maintenance system for HVAC Rooftop Units (RTU) using XGBoost classification and an interactive Streamlit dashboard.

![Dashboard Reference](dashboard.jpeg)

## 📋 Features

- **Multi-class Fault Detection** — Identifies 7 fault types: Normal, Filter Clog, Fan Fault, Refrigerant Leak, Electrical Issue, Compressor Fault, Control Sensor Fault
- **XGBoost Classifier** — 80/10/10 stratified train/val/test split with 150 estimators
- **Interactive Dashboard** — 5-page Streamlit app with dark industrial theme
- **SHAP Explainability** — Feature importance and SHAP analysis
- **Live Prediction** — Real-time fault prediction from sensor inputs
- **Metrics Tracking** — SQLite-backed training run history
- **Stitch Integration** — Data refresh and prediction logging (mock connector)

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd hvac_fault_detection
pip install -r requirements.txt
```

### 2. Train the Model (CLI)

```bash
python model/train.py
```

### 3. Run the Dashboard

```bash
streamlit run app.py
```

## 📁 Project Structure

```
hvac_fault_detection/
├── app.py                    ← Main Streamlit dashboard
├── model/
│   ├── train.py              ← Training pipeline
│   ├── predict.py            ← Inference logic
│   ├── model.pkl             ← Saved XGBoost model
│   ├── label_encoder.pkl     ← Label encoder
│   └── feature_names.pkl     ← Feature column names
├── data/
│   └── hvac_synthetic_dataset.csv
├── utils/
│   ├── preprocess.py         ← Data loading & preprocessing
│   ├── visualizations.py     ← Plotly chart helpers
│   └── stitch_connector.py   ← Stitch MCP connector (mock)
├── metrics_history.db        ← SQLite training logs
├── requirements.txt
└── README.md
```

## ⚙️ Model Configuration

| Parameter       | Value      |
|----------------|------------|
| Algorithm       | XGBClassifier |
| n_estimators    | 150        |
| learning_rate   | 0.1        |
| max_depth       | 6          |
| eval_metric     | mlogloss   |
| random_state    | 42         |
| Data Split      | 80/10/10   |

## 🔌 Stitch MCP Configuration

The system includes a mock Stitch connector. To configure a real connector:

### Environment Variables (.env)

```env
STITCH_API_KEY=your_stitch_api_key
STITCH_SOURCE_ID=hvac_sensor_feed
STITCH_DESTINATION_ID=prediction_warehouse
STITCH_BASE_URL=https://api.stitchdata.com/v4
```

Replace `utils/stitch_connector.py` with real SDK calls when ready.

## 📊 Dashboard Pages

1. **📂 Data Overview** — Dataset stats, fault distribution, sensor trends
2. **🏋️ Model Training** — Train XGBoost with live progress, view results
3. **🔍 Feature Importance** — Top-N importances + SHAP analysis
4. **🤖 Live Prediction** — Real-time fault prediction from sensor inputs
5. **📈 Metrics History** — Training run trends and comparison

## 📄 License

MIT License
