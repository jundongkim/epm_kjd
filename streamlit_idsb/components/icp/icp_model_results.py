"""
ICP 모델 결과 시각화 및 분석 모듈
"""

import streamlit as st
import pandas as pd
import os
import glob
import matplotlib.pyplot as plt
import seaborn as sns
from PIL import Image
import io
import numpy as np
import xgboost as xgb
import shap
from components.ai_utils import (
    init_session_state,
    display_analysis_ui,
    generate_ai_analysis
)

# 폴더 경로
PLOTS_DIR = "ICP/plots_xgb"
MODELS_DIR = "ICP/models_xgb"

def show_icp_model_results():
    """
    ICP 모델 결과를 보여주는 메인 함수
    """
    # AI 분석을 위한 세션 상태 초기화
    init_session_state(key_prefix="icp_model_results")
    
    st.title("ICP 모델 분석 결과")
    
    # 세션 상태 초기화
    if 'selected_plot_category' not in st.session_state:
        st.session_state.selected_plot_category = "모델 성능"
    
    # 폴더 존재 여부 확인
    if not os.path.exists(PLOTS_DIR):
        st.error(f"'{PLOTS_DIR}' 폴더를 찾을 수 없습니다. 먼저 모델을 훈련해 주세요.")
        return
    
    # 파일 목록 가져오기
    html_files = glob.glob(os.path.join(PLOTS_DIR, "*.html"))
    csv_files = glob.glob(os.path.join(PLOTS_DIR, "*.csv"))
    
    if not html_files:
        st.warning(f"'{PLOTS_DIR}' 폴더에 HTML 시각화 파일이 없습니다. 먼저 모델을 훈련해 주세요.")
        return
    
    # 시각화 카테고리 분류
    categories = {
        "모델 성능": ["confusion_matrix", "roc_curve", "precision_recall_curve", "learning_curve"],
        "특성 중요도": ["feature_importance", "shap_feature_importance", "shap_summary"],
        "SHAP 의존성": ["shap_dependence_"]
    }
    
    # 카테고리별 추천 높이 설정
    recommended_heights = {
        "모델 성능": 750,
        "특성 중요도": 700,
        "SHAP 의존성": 700
    }
    
    # 파일 유형별 추천 높이 미세 조정
    file_type_heights = {
        "confusion_matrix": 750,
        "confusion_matrix_normalized": 750,
        "roc_curve": 800,
        "precision_recall_curve": 800,
        "learning_curve": 750,
        "feature_importance": 700,
        "shap_feature_importance": 750,
        "shap_summary": 800,
        "shap_dependence": 700
    }
    
    # 메인 페이지 상단에 설정 섹션 추가
    st.markdown("## 시각화 설정")
    
    # 설정을 위한 열 생성
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 시각화 카테고리 선택
        category_names = list(categories.keys())
        selected_category = st.radio(
            "시각화 카테고리:", 
            category_names, 
            index=category_names.index(st.session_state.selected_plot_category) 
                if st.session_state.selected_plot_category in category_names else 0,
            horizontal=True
        )
    
    # 선택된 카테고리 저장
    st.session_state.selected_plot_category = selected_category
    
    # 선택한 카테고리에 해당하는 파일 필터링
    filtered_files = []
    for pattern in categories[selected_category]:
        # 중복 파일 제거를 위해 파일 경로 기준으로 필터링
        matched_files = [f for f in html_files if pattern in os.path.basename(f)]
        for file in matched_files:
            if file not in filtered_files:
                filtered_files.append(file)
    
    if not filtered_files:
        st.info(f"선택한 카테고리({selected_category})에 해당하는 시각화 파일이 없습니다.")
        return
    
    # 시각화 표시
    st.markdown("---")
    st.subheader(f"{selected_category} 시각화")
    
    # 선택한 파일이 있는지 확인
    if "selected_viz_file" not in st.session_state:
        st.session_state.selected_viz_file = filtered_files[0] if filtered_files else None
    
    # 다음 및 이전 버튼이 클릭되었는지 확인하기 위한 상태
    if "viz_index" not in st.session_state:
        st.session_state.viz_index = 0
    
    # 파일 선택 UI
    file_options = [os.path.basename(f).replace('.html', '') for f in filtered_files]
    
    # viz_index가 범위를 벗어나지 않도록 보정
    if st.session_state.viz_index >= len(file_options):
        st.session_state.viz_index = 0
    
    # 파일 선택과 시각화 높이 조절을 위한 열 생성
    col1, col2 = st.columns([3, 1])
    
    with col1:
        selected_file_name = st.selectbox(
            "시각화 선택:", 
            file_options, 
            index=st.session_state.viz_index
        )
    
    # 기본 높이 설정 (카테고리 기반)
    default_height = recommended_heights.get(selected_category, 750)
    
    # 파일 이름 기반으로 높이 미세 조정
    for file_type, height in file_type_heights.items():
        if file_type in selected_file_name:
            default_height = height
            break
    
    with col2:
        # 높이 조절 슬라이더
        vis_height = st.slider(
            "시각화 높이:",
            min_value=400,
            max_value=1200,
            value=default_height,
            step=50,
            key=f"model_vis_height_{selected_category}"
        )
    
    selected_file_path = os.path.join(PLOTS_DIR, f"{selected_file_name}.html")
    st.session_state.selected_viz_file = selected_file_path
    st.session_state.viz_index = file_options.index(selected_file_name)
    
    # HTML 내용 읽기 및 표시
    try:
        with open(selected_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 컨테이너로 감싸기
        vis_container = st.container()
        with vis_container:
            st.caption(f"파일: {selected_file_name} (높이: {vis_height}px)")
            # HTML 컴포넌트로 렌더링
            st.components.v1.html(html_content, height=vis_height, scrolling=True)
        
        # 관련 CSV 파일이 있으면 데이터 표시 버튼 추가
        csv_file_name = selected_file_name.replace('_normalized', '').replace('_html', '')
        csv_file = os.path.join(PLOTS_DIR, f"{csv_file_name}.csv")
        if os.path.exists(csv_file):
            if st.button(f"{csv_file_name} 데이터 보기", key=f"btn_{csv_file_name}"):
                df = pd.read_csv(csv_file)
                st.dataframe(df)
                
                # CSV 다운로드 버튼
                csv_data = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label=f"{csv_file_name} 데이터 다운로드",
                    data=csv_data,
                    file_name=f"{csv_file_name}.csv",
                    mime="text/csv"
                )
    except Exception as e:
        st.error(f"HTML 파일 로드 오류: {e}")
        st.error(f"파일 경로: {selected_file_path}")
    
    # AI 분석 섹션
    st.markdown("---")
    st.subheader(f"🤖 AI 분석: {selected_file_name}")
    
    # 프롬프트 생성
    prompt = f"""
    다음은 ICP 모델 분석 결과 시각화입니다:
    파일명: {selected_file_name}.html
    카테고리: {selected_category}
    
    이 시각화 결과를 자세히 분석하고 아래 구조에 맞춰 마크다운 리포트를 작성해주세요:
    
    ### 1. 시각화 개요
    - 이 시각화는 무엇을 보여주고 있습니까? (예: 모델 성능 지표, 특성 중요도, SHAP 값 등)
    - 어떤 모델링 관점에서 이 결과를 해석해야 합니까?
    
    ### 2. 주요 관찰 사항
    - 시각화에서 중요한 패턴이나 특징은 무엇입니까?
    - 모델의 성능이나 특성 중요도에서 특이점이 있습니까?
    
    ### 3. 모델 개선 인사이트
    - 이 시각화 결과를 바탕으로 모델을 어떻게 개선할 수 있습니까?
    - 특별히 주목해야 할 특성이나 패턴이 있습니까?
    
    ### 4. 비즈니스 적용 방안
    - 이 분석 결과가 실제 비즈니스/품질 관리에 어떻게 적용될 수 있습니까?
    - 의사결정에 어떤 도움을 줄 수 있습니까?
    
    리포트는 명확하고 간결하게 작성하고, 중요한 발견이나 인사이트는 **볼드체**로 강조해주세요.
    """
    
    # AI 분석 UI 표시
    try:
        is_running = display_analysis_ui(
            prompt=prompt,
            button_label="AI 시각화 분석 실행",
            key_prefix="icp_model_results",
            info_message="AI 분석을 실행하려면 버튼을 클릭하세요."
        )
        
        if is_running:
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                metadata_placeholder = st.empty()
                with st.spinner("AI가 시각화를 분석하고 있습니다..."):
                    generate_ai_analysis(
                        prompt=prompt,
                        key_prefix="icp_model_results",
                        message_placeholder=message_placeholder,
                        metadata_placeholder=metadata_placeholder
                    )
    except Exception as e:
        st.error(f"AI 시각화 분석 생성 중 오류가 발생했습니다: {str(e)}")
    
    # 성능 지표 불러오기
    metrics_file = os.path.join(PLOTS_DIR, "performance_metrics.csv")
    if os.path.exists(metrics_file):
        st.markdown("---")
        st.subheader("모델 성능 지표")
        metrics_df = pd.read_csv(metrics_file)
        
        # 메트릭 표시
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("정확도", f"{metrics_df['accuracy'][0]:.4f}")
        with col2:
            st.metric("정밀도", f"{metrics_df['precision'][0]:.4f}")
        with col3:
            st.metric("재현율", f"{metrics_df['recall'][0]:.4f}")
        with col4:
            st.metric("F1 점수", f"{metrics_df['f1'][0]:.4f}")
        with col5:
            st.metric("AUC", f"{metrics_df['auc'][0]:.4f}")
    
    # 특성 중요도 분석
    if selected_category == "특성 중요도":
        importance_file = os.path.join(PLOTS_DIR, "feature_importance.csv")
        if os.path.exists(importance_file):
            importance_df = pd.read_csv(importance_file)
            
            st.subheader("주요 특성 분석")
            
            # 상위 10개 특성만 표시
            top_features = importance_df.head(10)
            
            # 특성 중요도 해석
            interpretation = """
            특성 중요도는 모델의 예측에 각 특성이 얼마나 기여하는지 보여줍니다. 
            높은 중요도를 가진 특성은 모델의 예측에 더 큰 영향을 미칩니다.
            
            주요 특성들:
            """
            
            feature_list = ""
            feature_col = 'Feature' if 'Feature' in top_features.columns else 'feature'
            importance_col = 'Importance' if 'Importance' in top_features.columns else 'importance'
            
            for i, (feature, importance) in enumerate(zip(top_features[feature_col], top_features[importance_col])):
                feature_list += f"- **{feature}**: 상대적 중요도 {importance:.4f}\n"
            
            st.markdown(interpretation + "\n" + feature_list)
    
    # SHAP 의존성 플롯 분석
    elif selected_category == "SHAP 의존성":
        st.markdown("""
        SHAP 의존성 플롯은 특성값과 해당 특성의 모델 예측 기여도(SHAP 값) 간의 관계를 보여줍니다.
        - X축: 특성값
        - Y축: SHAP 값 (모델 예측에 대한 기여도)
        - 색상: 다른 특성과의 상호작용 (기본적으로 가장 강한 상호작용을 가진 특성으로 색상 지정)
        
        양수 SHAP 값은 예측 확률을 증가시키는 기여를, 음수 SHAP 값은 예측 확률을 감소시키는 기여를 나타냅니다.
        """)
    
    # 모델 성능 분석
    elif selected_category == "모델 성능":
        st.markdown("""
        ### 모델 성능 분석
        
        **혼동 행렬(Confusion Matrix)**:
        - 실제 클래스와 예측 클래스 간의 관계를 보여줍니다.
        - 대각선 요소는 올바르게 분류된 샘플을, 비대각선 요소는 잘못 분류된 샘플을 나타냅니다.
        
        **ROC 곡선**:
        - 다양한 임계값에서 모델의 성능을 평가합니다.
        - AUC(Area Under Curve)가 1에 가까울수록 모델 성능이 우수합니다.
        
        **정밀도-재현율 곡선**:
        - 정밀도(Precision)와 재현율(Recall) 간의 트레이드오프를 보여줍니다.
        - 불균형 데이터셋에서 모델 성능을 평가하는 데 유용합니다.
        
        **학습 곡선**:
        - 훈련 진행에 따른 모델 성능 변화를 보여줍니다.
        - 과적합 여부를 판단하는 데 도움이 됩니다.
        """)

if __name__ == "__main__":
    show_icp_model_results() 