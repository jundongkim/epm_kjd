import pandas as pd
from sklearn.preprocessing import MinMaxScaler, StandardScaler

def handle_missing_values(df, method):
    df_processed = df.copy()
    if method == "drop_rows":
        df_processed = df_processed.dropna()
    elif method == "drop_columns":
        df_processed = df_processed.dropna(axis=1)
    elif method == "mean":
        df_processed = df_processed.fillna(df.mean())
    elif method == "median":
        df_processed = df_processed.fillna(df.median())
    elif method == "mode":
        df_processed = df_processed.fillna(df.mode().iloc[0])
    elif method == "zero":
        df_processed = df_processed.fillna(0)
    return df_processed

def handle_outliers(df, numerical_cols, method, stats):
    df_processed = df.copy()
    if 'outliers' not in stats or not stats['outliers']:
        return df_processed
    for col in numerical_cols:
        if col in stats['outliers']:
            mask = (df_processed[col] < stats['outliers'][col]['lower_bound']) | (df_processed[col] > stats['outliers'][col]['upper_bound'])
            if method == "clip":
                df_processed.loc[df_processed[col] < stats['outliers'][col]['lower_bound'], col] = stats['outliers'][col]['lower_bound']
                df_processed.loc[df_processed[col] > stats['outliers'][col]['upper_bound'], col] = stats['outliers'][col]['upper_bound']
            elif method == "remove":
                df_processed = df_processed[~mask]
            elif method == "mean":
                df_processed.loc[mask, col] = df[col].mean()
            elif method == "median":
                df_processed.loc[mask, col] = df[col].median()
    return df_processed

def normalize_data(df, numerical_cols, method, exclude_cols=None):
    if exclude_cols is None:
        exclude_cols = []
    df_processed = df.copy()
    cols_to_scale = [col for col in numerical_cols if col not in exclude_cols and col in df.columns]
    
    # Return original data if no columns to scale
    if not cols_to_scale or df_processed.empty:
        return df_processed, None
    
    if method == "min_max":
        scaler = MinMaxScaler()
    elif method == "standard":
        scaler = StandardScaler()
    else:
        return df_processed, None
    
    # Make sure we have numeric data to scale
    numeric_df = df_processed[cols_to_scale].select_dtypes(include=['number'])
    if numeric_df.empty:
        return df_processed, None
    
    # Apply scaling only to numeric columns
    cols_to_scale = numeric_df.columns.tolist()
    
    try:
        scaled_data = scaler.fit_transform(df_processed[cols_to_scale])
        # Create a new DataFrame with the scaled values
        scaled_df = pd.DataFrame(scaled_data, columns=cols_to_scale, index=df_processed.index)
        
        # Replace the original columns with the scaled values
        for col in cols_to_scale:
            df_processed[col] = scaled_df[col]
    except Exception as e:
        print(f"Error in normalization: {e}")
        # If there's an error in normalization, return the original DataFrame
        return df, None
        
    return df_processed, scaler 