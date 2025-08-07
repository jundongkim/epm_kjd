import streamlit as st
import numpy as np
import time
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import glob
import os
import logging
import warnings

# Suppress Streamlit warnings during parallel processing and initialization
logging.getLogger('streamlit').setLevel(logging.CRITICAL)
logging.getLogger('streamlit.runtime').setLevel(logging.CRITICAL)
logging.getLogger('streamlit.runtime.caching').setLevel(logging.CRITICAL)
logging.getLogger('streamlit.runtime.state').setLevel(logging.CRITICAL)
warnings.filterwarnings('ignore', category=UserWarning, module='streamlit')
warnings.filterwarnings('ignore', message='.*No runtime found.*')
warnings.filterwarnings('ignore', message='.*Session state does not function.*')
warnings.filterwarnings('ignore', message='.*to view a Streamlit app.*')

from visualization.ui_components import create_sidebar_controls, display_anomaly_status
from pc_lib.model_runner import create_model_runner
from pc_lib.data_loader import generate_simulation_data, load_data_from_csv
from pc_lib.utils import inject_custom_font
from pc_lib.visualization import display_results_page
from config import LAYER_NAMES, LAYER_ICONS, WINDOW_SIZE, PLOT_COLORS
from utils.performance_utils import patch_gaussian_filter

# Enable performance tracking for gaussian filters
patch_gaussian_filter()

# Import 3D visualization functions
try:
    from visualization.cylindrical_3d import (
        plot_cylindrical_3d, 
        plot_heatmap_unwrapped, 
        plot_complete_cylindrical_3d,
        plot_smooth_cylindrical_3d,
        plot_smooth_cylindrical_3d_with_range_selector,
        load_bar_data,
        COLOR_THEMES
    )
    CYLINDRICAL_3D_AVAILABLE = True
except ImportError:
    CYLINDRICAL_3D_AVAILABLE = False

# =======================
# Streamlit App
# =======================

# --- App Constants ---
window_size = WINDOW_SIZE
# run_time is now determined by num_steps

# --- Initialize session state for results ---
if 'results_df' not in st.session_state:
    st.session_state.results_df = None
if 'run_params' not in st.session_state:
    st.session_state.run_params = {}

# --- Font and Page Config ---
st.set_page_config(page_title="Real-time Predictive Coding Demo", layout="wide")
inject_custom_font("fonts/Paperlogy.ttf")

# --- Main Menu Selection (Sidebar Top) ---
st.sidebar.markdown("### 🎯 Application Mode")
menu_option = st.sidebar.selectbox(
    "Select Application Mode",
    ["Predictive Coding Demo", "MLFT - 3D Cylindrical Visualization"],
    index=0,
    label_visibility="collapsed"
)
st.sidebar.markdown("---")

if menu_option == "MLFT - 3D Cylindrical Visualization":
    # =======================
    # MLFT 3D Visualization Section
    # =======================
    
    st.title("🔬 MLFT - 3D Cylindrical Visualization")
    st.markdown("---")
    
    if not CYLINDRICAL_3D_AVAILABLE:
        st.error("❌ cylindrical_3d_visualization.py module not available. Please ensure the file is in the same directory.")
        st.stop()
    
    # Sidebar for file selection and visualization options
    st.sidebar.header("📁 File Selection")
    
    # Find available BAR and TR files
    iot_folder = "data/iot"
    if not os.path.exists(iot_folder):
        st.error(f"❌ '{iot_folder}' folder not found. Please ensure the data/iot folder exists with BAR/TR files.")
        st.stop()
    
    # Get available files
    bar_files = glob.glob(os.path.join(iot_folder, "BAR*.CSV")) + glob.glob(os.path.join(iot_folder, "BAR*.csv"))
    tr_files = glob.glob(os.path.join(iot_folder, "*TR.CSV")) + glob.glob(os.path.join(iot_folder, "*TR.csv"))
    
    all_files = sorted(bar_files + tr_files)
    
    if not all_files:
        st.error(f"❌ No BAR or TR files found in '{iot_folder}' folder.")
        st.stop()
    
    # File selection
    selected_file = st.sidebar.selectbox(
        "Select BAR/TR File",
        options=all_files,
        format_func=lambda x: os.path.basename(x)
    )
    
    st.sidebar.markdown("---")
    st.sidebar.header("🎛️ Visualization Options")
    
    # Visualization type selection
    viz_type = st.sidebar.selectbox(
        "Visualization Type",
        [
            "Basic 3D (Points + Tracks)",
            "3D Surface",
            "Combined (Surface + Points + Tracks)", 
            "Complete Surface (CH-A1↔CH-B5 Connected)",
            "Complete Surface + Points",
            "Smooth Surface (Channel Interpolated)",
            "Ultra-Smooth Surface (Channel + Point Interpolated)",
            "Heatmap (Unwrapped)"
        ]
    )
    
    # Orientation selection
    orientation = st.sidebar.selectbox(
        "Orientation",
        ["horizontal", "vertical"],
        format_func=lambda x: "⬆️ Vertical" if x == "vertical" else "➡️ Horizontal"
    )
    
    # Color theme selection
    color_theme = st.sidebar.selectbox(
        "Color Theme",
        options=list(COLOR_THEMES.keys()),
        format_func=lambda x: COLOR_THEMES[x]['name'],
        help="Select a color theme. Includes themes suitable for specialty steel materials."
    )
    
    # Show theme description
    if color_theme in COLOR_THEMES:
        st.sidebar.caption(f"📝 {COLOR_THEMES[color_theme]['description']}")
    
    # Additional options for complete surface and smooth surface
    if "Complete Surface" in viz_type:
        show_wireframe = st.sidebar.checkbox("Show Wireframe", value=True)
        show_surface = st.sidebar.checkbox("Show Surface", value=True)
        show_points = st.sidebar.checkbox("Show Points", value="Points" in viz_type)
    elif "Smooth Surface" in viz_type or "Ultra-Smooth" in viz_type:
        # Channel interpolation
        interpolation_factor = st.sidebar.slider("Channel Interpolation Factor", 2, 10, 5, 1, 
                                                help="Higher values create smoother circumferential surfaces")
        
        # Point interpolation (only for Ultra-Smooth)
        if "Ultra-Smooth" in viz_type:
            # Point interpolation options
            col_pt1, col_pt2 = st.sidebar.columns([3, 1])
            with col_pt1:
                point_interpolation_factor = st.slider("Point Interpolation Factor", 1, 20, 1, 1,
                                                      help="Higher values create denser point data")
            with col_pt2:
                point_full_range = st.checkbox("Full", value=False, 
                                             help="Maximum resolution (1mm intervals)")
            
            # Range selector
            with st.sidebar.expander("📏 Range Selection"):
                enable_range = st.checkbox("Enable Range Selection", value=False,
                                         help="Limit display to a specific point range for performance")
                if enable_range:
                    # Load data to get range
                    try:
                        temp_df, _ = load_bar_data(selected_file)
                        point_min = float(temp_df['Point'].min())
                        point_max = float(temp_df['Point'].max())
                        
                        # Streamlit range slider
                        point_range_values = st.slider(
                            "Select Point Range (mm)",
                            min_value=point_min,
                            max_value=point_max,
                            value=(point_min, min(point_min + 100, point_max)),
                            step=1.0,
                            help="Drag to select the range of points to display"
                        )
                        point_range = tuple(point_range_values)
                        
                        # Display selected range
                        st.caption(f"Selected: {point_range[0]:.1f} - {point_range[1]:.1f} mm "
                                 f"({point_range[1] - point_range[0]:.1f} mm range)")
                    except Exception as e:
                        point_range = None
                        st.warning(f"⚠️ Could not load data for range selection: {str(e)}")
                else:
                    point_range = None
        else:
            point_interpolation_factor = 1
            point_full_range = False
            point_range = None
        
        show_wireframe = st.sidebar.checkbox("Show Wireframe", value=False)
        show_original_points = st.sidebar.checkbox("Show Original Points", value=False)
        
        # Parallel processing options
        with st.sidebar.expander("⚡ Performance Settings"):
            use_parallel = st.checkbox("Enable Parallel Processing", value=True, 
                                     help="Use multiprocessing to speed up interpolation")
            if use_parallel:
                import multiprocessing as mp
                max_workers = mp.cpu_count()
                n_workers = st.slider("Number of Workers", 1, max_workers, min(4, max_workers), 1,
                                    help=f"Number of parallel processes (max: {max_workers})")
            else:
                n_workers = None
    else:
        # Set default values for other visualization types
        use_parallel = True
        n_workers = None
        point_interpolation_factor = 1
        point_full_range = False
        point_range = None
    
    st.sidebar.markdown("---")
    
    # Auto-refresh option
    auto_refresh = st.sidebar.checkbox("🔄 Auto Refresh", value=False)
    if auto_refresh:
        refresh_interval = st.sidebar.slider("Refresh Interval (seconds)", 1, 10, 3)
    
    # Manual refresh button
    if st.sidebar.button("🔄 Refresh Visualization", type="primary"):
        st.rerun()
    
    # Main content area - Full width for 3D visualization
    st.subheader(f"📊 {viz_type} - {os.path.basename(selected_file)}")
    
    # Create placeholder for the plot
    plot_placeholder = st.empty()
    
    try:
        # Load data and create visualization based on selection
        with st.spinner("🔄 Loading data and generating visualization..."):
            
            if viz_type == "Heatmap (Unwrapped)":
                fig = plot_heatmap_unwrapped(file_path=selected_file, color_theme=color_theme)
            
            elif "Smooth Surface" in viz_type and "Ultra-Smooth" not in viz_type:
                fig = plot_smooth_cylindrical_3d(
                    file_path=selected_file,
                    orientation=orientation,
                    interpolation_factor=interpolation_factor,
                    point_interpolation_factor=point_interpolation_factor,
                    point_full_range=point_full_range,
                    show_wireframe=show_wireframe,
                    show_original_points=show_original_points,
                    color_theme=color_theme,
                    use_parallel=use_parallel,
                    n_workers=n_workers
                )
            
            elif "Ultra-Smooth" in viz_type:
                fig = plot_smooth_cylindrical_3d_with_range_selector(
                    file_path=selected_file,
                    orientation=orientation,
                    interpolation_factor=interpolation_factor,
                    point_interpolation_factor=point_interpolation_factor,
                    point_full_range=point_full_range,
                    show_wireframe=show_wireframe,
                    show_original_points=show_original_points,
                    color_theme=color_theme,
                    use_parallel=use_parallel,
                    n_workers=n_workers,
                    point_range=point_range
                )
            
            elif "Complete Surface" in viz_type:
                if viz_type == "Complete Surface (CH-A1↔CH-B5 Connected)":
                    fig = plot_complete_cylindrical_3d(
                        file_path=selected_file,
                        orientation=orientation,
                        show_wireframe=show_wireframe,
                        show_surface=show_surface,
                        show_points=False,
                        color_theme=color_theme
                    )
                else:  # Complete Surface + Points
                    fig = plot_complete_cylindrical_3d(
                        file_path=selected_file,
                        orientation=orientation,
                        show_wireframe=False,
                        show_surface=show_surface,
                        show_points=show_points,
                        color_theme=color_theme
                    )
            
            else:
                # Regular cylindrical 3D visualizations
                if viz_type == "Basic 3D (Points + Tracks)":
                    show_surface_flag = False
                    show_points_flag = True
                    show_tracks_flag = True
                elif viz_type == "3D Surface":
                    show_surface_flag = True
                    show_points_flag = False
                    show_tracks_flag = False
                else:  # Combined
                    show_surface_flag = True
                    show_points_flag = True
                    show_tracks_flag = True
                
                fig = plot_cylindrical_3d(
                    file_path=selected_file,
                    orientation=orientation,
                    show_surface=show_surface_flag,
                    show_points=show_points_flag,
                    show_tracks=show_tracks_flag,
                    color_theme=color_theme
                )
            
            # Update title to include file name and increase height for better viewing
            current_title = fig.layout.title.text
            fig.update_layout(
                title=f"{current_title} - {os.path.basename(selected_file)}",
                height=800  # Increased height for better 3D viewing
            )
            
            # Display the plot with full width
            with plot_placeholder.container():
                st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"❌ Error generating visualization: {str(e)}")
        st.exception(e)
    
    # Auto-refresh functionality
    if auto_refresh:
        time.sleep(refresh_interval)
        st.rerun()
    
    # File Information Section (moved below 3D visualization)
    st.markdown("---")
    st.subheader("📋 File Information")
    
    try:
        # Load and display file information
        df, channels = load_bar_data(selected_file)
        
        # Create columns for better layout
        col_info1, col_info2, col_info3 = st.columns(3)
        
        with col_info1:
            st.markdown("**📄 File Details:**")
            st.write(f"- **File**: {os.path.basename(selected_file)}")
            st.write(f"- **Type**: {'TR File' if 'TR' in selected_file.upper() else 'BAR File'}")
            st.write(f"- **Rows**: {len(df):,}")
            st.write(f"- **Columns**: {len(df.columns)}")
            
            # Data range info
            if 'Point' in df.columns:
                valid_points = df['Point'].dropna()
                if len(valid_points) > 0:
                    st.write(f"- **Point Range**: {valid_points.min():.1f} ~ {valid_points.max():.1f} mm")
        
        with col_info2:
            st.markdown("**🔧 Available Channels:**")
            for i, channel in enumerate(channels[:5]):  # First 5 channels
                if channel in df.columns:
                    channel_data = df[channel].dropna()
                    if len(channel_data) > 0:
                        st.write(f"- **{channel}**: {channel_data.min():.3f} ~ {channel_data.max():.3f}")
                    else:
                        st.write(f"- **{channel}**: No data")
        
        with col_info3:
            st.markdown("**🔧 More Channels:**")
            for i, channel in enumerate(channels[5:]):  # Remaining channels
                if channel in df.columns:
                    channel_data = df[channel].dropna()
                    if len(channel_data) > 0:
                        st.write(f"- **{channel}**: {channel_data.min():.3f} ~ {channel_data.max():.3f}")
                    else:
                        st.write(f"- **{channel}**: No data")
        
        # Data Preview
        st.markdown("---")
        st.markdown("**📊 Data Preview:**")
        
        # Show first few rows of data
        preview_df = df.head(10)
        if 'Point' in preview_df.columns:
            # Format Point column
            preview_df = preview_df.copy()
            preview_df['Point'] = preview_df['Point'].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "")
        
        st.dataframe(preview_df, use_container_width=True, height=300)
        
    except Exception as e:
        st.error(f"❌ Error loading file information: {str(e)}")
    
    # Download section
    st.markdown("---")
    st.subheader("💾 Export Options")
    
    col_export1, col_export2 = st.columns(2)
    
    with col_export1:
        if st.button("📥 Download Current Visualization as HTML"):
            try:
                # Generate the current visualization
                if viz_type == "Heatmap (Unwrapped)":
                    fig = plot_heatmap_unwrapped(file_path=selected_file, color_theme=color_theme)
                elif "Smooth Surface" in viz_type and "Ultra-Smooth" not in viz_type:
                    fig = plot_smooth_cylindrical_3d(
                        file_path=selected_file, orientation=orientation,
                        interpolation_factor=interpolation_factor, point_interpolation_factor=point_interpolation_factor,
                        point_full_range=point_full_range, show_wireframe=show_wireframe, show_original_points=show_original_points, 
                        color_theme=color_theme, use_parallel=use_parallel, n_workers=n_workers
                    )
                elif "Ultra-Smooth" in viz_type:
                    fig = plot_smooth_cylindrical_3d_with_range_selector(
                        file_path=selected_file, orientation=orientation,
                        interpolation_factor=interpolation_factor, point_interpolation_factor=point_interpolation_factor,
                        point_full_range=point_full_range, show_wireframe=show_wireframe, show_original_points=show_original_points, 
                        color_theme=color_theme, use_parallel=use_parallel, n_workers=n_workers,
                        point_range=point_range
                    )
                elif "Complete Surface" in viz_type:
                    if viz_type == "Complete Surface (CH-A1↔CH-B5 Connected)":
                        fig = plot_complete_cylindrical_3d(
                            file_path=selected_file, orientation=orientation,
                            show_wireframe=show_wireframe, show_surface=show_surface, show_points=False, color_theme=color_theme
                        )
                    else:
                        fig = plot_complete_cylindrical_3d(
                            file_path=selected_file, orientation=orientation,
                            show_wireframe=False, show_surface=show_surface, show_points=show_points, color_theme=color_theme
                        )
                else:
                    show_surface_flag = viz_type != "Basic 3D (Points + Tracks)"
                    show_points_flag = viz_type != "3D Surface"
                    show_tracks_flag = viz_type != "3D Surface"
                    fig = plot_cylindrical_3d(
                        file_path=selected_file, orientation=orientation,
                        show_surface=show_surface_flag, show_points=show_points_flag, show_tracks=show_tracks_flag, color_theme=color_theme
                    )
                
                # Save to HTML string
                html_string = fig.to_html(include_plotlyjs='cdn')
                
                # Create download
                filename = f"{os.path.splitext(os.path.basename(selected_file))[0]}_{viz_type.replace(' ', '_')}_{orientation}.html"
                st.download_button(
                    label="⬇️ Download HTML",
                    data=html_string,
                    file_name=filename,
                    mime="text/html"
                )
                
            except Exception as e:
                st.error(f"❌ Error generating download: {str(e)}")
    
    with col_export2:
        st.info("💡 **Tip**: Use the download button to save interactive HTML visualizations for offline viewing or sharing.")
        
        if "Smooth Surface" in viz_type:
            if "Ultra-Smooth" in viz_type:
                total_channels = 10 * interpolation_factor
                point_text = "Full Range (1mm)" if point_full_range else f"{point_interpolation_factor}x"
                st.success(f"🌟 **Ultra-Smooth Surface**: Ch:{interpolation_factor}x + Pt:{point_text}")
                st.info(f"📊 **Enhanced Resolution**: {10} → {total_channels} channels + Point interpolation")
                if point_range:
                    st.info(f"📏 **Range**: {point_range[0]:.1f} - {point_range[1]:.1f} mm ({point_range[1] - point_range[0]:.1f} mm)")
            else:
                total_channels = 10 * interpolation_factor
                point_text = "Full Range (1mm)" if point_full_range else (f"{point_interpolation_factor}x" if point_interpolation_factor > 1 else "Original")
                if point_interpolation_factor > 1 or point_full_range:
                    st.success(f"🌟 **Smooth Surface**: Ch:{interpolation_factor}x + Pt:{point_text}")
                else:
                    st.success(f"🌟 **Smooth Surface**: {interpolation_factor}x channel interpolation ({10} → {total_channels} channels)")
        
        # Color theme info
        st.info(f"🎨 **Color Theme**: {COLOR_THEMES[color_theme]['name']} - {COLOR_THEMES[color_theme]['description']}")

else:
    # =======================
    # Original Predictive Coding Demo Section
    # =======================
    
    st.title("Real-time Predictive Coding")
    
    # --- Sidebar Controls ---
    controls = create_sidebar_controls()
    pc_model = controls['pc_model']
    scenario = controls['scenario']
    params = controls['params']

    # Extract individual parameters for compatibility
    uploaded_file = params.get('uploaded_file')
    if scenario != 'CSV Upload':
        amp = params['amp']
        freq = params['freq']
        noise = params['noise']
        step_time = params['step_time']
        num_steps = params['num_steps']
        start_date = params['start_date']
        use_seed = params['use_seed']
        random_seed = params['random_seed']
        num_anomalies = params['num_anomalies']
        anomaly_magnitude = params['anomaly_magnitude']
    else:
        # Set dummy values for CSV mode
        amp, freq, noise, step_time, num_steps, use_seed = 1.0, 0.1, 0.0, 50, 0, False
        num_anomalies, anomaly_magnitude = 0, 0.0
        start_date = datetime.now().date()

    # Extract model parameters
    if pc_model in ["Hierarchical", "Deep Hierarchical", "Adaptive Hierarchical", "STDP Hierarchical"]:
        sigmas = params['sigmas']
        thresholds = params['thresholds']
        if pc_model in ["Adaptive Hierarchical", "STDP Hierarchical"]:
            initial_weights = params['initial_weights']
            learning_rates = params['learning_rates']
            if pc_model == "STDP Hierarchical":
                event_thresholds = params['event_thresholds']
    elif pc_model in ["Basic", "Event-Driven", "Precision-Weighting"]:
        sigma = params['sigma']
        threshold = params['threshold']
        if pc_model == "Event-Driven":
            event_threshold = params['event_threshold']
        elif pc_model == "Precision-Weighting":
            sensory_precision = params['sensory_precision']
            model_precision = params['model_precision']
    elif pc_model == "Active Inference":
        if 'internal_model_params' not in st.session_state:
            st.session_state.internal_model_params = {'freq': 0.05, 'amp': 3.0}
        sigma = params['sigma']
        threshold = params['threshold']

    num_rows_to_show = params['num_rows_to_show']
    performance_level = params.get('performance_level', 'basic')  # Extract performance level


    if st.sidebar.button("Start Demo"):
        # --- Start of Simulation Block ---

        # Clear previous run results when starting a new demo
        st.session_state.results_df = None
        st.session_state.run_params = {}

        placeholder = st.empty()
        table_placeholder = st.empty()
        status_box = st.empty()

        # --- Data Loading and Preparation ---
        if scenario == "CSV Upload":
            if uploaded_file is None:
                st.error("Please upload a CSV file to run the demo.")
                st.stop()
            source_df = load_data_from_csv(uploaded_file)
            if source_df is None:
                st.stop()
            sleep_interval = 0.01  # Use a fast interval for pre-loaded data
        else:
            # Generate data for built-in scenarios using data_loader
            simulation_params = {
                'scenario': scenario,
                'amp': amp,
                'freq': freq,
                'noise': noise,
                'step_time': step_time,
                'num_steps': num_steps,
                'start_date': start_date,
                'use_seed': use_seed,
                'random_seed': random_seed,
                'num_anomalies': num_anomalies,
                'anomaly_magnitude': anomaly_magnitude
            }
            source_df = generate_simulation_data(simulation_params)
            sleep_interval = 20 / num_steps if num_steps > 0 else 0.02


        # --- Simulation Loop ---
        data = []
        time_axis = []
        full_run_data = [] 

        # Configure and start performance profiling
        from utils.performance_utils import global_profiler
        from config import PERFORMANCE_MONITORING_OPTIONS
        performance_config = PERFORMANCE_MONITORING_OPTIONS.get(performance_level, PERFORMANCE_MONITORING_OPTIONS['basic'])
        global_profiler.configure(performance_config)
        global_profiler.start_profiling()

        # Define the callback function for Active Inference to update its state
        def set_internal_model_params(new_params):
            st.session_state.internal_model_params = new_params

        if pc_model == "Active Inference":
            # Reset internal model at the start of each run
            st.session_state.internal_model_params = {'freq': 0.05, 'amp': 3.0}

        for i in range(len(source_df)):
            # Record memory usage periodically (only if monitoring is enabled)
            if performance_config.get('enable_memory_tracking', False) and i % 10 == 0:  # Every 10 steps
                global_profiler.record_memory_usage()
                
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
                # Create model runner and run model
                model_params = params.copy()
                model_runner = create_model_runner(pc_model, model_params)
                preds, errs, is_anomaly, anomaly_info = model_runner.run_model(window_data, numeric_window_time)
                
                # Display anomaly status using ui_components
                display_anomaly_status(is_anomaly, anomaly_info, pc_model, status_box)
                
                # Display Active Inference internal model status
                if pc_model == "Active Inference" and scenario in ["Sine Wave", "CSV Upload"]:
                    params_ai = st.session_state.internal_model_params
                    status_box.info(f"Internal Model: Freq={params_ai['freq']:.3f} Hz, Amp={params_ai['amp']:.2f}")
                
                # Get events for Event-Driven model
                events = getattr(model_runner, 'events', None)

                with placeholder.container():
                    fig = go.Figure()

                    # Actual Data
                    fig.add_trace(go.Scatter(x=window_time, y=window_data, mode='lines+markers', name='Actual Data',
                                             line=dict(color='black', width=1.5),
                                             marker=dict(size=4, color='black', opacity=0.7)))
                    
                    # Predictions
                    if pc_model in ["Hierarchical", "Deep Hierarchical", "Adaptive Hierarchical", "STDP Hierarchical"]:
                        for i_pred, (p, s) in enumerate(zip(preds, params['sigmas'])):
                            color = PLOT_COLORS[i_pred % len(PLOT_COLORS)]
                            pred_name = f'Pred (σ={s})'
                            if pc_model in ["Adaptive Hierarchical", "STDP Hierarchical"]:
                                # Show current weights in prediction labels
                                current_weights = getattr(model_runner, 'current_weights', params.get('initial_weights', [1.0]*len(params['sigmas'])))
                                if i_pred < len(current_weights):
                                    pred_name = f'Pred (w={current_weights[i_pred]:.2f})'
                                    if pc_model == "STDP Hierarchical":
                                        pred_name += f' [STDP]'
                            fig.add_trace(go.Scatter(x=window_time, y=p, mode='lines', name=pred_name,
                                                     line=dict(color=color)))
                    elif preds and len(preds[0]) > 0:
                        pred_data = preds[0]
                        
                        # For Event-Driven model, handle sparse predictions (NaN values)
                        if pc_model == "Event-Driven":
                            # Only plot non-NaN prediction points
                            valid_indices = ~np.isnan(pred_data)
                            if np.any(valid_indices):
                                fig.add_trace(go.Scatter(
                                    x=window_time[valid_indices], 
                                    y=pred_data[valid_indices], 
                                    mode='markers+lines', 
                                    name='Event Predictions',
                                    line=dict(color='#1f77b4'),
                                    marker=dict(size=8, color='#1f77b4')
                                ))
                        else:
                            # Regular prediction plotting for other models
                            if np.any(~np.isnan(pred_data)):
                                fig.add_trace(go.Scatter(x=window_time, y=pred_data, mode='lines', name='Prediction', line=dict(color='#1f77b4')))

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
                    
                    # STDP Learning Event Markers
                    if pc_model == "STDP Hierarchical" and events is not None:
                        # Events array should match window_data length
                        if len(events) == len(window_data):
                            event_indices = np.where(events)[0]
                            if event_indices.size > 0:
                                fig.add_trace(go.Scatter(x=window_time[event_indices], y=window_data[event_indices],
                                                        mode='markers', name='STDP Learning Event',
                                                        marker=dict(color='orange', size=12, symbol='star', 
                                                                   line=dict(width=2, color='darkorange'))))
                    
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
                            # Use model runner to get the final prediction and error
                            final_pred_pt, final_err_pt = model_runner.get_prediction_for_point(preds, errs)
                            if pc_model in ["Hierarchical", "Deep Hierarchical", "Adaptive Hierarchical", "STDP Hierarchical"]:
                                final_pred, final_err = preds[-1], errs[-1]
                                final_threshold = params['thresholds'][-1]
                            else:
                                final_pred, final_err = preds[0], errs[0]
                                final_threshold = params['threshold']

                        if final_pred is not None:
                            start_index = max(0, len(window_data) - num_rows_to_show)
                            
                            # --- Generate Anomaly Labels for the Table ---
                            anomaly_labels = []
                            if pc_model in ["Hierarchical", "Deep Hierarchical", "Adaptive Hierarchical", "STDP Hierarchical"]:
                                # Use only the finest layer for anomaly labeling
                                finest_layer_idx = len(params['thresholds']) - 1
                                finest_threshold = params['thresholds'][finest_layer_idx]
                                finest_err = errs[finest_layer_idx][start_index:]
                                
                                # Get correct layer name and icon
                                layer_name = (LAYER_NAMES[finest_layer_idx] 
                                             if finest_layer_idx < len(LAYER_NAMES) 
                                             else f"Layer {finest_layer_idx + 1}")
                                icon = LAYER_ICONS.get(layer_name, "🔴")
                                
                                for i_label in range(len(finest_err)):
                                    if abs(finest_err[i_label]) > finest_threshold:
                                        anomaly_labels.append(f"{icon} {layer_name}")
                                    else:
                                        anomaly_labels.append("🟢 No")
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
                            if pc_model in ["Hierarchical", "Deep Hierarchical", "Adaptive Hierarchical", "STDP Hierarchical"]:
                                # Use only the finest layer (last layer) for anomaly detection
                                finest_layer_idx = len(params['thresholds']) - 1
                                finest_threshold = params['thresholds'][finest_layer_idx]
                                anomaly_count = np.sum(np.abs(errs[finest_layer_idx]) > finest_threshold)
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
            if len(data) >= 10 and preds and errs:
                # Use model_runner to get predictions and anomaly labels for this point
                final_pred_for_point, final_err_for_point = model_runner.get_prediction_for_point(preds, errs)
                anomaly_label_for_point = model_runner.get_anomaly_label_for_point(errs)
                
                # Add STDP learning event information
                learning_event = False
                if pc_model == "STDP Hierarchical" and events is not None:
                    # Check if there's a learning event at the last position in the window
                    if len(events) > 0:
                        learning_event = events[-1]  # Last event in current window
                
                data_record = {
                    "Time": t_datetime, "Actual Data": val, "Predicted Data": final_pred_for_point,
                    "Error": final_err_for_point, "Anomaly": anomaly_label_for_point
                }
                
                # Add learning event column for STDP model
                if pc_model == "STDP Hierarchical":
                    data_record["Learning Event"] = learning_event
                
                full_run_data.append(data_record)
            else:
                # For the first few points before the window is full
                data_record = {"Time": t_datetime, "Actual Data": val, "Predicted Data": np.nan, "Error": np.nan, "Anomaly": "N/A"}
                if pc_model == "STDP Hierarchical":
                    data_record["Learning Event"] = False
                full_run_data.append(data_record)

            time.sleep(sleep_interval)

        st.success("Demo finished.")
        status_box.empty()

        # Stop profiling and store performance metrics
        performance_metrics = global_profiler.stop_profiling()
        st.session_state.performance_metrics = performance_metrics

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
