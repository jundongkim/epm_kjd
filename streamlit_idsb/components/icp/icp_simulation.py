"""
ICP 시뮬레이션 모듈 - 과거 예측 검증 및 미래 예측 시뮬레이션
"""

import streamlit as st
import pandas as pd
import numpy as np
import os
import xgboost as xgb
import plotly.express as px
import plotly.graph_objects as go
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
from components.ai_utils import (
    init_session_state,
    display_analysis_ui,
    generate_ai_analysis
)

# 모델 및 데이터 경로
MODEL_PATH = "ICP/models_xgb/xgboost_classifier.json"
DATA_PATH = "ICP/icp_normalized_data_3.csv"

def load_model():
    """XGBoost 모델을 로드합니다."""
    try:
        if os.path.exists(MODEL_PATH):
            model = xgb.XGBClassifier()
            model.load_model(MODEL_PATH)
            return model
        else:
            st.error(f"모델 파일을 찾을 수 없습니다: {MODEL_PATH}")
            return None
    except Exception as e:
        st.error(f"모델 로드 중 오류 발생: {str(e)}")
        return None

def load_data():
    """ICP 데이터를 로드합니다."""
    try:
        if os.path.exists(DATA_PATH):
            df = pd.read_csv(DATA_PATH)
            return df
        else:
            st.error(f"데이터 파일을 찾을 수 없습니다: {DATA_PATH}")
            return None
    except Exception as e:
        st.error(f"데이터 로드 중 오류 발생: {str(e)}")
        return None

def get_feature_columns(df):
    """특성(QCP) 컬럼 목록을 반환합니다."""
    # qcp_ 접두사가 있는 컬럼만 선택 (target 제외)
    feature_cols = [col for col in df.columns if col.startswith('qcp_') and col != 'target']
    return feature_cols

def show_past_prediction_comparison(df, model):
    """과거 ICP 예측과 실제 결과를 비교합니다."""
    st.subheader("1. 과거 ICP 예측 결과 비교")
    
    if df is None or model is None:
        return
    
    # 필요한 컬럼 확인
    if 'target' not in df.columns:
        st.error("필요한 target 컬럼이 데이터에 없습니다.")
        return
    
    # 세션 상태 키 초기화
    if 'past_prediction_executed' not in st.session_state:
        st.session_state.past_prediction_executed = False
    if 'past_prediction_results' not in st.session_state:
        st.session_state.past_prediction_results = None
    if 'past_sample_option_previous' not in st.session_state:
        st.session_state.past_sample_option_previous = None
    if 'past_sample_size_previous' not in st.session_state:
        st.session_state.past_sample_size_previous = None
    if 'past_record_index_previous' not in st.session_state:
        st.session_state.past_record_index_previous = None
    
    # 특성 컬럼 가져오기
    feature_cols = get_feature_columns(df)
    
    if not feature_cols:
        st.error("QCP 특성 컬럼을 찾을 수 없습니다.")
        return
    
    # 데이터 샘플 선택 옵션
    sample_options = [
        "전체 데이터 사용",
        "랜덤 샘플 사용",
        "특정 레코드 선택"
    ]
    
    sample_option = st.radio("데이터 선택 방식:", sample_options, key="past_sample_option")
    
    # 선택 방식이 변경되면 예측 상태 리셋
    if st.session_state.past_sample_option_previous != sample_option:
        st.session_state.past_prediction_executed = False
        st.session_state.past_prediction_results = None
        st.session_state.past_sample_option_previous = sample_option
    
    # 데이터 선택 적용
    if sample_option == "전체 데이터 사용":
        selected_df = df.copy()
    elif sample_option == "랜덤 샘플 사용":
        sample_size = st.slider("샘플 크기:", min_value=10, max_value=min(1000, len(df)), value=min(100, len(df)), key="past_sample_size")
        
        # 샘플 크기가 변경되면 예측 상태 리셋
        if st.session_state.past_sample_size_previous != sample_size:
            st.session_state.past_prediction_executed = False
            st.session_state.past_prediction_results = None
            st.session_state.past_sample_size_previous = sample_size
        
        selected_df = df.sample(sample_size, random_state=42)
    else:  # 특정 레코드 선택
        # 인덱스 기반 선택
        record_index = st.slider("레코드 인덱스 선택:", min_value=0, max_value=len(df)-1, value=0, key="past_record_index")
        
        # 레코드 인덱스가 변경되면 예측 상태 리셋
        if st.session_state.past_record_index_previous != record_index:
            st.session_state.past_prediction_executed = False
            st.session_state.past_prediction_results = None
            st.session_state.past_record_index_previous = record_index
        
        selected_df = df.iloc[[record_index]]
    
    # Lot_ID 대신 인덱스를 사용하기 위해 리셋 인덱스
    selected_df = selected_df.reset_index().rename(columns={'index': 'Record_ID'})
    
    # 예측 실행 버튼 또는 이전 예측 결과가 있으면 결과 표시
    if st.button("예측 실행 및 비교", key="past_prediction_btn") or st.session_state.past_prediction_executed:
        # 처음 실행 시 계산 수행, 아니면 세션에서 가져옴
        if not st.session_state.past_prediction_executed or st.session_state.past_prediction_results is None:
            with st.spinner("예측 중..."):
                # X와 y 분리
                X = selected_df[feature_cols]
                y_true = selected_df['target']
                
                # 예측 수행
                y_pred = model.predict(X)
                y_pred_proba = model.predict_proba(X)[:, 1]  # 양성 클래스 확률
                
                # 결과 프레임 생성
                result_df = selected_df[['Record_ID']].copy()
                result_df['실제값'] = y_true
                result_df['예측값'] = y_pred
                result_df['예측_확률'] = y_pred_proba
                result_df['정답여부'] = (y_true == y_pred).map({True: '✓', False: '✗'})
                
                # 정확도 계산
                accuracy = accuracy_score(y_true, y_pred)
                precision = precision_score(y_true, y_pred, zero_division=0)
                recall = recall_score(y_true, y_pred, zero_division=0)
                f1 = f1_score(y_true, y_pred, zero_division=0)
                
                # 혼동 행렬 계산
                cm = confusion_matrix(y_true, y_pred)
                
                # 결과 세션에 저장
                st.session_state.past_prediction_results = {
                    'result_df': result_df,
                    'accuracy': accuracy,
                    'precision': precision,
                    'recall': recall,
                    'f1': f1,
                    'confusion_matrix': cm,
                    'y_true': y_true,
                    'y_pred': y_pred,
                    'y_pred_proba': y_pred_proba
                }
                st.session_state.past_prediction_executed = True
        
        # 세션에서 결과 가져오기
        results = st.session_state.past_prediction_results
        result_df = results['result_df']
        accuracy = results['accuracy']
        precision = results['precision']
        recall = results['recall']
        f1 = results['f1']
        cm = results['confusion_matrix']
        y_true = results['y_true']
        y_pred = results['y_pred']
        y_pred_proba = results['y_pred_proba']
        
        # 결과 표시
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("예측 성능 지표")
            metrics_df = pd.DataFrame({
                '지표': ['정확도(Accuracy)', '정밀도(Precision)', '재현율(Recall)', 'F1 점수'],
                '값': [accuracy, precision, recall, f1]
            })
            st.dataframe(metrics_df, use_container_width=True)
            
            # 혼동 행렬 시각화
            st.subheader("혼동 행렬")
            
            # 단일 데이터 예측 시 간단한 결과 표시
            if len(y_true) == 1:
                result_status = "맞음 ✓" if y_true.iloc[0] == y_pred[0] else "틀림 ✗"
                actual = "불량" if y_true.iloc[0] == 1 else "양호"
                predicted = "불량" if y_pred[0] == 1 else "양호"
                
                st.write(f"**실제값**: {actual} (클래스 {y_true.iloc[0]})")
                st.write(f"**예측값**: {predicted} (클래스 {y_pred[0]})")
                st.write(f"**결과**: {result_status}")
                
                # 예측 확률 표시 (안전하게 처리)
                positive_prob = y_pred_proba[0]
                st.write(f"**불량 예측 확률**: {positive_prob:.4f} ({positive_prob*100:.2f}%)")
                
                # 확률 게이지 (안전하게 수정)
                prob_fig = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = positive_prob * 100,
                    title = {'text': "불량 예측 확률 (%)"},
                    gauge = {
                        'axis': {'range': [0, 100]},
                        'bar': {'color': "red" if y_pred[0] == 1 else "gray"},
                        'steps': [
                            {'range': [0, 50], 'color': "lightgray"},
                            {'range': [50, 100], 'color': "lightpink"}
                        ],
                        'threshold': {
                            'line': {'color': "green", 'width': 4},
                            'thickness': 0.75,
                            'value': 50
                        }
                    }
                ))
                
                prob_fig.update_layout(height=300, width=350)
                st.plotly_chart(prob_fig)
            else:
                # 여러 데이터인 경우 혼동 행렬 표시
                # plotly를 사용한 혼동 행렬 시각화
                z = cm
                x = ['양호 예측', '불량 예측']
                y = ['실제 양호', '실제 불량']
                
                # 2x2 혼동 행렬이 아닌 경우 처리
                if z.shape != (2, 2):
                    # 클래스가 하나만 있을 경우 2x2로 확장
                    if z.shape == (1, 1):
                        # 단일 클래스만 있는 경우 (모두 0 또는 모두 1)
                        classes = np.unique(np.concatenate([y_true, y_pred]))
                        if len(classes) == 1:
                            # 모두 같은 클래스일 경우
                            class_val = classes[0]
                            if class_val == 0:  # 모두 불량
                                z = np.array([[z[0, 0], 0], [0, 0]])
                            else:  # 모두 양호
                                z = np.array([[0, 0], [0, z[0, 0]]])
                    elif z.shape == (1, 2):
                        # 실제값은 하나의 클래스만 있지만 예측은 두 클래스가 있는 경우
                        if np.all(y_true == 0):  # 모두 불량
                            z = np.array([z[0], [0, 0]])
                        else:  # 모두 양호
                            z = np.array([[0, 0], z[0]])
                    elif z.shape == (2, 1):
                        # 예측값은 하나의 클래스만 있지만 실제값은 두 클래스가 있는 경우
                        if np.all(y_pred == 0):  # 모두 불량으로 예측
                            z = np.array([z[:, 0], [0, 0]]).T
                        else:  # 모두 양호로 예측
                            z = np.array([[0, 0], z[:, 0]]).T
                
                # 색상 설정 (Blues 색상 스키마 모방)
                colorscale = [
                    [0, "rgb(241, 247, 255)"],    # lightest blue
                    [1, "rgb(24, 116, 205)"]      # darkest blue
                ]
                
                # 주석 텍스트 설정
                annotations = []
                for i in range(len(y)):
                    for j in range(len(x)):
                        value = z[i, j] if i < z.shape[0] and j < z.shape[1] else 0
                        annotations.append(
                            dict(
                                x=j,
                                y=i,
                                text=str(value),
                                font=dict(color='white' if value > z.max()/2 else 'black', size=14),
                                showarrow=False
                            )
                        )
                
                # 혼동 행렬 히트맵 생성
                confusion_fig = go.Figure(data=go.Heatmap(
                    z=z,
                    x=x,
                    y=y,
                    colorscale=colorscale,
                    showscale=False
                ))
                
                # 주석 및 레이아웃 설정
                confusion_fig.update_layout(
                    title='혼동 행렬',
                    annotations=annotations,
                    xaxis=dict(title='예측', tickmode='array', tickvals=[0, 1], ticktext=x),
                    yaxis=dict(title='실제', tickmode='array', tickvals=[0, 1], ticktext=y),
                    width=450,
                    height=400,
                    margin=dict(t=40, b=40, l=40, r=40)
                )
                
                # 그래프 표시
                st.plotly_chart(confusion_fig)
        
        with col2:
            # 예측 분포 시각화
            st.subheader("예측 확률 분포")
            
            fig = px.histogram(result_df, x='예측_확률', color='실제값', barmode='overlay',
                             labels={'예측_확률': '양성 클래스 예측 확률', '실제값': '실제 결과'},
                             title='예측 확률 분포')
            fig.update_layout(xaxis_range=[0, 1])
            st.plotly_chart(fig, use_container_width=True)
            
            # ROC 곡선 (향후 구현)
        
        # 예측 결과 테이블
        st.subheader("예측 결과 상세")
        st.dataframe(result_df, use_container_width=True)
        
        # CSV 다운로드 버튼
        csv = result_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="CSV로 다운로드",
            data=csv,
            file_name="icp_prediction_results.csv",
            mime="text/csv",
        )
        
        # AI 분석 섹션 추가
        st.markdown("---")
        st.subheader("🤖 AI 분석: 예측 결과 평가")
        
        # 지표 정보 준비
        metrics_summary = (
            f"정확도: {accuracy:.4f}, 정밀도: {precision:.4f}, "
            f"재현율: {recall:.4f}, F1 점수: {f1:.4f}"
        )
        
        # 프롬프트 생성
        prompt = f"""
        다음은 ICP 예측 모델(XGBoost)의 성능 평가 결과입니다:
        
        성능 지표: {metrics_summary}
        데이터 샘플 수: {len(y_true)}
        
        이 성능 평가 결과를 자세히 분석하고 아래 구조에 맞춰 마크다운 리포트를 작성해주세요:
        
        ### 1. 성능 요약
        - 모델의 전반적인 성능은 어떠한가요? (참고: 이 모델에서는 1이 불량, 0이 양호를 의미함)
        - 주요 지표를 기준으로 볼 때 어떤 특징이 있나요?
        
        ### 2. 강점과 약점
        - 모델이 잘 예측하는 부분은 무엇인가요?
        - 모델이 개선이 필요한 부분은 무엇인가요?
        
        ### 3. 실무 적용 방안
        - 이 모델을 현장에 적용할 때 주의해야 할 점은 무엇인가요?
        - 어떤 상황에서 모델을 신뢰할 수 있고, 어떤 상황에서 신중해야 하나요?
        
        ### 4. 개선 제안
        - 모델 성능을 향상시키기 위한 구체적인 제안은 무엇인가요?
        - 데이터 측면에서 어떤 개선이 필요한가요?
        
        리포트는 명확하고 간결하게 작성하고, 중요한 발견이나 인사이트는 **볼드체**로 강조해주세요.
        """
        
        # AI 분석 UI 표시
        try:
            # 세션 상태에 AI 분석 실행 상태 저장
            # 이것이 리셋 방지의 핵심입니다
            is_running = display_analysis_ui(
                prompt=prompt,
                button_label="AI 예측 결과 분석 실행",
                key_prefix="icp_past_prediction",
                info_message="AI 분석을 실행하려면 버튼을 클릭하세요."
            )
            
            if is_running:
                with st.chat_message("assistant"):
                    message_placeholder = st.empty()
                    metadata_placeholder = st.empty()
                    with st.spinner("AI가 예측 결과를 분석하고 있습니다..."):
                        generate_ai_analysis(
                            prompt=prompt,
                            key_prefix="icp_past_prediction",
                            message_placeholder=message_placeholder,
                            metadata_placeholder=metadata_placeholder
                        )
        except Exception as e:
            st.error(f"AI 분석 생성 중 오류가 발생했습니다: {str(e)}")

def show_future_prediction(df, model):
    """미래 ICP 예측 시뮬레이션을 제공합니다."""
    st.subheader("2. 미래 ICP 예측 시뮬레이션")
    
    if df is None or model is None:
        return
    
    # 세션 상태 키 초기화
    if 'future_prediction_executed' not in st.session_state:
        st.session_state.future_prediction_executed = False
    if 'future_prediction_results' not in st.session_state:
        st.session_state.future_prediction_results = None
    
    # 특성 컬럼 가져오기
    feature_cols = get_feature_columns(df)
    
    if not feature_cols:
        st.error("QCP 특성 컬럼을 찾을 수 없습니다.")
        return
    
    # 사용자 입력 방식 선택
    input_methods = ["기존 데이터에서 선택하여 수정", "모든 값 수동 입력"]
    input_method = st.radio("입력 방식 선택:", input_methods, key="future_input_method")
    
    input_data = {}
    
    if input_method == "기존 데이터에서 선택하여 수정":
        # 데이터 인덱스 기반 선택
        sample_index = st.slider("참조할 데이터 인덱스:", 0, len(df)-1, 0, key="future_sample_index")
        sample_row = df.iloc[sample_index]
        
        # 선택한 샘플 데이터 표시
        st.write("**선택한 데이터:**")
        st.dataframe(sample_row[feature_cols].to_frame().T)
        
        # 수정할 특성 선택
        st.write("**수정할 특성 선택:**")
        cols = st.columns(3)
        
        for i, feature in enumerate(feature_cols):
            col_idx = i % 3
            with cols[col_idx]:
                # 이전에 저장된 값 있으면 사용, 없으면 샘플 값 사용
                saved_value = st.session_state.get(f"future_input_{feature}", float(sample_row[feature]))
                input_data[feature] = st.number_input(
                    f"{feature}",
                    value=saved_value,
                    format="%.5f",
                    key=f"future_input_{feature}"
                )
    else:
        # 모든 값 수동 입력
        st.write("**QCP 값 입력:**")
        cols = st.columns(3)
        
        for i, feature in enumerate(feature_cols):
            col_idx = i % 3
            with cols[col_idx]:
                # 데이터의 평균과 표준편차를 사용하여 기본값 설정
                default_value = st.session_state.get(f"future_input_{feature}", float(df[feature].mean()))
                input_data[feature] = st.number_input(
                    f"{feature}",
                    value=default_value,
                    format="%.5f",
                    key=f"future_input_{feature}"
                )
    
    # 예측 버튼 또는 이전 예측 결과가 있으면 결과 표시
    if st.button("ICP 결과 예측", key="future_prediction_btn") or st.session_state.future_prediction_executed:
        # 처음 실행 시 계산 수행, 아니면 세션에서 가져옴
        if not st.session_state.future_prediction_executed or st.session_state.future_prediction_results is None:
            with st.spinner("예측 중..."):
                # 입력 데이터를 DataFrame으로 변환
                input_df = pd.DataFrame([input_data])
                
                # 예측 수행
                prediction = model.predict(input_df)[0]
                prediction_proba = model.predict_proba(input_df)[0]
                
                # 안전하게 확률 처리
                positive_prob = prediction_proba[1] if len(prediction_proba) > 1 else prediction_proba[0]
                
                # 결과 카드 스타일
                result_color = "red" if prediction == 1 else "green"
                result_text = "불량 (Fail)" if prediction == 1 else "양호 (Pass)"
                
                # 특성 중요도 계산 (gain 기준)
                importances = model.get_booster().get_score(importance_type='gain')
                
                # 입력 값과 중요도 합치기
                feature_df = pd.DataFrame({
                    'QCP': feature_cols,
                    '입력값': [input_data[feat] for feat in feature_cols]
                })
                
                # 중요도 추가
                feature_df['중요도'] = feature_df['QCP'].map(lambda x: importances.get(x, 0))
                feature_df = feature_df.sort_values('중요도', ascending=False)
                
                # 결과 세션에 저장
                st.session_state.future_prediction_results = {
                    'prediction': prediction,
                    'positive_prob': positive_prob,
                    'result_color': result_color,
                    'result_text': result_text,
                    'feature_df': feature_df,
                    'input_data': input_data
                }
                st.session_state.future_prediction_executed = True
        
        # 세션에서 결과 가져오기
        results = st.session_state.future_prediction_results
        prediction = results['prediction']
        positive_prob = results['positive_prob']
        result_color = results['result_color'] 
        result_text = results['result_text']
        feature_df = results['feature_df']
        
        # 결과 표시
        st.markdown("### 예측 결과")
        
        # 결과 카드 생성
        st.markdown(f"""
        <div style="padding: 20px; border-radius: 10px; background-color: {result_color}; color: white; text-align: center; margin-bottom: 20px;">
            <h2 style="margin: 0;">ICP 예측 결과: {result_text}</h2>
            <p style="margin: 10px 0 0 0; font-size: 18px;">신뢰도: {positive_prob * 100:.2f}%</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 확률 게이지 차트
        st.subheader("예측 확률 분포")
        
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = positive_prob * 100,
            title = {'text': "불량 확률 (%)"},
            gauge = {
                'axis': {'range': [0, 100]},
                'bar': {'color': "red" if prediction == 1 else "gray"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 100], 'color': "lightpink"}
                ],
                'threshold': {
                    'line': {'color': "green", 'width': 4},
                    'thickness': 0.75,
                    'value': 50
                }
            }
        ))
        
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)
        
        # 입력 데이터와 중요도 표시
        st.subheader("입력 데이터 요약")
        
        # 상위 10개 특성만 표시
        top_features = feature_df.head(10)
        
        # 중요도 막대 그래프
        fig = px.bar(top_features, x='QCP', y='중요도', title='주요 영향 특성 (상위 10개)',
                     text='입력값', labels={'QCP': 'QCP 항목', '중요도': '영향도'})
        fig.update_traces(marker_color='royalblue')
        st.plotly_chart(fig, use_container_width=True)
        
        # 모든 입력 데이터 표시
        with st.expander("전체 입력 데이터 보기"):
            st.dataframe(feature_df)
        
        # AI 분석 섹션 추가
        st.markdown("---")
        st.subheader("🤖 AI 분석: 예측 결과 해석")
        
        # 상위 5개 중요 특성 정보 준비
        top_features_str = ", ".join([
            f"{row['QCP']} (중요도: {row['중요도']:.4f}, 값: {row['입력값']:.4f})" 
            for _, row in top_features.head(5).iterrows()
        ])
        
        # 프롬프트 생성
        prompt = f"""
        다음은 ICP 예측 모델(XGBoost)의 예측 결과입니다:
        
        결과: {result_text} (신뢰도: {positive_prob * 100:.2f}%)
        
        주요 영향 특성 (상위 5개):
        {top_features_str}
        
        이 예측 결과를 자세히 분석하고 아래 구조에 맞춰 마크다운 리포트를 작성해주세요:
        
        ### 1. 예측 결과 요약
        - 모델이 예측한 결과는 무엇이며, 신뢰도는 어느 정도인가요? (참고: 이 모델에서는 1이 불량, 0이 양호를 의미함)
        - 이 결과의 의미는 무엇인가요?
        
        ### 2. 주요 영향 요인 분석
        - 어떤 QCP 특성이 이 예측에 가장 큰 영향을 미쳤나요?
        - 주요 특성의 값은 적정 범위에 있나요? 아니면 특이점이 있나요?
        
        ### 3. 결과 평가 및 신뢰성
        - 이 예측 결과를 얼마나 신뢰할 수 있나요?
        - 추가적인 검증이 필요한 부분이 있나요?
        
        ### 4. 실무 적용 시 고려사항
        - 이 예측 결과를 바탕으로 어떤 조치를 고려할 수 있나요?
        - 결과의 신뢰도를 높이기 위해 추가로 점검해야 할 사항이 있나요?
        
        리포트는 명확하고 간결하게 작성하고, 중요한 발견이나 인사이트는 **볼드체**로 강조해주세요.
        """
        
        # AI 분석 UI 표시
        try:
            # 세션 상태에 AI 분석 실행 상태 저장
            # 이것이 리셋 방지의 핵심입니다
            is_running = display_analysis_ui(
                prompt=prompt,
                button_label="AI 예측 해석 실행",
                key_prefix="icp_future_prediction",
                info_message="AI 분석을 실행하려면 버튼을 클릭하세요."
            )
            
            if is_running:
                with st.chat_message("assistant"):
                    message_placeholder = st.empty()
                    metadata_placeholder = st.empty()
                    with st.spinner("AI가 예측 결과를 해석하고 있습니다..."):
                        generate_ai_analysis(
                            prompt=prompt,
                            key_prefix="icp_future_prediction",
                            message_placeholder=message_placeholder,
                            metadata_placeholder=metadata_placeholder
                        )
        except Exception as e:
            st.error(f"AI 분석 생성 중 오류가 발생했습니다: {str(e)}")

def show_icp_simulation():
    """ICP 시뮬레이션 메인 함수"""
    st.title("ICP 시뮬레이션")
    
    # 세션 상태 초기화 (AI 분석 포함)
    init_session_state(key_prefix="icp_simulation")
    init_session_state(key_prefix="icp_past_prediction")
    init_session_state(key_prefix="icp_future_prediction")
    
    # 모델 및 데이터 로드
    model = load_model()
    df = load_data()
    
    if model is None or df is None:
        st.error("모델 또는 데이터 로드에 실패했습니다. 파일 경로를 확인해주세요.")
        return
    
    # 세션 상태 리셋 버튼
    with st.sidebar:
        st.subheader("설정")
        if st.button("예측 결과 초기화", key="reset_prediction_results"):
            # 예측 결과 초기화
            st.session_state.past_prediction_executed = False
            st.session_state.past_prediction_results = None
            st.session_state.future_prediction_executed = False
            st.session_state.future_prediction_results = None
            # 입력 값도 초기화
            for key in list(st.session_state.keys()):
                if key.startswith("future_input_"):
                    del st.session_state[key]
            st.success("예측 결과가 초기화되었습니다.")
            st.rerun()
    
    # 탭 생성
    tab_id = st.radio("분석 유형 선택:", ["과거 예측 검증", "미래 ICP 예측"], horizontal=True, key="simulation_tab")
    
    # 탭 내용 구성
    if tab_id == "과거 예측 검증":
        show_past_prediction_comparison(df, model)
    else:
        show_future_prediction(df, model) 