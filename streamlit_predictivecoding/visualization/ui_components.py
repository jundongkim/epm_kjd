import streamlit as st
from datetime import datetime
from config import (DEFAULT_PARAMETERS, SCENARIO_PARAMETERS, TABLE_DISPLAY_ROWS, 
                   WINDOW_SIZE, MODEL_OPTIONS, SCENARIO_OPTIONS)

# =======================
# UI Component Functions
# =======================

def create_sidebar_controls():
    """Sets up all sidebar controls and returns the configuration."""
    st.sidebar.title("Controls")
    
    # Model selection
    pc_model = st.sidebar.selectbox(
        "Choose Predictive Coding Model",
        MODEL_OPTIONS
    )
    
    # Scenario selection
    st.sidebar.header("Scenario Settings")
    scenario = st.sidebar.selectbox(
        "Choose Scenario", 
        SCENARIO_OPTIONS
    )
    
    # Get scenario-specific parameters
    scenario_params = get_scenario_parameters(scenario)
    
    # Get model-specific parameters
    model_params = get_model_parameters(pc_model)
    
    # Performance monitoring settings
    performance_params = get_performance_parameters()
    
    # Display settings
    display_params = get_display_parameters()
    
    # Combine all parameters
    all_params = {**scenario_params, **model_params, **performance_params, **display_params}
    
    return {
        'pc_model': pc_model,
        'scenario': scenario,
        'params': all_params
    }

def get_scenario_parameters(scenario):
    """Get parameters specific to the selected scenario."""
    params = {}
    
    if scenario == 'CSV Upload':
        params['uploaded_file'] = st.sidebar.file_uploader(
            "Upload your IoT data", type=['csv'],
            help="CSV file must have 'Time' and 'Actual Data' columns."
        )
        # Set dummy values for params not used in CSV mode
        return {**params, **_get_dummy_scenario_params()}
    
    # Common scenario parameters
    s_params = SCENARIO_PARAMETERS
    params.update({
        'amp': st.sidebar.slider("Amplitude", 
                                s_params['amp']['min'], 
                                s_params['amp']['max'], 
                                s_params['amp']['default']),
        'freq': st.sidebar.slider("Frequency (Hz)", 
                                 s_params['freq']['min'], 
                                 s_params['freq']['max'], 
                                 s_params['freq']['default']),
        'noise': st.sidebar.slider("Noise Level", 
                                  s_params['noise']['min'], 
                                  s_params['noise']['max'], 
                                  s_params['noise']['default']),
        'step_time': st.sidebar.slider("Step Time (sec)", 
                                      s_params['step_time']['min'], 
                                      s_params['step_time']['max'], 
                                      s_params['step_time']['default'])
    })
    
    st.sidebar.markdown("---")
    
    # Additional parameters
    params.update({
        'num_steps': st.sidebar.number_input("Total Data Points to Generate", 
                                           min_value=s_params['num_steps']['min'], 
                                           max_value=s_params['num_steps']['max'], 
                                           value=s_params['num_steps']['default'], 
                                           step=100),
        'start_date': st.sidebar.date_input("Start Date", value=datetime.now()),
        'use_seed': st.sidebar.checkbox("Use Fixed Random Seed", value=True, 
                                       help="Ensures the same random data is generated on each run"),
        'random_seed': st.sidebar.number_input("Random Seed", value=42, step=1)
    })
    
    # Anomaly injection parameters
    st.sidebar.header("Anomaly Injection")
    params.update({
        'num_anomalies': st.sidebar.number_input("Number of Anomalies to Inject", 
                                               min_value=s_params['num_anomalies']['min'], 
                                               max_value=s_params['num_anomalies']['max'], 
                                               value=s_params['num_anomalies']['default'], 
                                               step=1),
        'anomaly_magnitude': st.sidebar.slider("Anomaly Magnitude", 
                                             s_params['anomaly_magnitude']['min'], 
                                             s_params['anomaly_magnitude']['max'], 
                                             s_params['anomaly_magnitude']['default'],
                                             help="The value to add to the data to create a spike.")
    })
    
    return params

def get_model_parameters(pc_model):
    """Get parameters specific to the selected model."""
    st.sidebar.header(f"{pc_model} Settings")
    
    defaults = DEFAULT_PARAMETERS.get(pc_model, {})
    params = {}
    
    if pc_model in ["Hierarchical", "Deep Hierarchical", "Adaptive Hierarchical", "STDP Hierarchical"]:
        # Get default values from config.py (single source of truth)
        default_sigmas = ", ".join(map(str, defaults.get('sigmas', [50, 20, 5])))
        default_thresholds = ", ".join(map(str, defaults.get('thresholds', [3.0, 2.5, 2.0])))
        
        # Model-specific info messages
        if pc_model == "Deep Hierarchical":
            st.sidebar.info("A model with more layers. You can customize the number and values of layers.")
        elif pc_model == "Adaptive Hierarchical":
            st.sidebar.info("🧠 Brain-inspired model with learnable layer weights. Weights adapt based on prediction errors.")
        elif pc_model == "STDP Hierarchical":
            st.sidebar.info("⚡ STDP-based model with event-driven learning. Updates weights only when errors exceed thresholds.")
        
        sigmas_str = st.sidebar.text_input("Sigmas (comma-separated)", default_sigmas)
        thresholds_str = st.sidebar.text_input("Thresholds (comma-separated)", default_thresholds)
        
        try:
            params['sigmas'] = [int(s.strip()) for s in sigmas_str.split(',')]
            params['thresholds'] = [float(t.strip()) for t in thresholds_str.split(',')]
            
            if len(params['sigmas']) != len(params['thresholds']):
                st.sidebar.error("The number of sigmas must match the number of thresholds.")
                st.stop()
        except ValueError:
            st.sidebar.error("Please enter comma-separated numbers for sigmas and thresholds.")
            st.stop()
        
        # Additional parameters for Adaptive Hierarchical and STDP Hierarchical
        if pc_model in ["Adaptive Hierarchical", "STDP Hierarchical"]:
            st.sidebar.markdown("**🔬 Adaptive Learning Settings**")
            
            # Initial weights
            default_weights = ", ".join([str(w) for w in defaults.get('initial_weights', [0.5, 0.3, 0.2])])
            weights_str = st.sidebar.text_input("Initial Weights (comma-separated)", default_weights,
                                              help="Starting weights for each layer (coarse→fine hierarchy)")
            
            # Learning rates
            default_learning_rates = ", ".join([str(lr) for lr in defaults.get('learning_rates', [0.01, 0.02, 0.05])])
            learning_rates_str = st.sidebar.text_input("Learning Rates (comma-separated)", default_learning_rates,
                                                     help="How fast each layer adapts (0.01-0.1 recommended)")
            
            # Additional parameter for STDP model
            if pc_model == "STDP Hierarchical":
                default_event_thresholds = ", ".join([str(et) for et in defaults.get('event_thresholds', [1.5, 1.2, 0.9])])
                event_thresholds_str = st.sidebar.text_input("Event Thresholds (comma-separated)", default_event_thresholds,
                                                           help="Error thresholds for triggering weight updates")
            
            try:
                params['initial_weights'] = [float(w.strip()) for w in weights_str.split(',')]
                params['learning_rates'] = [float(lr.strip()) for lr in learning_rates_str.split(',')]
                
                if pc_model == "STDP Hierarchical":
                    params['event_thresholds'] = [float(et.strip()) for et in event_thresholds_str.split(',')]
                    if len(params['event_thresholds']) != len(params['sigmas']):
                        st.sidebar.error("Number of event thresholds must match number of layers.")
                        st.stop()
                
                if len(params['initial_weights']) != len(params['sigmas']):
                    st.sidebar.error("Number of initial weights must match number of layers.")
                    st.stop()
                if len(params['learning_rates']) != len(params['sigmas']):
                    st.sidebar.error("Number of learning rates must match number of layers.")
                    st.stop()
            except ValueError:
                st.sidebar.error("Please enter valid numbers for weights and learning rates.")
                st.stop()
    
    elif pc_model == "Basic":
        params.update({
            'sigma': st.sidebar.slider("Sigma", 1.0, 100.0, defaults['sigma']),
            'threshold': st.sidebar.slider("Anomaly Threshold", 0.1, 10.0, defaults['threshold'])
        })
    
    elif pc_model == "Event-Driven":
        params.update({
            'sigma': st.sidebar.slider("Sigma", 1.0, 100.0, defaults['sigma']),
            'threshold': st.sidebar.slider("Anomaly Threshold", 0.1, 10.0, defaults['threshold']),
            'event_threshold': st.sidebar.slider("Event Threshold", 0.1, 10.0, defaults['event_threshold'])
        })
    
    elif pc_model == "Precision-Weighting":
        params.update({
            'sigma': st.sidebar.slider("Sigma", 1.0, 100.0, defaults['sigma']),
            'threshold': st.sidebar.slider("Anomaly Threshold", 0.1, 10.0, defaults['threshold']),
            'sensory_precision': st.sidebar.slider("Sensory Precision", 0.1, 10.0, defaults['sensory_precision']),
            'model_precision': st.sidebar.slider("Model Precision", 0.1, 10.0, defaults['model_precision'])
        })
    
    elif pc_model == "Active Inference":
        st.sidebar.info("Active Inference model is designed to learn sine wave parameters.")
        
        if 'internal_model_params' not in st.session_state:
            st.session_state.internal_model_params = {
                'freq': defaults['initial_freq'], 
                'amp': defaults['initial_amp']
            }
        
        params.update({
            'sigma': st.sidebar.slider("Smoothing Sigma", 0.1, 20.0, defaults['sigma'],
                                     help="Controls the smoothing of the input data"),
            'threshold': st.sidebar.slider("Anomaly Threshold", 0.1, 10.0, defaults['threshold'])
        })
    
    return params

def get_performance_parameters():
    """Get performance monitoring parameters."""
    st.sidebar.header("🚀 Performance Monitoring")
    
    from config import PERFORMANCE_MONITORING_OPTIONS, DEFAULT_PERFORMANCE_LEVEL
    
    performance_level = st.sidebar.selectbox(
        "Performance Monitoring Level",
        options=list(PERFORMANCE_MONITORING_OPTIONS.keys()),
        index=list(PERFORMANCE_MONITORING_OPTIONS.keys()).index(DEFAULT_PERFORMANCE_LEVEL),
        format_func=lambda x: PERFORMANCE_MONITORING_OPTIONS[x]["name"],
        help="Choose performance monitoring level. Higher levels provide more details but slower execution."
    )
    
    performance_config = PERFORMANCE_MONITORING_OPTIONS[performance_level]
    
    # Show performance info in an expander
    with st.sidebar.expander("📋 Performance Details"):
        st.markdown(f"**{performance_config['description']}**")
        st.markdown("**Settings:**")
        st.write(f"- Profiling: {'✅' if performance_config['enable_profiling'] else '❌'}")
        st.write(f"- Memory Tracking: {'✅' if performance_config['enable_memory_tracking'] else '❌'}")
        st.write(f"- Operation Logging: {'✅' if performance_config['enable_operation_logging'] else '❌'}")
        
        if performance_config.get('log_threshold'):
            st.write(f"- Log Threshold: {performance_config['log_threshold']}s")
        if performance_config.get('memory_sample_interval'):
            st.write(f"- Memory Sample Interval: Every {performance_config['memory_sample_interval']} ops")
    
    return {'performance_level': performance_level}

def get_display_parameters():
    """Get display-related parameters."""
    st.sidebar.header("Display Settings")
    
    t_params = TABLE_DISPLAY_ROWS
    num_rows_to_show = st.sidebar.slider(
        "Rows in Recent Data Table",
        min_value=t_params['min'],
        max_value=t_params['max'],
        value=t_params['default'],
        step=t_params['step'],
        help="Number of recent data points to show in the table below the graph."
    )
    
    return {'num_rows_to_show': num_rows_to_show}

def _get_dummy_scenario_params():
    """Return dummy parameters for CSV upload scenario."""
    return {
        'amp': 1.0, 'freq': 0.1, 'noise': 0.0, 'step_time': 50,
        'num_steps': 0, 'use_seed': False, 'start_date': datetime.now().date(),
        'num_anomalies': 0, 'anomaly_magnitude': 0.0, 'random_seed': 42
    }

def display_anomaly_status(is_anomaly, anomaly_info, pc_model, status_box):
    """Display anomaly status in the status box."""
    if not is_anomaly:
        status_box.empty()
        return
        
    if pc_model in ["Hierarchical", "Deep Hierarchical"]:
        layer_name = anomaly_info.get('layer_name', 'Unknown')
        error = anomaly_info.get('error', 0)
        threshold = anomaly_info.get('threshold', 0)
        
        message = f"**{layer_name} Layer Anomaly:** Error {error:.2f} > Threshold {threshold}"
        icon = anomaly_info.get('icon', '🔴')
        
        if layer_name == "Coarse":
            status_box.error(f"{icon} {message} - Major trend shift detected!")
        elif layer_name == "Medium":
            status_box.warning(f"{icon} {message} - Pattern deviation detected.")
        else:
            status_box.info(f"{icon} {message} - Spike or sudden change detected.")
    else:
        # Standard anomaly display for other models
        t_datetime = anomaly_info.get('time', 'Unknown')
        error = anomaly_info.get('error', 0)
        status_box.warning(f"Anomaly detected at t={t_datetime}: error={error:.2f}", icon="⚡️") 