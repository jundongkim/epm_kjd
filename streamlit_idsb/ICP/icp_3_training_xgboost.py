import pandas as pd
import numpy as np
import os
import xgboost as xgb
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.metrics import confusion_matrix, classification_report, roc_curve, precision_recall_curve
import shap
import warnings
warnings.filterwarnings('ignore')

# 동적 시각화를 위한 plotly 라이브러리 추가
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.figure_factory as ff

# 결과 저장 디렉토리 설정
MODEL_DIR = "models_xgb"
VIS_DIR = "plots_xgb"
HTML_DIR = "plots_xgb/html"  # HTML 파일 저장 디렉토리

def create_directories():
    """필요한 디렉토리 생성"""
    os.makedirs(MODEL_DIR, exist_ok=True)
    os.makedirs(VIS_DIR, exist_ok=True)
    os.makedirs(HTML_DIR, exist_ok=True)
    print(f"디렉토리 생성 완료: {MODEL_DIR}, {VIS_DIR}, {HTML_DIR}")

def load_data(file_path="icp_normalized_data_1.csv"):
    """데이터 로드 및 전처리"""
    print(f"데이터 로드 중: {file_path}")
    df = pd.read_csv(file_path)
    
    # 데이터 기본 정보 출력
    print(f"데이터 형태: {df.shape}")
    print(f"클래스 분포: \n{df['target'].value_counts()}")
    print(f"타겟 비율: {df['target'].mean():.4f}")
    
    # 특성과 타겟 분리
    X = df.drop('target', axis=1)
    y = df['target']
    
    # 훈련/테스트 데이터 분리 (층화 샘플링)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"훈련 데이터: {X_train.shape}, 테스트 데이터: {X_test.shape}")
    return X_train, X_test, y_train, y_test, X, y

def train_xgboost_model(X_train, y_train, X_test, y_test):
    """XGBoost 모델 훈련 및 평가"""
    print("\n--- XGBoost 모델 훈련 시작 ---")
    
    # XGBoost 파라미터 설정
    params = {
        'objective': 'binary:logistic',
        'eval_metric': 'auc',
        'eta': 0.05,
        'max_depth': 6,
        'min_child_weight': 1,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'scale_pos_weight': sum(y_train == 0) / sum(y_train == 1),  # 클래스 불균형 처리
        'seed': 42
    }
    
    # 교차 검증 성능 평가
    cv_results = cross_validate_xgboost(X_train, y_train, params)
    
    # 최종 모델 훈련
    dtrain = xgb.DMatrix(X_train, label=y_train)
    dtest = xgb.DMatrix(X_test, label=y_test)
    
    evals = [(dtrain, 'train'), (dtest, 'eval')]
    model = xgb.train(
        params,
        dtrain,
        num_boost_round=1000,
        evals=evals,
        early_stopping_rounds=50,
        verbose_eval=100
    )
    
    print(f"최적 반복 횟수: {model.best_iteration}")
    print(f"최종 검증 AUC: {model.best_score:.4f}")
    
    # 모델 저장
    model_path = os.path.join(MODEL_DIR, "xgboost_classifier.json")
    model.save_model(model_path)
    print(f"모델 저장 완료: {model_path}")
    
    return model, cv_results

def cross_validate_xgboost(X_train, y_train, params, n_folds=5):
    """교차 검증으로 XGBoost 모델 성능 평가"""
    print(f"\n{n_folds}겹 교차 검증 수행 중...")
    
    # 교차 검증 설정
    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=42)
    
    # 성능 지표 저장
    cv_scores = {
        'accuracy': [],
        'precision': [],
        'recall': [],
        'f1': [],
        'auc': []
    }
    
    # 교차 검증 수행
    for fold, (train_idx, val_idx) in enumerate(skf.split(X_train, y_train)):
        # 훈련/검증 데이터 분리
        X_tr, X_val = X_train.iloc[train_idx], X_train.iloc[val_idx]
        y_tr, y_val = y_train.iloc[train_idx], y_train.iloc[val_idx]
        
        # XGBoost 데이터 형식으로 변환
        dtrain = xgb.DMatrix(X_tr, label=y_tr)
        dval = xgb.DMatrix(X_val, label=y_val)
        
        # 모델 훈련
        model = xgb.train(
            params,
            dtrain,
            num_boost_round=1000,
            evals=[(dtrain, 'train'), (dval, 'val')],
            early_stopping_rounds=50,
            verbose_eval=False
        )
        
        # 예측 및 성능 평가
        y_pred_prob = model.predict(dval)
        y_pred = (y_pred_prob > 0.5).astype(int)
        
        # 성능 지표 계산
        cv_scores['accuracy'].append(accuracy_score(y_val, y_pred))
        cv_scores['precision'].append(precision_score(y_val, y_pred))
        cv_scores['recall'].append(recall_score(y_val, y_pred))
        cv_scores['f1'].append(f1_score(y_val, y_pred))
        cv_scores['auc'].append(roc_auc_score(y_val, y_pred_prob))
        
        print(f"폴드 {fold+1} - AUC: {cv_scores['auc'][-1]:.4f}, F1: {cv_scores['f1'][-1]:.4f}")
    
    # 평균 성능 출력
    print("\n교차 검증 평균 성능:")
    for metric, scores in cv_scores.items():
        print(f"{metric}: {np.mean(scores):.4f} ± {np.std(scores):.4f}")
    
    return cv_scores

def evaluate_model(model, X_test, y_test):
    """모델 성능 평가 및 시각화"""
    print("\n--- 모델 평가 시작 ---")
    
    # 테스트 데이터 변환
    dtest = xgb.DMatrix(X_test)
    
    # 예측
    y_pred_prob = model.predict(dtest)
    y_pred = (y_pred_prob > 0.5).astype(int)
    
    # 성능 지표 계산
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_pred_prob)
    
    print("테스트 데이터 성능:")
    print(f"Accuracy: {accuracy:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall: {recall:.4f}")
    print(f"F1 Score: {f1:.4f}")
    print(f"AUC: {auc:.4f}")
    
    # 혼동 행렬
    cm = confusion_matrix(y_test, y_pred)
    
    # 분류 보고서
    print("\n분류 보고서:")
    print(classification_report(y_test, y_pred))
    
    # 결과 데이터프레임 생성
    results = {
        'actual': y_test,
        'predicted': y_pred,
        'probability': y_pred_prob
    }
    results_df = pd.DataFrame(results)
    
    # 결과 저장
    results_path = os.path.join(VIS_DIR, "test_predictions.csv")
    results_df.to_csv(results_path, index=False)
    
    # 성능 지표 저장
    metrics = {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'auc': auc
    }
    metrics_df = pd.DataFrame([metrics])
    metrics_path = os.path.join(VIS_DIR, "performance_metrics.csv")
    metrics_df.to_csv(metrics_path, index=False)
    
    return results_df, cm

def plot_feature_importance(model, X):
    """특성 중요도 시각화"""
    print("\n--- 특성 중요도 시각화 ---")
    
    # 특성 중요도 추출
    feature_importance = model.get_score(importance_type='gain')
    importance_df = pd.DataFrame({
        'Feature': list(feature_importance.keys()),
        'Importance': list(feature_importance.values())
    })
    importance_df = importance_df.sort_values('Importance', ascending=False)
    
    # 상위 20개 특성만 선택
    top_features = importance_df.head(20)
    
    # 특성 중요도 CSV 저장
    importance_csv_path = os.path.join(VIS_DIR, "feature_importance.csv")
    importance_df.to_csv(importance_csv_path, index=False)
    
    # Plotly를 사용한 동적 시각화 (HTML)
    fig_importance = px.bar(
        top_features, 
        x='Importance', 
        y='Feature',
        orientation='h',
        color='Importance',
        color_continuous_scale='Viridis'
    )
    
    fig_importance.update_layout(
        title='Top 20 Feature Importance (gain)',
        xaxis=dict(title='Importance'),
        yaxis=dict(title='Feature', categoryorder='total ascending'),
        template='plotly_white'
    )
    
    # HTML 저장
    importance_html_path = os.path.join(VIS_DIR, "feature_importance.html")
    fig_importance.write_html(importance_html_path)
    
    return importance_df

def plot_confusion_matrix(cm, y_test):
    """혼동 행렬 시각화"""
    print("\n--- 혼동 행렬 시각화 ---")
    
    # 클래스 분포 계산
    class_counts = pd.Series(y_test).value_counts()
    labels = [f'Negative (n={class_counts[0]})', f'Positive (n={class_counts[1]})']
    
    # 혼동 행렬 정규화
    cm_norm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
    
    # Plotly를 사용한 동적 시각화 (HTML)
    # 혼동 행렬 시각화
    fig_cm = ff.create_annotated_heatmap(
        z=cm, 
        x=labels,
        y=labels,
        annotation_text=cm,
        colorscale='Blues'
    )
    
    fig_cm.update_layout(
        title='Confusion Matrix',
        xaxis=dict(title='Predicted Label'),
        yaxis=dict(title='True Label'),
        height=700,
        width=800
    )
    
    # HTML 저장
    cm_html_path = os.path.join(VIS_DIR, "confusion_matrix.html")
    fig_cm.write_html(cm_html_path)
    
    # 정규화된 혼동 행렬 시각화
    fig_cm_norm = ff.create_annotated_heatmap(
        z=cm_norm, 
        x=labels,
        y=labels,
        annotation_text=[[f"{val:.2%}" for val in row] for row in cm_norm],
        colorscale='Blues'
    )
    
    fig_cm_norm.update_layout(
        title='Normalized Confusion Matrix',
        xaxis=dict(title='Predicted Label'),
        yaxis=dict(title='True Label'),
        height=700,
        width=800
    )
    
    # HTML 저장
    cm_norm_html_path = os.path.join(VIS_DIR, "confusion_matrix_normalized.html")
    fig_cm_norm.write_html(cm_norm_html_path)

def plot_roc_curve(y_test, y_pred_prob):
    """ROC 곡선 시각화"""
    print("\n--- ROC 곡선 시각화 ---")
    
    # ROC 곡선 계산
    fpr, tpr, thresholds = roc_curve(y_test, y_pred_prob)
    auc = roc_auc_score(y_test, y_pred_prob)
    
    # ROC 곡선 데이터 저장
    min_length = min(len(fpr), len(tpr), len(thresholds))
    roc_df = pd.DataFrame({
        'fpr': fpr[:min_length],
        'tpr': tpr[:min_length],
        'thresholds': thresholds[:min_length]
    })
    
    roc_csv_path = os.path.join(VIS_DIR, "roc_curve_data.csv")
    roc_df.to_csv(roc_csv_path, index=False)
    
    # Plotly를 사용한 동적 시각화 (HTML)
    fig_roc = go.Figure()
    
    # ROC 곡선 추가
    fig_roc.add_trace(
        go.Scatter(
            x=fpr, 
            y=tpr,
            mode='lines',
            name=f'ROC curve (AUC = {auc:.4f})',
            line=dict(color='blue', width=2)
        )
    )
    
    # 무작위 분류기 라인
    fig_roc.add_trace(
        go.Scatter(
            x=[0, 1], 
            y=[0, 1],
            mode='lines',
            name='Random classifier',
            line=dict(color='black', width=2, dash='dash')
        )
    )
    
    # 레이아웃 설정
    fig_roc.update_layout(
        title='Receiver Operating Characteristic (ROC) Curve',
        xaxis=dict(title='False Positive Rate', range=[0, 1]),
        yaxis=dict(title='True Positive Rate', range=[0, 1.05]),
        legend=dict(x=0.7, y=0.1),
        template='plotly_white',
        height=700,
        width=800
    )
    
    # 그리드 추가
    fig_roc.update_xaxes(showgrid=True, gridwidth=0.3, gridcolor='rgba(128, 128, 128, 0.3)')
    fig_roc.update_yaxes(showgrid=True, gridwidth=0.3, gridcolor='rgba(128, 128, 128, 0.3)')
    
    # HTML 저장
    roc_html_path = os.path.join(VIS_DIR, "roc_curve.html")
    fig_roc.write_html(roc_html_path)

def plot_precision_recall_curve(y_test, y_pred_prob):
    """정밀도-재현율 곡선 시각화"""
    print("\n--- 정밀도-재현율 곡선 시각화 ---")
    
    # 정밀도-재현율 곡선 계산
    precision, recall, thresholds = precision_recall_curve(y_test, y_pred_prob)
    avg_precision = precision_score(y_test, (y_pred_prob > 0.5).astype(int))
    baseline = sum(y_test) / len(y_test)
    
    # 정밀도-재현율 곡선 데이터 저장
    if len(precision) != len(recall):
        raise ValueError("Precision and recall arrays have different lengths!")
    
    # thresholds가 한 개 적을 수 있으므로, precision과 recall을 자르기
    min_length = min(len(precision), len(recall), len(thresholds))
    pr_df = pd.DataFrame({
        'precision': precision[:min_length],
        'recall': recall[:min_length],
        'thresholds': thresholds[:min_length]
    })
    
    pr_csv_path = os.path.join(VIS_DIR, "precision_recall_curve_data.csv")
    pr_df.to_csv(pr_csv_path, index=False)
    
    # Plotly를 사용한 동적 시각화 (HTML)
    fig_pr = go.Figure()
    
    # PR 곡선 추가
    fig_pr.add_trace(
        go.Scatter(
            x=recall, 
            y=precision,
            mode='lines',
            name=f'PR curve (Avg Precision = {avg_precision:.4f})',
            line=dict(color='blue', width=2)
        )
    )
    
    # 베이스라인 추가
    fig_pr.add_trace(
        go.Scatter(
            x=[0, 1], 
            y=[baseline, baseline],
            mode='lines',
            name=f'Baseline (Positive ratio = {baseline:.4f})',
            line=dict(color='red', width=2, dash='dash')
        )
    )
    
    # 레이아웃 설정
    fig_pr.update_layout(
        title='Precision-Recall Curve',
        xaxis=dict(title='Recall', range=[0, 1]),
        yaxis=dict(title='Precision', range=[0, 1.05]),
        legend=dict(x=0.01, y=0.01),
        template='plotly_white',
        height=700,
        width=800
    )
    
    # 그리드 추가
    fig_pr.update_xaxes(showgrid=True, gridwidth=0.3, gridcolor='rgba(128, 128, 128, 0.3)')
    fig_pr.update_yaxes(showgrid=True, gridwidth=0.3, gridcolor='rgba(128, 128, 128, 0.3)')
    
    # HTML 저장
    pr_html_path = os.path.join(VIS_DIR, "precision_recall_curve.html")
    fig_pr.write_html(pr_html_path)

def generate_shap_plots(model, X_test, y_test):
    """SHAP 값을 이용한 특성 중요도 해석"""
    print("\n--- SHAP 분석 시작 ---")
    
    # SHAP 값 계산
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_test)
    
    # SHAP 값 저장
    shap_df = pd.DataFrame(shap_values, columns=X_test.columns)
    shap_df['prediction'] = model.predict(xgb.DMatrix(X_test))
    shap_df['actual'] = y_test.values
    
    shap_csv_path = os.path.join(VIS_DIR, "shap_values.csv")
    shap_df.to_csv(shap_csv_path, index=False)
    
    # Plotly를 사용한 동적 시각화 (HTML)
    # SHAP 값 평균 계산하여 특성 중요도 시각화
    shap_importance = pd.DataFrame({
        'Feature': X_test.columns,
        'Importance': np.abs(shap_values).mean(0)
    }).sort_values('Importance', ascending=False)
    
    # 상위 20개 특성 선택
    top_shap_features = shap_importance.head(20)
    
    # SHAP 특성 중요도 시각화
    fig_shap_importance = px.bar(
        top_shap_features, 
        x='Importance', 
        y='Feature',
        orientation='h',
        color='Importance',
        color_continuous_scale='RdBu_r'
    )
    
    fig_shap_importance.update_layout(
        title='SHAP Feature Importance',
        xaxis=dict(title='mean(|SHAP value|)'),
        yaxis=dict(title='Feature', categoryorder='total ascending'),
        template='plotly_white',
        height=700,
        width=800
    )
    
    # HTML 저장
    shap_importance_html_path = os.path.join(VIS_DIR, "shap_feature_importance.html")
    fig_shap_importance.write_html(shap_importance_html_path)
    
    # 상위 10개 특성에 대한 데이터 준비
    top10_features = shap_importance['Feature'].head(10).tolist()
    
    # SHAP 요약 플롯 (개선된 버전) - 모든 특성에 대한 분포와 영향
    fig_summary = go.Figure()
    
    # 각 특성별로 처리 (scatter plot 방식으로 변경)
    for i, feature in enumerate(top10_features[::-1]):  # 역순으로 처리하여 중요도 순으로 표시
        feature_idx = list(X_test.columns).index(feature)
        feature_vals = X_test[feature].values
        feature_shap_vals = shap_values[:, feature_idx]
        
        # 특성 값 기준으로 정규화 (0-1 사이 값으로)
        min_val = np.min(feature_vals)
        max_val = np.max(feature_vals)
        norm_range = max_val - min_val
        if norm_range == 0:  # 모든 값이 같은 경우
            norm_vals = np.ones_like(feature_vals) * 0.5
        else:
            norm_vals = (feature_vals - min_val) / norm_range
            
        # 색상 매핑 (0: 파란색, 1: 빨간색)
        colors = ['rgba(0,0,255,0.7)' if v < 0.5 else 'rgba(255,0,0,0.7)' for v in norm_vals]
        
        # 작은 jitter 추가하여 y축 위치 조정
        y_jitter = np.random.normal(0, 0.1, size=len(feature_shap_vals))
        
        # 특성별 산점도 추가
        fig_summary.add_trace(
            go.Scatter(
                x=feature_shap_vals,
                y=[i] * len(feature_shap_vals) + y_jitter,  # 각 특성별 y 위치 + jitter
                mode='markers',
                marker=dict(
                    size=8,
                    color=colors,
                    opacity=0.7
                ),
                name=feature,
                hovertemplate=
                f"{feature}<br>" +
                "SHAP 값: %{x:.4f}<br>" +
                "특성 값: %{text:.4f}" +
                "<extra></extra>",
                text=feature_vals
            )
        )
        
        # 각 특성별 SHAP 값의 분포를 보여주는 바이올린 플롯 추가
        violin_data = []
        for j, val in enumerate(feature_shap_vals):
            violin_data.append({
                'x': val,
                'y': i,
                'feature': feature
            })
        
        df_violin = pd.DataFrame(violin_data)
        
        # SHAP 값의 음수/양수 분포를 표시하기 위한 KDE 계산
        pos_vals = feature_shap_vals[feature_shap_vals >= 0]
        neg_vals = feature_shap_vals[feature_shap_vals < 0]
        
        # 양수 영역 KDE (충분한 데이터가 있는 경우만)
        if len(pos_vals) > 5:
            try:
                from scipy import stats
                kde_pos = stats.gaussian_kde(pos_vals)
                x_pos = np.linspace(0, np.max(pos_vals), 100)
                y_pos = kde_pos(x_pos)
                
                # KDE 스케일 조정
                y_pos = y_pos / np.max(y_pos) * 0.2
                
                # 양수 영역 KDE 추가
                fig_summary.add_trace(
                    go.Scatter(
                        x=x_pos,
                        y=i + y_pos,
                        mode='lines',
                        line=dict(color='rgba(255,0,0,0.5)', width=1.5),
                        fill='toself',
                        fillcolor='rgba(255,0,0,0.2)',
                        showlegend=False,
                        hoverinfo='skip'
                    )
                )
                
                fig_summary.add_trace(
                    go.Scatter(
                        x=x_pos,
                        y=i - y_pos,
                        mode='lines',
                        line=dict(color='rgba(255,0,0,0.5)', width=1.5),
                        fill='toself',
                        fillcolor='rgba(255,0,0,0.2)',
                        showlegend=False,
                        hoverinfo='skip'
                    )
                )
            except Exception as e:
                print(f"KDE 계산 중 오류 (양수 영역): {e}")
        
        # 음수 영역 KDE (충분한 데이터가 있는 경우만)
        if len(neg_vals) > 5:
            try:
                from scipy import stats
                kde_neg = stats.gaussian_kde(neg_vals)
                x_neg = np.linspace(np.min(neg_vals), 0, 100)
                y_neg = kde_neg(x_neg)
                
                # KDE 스케일 조정
                y_neg = y_neg / np.max(y_neg) * 0.2
                
                # 음수 영역 KDE 추가
                fig_summary.add_trace(
                    go.Scatter(
                        x=x_neg,
                        y=i + y_neg,
                        mode='lines',
                        line=dict(color='rgba(0,0,255,0.5)', width=1.5),
                        fill='toself',
                        fillcolor='rgba(0,0,255,0.2)',
                        showlegend=False,
                        hoverinfo='skip'
                    )
                )
                
                fig_summary.add_trace(
                    go.Scatter(
                        x=x_neg,
                        y=i - y_neg,
                        mode='lines',
                        line=dict(color='rgba(0,0,255,0.5)', width=1.5),
                        fill='toself',
                        fillcolor='rgba(0,0,255,0.2)',
                        showlegend=False,
                        hoverinfo='skip'
                    )
                )
            except Exception as e:
                print(f"KDE 계산 중 오류 (음수 영역): {e}")
    
    # 범례 정보 추가
    fig_summary.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode='markers',
            marker=dict(size=10, color='rgba(255,0,0,0.7)'),
            name='높은 특성값',
            showlegend=True
        )
    )
    
    fig_summary.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode='markers',
            marker=dict(size=10, color='rgba(0,0,255,0.7)'),
            name='낮은 특성값',
            showlegend=True
        )
    )
    
    # 0 기준선 추가
    fig_summary.add_vline(x=0, line_width=1, line_dash="dash", line_color="gray")
    
    # SHAP 값 범위 계산
    max_abs_shap = np.max(np.abs(shap_values))
    shap_range = [-max_abs_shap * 1.05, max_abs_shap * 1.05]
    
    # 레이아웃 설정
    fig_summary.update_layout(
        title='SHAP Summary Plot (Top 10 Features)',
        xaxis=dict(
            title='SHAP Value (Impact on model output)',
            range=shap_range,
            zeroline=True,
            zerolinewidth=2,
            zerolinecolor='gray'
        ),
        yaxis=dict(
            title='Features',
            tickvals=list(range(len(top10_features))),
            ticktext=top10_features[::-1]  # 중요도 높은 순으로 표시
        ),
        template='plotly_white',
        height=700,
        width=900,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        )
    )
    
    # HTML 저장
    summary_html_path = os.path.join(VIS_DIR, "shap_summary_enhanced.html")
    fig_summary.write_html(summary_html_path)
    
    # 기존 SHAP 요약 시각화 (특성-값 관계)
    shap_summary_data = []
    
    for feature in top10_features:
        feature_idx = list(X_test.columns).index(feature)
        feature_vals = X_test[feature].values
        feature_shap_vals = shap_values[:, feature_idx]
        
        for i in range(len(feature_vals)):
            shap_summary_data.append({
                'Feature': feature,
                'Feature Value': feature_vals[i],
                'SHAP Value': feature_shap_vals[i]
            })
    
    shap_summary_df = pd.DataFrame(shap_summary_data)
    
    # SHAP 요약 시각화
    fig_shap_summary = px.scatter(
        shap_summary_df,
        x='Feature Value',
        y='SHAP Value',
        color='SHAP Value',
        facet_col='Feature',
        facet_col_wrap=2,
        color_continuous_scale='RdBu_r',
        height=1000
    )
    
    fig_shap_summary.update_layout(
        title='SHAP Value vs Feature Value',
        template='plotly_white',
        height=800,
        width=1000
    )
    
    # HTML 저장
    shap_summary_html_path = os.path.join(VIS_DIR, "shap_summary.html")
    fig_shap_summary.write_html(shap_summary_html_path)
    
    # Force Plot 구현 (개별 예측 설명)
    # 5개의 랜덤 샘플에 대한 force plot 생성
    n_samples = 5
    sample_indices = np.random.choice(len(X_test), size=n_samples, replace=False)
    
    # 모든 force plot을 한 화면에 표시할 figure 생성
    fig_force = make_subplots(rows=n_samples, cols=1, 
                           subplot_titles=[f"Sample #{i} (Actual: {y_test.iloc[idx]}, Pred: {shap_df['prediction'].iloc[idx]:.3f})" 
                                          for i, idx in enumerate(sample_indices, 1)])
    
    # 각 샘플에 대한 force plot 생성
    for i, idx in enumerate(sample_indices, 1):
        sample_shap = shap_values[idx]
        sample_features = X_test.iloc[idx]
        base_value = explainer.expected_value  # 기본 값 (평균 예측)
        
        # 상위 영향력 있는 특성만 선택 (상위 10개)
        feature_indices = np.argsort(-np.abs(sample_shap))[:10]
        selected_features = [X_test.columns[j] for j in feature_indices]
        selected_shap = sample_shap[feature_indices]
        selected_values = sample_features.iloc[feature_indices].values
        
        # 누적값 계산
        cumulative = np.zeros(len(selected_features) + 1)
        cumulative[0] = base_value
        cumulative[1:] = base_value + np.cumsum(selected_shap)
        
        # 각 특성 기여도 막대 추가
        for j in range(len(selected_features)):
            feature = selected_features[j]
            value = selected_values[j]
            impact = selected_shap[j]
            
            # 양수/음수 기여도에 따라 색상 결정
            color = 'rgba(255,0,0,0.7)' if impact > 0 else 'rgba(0,0,255,0.7)'
            
            fig_force.add_trace(
                go.Bar(
                    x=[impact],
                    y=[0],
                    orientation='h',
                    base=cumulative[j],
                    marker=dict(color=color),
                    text=f"{feature}: {value:.3f}",
                    hoverinfo='text',
                    name=feature,
                    showlegend=False,
                    width=0.7
                ),
                row=i, col=1
            )
        
        # 시작점(base value) 표시
        fig_force.add_trace(
            go.Scatter(
                x=[base_value],
                y=[0],
                mode='markers',
                marker=dict(size=12, color='black', symbol='circle'),
                hoverinfo='text',
                text=f'Base value: {base_value:.3f}',
                name='Base value',
                showlegend=(i == 1)  # 첫 번째 샘플에만 범례 표시
            ),
            row=i, col=1
        )
        
        # 최종 예측값 표시
        fig_force.add_trace(
            go.Scatter(
                x=[cumulative[-1]],
                y=[0],
                mode='markers',
                marker=dict(size=12, color='red', symbol='diamond'),
                hoverinfo='text',
                text=f'Prediction: {cumulative[-1]:.3f}',
                name='Prediction',
                showlegend=(i == 1)  # 첫 번째 샘플에만 범례 표시
            ),
            row=i, col=1
        )
    
    # 레이아웃 설정
    fig_force.update_layout(
        title='SHAP Force Plot - Feature Contributions to Predictions',
        height=250 * n_samples,
        width=900,
        template='plotly_white'
    )
    
    # 모든 서브플롯에 동일한 X축 범위 적용
    for i in range(1, n_samples + 1):
        fig_force.update_xaxes(title='Feature Contribution (SHAP value)', row=i, col=1)
        fig_force.update_yaxes(visible=False, row=i, col=1)
    
    # HTML 저장
    force_html_path = os.path.join(VIS_DIR, "shap_force_plot.html")
    fig_force.write_html(force_html_path)
    
    # 향상된 의존성 플롯 - 상위 10개 특성에 대해
    for feature in top10_features:
        # 각 특성별 의존성 플롯 (개선된 버전)
        feature_idx = list(X_test.columns).index(feature)
        feature_vals = X_test[feature].values
        feature_shap_vals = shap_values[:, feature_idx]
        
        # 다른 특성과의 상호작용 찾기 위한 상관관계 계산
        interactions = []
        for i, other_feature in enumerate(X_test.columns):
            if other_feature != feature:
                corr = np.abs(np.corrcoef(feature_shap_vals, X_test[other_feature])[0, 1])
                if not np.isnan(corr):
                    interactions.append((other_feature, corr))
        
        # 상관관계 가장 높은 특성 선택 (상위 3개)
        top_interactions = []
        if interactions:
            interactions.sort(key=lambda x: x[1], reverse=True)
            top_interactions = interactions[:3]
        
        # 메인 의존성 플롯 생성
        fig_dep = go.Figure()
        
        # 기본 산점도 추가
        fig_dep.add_trace(
            go.Scatter(
                x=feature_vals,
                y=feature_shap_vals,
                mode='markers',
                marker=dict(
                    size=8,
                    color=feature_shap_vals,
                    colorscale='RdBu_r',
                    colorbar=dict(title='SHAP Value')
                ),
                name=feature
            )
        )
        
        # 스무딩된 트렌드 라인 추가 (LOESS)
        try:
            from scipy.stats import binned_statistic
            
            # 25개 빈으로 데이터 그룹화
            bins = 25
            bin_means, bin_edges, _ = binned_statistic(
                feature_vals, feature_shap_vals, statistic='mean', bins=bins
            )
            bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
            
            # 결측값 제거
            valid_mask = ~np.isnan(bin_means)
            bin_centers = bin_centers[valid_mask]
            bin_means = bin_means[valid_mask]
            
            if len(bin_centers) > 3:  # 최소 4개 포인트 필요
                # 스무딩된 라인 추가
                fig_dep.add_trace(
                    go.Scatter(
                        x=bin_centers,
                        y=bin_means,
                        mode='lines',
                        line=dict(color='black', width=2),
                        name='Trend'
                    )
                )
        except Exception as e:
            print(f"트렌드 라인 생성 중 오류: {e}")
        
        # 0 기준선 추가
        fig_dep.add_hline(y=0, line_width=1, line_dash="dash", line_color="gray")
        
        # 레이아웃 설정
        fig_dep.update_layout(
            title=f'SHAP Dependence Plot: {feature}',
            xaxis=dict(title=feature),
            yaxis=dict(title='SHAP value'),
            template='plotly_white',
            height=700,
            width=800
        )
        
        # 상호작용 정보 주석 추가
        if top_interactions:
            interaction_text = "상호작용이 높은 특성:<br>"
            for j, (int_feature, corr) in enumerate(top_interactions):
                interaction_text += f"{j+1}. {int_feature} (상관계수: {corr:.3f})<br>"
            
            fig_dep.add_annotation(
                xref="paper", yref="paper",
                x=0.01, y=0.99,
                text=interaction_text,
                showarrow=False,
                font=dict(size=12),
                bgcolor="rgba(255, 255, 255, 0.8)",
                bordercolor="black",
                borderwidth=1,
                borderpad=4,
                align="left"
            )
        
        # HTML 저장
        dep_html_path = os.path.join(VIS_DIR, f"shap_dependence_{feature}.html")
        fig_dep.write_html(dep_html_path)
        
    # 상호작용 의존성 플롯 - 상위 5개 특성 쌍에 대해
    # 특성 간 상호작용 계산
    interaction_scores = []
    
    # 상위 10개 특성 중에서 쌍 만들기
    for i, feature1 in enumerate(top10_features):
        for feature2 in top10_features[i+1:]:
            feature1_idx = list(X_test.columns).index(feature1)
            feature2_idx = list(X_test.columns).index(feature2)
            
            feature1_vals = X_test[feature1].values
            feature2_vals = X_test[feature2].values
            feature1_shap = shap_values[:, feature1_idx]
            feature2_shap = shap_values[:, feature2_idx]
            
            # 두 특성의 SHAP 값 간 상관관계
            corr = np.abs(np.corrcoef(feature1_shap, feature2_shap)[0, 1])
            if not np.isnan(corr):
                interaction_scores.append((feature1, feature2, corr))
    
    # 상위 5개 상호작용 쌍 선택
    if interaction_scores:
        interaction_scores.sort(key=lambda x: x[2], reverse=True)
        top_interactions = interaction_scores[:5]
        
        # 각 상호작용 쌍에 대한 의존성 플롯 생성
        for feature1, feature2, score in top_interactions:
            # 데이터 준비
            feature1_idx = list(X_test.columns).index(feature1)
            feature2_idx = list(X_test.columns).index(feature2)
            
            feature1_vals = X_test[feature1].values
            feature2_vals = X_test[feature2].values
            feature1_shap = shap_values[:, feature1_idx]
            feature2_shap = shap_values[:, feature2_idx]
            
            # 상호작용 플롯 (히트맵)
            fig_int = go.Figure()
            
            # 2D 히스토그램 생성 (SHAP 값의 분포)
            heatmap_data = np.zeros((20, 20))  # 20x20 그리드
            x_bins = np.linspace(min(feature1_vals), max(feature1_vals), 21)
            y_bins = np.linspace(min(feature2_vals), max(feature2_vals), 21)
            
            for k in range(len(feature1_vals)):
                x_idx = np.digitize(feature1_vals[k], x_bins) - 1
                y_idx = np.digitize(feature2_vals[k], y_bins) - 1
                
                if 0 <= x_idx < 20 and 0 <= y_idx < 20:
                    # SHAP 값들의 평균 사용
                    heatmap_data[y_idx, x_idx] += (feature1_shap[k] + feature2_shap[k]) / 2
            
            # 히트맵 추가
            fig_int.add_trace(
                go.Heatmap(
                    z=heatmap_data,
                    x=[(x_bins[i] + x_bins[i+1])/2 for i in range(20)],
                    y=[(y_bins[i] + y_bins[i+1])/2 for i in range(20)],
                    colorscale='RdBu_r',
                    zmin=-np.max(np.abs(heatmap_data)),
                    zmax=np.max(np.abs(heatmap_data)),
                    colorbar=dict(title='Avg SHAP Value')
                )
            )
            
            # 레이아웃 설정
            fig_int.update_layout(
                title=f'SHAP Interaction: {feature1} vs {feature2} (Score: {score:.3f})',
                xaxis=dict(title=feature1),
                yaxis=dict(title=feature2),
                template='plotly_white',
                height=700,
                width=800
            )
            
            # HTML 저장
            int_html_path = os.path.join(VIS_DIR, f"shap_interaction_{feature1}_{feature2}.html")
            fig_int.write_html(int_html_path)
    
    print(f"SHAP 분석 결과 저장 완료: {VIS_DIR}")
    print(f"생성된 SHAP 시각화 파일:")
    print(f"  - 특성 중요도: shap_feature_importance.html")
    print(f"  - 요약 플롯: shap_summary.html, shap_summary_enhanced.html")
    print(f"  - 의존성 플롯: shap_dependence_*.html")
    print(f"  - Force 플롯: shap_force_plot.html")
    print(f"  - 상호작용 플롯: shap_interaction_*.html")

def plot_learning_curve(model, X_train, y_train, X_test, y_test):
    """학습 곡선 시각화"""
    print("\n--- 학습 곡선 시각화 ---")
    
    # 학습 로그 추출
    if hasattr(model, 'evals_result') and model.evals_result():
        evals_result = model.evals_result()
        
        # 학습 곡선 데이터 저장
        learning_df = pd.DataFrame({
            'iteration': range(1, len(evals_result['train']['auc']) + 1),
            'train_auc': evals_result['train']['auc'],
            'validation_auc': evals_result['eval']['auc']
        })
        learning_csv_path = os.path.join(VIS_DIR, "learning_curve_data.csv")
        learning_df.to_csv(learning_csv_path, index=False)
        
        # Plotly를 사용한 동적 시각화 (HTML)
        fig_learning = go.Figure()
        
        # 훈련 데이터 AUC
        fig_learning.add_trace(
            go.Scatter(
                x=learning_df['iteration'],
                y=learning_df['train_auc'],
                mode='lines',
                name='Train AUC',
                line=dict(color='blue', width=2)
            )
        )
        
        # 검증 데이터 AUC
        fig_learning.add_trace(
            go.Scatter(
                x=learning_df['iteration'],
                y=learning_df['validation_auc'],
                mode='lines',
                name='Validation AUC',
                line=dict(color='red', width=2)
            )
        )
        
        # 최적 반복 횟수 표시 (있는 경우)
        if hasattr(model, 'best_iteration'):
            fig_learning.add_vline(
                x=model.best_iteration, 
                line_dash="dash", 
                line_color="green",
                annotation_text=f"Best iteration: {model.best_iteration}"
            )
        
        # 레이아웃 설정
        fig_learning.update_layout(
            title='XGBoost Learning Curve (AUC)',
            xaxis=dict(title='Boosting Iterations'),
            yaxis=dict(title='AUC'),
            template='plotly_white',
            height=700,
            width=800
        )
        
        # 그리드 추가
        fig_learning.update_xaxes(showgrid=True, gridwidth=0.3, gridcolor='rgba(128, 128, 128, 0.3)')
        fig_learning.update_yaxes(showgrid=True, gridwidth=0.3, gridcolor='rgba(128, 128, 128, 0.3)')
        
        # HTML 저장
        learning_html_path = os.path.join(VIS_DIR, "learning_curve.html")
        fig_learning.write_html(learning_html_path)
    else:
        print("모델에 학습 로그가 없어 학습 곡선을 생성할 수 없습니다.")

def main():
    """메인 함수: 데이터 로드, 모델 훈련 및 평가, 시각화 수행"""
    print("=== ICP 데이터 XGBoost 분류기 훈련 및 평가 ===")
    
    # 디렉토리 생성
    create_directories()
    
    # 데이터 로드
    X_train, X_test, y_train, y_test, X, y = load_data()
    
    # XGBoost 모델 훈련
    model, cv_results = train_xgboost_model(X_train, y_train, X_test, y_test)
    
    # 모델 평가
    results_df, confusion_matrix = evaluate_model(model, X_test, y_test)
    
    # 시각화
    plot_confusion_matrix(confusion_matrix, y_test)
    plot_roc_curve(y_test, results_df['probability'])
    plot_precision_recall_curve(y_test, results_df['probability'])
    plot_feature_importance(model, X)
    plot_learning_curve(model, X_train, y_train, X_test, y_test)
    
    # SHAP 분석
    try:
        generate_shap_plots(model, X_test.iloc[:100], y_test.iloc[:100])  # 100개 샘플로 제한하여 계산 시간 줄임
    except Exception as e:
        print(f"SHAP 분석 중 오류 발생: {e}")
    
    print("\n=== 처리 완료 ===")
    print(f"모델 저장 위치: {MODEL_DIR}")
    print(f"시각화 저장 위치: {VIS_DIR}")

if __name__ == "__main__":
    main() 