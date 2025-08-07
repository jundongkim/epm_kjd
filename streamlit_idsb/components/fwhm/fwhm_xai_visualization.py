"""
FWHM XAI (설명 가능한 AI) 시각화 및 분석 모듈
"""

import streamlit as st
import pandas as pd
import os
import glob
import numpy as np
import plotly.express as px
from components.ai_utils import (
    init_session_state,
    display_analysis_ui,
    generate_ai_analysis
)
import re
from datetime import datetime

# 모델별 플롯 폴더 경로 설정
PLOTS_DIRS = {
    "CatBoost": "FWHM/plots_cbm",
    "XGBoost": "FWHM/plots_xgb"
}

def show_fwhm_xai_visualization():
    """
    FWHM XAI(설명 가능한 AI) 시각화를 보여주는 메인 함수
    """
    # AI 분석을 위한 세션 상태 초기화
    init_session_state(key_prefix="fwhm_xai_visualization")
    
    st.title("FWHM 설명 가능한 AI (XAI) 분석")
    
    # 세션 상태 초기화
    if 'selected_xai_category' not in st.session_state:
        st.session_state.selected_xai_category = "특성 중요도"
    
    # 사이드바에서 이미 설정된 모델 선택 값과 데이터셋 선택 값을 사용
    if 'selected_fwhm_model' in st.session_state:
        model_type = st.session_state.selected_fwhm_model
    else:
        model_type = "CatBoost"  # 기본값
        
    # 선택된 데이터셋 확인
    if 'selected_fwhm_dataset' in st.session_state:
        selected_dataset = st.session_state.selected_fwhm_dataset
    else:
        selected_dataset = "F28"  # 기본값
        
    # 선택된 모델 및 데이터셋 표시
    st.info(f"현재 선택된 모델: **{model_type}**, 데이터셋: **{selected_dataset}**", icon="ℹ️")
    
    # 선택된 모델과 데이터셋에 따른 플롯 디렉토리 결정
    dataset_suffix = f"_{selected_dataset}"
    
    # 모델 타입에 따른 디렉토리 접두어 매핑
    model_dir_prefix = {
        "CatBoost": "cbm",
        "XGBoost": "xgb"
    }
    
    # 안전하게 디렉토리 접두어 가져오기
    dir_prefix = model_dir_prefix.get(model_type, "cbm")  # 기본값은 cbm
    
    PLOTS_DIR = f"FWHM/plots_{dir_prefix}{dataset_suffix}"
    
    # 폴더 존재 여부 확인
    if not os.path.exists(PLOTS_DIR):
        st.error(f"'{PLOTS_DIR}' 폴더를 찾을 수 없습니다. 먼저 {model_type} 모델을 {selected_dataset} 데이터셋으로 훈련해 주세요.")
        return
    
    # 파일 목록 가져오기
    html_files = glob.glob(os.path.join(PLOTS_DIR, "*.html"))
    csv_files = glob.glob(os.path.join(PLOTS_DIR, "*.csv"))
    
    if not html_files:
        st.warning(f"'{PLOTS_DIR}' 폴더에 HTML 시각화 파일이 없습니다. 먼저 모델을 훈련해 주세요.")
        return
    
    # 모델별 파일 패턴 접두사 설정
    file_prefix = {
        "CatBoost": "catboost_",
        "XGBoost": "xgb_"
    }
    
    prefix = file_prefix[model_type]
    
    # 시각화 카테고리 분류
    categories = {
        "특성 중요도": [f"{prefix}shap_feature_importance", "feature_importance"],
        "SHAP 요약": [f"{prefix}shap_summary"],
        "SHAP 의존성": [f"{prefix}shap_dependence_"],
        "SHAP Force 플롯": [f"{prefix}shap_force_plot"],
        "SHAP 상호작용": [f"{prefix}shap_interaction_"]
    }
    
    # 디버깅 정보: 각 카테고리별 매칭된 파일 확인 (확장 가능)
    with st.expander("🔍 파일 매칭 정보 (디버깅)", expanded=False):
        st.write("### 발견된 HTML 파일 목록")
        st.write([os.path.basename(f) for f in html_files])
        
        st.write("### 카테고리별 매칭된 파일")
        for category, patterns in categories.items():
            matched_files = []
            for pattern in patterns:
                matched_files.extend([os.path.basename(f) for f in html_files if pattern in os.path.basename(f)])
            st.write(f"**{category}**: {matched_files}")
    
    # 카테고리별 추천 높이 설정
    recommended_heights = {
        "특성 중요도": 700,
        "SHAP 요약": 800,
        "SHAP 의존성": 700,
        "SHAP Force 플롯": 800,
        "SHAP 상호작용": 750
    }
    
    # 파일 유형별 추천 높이 미세 조정
    file_type_heights = {
        "shap_feature_importance": 700,
        "feature_importance": 650,
        "shap_summary": 800,
        "shap_summary_enhanced": 850,
        "shap_dependence": 700,
        "shap_force_plot": 800,
        "shap_interaction": 750
    }
    
    # 메인 페이지 상단에 설정 섹션 추가
    st.markdown("## 시각화 설정")
    
    # 설정을 위한 열 생성
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 시각화 카테고리 선택
        category_names = list(categories.keys())
        category_names.append("SHAP 데이터")
        
        selected_category = st.radio(
            "시각화 카테고리:", 
            category_names, 
            index=category_names.index(st.session_state.selected_xai_category) 
                if st.session_state.selected_xai_category in category_names else 0,
            horizontal=True
        )
    
    # 선택된 카테고리 저장
    st.session_state.selected_xai_category = selected_category
    
    # SHAP 데이터 선택 시
    if selected_category == "SHAP 데이터":
        st.subheader("SHAP 값 데이터")
        show_shap_data(PLOTS_DIR, prefix)
        return
    
    # 선택한 카테고리에 해당하는 파일 필터링
    filtered_files = []
    if selected_category in categories:
        for pattern in categories[selected_category]:
            # 중복 파일 제거를 위해 파일 경로 기준으로 필터링
            matched_files = [f for f in html_files if pattern in os.path.basename(f)]
            for file in matched_files:
                if file not in filtered_files:
                    filtered_files.append(file)
    
    if not filtered_files:
        st.info(f"선택한 카테고리({selected_category})에 해당하는 시각화 파일이 없습니다.")
        st.write("전체 HTML 파일 목록:")
        st.write([os.path.basename(f) for f in html_files])
        
        st.write("현재 검색 패턴:")
        st.write(categories.get(selected_category, []))
        
        if selected_category == "SHAP 의존성":
            # SHAP 의존성의 경우 추가 디버깅 정보
            dependence_files = [f for f in html_files if "dependence" in os.path.basename(f).lower()]
            if dependence_files:
                st.write("'dependence'를 포함하는 파일:")
                st.write([os.path.basename(f) for f in dependence_files])
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
            index=st.session_state.viz_index,
            key=f"xai_viz_select_{selected_category}"
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
            key=f"xai_vis_height_{selected_category}"
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
    다음은 FWHM 데이터의 {model_type} 모델에 대한 XAI(설명 가능한 AI) 시각화입니다:
    파일명: {selected_file_name}.html
    카테고리: {selected_category}
    모델: {model_type}
    
    이 시각화 결과를 자세히 분석하고 아래 구조에 맞춰 마크다운 리포트를 작성해주세요:
    
    ### 1. 시각화 개요
    - 이 시각화는 무엇을 보여주고 있으며, 어떤 인사이트를 제공합니까?
    - 이 결과는 모델의 예측 메커니즘에 대해 무엇을 알려줍니까?
    
    ### 2. 주요 특성 분석
    - SHAP 값을 기반으로 가장 중요한 특성은 무엇이며, 이들이 어떻게 예측에 기여합니까?
    - 특성값과 SHAP 값 사이에 어떤 관계가 있습니까?
    
    ### 3. 모델 해석 인사이트
    - 이 SHAP 분석을 통해 모델의 작동 방식에 대해 어떤 인사이트를 얻을 수 있습니까?
    - 모델이 특정 특성에 의존하는 이유와 그 영향은 무엇입니까?
    
    ### 4. 비즈니스 적용 및 개선 방안
    - 이 XAI 분석 결과가 실제 비즈니스/품질 관리 프로세스에 어떻게 적용될 수 있습니까?
    - 이 인사이트를 바탕으로 모델이나 공정 개선을 위한 구체적인 제안은 무엇입니까?
    
    리포트는 명확하고 간결하게 작성하고, 중요한 발견이나 인사이트는 **볼드체**로 강조해주세요.
    """
    
    # AI 분석 UI 표시
    try:
        is_running = display_analysis_ui(
            prompt=prompt,
            button_label="AI 시각화 분석 실행",
            key_prefix="fwhm_xai_visualization",
            info_message="AI 분석을 실행하려면 버튼을 클릭하세요."
        )
        
        if is_running:
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                metadata_placeholder = st.empty()
                with st.spinner("AI가 시각화를 분석하고 있습니다..."):
                    generate_ai_analysis(
                        prompt=prompt,
                        key_prefix="fwhm_xai_visualization",
                        message_placeholder=message_placeholder,
                        metadata_placeholder=metadata_placeholder
                    )
    except Exception as e:
        st.error(f"AI 시각화 분석 생성 중 오류가 발생했습니다: {str(e)}")
    
    # 특성 의존성 분석 추가 정보
    if selected_category == "SHAP 의존성":
        st.markdown("""
        ### SHAP 의존성 분석
        
        SHAP 의존성 플롯은 특성값과 해당 특성의 모델 예측 기여도(SHAP 값) 간의 관계를 보여줍니다.
        - X축: 특성값
        - Y축: SHAP 값 (모델 예측에 대한 기여도)
        - 색상: 다른 특성과의 상호작용 (기본적으로 가장 강한 상호작용을 가진 특성으로 색상 지정)
        
        양수 SHAP 값은 예측값을 증가시키는 기여를, 음수 SHAP 값은 예측값을 감소시키는 기여를 나타냅니다.
        """)

def show_shap_data(PLOTS_DIR, prefix):
    """SHAP 값 데이터를 표시하고 다운로드 기능을 제공하는 함수"""
    shap_csv = os.path.join(PLOTS_DIR, f"{prefix}shap_values.csv")
    
    if os.path.exists(shap_csv):
        # 데이터 로드
        df = pd.read_csv(shap_csv)
        
        # 기본 정보 표시
        st.info(f"⚠️ SHAP 값 데이터가 포함된 CSV 파일을 찾았습니다: {os.path.basename(shap_csv)}")
        
        # 데이터 개요
        col1, col2 = st.columns(2)
        with col1:
            st.metric("행 수", df.shape[0])
        with col2:
            st.metric("특성 수", df.shape[1] - 2 if 'prediction' in df.columns and 'actual' in df.columns else df.shape[1] - 1 if 'prediction' in df.columns else df.shape[1])
            
        # 데이터 미리보기 및 분석 옵션
        tab1, tab2, tab3 = st.tabs(["데이터 미리보기", "기술 통계", "상관관계"])
        
        with tab1:
            # 표시할 행 수 선택
            rows_to_show = st.slider("표시할 행 수:", min_value=5, max_value=min(100, df.shape[0]), value=20, step=5)
            st.dataframe(df.head(rows_to_show))
            
        with tab2:
            # 기술 통계 계산
            st.write("SHAP 값 기술 통계:")
            # SHAP 값에 대한 통계만 계산 (prediction, actual 열 제외)
            feature_cols = [col for col in df.columns if col not in ['prediction', 'actual']]
            if feature_cols:
                stats_df = df[feature_cols].describe().T
                # SHAP 값 절대값의 평균으로 정렬
                stats_df['abs_mean'] = df[feature_cols].abs().mean()
                stats_df = stats_df.sort_values('abs_mean', ascending=False)
                stats_df = stats_df.drop('abs_mean', axis=1)
                st.dataframe(stats_df)
            else:
                st.warning("특성 열을 찾을 수 없습니다.")
                
        with tab3:
            # 상관관계 분석
            st.write("SHAP 값 간 상관관계:")
            
            if feature_cols and len(feature_cols) > 1:
                # 상위 N개 특성만 선택
                num_features = st.slider(
                    "상관관계를 계산할 상위 특성 수:", 
                    min_value=5, 
                    max_value=min(30, len(feature_cols)), 
                    value=min(15, len(feature_cols))
                )
                
                # SHAP 값의 절대값 기준으로 상위 특성 선택
                top_features = df[feature_cols].abs().mean().sort_values(ascending=False).head(num_features).index.tolist()
                if top_features:
                    corr_df = df[top_features].corr()
                    
                    # 히트맵 생성
                    fig = px.imshow(
                        corr_df,
                        text_auto='.2f',
                        color_continuous_scale='RdBu_r',
                        origin='lower',
                        title="상위 특성 간 SHAP 값 상관관계"
                    )
                    fig.update_layout(height=600, width=800)
                    st.plotly_chart(fig)
                else:
                    st.warning("상관관계를 계산할 특성이 충분하지 않습니다.")
            else:
                st.warning("상관관계 분석을 위한 특성이 충분하지 않습니다.")
        
        # 특성 필터링 및 상세보기
        st.subheader("특성 필터링 및 상세보기")
        
        # 특성 검색 및 필터링
        if feature_cols:
            search_term = st.text_input("특성 이름 검색:", key="shap_search")
            if search_term:
                filtered_cols = [col for col in feature_cols if search_term.lower() in col.lower()]
                if filtered_cols:
                    st.success(f"{len(filtered_cols)}개의 특성을 찾았습니다.")
                    
                    # prediction/actual 열이 있으면 포함
                    display_cols = filtered_cols.copy()
                    if 'prediction' in df.columns:
                        display_cols.append('prediction')
                    if 'actual' in df.columns:
                        display_cols.append('actual')
                    
                    st.dataframe(df[display_cols].head(20))
                else:
                    st.warning(f"'{search_term}'을 포함하는 특성을 찾을 수 없습니다.")
        
        # 다운로드 버튼
        st.subheader("데이터 다운로드")
        csv_data = df.to_csv(index=False).encode('utf-8')
        
        # 열 선택 옵션
        download_option = st.radio(
            "다운로드 옵션:",
            ["전체 데이터", "선택한 특성만"],
            horizontal=True
        )
        
        if download_option == "선택한 특성만" and feature_cols:
            selected_cols = st.multiselect(
                "다운로드할 특성 선택 (prediction, actual은 자동 포함):",
                options=feature_cols,
                default=feature_cols[:min(5, len(feature_cols))]
            )
            
            if selected_cols:
                # prediction, actual 열 추가
                download_cols = selected_cols.copy()
                if 'prediction' in df.columns:
                    download_cols.append('prediction')
                if 'actual' in df.columns:
                    download_cols.append('actual')
                
                csv_data = df[download_cols].to_csv(index=False).encode('utf-8')
                
                st.download_button(
                    label=f"선택한 {len(selected_cols)}개 특성 데이터 다운로드",
                    data=csv_data,
                    file_name="selected_shap_values.csv",
                    mime="text/csv"
                )
            else:
                st.warning("다운로드할 특성을 선택해주세요.")
        else:
            st.download_button(
                label="전체 SHAP 값 데이터 다운로드",
                data=csv_data,
                file_name="shap_values.csv",
                mime="text/csv"
            )
        
        # AI 분석 섹션
        st.markdown("---")
        st.subheader(f"🤖 AI 분석: SHAP 데이터")
        
        # 프롬프트 생성
        prompt = f"""
        다음은 FWHM 데이터에 대한 원시 SHAP 값 데이터 분석입니다:
        
        파일: {os.path.basename(shap_csv)}
        
        이 데이터를 자세히 분석하고 아래 구조에 맞춰 마크다운 리포트를 작성해주세요:
        
        ### 1. 데이터 개요
        - SHAP 값 데이터는 무엇을 보여주고 있습니까?
        - 어떤 모델링 관점에서 이 결과를 해석해야 합니까?
        
        ### 2. 주요 관찰 사항
        - SHAP 값의 전반적인 분포 특성은 어떠한가요? 어떤 특성들이 가장 큰 절대값을 가지나요?
        - 특성 간 SHAP 값의 상관관계에서 주목할 만한 패턴이 있나요?
        
        ### 3. 모델 해석 인사이트
        - 양의 SHAP 값과 음의 SHAP 값을 가진 주요 특성들이 예측에 어떤 의미를 가지는지?
        - 이 결과를 바탕으로 모델을 어떻게 개선할 수 있습니까?
        
        ### 4. 비즈니스 적용 방안
        - 이 분석 결과가 실제 비즈니스/품질 관리에 어떻게 적용될 수 있습니까?
        - 의사결정에 어떤 도움을 줄 수 있습니까?
        
        리포트는 명확하고 간결하게 작성하고, 중요한 발견이나 인사이트는 **볼드체**로 강조해주세요.
        """
        
        # AI 분석 UI 표시
        try:
            is_running = display_analysis_ui(
                prompt=prompt,
                button_label="AI 데이터 분석 실행",
                key_prefix="fwhm_xai_data",
                info_message="AI 분석을 실행하려면 버튼을 클릭하세요."
            )
            
            if is_running:
                with st.chat_message("assistant"):
                    message_placeholder = st.empty()
                    metadata_placeholder = st.empty()
                    with st.spinner("AI가 SHAP 데이터를 분석하고 있습니다..."):
                        generate_ai_analysis(
                            prompt=prompt,
                            key_prefix="fwhm_xai_data",
                            message_placeholder=message_placeholder,
                            metadata_placeholder=metadata_placeholder
                        )
        except Exception as e:
            st.error(f"AI 분석 생성 중 오류가 발생했습니다: {str(e)}")
            
        return True
    else:
        st.error(f"SHAP 값 데이터 파일을 찾을 수 없습니다. 경로: {shap_csv}")
        st.warning("먼저 모델을 훈련하고 SHAP 분석을 실행하여 SHAP 값을 생성해주세요.")
        
        # 파일 경로 확인
        st.info("파일 경로 정보:")
        st.code(f"SHAP CSV 파일 절대 경로: {os.path.abspath(shap_csv)}")
        
        # 다른 CSV 파일 찾기
        other_csv_files = glob.glob(os.path.join(PLOTS_DIR, "*.csv"))
        if other_csv_files:
            st.info(f"{PLOTS_DIR} 폴더에서 다음 CSV 파일을 찾았습니다:")
            for f in other_csv_files:
                st.code(f"- {os.path.basename(f)}")
        else:
            st.warning(f"{PLOTS_DIR} 폴더에 CSV 파일이 없습니다.")
        
        return False

if __name__ == "__main__":
    show_fwhm_xai_visualization() 