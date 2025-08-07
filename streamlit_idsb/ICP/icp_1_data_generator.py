import pandas as pd
import numpy as np
import os

def generate_icp_dataset():
    """
    Generate a dataset with the following specifications:
    - 179 columns (features)
    - 978 records (rows)
    - Target values are 0 or 1 (with ~246 records having a target value of 1)
    - All values are normalized between 0 and 1
    """
    # Set random seed for reproducibility
    np.random.seed(42)
    
    # Number of records and features
    n_records = 978
    n_features = 178  # 178 features + 1 target column = 179 columns total
    
    # Generate random features following a normal distribution
    # We use normal distribution and then normalize the values to [0, 1]
    features = np.random.normal(loc=0.5, scale=0.15, size=(n_records, n_features))
    
    # Clip values to ensure they're between 0 and 1
    features = np.clip(features, 0, 1)
    
    # Create a DataFrame with the feature data
    # Using qcp_001, qcp_002, etc. as column names
    column_names = [f'qcp_{i+1:03d}' for i in range(n_features)]
    df = pd.DataFrame(features, columns=column_names)
    
    # Generate target values (246 records with target=1, the rest with target=0)
    # Maintaining approximately the same proportion as the original (49/195)
    target = np.zeros(n_records)
    # Randomly select 246 indices for target=1
    indices_for_ones = np.random.choice(n_records, size=246, replace=False)
    target[indices_for_ones] = 1
    
    # Add target column to the dataframe
    df['target'] = target
    
    return df

def save_dataset(df, filename):
    """
    Save the dataset to a CSV file
    """
    # Ensure the directory exists
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
    df.to_csv(output_path, index=False)
    print(f"Dataset saved to {output_path}")
    
    # Print statistics
    print(f"Dataset shape: {df.shape}")
    print(f"Number of records with target=1: {df['target'].sum()}")
    print(f"Number of records with target=0: {df.shape[0] - df['target'].sum()}")
    
    # Print min and max values to confirm normalization
    print(f"Min value across all features: {df.iloc[:, :-1].min().min()}")
    print(f"Max value across all features: {df.iloc[:, :-1].max().max()}")

def main():
    # Generate the dataset
    df = generate_icp_dataset()
    
    # Save the dataset
    save_dataset(df, 'icp_normalized_data_3.csv')

if __name__ == "__main__":
    main() 