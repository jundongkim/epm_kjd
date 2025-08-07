"""
Utilities package for Predictive Coding project

This package contains:
- performance_utils: Performance monitoring and optimization utilities
- simulation_engine: Simulation engine for predictive coding models
"""

from .performance_utils import (
    PerformanceProfiler,
    performance_monitor,
    ModelComplexityAnalyzer,
    patch_gaussian_filter,
    global_profiler
)

# SimulationEngine import removed to avoid circular imports
# Import directly when needed: from utils.simulation_engine import SimulationEngine

__all__ = [
    # Performance utilities
    'PerformanceProfiler',
    'performance_monitor', 
    'ModelComplexityAnalyzer',
    'patch_gaussian_filter',
    'global_profiler',
    
    # Simulation engine - import directly to avoid circular imports
    # 'SimulationEngine'  # Use: from utils.simulation_engine import SimulationEngine
] 