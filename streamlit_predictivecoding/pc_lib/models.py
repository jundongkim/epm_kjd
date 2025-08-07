import numpy as np
from scipy.ndimage import gaussian_filter1d
from utils.performance_utils import performance_monitor

# =======================
# Predictive Coding Models
# =======================

@performance_monitor("basic_predictive_coding")
def basic_predictive_coding(data, sigma, threshold):
    """A single layer of predictive coding.
    Args:
        data: Input signal
        sigma: Smoothing parameter
        threshold: Anomaly detection threshold
    Returns:
        preds: List of predictions at each timestep
        errs: List of errors at each timestep
    """
    pred = gaussian_filter1d(data, sigma=sigma)
    error = data - pred
    return [pred], [error]


@performance_monitor("hierarchical_predictive_coding")
def hierarchical_predictive_coding(data, sigmas, thresholds):
    """
    A true hierarchical model where each layer tries to predict the error
    from the layer below it.
    Args:
        data: Input signal
        sigmas: Smoothing parameters for each layer
        thresholds: Anomaly detection thresholds for each layer
    Returns:
        preds: List of cumulative predictions at each timestep
        errs: List of layer errors at each timestep
    """
    preds = []
    errs = []
    
    current_signal = data
    cumulative_prediction = np.zeros_like(data)

    for sigma in sigmas:
        # The current layer predicts the current signal (which is the error from the layer below)
        prediction_for_layer = gaussian_filter1d(current_signal, sigma=sigma)
        
        # The error of this layer is what's left to be explained by higher layers
        error_for_layer = current_signal - prediction_for_layer
        errs.append(error_for_layer)
        
        # The cumulative prediction is the sum of predictions from this and all lower layers.
        cumulative_prediction = cumulative_prediction + prediction_for_layer
        preds.append(cumulative_prediction)
        
        # The input for the next layer is the error from this layer.
        current_signal = error_for_layer
        
    return preds, errs


@performance_monitor("event_driven_predictive_coding")
def event_driven_predictive_coding(data, sigma, threshold, event_threshold):
    """
    True event-driven predictive coding that only makes predictions when significant events occur.
    
    This model:
    1. First pass: Identify events using basic prediction
    2. Second pass: Only make predictions at event timestamps
    3. Results in sparse predictions (fewer total predictions)
    
    Args:
        data: Input signal
        sigma: Smoothing parameter for prediction
        threshold: Anomaly detection threshold
        event_threshold: Threshold for triggering prediction events
    
    Returns:
        preds: List of predictions (sparse - only at event times)
        errs: List of errors (sparse - only at event times)  
        events: Boolean array indicating when events occurred
    """
    
    # Step 1: Initial pass to identify events using basic prediction
    initial_pred = gaussian_filter1d(data, sigma=sigma)
    initial_error = data - initial_pred
    events = np.abs(initial_error) > event_threshold
    
    # Step 2: Create sparse prediction arrays (initialized with NaN)
    sparse_pred = np.full_like(data, np.nan)
    sparse_error = np.full_like(data, np.nan)
    
    # Step 3: Only compute predictions at event timestamps
    event_indices = np.where(events)[0]
    
    if len(event_indices) > 0:
        # For each event, create a local window for prediction
        for event_idx in event_indices:
            # Define window around the event (for context)
            window_size = max(5, int(sigma))  # Minimum window size
            start_idx = max(0, event_idx - window_size)
            end_idx = min(len(data), event_idx + window_size + 1)
            
            # Extract local data window
            local_data = data[start_idx:end_idx]
            
            # Make prediction for this local window
            local_pred = gaussian_filter1d(local_data, sigma=sigma)
            local_error = local_data - local_pred
            
            # Store prediction only for the event timestamp
            relative_event_idx = event_idx - start_idx
            if 0 <= relative_event_idx < len(local_pred):
                sparse_pred[event_idx] = local_pred[relative_event_idx]
                sparse_error[event_idx] = local_error[relative_event_idx]
    
    return [sparse_pred], [sparse_error], events


@performance_monitor("precision_weighted_predictive_coding")
def precision_weighted_predictive_coding(data, sigma, threshold, sensory_precision, model_precision):
    """Weights prediction errors by their precision.
    Args:
        data: Input signal
        sigma: Smoothing parameter for prediction
        threshold: Anomaly detection threshold
        sensory_precision: Precision of sensory data
        model_precision: Precision of model's prediction
    Returns:
        preds: List of predictions at each timestep
        errs: List of errors at each timestep
    """
    sensory_pred = gaussian_filter1d(data, sigma=sigma)
    
    # A more heavily smoothed version represents the model's prior belief
    model_pred = gaussian_filter1d(data, sigma=sigma*2)

    # Update belief based on precision-weighted errors
    prediction = (sensory_precision * sensory_pred + model_precision * model_pred) / (sensory_precision + model_precision)
    error = data - prediction

    return [prediction], [error]


@performance_monitor("deep_hierarchical_predictive_coding")
def deep_hierarchical_predictive_coding(data, sigmas, thresholds):
    """
    A true hierarchical model where each layer tries to predict the error
    from the layer below it. This version is intended for a deeper hierarchy.
    Args:
        data: Input signal
        sigmas: Smoothing parameters for each layer
        thresholds: Anomaly detection thresholds for each layer
    Returns:
        preds: List of cumulative predictions at each timestep
        errs: List of layer errors at each timestep
    """
    preds = []
    errs = []
    
    current_signal = data
    cumulative_prediction = np.zeros_like(data)

    for sigma in sigmas:
        # The current layer predicts the current signal (which is the error from the layer below)
        prediction_for_layer = gaussian_filter1d(current_signal, sigma=sigma)
        
        # The error of this layer is what's left to be explained by higher layers
        error_for_layer = current_signal - prediction_for_layer
        errs.append(error_for_layer)
        
        # The cumulative prediction is the sum of predictions from this and all lower layers.
        cumulative_prediction = cumulative_prediction + prediction_for_layer
        preds.append(cumulative_prediction)
        
        # The input for the next layer is the error from this layer.
        current_signal = error_for_layer
        
    return preds, errs


@performance_monitor("active_inference_fft")
def active_inference(data, t, internal_model_params, set_internal_model_params, sigma):
    """
    A simplified model of active inference where the model can 'act' to change its internal model.
    This version uses FFT to analyze the incoming signal and adjust its internal model of the sine wave.
    Args:
        data: Input signal
        t: Time array
        internal_model_params: Dictionary containing internal model parameters
        set_internal_model_params: Function to set internal model parameters
        sigma: Smoothing parameter for prediction
    Returns:
    """
    internal_freq = internal_model_params['freq']
    internal_amp = internal_model_params['amp']

    # Smooth the sensory input to get the underlying trend for analysis
    smoothed_data = gaussian_filter1d(data, sigma=sigma)

    # --- Parameter Estimation via FFT on the smoothed data ---
    n = len(smoothed_data)
    
    # Update the internal model periodically (e.g., every 10 steps) to ensure stability and efficiency.
    # A minimum number of points is required for a meaningful FFT.
    if n > 20 and n % 10 == 0: 
        # Ensure time step is calculable and positive
        time_step = t[1] - t[0] if len(t) > 1 and t[1] > t[0] else 0.1 # Fallback

        # Perform FFT on the centered (mean-subtracted) smoothed data
        yf = np.fft.fft(smoothed_data - np.mean(smoothed_data))
        xf = np.fft.fftfreq(n, time_step)

        # Find the peak frequency in the positive spectrum (ignoring DC component at index 0)
        # We search only in the first half of the array which corresponds to positive frequencies.
        try:
            peak_idx_in_half = np.argmax(np.abs(yf[1:n//2])) + 1
            
            estimated_freq = xf[peak_idx_in_half]
            
            # Estimate amplitude from the FFT magnitude. Scaled by 2.0/n for single-sided spectrum.
            estimated_amp = 2.0/n * np.abs(yf[peak_idx_in_half])

            # --- Smoothly update the internal model parameters (Exponential Moving Average) ---
            alpha = 0.1 # Smoothing factor to prevent drastic, jittery changes
            new_freq = alpha * estimated_freq + (1 - alpha) * internal_freq
            new_amp = alpha * estimated_amp + (1 - alpha) * internal_amp
            
            # Clip the values to stay within a reasonable range
            new_freq = np.clip(new_freq, 0.01, 1.0)
            new_amp = np.clip(new_amp, 1.0, 10.0)

            set_internal_model_params({'freq': new_freq, 'amp': new_amp})
        except ValueError:
            # This can happen if the slice is empty. We can just skip the update.
            pass


    # Generate prediction from internal model using its current (possibly updated) parameters
    prediction = internal_amp * np.sin(2 * np.pi * internal_freq * t)
    
    # The final error is the difference between the raw sensory data and the model's prediction.
    # This error is used for anomaly detection in the Streamlit app.
    error = data - prediction

    return [prediction], [error] 


@performance_monitor("adaptive_hierarchical_learning")
def adaptive_hierarchical_predictive_coding(data, sigmas, thresholds, initial_weights=None, learning_rates=None):
    """
    Simplified Adaptive Hierarchical Predictive Coding.
    
    New approach:
    1. Generate multiple base predictions using different sigmas
    2. Learn optimal weights to combine these predictions
    3. Direct optimization of final prediction quality
    
    Args:
        data: Input signal
        sigmas: Smoothing parameters for each layer [coarse, medium, fine]
        thresholds: Anomaly detection thresholds for each layer
        initial_weights: Initial layer weights
        learning_rates: Learning rates for each layer
    
    Returns:
        preds: List of predictions for each layer
        errs: List of layer errors
        weights_history: Evolution of weights over time
    """
    n_layers = len(sigmas)
    
    # Initialize weights and learning rates
    if initial_weights is None:
        default_weights = [0.4, 0.3, 0.2, 0.1, 0.05]
        initial_weights = np.array(default_weights[:n_layers])
    else:
        initial_weights = np.array(initial_weights)
    
    if learning_rates is None:
        default_rates = [0.01, 0.02, 0.03, 0.04, 0.05]
        learning_rates = np.array(default_rates[:n_layers])
    else:
        learning_rates = np.array(learning_rates)
    
    # Normalize initial weights
    weights = initial_weights / np.sum(initial_weights)
    
    # Generate base predictions for all layers using different smoothing
    base_predictions = []
    for i, sigma in enumerate(sigmas):
        # Each layer generates its own smoothed version of the data
        pred = gaussian_filter1d(data, sigma=sigma)
        base_predictions.append(pred)
    
    # Storage for results
    final_predictions = []
    final_errors = []
    weights_history = []
    
    # Simple moving window for online learning
    window_size = 50  # Look at recent 50 points for learning
    
    for t in range(len(data)):
        weights_history.append(weights.copy())
        
        # Generate weighted prediction at current timestep
        current_pred = 0.0
        layer_preds = []
        
        for i in range(n_layers):
            layer_pred = base_predictions[i][t] * weights[i]
            layer_preds.append(layer_pred)
            current_pred += layer_pred
        
        # Store current prediction
        final_predictions.append(current_pred)
        
        # Calculate prediction error
        current_error = data[t] - current_pred
        final_errors.append(current_error)
        
        # Online weight learning (after sufficient data)
        if t > window_size:
            # Look at recent performance window
            start_idx = max(0, t - window_size)
            recent_data = data[start_idx:t]
            
            # Calculate each layer's individual contribution error
            for i in range(n_layers):
                # Get recent predictions for this layer
                recent_layer_preds = base_predictions[i][start_idx:t]
                
                # Calculate how well this layer alone would predict
                layer_errors = recent_data - recent_layer_preds
                layer_mse = np.mean(layer_errors**2)
                
                # Calculate current weighted combination error
                recent_combined_preds = []
                for j in range(start_idx, t):
                    combined = sum(base_predictions[k][j] * weights[k] for k in range(n_layers))
                    recent_combined_preds.append(combined)
                
                combined_errors = recent_data - np.array(recent_combined_preds)
                combined_mse = np.mean(combined_errors**2)
                
                # Weight update based on relative performance
                if layer_mse < combined_mse:
                    # This layer is better than current combination, increase weight
                    weight_delta = learning_rates[i] * 0.01 * (combined_mse - layer_mse) / (combined_mse + 1e-6)
                else:
                    # This layer is worse, decrease weight
                    weight_delta = -learning_rates[i] * 0.01 * (layer_mse - combined_mse) / (layer_mse + 1e-6)
                
                # Apply update
                weights[i] += weight_delta
                
                # Keep weights positive
                weights[i] = max(weights[i], 0.01)
            
            # Renormalize weights to sum to 1
            weights = weights / np.sum(weights)
    
    # Create final output format
    # For each layer, show its cumulative contribution
    final_preds = []
    final_errs = []
    
    for i in range(n_layers):
        # Layer i shows the prediction using weights up to layer i
        layer_pred = np.zeros_like(data)
        for t in range(len(data)):
            # Use the weights that were active at time t
            if t < len(weights_history):
                active_weights = weights_history[t]
                # Cumulative prediction up to layer i
                pred_sum = sum(base_predictions[j][t] * active_weights[j] for j in range(i + 1))
                layer_pred[t] = pred_sum
        
        final_preds.append(layer_pred)
        final_errs.append(data - layer_pred)
    
    return final_preds, final_errs, weights_history


@performance_monitor("stdp_hierarchical_learning")
def stdp_adaptive_hierarchical_predictive_coding(data, sigmas, thresholds, initial_weights=None, learning_rates=None, event_thresholds=None):
    """
    STDP-based Adaptive Hierarchical Predictive Coding.
    
    Fixed implementation using effective learning mechanism:
    - Same learning algorithm as adaptive model
    - STDP-style event-driven updates
    - Biologically inspired learning rates
    - Performance-based weight adjustments
    
    Args:
        data: Input signal
        sigmas: Smoothing parameters for each layer [coarse, medium, fine]
        thresholds: Anomaly detection thresholds for each layer
        initial_weights: Initial layer weights
        learning_rates: Learning rates for each layer
        event_thresholds: Error thresholds for triggering weight updates
    
    Returns:
        preds: List of predictions for each layer
        errs: List of layer errors
        weights_history: Evolution of weights over time
        events: Boolean array indicating when learning events occurred
    """
    n_layers = len(sigmas)
    
    # Initialize parameters
    if initial_weights is None:
        default_weights = [0.4, 0.3, 0.2, 0.1, 0.05]
        initial_weights = np.array(default_weights[:n_layers])
    else:
        initial_weights = np.array(initial_weights)
    
    if learning_rates is None:
        # STDP-style learning rates (slightly more conservative)
        default_rates = [0.008, 0.016, 0.024, 0.032, 0.040]
        learning_rates = np.array(default_rates[:n_layers])
    else:
        learning_rates = np.array(learning_rates)
    
    if event_thresholds is None:
        # STDP event thresholds for occasional stronger updates
        # Make events more selective - only for significant prediction errors
        event_thresholds = np.array(thresholds) * 0.8  # Much more strict: 80% of anomaly threshold
    else:
        event_thresholds = np.array(event_thresholds)
    
    # Normalize initial weights
    weights = initial_weights / np.sum(initial_weights)
    
    # Generate base predictions using same approach as adaptive model
    base_predictions = []
    for i, sigma in enumerate(sigmas):
        pred = gaussian_filter1d(data, sigma=sigma)
        base_predictions.append(pred)
    
    # Pre-compute events based on initial prediction errors (like Event-Driven model)
    # This ensures consistent event detection throughout the timeline
    initial_combined_pred = sum(base_predictions[i] * weights[i] for i in range(n_layers))
    initial_errors = np.abs(data - initial_combined_pred)
    
    # Detect events based on initial error threshold (similar to Event-Driven approach)
    events = initial_errors > min(event_thresholds)
    # Add some periodic learning events for continuous adaptation (less frequent)
    for t in range(0, len(data), 15):  # Every 15th timestep gets a learning event (was 5)
        events[t] = True
    
    # Storage for results
    weights_history = []
    
    # Use smaller window size for earlier event detection
    window_size = 10
    
    for t in range(len(data)):
        weights_history.append(weights.copy())
        
        # Generate weighted prediction
        current_pred = sum(base_predictions[i][t] * weights[i] for i in range(n_layers))
        
        # Calculate prediction error
        prediction_error = data[t] - current_pred
        
        # STDP-style learning: Only learn at pre-detected event timestamps
        if t > 2 and events[t]:  # Learn only at event locations
            # Look at recent performance window
            start_idx = max(0, t - window_size)
            recent_data = data[start_idx:t]
            
            # Use stronger learning for high-error events
            learning_multiplier = 2.0 if abs(prediction_error) > min(event_thresholds) else 1.0
            
            # Calculate each layer's individual contribution error (same as adaptive)
            for i in range(n_layers):
                # Get recent predictions for this layer
                recent_layer_preds = base_predictions[i][start_idx:t]
                
                # Calculate how well this layer alone would predict
                layer_errors = recent_data - recent_layer_preds
                layer_mse = np.mean(layer_errors**2)
                
                # Calculate current weighted combination error
                recent_combined_preds = []
                for j in range(start_idx, t):
                    combined = sum(base_predictions[k][j] * weights[k] for k in range(n_layers))
                    recent_combined_preds.append(combined)
                
                combined_errors = recent_data - np.array(recent_combined_preds)
                combined_mse = np.mean(combined_errors**2)
                
                # Weight update based on relative performance (same logic as adaptive)
                if layer_mse < combined_mse:
                    # This layer is better than current combination, increase weight
                    weight_delta = learning_rates[i] * 0.01 * learning_multiplier * (combined_mse - layer_mse) / (combined_mse + 1e-6)
                else:
                    # This layer is worse, decrease weight
                    weight_delta = -learning_rates[i] * 0.01 * learning_multiplier * (layer_mse - combined_mse) / (layer_mse + 1e-6)
                
                # Apply update
                weights[i] += weight_delta
                
                # Keep weights positive (same as adaptive)
                weights[i] = max(weights[i], 0.01)
            
            # Renormalize weights to sum to 1 (same as adaptive)
            weights = weights / np.sum(weights)
    
    # Create final output format (same as adaptive model)
    final_preds = []
    final_errs = []
    
    for i in range(n_layers):
        # Layer i shows the prediction using weights up to layer i
        layer_pred = np.zeros_like(data)
        for t in range(len(data)):
            # Use the weights that were active at time t
            if t < len(weights_history):
                active_weights = weights_history[t]
                # Cumulative prediction up to layer i
                pred_sum = sum(base_predictions[j][t] * active_weights[j] for j in range(i + 1))
                layer_pred[t] = pred_sum
        
        final_preds.append(layer_pred)
        final_errs.append(data - layer_pred)
    
    return final_preds, final_errs, weights_history, events 