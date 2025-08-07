# =======================
# Configuration Constants
# =======================

# App Settings
WINDOW_SIZE = 200
DEFAULT_NUM_STEPS = 1000
DEFAULT_SLEEP_INTERVAL = 0.02
MIN_DATA_POINTS_FOR_PROCESSING = 10

# Default Model Parameters
DEFAULT_PARAMETERS = {
    'Basic': {
        'sigma': 20.0,
        'threshold': 1.5
    },
    'Hierarchical': {
        'sigmas': [50, 20, 5],
        'thresholds': [3.0, 2.5, 2.0]
    },
    'Deep Hierarchical': {
        'sigmas': [100, 60, 30, 10, 3],
        'thresholds': [6.0, 4.0, 2.5, 1.5, 0.8]
    },
    'Adaptive Hierarchical': {
        'sigmas': [80, 50, 20, 8, 3],  # 5 layers for more complex patterns
        'thresholds': [5.0, 4.0, 3.0, 2.5, 2.0],  # Corresponding thresholds
        'initial_weights': [0.4, 0.3, 0.2, 0.1, 0.05],  # Hierarchical weights (coarse→fine)
        'learning_rates': [0.1, 0.2, 0.3, 0.4, 0.5]  # Much more conservative learning rates
    },
    'STDP Hierarchical': {
        'sigmas': [80, 50, 20, 8, 3],  # 5 layers to match Adaptive
        'thresholds': [5.0, 4.0, 3.0, 2.5, 2.0],
        'initial_weights': [0.4, 0.3, 0.2, 0.1, 0.05],
        'learning_rates': [0.1, 0.2, 0.3, 0.4, 0.5],  # Higher learning rates for STDP
        'event_thresholds': [3.0, 2.5, 2.0, 1.5, 1.2]  # More selective thresholds for efficient learning
    },
    'Event-Driven': {
        'sigma': 20.0,
        'threshold': 1.5,
        'event_threshold': 2.0
    },
    'Precision-Weighting': {
        'sigma': 20.0,
        'threshold': 1.5,
        'sensory_precision': 5.0,
        'model_precision': 2.0
    },
    'Active Inference': {
        'sigma': 3.0,
        'threshold': 2.0,
        'initial_freq': 0.05,
        'initial_amp': 3.0
    }
}

# Scenario Parameters
SCENARIO_PARAMETERS = {
    'amp': {'min': 1.0, 'max': 10.0, 'default': 5.0},
    'freq': {'min': 0.01, 'max': 1.0, 'default': 0.1},
    'noise': {'min': 0.0, 'max': 5.0, 'default': 1.0},
    'step_time': {'min': 1, 'max': 100, 'default': 50},
    'num_steps': {'min': 200, 'max': 5000, 'default': 1000},
    'num_anomalies': {'min': 0, 'max': 20, 'default': 3},
    'anomaly_magnitude': {'min': 1.0, 'max': 50.0, 'default': 20.0}
}

# Model Specific Settings
LAYER_NAMES = ["Coarse", "Medium", "Fine", "Deeper", "Deepest"]
ANOMALY_ICONS = {
    "Coarse": "🚨", 
    "Medium": "⚠️", 
    "Fine": "⚡️",
    "Deeper": "🔴",
    "Deepest": "🔴"
}

# UI Settings
TABLE_DISPLAY_ROWS = {'min': 10, 'max': WINDOW_SIZE, 'default': 10, 'step': 10}

# Layer Configuration (moved from hardcoded values in app.py)
LAYER_ICONS = {"Coarse": "🚨", "Medium": "⚠️", "Fine": "⚡️", "Deeper": "🔴", "Deepest": "🔴"}

# Model Selection Options
MODEL_OPTIONS = [
    "Basic", 
    "Hierarchical", 
    "Deep Hierarchical", 
    "Event-Driven", 
    "Precision-Weighting", 
    "Active Inference", 
    "Adaptive Hierarchical", 
    "STDP Hierarchical"
]

# Scenario Options
SCENARIO_OPTIONS = ["Sine Wave", "Step Change", "Random Walk", "CSV Upload"]

# Colors for Plots
PLOT_COLORS = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']

# =======================
# Performance Monitoring Settings
# =======================

# Performance monitoring options
PERFORMANCE_MONITORING_OPTIONS = {
    "disabled": {
        "name": "🚫 Disabled (Fastest)",
        "description": "No performance monitoring - Maximum speed",
        "enable_profiling": False,
        "enable_memory_tracking": False,
        "enable_operation_logging": False,
        "log_threshold": None,
        "memory_sample_interval": None
    },
    "basic": {
        "name": "⚡ Basic (Fast)",
        "description": "Basic timing only - Minimal overhead",
        "enable_profiling": True,
        "enable_memory_tracking": False,
        "enable_operation_logging": False,
        "log_threshold": 1.0,  # Only log operations > 1 second
        "memory_sample_interval": None
    },
    "standard": {
        "name": "📊 Standard (Balanced)",
        "description": "Timing + simplified metrics - Moderate overhead",
        "enable_profiling": True,
        "enable_memory_tracking": True,
        "enable_operation_logging": True,
        "log_threshold": 0.5,  # Log operations > 500ms
        "memory_sample_interval": 100  # Sample every 100 operations
    },
    "detailed": {
        "name": "🔬 Detailed (Slow)",
        "description": "Full monitoring + detailed analysis - High overhead",
        "enable_profiling": True,
        "enable_memory_tracking": True,
        "enable_operation_logging": True,
        "log_threshold": 0.1,  # Log operations > 100ms
        "memory_sample_interval": 10  # Sample every 10 operations
    }
}

# Default performance monitoring level
DEFAULT_PERFORMANCE_LEVEL = "basic" 