import os
import glob

def main():
    root = "d:\\D,Drive\\Promptathon\\Dashboard\\hvac_fault_detection"
    with open(os.path.join(root, "app_new.py"), "w", encoding="utf-8") as out:
        out.write('"""HVAC Fault Detection System - Streamlit Dashboard"""\n')
        out.write('import streamlit as st\n')
        out.write('import os, sys, collections, datetime, json, joblib, random\n')
        out.write('import pandas as pd\n\n')
        
        out.write('ROOT = os.path.dirname(os.path.abspath(__file__))\n')
        out.write('sys.path.insert(0, ROOT)\n\n')
        
        # Imports from utils/model
        out.write('from utils.simulator import SensorSimulator\n')
        out.write('from utils.visualizations import *\n')
        out.write('from utils.alert_engine import *\n')
        out.write('from model.predict import predict_fault, load_model, clear_model_cache\n')
        out.write('from utils.preprocess import get_feature_names, validate_input, FEATURE_RANGES, load_dataset, preprocess_features\n')
        out.write('from utils.stitch_connector import log_prediction\n')
        out.write('from model.train import train_model, DEFAULT_HYPERPARAMS, get_metrics_history\n\n')
        
        # Original app.py parts (CSS, Session State, Header)
        # We will write the structure manually to make sure it's correct.
        
if __name__ == "__main__":
    main()
