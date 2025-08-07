import streamlit as st
import numpy as np
import time
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

from pc_demolib.models import (
    basic_predictive_coding,
    hierarchical_predictive_coding,
    event_driven_predictive_coding,
    precision_weighted_predictive_coding,
    deep_hierarchical_predictive_coding,
    active_inference
)
from pc_demolib.scenarios import (
    gen_sine,
    gen_step,
    gen_random_walk
)
from pc_demolib.utils import inject_custom_font
from pc_demolib.visualization import display_results_page

# =======================
# Streamlit App
# =======================

# --- App Constants ---
window_size = 200
# run_time is now determined by num_steps

# --- Initialize session state for results ---
if 'results_df' not in st.session_state:
    st.session_state.results_df = None
if 'run_params' not in st.session_state:
    st.session_state.run_params = {}

# --- Font and Page Config ---
st.set_page_config(page_title="Real-time Predictive Coding Demo", layout="wide")
inject_custom_font("fonts/Paperlogy.ttf")

st.title("Real-time Predictive Coding")

# --- Sidebar Controls ---
st.sidebar.title("Controls")
pc_model = st.sidebar.selectbox("Choose Predictive Coding Model",
                                ["Basic", "Hierarchical", "Event-Driven", "Precision-Weighting",
                                 "Deep Hierarchical", "Active Inference"])

st.sidebar.header("Scenario Settings")
# Add CSV Upload to scenario options
scenario = st.sidebar.selectbox("Choose Scenario", ["Sine Wave", "Step Change", "Random Walk", "CSV Upload"])

# --- Scenario-Specific Controls ---
uploaded_file = None
if scenario == 'CSV Upload':
    uploaded_file = st.sidebar.file_uploader(
        "Upload your IoT data", type=['csv'],
        help="CSV file must have 'Time' and 'Actual Data' columns."
    )
    # Set dummy values for params not used in CSV mode
    amp, freq, noise, step_time, num_steps, use_seed = 1.0, 0.1, 0.0, 50, 0, False
    num_anomalies, anomaly_magnitude = 0, 0.0
    start_date = datetime.now().date() # for compatibility
else:
    amp = st.sidebar.slider("Amplitude", 1.0, 10.0, 5.0)
    freq = st.sidebar.slider("Frequency (Hz)", 0.01, 1.0, 0.1)
    noise = st.sidebar.slider("Noise Level", 0.0, 5.0, 1.0)
    step_time = st.sidebar.slider("Step Time (sec)", 1, 100, 50)
    st.sidebar.markdown("---")
    num_steps = st.sidebar.number_input("Total Data Points to Generate", min_value=200, max_value=5000, value=1000, step=100)
    start_date = st.sidebar.date_input("Start Date", value=datetime.now())
    st.sidebar.markdown("---")
    use_seed = st.sidebar.checkbox("Use Fixed Random Seed", value=True, help="Ensures the same random data is generated on each run, for fair model comparison.")
    random_seed = st.sidebar.number_input("Random Seed", value=42, step=1, disabled=not use_seed)
    
    # --- Anomaly Injection ---
    st.sidebar.header("Anomaly Injection")
    num_anomalies = st.sidebar.number_input("Number of Anomalies to Inject", min_value=0, max_value=20, value=3, step=1)
    anomaly_magnitude = st.sidebar.slider("Anomaly Magnitude", 1.0, 50.0, 20.0, help="The value to add to the data to create a spike.")

# --- Model-Specific Parameters ---
st.sidebar.header(f"{pc_model} Settings")

if pc_model in ["Hierarchical", "Deep Hierarchical"]:
    if pc_model == "Deep Hierarchical":
        st.sidebar.info("A model with more layers. You can customize the number and values of layers.")
        default_sigmas = "100, 60, 30, 10, 3"
        default_thresholds = "6.0, 4.0, 2.5, 1.5, 0.8"
    else: # Hierarchical
        default_sigmas = "50, 20, 5"
        default_thresholds = "5.0, 3.0, 1.5"

    sigmas_str = st.sidebar.text_input("Sigmas (comma-separated)", default_sigmas)
    thresholds_str = st.sidebar.text_input("Thresholds (comma-separated)", default_thresholds)
    
    try:
        sigmas = [int(s.strip()) for s in sigmas_str.split(',')]
        thresholds = [float(t.strip()) for t in thresholds_str.split(',')]
        if len(sigmas) != len(thresholds):
            st.sidebar.error("The number of sigmas must match the number of thresholds.")
            st.stop()
    except ValueError:
        st.sidebar.error("Please enter comma-separated numbers for sigmas and thresholds.")
        st.stop()

elif pc_model == "Basic":
    sigma = st.sidebar.slider("Sigma", 1.0, 100.0, 20.0)
    threshold = st.sidebar.slider("Anomaly Threshold", 0.1, 10.0, 1.5)
elif pc_model == "Event-Driven":
    sigma = st.sidebar.slider("Sigma", 1.0, 100.0, 20.0)
    threshold = st.sidebar.slider("Anomaly Threshold", 0.1, 10.0, 1.5)
    event_threshold = st.sidebar.slider("Event Threshold", 0.1, 10.0, 2.0)
elif pc_model == "Precision-Weighting":
    sigma = st.sidebar.slider("Sigma", 1.0, 100.0, 20.0)
    threshold = st.sidebar.slider("Anomaly Threshold", 0.1, 10.0, 1.5)
    sensory_precision = st.sidebar.slider("Sensory Precision", 0.1, 10.0, 5.0)
    model_precision = st.sidebar.slider("Model Precision", 0.1, 10.0, 2.0)
elif pc_model == "Active Inference":
    # Inform the user that Active Inference is best suited for Sine Wave, but don't force it.
    st.sidebar.info("Active Inference model is designed to learn sine wave parameters.")
    
    if 'internal_model_params' not in st.session_state:
        st.session_state.internal_model_params = {'freq': 0.05, 'amp': 3.0}
    sigma = st.sidebar.slider("Smoothing Sigma", 0.1, 20.0, 3.0, help="Controls the smoothing of the input data to help the model learn the underlying trend.")
    threshold = st.sidebar.slider("Anomaly Threshold", 0.1, 10.0, 2.0)

# --- Display Settings ---
st.sidebar.header("Display Settings")
num_rows_to_show = st.sidebar.slider(
    "Rows in Recent Data Table",
    min_value=10,
    max_value=window_size,
    value=10,
    step=10,
    help="Number of recent data points to show in the table below the graph."
)


if st.sidebar.button("Start Demo"):
    # --- Start of Simulation Block ---

    # Clear previous run results when starting a new demo
    st.session_state.results_df = None
    st.session_state.run_params = {}

    placeholder = st.empty()
    table_placeholder = st.empty()
    status_box = st.empty()

    # --- Data Loading and Preparation ---
    source_df = None
    if scenario == "CSV Upload":
        if uploaded_file is None:
            st.error("Please upload a CSV file to run the demo.")
            st.stop()
        try:
            source_df = pd.read_csv(uploaded_file)
            if 'Time' not in source_df.columns or 'Actual Data' not in source_df.columns:
                st.error("CSV must contain 'Time' and 'Actual Data' columns.")
                st.stop()
            
            source_df['Time'] = pd.to_datetime(source_df['Time'])
            source_df['Actual Data'] = pd.to_numeric(source_df['Actual Data'], errors='coerce')
            source_df.dropna(subset=['Time', 'Actual Data'], inplace=True)
            source_df = source_df.sort_values(by='Time').reset_index(drop=True)
            
            time_deltas = (source_df['Time'] - source_df['Time'].iloc[0]).dt.total_seconds()
            source_df['Numeric Time'] = time_deltas
            
            sleep_interval = 0.01 # Use a fast interval for pre-loaded data
        except Exception as e:
            st.error(f"Error processing CSV file: {e}")
            st.stop()
    else:
        # Generate data for built-in scenarios
        if use_seed:
            np.random.seed(random_seed)

        time_step = 0.1
        numeric_time_axis_gen = np.arange(0, num_steps * time_step, time_step)
        start_datetime = datetime.combine(start_date, datetime.min.time())
        datetime_axis_gen = [start_datetime + timedelta(seconds=t) for t in numeric_time_axis_gen]
        
        anomaly_indices_to_inject = []
        if num_anomalies > 0:
            anomaly_indices_to_inject = list(np.linspace(start=num_steps * 0.1, stop=num_steps * 0.9, num=num_anomalies).astype(int))

        generated_values = []
        prev_val = 0.0
        for i, t_numeric in enumerate(numeric_time_axis_gen):
            if scenario == "Sine Wave":
                val = gen_sine(t_numeric, amp, freq, noise)
            elif scenario == "Step Change":
                val = gen_step(t_numeric, amp, step_time/10, noise)
            else: # Random Walk
                val = gen_random_walk(prev_val, noise)
            
            if len(anomaly_indices_to_inject) > 0 and i == anomaly_indices_to_inject[0]:
                val += anomaly_magnitude
                anomaly_indices_to_inject.pop(0)

            prev_val = val
            generated_values.append(val)
            
        source_df = pd.DataFrame({
            'Time': datetime_axis_gen,
            'Actual Data': generated_values,
            'Numeric Time': numeric_time_axis_gen
        })
        sleep_interval = 20 / num_steps if num_steps > 0 else 0.02


    # --- Simulation Loop ---
    data = []
    time_axis = []
    full_run_data = [] 

    # Define the callback function for Active Inference to update its state
    def set_internal_model_params(new_params):
        st.session_state.internal_model_params = new_params

    if pc_model == "Active Inference":
        # Reset internal model at the start of each run
        st.session_state.internal_model_params = {'freq': 0.05, 'amp': 3.0}

    for i in range(len(source_df)):
        row = source_df.iloc[i]
        t_datetime = row['Time']
        val = row['Actual Data']
        
        data.append(val)
        time_axis.append(t_datetime)

        window_data = np.array(data[-window_size:])
        window_time = np.array(time_axis[-window_size:])
        
        numeric_window_start_index = max(0, i - window_size + 1)
        numeric_window_time = source_df['Numeric Time'].iloc[numeric_window_start_index:i+1].values
        
        preds, errs = [], []
        is_anomaly = False
        events = None

        # Only run models and visualization if we have enough data
        if len(data) >= 10:
            if pc_model == "Basic":
                preds, errs = basic_predictive_coding(window_data, sigma, threshold)
                if errs and errs[0].any(): is_anomaly = abs(errs[0][-1]) > threshold
                if is_anomaly:
                    status_box.warning(f"Anomaly detected at t={t_datetime.strftime('%H:%M:%S')}: error={errs[0][-1]:.2f}", icon="⚡️")

            elif pc_model in ["Hierarchical", "Deep Hierarchical"]:
                current_sigmas = sigmas if pc_model == "Hierarchical" else [100, 60, 30, 10, 3]
                current_thresholds = thresholds if pc_model == "Hierarchical" else [6.0, 4.0, 2.5, 1.5, 0.8]
                preds, errs = hierarchical_predictive_coding(window_data, current_sigmas, current_thresholds)
                
                # --- Tiered Anomaly Detection ---
                # Check each layer's error against its own threshold, from coarsest to finest.
                anomaly_detected_layer = -1
                for layer_idx in range(len(current_thresholds)):
                    layer_error = errs[layer_idx][-1]
                    if abs(layer_error) > current_thresholds[layer_idx]:
                        anomaly_detected_layer = layer_idx
                        break # Stop at the first (most significant) anomaly found
                
                is_anomaly = anomaly_detected_layer != -1

                if is_anomaly:
                    layer_names = ["Coarse", "Medium", "Fine", "Deeper", "Deepest"]
                    layer_name = layer_names[anomaly_detected_layer] if anomaly_detected_layer < len(layer_names) else f"Layer {anomaly_detected_layer+1}"
                    
                    icons = {"Coarse": "🚨", "Medium": "⚠️", "Fine": "⚡️"}
                    icon = icons.get(layer_name, "🔴")
                    
                    message = f"**{layer_name} Layer Anomaly:** Error {errs[anomaly_detected_layer][-1]:.2f} > Threshold {current_thresholds[anomaly_detected_layer]}"
                    if layer_name == "Coarse":
                        status_box.error(f"{icon} {message} - Major trend shift detected!")
                    elif layer_name == "Medium":
                        status_box.warning(f"{icon} {message} - Pattern deviation detected.")
                    else:
                        status_box.info(f"{icon} {message} - Spike or sudden change detected.")
                else:
                     status_box.empty()

            elif pc_model == "Event-Driven":
                preds, errs, events = event_driven_predictive_coding(window_data, sigma, threshold, event_threshold)
                if errs and errs[0].any(): is_anomaly = abs(errs[0][-1]) > threshold
                if is_anomaly:
                    status_box.warning(f"Anomaly detected at t={t_datetime.strftime('%H:%M:%S')}: error={errs[0][-1]:.2f}", icon="⚡️")
            elif pc_model == "Precision-Weighting":
                preds, errs = precision_weighted_predictive_coding(window_data, sigma, threshold, sensory_precision, model_precision)
                if errs and errs[0].any(): is_anomaly = abs(errs[0][-1]) > threshold
                if is_anomaly:
                    status_box.warning(f"Anomaly detected at t={t_datetime.strftime('%H:%M:%S')}: error={errs[0][-1]:.2f}", icon="⚡️")
            elif pc_model == "Active Inference":
                preds, errs = active_inference(window_data, numeric_window_time, st.session_state.internal_model_params, set_internal_model_params, sigma)
                if errs and errs[0].any(): is_anomaly = abs(errs[0][-1]) > threshold
                # Only show the internal model status if the scenario is appropriate
                if scenario in ["Sine Wave", "CSV Upload"]:
                    status_box.info(f"Internal Model: Freq={st.session_state.internal_model_params['freq']:.3f} Hz, Amp={st.session_state.internal_model_params['amp']:.2f}")
                
                if is_anomaly:
                    status_box.warning(f"Anomaly detected at t={t_datetime.strftime('%H:%M:%S')}: error={errs[0][-1]:.2f}", icon="⚡️")

            with placeholder.container():
                fig = go.Figure()

                # Actual Data
                fig.add_trace(go.Scatter(x=window_time, y=window_data, mode='lines+markers', name='Actual Data',
                                         line=dict(color='black', width=1.5),
                                         marker=dict(size=4, color='black', opacity=0.7)))
                
                # Predictions
                if pc_model in ["Hierarchical", "Deep Hierarchical"]:
                    current_sigmas = sigmas if pc_model == "Hierarchical" else [100, 60, 30, 10, 3]
                    # Use a built-in color sequence
                    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
                    for i_pred, (p, s) in enumerate(zip(preds, current_sigmas)):
                        fig.add_trace(go.Scatter(x=window_time, y=p, mode='lines', name=f'Pred (σ={s})',
                                                 line=dict(color=colors[i_pred % len(colors)])))
                elif preds and preds[0].any():
                    fig.add_trace(go.Scatter(x=window_time, y=preds[0], mode='lines', name='Prediction', line=dict(color='#1f77b4')))

                # Anomaly Marker
                if is_anomaly:
                    fig.add_trace(go.Scatter(x=[window_time[-1]], y=[val], mode='markers', name='Anomaly',
                                             marker=dict(color='red', size=12, symbol='x')))

                # Event-Driven Markers
                if pc_model == "Event-Driven" and events is not None:
                    event_indices = np.where(events)[0]
                    if event_indices.size > 0:
                        fig.add_trace(go.Scatter(x=window_time[event_indices], y=window_data[event_indices],
                                                mode='markers', name='Update Event',
                                                marker=dict(color='orange', size=8, symbol='cross')))
                
                # Layout updates
                y_min_val = np.min(window_data)
                y_max_val = np.max(window_data)

                if preds and preds[0].any():
                    y_min_val = min(y_min_val, np.min(preds[0]))
                    y_max_val = max(y_max_val, np.max(preds[0]))

                buffer = (y_max_val - y_min_val) * 0.1 if (y_max_val - y_min_val) > 0 else 1
                yaxis_range = [y_min_val - buffer - 1, y_max_val + buffer + 1]

                fig.update_layout(
                    title=dict(text=f"{pc_model} Model", font=dict(size=16, family="Paperlogy")),
                    xaxis_title="Time (s)",
                    yaxis_title="Value",
                    yaxis_range=yaxis_range,
                    font=dict(family="Paperlogy", size=12),
                    legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
                    template="plotly_white",
                    margin=dict(l=40, r=40, b=40, t=40)
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            # Display a table with the most recent data points
            with table_placeholder.container():
                st.subheader("Recent Data Points")
                
                if len(window_data) > 0:
                    final_pred, final_err, final_threshold = None, None, 0

                    if preds and errs:
                        if pc_model == "Basic":
                            final_pred, final_err, final_threshold = preds[0], errs[0], threshold
                        elif pc_model in ["Hierarchical", "Deep Hierarchical"]:
                            current_thresholds = thresholds if pc_model == "Hierarchical" else [6.0, 4.0, 2.5, 1.5, 0.8]
                            final_pred, final_err, final_threshold = preds[-1], errs[-1], current_thresholds[-1]
                        elif pc_model in ["Event-Driven", "Precision-Weighting", "Active Inference"]:
                            final_pred, final_err, final_threshold = preds[0], errs[0], threshold

                    if final_pred is not None:
                        start_index = max(0, len(window_data) - num_rows_to_show)
                        
                        # --- Generate Anomaly Labels for the Table ---
                        anomaly_labels = []
                        if pc_model in ["Hierarchical", "Deep Hierarchical"]:
                            current_thresholds = thresholds if pc_model == "Hierarchical" else [6.0, 4.0, 2.5, 1.5, 0.8]
                            layer_names = ["Coarse", "Medium", "Fine", "Deeper", "Deepest"]
                            icons = {"Coarse": "🚨", "Medium": "⚠️", "Fine": "⚡️"}
                            
                            visible_errs = [err[start_index:] for err in errs]
                            for i_label in range(len(visible_errs[0])):
                                label = "🟢 No"
                                for layer_idx in range(len(current_thresholds)):
                                    if abs(visible_errs[layer_idx][i_label]) > current_thresholds[layer_idx]:
                                        layer_name = layer_names[layer_idx] if layer_idx < len(layer_names) else f"L{layer_idx+1}"
                                        icon = icons.get(layer_name, "🔴")
                                        label = f"{icon} {layer_name}"
                                        break
                                anomaly_labels.append(label)
                        else:
                            anomaly_labels = ["🔴 Yes" if abs(e) > final_threshold else "🟢 No" for e in final_err[start_index:]]

                        table_df = pd.DataFrame({
                            "Time": [dt.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3] for dt in window_time[start_index:]],
                            "Actual Data": np.round(window_data[start_index:], 2),
                            "Predicted Data": np.round(final_pred[start_index:], 2),
                            "Error": np.round(final_err[start_index:], 2),
                            "Anomaly": anomaly_labels
                        })
                        # Display a reversed, re-indexed view of the table for better UX, without modifying the original df
                        st.dataframe(table_df.iloc[::-1].reset_index(drop=True), use_container_width=True)

                        # --- Add Summary Statistics ---
                        st.subheader("Window Statistics")

                        total_points = len(window_data)
                        anomaly_count = 0
                        if pc_model in ["Hierarchical", "Deep Hierarchical"]:
                            current_thresholds = thresholds if pc_model == "Hierarchical" else [6.0, 4.0, 2.5, 1.5, 0.8]
                            for k in range(len(window_data)):
                                for i_stat in range(len(current_thresholds)):
                                    if abs(errs[i_stat][k]) > current_thresholds[i_stat]:
                                        anomaly_count += 1
                                        break
                        else:
                            anomaly_count = np.sum(np.abs(final_err) > final_threshold)
                        
                        anomaly_rate = (anomaly_count / total_points * 100) if total_points > 0 else 0

                        col1, col2, col3 = st.columns(3)
                        col1.metric("Total Points in Window", f"{total_points}")
                        col2.metric("Anomalies Detected", f"🔴 {anomaly_count}")
                        col3.metric("Anomaly Rate", f"{anomaly_rate:.2f}%")

                        # Data stats
                        st.markdown("---")
                        col4, col5 = st.columns(2)
                        with col4:
                            st.markdown("##### Actual Data Stats")
                            stats_actual = pd.DataFrame({
                                "Metric": ["Mean", "Std Dev", "Min", "Max"],
                                "Value": [f"{np.mean(window_data):.2f}", f"{np.std(window_data):.2f}", f"{np.min(window_data):.2f}", f"{np.max(window_data):.2f}"]
                            }).set_index("Metric")
                            st.dataframe(stats_actual, use_container_width=True)
                        
                        with col5:
                            st.markdown("##### Predicted Data Stats")
                            stats_pred = pd.DataFrame({
                                "Metric": ["Mean", "Std Dev", "Min", "Max"],
                                "Value": [f"{np.mean(final_pred):.2f}", f"{np.std(final_pred):.2f}", f"{np.min(final_pred):.2f}", f"{np.max(final_pred):.2f}"]
                            }).set_index("Metric")
                            st.dataframe(stats_pred, use_container_width=True)

        # --- Record data for final CSV export ---
        final_pred_for_point, final_err_for_point, anomaly_label_for_point = None, None, "🟢 No"
        if preds and errs:
            # For non-hierarchical models, get the prediction for the last point
            if pc_model in ["Basic", "Event-Driven", "Precision-Weighting", "Active Inference"]:
                final_pred_for_point, final_err_for_point = preds[0][-1], errs[0][-1]
                current_threshold = threshold
                if pc_model == 'Event-Driven': 
                    current_threshold = event_threshold
                elif pc_model == 'Active Inference':
                    # Use the threshold defined for Active Inference
                    pass # threshold is already set correctly
                
                if abs(final_err_for_point) > current_threshold:
                    anomaly_label_for_point = "🔴 Yes"
            # For hierarchical models, get the label from the tiered check
            elif pc_model in ["Hierarchical", "Deep Hierarchical"]:
                final_pred_for_point, final_err_for_point = preds[-1][-1], errs[-1][-1] # Use finest layer for raw values
                # Re-check anomaly status for the single last point
                current_thresholds = thresholds if pc_model == "Hierarchical" else [6.0, 4.0, 2.5, 1.5, 0.8]
                layer_names = ["Coarse", "Medium", "Fine", "Deeper", "Deepest"]
                icons = {"Coarse": "🚨", "Medium": "⚠️", "Fine": "⚡️"}
                for layer_idx in range(len(current_thresholds)):
                    if abs(errs[layer_idx][-1]) > current_thresholds[layer_idx]:
                        layer_name = layer_names[layer_idx] if layer_idx < len(layer_names) else f"L{layer_idx+1}"
                        icon = icons.get(layer_name, "🔴")
                        anomaly_label_for_point = f"{icon} {layer_name}"
                        break
        
        # Append data for the current step
        if final_pred_for_point is not None:
            full_run_data.append({
                "Time": t_datetime, "Actual Data": val, "Predicted Data": final_pred_for_point,
                "Error": final_err_for_point, "Anomaly": anomaly_label_for_point
            })
        else: # For the first few points before the window is full
             full_run_data.append({"Time": t_datetime, "Actual Data": val, "Predicted Data": np.nan, "Error": np.nan, "Anomaly": "N/A"})


        time.sleep(sleep_interval)

    st.success("Demo finished.")
    status_box.empty()

    # Store final results and parameters in session state
    st.session_state.results_df = pd.DataFrame(full_run_data)
    st.session_state.run_params = {'pc_model': pc_model, 'scenario': scenario}

    # Clear the placeholders and force a rerun to display the static results page
    placeholder.empty()
    table_placeholder.empty()
    st.rerun()


else:
    # --- This block runs on initial load and after a simulation is complete ---
    if st.session_state.get('results_df') is None:
        st.info("Configure parameters and click 'Start Demo' to begin the simulation.")
    else:
        # --- Display Static Results Page ---
        display_results_page(
            results_df=st.session_state.results_df,
            run_params=st.session_state.run_params,
            num_rows_to_show=num_rows_to_show
        )
