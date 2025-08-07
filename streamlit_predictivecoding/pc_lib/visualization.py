import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from sklearn.metrics import r2_score
import functools

def conditional_st_cache(func):
    """
    Conditional Streamlit cache decorator that only applies caching when Streamlit runtime is available.
    This prevents warnings during parallel processing or standalone execution.
    """
    try:
        # Check if Streamlit runtime is available
        if hasattr(st, 'runtime') and st.runtime.exists():
            # Use Streamlit caching when runtime is available
            return st.cache_data(func)
        else:
            # Use simple function caching when Streamlit runtime is not available
            return functools.lru_cache(maxsize=128)(func)
    except:
        # Fallback to simple function caching if any error occurs
        return functools.lru_cache(maxsize=128)(func)

@conditional_st_cache
def convert_df_to_csv(df):
    """Converts a DataFrame to a CSV file for downloading."""
    return df.to_csv(index=False).encode('utf-8')

def display_results_page(results_df, run_params, num_rows_to_show):
    """
    Displays the entire static results page from a completed simulation run.
    """
    # Defensive copy and index reset to prevent errors from upstream modifications
    results_df = results_df.copy().reset_index()

    st.header(f"Final Results for: {run_params.get('pc_model')} - {run_params.get('scenario')}")

    # Ensure 'Time' column is present and in datetime format for plotting
    if 'Time' not in results_df.columns:
        st.error("A 'Time' column is missing in the final results data.")
        st.stop()
    results_df['Time'] = pd.to_datetime(results_df['Time'])

    # 1. Re-create Final Graph
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=results_df['Time'], y=results_df['Actual Data'], mode='lines+markers', name='Actual Data', line=dict(color='black', width=1.5), marker=dict(size=4, color='black', opacity=0.7)))
    
    # Handle Event-Driven model's sparse predictions
    if run_params.get('pc_model') == 'Event-Driven':
        # Only plot non-NaN prediction points for Event-Driven
        valid_predictions = results_df['Predicted Data'].notna()
        if valid_predictions.any():
            fig.add_trace(go.Scatter(
                x=results_df.loc[valid_predictions, 'Time'], 
                y=results_df.loc[valid_predictions, 'Predicted Data'], 
                mode='markers+lines', 
                name='Event Predictions',
                line=dict(color='#1f77b4'),
                marker=dict(size=6, color='#1f77b4')
            ))
    else:
        # Regular prediction plotting for other models
        fig.add_trace(go.Scatter(x=results_df['Time'], y=results_df['Predicted Data'], mode='lines', name='Prediction', line=dict(color='#1f77b4')))
    
    # Add STDP learning events if available
    if run_params.get('pc_model') == 'STDP Hierarchical' and 'Learning Event' in results_df.columns:
        learning_events = results_df[results_df['Learning Event'] == True]
        if not learning_events.empty:
            fig.add_trace(go.Scatter(
                x=learning_events['Time'], 
                y=learning_events['Actual Data'], 
                mode='markers', 
                name='STDP Learning Events',
                marker=dict(color='orange', size=12, symbol='star', line=dict(width=2, color='darkorange')),
                hovertemplate='<b>STDP Learning Event</b><br>Time: %{x}<br>Value: %{y:.2f}<extra></extra>'
            ))
    
    anomaly_points = results_df[results_df['Anomaly'].str.contains("🔴|🚨|⚠️|⚡️", na=False)]
    if not anomaly_points.empty:
        fig.add_trace(go.Scatter(x=anomaly_points['Time'], y=anomaly_points['Actual Data'], mode='markers', name='Anomaly', marker=dict(color='red', size=12, symbol='x')))
    
    fig.update_layout(
        title=dict(text=f"{run_params.get('pc_model')} Model", font=dict(size=16, family="Paperlogy")),
        xaxis_title="Time", yaxis_title="Value", font=dict(family="Paperlogy", size=12),
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        template="plotly_white", margin=dict(l=40, r=40, b=40, t=40)
    )
    st.plotly_chart(fig, use_container_width=True)

    # 2. Re-create Final Table
    st.subheader("Final Data Points")
    # Format the 'Time' column for display
    display_df = results_df.copy()
    display_df['Time'] = display_df['Time'].dt.strftime('%Y-%m-%d %H:%M:%S.%f').str[:-3]
    st.dataframe(display_df.tail(num_rows_to_show).reset_index(drop=True), use_container_width=True)
    
    # 3. Re-create Final Stats
    st.subheader("Overall Statistics")
    total_points = len(results_df)
    anomaly_count = len(anomaly_points)
    anomaly_rate = (anomaly_count / total_points * 100) if total_points > 0 else 0
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Points Generated", f"{total_points}")
    col2.metric("Total Anomalies Detected", f"🔴 {anomaly_count}")
    col3.metric("Overall Anomaly Rate", f"{anomaly_rate:.2f}%")

    # 4. Add Data/Prediction Statistics Comparison
    st.markdown("---")
    st.subheader("Data & Prediction Statistics Comparison")

    col_actual, col_pred = st.columns(2)

    with col_actual:
        st.markdown("##### Actual Data")
        actual_stats = results_df['Actual Data'].describe()
        mean_actual = actual_stats.get('mean', 0)
        std_actual = actual_stats.get('std', 0)
        # Robust CV calculation: only compute if mean is significantly different from 0
        # CV is only meaningful when |mean| > std/10 (avoid extreme CV values)
        cv_actual = (std_actual / abs(mean_actual)) if abs(mean_actual) > max(std_actual * 0.1, 1e-3) else np.nan
        
        stats_data_actual = {
            "Mean": f"{mean_actual:.2f}",
            "Std Dev": f"{std_actual:.2f}",
            "Min": f"{actual_stats.get('min', 0):.2f}",
            "Max": f"{actual_stats.get('max', 0):.2f}",
            "CV (%)": f"{min(cv_actual * 100, 999.99):.2f}" if not np.isnan(cv_actual) else "N/A"
        }
        st.dataframe(pd.DataFrame(stats_data_actual.items(), columns=["Metric", "Value"]).set_index("Metric"), use_container_width=True)

    with col_pred:
        st.markdown("##### Predicted Data")
        # Drop NaNs from prediction for accurate stats
        pred_series = results_df['Predicted Data'].dropna()
        if not pred_series.empty:
            pred_stats = pred_series.describe()
            mean_pred = pred_stats.get('mean', 0)
            std_pred = pred_stats.get('std', 0)
            # Robust CV calculation: only compute if mean is significantly different from 0
            # CV is only meaningful when |mean| > std/10 (avoid extreme CV values)
            cv_pred = (std_pred / abs(mean_pred)) if abs(mean_pred) > max(std_pred * 0.1, 1e-3) else np.nan
            
            stats_data_pred = {
                "Mean": f"{mean_pred:.2f}",
                "Std Dev": f"{std_pred:.2f}",
                "Min": f"{pred_stats.get('min', 0):.2f}",
                "Max": f"{pred_stats.get('max', 0):.2f}",
                "CV (%)": f"{min(cv_pred * 100, 999.99):.2f}" if not np.isnan(cv_pred) else "N/A"
            }
            st.dataframe(pd.DataFrame(stats_data_pred.items(), columns=["Metric", "Value"]).set_index("Metric"), use_container_width=True)
        else:
            st.info("No prediction data to analyze.")

    # 5. Add Actual vs. Predicted Scatter Plot with R² Score
    st.markdown("---")
    st.subheader("Model Performance: Actual vs. Predicted")
    
    # Filter out NaN values for accurate R² calculation
    valid_data = results_df[['Actual Data', 'Predicted Data']].dropna()
    
    if len(valid_data) > 1:  # Need at least 2 points for R² calculation
        actual_values = valid_data['Actual Data'].values
        predicted_values = valid_data['Predicted Data'].values
        
        # Calculate R² score
        r2 = r2_score(actual_values, predicted_values)
        
        # Create scatter plot
        fig_scatter = go.Figure()
        
        # Add scatter points
        fig_scatter.add_trace(go.Scatter(
            x=actual_values,
            y=predicted_values,
            mode='markers',
            name='Data Points',
            marker=dict(
                color='rgba(31, 119, 180, 0.6)',
                size=6,
                line=dict(width=0.5, color='rgba(31, 119, 180, 0.8)')
            ),
            hovertemplate='<b>Actual:</b> %{x:.2f}<br><b>Predicted:</b> %{y:.2f}<extra></extra>'
        ))
        
        # Add perfect prediction line (y = x)
        min_val = min(min(actual_values), min(predicted_values))
        max_val = max(max(actual_values), max(predicted_values))
        
        # Add some padding to the range for better visualization
        data_range = max_val - min_val
        padding = data_range * 0.05 if data_range > 0 else 1  # 5% padding
        axis_min = min_val - padding
        axis_max = max_val + padding
        
        fig_scatter.add_trace(go.Scatter(
            x=[axis_min, axis_max],
            y=[axis_min, axis_max],
            mode='lines',
            name='Perfect Prediction',
            line=dict(color='red', width=2, dash='dash'),
            hovertemplate='Perfect Prediction Line<extra></extra>'
        ))
        
        # Update layout
        fig_scatter.update_layout(
            title=dict(
                text=f"Actual vs. Predicted Values (R² = {r2:.4f})",
                font=dict(size=16, family="Paperlogy")
            ),
            xaxis_title="Actual Values",
            yaxis_title="Predicted Values",
            font=dict(family="Paperlogy", size=12),
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
            template="plotly_white",
            margin=dict(l=40, r=40, b=40, t=40),
            showlegend=True,
            # Set axis ranges based on actual data
            xaxis=dict(range=[axis_min, axis_max]),
            yaxis=dict(range=[axis_min, axis_max])
        )
        
        # Remove the equal aspect ratio constraint that was causing issues
        # fig_scatter.update_xaxes(scaleanchor="y", scaleratio=1)
        # fig_scatter.update_yaxes(scaleanchor="x", scaleratio=1)
        
        st.plotly_chart(fig_scatter, use_container_width=True)
        
        # Calculate additional performance metrics
        mse = np.mean((actual_values - predicted_values) ** 2)
        rmse = np.sqrt(mse)
        mae = np.mean(np.abs(actual_values - predicted_values))
        
        # Calculate MAPE (Mean Absolute Percentage Error) - handle division by zero
        non_zero_actual = actual_values[actual_values != 0]
        non_zero_predicted = predicted_values[actual_values != 0]
        if len(non_zero_actual) > 0:
            mape = np.mean(np.abs((non_zero_actual - non_zero_predicted) / non_zero_actual)) * 100
        else:
            mape = np.nan
        
        # Display comprehensive performance metrics
        st.subheader("Performance Metrics")
        
        # Create 4 columns for metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("R² Score", f"{r2:.4f}")
            st.caption("Coefficient of Determination\n(1.0 = perfect, 0.0 = no predictive power)")
        
        with col2:
            st.metric("RMSE", f"{rmse:.4f}")
            st.caption("Root Mean Square Error\n(lower is better)")
        
        with col3:
            st.metric("MSE", f"{mse:.4f}")
            st.caption("Mean Square Error\n(lower is better)")
        
        with col4:
            if not np.isnan(mape):
                st.metric("MAPE", f"{mape:.2f}%")
                st.caption("Mean Absolute Percentage Error\n(lower is better)")
            else:
                st.metric("MAPE", "N/A")
                st.caption("Cannot calculate MAPE\n(actual values contain zeros)")
        
        # Add MAE in a second row
        col5, col6, col7, col8 = st.columns(4)
        
        with col5:
            st.metric("MAE", f"{mae:.4f}")
            st.caption("Mean Absolute Error\n(lower is better)")
        
        with col6:
            # Calculate correlation coefficient
            correlation = np.corrcoef(actual_values, predicted_values)[0, 1]
            st.metric("Correlation", f"{correlation:.4f}")
            st.caption("Pearson Correlation\n(1.0 = perfect positive correlation)")
        
        with col7:
            # Calculate prediction bias (mean error)
            bias = np.mean(predicted_values - actual_values)
            st.metric("Bias", f"{bias:.4f}")
            st.caption("Mean Prediction Bias\n(0.0 = unbiased)")
        
        with col8:
            # Calculate prediction efficiency (normalized RMSE)
            actual_std = np.std(actual_values)
            if actual_std > 0:
                efficiency = 1 - (rmse / actual_std)
                st.metric("Efficiency", f"{efficiency:.4f}")
                st.caption("Prediction Efficiency\n(1.0 = perfect, 0.0 = no skill)")
            else:
                st.metric("Efficiency", "N/A")
                st.caption("Cannot calculate efficiency\n(no variance in actual data)")
        
        # Add Computational Performance Metrics
        st.markdown("---")
        
        # Get model complexity analysis
        from utils.performance_utils import ModelComplexityAnalyzer, global_profiler
        complexity_analyzer = ModelComplexityAnalyzer()
        model_complexity = complexity_analyzer.get_model_complexity(
            run_params.get('pc_model'), run_params
        )
        
        # Get profiling results if available
        performance_metrics = {}
        if hasattr(st.session_state, 'performance_metrics'):
            performance_metrics = st.session_state.performance_metrics
        
        # Check if performance monitoring was enabled
        monitoring_enabled = performance_metrics.get('profiling_enabled', False)
        monitoring_level = performance_metrics.get('monitoring_level', 'Unknown')
        
        # Display header based on monitoring status
        if monitoring_enabled:
            st.subheader(f"🚀 Computational Performance Metrics - {monitoring_level}")
        else:
            st.subheader("🚀 Computational Performance Metrics - Monitoring Disabled")
            st.info("💡 **Performance monitoring was disabled for maximum execution speed.** "
                   "To see detailed metrics, enable performance monitoring in the sidebar.")
            st.markdown("**Estimates based on model complexity:**")
        
        # Debug: Show what performance data is available
        with st.expander("🔧 Debug: Performance Data Status"):
            if performance_metrics:
                st.write(f"✅ Performance monitoring: **{monitoring_level}**")
                if monitoring_enabled:
                    for key, value in performance_metrics.items():
                        if isinstance(value, dict):
                            st.write(f"- {key}: {len(value)} items")
                        else:
                            st.write(f"- {key}: {value}")
                else:
                    st.write("⚡ Performance monitoring was disabled for maximum speed")
            else:
                st.write("❌ No performance metrics found in session state")
        
        # Display computational complexity
        col_comp1, col_comp2, col_comp3, col_comp4 = st.columns(4)
        
        with col_comp1:
            st.metric("Complexity Score", f"{model_complexity['complexity_score']:.1f}")
            st.caption("Relative computational complexity\n(1.0 = Basic model)")
        
        with col_comp2:
            st.metric("Operations/Step", f"{model_complexity['operations_per_step']}")
            st.caption("Expected operations per timestep\n(approximate)")
        
        with col_comp3:
            if performance_metrics.get('total_time'):
                total_time = performance_metrics['total_time']
                st.metric("Total Time", f"{total_time:.3f}s")
                st.caption("Total simulation time\n(wall clock time)")
            else:
                # Estimate time based on data points and expected performance
                num_points = len(results_df)
                estimated_time = num_points * model_complexity['complexity_score'] * 0.001  # rough estimate
                st.metric("Total Time", f"~{estimated_time:.3f}s")
                st.caption("Estimated time\n(profiling disabled)")
        
        with col_comp4:
            if performance_metrics.get('avg_execution_time'):
                avg_time_ms = performance_metrics['avg_execution_time'] * 1000
                st.metric("Avg Time/Op", f"{avg_time_ms:.2f}ms")
                st.caption("Average operation time\n(milliseconds)")
            else:
                # Estimate operation time
                estimated_op_time = model_complexity['complexity_score'] * 0.5  # rough estimate in ms
                st.metric("Avg Time/Op", f"~{estimated_op_time:.1f}ms")
                st.caption("Estimated time per operation\n(profiling disabled)")
        
        # Memory and throughput metrics
        col_comp5, col_comp6, col_comp7, col_comp8 = st.columns(4)
        
        with col_comp5:
            if performance_metrics.get('memory_peak_mb'):
                memory_peak = performance_metrics['memory_peak_mb']
                st.metric("Peak Memory", f"{memory_peak:.1f}MB")
                st.caption("Maximum memory usage\n(during simulation)")
            else:
                # Estimate memory usage
                estimated_memory = 50 + (len(results_df) * model_complexity['complexity_score'] * 0.01)
                st.metric("Peak Memory", f"~{estimated_memory:.1f}MB")
                st.caption("Estimated memory usage\n(monitoring disabled)")
        
        with col_comp6:
            if performance_metrics.get('memory_growth_mb'):
                memory_growth = performance_metrics['memory_growth_mb']
                st.metric("Memory Growth", f"{memory_growth:.1f}MB")
                st.caption("Memory increase during simulation\n(baseline to peak)")
            else:
                # Estimate memory growth
                estimated_growth = len(results_df) * model_complexity['complexity_score'] * 0.005
                st.metric("Memory Growth", f"~{estimated_growth:.1f}MB")
                st.caption("Estimated memory growth\n(monitoring disabled)")
        
        with col_comp7:
            if performance_metrics.get('total_time') and performance_metrics.get('total_time') > 0:
                points_per_second = len(results_df) / performance_metrics['total_time']
                st.metric("Throughput", f"{points_per_second:.1f} pts/s")
                st.caption("Data points processed per second\n(processing rate)")
            else:
                # Estimate throughput based on complexity
                estimated_throughput = max(10, 1000 / model_complexity['complexity_score'])
                st.metric("Throughput", f"~{estimated_throughput:.0f} pts/s")
                st.caption("Estimated throughput\n(based on model complexity)")
        
        with col_comp8:
            if performance_metrics.get('num_operations'):
                num_ops = performance_metrics['num_operations']
                st.metric("Total Operations", f"{num_ops}")
                st.caption("Total computational operations\n(recorded during simulation)")
            else:
                # Estimate total operations
                estimated_ops = len(results_df) * model_complexity['operations_per_step']
                st.metric("Total Operations", f"~{estimated_ops}")
                st.caption("Estimated operations\n(data points × ops/step)")
        
        # Model complexity details
        with st.expander("🔍 Model Complexity Details"):
            st.markdown(f"**Model:** {model_complexity['model_name']}")
            st.markdown(f"**Description:** {model_complexity['description']}")
            
            st.markdown("**Computational Factors:**")
            for factor in model_complexity['factors']:
                st.markdown(f"• {factor}")
            
            if performance_metrics.get('complexity_metrics'):
                complexity_metrics = performance_metrics['complexity_metrics']
                st.markdown("**Recorded Operations:**")
                
                metrics_data = []
                if complexity_metrics['filter_operations'] > 0:
                    metrics_data.append(["Filter Operations", complexity_metrics['filter_operations']])
                if complexity_metrics['learning_operations'] > 0:
                    metrics_data.append(["Learning Operations", complexity_metrics['learning_operations']])
                if complexity_metrics['event_detections'] > 0:
                    metrics_data.append(["Event Detections", complexity_metrics['event_detections']])
                if complexity_metrics['fft_operations'] > 0:
                    metrics_data.append(["FFT Operations", complexity_metrics['fft_operations']])
                
                if metrics_data:
                    complexity_df = pd.DataFrame(metrics_data, columns=["Operation Type", "Count"])
                    st.dataframe(complexity_df, use_container_width=True)
            
            if performance_metrics.get('operation_counts'):
                st.markdown("**Detailed Operation Timing:**")
                op_data = []
                for op_name, op_stats in performance_metrics['operation_counts'].items():
                    op_data.append([
                        op_name,
                        op_stats['count'],
                        f"{op_stats['total_time']:.3f}s",
                        f"{op_stats['avg_time']*1000:.2f}ms"
                    ])
                
                if op_data:
                    op_df = pd.DataFrame(op_data, columns=[
                        "Operation", "Count", "Total Time", "Avg Time"
                    ])
                    st.dataframe(op_df, use_container_width=True)
        
        # Performance comparison guide
        with st.expander("📊 Performance Interpretation Guide"):
            st.markdown("""
            **Complexity Score:**
            - 1.0 = Basic model (single gaussian filter)
            - 1.5-2.0 = Simple enhancement (event-driven, precision weighting)
            - 3.0-5.0 = Hierarchical models (multiple layers)
            - 7.5+ = Advanced learning models (adaptive, STDP)
            
            **Throughput Benchmarks:**
            - > 1000 pts/s = Excellent (real-time capable)
            - 100-1000 pts/s = Good (near real-time)
            - 10-100 pts/s = Moderate (batch processing)
            - < 10 pts/s = Slow (complex models, large datasets)
            
            **Memory Usage:**
            - < 50MB = Low memory footprint
            - 50-200MB = Moderate memory usage
            - 200-500MB = High memory usage
            - > 500MB = Very high memory usage
            
            **Operation Time:**
            - < 1ms = Very fast
            - 1-10ms = Fast
            - 10-50ms = Moderate
            - 50-100ms = Slow
            - > 100ms = Very slow
            
            **Model Trade-offs:**
            - Basic: Fastest, lowest memory, simple predictions
            - Event-Driven: Variable performance, event-dependent
            - Hierarchical: Linear scaling with layers, better accuracy
            - Adaptive/STDP: Highest complexity, learning capability
            - Active Inference: Moderate complexity, parameter adaptation
            """)

        # Overall interpretation
        st.markdown("---")
        if r2 >= 0.9:
            interpretation = "🟢 **Excellent prediction accuracy**"
        elif r2 >= 0.7:
            interpretation = "🟡 **Good prediction accuracy**"
        elif r2 >= 0.5:
            interpretation = "🟠 **Moderate prediction accuracy**"
        elif r2 >= 0.3:
            interpretation = "🔴 **Poor prediction accuracy**"
        else:
            interpretation = "🔴 **Very poor prediction accuracy**"
        
        # Add performance assessment
        if performance_metrics.get('total_time'):
            points_per_second = len(results_df) / performance_metrics['total_time'] if performance_metrics['total_time'] > 0 else 0
            if points_per_second > 1000:
                perf_interpretation = "⚡ **Excellent computational performance**"
            elif points_per_second > 100:
                perf_interpretation = "🚀 **Good computational performance**"
            elif points_per_second > 10:
                perf_interpretation = "⏱️ **Moderate computational performance**"
            else:
                perf_interpretation = "🐌 **Slow computational performance**"
        else:
            perf_interpretation = "📊 **Performance data not available**"
        
        st.markdown(f"### Overall Model Performance: {interpretation}")
        st.markdown(f"### Computational Performance: {perf_interpretation}")
        
        # Add interpretation guidelines
        with st.expander("📊 Metric Interpretation Guide"):
            st.markdown("""
            **R² (Coefficient of Determination):**
            - 1.0 = Perfect prediction
            - 0.9-1.0 = Excellent
            - 0.7-0.9 = Good
            - 0.5-0.7 = Moderate
            - 0.3-0.5 = Poor
            - < 0.2 = Very poor
            
            **RMSE/MSE (Root Mean Square Error / Mean Square Error):**
            - Lower values indicate better performance
            - RMSE is in the same units as the original data
            - MSE penalizes larger errors more heavily
            
            **MAE (Mean Absolute Error):**
            - Average absolute difference between actual and predicted
            - Less sensitive to outliers than RMSE
            - Lower values indicate better performance
            
            **MAPE (Mean Absolute Percentage Error):**
            - Percentage-based error metric
            - < 10% = Highly accurate
            - 10-20% = Good accuracy
            - 20-50% = Reasonable accuracy
            - > 50% = Poor accuracy
            
            **Correlation:**
            - Measures linear relationship strength
            - 1.0 = Perfect positive correlation
            - 0.0 = No linear relationship
            - -1.0 = Perfect negative correlation
            
            **Bias:**
            - Average prediction error (predicted - actual)
            - Positive = Model tends to overpredict
            - Negative = Model tends to underpredict
            - 0.0 = Unbiased predictions
            
            **Efficiency:**
            - Normalized prediction skill
            - 1.0 = Perfect prediction skill
            - 0.0 = No prediction skill (as good as using mean)
            - < 0.0 = Worse than using mean
            """)
        
    
    else:
        st.warning("Insufficient data points for scatter plot analysis.")

    # 6. Display Download Button
    st.markdown("---")
    st.subheader("Download Full Report")
    st.markdown("Click the button below to download the complete data and analysis results from the simulation as a CSV file.")
    
    csv_data = convert_df_to_csv(results_df)
    
    st.download_button(
       label="Download data as CSV",
       data=csv_data,
       file_name=f"pc_demo_results_{run_params.get('pc_model')}_{run_params.get('scenario')}.csv",
       mime="text/csv",
    ) 