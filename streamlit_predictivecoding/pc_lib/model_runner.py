import numpy as np
import streamlit as st
from .models import (
    basic_predictive_coding,
    hierarchical_predictive_coding,
    event_driven_predictive_coding,
    precision_weighted_predictive_coding,
    deep_hierarchical_predictive_coding,
    adaptive_hierarchical_predictive_coding,
    stdp_adaptive_hierarchical_predictive_coding,
    active_inference
)
from config import LAYER_NAMES, ANOMALY_ICONS

# =======================
# Model Runner Functions
# =======================

class ModelRunner:
    """Handles model execution and anomaly detection."""
    
    def __init__(self, pc_model, params):
        self.pc_model = pc_model
        self.params = params
        self.events = None
        self.current_weights = None  # For Adaptive Hierarchical model
        
    def run_model(self, window_data, numeric_window_time=None):
        """Run the specified model and return predictions, errors, and anomaly info."""
        preds, errs = [], []
        is_anomaly = False
        anomaly_info = {}
        
        try:
            if self.pc_model == "Basic":
                preds, errs = basic_predictive_coding(
                    window_data, self.params['sigma'], self.params['threshold']
                )
                is_anomaly, anomaly_info = self._check_basic_anomaly(errs, window_data)
                
            elif self.pc_model == "Hierarchical":
                preds, errs = hierarchical_predictive_coding(
                    window_data, self.params['sigmas'], self.params['thresholds']
                )
                is_anomaly, anomaly_info = self._check_hierarchical_anomaly(errs)
                
            elif self.pc_model == "Deep Hierarchical":
                preds, errs = deep_hierarchical_predictive_coding(
                    window_data, self.params['sigmas'], self.params['thresholds']
                )
                is_anomaly, anomaly_info = self._check_hierarchical_anomaly(errs)
                
            elif self.pc_model == "Adaptive Hierarchical":
                result = adaptive_hierarchical_predictive_coding(
                    window_data, 
                    self.params['sigmas'], 
                    self.params['thresholds'],
                    self.params.get('initial_weights'),
                    self.params.get('learning_rates')
                )
                preds, errs, weights_history = result
                # Store current weights for display
                self.current_weights = weights_history[-1] if weights_history else self.params.get('initial_weights')
                is_anomaly, anomaly_info = self._check_hierarchical_anomaly(errs)
                
            elif self.pc_model == "STDP Hierarchical":
                result = stdp_adaptive_hierarchical_predictive_coding(
                    window_data,
                    self.params['sigmas'],
                    self.params['thresholds'],
                    self.params.get('initial_weights'),
                    self.params.get('learning_rates'),
                    self.params.get('event_thresholds')
                )
                preds, errs, weights_history, window_events = result
                
                # Store window events (they will be mapped correctly in visualization)
                self.events = window_events
                
                # Store current weights for display
                self.current_weights = weights_history[-1] if weights_history else self.params.get('initial_weights')
                is_anomaly, anomaly_info = self._check_hierarchical_anomaly(errs)
                
            elif self.pc_model == "Event-Driven":
                preds, errs, self.events = event_driven_predictive_coding(
                    window_data, self.params['sigma'], 
                    self.params['threshold'], self.params['event_threshold']
                )
                is_anomaly, anomaly_info = self._check_basic_anomaly(errs, window_data)
                
            elif self.pc_model == "Precision-Weighting":
                preds, errs = precision_weighted_predictive_coding(
                    window_data, self.params['sigma'], self.params['threshold'],
                    self.params['sensory_precision'], self.params['model_precision']
                )
                is_anomaly, anomaly_info = self._check_basic_anomaly(errs, window_data)
                
            elif self.pc_model == "Active Inference":
                # Define callback function for Active Inference
                def set_internal_model_params(new_params):
                    st.session_state.internal_model_params = new_params
                    
                preds, errs = active_inference(
                    window_data, numeric_window_time, 
                    st.session_state.internal_model_params, 
                    set_internal_model_params, self.params['sigma']
                )
                is_anomaly, anomaly_info = self._check_basic_anomaly(errs, window_data)
                
        except Exception as e:
            st.error(f"Error running {self.pc_model} model: {str(e)}")
            return [], [], False, {}
            
        return preds, errs, is_anomaly, anomaly_info
    
    def _check_basic_anomaly(self, errs, window_data):
        """Check for anomalies in basic models."""
        if not errs or not errs[0].any():
            return False, {}
            
        error = errs[0][-1]
        threshold = self.params['threshold']
        is_anomaly = abs(error) > threshold
        
        anomaly_info = {
            'error': error,
            'threshold': threshold,
            'time': self._get_current_time()
        }
        
        return is_anomaly, anomaly_info
    
    def _check_hierarchical_anomaly(self, errs):
        """Check for anomalies in hierarchical models using only the finest layer."""
        # Use only the finest (last) layer for anomaly detection
        # Fine layer error already incorporates all higher-level predictions
        finest_layer_idx = len(self.params['thresholds']) - 1
        finest_threshold = self.params['thresholds'][finest_layer_idx]
        finest_error = errs[finest_layer_idx][-1]
        
        is_anomaly = abs(finest_error) > finest_threshold
        anomaly_info = {}
        
        if is_anomaly:
            # Get the correct layer name based on index
            layer_name = (LAYER_NAMES[finest_layer_idx] 
                         if finest_layer_idx < len(LAYER_NAMES) 
                         else f"Layer {finest_layer_idx + 1}")
            icon = ANOMALY_ICONS.get(layer_name, "🔴")
            
            anomaly_info = {
                'layer_name': layer_name,
                'error': finest_error,
                'threshold': finest_threshold,
                'icon': icon
            }
        
        return is_anomaly, anomaly_info
    
    def _get_current_time(self):
        """Get current formatted time string."""
        from datetime import datetime
        return datetime.now().strftime('%H:%M:%S')
    
    def get_prediction_for_point(self, preds, errs, index=-1):
        """Get prediction and error for a specific point (default: last point)."""
        if not preds or not errs:
            return None, None
            
        if self.pc_model in ["Hierarchical", "Deep Hierarchical", "Adaptive Hierarchical", "STDP Hierarchical"]:
            # Use finest layer for raw values
            pred = preds[-1][index]
            err = errs[-1][index]
        else:
            pred = preds[0][index]
            err = errs[0][index]
            
        return pred, err
    
    def get_anomaly_label_for_point(self, errs, index=-1):
        """Get anomaly label for a specific point."""
        if self.pc_model in ["Hierarchical", "Deep Hierarchical", "Adaptive Hierarchical", "STDP Hierarchical"]:
            # Use only the finest layer for consistency with real-time detection
            # Fine layer error incorporates all higher-level predictions
            finest_layer_idx = len(self.params['thresholds']) - 1
            finest_threshold = self.params['thresholds'][finest_layer_idx]
            finest_error = errs[finest_layer_idx][index]
            
            if abs(finest_error) > finest_threshold:
                layer_name = (LAYER_NAMES[finest_layer_idx] 
                             if finest_layer_idx < len(LAYER_NAMES) 
                             else f"L{finest_layer_idx + 1}")
                icon = ANOMALY_ICONS.get(layer_name, "🔴")
                return f"{icon} {layer_name}"
            return "🟢 No"
        else:
            # Basic anomaly check
            threshold = self.params['threshold']
            if self.pc_model == 'Event-Driven':
                threshold = self.params['event_threshold']
            
            return "🔴 Yes" if abs(errs[0][index]) > threshold else "🟢 No"

def create_model_runner(pc_model, params):
    """Factory function to create a ModelRunner instance."""
    return ModelRunner(pc_model, params) 