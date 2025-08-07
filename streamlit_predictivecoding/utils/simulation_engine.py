import streamlit as st
import numpy as np
import pandas as pd
import time
from datetime import datetime, timedelta
import plotly.graph_objects as go

from pc_lib.data_loader import generate_simulation_data, load_data_from_csv
from config import WINDOW_SIZE, MIN_DATA_POINTS_FOR_PROCESSING, PLOT_COLORS
from visualization.ui_components import display_anomaly_status
from .performance_utils import global_profiler

# =======================
# Simulation Engine
# =======================

class SimulationEngine:
    """Handles the main simulation loop and data processing."""
    
    def __init__(self, config):
        self.config = config
        # Import here to avoid circular imports
        from pc_lib.model_runner import create_model_runner
        self.model_runner = create_model_runner(config['pc_model'], config)
        self.full_run_data = []
        
    def run_simulation(self, placeholder, table_placeholder, status_box):
        """Execute the main simulation loop."""
        # Start performance profiling
        global_profiler.start_profiling()
        
        try:
            # Prepare data source
            source_df = self._prepare_data_source()
            if source_df is None:
                return False
            
            # Initialize simulation state
            data, time_axis = [], []
            sleep_interval = self._calculate_sleep_interval(source_df)
            
            # Initialize Active Inference if needed
            self._initialize_active_inference()
            
            # Main simulation loop
            for i in range(len(source_df)):
                try:
                    # Record memory usage periodically
                    if i % 10 == 0:  # Every 10 steps
                        global_profiler.record_memory_usage()
                    
                    # Get current data point
                    row = source_df.iloc[i]
                    t_datetime = row['Time']
                    val = row['Actual Data']
                    
                    data.append(val)
                    time_axis.append(t_datetime)
                    
                    # Process window data
                    window_data = np.array(data[-WINDOW_SIZE:])
                    window_time = np.array(time_axis[-WINDOW_SIZE:])
                    
                    # Get numeric time for models that need it
                    numeric_window_start_index = max(0, i - WINDOW_SIZE + 1)
                    numeric_window_time = source_df['Numeric Time'].iloc[
                        numeric_window_start_index:i+1].values
                    
                    # Run model and update visualization
                    preds, errs = [], []
                    if len(data) >= MIN_DATA_POINTS_FOR_PROCESSING:
                        preds, errs = self._process_data_point(
                            window_data, window_time, numeric_window_time,
                            t_datetime, val, placeholder, status_box
                        )
                        
                        # Update data table with existing predictions
                        self._update_data_table(
                            window_data, window_time, preds, errs, table_placeholder
                        )
                    
                    # Record data for final export (with predictions if available)
                    if len(data) >= MIN_DATA_POINTS_FOR_PROCESSING and preds and errs:
                        self._record_data_point(t_datetime, val, window_data, numeric_window_time)
                    else:
                        # Record without predictions for initial points
                        self._record_data_point(t_datetime, val)
                    
                    time.sleep(sleep_interval)
                    
                except Exception as e:
                    st.error(f"Error in simulation at step {i}: {str(e)}")
                    return False
            
            # Finalize simulation
            self._finalize_simulation(status_box)
            
            # Stop profiling and store results
            performance_metrics = global_profiler.stop_profiling()
            st.session_state.performance_metrics = performance_metrics
            
            return True
            
        except Exception as e:
            # Stop profiling on error
            global_profiler.stop_profiling()
            st.error(f"Critical error in simulation: {str(e)}")
            return False
    
    def _prepare_data_source(self):
        """Prepare the data source based on scenario type."""
        if self.config['scenario'] == "CSV Upload":
            if self.config['uploaded_file'] is None:
                st.error("Please upload a CSV file to run the demo.")
                return None
            return load_data_from_csv(self.config['uploaded_file'])
        else:
            # Generate data for built-in scenarios
            if self.config['use_seed']:
                np.random.seed(self.config['random_seed'])
            return generate_simulation_data(self.config)
    
    def _calculate_sleep_interval(self, source_df):
        """Calculate appropriate sleep interval for simulation."""
        if self.config['scenario'] == "CSV Upload":
            return 0.01  # Fast interval for pre-loaded data
        else:
            num_steps = self.config['num_steps']
            return 20 / num_steps if num_steps > 0 else 0.02
    
    def _initialize_active_inference(self):
        """Initialize Active Inference model parameters if needed."""
        if self.config['pc_model'] == "Active Inference":
            st.session_state.internal_model_params = {
                'freq': 0.05, 'amp': 3.0
            }
    
    def _process_data_point(self, window_data, window_time, numeric_window_time,
                           t_datetime, val, placeholder, status_box):
        """Process a single data point through the model and update visualization."""
        # Run model
        preds, errs, is_anomaly, anomaly_info = self.model_runner.run_model(
            window_data, numeric_window_time
        )
        
        # Display anomaly status
        display_anomaly_status(
            is_anomaly, anomaly_info, self.config['pc_model'], status_box
        )
        
        # Display Active Inference internal model status
        if (self.config['pc_model'] == "Active Inference" and 
            self.config['scenario'] in ["Sine Wave", "CSV Upload"]):
            params = st.session_state.internal_model_params
            status_box.info(f"Internal Model: Freq={params['freq']:.3f} Hz, "
                          f"Amp={params['amp']:.2f}")
        
        # Update visualization
        self._update_visualization(
            window_data, window_time, preds, errs, val, is_anomaly, placeholder
        )
        
        # Return predictions and errors for further use
        return preds, errs
    
    def _update_visualization(self, window_data, window_time, preds, errs, 
                            current_val, is_anomaly, placeholder):
        """Update the main visualization plot."""
        with placeholder.container():
            fig = go.Figure()
            
            # Actual Data
            fig.add_trace(go.Scatter(
                x=window_time, y=window_data, mode='lines+markers', 
                name='Actual Data', line=dict(color='black', width=1.5),
                marker=dict(size=4, color='black', opacity=0.7)
            ))
            
            # Predictions
            self._add_prediction_traces(fig, window_time, preds)
            
            # Anomaly Marker
            if is_anomaly:
                fig.add_trace(go.Scatter(
                    x=[window_time[-1]], y=[current_val], mode='markers', 
                    name='Anomaly', marker=dict(color='red', size=12, symbol='x')
                ))
            
            # Event-Driven Markers
            if (self.config['pc_model'] == "Event-Driven" and 
                hasattr(self.model_runner, 'events') and 
                self.model_runner.events is not None):
                self._add_event_markers(fig, window_time, window_data)
            
            # STDP Learning Event Markers
            if (self.config['pc_model'] == "STDP Hierarchical" and 
                hasattr(self.model_runner, 'events') and 
                self.model_runner.events is not None):
                self._add_stdp_event_markers(fig, window_time, window_data)
            
            # Update layout
            self._update_plot_layout(fig, window_data, preds)
            
            st.plotly_chart(fig, use_container_width=True)
    
    def _add_prediction_traces(self, fig, window_time, preds):
        """Add prediction traces to the plot."""
        if self.config['pc_model'] in ["Hierarchical", "Deep Hierarchical", "Adaptive Hierarchical", "STDP Hierarchical"]:
            sigmas = self.config['sigmas']
            for i_pred, (p, s) in enumerate(zip(preds, sigmas)):
                color = PLOT_COLORS[i_pred % len(PLOT_COLORS)]
                pred_name = f'Pred (σ={s})'
                
                # Show current weights for Adaptive and STDP models
                if self.config['pc_model'] in ["Adaptive Hierarchical", "STDP Hierarchical"]:
                    current_weights = getattr(self.model_runner, 'current_weights', self.config.get('initial_weights', [1.0]*len(sigmas)))
                    if i_pred < len(current_weights):
                        pred_name = f'Pred (w={current_weights[i_pred]:.2f})'
                        if self.config['pc_model'] == "STDP Hierarchical":
                            pred_name += f' [STDP]'
                
                fig.add_trace(go.Scatter(
                    x=window_time, y=p, mode='lines', name=pred_name,
                    line=dict(color=color)
                ))
        elif preds and len(preds[0]) > 0:
            pred_data = preds[0]
            
            # For Event-Driven model, handle sparse predictions (NaN values)
            if self.config['pc_model'] == "Event-Driven":
                # Only plot non-NaN prediction points
                valid_indices = ~np.isnan(pred_data)
                if np.any(valid_indices):
                    fig.add_trace(go.Scatter(
                        x=window_time[valid_indices], 
                        y=pred_data[valid_indices], 
                        mode='markers+lines', 
                        name='Event Predictions',
                        line=dict(color=PLOT_COLORS[0]),
                        marker=dict(size=8, color=PLOT_COLORS[0])
                    ))
            else:
                # Regular prediction plotting for other models
                if np.any(~np.isnan(pred_data)):
                    fig.add_trace(go.Scatter(
                        x=window_time, y=pred_data, mode='lines', name='Prediction', 
                        line=dict(color=PLOT_COLORS[0])
                    ))
    
    def _add_event_markers(self, fig, window_time, window_data):
        """Add event markers for Event-Driven model."""
        event_indices = np.where(self.model_runner.events)[0]
        if event_indices.size > 0:
            fig.add_trace(go.Scatter(
                x=window_time[event_indices], y=window_data[event_indices],
                mode='markers', name='Update Event',
                marker=dict(color='orange', size=8, symbol='cross')
            ))
    
    def _add_stdp_event_markers(self, fig, window_time, window_data):
        """Add STDP learning event markers for STDP Hierarchical model."""
        if (hasattr(self.model_runner, 'events') and 
            self.model_runner.events is not None):
            
            # Events array should match window_data length
            if len(self.model_runner.events) == len(window_data):
                event_indices = np.where(self.model_runner.events)[0]
                
                if event_indices.size > 0:
                    fig.add_trace(go.Scatter(
                        x=window_time[event_indices], y=window_data[event_indices],
                        mode='markers', name='STDP Learning Event',
                        marker=dict(color='orange', size=12, symbol='star', 
                                   line=dict(width=2, color='darkorange'))
                    ))
    
    def _update_plot_layout(self, fig, window_data, preds):
        """Update the plot layout and axis ranges."""
        y_min = np.min(window_data)
        y_max = np.max(window_data)
        
        if preds and preds[0].any():
            y_min = min(y_min, np.min(preds[0]))
            y_max = max(y_max, np.max(preds[0]))
        
        buffer = (y_max - y_min) * 0.1 if (y_max - y_min) > 0 else 1
        yaxis_range = [y_min - buffer - 1, y_max + buffer + 1]
        
        fig.update_layout(
            title=dict(text=f"{self.config['pc_model']} Model", 
                      font=dict(size=16, family="Paperlogy")),
            xaxis_title="Time", yaxis_title="Value",
            yaxis_range=yaxis_range,
            font=dict(family="Paperlogy", size=12),
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
            template="plotly_white",
            margin=dict(l=40, r=40, b=40, t=40)
        )
    
    def _update_data_table(self, window_data, window_time, preds, errs, table_placeholder):
        """Update the data table display."""
        with table_placeholder.container():
            st.subheader("Recent Data Points")
            
            if preds and errs:
                num_rows = self.config['num_rows_to_show']
                start_index = max(0, len(window_data) - num_rows)
                
                # Generate anomaly labels
                anomaly_labels = []
                for i in range(start_index, len(window_data)):
                    label = self.model_runner.get_anomaly_label_for_point(errs, i)
                    anomaly_labels.append(label)
                
                # Get the appropriate prediction and error arrays
                if self.config['pc_model'] in ["Hierarchical", "Deep Hierarchical"]:
                    final_pred = preds[-1]  # Use finest layer
                    final_err = errs[-1]
                else:
                    final_pred = preds[0]
                    final_err = errs[0]
                
                table_df = pd.DataFrame({
                    "Time": [dt.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3] 
                           for dt in window_time[start_index:]],
                    "Actual Data": np.round(window_data[start_index:], 2),
                    "Predicted Data": np.round(final_pred[start_index:], 2),
                    "Error": np.round(final_err[start_index:], 2),
                    "Anomaly": anomaly_labels
                })
                
                # Display reversed table for better UX
                st.dataframe(table_df.iloc[::-1].reset_index(drop=True), 
                           use_container_width=True)
                
                # Add basic statistics
                self._display_window_statistics(window_data, final_pred, final_err)
    
    def _display_window_statistics(self, window_data, pred_data, err_data):
        """Display basic window statistics."""
        st.subheader("Window Statistics")
        
        total_points = len(window_data)
        threshold = self.config.get('threshold', 1.5)
        anomaly_count = np.sum(np.abs(err_data) > threshold)
        anomaly_rate = (anomaly_count / total_points * 100) if total_points > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Points in Window", f"{total_points}")
        col2.metric("Anomalies Detected", f"🔴 {anomaly_count}")
        col3.metric("Anomaly Rate", f"{anomaly_rate:.2f}%")
    
    def _record_data_point(self, t_datetime, val, window_data=None, numeric_window_time=None):
        """Record data point for final export."""
        pred, err = None, None
        anomaly_label = "N/A"
        learning_event = False
        
        # Only compute prediction if we have enough data
        if window_data is not None and len(window_data) >= MIN_DATA_POINTS_FOR_PROCESSING:
            try:
                # Run model to get predictions for this point
                preds, errs, _, _ = self.model_runner.run_model(window_data, numeric_window_time)
                
                if preds and errs:
                    # Get prediction and error for the last point
                    pred, err = self.model_runner.get_prediction_for_point(preds, errs, -1)
                    # Get anomaly label for the last point
                    anomaly_label = self.model_runner.get_anomaly_label_for_point(errs, -1)
                
                # Check for STDP learning events
                if (self.config['pc_model'] == "STDP Hierarchical" and 
                    hasattr(self.model_runner, 'events') and 
                    self.model_runner.events is not None):
                    # Check if there's a learning event at the last position in the window
                    if len(self.model_runner.events) > 0:
                        learning_event = self.model_runner.events[-1]  # Last event in current window
                    
            except Exception as e:
                # Log error but continue
                import logging
                logging.warning(f"Error computing prediction for data point: {str(e)}")
        
        data_record = {
            "Time": t_datetime, 
            "Actual Data": val, 
            "Predicted Data": pred if pred is not None else np.nan,
            "Error": err if err is not None else np.nan, 
            "Anomaly": anomaly_label
        }
        
        # Add learning event column for STDP model
        if self.config['pc_model'] == "STDP Hierarchical":
            data_record["Learning Event"] = learning_event
            
        self.full_run_data.append(data_record)
    
    def _finalize_simulation(self, status_box):
        """Finalize the simulation and store results."""
        st.success("Demo finished.")
        status_box.empty()
        
        # Store results in session state
        st.session_state.results_df = pd.DataFrame(self.full_run_data)
        st.session_state.run_params = {
            'pc_model': self.config['pc_model'], 
            'scenario': self.config['scenario']
        }

def run_simulation(config, placeholder, table_placeholder, status_box):
    """Factory function to create and run a simulation."""
    engine = SimulationEngine(config)
    return engine.run_simulation(placeholder, table_placeholder, status_box) 