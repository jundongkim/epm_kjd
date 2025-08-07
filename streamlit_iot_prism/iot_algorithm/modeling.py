# modeling.py: 모델 학습/평가 함수 모듈 (Streamlit UI와 분리)
# 기존 코드 활용, 필요시 함수화/정리

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.svm import SVR
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.model_selection import cross_val_score
import plotly.graph_objects as go

# Add CatBoost and XGBoost imports
try:
    import catboost as cb
    CATBOOST_AVAILABLE = True
except ImportError:
    CATBOOST_AVAILABLE = False
    
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False


def train_model(X_train, y_train, model_type, X_test=None, y_test=None, **params):
    if model_type == "linear":
        model = LinearRegression(**params)
    elif model_type == "ridge":
        model = Ridge(**params)
    elif model_type == "lasso":
        model = Lasso(**params)
    elif model_type == "random_forest":
        model = RandomForestRegressor(**params)
    elif model_type == "gradient_boosting":
        model = GradientBoostingRegressor(**params)
    elif model_type == "svr":
        model = SVR(**params)
    elif model_type == "catboost":
        if not CATBOOST_AVAILABLE:
            raise ImportError("CatBoost is not installed. Please install with: pip install catboost")
        
        # Extract parameters for model initialization and fit method
        model_params = {
            'iterations': params.get('iterations', 1000),
            'learning_rate': params.get('learning_rate', 0.01),
            'depth': params.get('depth', 6),
            'loss_function': params.get('loss_function', 'RMSE'),
            'eval_metric': params.get('eval_metric', 'RMSE'),
            'random_seed': params.get('random_seed', 42),
            'verbose': params.get('verbose', 1)
        }
        
        # Initialize CatBoost model
        model = cb.CatBoostRegressor(**model_params)
        
        # Use test data as evaluation set if provided
        if X_test is not None and y_test is not None:
            # Prepare fit parameters
            fit_params = {
                'eval_set': [(X_test, y_test)],
                'verbose': model_params['verbose']
            }
            
            # Add early stopping if specified
            if 'early_stopping_rounds' in params:
                fit_params['early_stopping_rounds'] = params['early_stopping_rounds']
            
            # Add use_best_model if specified
            if 'use_best_model' in params:
                fit_params['use_best_model'] = params['use_best_model']
            
            # Train model with evaluation set
            model.fit(X_train, y_train, **fit_params)
        else:
            # Train model without evaluation set
            model.fit(X_train, y_train)
            
        return model
    elif model_type == "xgboost":
        if not XGBOOST_AVAILABLE:
            raise ImportError("XGBoost is not installed. Please install with: pip install xgboost")
        
        # Extract parameters for XGBoost core API
        xgb_params = {
            'objective': params.get('objective', 'reg:squarederror'),
            'learning_rate': params.get('learning_rate', 0.01),
            'max_depth': params.get('max_depth', 6),
            'eval_metric': params.get('eval_metric', 'rmse'),
            'random_state': params.get('random_state', 42)
        }
        
        # Add additional parameters if provided
        for param in ['subsample', 'colsample_bytree', 'min_child_weight', 'gamma']:
            if param in params:
                xgb_params[param] = params[param]
        
        # Use test data as evaluation set if provided
        if X_test is not None and y_test is not None:
            # Create DMatrix objects for XGBoost
            dtrain = xgb.DMatrix(X_train, label=y_train)
            dtest = xgb.DMatrix(X_test, label=y_test)
            
            # Dictionary to store training history
            evals_result = {}
            
            # Train the model using xgb.train (core API)
            model = xgb.train(
                xgb_params,
                dtrain,
                num_boost_round=params.get('n_estimators', 1000),
                evals=[(dtrain, 'train'), (dtest, 'test')],
                early_stopping_rounds=params.get('early_stopping_rounds', None),
                evals_result=evals_result,  # Store evaluation history
                verbose_eval=params.get('verbose', 1)  # Print info
            )
            
            # Store evaluation results in the model for later access
            model.evals_result_dict = evals_result
            
            return model
        else:
            # If no test data, use XGBRegressor for simplicity
            model = xgb.XGBRegressor(
                n_estimators=params.get('n_estimators', 1000),
                learning_rate=params.get('learning_rate', 0.01),
                max_depth=params.get('max_depth', 6),
                objective=params.get('objective', 'reg:squarederror'),
                random_state=params.get('random_state', 42),
                verbosity=params.get('verbose', 1)
            )
            model.fit(X_train, y_train)
            return model
    else:
        raise ValueError(f"Unknown model type: {model_type}")
    
    model.fit(X_train, y_train)
    return model


def evaluate_model(model, X_train, X_test, y_train, y_test):
    # Check if this is a XGBoost model trained with the core API
    if XGBOOST_AVAILABLE and hasattr(model, 'predict') and not hasattr(model, 'fit'):
        # For XGBoost core API models, we need to use DMatrix
        dtrain = xgb.DMatrix(X_train)
        dtest = xgb.DMatrix(X_test)
        
        y_train_pred = model.predict(dtrain)
        y_test_pred = model.predict(dtest)
    else:
        # For all other models (including XGBRegressor)
        y_train_pred = model.predict(X_train)
        y_test_pred = model.predict(X_test)
    
    metrics = {
        'train': {
            'mse': mean_squared_error(y_train, y_train_pred),
            'rmse': np.sqrt(mean_squared_error(y_train, y_train_pred)),
            'mae': mean_absolute_error(y_train, y_train_pred),
            'r2': r2_score(y_train, y_train_pred),
            'predictions': y_train_pred
        },
        'test': {
            'mse': mean_squared_error(y_test, y_test_pred),
            'rmse': np.sqrt(mean_squared_error(y_test, y_test_pred)),
            'mae': mean_absolute_error(y_test, y_test_pred),
            'r2': r2_score(y_test, y_test_pred),
            'predictions': y_test_pred
        }
    }
    return metrics, y_train_pred, y_test_pred


def plot_model_predictions(y_true, y_pred, title="Actual vs Predicted Values"):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=y_true, y=y_pred, mode='markers', marker=dict(size=8, opacity=0.7), name='Predictions'))
    min_val = min(min(y_true), min(y_pred))
    max_val = max(max(y_true), max(y_pred))
    fig.add_trace(go.Scatter(x=[min_val, max_val], y=[min_val, max_val], mode='lines', line=dict(color='red', dash='dash'), name='Perfect Prediction'))
    fig.update_layout(title=title, xaxis_title="Actual Values", yaxis_title="Predicted Values", height=600, width=800)
    return fig


def plot_feature_importance(model, feature_names, model_type):
    fig = go.Figure()
    
    # Get feature importance based on model type
    if model_type in ["linear", "ridge", "lasso"]:
        importance = np.abs(model.coef_)
    elif model_type in ["random_forest", "gradient_boosting"]:
        importance = model.feature_importances_
    elif model_type == "catboost" and CATBOOST_AVAILABLE:
        importance = model.get_feature_importance()
    elif model_type == "xgboost" and XGBOOST_AVAILABLE:
        # Check if this is a XGBoost model trained with the core API
        if hasattr(model, 'get_score') and not hasattr(model, 'fit'):
            # For XGBoost core API models, use get_score directly
            importance_dict = model.get_score(importance_type='gain')
            
            # Convert dictionary to array matching feature_names order
            if isinstance(importance_dict, dict):
                # Create a Series with feature names as index
                importance_series = pd.Series(importance_dict)
                
                # Reindex to match feature_names order, filling missing values with 0
                importance = np.zeros(len(feature_names))
                for i, feature in enumerate(feature_names):
                    if feature in importance_series:
                        importance[i] = importance_series[feature]
        else:
            # For XGBRegressor models
            try:
                importance = model.feature_importances_
            except:
                # Fallback to get_score if feature_importances_ is not available
                try:
                    importance_dict = model.get_booster().get_score(importance_type='gain')
                    # Convert dictionary to list matching feature_names order
                    importance = np.zeros(len(feature_names))
                    for i, feature in enumerate(feature_names):
                        feature_key = f"f{i}"
                        if feature_key in importance_dict:
                            importance[i] = importance_dict[feature_key]
                except:
                    return None, None
    else:
        return None, None
    
    # Create DataFrame for importance
    importance_df = pd.DataFrame({'Feature': feature_names, 'Importance': importance})
    importance_df = importance_df.sort_values('Importance', ascending=False)
    
    # Create plot
    fig.add_trace(go.Bar(x=importance_df['Feature'], y=importance_df['Importance'], marker_color='royalblue'))
    fig.update_layout(title="Feature Importance", xaxis_title="Feature", yaxis_title="Importance", height=500)
    
    return fig, importance_df


def perform_cross_validation(X, y, model_type, cv=5, **params):
    if model_type == "linear":
        model = LinearRegression(**params)
    elif model_type == "ridge":
        model = Ridge(**params)
    elif model_type == "lasso":
        model = Lasso(**params)
    elif model_type == "random_forest":
        model = RandomForestRegressor(**params)
    elif model_type == "gradient_boosting":
        model = GradientBoostingRegressor(**params)
    elif model_type == "svr":
        model = SVR(**params)
    elif model_type == "catboost":
        if not CATBOOST_AVAILABLE:
            raise ImportError("CatBoost is not installed")
        default_params = {'iterations': 1000, 'learning_rate': 0.01, 'depth': 6, 'verbose': False}
        for key, value in params.items():
            default_params[key] = value
        model = cb.CatBoostRegressor(**default_params)
    elif model_type == "xgboost":
        if not XGBOOST_AVAILABLE:
            raise ImportError("XGBoost is not installed")
        default_params = {'n_estimators': 1000, 'learning_rate': 0.01, 'max_depth': 6, 'verbosity': 0}
        for key, value in params.items():
            default_params[key] = value
        model = xgb.XGBRegressor(**default_params)
    else:
        raise ValueError(f"Unknown model type: {model_type}")
    
    cv_scores = cross_val_score(model, X, y, cv=cv, scoring='neg_mean_squared_error')
    rmse_scores = np.sqrt(-cv_scores)
    return {
        'mean_rmse': rmse_scores.mean(),
        'std_rmse': rmse_scores.std(),
        'individual_scores': rmse_scores
    }


def compare_models(models, metrics, model_names):
    fig = go.Figure()
    comparison_df = pd.DataFrame({
        'Model': model_names,
        'Train RMSE': [metrics[i]['train']['rmse'] for i in range(len(metrics))],
        'Test RMSE': [metrics[i]['test']['rmse'] for i in range(len(metrics))],
        'Train R²': [metrics[i]['train']['r2'] for i in range(len(metrics))],
        'Test R²': [metrics[i]['test']['r2'] for i in range(len(metrics))]
    })
    fig.add_trace(go.Bar(x=model_names, y=[metrics[i]['test']['rmse'] for i in range(len(metrics))], name='Test RMSE', marker_color='crimson'))
    fig.add_trace(go.Bar(x=model_names, y=[metrics[i]['train']['rmse'] for i in range(len(metrics))], name='Train RMSE', marker_color='royalblue'))
    fig.update_layout(title="Model Comparison - RMSE", xaxis_title="Model", yaxis_title="RMSE", barmode='group', height=500)
    return fig, comparison_df


def plot_learning_curve(model, X_train, X_test, y_train, y_test, model_type, **params):
    """
    Plot the learning curve (training and validation error vs. model complexity)
    for different model types.
    
    Returns:
        fig: plotly figure object
        history: dictionary with training history if available
    """
    fig = go.Figure()
    history = {}
    
    # For models that provide staged predictions (like boosting models)
    if model_type == "gradient_boosting":
        train_scores = []
        test_scores = []
        n_estimators = model.n_estimators
        
        # Get staged predictions for different number of estimators
        for i, y_train_pred in enumerate(model.staged_predict(X_train)):
            train_scores.append(mean_squared_error(y_train, y_train_pred))
        
        for i, y_test_pred in enumerate(model.staged_predict(X_test)):
            test_scores.append(mean_squared_error(y_test, y_test_pred))
        
        # Convert MSE to RMSE
        train_scores = np.sqrt(train_scores)
        test_scores = np.sqrt(test_scores)
        
        iterations = list(range(1, n_estimators + 1))
        
        # Store history
        history = {
            'iterations': iterations,
            'train_scores': train_scores,
            'test_scores': test_scores
        }
        
        # Plot training and validation error
        fig.add_trace(go.Scatter(x=iterations, y=train_scores, 
                                mode='lines', name='Train RMSE',
                                line=dict(color='blue', width=2)))
        fig.add_trace(go.Scatter(x=iterations, y=test_scores, 
                                mode='lines', name='Test RMSE',
                                line=dict(color='orange', width=2)))
        
        # Set y-axis range (start from 0 to max value * 1.1)
        max_score = max(max(train_scores), max(test_scores))
        fig.update_yaxes(range=[0, max_score * 1.1])
        
    elif model_type == "catboost" and CATBOOST_AVAILABLE:
        try:
            # Get evaluation results from CatBoost model
            eval_result = model.get_evals_result()
            
            if eval_result and 'learn' in eval_result:
                # Get metric name (RMSE, MAE, MAPE, etc.)
                metric_names = list(eval_result['learn'].keys())
                if not metric_names:
                    raise ValueError("No metrics found in evaluation results")
                
                metric_name = metric_names[0]  # Use the first metric
                train_scores = eval_result['learn'][metric_name]
                
                # Check for validation data (could be named 'validation' or 'test')
                validation_key = None
                for key in eval_result:
                    if key != 'learn':
                        validation_key = key
                        break
                
                if validation_key:
                    test_scores = eval_result[validation_key][metric_name]
                    iterations = list(range(1, len(train_scores) + 1))
                    
                    # Find best iteration if early stopping was used
                    best_iter = None
                    if hasattr(model, 'get_best_iteration'):
                        best_iter = model.get_best_iteration()
                    
                    # Store history
                    history = {
                        'iterations': iterations,
                        'train_scores': train_scores,
                        'test_scores': test_scores,
                        'best_iteration': best_iter
                    }
                    
                    # Plot training error
                    fig.add_trace(go.Scatter(
                        x=iterations, 
                        y=train_scores, 
                        mode='lines', 
                        name=f'Train {metric_name}',
                        line=dict(color='blue', width=2)
                    ))
                    
                    # Plot validation error
                    fig.add_trace(go.Scatter(
                        x=iterations, 
                        y=test_scores, 
                        mode='lines', 
                        name=f'Validation {metric_name}',
                        line=dict(color='orange', width=2)
                    ))
                    
                    # Add vertical line at best iteration if available
                    if best_iter:
                        fig.add_vline(
                            x=best_iter, 
                            line_width=2, 
                            line_dash="dash", 
                            line_color="green", 
                            annotation_text=f"Best Iteration: {best_iter}", 
                            annotation_position="top right"
                        )
                    
                    # Set y-axis range
                    max_score = max(max(train_scores), max(test_scores))
                    fig.update_yaxes(range=[0, max_score * 1.1])
                else:
                    # If no validation data in eval_result
                    raise ValueError("No validation data found in evaluation results")
            else:
                # If no evaluation results, manually calculate scores
                raise ValueError("No evaluation results found")
                
        except Exception as e:
            print(f"Error plotting CatBoost learning curve: {e}")
            # Fallback to manual calculation
            y_train_pred = model.predict(X_train)
            y_test_pred = model.predict(X_test)
            
            train_rmse = np.sqrt(mean_squared_error(y_train, y_train_pred))
            test_rmse = np.sqrt(mean_squared_error(y_test, y_test_pred))
            
            fig.add_trace(go.Bar(
                x=['Training', 'Validation'], 
                y=[train_rmse, test_rmse],
                marker_color=['blue', 'orange']
            ))
            
            # Store dummy history
            history = {
                'iterations': [1],
                'train_scores': [train_rmse],
                'test_scores': [test_rmse]
            }
            
    elif model_type == "xgboost" and XGBOOST_AVAILABLE:
        try:
            # Check if this is a model trained with xgb.train (core API)
            if hasattr(model, 'evals_result_dict'):
                # Use the stored evaluation results
                evals_result = model.evals_result_dict
                
                # Get metric names
                train_metric_name = list(evals_result['train'].keys())[0]
                test_metric_name = list(evals_result['test'].keys())[0]
                
                # Get training and test scores
                train_scores = evals_result['train'][train_metric_name]
                test_scores = evals_result['test'][test_metric_name]
                iterations_list = list(range(len(train_scores)))
                
                # Get best iteration if available
                best_iter = None
                if hasattr(model, 'best_iteration'):
                    best_iter = model.best_iteration
                
                # Store history
                history = {
                    'iterations': iterations_list,
                    'train_scores': train_scores,
                    'test_scores': test_scores,
                    'best_iteration': best_iter
                }
                
                # Plot training and validation error
                fig.add_trace(go.Scatter(
                    x=iterations_list, 
                    y=train_scores, 
                    mode='lines', 
                    name=f'Train {train_metric_name}',
                    line=dict(color='blue', width=2)
                ))
                
                fig.add_trace(go.Scatter(
                    x=iterations_list, 
                    y=test_scores, 
                    mode='lines', 
                    name=f'Validation {test_metric_name}',
                    line=dict(color='orange', width=2)
                ))
                
                # Add vertical line at best iteration if available
                if best_iter:
                    fig.add_vline(
                        x=best_iter, 
                        line_width=2, 
                        line_dash="dash", 
                        line_color="green", 
                        annotation_text=f"Best Iteration: {best_iter}", 
                        annotation_position="top right"
                    )
                
                # Set y-axis range
                max_score = max(max(train_scores), max(test_scores))
                fig.update_yaxes(range=[0, max_score * 1.1])
                
                return fig, history
            
            # Try to get evaluation results from XGBRegressor
            elif hasattr(model, 'evals_result') and model.evals_result():
                eval_results = model.evals_result()
                
                # Get metric name
                train_metric = list(eval_results['validation_0'].keys())[0]
                test_metric = list(eval_results['validation_1'].keys())[0]
                
                train_scores = eval_results['validation_0'][train_metric]
                test_scores = eval_results['validation_1'][test_metric]
                iterations = list(range(1, len(train_scores) + 1))
                
                # Find best iteration if early stopping was used
                best_iter = None
                if hasattr(model, 'best_iteration'):
                    best_iter = model.best_iteration
                
                # Store history
                history = {
                    'iterations': iterations,
                    'train_scores': train_scores,
                    'test_scores': test_scores,
                    'best_iteration': best_iter
                }
                
                # Plot training and validation error
                fig.add_trace(go.Scatter(
                    x=iterations, 
                    y=train_scores, 
                    mode='lines', 
                    name=f'Train {train_metric}',
                    line=dict(color='blue', width=2)
                ))
                
                fig.add_trace(go.Scatter(
                    x=iterations, 
                    y=test_scores, 
                    mode='lines', 
                    name=f'Validation {test_metric}',
                    line=dict(color='orange', width=2)
                ))
                
                # Add vertical line at best iteration if available
                if best_iter:
                    fig.add_vline(
                        x=best_iter, 
                        line_width=2, 
                        line_dash="dash", 
                        line_color="green", 
                        annotation_text=f"Best Iteration: {best_iter}", 
                        annotation_position="top right"
                    )
                
                # Set y-axis range
                max_score = max(max(train_scores), max(test_scores))
                fig.update_yaxes(range=[0, max_score * 1.1])
            else:
                # If no evaluation results, manually calculate learning curve
                raise ValueError("No evaluation results found in model")
                
        except Exception as e:
            print(f"Error retrieving XGBoost learning curve: {e}")
            # Fallback to manual calculation of learning curve
            try:
                # Get number of trees
                n_estimators = model.n_estimators if hasattr(model, 'n_estimators') else params.get('n_estimators', 100)
                
                # Sample points for the learning curve (max 20 points)
                step = max(1, n_estimators // 20)
                iterations = list(range(step, n_estimators + 1, step))
                if not iterations or iterations[-1] != n_estimators:
                    iterations.append(n_estimators)
                
                train_scores = []
                test_scores = []
                
                # For newer XGBoost versions, we need to use a different approach
                print("Calculating manual XGBoost learning curve...")
                
                # Method 1: Train multiple models with different n_estimators
                for i in iterations:
                    # Create a model with i trees
                    temp_params = {
                        'n_estimators': i,
                        'learning_rate': params.get('learning_rate', 0.1),
                        'max_depth': params.get('max_depth', 6),
                        'objective': params.get('objective', 'reg:squarederror'),
                        'random_state': params.get('random_state', 42),
                        'verbosity': 0
                    }
                    
                    # Copy additional parameters
                    for param in ['subsample', 'colsample_bytree', 'min_child_weight', 'gamma']:
                        if param in params:
                            temp_params[param] = params[param]
                    
                    # Create and train a temporary model
                    temp_model = xgb.XGBRegressor(**temp_params)
                    temp_model.fit(X_train, y_train)
                    
                    # Make predictions
                    train_pred = temp_model.predict(X_train)
                    test_pred = temp_model.predict(X_test)
                    
                    # Calculate RMSE
                    train_rmse = np.sqrt(mean_squared_error(y_train, train_pred))
                    test_rmse = np.sqrt(mean_squared_error(y_test, test_pred))
                    
                    train_scores.append(train_rmse)
                    test_scores.append(test_rmse)
                
                # Store history
                history = {
                    'iterations': iterations,
                    'train_scores': train_scores,
                    'test_scores': test_scores
                }
                
                # Plot learning curve
                fig.add_trace(go.Scatter(
                    x=iterations, 
                    y=train_scores, 
                    mode='lines+markers', 
                    name='Train RMSE',
                    line=dict(color='blue', width=2)
                ))
                
                fig.add_trace(go.Scatter(
                    x=iterations, 
                    y=test_scores, 
                    mode='lines+markers', 
                    name='Validation RMSE',
                    line=dict(color='orange', width=2)
                ))
                
                # Set y-axis range
                max_score = max(max(train_scores), max(test_scores))
                fig.update_yaxes(range=[0, max_score * 1.1])
            except Exception as e:
                print(f"Error calculating manual XGBoost learning curve: {e}")
                # If all else fails, just show final scores
                y_train_pred = model.predict(X_train)
                y_test_pred = model.predict(X_test)
                
                train_rmse = np.sqrt(mean_squared_error(y_train, y_train_pred))
                test_rmse = np.sqrt(mean_squared_error(y_test, y_test_pred))
                
                fig.add_trace(go.Bar(
                    x=['Training', 'Validation'], 
                    y=[train_rmse, test_rmse],
                    marker_color=['blue', 'orange']
                ))
                
                # Store dummy history
                history = {
                    'iterations': [1],
                    'train_scores': [train_rmse],
                    'test_scores': [test_rmse]
                }
    else:
        # For other models, create a dummy figure with validation scores
        y_train_pred = model.predict(X_train)
        y_test_pred = model.predict(X_test)
        
        train_rmse = np.sqrt(mean_squared_error(y_train, y_train_pred))
        test_rmse = np.sqrt(mean_squared_error(y_test, y_test_pred))
        
        fig.add_trace(go.Bar(
            x=['Training', 'Test'], 
            y=[train_rmse, test_rmse],
            marker_color=['blue', 'orange']
        ))
        
        # Store dummy history
        history = {
            'iterations': [1],
            'train_scores': [train_rmse],
            'test_scores': [test_rmse]
        }
    
    # Update layout
    fig.update_layout(
        title="Learning Curve",
        xaxis_title="Iterations",
        yaxis_title="Error",
        legend=dict(
            x=0.02,
            y=0.98,
            bgcolor='rgba(255, 255, 255, 0.5)'
        ),
        template='plotly_white',
        height=600
    )
    
    return fig, history

# ... 기존 코드 ... 