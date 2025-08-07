import streamlit as st
import pandas as pd
import numpy as np
import time
import functools
import psutil
import tracemalloc
from typing import Any, Callable, Dict, List, Optional, Tuple
import logging
from scipy.ndimage import gaussian_filter1d as original_gaussian_filter1d

def conditional_st_cache(func=None, **kwargs):
    """
    Conditional Streamlit cache decorator that only applies caching when Streamlit runtime is available.
    This prevents warnings during parallel processing or standalone execution.
    """
    def decorator(func):
        try:
            # Check if Streamlit runtime is available
            if hasattr(st, 'runtime') and st.runtime.exists():
                # Use Streamlit caching when runtime is available
                return st.cache_data(**kwargs)(func)
            else:
                # Use simple function caching when Streamlit runtime is not available
                return functools.lru_cache(maxsize=128)(func)
        except:
            # Fallback to simple function caching if any error occurs
            return functools.lru_cache(maxsize=128)(func)
    
    if func is None:
        # Called with arguments: @conditional_st_cache(ttl=300)
        return decorator
    else:
        # Called without arguments: @conditional_st_cache
        return decorator(func)

# =======================
# Performance Optimization Utils
# =======================

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def tracked_gaussian_filter1d(input, sigma, **kwargs):
    """Wrapper for gaussian_filter1d to track filter operations."""
    start_time = time.perf_counter()
    result = original_gaussian_filter1d(input, sigma=sigma, **kwargs)
    end_time = time.perf_counter()
    
    # Record operation if profiler is active
    global_profiler.record_operation("gaussian_filter1d", start_time, end_time)
    return result

# Monkey patch scipy's gaussian_filter1d for global tracking
def patch_gaussian_filter():
    """Replace scipy's gaussian_filter1d with tracked version."""
    import scipy.ndimage
    scipy.ndimage.gaussian_filter1d = tracked_gaussian_filter1d

class PerformanceProfiler:
    """Comprehensive performance profiling for predictive coding models."""
    
    def __init__(self):
        self.reset()
        # Performance monitoring configuration
        self.config = None
        self.memory_sample_counter = 0
    
    def reset(self):
        """Reset all performance metrics."""
        self.execution_times = []
        self.memory_usage = []
        self.start_time = None
        self.memory_start = None
        self.operation_counts = {}
        self.is_profiling = False
        self.memory_sample_counter = 0
        
    def configure(self, config: Dict[str, Any]):
        """Configure performance monitoring based on settings."""
        self.config = config
        
    def start_profiling(self):
        """Start performance profiling."""
        self.reset()
        
        # Only start profiling if enabled
        if not self.config or not self.config.get('enable_profiling', False):
            return
            
        self.is_profiling = True
        self.start_time = time.perf_counter()
        
        # Start memory monitoring only if enabled
        if self.config.get('enable_memory_tracking', False):
            try:
                tracemalloc.start()
                self.memory_start = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            except Exception as e:
                logger.warning(f"Could not start memory monitoring: {e}")
    
    def record_operation(self, operation_name: str, start_time: float, end_time: float):
        """Record timing for a specific operation."""
        if not self.is_profiling or not self.config:
            return
            
        execution_time = end_time - start_time
        
        # Only record if logging is enabled
        if self.config.get('enable_operation_logging', False):
            self.execution_times.append(execution_time)
            
            if operation_name not in self.operation_counts:
                self.operation_counts[operation_name] = {'count': 0, 'total_time': 0.0, 'avg_time': 0.0}
            
            self.operation_counts[operation_name]['count'] += 1
            self.operation_counts[operation_name]['total_time'] += execution_time
            self.operation_counts[operation_name]['avg_time'] = (
                self.operation_counts[operation_name]['total_time'] / 
                self.operation_counts[operation_name]['count']
            )
    
    def record_memory_usage(self):
        """Record current memory usage."""
        if not self.is_profiling or not self.config:
            return
            
        if not self.config.get('enable_memory_tracking', False):
            return
        
        # Sample memory usage based on interval to reduce overhead
        memory_sample_interval = self.config.get('memory_sample_interval')
        if memory_sample_interval:
            self.memory_sample_counter += 1
            if self.memory_sample_counter % memory_sample_interval != 0:
                return
            
        try:
            current_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            self.memory_usage.append(current_memory)
        except Exception as e:
            logger.warning(f"Could not record memory usage: {e}")
    
    def stop_profiling(self) -> Dict[str, Any]:
        """Stop profiling and return comprehensive metrics."""
        if not self.is_profiling or not self.config:
            return {}
        
        total_time = time.perf_counter() - self.start_time if self.start_time else 0
        
        # Basic metrics always available
        result = {
            'total_time': total_time,
            'monitoring_level': self.config.get('name', 'Unknown'),
            'profiling_enabled': True
        }
        
        # Memory analysis (only if enabled)
        if self.config.get('enable_memory_tracking', False):
            memory_peak = max(self.memory_usage) if self.memory_usage else 0
            memory_avg = np.mean(self.memory_usage) if self.memory_usage else 0
            memory_growth = (memory_peak - self.memory_start) if self.memory_start else 0
            
            result.update({
                'memory_peak_mb': memory_peak,
                'memory_avg_mb': memory_avg,
                'memory_growth_mb': memory_growth,
            })
        
        # Timing analysis (only if operation logging enabled)
        if self.config.get('enable_operation_logging', False):
            total_execution_time = sum(self.execution_times)
            avg_execution_time = np.mean(self.execution_times) if self.execution_times else 0
            complexity_metrics = self._calculate_complexity_metrics()
            
            result.update({
                'total_execution_time': total_execution_time,
                'avg_execution_time': avg_execution_time,
                'operation_counts': self.operation_counts,
                'complexity_metrics': complexity_metrics,
                'num_operations': len(self.execution_times)
            })
        
        # Cleanup
        if self.config.get('enable_memory_tracking', False):
            try:
                tracemalloc.stop()
            except Exception:
                pass
        
        self.is_profiling = False
        return result
    
    def _calculate_complexity_metrics(self) -> Dict[str, Any]:
        """Calculate computational complexity indicators."""
        if not self.config.get('enable_operation_logging', False):
            return {}
            
        metrics = {
            'filter_operations': 0,
            'learning_operations': 0,
            'event_detections': 0,
            'fft_operations': 0,
            'total_operations': 0
        }
        
        for op_name, op_data in self.operation_counts.items():
            metrics['total_operations'] += op_data['count']
            
            if 'filter' in op_name.lower() or 'gaussian' in op_name.lower():
                metrics['filter_operations'] += op_data['count']
            elif 'learning' in op_name.lower() or 'weight' in op_name.lower():
                metrics['learning_operations'] += op_data['count']
            elif 'event' in op_name.lower():
                metrics['event_detections'] += op_data['count']
            elif 'fft' in op_name.lower():
                metrics['fft_operations'] += op_data['count']
        
        return metrics

# Global profiler instance
global_profiler = PerformanceProfiler()

def performance_monitor(operation_name: str = None):
    """Enhanced decorator to monitor function performance with detailed metrics."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Only monitor if profiling is active and configured
            if not global_profiler.is_profiling or not global_profiler.config:
                return func(*args, **kwargs)
                
            op_name = operation_name or func.__name__
            start_time = time.perf_counter()
            
            try:
                result = func(*args, **kwargs)
                end_time = time.perf_counter()
                execution_time = end_time - start_time
                
                # Record operation
                global_profiler.record_operation(op_name, start_time, end_time)
                
                # Log only if enabled and threshold met
                log_threshold = global_profiler.config.get('log_threshold')
                if log_threshold and execution_time > log_threshold:
                    logger.info(f"{op_name} took {execution_time:.3f}s")
                
                return result
            except Exception as e:
                end_time = time.perf_counter()
                execution_time = end_time - start_time
                logger.error(f"{op_name} failed after {execution_time:.3f}s: {str(e)}")
                raise
        return wrapper
    return decorator

class ModelComplexityAnalyzer:
    """Analyze computational complexity of different models."""
    
    @staticmethod
    def get_model_complexity(model_name: str, config: Dict) -> Dict[str, Any]:
        """Calculate expected computational complexity for a model."""
        complexity = {
            'model_name': model_name,
            'complexity_score': 1.0,
            'operations_per_step': 1,
            'memory_factor': 1.0,
            'description': '',
            'factors': []
        }
        
        if model_name == "Basic":
            complexity.update({
                'complexity_score': 1.0,
                'operations_per_step': 1,
                'description': 'Single gaussian filter operation',
                'factors': ['1 gaussian_filter1d call']
            })
            
        elif model_name == "Event-Driven":
            complexity.update({
                'complexity_score': 1.5,
                'operations_per_step': 2,
                'description': 'Initial filter + event-based local processing',
                'factors': ['1 initial gaussian_filter1d', 'Variable event processing']
            })
            
        elif model_name in ["Hierarchical", "Deep Hierarchical"]:
            num_layers = len(config.get('sigmas', [2.0, 1.5, 1.0]))
            complexity.update({
                'complexity_score': num_layers,
                'operations_per_step': num_layers,
                'description': f'Multiple layer processing ({num_layers} layers)',
                'factors': [f'{num_layers} gaussian_filter1d calls', 'Layer-wise processing']
            })
            
        elif model_name == "Precision-Weighting":
            complexity.update({
                'complexity_score': 2.0,
                'operations_per_step': 2,
                'description': 'Dual sigma processing with precision weighting',
                'factors': ['2 gaussian_filter1d calls', 'Precision calculations']
            })
            
        elif model_name == "Adaptive Hierarchical":
            num_layers = len(config.get('sigmas', [3.0, 2.0, 1.5, 1.2, 1.0]))
            complexity.update({
                'complexity_score': num_layers * 1.5,
                'operations_per_step': num_layers + 2,
                'description': f'Hierarchical processing with online learning ({num_layers} layers)',
                'factors': [f'{num_layers} gaussian_filter1d calls', 'Window-based MSE calculations', 'Weight updates']
            })
            
        elif model_name == "STDP Hierarchical":
            num_layers = len(config.get('sigmas', [3.0, 2.0, 1.5, 1.2, 1.0]))
            complexity.update({
                'complexity_score': num_layers * 1.8,
                'operations_per_step': num_layers + 3,
                'description': f'STDP learning with event detection ({num_layers} layers)',
                'factors': [f'{num_layers} gaussian_filter1d calls', 'Event-driven learning', 'STDP weight updates']
            })
            
        elif model_name == "Active Inference":
            complexity.update({
                'complexity_score': 2.5,
                'operations_per_step': 3,
                'description': 'Filter + periodic FFT analysis + parameter updates',
                'factors': ['1 gaussian_filter1d call', 'FFT analysis (every 10 steps)', 'Parameter optimization']
            })
        
        return complexity

@conditional_st_cache(ttl=300)  # Cache for 5 minutes
def cached_data_generation(scenario: str, params: Dict) -> pd.DataFrame:
    """Cache expensive data generation operations."""
    from pc_lib.data_loader import generate_simulation_data
    return generate_simulation_data(params)

@conditional_st_cache
def cached_csv_processing(file_content: bytes) -> pd.DataFrame:
    """Cache CSV file processing."""
    import io
    df = pd.read_csv(io.BytesIO(file_content))
    return df

class DataValidator:
    """Validates data integrity and format."""
    
    @staticmethod
    def validate_csv_data(df: pd.DataFrame) -> tuple[bool, str]:
        """Validate uploaded CSV data."""
        if df is None or df.empty:
            return False, "DataFrame is empty"
        
        required_columns = ['Time', 'Actual Data']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return False, f"Missing required columns: {missing_columns}"
        
        # Check for null values
        if df[required_columns].isnull().any().any():
            return False, "Data contains null values in required columns"
        
        # Check data types
        try:
            pd.to_datetime(df['Time'])
            pd.to_numeric(df['Actual Data'])
        except (ValueError, TypeError) as e:
            return False, f"Data type validation failed: {str(e)}"
        
        return True, "Data is valid"
    
    @staticmethod
    def validate_model_parameters(pc_model: str, params: Dict) -> tuple[bool, str]:
        """Validate model parameters."""
        try:
            if pc_model in ["Hierarchical", "Deep Hierarchical"]:
                if len(params.get('sigmas', [])) != len(params.get('thresholds', [])):
                    return False, "Number of sigmas must match number of thresholds"
                
                if any(s <= 0 for s in params.get('sigmas', [])):
                    return False, "All sigma values must be positive"
                
                if any(t <= 0 for t in params.get('thresholds', [])):
                    return False, "All threshold values must be positive"
            
            # Validate common parameters
            common_params = ['sigma', 'threshold']
            for param in common_params:
                if param in params and params[param] <= 0:
                    return False, f"{param} must be positive"
            
            return True, "Parameters are valid"
            
        except Exception as e:
            return False, f"Parameter validation error: {str(e)}"

class MemoryOptimizer:
    """Optimize memory usage for large datasets."""
    
    @staticmethod
    def optimize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """Optimize DataFrame memory usage."""
        # Convert float64 to float32 where possible
        float_cols = df.select_dtypes(include=['float64']).columns
        df[float_cols] = df[float_cols].astype('float32')
        
        # Convert int64 to smaller int types where possible
        int_cols = df.select_dtypes(include=['int64']).columns
        for col in int_cols:
            col_min = df[col].min()
            col_max = df[col].max()
            
            if col_min >= np.iinfo(np.int8).min and col_max <= np.iinfo(np.int8).max:
                df[col] = df[col].astype(np.int8)
            elif col_min >= np.iinfo(np.int16).min and col_max <= np.iinfo(np.int16).max:
                df[col] = df[col].astype(np.int16)
            elif col_min >= np.iinfo(np.int32).min and col_max <= np.iinfo(np.int32).max:
                df[col] = df[col].astype(np.int32)
        
        return df
    
    @staticmethod
    def limit_data_size(data: List, max_size: int = 10000) -> List:
        """Limit data size to prevent memory issues."""
        if len(data) > max_size:
            # Keep most recent data
            return data[-max_size:]
        return data

class ErrorHandler:
    """Centralized error handling."""
    
    @staticmethod
    def handle_simulation_error(error: Exception, step: int) -> bool:
        """Handle errors during simulation."""
        error_msg = f"Error at simulation step {step}: {str(error)}"
        logger.error(error_msg)
        
        if isinstance(error, MemoryError):
            st.error("⚠️ Memory limit exceeded. Try reducing the number of data points.")
            return False
        elif isinstance(error, ValueError):
            st.error(f"⚠️ Invalid data value: {str(error)}")
            return False
        elif isinstance(error, KeyError):
            st.error(f"⚠️ Missing required data field: {str(error)}")
            return False
        else:
            st.error(f"⚠️ Unexpected error: {str(error)}")
            return False
    
    @staticmethod
    def handle_model_error(error: Exception, model_name: str) -> None:
        """Handle model-specific errors."""
        error_msg = f"Error in {model_name} model: {str(error)}"
        logger.error(error_msg)
        
        if "sigma" in str(error).lower():
            st.error("⚠️ Invalid sigma parameter. Please check your smoothing values.")
        elif "threshold" in str(error).lower():
            st.error("⚠️ Invalid threshold parameter. Please check your anomaly detection thresholds.")
        else:
            st.error(f"⚠️ Model error in {model_name}: {str(error)}")

class ProgressTracker:
    """Track and display simulation progress."""
    
    def __init__(self, total_steps: int):
        self.total_steps = total_steps
        self.current_step = 0
        self.progress_bar = st.progress(0)
        self.status_text = st.empty()
        
    def update(self, step: int, message: str = ""):
        """Update progress bar and status."""
        self.current_step = step
        progress = min(step / self.total_steps, 1.0)
        
        self.progress_bar.progress(progress)
        
        if message:
            self.status_text.text(f"Step {step}/{self.total_steps}: {message}")
        else:
            self.status_text.text(f"Processing step {step}/{self.total_steps}")
    
    def complete(self):
        """Mark simulation as complete."""
        self.progress_bar.progress(1.0)
        self.status_text.text("Simulation completed!")
        
    def cleanup(self):
        """Clean up progress indicators."""
        self.progress_bar.empty()
        self.status_text.empty()

def safe_execute(func: Callable, *args, **kwargs) -> tuple[bool, Any]:
    """Safely execute a function and return success status with result."""
    try:
        result = func(*args, **kwargs)
        return True, result
    except Exception as e:
        logger.error(f"Safe execution failed for {func.__name__}: {str(e)}")
        return False, str(e)

def optimize_plotting_data(x_data: np.ndarray, y_data: np.ndarray, 
                          max_points: int = 1000) -> tuple[np.ndarray, np.ndarray]:
    """Optimize data for plotting by reducing points if necessary."""
    if len(x_data) <= max_points:
        return x_data, y_data
    
    # Use uniform sampling to reduce points
    indices = np.linspace(0, len(x_data) - 1, max_points, dtype=int)
    return x_data[indices], y_data[indices]

def get_system_info() -> Dict[str, Any]:
    """Get system information for debugging."""
    import psutil
    import platform
    
    return {
        'platform': platform.system(),
        'python_version': platform.python_version(),
        'cpu_count': psutil.cpu_count(),
        'memory_gb': round(psutil.virtual_memory().total / (1024**3), 2),
        'memory_available_gb': round(psutil.virtual_memory().available / (1024**3), 2)
    } 