import numpy as np
import pandas as pd
from datetime import datetime

def generate_iot_data(n_samples, n_features, dist_type, dist_param1, dist_param2, 
                     noise_level=0.2, missing_rate=0.05, outlier_rate=0.05, 
                     min_value=0, max_range_multiplier=1, use_diverse_ranges=True, seed=42):
    """
    Generate synthetic IoT sensor data with various distributions and options.
    
    Parameters:
    -----------
    n_samples : int
        Number of data samples to generate
    n_features : int
        Number of sensor features to generate
    dist_type : str
        Distribution type ("Normal", "Uniform", "LogNormal", "Binomial")
    dist_param1 : float
        First parameter for the distribution (mean, min, etc.)
    dist_param2 : float
        Second parameter for the distribution (std, max, etc.)
    noise_level : float
        Level of noise to add to the target variable
    missing_rate : float
        Percentage of missing values to introduce
    outlier_rate : float
        Percentage of outlier values to introduce
    min_value : float
        Minimum value for all sensors (default: 0)
    max_range_multiplier : float
        Multiplier for maximum range diversity (higher = more diverse max values)
    use_diverse_ranges : bool
        Whether to use diverse ranges for different sensors
    seed : int
        Random seed for reproducibility
    """
    # Set random seed for reproducibility
    np.random.seed(seed)
    
    # Create different parameter ranges for each sensor
    feature_params = []
    max_values = []
    
    for i in range(n_features):
        if use_diverse_ranges:
            # Generate diverse max values (some can be very large)
            # Exponential distribution for max values to get some very large values
            max_value = np.random.exponential(scale=300) * max_range_multiplier
            
            # Ensure some sensors have large values (1000+)
            if i % 5 == 0 and n_features > 5:  # Every 5th sensor
                max_value = max(1000, max_value * 3)
            
            # Cap extremely large values
            max_value = min(max_value, 10000)
        else:
            # Use the provided dist_param2 as the max value
            max_value = dist_param2 * max_range_multiplier
        
        max_values.append(max_value)
        
        # Generate diverse parameters for each sensor
        if dist_type == "Normal":
            # Mean centered between min_value and max_value
            mean = min_value + (max_value - min_value) * 0.5
            # Standard deviation based on the range
            std = (max_value - min_value) * 0.2
            feature_params.append((mean, std))
        elif dist_type == "Uniform":
            # Uniform from min_value to max_value
            feature_params.append((min_value, max_value))
        elif dist_type == "LogNormal":
            # Adjust lognormal parameters to fit the desired range
            # For lognormal, we need to transform parameters
            desired_mean = min_value + (max_value - min_value) * 0.3
            desired_std = (max_value - min_value) * 0.3
            
            # Convert to lognormal parameters (approximation)
            if desired_mean <= min_value:
                desired_mean = min_value + 1
            
            variance = desired_std ** 2
            mu = np.log(desired_mean ** 2 / np.sqrt(variance + desired_mean ** 2))
            sigma = np.sqrt(np.log(1 + variance / desired_mean ** 2))
            
            feature_params.append((mu, sigma))
        elif dist_type == "Binomial":
            # For binomial, n controls the max value
            n = int(max_value)
            n = max(1, n)  # Ensure n is at least 1
            p = 0.3 + np.random.uniform(0, 0.4)  # p between 0.3 and 0.7
            feature_params.append((n, p))
    
    # Generate data for each feature with its own parameters
    X = np.zeros((n_samples, n_features))
    
    for i in range(n_features):
        if dist_type == "Normal":
            # Generate normal distribution then clip to ensure min_value
            X[:, i] = np.random.normal(loc=feature_params[i][0], scale=feature_params[i][1], size=n_samples)
            X[:, i] = np.clip(X[:, i], min_value, max_values[i])
        elif dist_type == "Uniform":
            X[:, i] = np.random.uniform(low=min_value, high=max_values[i], size=n_samples)
        elif dist_type == "LogNormal":
            # LogNormal naturally gives positive values
            X[:, i] = np.random.lognormal(mean=feature_params[i][0], sigma=feature_params[i][1], size=n_samples)
            # Scale to fit within desired range
            X[:, i] = min_value + (X[:, i] - np.min(X[:, i])) * (max_values[i] - min_value) / (np.max(X[:, i]) - np.min(X[:, i]) + 1e-10)
        elif dist_type == "Binomial":
            X[:, i] = np.random.binomial(n=feature_params[i][0], p=feature_params[i][1], size=n_samples)
    
    # Correlation (optional, only for continuous)
    if dist_type in ["Normal", "Uniform", "LogNormal"] and n_features > 1:
        # Add some correlation between sensors, but not too much
        for i in range(1, n_features):
            if np.random.random() < 0.4:  # 40% chance of correlation with another sensor
                corr_strength = np.random.uniform(0.2, 0.5)
                corr_with = np.random.randint(0, i)  # Correlate with a previous sensor
                
                # Add correlation while preserving the range
                temp = X[:, i] + corr_strength * X[:, corr_with] * (max_values[i] / max_values[corr_with])
                # Rescale to maintain the original range
                X[:, i] = np.clip(temp, min_value, max_values[i])
    
    # Target - use weighted coefficients based on feature importance
    # Scale coefficients inversely with feature magnitude to prevent domination by large-scale features
    coeffs = np.random.uniform(-2, 2, n_features)
    for i in range(n_features):
        if max_values[i] > 100:
            coeffs[i] = coeffs[i] / np.log10(max_values[i])
    
    y = np.dot(X, coeffs) + noise_level * np.random.randn(n_samples)
    
    # DataFrame
    feature_names = [f"sensor_{i+1}" for i in range(n_features)]
    col_names = feature_names + ["target"]
    data = np.column_stack((X, y))
    df = pd.DataFrame(data, columns=col_names)
    
    # Timestamp
    now = datetime.now()
    df['timestamp'] = pd.date_range(start=now, periods=n_samples, freq='5min')
    
    # Missing values
    if missing_rate > 0:
        mask = np.random.random(size=(n_samples, n_features)) < missing_rate
        for i in range(n_features):
            df.loc[mask[:, i], feature_names[i]] = np.nan
    
    # Outliers
    if outlier_rate > 0:
        for i, col in enumerate(feature_names):
            mask = np.random.random(size=n_samples) < outlier_rate
            outlier_indices = np.where(mask)[0]
            # Generate outliers that respect the minimum value constraint
            outlier_values = df[col].mean() + df[col].std() * np.random.uniform(3, 8, size=len(outlier_indices))
            # Some outliers can exceed the max value
            exceed_max = np.random.random(size=len(outlier_indices)) < 0.3
            outlier_values[exceed_max] = max_values[i] * np.random.uniform(1.1, 1.5, size=sum(exceed_max))
            # Ensure all outliers respect min_value
            outlier_values = np.maximum(outlier_values, min_value)
            df.loc[outlier_indices, col] = outlier_values
    
    return df 