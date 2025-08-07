import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import streamlit as st

from .scenarios import gen_sine, gen_step, gen_random_walk

def generate_simulation_data(params):
    """
    Generates data for the built-in scenarios (Sine, Step, etc.).
    Applies anomalies based on run parameters.
    """
    # Set random seed for reproducible data generation
    # Note: seed may already be set by simulation_engine.py, but we ensure it here for direct calls
    if params.get('use_seed', True) and 'random_seed' in params:
        np.random.seed(params['random_seed'])
    
    # Use a fixed numerical time axis for calculations
    time_step = 0.1  # seconds per point
    numeric_time_axis = np.arange(0, params['num_steps'] * time_step, time_step)
    
    # Create a parallel datetime axis for display
    start_datetime = datetime.combine(params['start_date'], datetime.min.time())
    datetime_axis = [start_datetime + timedelta(seconds=t) for t in numeric_time_axis]

    prev_val = 0.0
    values = []
    for t_numeric in numeric_time_axis:
        if params['scenario'] == "Sine Wave":
            val = gen_sine(t_numeric, params['amp'], params['freq'], params['noise'])
        elif params['scenario'] == "Step Change":
            val = gen_step(t_numeric, params['amp'], params['step_time'] / 10, params['noise'])
        else:  # Random Walk
            val = gen_random_walk(prev_val, params['noise'])
            prev_val = val
        values.append(val)

    # Inject anomalies into the generated data
    if params.get('num_anomalies', 0) > 0:
        anomaly_indices = np.linspace(
            start=params['num_steps'] * 0.1,
            stop=params['num_steps'] * 0.9,
            num=params['num_anomalies']
        ).astype(int)
        
        for idx in anomaly_indices:
            # Ensure the index is within bounds
            if idx < len(values):
                values[idx] += params['anomaly_magnitude']
            
    df = pd.DataFrame({'Time': datetime_axis, 'Actual Data': values, 'Numeric Time': numeric_time_axis})
    return df

def load_data_from_csv(uploaded_file):
    """
    Loads and validates data from an uploaded CSV file.
    It expects 'Time' and 'Actual Data' columns.
    """
    if uploaded_file is None:
        return None
    try:
        df = pd.read_csv(uploaded_file)
        
        # --- Data Validation and Parsing ---
        if 'Time' not in df.columns or 'Actual Data' not in df.columns:
            st.error("CSV must contain 'Time' and 'Actual Data' columns.")
            return None
        
        # Convert 'Time' to datetime objects, which is crucial for plotting
        df['Time'] = pd.to_datetime(df['Time'])
        
        # Convert 'Actual Data' to a numeric type, coercing any errors
        df['Actual Data'] = pd.to_numeric(df['Actual Data'], errors='coerce')
        
        # Drop rows where the conversion might have failed
        df.dropna(subset=['Time', 'Actual Data'], inplace=True)
        
        # Create a numeric time axis for models that need it (like Active Inference)
        time_deltas = (df['Time'] - df['Time'].iloc[0]).dt.total_seconds()
        df['Numeric Time'] = time_deltas
        
        return df.sort_values(by='Time').reset_index(drop=True)
        
    except Exception as e:
        st.error(f"Error processing CSV file: {e}")
        return None 