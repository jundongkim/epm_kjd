import os
import time
import json
import datetime
import numpy as np
import pandas as pd
from glob import glob
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from concurrent.futures import ThreadPoolExecutor
import torch
import xgboost as xgb # XGBoost 임포트 추가
from components.ai_utils import (
    init_session_state,
    display_analysis_ui,
    generate_ai_analysis,
    generate_cache_key
)
from utils.style import ECOPRO_COLORS

def init_simulation_session_state():
    """시뮬레이션 세션 상태 초기화"""
    # 랜덤 레코드 선택 상태 초기화
    st.session_state["new_record_selected"] = False

def on_change_input_values():
    """입력 필드 값 수정 시 session_state 초기화"""
    # 현재 시뮬레이션 모드 실행 버튼 상태 초기화
    CURRENT_SIM_MODE = st.session_state["current_sim_mode"]
    run_button_state_key = f"{CURRENT_SIM_MODE}_button_clicked"
    st.session_state[run_button_state_key] = False

    # `물질 혼합 예측` 모드에서 실제 Target_F 값 출력 필요 여부 초기화
    if CURRENT_SIM_MODE == "물질 혼합 예측":
        st.session_state["actual_target_f_needed"] = False

def show_simulation(df, model):
    """시뮬레이션 탭 표시"""
    # 세션 상태 초기화
    init_session_state(key_prefix="simulation")
    # 반가폭 시뮬레이션 관련 세션 상태 초기화
    # init_simulation_session_state()

    # 시뮬레이션 모드 변경 시 분석 상태 초기화를 위한 세션 변수
    if "prev_sim_mode" not in st.session_state:
        st.session_state.prev_sim_mode = None

    # 선택된 데이터셋 확인
    if 'selected_fwhm_dataset' in st.session_state:
        selected_dataset = st.session_state.selected_fwhm_dataset
    else:
        selected_dataset = "F28"  # 기본값

    st.header(f"모델 시뮬레이션 (데이터셋: {selected_dataset})")

    # MPS 사용 가능 여부 확인
    device = get_device()
    if device.type == "mps":
        st.success("✅ Apple M1 GPU(MPS)를 사용할 수 있습니다.")
    else:
        st.warning("⚠️ MPS를 사용할 수 없어 CPU로 실행됩니다.")
        if not torch.backends.mps.is_built():
            st.error("❌ PyTorch가 MPS를 지원하도록 빌드되지 않았습니다.")
        elif not torch.backends.mps.is_available():
            st.error("❌ MPS 장치를 찾을 수 없습니다.")

    if model is None:
        st.warning("모델 파일이 없습니다. 먼저 fwhm.py를 실행하여 모델을 학습하세요.")
        return

    # 시뮬레이션 모드 선택
    sim_mode = st.radio("시뮬레이션 모드 선택", ["물질 혼합 예측", "최적 혼합 비율 찾기", "최적 Qcp 변수 찾기"], horizontal=True)

    # 모드 변경 감지 (분석 캐시 초기화)
    if "prev_sim_mode" in st.session_state and st.session_state.prev_sim_mode != sim_mode:
        # 분석 관련 세션 상태 초기화
        if "prediction_analysis_info" in st.session_state:
            del st.session_state.prediction_analysis_info
        if "opt_analysis_info" in st.session_state:
            del st.session_state.opt_analysis_info
        if "qcp_opt_analysis_info" in st.session_state:
            del st.session_state.qcp_opt_analysis_info

        # 버튼 클릭 상태 초기화
        if "predict_button_clicked" in st.session_state:
            del st.session_state.predict_button_clicked
        if "opt_button_clicked" in st.session_state:
            del st.session_state.opt_button_clicked
        if "qcp_opt_button_clicked" in st.session_state:
            del st.session_state.qcp_opt_button_clicked

    # 현재 모드 저장
    st.session_state.prev_sim_mode = sim_mode

    # 변수 데이터 준비 - 컬럼 이름 형식을 고려해서 딕셔너리 구성
    li_vars = {}
    pre_l_vars = {}
    pre_s_vars = {}
    qcp_vars = {}

    # Li 변수 (Li1, Li2, ..., Li_1, Li_2, ... 형식 모두 처리)
    for col in df.columns:
        # Li 변수 처리
        if col.startswith('Li'):
            if '_' in col:  # Li_1_A, Li_1 형식
                if col.count('_') >= 2:  # Li_1_A 형식 (ABCD 변수)
                    li_vars[col] = df[col].values
                else:  # Li_1 형식 (모델 특성)
                    base_name = col  # 예: Li_1
                    li_vars[base_name] = df[col].values
            else:  # Li1, Li1_A 형식
                if any(suffix in col for suffix in ['_A', '_B', '_C', '_D']):  # Li1_A 형식
                    li_vars[col] = df[col].values
                else:  # Li1 형식 (모델 특성)
                    base_name = col  # 예: Li1
                    li_vars[base_name] = df[col].values

        # Pre_L 변수 처리
        elif col.startswith('Pre_L'):
            if '_' in col:
                if col.count('_') >= 2:  # Pre_L_1_A 또는 Pre_L1_A 형식
                    pre_l_vars[col] = df[col].values
                else:  # Pre_L_1 형식
                    base_name = col
                    pre_l_vars[base_name] = df[col].values
            else:  # Pre_L1 형식
                base_name = col
                pre_l_vars[base_name] = df[col].values

        # Pre_S 변수 처리
        elif col.startswith('Pre_S'):
            if '_' in col:
                if col.count('_') >= 2:  # Pre_S_1_A 또는 Pre_S1_A 형식
                    pre_s_vars[col] = df[col].values
                else:  # Pre_S_1 형식
                    base_name = col
                    pre_s_vars[base_name] = df[col].values
            else:  # Pre_S1 형식
                base_name = col
                pre_s_vars[base_name] = df[col].values

        # Qcp 변수 처리
        elif col.startswith('Qcp'):
            if '_' in col:  # Qcp_1 형식
                # 새 형식으로 변환 (Qcp_1 -> Qcp1)
                new_name = f"Qcp{col.split('_')[1]}"
                qcp_vars[new_name] = df[col].values
            else:  # Qcp1 형식
                qcp_vars[col] = df[col].values

    # 선택된 모드에 따라 함수 호출
    if sim_mode == "물질 혼합 예측":
        st.session_state["current_sim_mode"] = "물질 혼합 예측"
        show_mixture_prediction(df, model, li_vars, pre_l_vars, pre_s_vars, qcp_vars)
    elif sim_mode == "최적 혼합 비율 찾기":
        st.session_state["current_sim_mode"] = "최적 혼합 비율 찾기"
        show_optimal_ratio_search(df, model, li_vars, pre_l_vars, pre_s_vars, qcp_vars)
    elif sim_mode == "최적 Qcp 변수 찾기":
        st.session_state["current_sim_mode"] = "최적 Qcp 변수 찾기"
        show_optimal_qcp_search(df, model, li_vars, pre_l_vars, pre_s_vars, qcp_vars)

def show_mixture_prediction(df, model, li_vars, pre_l_vars, pre_s_vars, qcp_vars):
    """물질 혼합 예측 UI 표시"""
    CURRENT_SIM_MODE = st.session_state["current_sim_mode"]
    run_button_state_key = f"{CURRENT_SIM_MODE}_button_clicked"

    # 페이지 초기화 시 분석 세션 상태 초기화
    if "reset_prediction_state" not in st.session_state:
        st.session_state.reset_prediction_state = True
        if "prediction_analysis_info" in st.session_state:
            del st.session_state.prediction_analysis_info
        if "li_vars_summary" in st.session_state:
            del st.session_state.li_vars_summary
        if "pre_l_vars_summary" in st.session_state:
            del st.session_state.pre_l_vars_summary
        if "pre_s_vars_summary" in st.session_state:
            del st.session_state.pre_s_vars_summary

    # 예측 버튼 클릭 상태 초기화
    if run_button_state_key not in st.session_state:
        st.session_state[run_button_state_key] = False

    st.subheader("모든 변수 입력 및 예측")
    st.write("아래 변수들의 값을 입력하고 각 종류별 비율을 설정하여 Target_F를 예측해보세요.")

    # 랜덤화 설정
    st.subheader("입력값 랜덤화 설정")
    rand_cols = st.columns([2, 1])
    with rand_cols[0]:
        st.session_state.rand_dist = st.radio(
            "랜덤화 분포 선택",
            ["균일 분포 (Uniform)", "정규 분포 (Normal)"],
            horizontal=True
        )

    # 고정 변수 입력 UI (최적화 대상이 아닌 변수)
    st.subheader("고정 변수 입력")

    # 원본 데이터 레코드 1개 로드
    select_random_record_clicked = st.button("원본 데이터에서 무작위 행 선택")

    if select_random_record_clicked:
        selected_record = get_random_record(df)
        # 원본 레코드 로드 상태 업데이트
        st.session_state["new_record_selected"] = True
        # 실제 Target_F 값 출력 필요 여부 초기화
        st.session_state["actual_target_f_needed"] = True
        # 예측 버튼 클릭 상태 초기화
        st.session_state[run_button_state_key] = False
    elif "simulation_selected_record" in st.session_state:
        selected_record = st.session_state["simulation_selected_record"]
        # 실제 Target_F 값 출력 필요 여부 초기화
        # st.session_state["actual_target_f_needed"] = False
    else:
        # 첫 진입 시 원본 레코드 1개 랜덤 선택
        selected_record = get_random_record(df)
        # 실제 Target_F 값 출력 필요 여부 초기화
        st.session_state["actual_target_f_needed"] = True

    # 고정된 물질 유형별 비율
    li_main_ratio = 0.33
    pre_l_main_ratio = 0.33
    pre_s_main_ratio = 0.34

    # 변수 그룹별 입력 UI
    var_tabs = st.tabs(["Li 변수", "Pre_L 변수", "Pre_S 변수", "Qcp 변수"]) # Qcp Tab added

    # 각 그룹별 가중 평균값을 저장할 딕셔너리
    all_input_values = {}  # 모든 개별 변수 값
    abcd_ratios = {  # 각 물질 유형별 A/B/C/D 비율
        "Li": [0.25, 0.25, 0.25, 0.25],
        "Pre_L": [0.25, 0.25, 0.25, 0.25],
        "Pre_S": [0.25, 0.25, 0.25, 0.25]
    }

    # Li 변수 입력
    with var_tabs[0]:
        li_values, _, li_abcd_ratios = show_variable_inputs(selected_record, "Li")
        all_input_values.update(li_values)
        if li_abcd_ratios:
            abcd_ratios["Li"] = li_abcd_ratios

    # Pre_L 변수 입력
    with var_tabs[1]:
        pre_l_values, _, pre_l_abcd_ratios = show_variable_inputs(selected_record, "Pre_L")
        all_input_values.update(pre_l_values)
        if pre_l_abcd_ratios:
            abcd_ratios["Pre_L"] = pre_l_abcd_ratios

    # Pre_S 변수 입력
    with var_tabs[2]:
        pre_s_values, _, pre_s_abcd_ratios = show_variable_inputs(selected_record, "Pre_S")
        all_input_values.update(pre_s_values)
        if pre_s_abcd_ratios:
            abcd_ratios["Pre_S"] = pre_s_abcd_ratios

    # Qcp 변수 입력 (A/B/C/D 비율 없음)
    with var_tabs[3]:
        qcp_values = show_simple_variable_inputs(selected_record, "Qcp") # Use new function for Qcp
        all_input_values.update(qcp_values)

    # 원본 레코드 1개 랜덤 로드 상태 초기화
    st.session_state["new_record_selected"] = False

    # 예측 버튼
    pred_button_clicked = st.button("Target_F 예측하기")

    # 버튼 클릭 상태 저장
    if pred_button_clicked:
        st.session_state[run_button_state_key] = True

    # 예측 시작
    if st.session_state[run_button_state_key]:
        # 분석 상태 초기화 (새로운 예측을 위해)
        if "prediction_analysis_info" in st.session_state:
            del st.session_state.prediction_analysis_info
        if "li_vars_summary" in st.session_state:
            del st.session_state.li_vars_summary
        if "pre_l_vars_summary" in st.session_state:
            del st.session_state.pre_l_vars_summary
        if "pre_s_vars_summary" in st.session_state:
            del st.session_state.pre_s_vars_summary

        # 예측 함수에 현재 비율 전달
        material_ratios = [li_main_ratio, pre_l_main_ratio, pre_s_main_ratio]

        # 예측 함수 호출
        prediction = predict_with_ratios(
            model,
            {k: v for k, v in all_input_values.items() if k.startswith('Li')},
            {k: v for k, v in all_input_values.items() if k.startswith('Pre_L')},
            {k: v for k, v in all_input_values.items() if k.startswith('Pre_S')},
            {k: v for k, v in all_input_values.items() if k.startswith('Qcp')}, # Pass Qcp values
            material_ratios,
            abcd_ratios
        )

        if prediction is not None:
            # 결과 표시
            st.success(f"### 예측된 Target_F 값: {prediction:.6f}")

            # 입력값 테이블 표시
            st.subheader("입력 변수 값")
            if st.session_state["actual_target_f_needed"]:
                show_input_tables(selected_record.to_dict(), li_main_ratio, pre_l_main_ratio, pre_s_main_ratio, qcp_values)
            else:
                show_input_tables(all_input_values, li_main_ratio, pre_l_main_ratio, pre_s_main_ratio, qcp_values)

            # 예측 결과 게이지 차트
            show_prediction_gauge(df, prediction, st.session_state["actual_target_f_needed"])

            # AI 분석 요약
            st.subheader("🤖 iDSB AI 예측 분석 요약")

            # 결과 데이터를 세션 상태에 저장 (페이지 리로드 시 유지)
            if "prediction_analysis_info" not in st.session_state:
                # 분석 정보 수집
                analysis_info = {
                    "예측된_Target_F": round(float(prediction), 6),
                    "물질_유형별_비율": {
                        "Li": li_main_ratio,
                        "Pre_L": pre_l_main_ratio,
                        "Pre_S": pre_s_main_ratio
                    },
                    "물질별_ABCD_비율": {
                        "Li": [round(r, 4) for r in abcd_ratios["Li"]],
                        "Pre_L": [round(r, 4) for r in abcd_ratios["Pre_L"]],
                        "Pre_S": [round(r, 4) for r in abcd_ratios["Pre_S"]]
                    },
                    "데이터_범위": {
                        "Target_F_최소값": round(float(df['Target_F'].min()), 6),
                        "Target_F_최대값": round(float(df['Target_F'].max()), 6),
                        "Target_F_평균값": round(float(df['Target_F'].mean()), 6)
                    }
                }

                # 입력 변수 요약 정보 추가
                li_vars_summary = {f"Li_{i}": round(float(all_input_values.get(f"Li_{i}", 0)), 4) for i in range(1, 29) if f"Li_{i}" in all_input_values}
                pre_l_vars_summary = {f"Pre_L{i}": round(float(all_input_values.get(f"Pre_L{i}", 0)), 4) for i in range(32) if f"Pre_L{i}" in all_input_values}
                pre_s_vars_summary = {f"Pre_S{i}": round(float(all_input_values.get(f"Pre_S{i}", 0)), 4) for i in range(32) if f"Pre_S{i}" in all_input_values}
                qcp_vars_summary = {f"Qcp{i}": round(float(all_input_values.get(f"Qcp{i}", 0)), 4) for i in range(1, 31) if f"Qcp{i}" in all_input_values} # Qcp summary

                # 세션 상태에 저장
                st.session_state.prediction_analysis_info = analysis_info
                st.session_state.li_vars_summary = li_vars_summary
                st.session_state.pre_l_vars_summary = pre_l_vars_summary
                st.session_state.pre_s_vars_summary = pre_s_vars_summary
                st.session_state.qcp_vars_summary = qcp_vars_summary # Save Qcp summary

            # 저장된 분석 정보 사용
            analysis_info = st.session_state.prediction_analysis_info
            li_vars_summary = st.session_state.li_vars_summary
            pre_l_vars_summary = st.session_state.pre_l_vars_summary
            pre_s_vars_summary = st.session_state.pre_s_vars_summary
            qcp_vars_summary = st.session_state.qcp_vars_summary # Load Qcp summary

            # 프롬프트 생성
            prompt = f"""
            아래 예측 정보를 바탕으로 전문적인 분석 리포트를 작성해주세요.
            리포트는 마크다운 형식으로 작성하며, 각 섹션을 명확히 구분해주세요.

            ## 예측 결과 정보
            {json.dumps(analysis_info, indent=2, ensure_ascii=False)}

            ## 주요 입력 변수 (일부)
            - Li 변수: {json.dumps(list(li_vars_summary.items())[:5], ensure_ascii=False)}
            - Pre_L 변수: {json.dumps(list(pre_l_vars_summary.items())[:5], ensure_ascii=False)}
            - Pre_S 변수: {json.dumps(list(pre_s_vars_summary.items())[:5], ensure_ascii=False)}
            - Qcp 변수: {json.dumps(list(qcp_vars_summary.items())[:5], ensure_ascii=False)} # Add Qcp summary to prompt

            다음 구조로 분석 리포트를 작성해주세요:

            1. 예측 결과 요약 (예측된 Target_F 값과 데이터 범위 내 위치)
            2. 물질 비율 분석 (Li, Pre_L, Pre_S 및 A/B/C/D 비율의 영향)
            3. 예측 결과 해석 (예측값의 의미와 중요성)
            4. 개선 제안 (더 좋은 결과를 위한 비율 조정 제안)
            5. 추가 실험 제안 (추가로 실험해볼 수 있는 조건)

            각 섹션은 ### 헤더로 구분하고, 중요한 수치나 인사이트는 **볼드체**로 강조해주세요.
            """

            # 캐시 키 생성
            cache_key = generate_cache_key(
                prompt=prompt,
                model=st.session_state.selected_model,
                temperature=st.session_state.temperature
            )
            cache_state_key = "simulation_prediction_cache"

            # 캐싱된 분석 결과 확인
            if cache_state_key not in st.session_state:
                st.session_state[cache_state_key] = {}

            # 모델 정보 및 분석 버튼
            col1, col2 = st.columns([3, 1])
            with col1:
                model_info = f"사용 모델: {st.session_state.selected_model} | 온도: {st.session_state.temperature}"
                st.caption(model_info)

            with col2:
                if "pred_analysis_running" not in st.session_state:
                    st.session_state.pred_analysis_running = False

                # 분석 버튼 (세션 상태 변수를 직접 변경하는 콜백 사용)
                if st.button("예측 분석 시작", key="pred_analysis_button", use_container_width=True):
                    st.session_state.pred_analysis_running = True
                    # 캐시 무효화하여 새로운 분석 실행
                    if cache_key in st.session_state[cache_state_key]:
                        del st.session_state[cache_state_key][cache_key]

            # 분석 결과 표시
            if cache_key in st.session_state[cache_state_key]:
                # 캐시된 결과 표시
                cached_response = st.session_state[cache_state_key][cache_key]
                with st.chat_message("assistant"):
                    st.markdown(cached_response["response"])
                    if cached_response.get("metadata"):
                        metadata_text = "\n\n---\n**처리 정보**\n```json\n"
                        metadata_text += json.dumps(cached_response["metadata"], indent=2, ensure_ascii=False)
                        metadata_text += "\n```"
                        st.markdown(metadata_text)

                # 분석 실행 플래그 초기화
                st.session_state.pred_analysis_running = False

            elif st.session_state.pred_analysis_running:
                # 분석 실행 중인 경우
                with st.chat_message("assistant"):
                    message_placeholder = st.empty()
                    metadata_placeholder = st.empty()

                    with st.spinner("AI가 예측 결과를 분석하고 있습니다..."):
                        try:
                            # AI 분석 실행
                            response, full_response, metadata = generate_ai_analysis(
                                prompt=prompt,
                                key_prefix="simulation_prediction",
                                message_placeholder=message_placeholder,
                                metadata_placeholder=metadata_placeholder
                            )

                            # 결과 캐싱
                            st.session_state[cache_state_key][cache_key] = {
                                "response": full_response,
                                "metadata": metadata
                            }
                        except Exception as e:
                            st.error(f"AI 예측 분석 생성 중 오류가 발생했습니다: {str(e)}")

                        # 분석 실행 플래그 초기화
                        st.session_state.pred_analysis_running = False

            else:
                # 분석 전 안내 메시지
                st.info("AI 예측 분석을 실행하려면 '예측 분석 시작' 버튼을 클릭하세요.")
        else:
            st.error("예측 중 오류가 발생했습니다.")

def show_optimal_ratio_search(df, model, li_vars, pre_l_vars, pre_s_vars, qcp_vars):
    """최적 혼합 비율 찾기 UI 표시"""
    CURRENT_SIM_MODE = st.session_state["current_sim_mode"]
    run_button_state_key = f"{CURRENT_SIM_MODE}_button_clicked"

    # 페이지 초기화 시 분석 세션 상태 초기화
    if "reset_optimization_state" not in st.session_state:
        st.session_state.reset_optimization_state = True
        if "opt_analysis_info" in st.session_state:
            del st.session_state.opt_analysis_info

    # 최적화 버튼 클릭 상태 초기화
    if run_button_state_key not in st.session_state:
        st.session_state[run_button_state_key] = False

    st.subheader("최적 물질 혼합 비율 찾기")
    st.write("각 특성 유형의 값을 입력하고 최적의 혼합 비율을 찾아보세요.")

    # 타겟 최적화 방향 선택
    opt_direction = st.radio("최적화 방향", ["Target_F 최대화", "Target_F 최소화", "Target_F 목표값에 근접"], horizontal=True)

    # 목표값 입력 UI (목표값 최적화 선택 시)
    target_value = None
    if opt_direction == "Target_F 목표값에 근접":
        # 데이터셋의 Target_F 최소/최대값 기준으로 슬라이더 범위 설정
        min_target = float(df['Target_F'].min())
        max_target = float(df['Target_F'].max())
        mean_target = float(df['Target_F'].mean())

        target_value = st.number_input(
            "목표 Target_F 값",
            min_value=min_target,
            max_value=max_target,
            value=mean_target,
            format="%.6f",
            help="최적화 알고리즘이 이 값에 가장 근접한 혼합 비율을 찾습니다."
        )
        st.info(f"설정된 목표값: {target_value:.6f} (데이터셋 범위: {min_target:.6f} ~ {max_target:.6f})")

    # 최적화 설정
    st.subheader("최적화 설정")

    # 설정 컬럼
    col1, col2, col3 = st.columns(3)

    with col1:
        precision = st.select_slider(
            "탐색 정밀도",
            options=[0.1, 0.01, 0.001],
            value=0.01,
            help="낮을수록 더 정밀하게 탐색하지만 시간이 오래 걸립니다."
        )

    with col2:
        max_iterations = st.slider(
            "최대 반복 횟수",
            min_value=10,
            max_value=500,
            value=100,
            step=10,
            help="최적화 알고리즘의 최대 반복 횟수"
        )

    with col3:
        tolerance = st.select_slider(
            "수렴 허용 오차",
            options=[1e-4, 1e-5, 1e-6, 1e-7],
            value=1e-6,
            help="이전 최적값과의 차이가 이 값보다 작으면 조기 종료"
        )

    # 고정 변수 입력 UI (최적화 대상이 아닌 변수)
    st.subheader("고정 변수 입력")

    # 원본 데이터 레코드 1개 로드
    select_random_record_clicked = st.button("원본 데이터에서 무작위 행 선택", key="select_random_record_button")
    if select_random_record_clicked:
        selected_record = get_random_record(df)
        # 랜덤 레코드 선택 상태 업데이트
        st.session_state["new_record_selected"] = True
        # 최적화 버튼 클릭 상태 초기화
        st.session_state[run_button_state_key] = False
    elif "simulation_selected_record" in st.session_state:
        selected_record = st.session_state["simulation_selected_record"]
    else:
        selected_record = get_random_record(df)

    # 물질 유형 비율은 고정값 사용
    st.info("물질 유형별 비율은 고정값(Li=0.33, Pre_L=0.33, Pre_S=0.34)으로 사용됩니다.")
    material_ratio_candidates = [0.33, 0.33, 0.34]  # Li, Pre_L, Pre_S (고정값)

    # 변수 입력 UI
    var_tabs = st.tabs(["Li 변수", "Pre_L 변수", "Pre_S 변수"])

    # 각 그룹별 가중 평균값을 저장할 딕셔너리
    all_values = {}
    abcd_ratios = {
        "Li": [0.25, 0.25, 0.25, 0.25],
        "Pre_L": [0.25, 0.25, 0.25, 0.25],
        "Pre_S": [0.25, 0.25, 0.25, 0.25]
    }

    # Li 변수 입력
    with var_tabs[0]:
        li_values, _, li_abcd_ratios = show_variable_inputs(selected_record, "Li")
        all_values.update(li_values)
        if li_abcd_ratios:
            abcd_ratios["Li"] = li_abcd_ratios

    # Pre_L 변수 입력
    with var_tabs[1]:
        pre_l_values, _, pre_l_abcd_ratios = show_variable_inputs(selected_record, "Pre_L")
        all_values.update(pre_l_values)
        if pre_l_abcd_ratios:
            abcd_ratios["Pre_L"] = pre_l_abcd_ratios

    # Pre_S 변수 입력
    with var_tabs[2]:
        pre_s_values, _, pre_s_abcd_ratios = show_variable_inputs(selected_record, "Pre_S")
        all_values.update(pre_s_values)
        if pre_s_abcd_ratios:
            abcd_ratios["Pre_S"] = pre_s_abcd_ratios

    # Qcp 변수 입력 (최적화 대상 아님 - 고정값)
    with st.expander("Qcp 변수 입력", expanded=True): # Use expander as it's not ratio-based
        qcp_values = show_simple_variable_inputs(selected_record, "Qcp")
        all_values.update(qcp_values)

    # 원본 레코드 1개 랜덤 로드 상태 초기화
    st.session_state["new_record_selected"] = False

    # 최적화 시작 버튼
    mix_opt_button_clicked = st.button("최적 혼합 비율 찾기", use_container_width=True)

    # 버튼 클릭 상태 저장
    if mix_opt_button_clicked:
        st.session_state[run_button_state_key] = True

    # 최적화 시작
    if st.session_state[run_button_state_key]:
        # 분석 상태 초기화 (새로운 최적화를 위해)
        if "opt_analysis_info" in st.session_state:
            del st.session_state.opt_analysis_info

        # 그리디 서치로 최적화 수행
        best_abcd_ratios, best_prediction, optimization_time = greedy_search(
            model,
            {k: v for k, v in all_values.items() if k.startswith('Li')},
            {k: v for k, v in all_values.items() if k.startswith('Pre_L')},
            {k: v for k, v in all_values.items() if k.startswith('Pre_S')},
            {k: v for k, v in all_values.items() if k.startswith('Qcp')}, # Pass fixed Qcp values
            material_ratio_candidates,
            opt_direction,
            abcd_ratios,  # UI에서 설정한 초기 비율 전달
            target_value,
            precision=precision,
            tolerance=tolerance,
            max_iterations=max_iterations
        )

        if best_prediction is not None:
            # 최적화 결과 표시
            st.success(f"최적화 완료! (소요 시간: {optimization_time:.2f}초)")
            show_optimization_visualization(material_ratio_candidates, best_prediction,
                                         opt_direction, best_abcd_ratios, target_value)
        else:
            st.error("최적화 중 오류가 발생했습니다.")

def show_optimal_qcp_search(df, model, li_vars, pre_l_vars, pre_s_vars, qcp_vars):
    """최적 Qcp 변수 찾기 UI 표시"""
    CURRENT_SIM_MODE = st.session_state["current_sim_mode"]
    run_button_state_key = f"{CURRENT_SIM_MODE}_button_clicked"

    # 페이지 초기화 시 분석 세션 상태 초기화
    if "reset_qcp_optimization_state" not in st.session_state:
        st.session_state.reset_qcp_optimization_state = True
        if "qcp_opt_analysis_info" in st.session_state:
            del st.session_state.qcp_opt_analysis_info

    # 최적화 버튼 클릭 상태 초기화
    if run_button_state_key not in st.session_state:
        st.session_state[run_button_state_key] = False

    st.subheader("최적 Qcp 변수 찾기")
    st.write("Li, Pre_L, Pre_S 물질 비율은 고정으로 두고, Qcp 변수만 최적화합니다.")

    # 타겟 최적화 방향 선택
    opt_direction = st.radio("최적화 방향", ["Target_F 최대화", "Target_F 최소화", "Target_F 목표값에 근접"],
                            horizontal=True, key="qcp_opt_direction")

    # 목표값 입력 UI (목표값 최적화 선택 시)
    target_value = None
    if opt_direction == "Target_F 목표값에 근접":
        # 데이터셋의 Target_F 최소/최대값 기준으로 슬라이더 범위 설정
        min_target = float(df['Target_F'].min())
        max_target = float(df['Target_F'].max())
        mean_target = float(df['Target_F'].mean())

        target_value = st.number_input(
            "목표 Target_F 값",
            min_value=min_target,
            max_value=max_target,
            value=mean_target,
            format="%.6f",
            help="최적화 알고리즘이 이 값에 가장 근접한 Qcp 변수 값을 찾습니다.",
            key="qcp_target_value"
        )
        st.info(f"설정된 목표값: {target_value:.6f} (데이터셋 범위: {min_target:.6f} ~ {max_target:.6f})")

    # 최적화 설정
    st.subheader("최적화 설정")

    # 설정 컬럼
    col1, col2, col3 = st.columns(3)

    with col1:
        precision = st.select_slider(
            "탐색 정밀도",
            options=[0.1, 0.01, 0.001],
            value=0.01,
            help="낮을수록 더 정밀하게 탐색하지만 시간이 오래 걸립니다.",
            key="qcp_precision"
        )

    with col2:
        max_iterations = st.slider(
            "최대 반복 횟수",
            min_value=10,
            max_value=500,
            value=100,
            step=10,
            help="최적화 알고리즘의 최대 반복 횟수",
            key="qcp_max_iterations"
        )

    with col3:
        tolerance = st.select_slider(
            "수렴 허용 오차",
            options=[1e-4, 1e-5, 1e-6, 1e-7],
            value=1e-6,
            help="이전 최적값과의 차이가 이 값보다 작으면 조기 종료",
            key="qcp_tolerance"
        )

    # 최적화할 Qcp 변수 선택
    st.subheader("최적화할 Qcp 변수 선택")

    # Qcp 변수 목록 (실제 데이터프레임에서 "Qcp"로 시작하는 컬럼 찾기)
    qcp_var_names = [col for col in df.columns if col.startswith('Qcp')]

    # 최적화할 변수와 범위 선택
    qcp_to_optimize = {}

    with st.expander("변수 선택 및 범위 설정", expanded=True):
        # 최적화할 변수 선택
        selected_qcp_vars = st.multiselect(
            "최적화할 Qcp 변수 선택 (복수 선택 가능)",
            options=qcp_var_names,
            default=qcp_var_names[:5]  # 기본적으로 처음 5개 선택
        )

        if not selected_qcp_vars:
            st.warning("최적화할 Qcp 변수를 하나 이상 선택해주세요.")

        # 선택된 변수별 범위 설정
        for var_name in selected_qcp_vars:
            st.write(f"#### {var_name} 최적화 범위")

            # 데이터프레임에서 해당 변수의 통계 가져오기
            try:
                if var_name in df.columns:
                    min_val = float(df[var_name].min())
                    max_val = float(df[var_name].max())
                    mean_val = float(df[var_name].mean())
                else:
                    # 기존 형식이 있는지 확인 (Qcp_1 등)
                    old_var_name = f"Qcp_{var_name[3:]}"  # Qcp1 -> Qcp_1
                    if old_var_name in df.columns:
                        min_val = float(df[old_var_name].min())
                        max_val = float(df[old_var_name].max())
                        mean_val = float(df[old_var_name].mean())
                    else:
                        # qcp_vars에서 해당 변수의 통계값을 계산
                        var_values = qcp_vars.get(var_name, None)
                        if var_values is not None and hasattr(var_values, '__len__') and len(var_values) > 0:
                            min_val = float(np.min(var_values))
                            max_val = float(np.max(var_values))
                            mean_val = float(np.mean(var_values))
                        else:
                            min_val, max_val, mean_val = 0.0, 1.0, 0.5
            except:
                min_val, max_val, mean_val = 0.0, 1.0, 0.5

            # 최소/최대 범위 설정
            col1, col2 = st.columns(2)
            with col1:
                min_range = st.number_input(
                    f"{var_name} 최소값",
                    value=min_val,
                    format="%.4f",
                    key=f"min_{var_name}"
                )
            with col2:
                max_range = st.number_input(
                    f"{var_name} 최대값",
                    value=max_val,
                    format="%.4f",
                    key=f"max_{var_name}"
                )

            # 범위 오류 확인
            if min_range >= max_range:
                st.error(f"{var_name}의 최소값은 최대값보다 작아야 합니다.")
                continue

            # 최적화 범위 저장
            qcp_to_optimize[var_name] = {
                "min": min_range,
                "max": max_range,
                "current": mean_val  # 초기값
            }

    # 고정 변수 입력 UI (최적화 대상이 아닌 변수)
    st.subheader("고정 변수 입력")

    # 원본 데이터 레코드 1개 로드
    select_random_record_clicked = st.button("원본 데이터에서 무작위 행 선택", key="select_random_record_button")
    if select_random_record_clicked:
        selected_record = get_random_record(df)
        # 랜덤 레코드 선택 상태 업데이트
        st.session_state["new_record_selected"] = True
        # 최적화 버튼 클릭 상태 초기화
        st.session_state[run_button_state_key] = False
    elif "simulation_selected_record" in st.session_state:
        selected_record = st.session_state["simulation_selected_record"]
    else:
        selected_record = get_random_record(df)

    # Li, Pre_L, Pre_S 변수 입력 (ABCD 비율)
    var_tabs = st.tabs(["Li 변수", "Pre_L 변수", "Pre_S 변수"])

    # 각 그룹별 가중 평균값을 저장할 딕셔너리
    all_values = {}
    abcd_ratios = {
        "Li": [0.25, 0.25, 0.25, 0.25],
        "Pre_L": [0.25, 0.25, 0.25, 0.25],
        "Pre_S": [0.25, 0.25, 0.25, 0.25]
    }

    # Li 변수 입력
    with var_tabs[0]:
        li_values, _, li_abcd_ratios = show_variable_inputs(selected_record, "Li")
        all_values.update(li_values)
        if li_abcd_ratios:
            abcd_ratios["Li"] = li_abcd_ratios

    # Pre_L 변수 입력
    with var_tabs[1]:
        pre_l_values, _, pre_l_abcd_ratios = show_variable_inputs(selected_record, "Pre_L")
        all_values.update(pre_l_values)
        if pre_l_abcd_ratios:
            abcd_ratios["Pre_L"] = pre_l_abcd_ratios

    # Pre_S 변수 입력
    with var_tabs[2]:
        pre_s_values, _, pre_s_abcd_ratios = show_variable_inputs(selected_record, "Pre_S")
        all_values.update(pre_s_values)
        if pre_s_abcd_ratios:
            abcd_ratios["Pre_S"] = pre_s_abcd_ratios

    # 고정 Qcp 변수 입력 (최적화 대상이 아닌 Qcp 변수)
    fixed_qcp_vars = [var for var in qcp_var_names if var not in selected_qcp_vars]
    if fixed_qcp_vars:
        with st.expander("고정 Qcp 변수 입력", expanded=True):
            fixed_qcp_values = {}
            for var_name in fixed_qcp_vars:
                # 현재 값 가져오기
                current_val = st.session_state["simulation_selected_record"].get(var_name, 0.0)
                # NumPy 배열인 경우 평균값 사용
                if hasattr(current_val, '__len__') and len(current_val) > 0:
                    current_val = float(np.mean(current_val))
                else:
                    current_val = float(current_val)

                fixed_qcp_values[var_name] = st.number_input(
                    f"{var_name}",
                    value=current_val,
                    format="%.4f",
                    key=f"fixed_{var_name}"
                )
            all_values.update(fixed_qcp_values)

    # 원본 레코드 1개 랜덤 로드 상태 초기화
    st.session_state["new_record_selected"] = False

    # 물질 유형 비율은 고정값 사용
    material_ratio_candidates = [0.33, 0.33, 0.34]  # Li, Pre_L, Pre_S (고정값)

    # 최적화 시작 버튼
    qcp_opt_button_clicked = st.button("Qcp 변수 최적화 시작", use_container_width=True)

    # 버튼 클릭 상태 저장
    if qcp_opt_button_clicked:
        st.session_state[run_button_state_key] = True

    # 최적화 시작
    if st.session_state[run_button_state_key] and selected_qcp_vars:
        # 분석 상태 초기화 (새로운 최적화를 위해)
        if "qcp_opt_analysis_info" in st.session_state:
            del st.session_state.qcp_opt_analysis_info

        # 진행 상황 표시
        progress_container = st.container()
        with progress_container:
            st.markdown("### 최적화 진행 상황")
            progress_bar = st.progress(0, "Qcp 변수 최적화 진행 중...")
            status_text = st.empty()

            # 실시간 최적화 결과
            results_container = st.container()
            with results_container:
                result_text = st.empty()

            import time
            start_time = time.time()

            # 초기 예측
            initial_qcp_values = {k: v for k, v in all_values.items() if k.startswith('Qcp')}
            for var in selected_qcp_vars:
                if var not in initial_qcp_values:
                    # qcp_vars에서 가져온 값이 배열인 경우 처리
                    if var in qcp_to_optimize:
                        initial_qcp_values[var] = qcp_to_optimize[var]["current"]
                    else:
                        var_values = qcp_vars.get(var, None)
                        if var_values is not None and hasattr(var_values, '__len__') and len(var_values) > 0:
                            initial_qcp_values[var] = float(np.mean(var_values))
                        else:
                            initial_qcp_values[var] = 0.0

            # 최적화 결과 저장 변수
            best_qcp_values = initial_qcp_values.copy()

            # 초기 예측값 계산
            initial_prediction = predict_with_ratios(
                model,
                {k: v for k, v in all_values.items() if k.startswith('Li')},
                {k: v for k, v in all_values.items() if k.startswith('Pre_L')},
                {k: v for k, v in all_values.items() if k.startswith('Pre_S')},
                initial_qcp_values,
                material_ratio_candidates,
                abcd_ratios
            )

            best_prediction = initial_prediction

            # precision에 따른 탐색 단계 설정
            if precision == 0.1:
                steps = 10
            elif precision == 0.01:
                steps = 20
            else:  # precision == 0.001
                steps = 50

            total_iterations = max_iterations * len(selected_qcp_vars)
            current_iteration = 0

            # 최적화 시작
            for iteration in range(max_iterations):
                improved = False

                for var_idx, var_name in enumerate(selected_qcp_vars):
                    current_iteration += 1
                    progress = current_iteration / total_iterations
                    progress_bar.progress(progress, f"변수 {var_name} 최적화 중... ({iteration+1}/{max_iterations})")

                    # 현재 변수의 최소/최대 범위
                    min_val = qcp_to_optimize[var_name]["min"]
                    max_val = qcp_to_optimize[var_name]["max"]

                    # 탐색 단계 생성
                    step_size = (max_val - min_val) / steps
                    search_values = [min_val + i * step_size for i in range(steps + 1)]

                    # 각 후보값에 대한 예측
                    for test_value in search_values:
                        # 테스트할 값 설정
                        test_qcp_values = best_qcp_values.copy()
                        test_qcp_values[var_name] = test_value

                        # 예측 수행
                        prediction = predict_with_ratios(
                            model,
                            {k: v for k, v in all_values.items() if k.startswith('Li')},
                            {k: v for k, v in all_values.items() if k.startswith('Pre_L')},
                            {k: v for k, v in all_values.items() if k.startswith('Pre_S')},
                            test_qcp_values,
                            material_ratio_candidates,
                            abcd_ratios
                        )

                        if prediction is not None:
                            # 최적화 방향에 따른 개선 확인
                            is_better = False
                            if opt_direction == "Target_F 최대화":
                                is_better = prediction > best_prediction
                            elif opt_direction == "Target_F 최소화":
                                is_better = prediction < best_prediction
                            else:  # 목표값에 근접
                                current_diff = abs(prediction - target_value)
                                best_diff = abs(best_prediction - target_value)
                                is_better = current_diff < best_diff

                            # 개선되었으면 업데이트
                            if is_better:
                                best_prediction = prediction
                                best_qcp_values[var_name] = test_value
                                improved = True

                                # 상태 업데이트
                                status_text.info(f"개선됨! {var_name} = {test_value:.4f}, Target_F = {best_prediction:.6f}")

                    # 현재 최적 결과 표시
                    if opt_direction == "Target_F 목표값에 근접" and target_value is not None:
                        result_text.success(f"현재 최적값: Target_F = {best_prediction:.6f} (목표값과의 차이: {abs(best_prediction - target_value):.6f})")
                    else:
                        result_text.success(f"현재 최적값: Target_F = {best_prediction:.6f}")

                # 개선이 없으면 조기 종료
                if not improved:
                    status_text.info("더 이상 개선되지 않아 최적화를 종료합니다.")
                    break

            # 최적화 완료
            optimization_time = time.time() - start_time
            progress_bar.progress(1.0, "최적화 완료!")

            # 최적화 결과 표시
            st.success(f"Qcp 변수 최적화 완료! (소요 시간: {optimization_time:.2f}초)")

            # 결과 시각화
            st.subheader("최적화 결과")

            # 최적 Qcp 값 표시
            st.write("#### 최적 Qcp 변수 값")

            # 결과 테이블 데이터
            result_data = []
            for var_name in selected_qcp_vars:
                initial_value = initial_qcp_values.get(var_name, 0.0)
                optimized_value = best_qcp_values.get(var_name, 0.0)
                change = optimized_value - initial_value
                change_pct = (change / initial_value * 100) if initial_value != 0 else float('inf')

                result_data.append({
                    "변수": var_name,
                    "초기값": initial_value,
                    "최적값": optimized_value,
                    "변화량": change,
                    "변화율(%)": change_pct if change_pct != float('inf') else None
                })

            # 결과 테이블 표시
            result_df = pd.DataFrame(result_data)
            st.dataframe(
                result_df.style.format({
                    "초기값": "{:.4f}",
                    "최적값": "{:.4f}",
                    "변화량": "{:.4f}",
                    "변화율(%)": "{:.2f}%"
                }),
                use_container_width=True
            )

            # 결과 시각화 (막대 그래프)
            if len(selected_qcp_vars) > 0:
                st.write("#### 최적화 전후 비교")

                # 데이터 준비
                chart_data = []
                for var_name in selected_qcp_vars:
                    chart_data.append({
                        "변수": var_name,
                        "값": initial_qcp_values.get(var_name, 0.0),
                        "유형": "초기값"
                    })
                    chart_data.append({
                        "변수": var_name,
                        "값": best_qcp_values.get(var_name, 0.0),
                        "유형": "최적값"
                    })

                chart_df = pd.DataFrame(chart_data)

                # 차트 생성
                fig = px.bar(
                    chart_df,
                    x="변수",
                    y="값",
                    color="유형",
                    barmode="group",
                    title="Qcp 변수 최적화 전후 비교",
                    color_discrete_sequence=[ECOPRO_COLORS['light_blue'], ECOPRO_COLORS['orange']]
                )

                # 차트 스타일 업데이트
                fig.update_layout(
                    font=dict(color=ECOPRO_COLORS['text']),
                    title=dict(
                        text="Qcp 변수 최적화 전후 비교",
                        font=dict(color=ECOPRO_COLORS['dark_blue'], size=20)
                    )
                )

                st.plotly_chart(fig, use_container_width=True)

            # Target_F 결과 비교
            st.write("#### Target_F 결과 비교")

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric(
                    "초기 Target_F",
                    f"{initial_prediction:.6f}"
                )
            with col2:
                st.metric(
                    "최적화 후 Target_F",
                    f"{best_prediction:.6f}",
                    f"{best_prediction - initial_prediction:.6f}"
                )
            with col3:
                if opt_direction == "Target_F 목표값에 근접" and target_value is not None:
                    initial_diff = abs(initial_prediction - target_value)
                    final_diff = abs(best_prediction - target_value)
                    improvement = initial_diff - final_diff
                    st.metric(
                        "목표값과의 차이 개선",
                        f"{final_diff:.6f}",
                        f"{improvement:.6f}"
                    )
                else:
                    change_pct = ((best_prediction - initial_prediction) / initial_prediction * 100) if initial_prediction != 0 else float('inf')
                    if change_pct != float('inf'):
                        st.metric(
                            "변화율",
                            f"{change_pct:.2f}%"
                        )
            with col4:
                st.metric(
                    "Target 값 범위 대비 변화율",
                    f"{change_pct:.2f}%"
                )

            # 게이지 차트로 Target_F 시각화
            if opt_direction == "Target_F 목표값에 근접" and target_value is not None:
                st.write("#### 목표값 대비 결과")

                # 게이지 차트 생성
                fig = go.Figure()

                # 목표값 표시선
                fig.add_trace(go.Indicator(
                    mode="gauge+number",
                    value=best_prediction,
                    title={"text": "최적화된 Target_F"},
                    gauge={
                        "axis": {"range": [None, max(best_prediction*1.5, target_value*1.5)]},
                        "bar": {"color": ECOPRO_COLORS['orange']},
                        "steps": [
                            {"range": [0, min(best_prediction, target_value)*0.9], "color": "lightgray"},
                            {"range": [min(best_prediction, target_value)*0.9, max(best_prediction, target_value)*1.1], "color": "gray"}
                        ],
                        "threshold": {
                            "line": {"color": "red", "width": 4},
                            "thickness": 0.75,
                            "value": target_value
                        }
                    }
                ))

                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)

def get_random_record(df: pd.DataFrame) -> pd.Series:
    """랜덤 레코드 선택"""
    selected_dataset = st.session_state["selected_fwhm_dataset"]

    if "simulation_test_data" not in st.session_state or st.session_state["simulation_test_data"] is None:
        try:
            testset_f28 = pd.read_csv(f"FWHM/test_data/test_data_F28.csv")
            testset_f29 = pd.read_csv(f"FWHM/test_data/test_data_F29.csv")
            testset_f30 = pd.read_csv(f"FWHM/test_data/test_data_F30.csv")
            testset_f31 = pd.read_csv(f"FWHM/test_data/test_data_F31.csv")
        except FileNotFoundError:
            testset_f28 = pd.read_csv(f"FWHM/normalize_data_F28.csv")
            testset_f29 = pd.read_csv(f"FWHM/normalize_data_F29.csv")
            testset_f30 = pd.read_csv(f"FWHM/normalize_data_F30.csv")
            testset_f31 = pd.read_csv(f"FWHM/normalize_data_F31.csv")
        test_dataset = {
            "F28": testset_f28,
            "F29": testset_f29,
            "F30": testset_f30,
            "F31": testset_f31,
        }
        st.session_state["simulation_test_data"] = test_dataset

    target_dataset = st.session_state["simulation_test_data"][selected_dataset]
    selected_record = target_dataset.sample(n=1).iloc[0]
    st.session_state["simulation_selected_record"] = selected_record
    return selected_record

def show_variable_inputs(selected_record, group_name):
    """변수 입력 UI 생성"""
    st.markdown(f"### {group_name} 변수 입력")

    # 세션 상태 키
    CURRENT_SIM_MODE = st.session_state["current_sim_mode"]
    run_button_state_key = f"{CURRENT_SIM_MODE}_button_clicked"
    ratio_state_key = f"ratios_{group_name}"
    table_state_key = f"simulation_table_data_{group_name}"

    # 원본 레코드 1개 랜덤 로드 상태 확인
    is_new_record = st.session_state["new_record_selected"] if "new_record_selected" in st.session_state else False

    # 물질 비율 초기화
    if ratio_state_key not in st.session_state or is_new_record:
        st.session_state[ratio_state_key] = {
            'A': 1.00, 'B': 0.00, 'C': 0.00, 'D': 0.00
        }

    # 랜덤화 버튼
    randomize = st.button(f"{group_name} 변수 랜덤화", key=f"random_{group_name.lower()}")

    # 물질 비율 랜덤화
    if randomize:
        import random
        cuts = sorted(random.sample(range(101), 3) + [0, 100])
        nums = [(cuts[i+1] - cuts[i]) / 100 for i in range(4)]
        st.session_state[ratio_state_key] = {
            'A': nums[0], 'B': nums[1], 'C': nums[2], 'D': nums[3]
        }
        # 실행 버튼 클릭 상태 초기화
        st.session_state[run_button_state_key] = False
        if CURRENT_SIM_MODE == "물질 혼합 예측":
            # `물질 혼합 예측` 모드에서 실제 Target_F 값 출력 필요 여부 초기화
            st.session_state["actual_target_f_needed"] = False

    # 각 A/B/C/D 그룹의 비율 설정
    st.markdown(f"#### {group_name} 물질 비율 설정")
    ratio_cols = st.columns(4)
    ratios = {}

    # 각 A/B/C/D 비율 입력 필드 생성
    for i, suffix in enumerate(['A', 'B', 'C', 'D']):
        with ratio_cols[i]:
            ratios[suffix] = st.number_input(
                f"{suffix} 비율",
                min_value=0.0,
                max_value=1.0,
                value=float(st.session_state[ratio_state_key][suffix]),
                step=0.01,
                key=f"{ratio_state_key}_{suffix}", # key 중복 에러 방지를 위한 number_input별 key 값
                on_change=on_change_input_values
            )

            # 입력값을 세션 상태에 즉시 저장
            st.session_state[ratio_state_key][suffix] = ratios[suffix]

    # 비율 정규화
    total_ratio = sum(ratios.values())
    if total_ratio <= 0:
        st.error("최소한 하나의 비율은 0보다 커야 합니다.")
        return {}, {}, []

    normalized_ratios = {k: v/total_ratio for k, v in ratios.items()}
    st.session_state[ratio_state_key].update(normalized_ratios)
    st.info(f"정규화된 비율: " + ", ".join([f"{k}={v:.2f}" for k, v in normalized_ratios.items()]) + " (합계=1.0)")

    # 변수 값을 저장할 데이터 구조 생성
    values = {}
    weighted_averages = {}

    # 테이블 데이터가 이미 세션에 있는지 확인
    # 랜덤화 버튼을 누르지 않았고, 새로운 랜덤 레코드를 선택하지 않았다면 세션에 저장된 데이터 사용
    if not randomize and not is_new_record and table_state_key in st.session_state:
        table_data = st.session_state[table_state_key]
    else:
        # 선택된 레코드에서 해당 그룹의 변수 찾기
        prefix = group_name  # Li, Pre_L 또는 Pre_S
        base_var_names = sorted(list(set([col for col in selected_record.index if col.startswith(prefix)])))

        table_data = []

        # 각 변수에 대해 A/B/C/D 값을 행으로 구성
        for base_var_name in base_var_names:
            row_data = {"변수명": base_var_name}
            group_values = {}

            for suffix in ['A', 'B', 'C', 'D']:
                var_name = f"{base_var_name}_{suffix}"

                if suffix == 'A' and (base_var_name in selected_record.index):
                    value = float(selected_record[base_var_name])
                else:
                    value = 0.0

                # 분포에 따른 랜덤값 생성
                if randomize:
                    min_val, max_val, mean_val, std_val = 0.0, 1.0, 0.5, 0.1

                    if st.session_state.get('rand_dist') == "정규 분포 (Normal)":
                        value = float(np.random.normal(mean_val, std_val))
                        value = np.clip(value, min_val, max_val)
                    else:  # 균일 분포
                        value = float(np.random.uniform(min_val, max_val))

                row_data[suffix] = value
                values[var_name] = value
                group_values[suffix] = value

            # 현재 변수의 가중 평균 계산
            weighted_avg = sum(val * normalized_ratios[suf] for suf, val in group_values.items())
            weighted_averages[base_var_name] = weighted_avg
            row_data["Weighted Avg"] = weighted_avg
            table_data.append(row_data)

        # 테이블 데이터를 세션 상태에 저장
        st.session_state[table_state_key] = table_data

    # 편집 가능한 테이블 출력
    column_config = {
        "변수명": st.column_config.TextColumn("변수명", disabled=True, width="medium")
    }

    for suffix in ['A', 'B', 'C', 'D']:
        column_config[suffix] = st.column_config.NumberColumn(
            suffix, min_value=0.0, max_value=1.0, format="%.4f"
        )

    column_config["Weighted Avg"] = st.column_config.NumberColumn(
        "가중 평균", disabled=True, format="%.4f"
    )

    edited_df = st.data_editor(
        pd.DataFrame(table_data),
        column_config=column_config,
        hide_index=True,
        on_change=on_change_input_values
    )

    # 수정된 값을 저장하고 가중 평균 업데이트
    updated_table_data = []
    for _, row in edited_df.iterrows():
        var_num = row["변수명"]
        group_values = {}
        row_data = {"변수명": var_num}

        for suffix in ['A', 'B', 'C', 'D']:
            var_name = f"{var_num}_{suffix}"
            value = row[suffix]
            values[var_name] = value
            group_values[suffix] = value
            row_data[suffix] = value

        # 가중 평균 업데이트
        weighted_avg = sum(val * normalized_ratios[suf] for suf, val in group_values.items())
        weighted_averages[var_num] = weighted_avg
        row_data["Weighted Avg"] = weighted_avg
        updated_table_data.append(row_data)

    # 업데이트된 테이블 데이터를 세션 상태에 저장
    st.session_state[table_state_key] = updated_table_data

    # 정규화된 비율 리스트로 반환
    abcd_ratio_list = [normalized_ratios[suf] for suf in ['A', 'B', 'C', 'D']]

    return values, weighted_averages, abcd_ratio_list

def show_optimization_results(df, model, all_values, opt_direction, material_ratio_candidates, abcd_ratio_candidates, start_from_ui=True, initial_abcd_ratios=None, target_value=None):
    """최적화 결과 표시"""
    # 진행 상태 표시
    progress_bar = st.progress(0)
    status_text = st.empty()

    # 최적화 실행
    status_text.text("최적 혼합 비율 탐색 중...")

    # 그리드 서치를 통한 최적화
    is_maximizing = opt_direction == "Target_F 최대화"
    is_minimizing = opt_direction == "Target_F 최소화"
    is_targeting = opt_direction == "Target_F 목표값에 근접"

    if is_maximizing:
        best_prediction = -np.inf
    elif is_minimizing:
        best_prediction = np.inf
    else:  # 목표값에 근접
        best_prediction = None
        best_diff = np.inf

    # 물질 유형 비율은 고정값 사용
    best_ratios = material_ratio_candidates  # 고정된 [Li, Pre_L, Pre_S] 비율

    # A/B/C/D 비율 초기값 설정
    if start_from_ui and initial_abcd_ratios:
        best_abcd_ratios = initial_abcd_ratios.copy()
    else:
        best_abcd_ratios = {
            "Li": [0.25, 0.25, 0.25, 0.25],
            "Pre_L": [0.25, 0.25, 0.25, 0.25],
            "Pre_S": [0.25, 0.25, 0.25, 0.25]
        }

    # 입력 변수 데이터 준비
    # 물질 별로 A/B/C/D에 해당하는 변수들 묶기
    li_vars = {var: val for var, val in all_values.items() if var.startswith('Li')}
    pre_l_vars = {var: val for var, val in all_values.items() if var.startswith('Pre_L')}
    pre_s_vars = {var: val for var, val in all_values.items() if var.startswith('Pre_S')}

    # A/B/C/D 비율 최적화
    status_text.text("A/B/C/D 비율 최적화 중...")

    # 총 진행 횟수 계산
    total_abcd_iterations = len(abcd_ratio_candidates) ** 3 * 3  # 3개 물질 유형, 각 A/B/C 선택 (D는 종속)

    # 먼저 현재 A/B/C/D 비율로 기준 예측치 확인
    initial_prediction = predict_with_ratios(
        model, li_vars, pre_l_vars, pre_s_vars,
        best_ratios,
        best_abcd_ratios
    )

    if initial_prediction is not None:
        if is_maximizing or is_minimizing:
            best_prediction = initial_prediction
            status_text.text(f"초기 A/B/C/D 비율로 예측된 Target_F: {best_prediction:.6f}")
        else:  # 목표값에 근접
            best_prediction = initial_prediction
            best_diff = abs(initial_prediction - target_value)
            status_text.text(f"초기 A/B/C/D 비율로 예측된 Target_F: {best_prediction:.6f} (목표값과의 차이: {best_diff:.6f})")

    # 진행 상태 추적 변수
    current_iteration = 0

    # 각 물질 유형에 대해 최적화
    material_types = ["Li", "Pre_L", "Pre_S"]

    for mat_idx, mat_type in enumerate(material_types):
        if is_targeting:
            status_text.text(f"{mat_type} A/B/C/D 비율 최적화 중...(현재 최적 Target_F: {best_prediction:.6f}, 목표값과의 차이: {abs(best_prediction - target_value):.6f})")
        else:
            status_text.text(f"{mat_type} A/B/C/D 비율 최적화 중...(현재 최적 Target_F: {best_prediction:.6f})")

        # A, B, C 비율 탐색 (D는 나머지로 계산)
        for a_ratio in abcd_ratio_candidates:
            for b_ratio in abcd_ratio_candidates:
                for c_ratio in abcd_ratio_candidates:
                    # 합이 1을 넘으면 무시
                    if a_ratio + b_ratio + c_ratio > 1.0:
                        current_iteration += 1
                        continue

                    # D 비율은 나머지
                    d_ratio = max(0.0, 1.0 - (a_ratio + b_ratio + c_ratio))

                    # 비율 총합이 0이면 무시
                    if a_ratio + b_ratio + c_ratio + d_ratio == 0:
                        current_iteration += 1
                        continue

                    # 정규화
                    total = a_ratio + b_ratio + c_ratio + d_ratio
                    if total > 0:
                        norm_a = a_ratio / total
                        norm_b = b_ratio / total
                        norm_c = c_ratio / total
                        norm_d = d_ratio / total
                    else:
                        current_iteration += 1
                        continue

                    # 현재 최적의 비율에서 한 물질 유형의 A/B/C/D 비율만 변경
                    curr_material_ratios = best_abcd_ratios.copy()
                    curr_material_ratios[mat_type] = [norm_a, norm_b, norm_c, norm_d]

                    # 예측 시행
                    prediction = predict_with_ratios(
                        model, li_vars, pre_l_vars, pre_s_vars,
                        best_ratios,
                        curr_material_ratios
                    )

                    # 최적값 업데이트
                    if prediction is not None:
                        is_better = False
                        if opt_direction == "Target_F 최대화":
                            is_better = prediction > best_prediction
                        elif opt_direction == "Target_F 최소화":
                            is_better = prediction < best_prediction
                        else:  # 목표값에 근접
                            current_diff = abs(prediction - target_value)
                            best_diff = abs(best_prediction - target_value)
                            is_better = current_diff < best_diff

                        if is_better:
                            best_prediction = prediction
                            best_abcd_ratios[mat_type] = [norm_a, norm_b, norm_c, norm_d]
                            # 현재 최적값 업데이트
                            status_text.text(f"현재 최적 {mat_type} A/B/C/D 비율: [{norm_a:.2f}, {norm_b:.2f}, {norm_c:.2f}, {norm_d:.2f}], Target_F: {prediction:.6f}")

                    # 진행 상태 업데이트
                    current_iteration += 1
                    progress = current_iteration / total_abcd_iterations
                    progress_bar.progress(progress)

    # 결과 표시
    progress_bar.progress(1.0)
    status_text.text("최적 혼합 비율 탐색 완료!")

    # 최종 결과 표시
    show_optimization_visualization(best_ratios, best_prediction, opt_direction, best_abcd_ratios, target_value)

@st.cache_data(show_spinner=False)
def predict_with_ratios(_model, li_vars, pre_l_vars, pre_s_vars, qcp_vars, material_ratios, abcd_ratios):
    """주어진 비율로 예측 수행"""
    try:
        # 재료별 비율 분해
        li_ratio, pre_l_ratio, pre_s_ratio = material_ratios

        # 입력 데이터 준비
        input_data = {}

        # 모델에서 사용하는 특성 이름 형식 확인 (옛 포맷 또는 새 포맷)
        # 모델의 특성 이름 가져오기
        if isinstance(_model, xgb.Booster):
            feature_names = _model.feature_names
        elif hasattr(_model, 'feature_names_'): # CatBoost, 일부 sklearn 모델
            feature_names = _model.feature_names_
        elif hasattr(_model, 'feature_name_'): # LightGBM
            feature_names = _model.feature_name_
        else:
            # feature_names를 얻을 수 없는 경우
            st.warning("모델에서 특성 이름 형식을 확인할 수 없습니다. 기본 형식을 사용합니다.")
            feature_names = []

        # 특성 이름 형식 확인 (Li_1 형식인지 Li1 형식인지)
        # uses_underscore = any(name.startswith('Li') or name.startswith('Qcp') for name in feature_names) if feature_names else True

        # Li 변수 처리
        li_var_names = [col for col in feature_names if col.startswith('Li')]
        for var_name in li_var_names:
            # 각 A/B/C/D 변수 확인
            group_values = {}
            for suffix in ['A', 'B', 'C', 'D']:
                # 새 형식에 맞게 변수 이름도 조정
                input_var_name = f"{var_name}_{suffix}"
                if input_var_name in li_vars:
                    group_values[suffix] = li_vars[input_var_name]

            # 가중 평균 계산
            if group_values:
                weighted_avg = 0
                for idx, suffix in enumerate(['A', 'B', 'C', 'D']):
                    if suffix in group_values:
                        weighted_avg += group_values[suffix] * abcd_ratios["Li"][idx]
                input_data[var_name] = weighted_avg

        # Pre_L 변수 처리
        pre_l_var_names = [col for col in feature_names if col.startswith('Pre_L')]
        for var_name in pre_l_var_names:
            # 각 A/B/C/D 변수 확인
            group_values = {}
            for suffix in ['A', 'B', 'C', 'D']:
                # 입력값 pre_l_vars에서 가져올 때는 항상 새 형식(Pre_L1_A) 사용
                input_var_name = f"{var_name}_{suffix}" # 예: Pre_L1_A
                if input_var_name in pre_l_vars:
                    group_values[suffix] = pre_l_vars[input_var_name]

            # 가중 평균 계산
            if group_values:
                weighted_avg = 0
                # abcd_ratios["Pre_L"] 는 [A비율, B비율, C비율, D비율] 리스트
                for idx_abcd, suffix in enumerate(['A', 'B', 'C', 'D']):
                    if suffix in group_values:
                        weighted_avg += group_values[suffix] * abcd_ratios["Pre_L"][idx_abcd]
                input_data[var_name] = weighted_avg # 최종적으로 모델이 기대하는 var_name으로 저장

        # Pre_S 변수 처리
        pre_s_var_names = [col for col in feature_names if col.startswith('Pre_S')]
        for var_name in pre_s_var_names:
            # 각 A/B/C/D 변수 확인
            group_values = {}
            for suffix in ['A', 'B', 'C', 'D']:
                input_var_name = f"{var_name}_{suffix}" # 예: Pre_S1_A
                if input_var_name in pre_s_vars:
                    group_values[suffix] = pre_s_vars[input_var_name]

            # 가중 평균 계산
            if group_values:
                weighted_avg = 0
                # abcd_ratios["Pre_S"] 는 [A비율, B비율, C비율, D비율] 리스트
                for idx_abcd, suffix in enumerate(['A', 'B', 'C', 'D']):
                    if suffix in group_values:
                        weighted_avg += group_values[suffix] * abcd_ratios["Pre_S"][idx_abcd]
                input_data[var_name] = weighted_avg # 최종적으로 모델이 기대하는 var_name으로 저장

        # Qcp 변수 추가 (이 변수들은 직접 값을 사용)
        for var_name, value in qcp_vars.items():
            input_data[var_name] = value

        # 모든 특성 이름 가져오기 (모델 훈련 시 사용된 순서대로)
        if isinstance(_model, xgb.Booster):
            feature_names = _model.feature_names
        elif hasattr(_model, 'feature_names_'): # CatBoost, 일부 sklearn 모델
            feature_names = _model.feature_names_
        elif hasattr(_model, 'feature_name_'): # LightGBM
            feature_names = _model.feature_name_
        else:
            # feature_names를 얻을 수 없는 경우, input_data의 키 순서를 사용 (정확하지 않을 수 있음)
            st.warning("모델에서 특성 이름 순서를 가져올 수 없습니다. 예측이 정확하지 않을 수 있습니다.")
            feature_names = list(input_data.keys())

        input_df = pd.DataFrame([input_data])

        # 컬럼 순서를 모델 훈련 시와 동일하게 맞춤
        try:
            input_df = input_df[feature_names]
        except KeyError as e:
            # st.error(f"특성 이름 형식 불일치: 모델 재학습이 필요할 수 있습니다.")
            st.error(f"특성 이름 형식 불일치: {e}")
            return None

        # 모델 타입에 따라 예측 수행
        if isinstance(_model, xgb.Booster):
            # XGBoost 모델인 경우 DMatrix 사용
            try:
                # 특성 이름 순서가 모델 훈련 시와 동일해야 함
                # input_df의 컬럼 순서가 훈련 시 사용된 순서와 같다고 가정
                dmatrix = xgb.DMatrix(input_df)
                prediction = _model.predict(dmatrix)[0]
            except Exception as e:
                st.error(f"XGBoost 예측 오류: {e}. 모델 훈련 시 사용된 특성과 순서가 일치하는지 확인하세요.")
                return None
        elif hasattr(_model, 'predict'): # CatBoost 또는 다른 Scikit-learn 호환 모델
            try:
                prediction = _model.predict(input_df)[0]
            except Exception as e:
                st.error(f"{type(_model).__name__} 예측 오류: {e}")
                return None
        else:
            st.error(f"지원되지 않는 모델 타입: {type(_model)}")
            return None

        return prediction

    except Exception as e:
        st.error(f"예측 중 오류 발생: {e}")
        return None

def show_input_tables(all_values, li_ratio, pre_l_ratio, pre_s_ratio, qcp_values):
    """입력값 테이블 표시"""
    # 물질 유형별로 테이블 생성
    li_input = {var: [val] for var, val in all_values.items() if var.startswith('Li')}
    pre_l_input = {var: [val] for var, val in all_values.items() if var.startswith('Pre_L')}
    pre_s_input = {var: [val] for var, val in all_values.items() if var.startswith('Pre_S')}

    # 데이터프레임 생성
    li_input_df = pd.DataFrame(li_input)
    pre_l_input_df = pd.DataFrame(pre_l_input)
    pre_s_input_df = pd.DataFrame(pre_s_input)

    # 탭으로 표시
    input_tabs = st.tabs(["Li 변수", "Pre_L 변수", "Pre_S 변수", "Qcp 변수"]) # Add Qcp tab

    with input_tabs[0]:
        st.write(f"Li 물질 비율: {li_ratio:.2f}")
        st.dataframe(li_input_df, use_container_width=True)

    with input_tabs[1]:
        st.write(f"Pre_L 물질 비율: {pre_l_ratio:.2f}")
        st.dataframe(pre_l_input_df, use_container_width=True)

    with input_tabs[2]:
        st.write(f"Pre_S 물질 비율: {pre_s_ratio:.2f}")
        st.dataframe(pre_s_input_df, use_container_width=True)

    with input_tabs[3]: # Qcp tab
        st.write(f"Qcp 변수 (직접 입력)")
        qcp_input_df = pd.DataFrame({k: [v] for k, v in qcp_values.items()})
        st.dataframe(qcp_input_df, use_container_width=True)

def show_prediction_gauge(df, prediction, actual_target_f_needed=False):
    """예측 결과 게이지 차트 표시"""
    st.subheader("예측 결과 시각화")

    # 전체 Target_F 범위
    target_min = float(df['Target_F'].min())
    target_max = float(df['Target_F'].max())
    target_range = target_max - target_min

    # 예측값 게이지 차트 생성
    prediction_fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=prediction,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "예측된 Target_F 값", 'font': {'color': ECOPRO_COLORS['dark_blue']}},
        number={'font': {'color': ECOPRO_COLORS['dark_blue']}},
        gauge={
            'axis': {'range': [target_min, target_max], 'tickfont': {'color': ECOPRO_COLORS['text']}},
            'bar': {'color': ECOPRO_COLORS['light_blue']},
            'steps': [
                {'range': [target_min, target_min + target_range/3], 'color': ECOPRO_COLORS['light_gray']},
                {'range': [target_min + target_range/3, target_min + 2*target_range/3], 'color': 'rgba(38, 169, 224, 0.3)'},
                {'range': [target_min + 2*target_range/3, target_max], 'color': 'rgba(22, 65, 147, 0.3)'}
            ],
            'threshold': {
                'line': {'color': ECOPRO_COLORS['orange'], 'width': 4},
                'thickness': 0.75,
                'value': prediction
            }
        }
    ))
    prediction_fig.update_layout(height=400, font={'color': ECOPRO_COLORS['text']})

    if actual_target_f_needed:
        # 실제 Target_F 값 게이지 차트 생성
        actual_target_f = st.session_state["simulation_selected_record"]["Target_F"]
        actual_target_f_fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=actual_target_f,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "실제 Target_F 값", 'font': {'color': ECOPRO_COLORS['dark_blue']}},
            number={'font': {'color': ECOPRO_COLORS['dark_blue']}},
            gauge={
                'axis': {'range': [target_min, target_max], 'tickfont': {'color': ECOPRO_COLORS['text']}},
                'bar': {'color': ECOPRO_COLORS['light_blue']},
                'steps': [
                    {'range': [target_min, target_min + target_range/3], 'color': ECOPRO_COLORS['light_gray']},
                    {'range': [target_min + target_range/3, target_min + 2*target_range/3], 'color': 'rgba(38, 169, 224, 0.3)'},
                    {'range': [target_min + 2*target_range/3, target_max], 'color': 'rgba(22, 65, 147, 0.3)'}
                ],
                'threshold': {
                    'line': {'color': ECOPRO_COLORS['orange'], 'width': 4},
                    'thickness': 0.75,
                    'value': actual_target_f
                }
            }
        ))
        actual_target_f_fig.update_layout(height=400, font={'color': ECOPRO_COLORS['text']})

        # 오차 / 오차율
        residual = prediction - actual_target_f
        residual_rate = (abs(residual)*100)/(actual_target_f*100) * 100
        normalized_residual = (abs(residual)*100)/((target_max - target_min)*100) * 100

        chart_col1, chart_col2, residual_col = st.columns([2, 2, 1], vertical_alignment="center")
        with chart_col1:
            st.plotly_chart(prediction_fig, use_container_width=True)
        with chart_col2:
            st.plotly_chart(actual_target_f_fig, use_container_width=True)
        with residual_col:
            st.metric("오차", f"{residual:.3f}", border=True)
            st.write(" ")
            st.metric("오차율", f"{residual_rate:.2f}%", border=True)
            st.write(" ")
            st.metric("Target 값 범위 대비 오차율", f"{normalized_residual:.2f}%", border=True)
    else:
        # 예측값 게이지 차트만 출력
        st.plotly_chart(prediction_fig, use_container_width=True)

def show_optimization_visualization(best_ratios, best_prediction, opt_direction, best_abcd_ratios, target_value=None):
    """최적화 결과 시각화"""
    st.markdown("""
    <style>
    .big-font {
        font-size:24px !important;
        font-weight:bold;
    }
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)

    # 결과 헤더
    st.markdown('<p class="big-font">🎯 최적 혼합 비율 탐색 결과</p>', unsafe_allow_html=True)

    # 메트릭 카드로 주요 결과 표시
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        if opt_direction == "Target_F 최대화":
            st.metric("최대화된 Target_F", f"{best_prediction:.6f}", "🔼 최대값")
        elif opt_direction == "Target_F 최소화":
            st.metric("최소화된 Target_F", f"{best_prediction:.6f}", "🔽 최소값")
        else:
            diff = abs(best_prediction - target_value)
            st.metric("예측된 Target_F", f"{best_prediction:.6f}", f"차이: {diff:.6f}")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Li:Pre_L:Pre_S 비율",
                 f"{best_ratios[0]:.2f}:{best_ratios[1]:.2f}:{best_ratios[2]:.2f}",
                 "고정 비율")
        st.markdown('</div>', unsafe_allow_html=True)

    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        if target_value is not None:
            st.metric("목표 Target_F", f"{target_value:.6f}",
                     f"정확도: {(1 - abs(best_prediction - target_value)/target_value)*100:.2f}%")
        else:
            st.metric("최적화 방향", opt_direction.split()[-1], "✓ 달성")
        st.markdown('</div>', unsafe_allow_html=True)

    # 물질별 최적 비율 시각화
    st.markdown("## 📊 물질별 최적 비율 분석")

    material_types = ["Li", "Pre_L", "Pre_S"]
    colors = {
        'A': ECOPRO_COLORS['dark_blue'],
        'B': ECOPRO_COLORS['light_blue'],
        'C': ECOPRO_COLORS['orange'],
        'D': ECOPRO_COLORS['blue_dark_light']
    }

    # 전체 물질 비교를 위한 통합 차트
    combined_data = []
    for mat_type in material_types:
        ratios = best_abcd_ratios[mat_type]
        for i, (component, ratio) in enumerate(zip(['A', 'B', 'C', 'D'], ratios)):
            combined_data.append({
                'Material': mat_type,
                'Component': component,
                'Ratio': ratio,
                'Color': colors[component]
            })

    # 통합 막대 그래프
    fig_combined = go.Figure()

    for component in ['A', 'B', 'C', 'D']:
        component_data = [d for d in combined_data if d['Component'] == component]
        fig_combined.add_trace(go.Bar(
            name=f'Component {component}',
            x=[d['Material'] for d in component_data],
            y=[d['Ratio'] for d in component_data],
            marker_color=colors[component],
            text=[f'{ratio:.3f}' for ratio in [d['Ratio'] for d in component_data]],
            textposition='auto',
        ))

    fig_combined.update_layout(
        title='물질별 A/B/C/D 비율 비교',
        barmode='stack',
        yaxis_title='비율',
        height=400,
        showlegend=True,
        legend_title='구성 요소',
        uniformtext_minsize=10,
        uniformtext_mode='hide'
    )

    st.plotly_chart(fig_combined, use_container_width=True)

    # 물질별 상세 분석
    for i, mat_type in enumerate(material_types):
        with st.expander(f"📈 {mat_type} 상세 분석", expanded=True):
            ratios = best_abcd_ratios[mat_type]

            col1, col2 = st.columns(2)

            with col1:
                # 도넛 차트
                fig_donut = go.Figure(data=[go.Pie(
                    labels=['A', 'B', 'C', 'D'],
                    values=ratios,
                    hole=0.6,
                    marker=dict(colors=[colors[label] for label in ['A', 'B', 'C', 'D']]),
                    textinfo='label+percent',
                    textposition='outside',
                    pull=[0.1, 0.1, 0.1, 0.1]
                )])

                fig_donut.update_layout(
                    title=dict(
                        text=f"{mat_type} 구성 비율",
                        x=0.5,
                        y=0.95,
                        xanchor='center',
                        yanchor='top'
                    ),
                    annotations=[dict(
                        text=f'총합\n100%',
                        x=0.5,
                        y=0.5,
                        font_size=14,
                        showarrow=False
                    )],
                    height=400,
                    showlegend=False
                )
                st.plotly_chart(fig_donut, use_container_width=True)

            with col2:
                # 레이더 차트
                fig_radar = go.Figure()

                fig_radar.add_trace(go.Scatterpolar(
                    r=ratios + [ratios[0]],  # 첫 값을 마지막에 추가하여 도형 완성
                    theta=['A', 'B', 'C', 'D', 'A'],
                    fill='toself',
                    name=mat_type,
                    marker_color='rgba(31, 119, 180, 0.7)'
                ))

                fig_radar.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0, max(ratios) * 1.2]
                        )
                    ),
                    title=f"{mat_type} 분포 패턴",
                    height=400,
                    showlegend=False
                )
                st.plotly_chart(fig_radar, use_container_width=True)

            # 상세 수치 표시
            st.markdown(f"""
            **정확한 비율:**
            - A: {ratios[0]:.4f} ({ratios[0]*100:.1f}%)
            - B: {ratios[1]:.4f} ({ratios[1]*100:.1f}%)
            - C: {ratios[2]:.4f} ({ratios[2]*100:.1f}%)
            - D: {ratios[3]:.4f} ({ratios[3]*100:.1f}%)
            """)

    # 결과 저장 섹션
    st.markdown("## 💾 결과 저장")
    save_container = st.container()

    # CSV 데이터 준비
    result_data = {
        "최적화 방향": opt_direction,
        "예측된 Target_F": best_prediction,
        "Li 비율": best_ratios[0],
        "Pre_L 비율": best_ratios[1],
        "Pre_S 비율": best_ratios[2],
        "best_abcd_ratios": best_abcd_ratios,
        "target_value": target_value
    }

    # A/B/C/D 비율 추가
    for mat_type in material_types:
        for i, component in enumerate(['A', 'B', 'C', 'D']):
            result_data[f"{mat_type}_{component} 비율"] = best_abcd_ratios[mat_type][i]

    if target_value is not None:
        result_data["목표 Target_F"] = target_value
        result_data["목표값과의 차이"] = abs(best_prediction - target_value)

    # DataFrame으로 변환
    result_df = pd.DataFrame([{k: v for k, v in result_data.items() if k != 'best_abcd_ratios'}])
    csv = result_df.to_csv(index=False)

    # CSV 다운로드 버튼
    save_container.download_button(
        label="📥 최적화 결과 CSV 파일로 저장",
        data=csv,
        file_name=f"최적화결과_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        help="모든 최적화 결과를 CSV 파일로 저장합니다."
    )

    # 최적화 결과 자동 저장
    save_optimization_result(result_data)

    # AI 분석 요약
    st.subheader("🤖 iDSB AI 최적화 분석 요약")

    # 결과 데이터를 세션 상태에 저장 (페이지 리로드 시 유지)
    if "opt_analysis_info" not in st.session_state:
        # 분석 정보 수집
        analysis_info = {
            "최적화_방향": opt_direction,
            "예측된_Target_F": round(float(best_prediction), 6),
            "물질_유형별_비율": {
                "Li": best_ratios[0],
                "Pre_L": best_ratios[1],
                "Pre_S": best_ratios[2]
            },
            "물질별_ABCD_최적_비율": {
                "Li": [round(r, 4) for r in best_abcd_ratios["Li"]],
                "Pre_L": [round(r, 4) for r in best_abcd_ratios["Pre_L"]],
                "Pre_S": [round(r, 4) for r in best_abcd_ratios["Pre_S"]]
            }
        }

        # 목표값 정보 추가
        if target_value is not None:
            analysis_info["목표_Target_F"] = round(float(target_value), 6)
            analysis_info["목표값과의_차이"] = round(float(abs(best_prediction - target_value)), 6)
            analysis_info["정확도"] = round((1 - abs(best_prediction - target_value)/target_value)*100, 2)

        st.session_state.opt_analysis_info = analysis_info

    # 저장된 분석 정보 사용
    analysis_info = st.session_state.opt_analysis_info

    # Qcp 값 가져오기 (all_values는 여기서 접근 불가, UI 상태에서 가져와야 함)
    qcp_values_from_state = {k.replace("value_", ""): v for k, v in st.session_state.items()
                           if k.startswith("value_Qcp")}

    # 프롬프트 생성
    prompt = f"""
    아래 최적화 결과 정보를 바탕으로 전문적인 분석 리포트를 작성해주세요.
    리포트는 마크다운 형식으로 작성하며, 각 섹션을 명확히 구분해주세요.

    ## 최적화 결과 정보
    {json.dumps(analysis_info, indent=2, ensure_ascii=False)}

    ## 고정된 Qcp 입력값 (일부)
    {json.dumps(list(qcp_values_from_state.items())[:5], ensure_ascii=False)}

    다음 구조로 분석 리포트를 작성해주세요:

    1. 최적화 결과 요약 (최적화 방향과 달성된 Target_F 값)
    2. 물질별 최적 비율 분석 (각 물질 유형의 ABCD 비율 패턴 분석)
    3. 고정 변수 영향 분석 (Qcp 값들이 최적화 결과에 미쳤을 영향 분석)
    4. 최적화 해석 (최적 혼합 비율이 가지는 의미와 중요성)
    5. 실용적 활용 방안 (최적화 결과를 실제 적용하기 위한 제안)
    6. 추가 연구 제안 (발전시키기 위한 추가 실험 또는 연구 방향)

    각 섹션은 ### 헤더로 구분하고, 중요한 수치나 인사이트는 **볼드체**로 강조해주세요.
    특히 흥미로운 패턴이나 특이점이 있다면 강조해주세요.
    """

    # 캐시 키 생성
    cache_key = generate_cache_key(
        prompt=prompt,
        model=st.session_state.selected_model,
        temperature=st.session_state.temperature
    )
    cache_state_key = "simulation_optimization_cache"

    # 캐싱된 분석 결과 확인
    if cache_state_key not in st.session_state:
        st.session_state[cache_state_key] = {}

    # 모델 정보 및 분석 버튼
    col1, col2 = st.columns([3, 1])
    with col1:
        model_info = f"사용 모델: {st.session_state.selected_model} | 온도: {st.session_state.temperature}"
        st.caption(model_info)

    with col2:
        if "opt_analysis_running" not in st.session_state:
            st.session_state.opt_analysis_running = False

        # 분석 버튼 (세션 상태 변수를 직접 변경하는 콜백 사용)
        run_analysis = st.button("최적화 분석 시작", key="opt_analysis_button", use_container_width=True)
        if run_analysis:
            st.session_state.opt_analysis_running = True
            # 캐시 무효화하여 새로운 분석 실행
            if cache_key in st.session_state[cache_state_key]:
                del st.session_state[cache_state_key][cache_key]

    # 분석 결과 표시
    if cache_key in st.session_state[cache_state_key]:
        # 캐시된 결과 표시
        cached_response = st.session_state[cache_state_key][cache_key]
        with st.chat_message("assistant"):
            st.markdown(cached_response["response"])
            if cached_response.get("metadata"):
                metadata_text = "\n\n---\n**처리 정보**\n```json\n"
                metadata_text += json.dumps(cached_response["metadata"], indent=2, ensure_ascii=False)
                metadata_text += "\n```"
                st.markdown(metadata_text)

        # 분석 실행 플래그 초기화
        st.session_state.opt_analysis_running = False

    elif st.session_state.opt_analysis_running:
        # 분석 실행 중인 경우
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            metadata_placeholder = st.empty()

            with st.spinner("AI가 최적화 결과를 분석하고 있습니다..."):
                try:
                    # AI 분석 실행
                    response, full_response, metadata = generate_ai_analysis(
                        prompt=prompt,
                        key_prefix="simulation_optimization",
                        message_placeholder=message_placeholder,
                        metadata_placeholder=metadata_placeholder
                    )

                    # 결과 캐싱
                    st.session_state[cache_state_key][cache_key] = {
                        "response": full_response,
                        "metadata": metadata
                    }
                except Exception as e:
                    st.error(f"AI 최적화 분석 생성 중 오류가 발생했습니다: {str(e)}")

                # 분석 실행 플래그 초기화
                st.session_state.opt_analysis_running = False

    else:
        # 분석 전 안내 메시지
        st.info("AI 최적화 분석을 실행하려면 '최적화 분석 시작' 버튼을 클릭하세요.")

@st.cache_data(show_spinner=False)
def greedy_search(_model, li_vars, pre_l_vars, pre_s_vars, qcp_vars, material_ratios, opt_direction, initial_abcd_ratios, target_value=None,
                 precision=0.01, tolerance=1e-6, max_iterations=100):
    """그리디 서치로 최적 비율 탐색"""
    import time
    start_time = time.time()

    # UI에서 설정한 초기 비율 사용
    best_abcd_ratios = initial_abcd_ratios.copy()

    # 초기 예측
    best_prediction = predict_with_ratios(_model, li_vars, pre_l_vars, pre_s_vars,
                                         qcp_vars, material_ratios, best_abcd_ratios)

    if best_prediction is None:
        return best_abcd_ratios, None

    # 진행 상태 표시 컨테이너들
    progress_container = st.container()
    with progress_container:
        st.markdown("### 최적화 진행 상황")

        # 설정 정보 expander
        with st.expander("🔍 탐색 설정 정보", expanded=True):
            # precision에 따른 탐색 범위 설정
            if precision == 0.1:
                base_steps = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
            elif precision == 0.01:
                base_steps = [i/100 for i in range(0, 101, 5)]  # 0.0에서 1.0까지 0.05 간격
            else:  # precision == 0.001
                base_steps = [i/1000 for i in range(0, 1001, 10)]  # 0.0에서 1.0까지 0.01 간격

            # 예상 조합 수 계산
            expected_combinations = len(base_steps) ** 3
            total_expected_combinations = expected_combinations * 3  # 3개 물질 유형

            st.markdown(f"""
            - **정밀도:** {precision}
            - **탐색 단계:** {len(base_steps)} 단계
            - **예상 조합 수:** {expected_combinations:,} 가지 (총 {total_expected_combinations:,} 가지)
            - **허용 오차:** {tolerance}
            - **최대 반복:** {max_iterations}
            """)

            # 초기 조건 표시
            st.markdown("**초기 조건:**")
            for mat_type in ["Li", "Pre_L", "Pre_S"]:
                ratios = initial_abcd_ratios[mat_type]
                st.markdown(f"- {mat_type}: A={ratios[0]:.3f}, B={ratios[1]:.3f}, C={ratios[2]:.3f}, D={ratios[3]:.3f}")
            st.markdown(f"- 초기 Target_F: {best_prediction:.6f}")

        # 진행 상태 표시
        overall_progress = st.progress(0, "전체 진행률")
        material_progress = st.progress(0, "현재 물질 진행률")

        # 실시간 상태 expander
        with st.expander("📊 실시간 진행 상태", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                status_text = st.empty()
                current_best_text = st.empty()
            with col2:
                timing_text = st.empty()
                stats_text = st.empty()

            # 진행 상태 메트릭스
            metric_cols = st.columns(4)
            with metric_cols[0]:
                total_count_metric = st.empty()
            with metric_cols[1]:
                current_count_metric = st.empty()
            with metric_cols[2]:
                improvements_metric = st.empty()
            with metric_cols[3]:
                time_per_combo_metric = st.empty()

        # 물질별 탐색 결과 expander
        material_results_expander = st.expander("🧪 물질별 탐색 결과", expanded=True)

    improved = True
    iteration = 0
    prev_best = best_prediction
    total_combinations_tried = 0
    total_improvements_found = 0
    material_combinations_tried = 0

    # 각 물질 유형별 최적화 진행
    while improved and iteration < max_iterations:
        improved = False
        iteration += 1

        material_results = []

        for mat_idx, mat_type in enumerate(["Li", "Pre_L", "Pre_S"]):
            material_start_time = time.time()
            material_combinations_tried = 0
            improvements_found = 0

            status_text.markdown(f"""
            **현재 진행 상태:**
            - 반복 횟수: {iteration}/{max_iterations}
            - 처리 중인 물질: {mat_type} ({mat_idx + 1}/3)
            """)

            # 현재 물질의 모든 가능한 조합 시도
            for a in base_steps:
                for b in base_steps:
                    if a + b > 1.0:  # 합이 1을 넘으면 건너뛰기
                        continue
                    for c in base_steps:
                        if a + b + c > 1.0:  # 합이 1을 넘으면 건너뛰기
                            continue

                        material_combinations_tried += 1
                        total_combinations_tried += 1

                        # 진행률 업데이트
                        material_progress.progress(
                            material_combinations_tried / expected_combinations,
                            f"{mat_type} 진행률: {material_combinations_tried}/{expected_combinations} 조합"
                        )
                        overall_progress.progress(
                            total_combinations_tried / total_expected_combinations,
                            f"전체 진행률: {total_combinations_tried}/{total_expected_combinations} 조합"
                        )

                        # D는 나머지
                        d = 1.0 - (a + b + c)

                        # 새로운 비율 조합
                        new_ratios = [a, b, c, d]

                        # 정규화 (합이 0인 경우 처리)
                        total = sum(new_ratios)
                        if total == 0:
                            continue

                        # 테스트할 비율 설정
                        test_abcd_ratios = best_abcd_ratios.copy()
                        test_abcd_ratios[mat_type] = new_ratios

                        # 예측 수행
                        prediction = predict_with_ratios(_model, li_vars, pre_l_vars,
                                                         pre_s_vars, qcp_vars, material_ratios,
                                                         test_abcd_ratios)

                        if prediction is not None:
                            is_better = False
                            if opt_direction == "Target_F 최대화":
                                is_better = prediction > best_prediction
                            elif opt_direction == "Target_F 최소화":
                                is_better = prediction < best_prediction
                            else:  # 목표값에 근접
                                current_diff = abs(prediction - target_value)
                                best_diff = abs(best_prediction - target_value)
                                is_better = current_diff < best_diff

                            if is_better:
                                improvements_found += 1
                                total_improvements_found += 1
                                best_prediction = prediction
                                best_abcd_ratios[mat_type] = new_ratios
                                improved = True

                                # 현재 최적값 업데이트
                                current_best_text.markdown(f"""
                                **현재 최적값 (개선됨! 🎯):**
                                - Target_F: {best_prediction:.6f}
                                - {mat_type} 비율: [{a:.3f}, {b:.3f}, {c:.3f}, {d:.3f}]
                                {f'- 목표값과의 차이: {abs(best_prediction - target_value):.6f}' if target_value is not None else ''}
                                """)

                        # 메트릭스 업데이트
                        elapsed_time = time.time() - start_time
                        total_count_metric.metric(
                            "총 시도한 조합",
                            f"{total_combinations_tried:,}",
                            f"전체의 {total_combinations_tried/total_expected_combinations*100:.1f}%"
                        )
                        current_count_metric.metric(
                            f"현재 물질({mat_type}) 시도",
                            f"{material_combinations_tried:,}",
                            f"전체의 {material_combinations_tried/expected_combinations*100:.1f}%"
                        )
                        improvements_metric.metric(
                            "발견된 개선점",
                            f"{total_improvements_found:,}",
                            f"성공률 {total_improvements_found/total_combinations_tried*100:.2f}%"
                        )
                        time_per_combo_metric.metric(
                            "조합당 소요 시간",
                            f"{(elapsed_time/total_combinations_tried*1000):.1f}ms",
                            f"총 {elapsed_time:.1f}초"
                        )

            # 물질별 결과 저장
            material_time = time.time() - material_start_time
            material_results.append({
                'type': mat_type,
                'time': material_time,
                'combinations': material_combinations_tried,
                'improvements': improvements_found,
                'ratios': best_abcd_ratios[mat_type]
            })

            # 물질별 결과 표시 업데이트
            with material_results_expander:
                st.markdown(f"#### 반복 {iteration} - {mat_type} 결과")
                st.markdown(f"""
                - **소요 시간:** {material_time:.2f}초
                - **시도한 조합 수:** {material_combinations_tried:,}
                - **발견한 개선점 수:** {improvements_found}
                - **현재 최적 비율:** A={best_abcd_ratios[mat_type][0]:.3f}, B={best_abcd_ratios[mat_type][1]:.3f}, C={best_abcd_ratios[mat_type][2]:.3f}, D={best_abcd_ratios[mat_type][3]:.3f}
                """)
                st.markdown("---")

        # 조기 종료 조건 체크
        if abs(best_prediction - prev_best) < tolerance:
            status_text.markdown(f"""
            **🎯 수렴 조건 도달!**
            - 반복 횟수: {iteration}/{max_iterations}
            - 개선폭: {abs(best_prediction - prev_best):.6f}
            """)
            break

        prev_best = best_prediction

    end_time = time.time()
    optimization_time = end_time - start_time

    overall_progress.progress(1.0, "최적화 완료!")
    material_progress.empty()
    status_text.markdown("### ✅ 최적화 완료!")

    return best_abcd_ratios, best_prediction, optimization_time

def parallel_predict_batch(model, combinations, batch_size=100):
    """병렬 처리로 배치 예측 수행"""
    with ThreadPoolExecutor() as executor:
        all_predictions = []
        for i in range(0, len(combinations), batch_size):
            batch = combinations[i:i + batch_size]
            predictions = list(executor.map(lambda x: predict_with_ratios(*x), batch))
            all_predictions.extend(predictions)
    return all_predictions

def save_optimization_result(result_data):
    """최적화 결과를 JSON 파일로 저장 (NumPy 타입 처리 추가)"""
    # 저장 디렉토리 생성
    save_dir = "optimization_results"
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    # 현재 시간으로 파일명 생성
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(save_dir, f"optimization_result_{now}.json")

    # NumPy 타입을 표준 Python 타입으로 변환하는 함수
    def convert_numpy_types(obj):
        if isinstance(obj, np.integer): # NumPy 정수형
            return int(obj)
        elif isinstance(obj, np.floating): # NumPy 실수형 (float32, float64 등)
            return float(obj)
        elif isinstance(obj, np.ndarray): # NumPy 배열
            return obj.tolist() # 리스트로 변환
        elif isinstance(obj, dict): # 딕셔너리인 경우 재귀 호출
            return {k: convert_numpy_types(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)): # 리스트/튜플인 경우 재귀 호출
            return [convert_numpy_types(i) for i in obj]
        return obj # 다른 타입은 그대로 반환

    # 변환 함수를 적용하여 JSON 직렬화 가능한 데이터 생성
    serializable_result_data = convert_numpy_types(result_data)

    # JSON으로 저장
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(serializable_result_data, f, ensure_ascii=False, indent=2)

    # st.success(f"최적화 결과 저장 완료: {filename}") # 메시지 제거 또는 변경 가능
    return filename

def load_latest_optimization_result():
    """가장 최근의 최적화 결과 로드"""
    import json
    import os
    from glob import glob

    save_dir = "optimization_results"
    if not os.path.exists(save_dir):
        return None

    # 모든 결과 파일 찾기
    result_files = glob(os.path.join(save_dir, "optimization_result_*.json"))
    if not result_files:
        return None

    # 가장 최근 파일 찾기
    latest_file = max(result_files, key=os.path.getctime)

    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"결과 파일 로드 중 오류 발생: {e}")
        return None

def check_mps_availability():
    """MPS(Metal Performance Shaders) 사용 가능 여부 확인"""
    if not torch.backends.mps.is_available():
        if not torch.backends.mps.is_built():
            print("MPS를 사용할 수 없습니다. PyTorch가 MPS를 지원하도록 빌드되지 않았습니다.")
        else:
            print("MPS를 사용할 수 없습니다. MPS 장치를 찾을 수 없습니다.")
        return False
    return True

def get_device():
    """사용할 디바이스 결정"""
    if check_mps_availability():
        return torch.device("mps")
    return torch.device("cpu")

def predict_with_ratios_mps(model, li_vars, pre_l_vars, pre_s_vars, material_ratios, abcd_ratios_batch):
    """M1 GPU를 활용한 배치 예측 (최적화된 버전)"""
    try:
        # MPS 디바이스 설정
        device = get_device()

        # 모델을 GPU로 한 번만 이동
        if not hasattr(model, 'device') or model.device != device:
            model = model.to(device)
            model.device = device

        # 배치 크기
        batch_size = len(abcd_ratios_batch)

        # 입력 데이터를 직접 GPU에 할당 (메모리 최적화)
        input_data = torch.zeros((batch_size, 92), device=device)  # Li(28) + Pre_L(32) + Pre_S(32) = 92

        # 변수 인덱스 미리 계산 (CPU 작업 최소화)
        li_indices = [(i, f"Li{i}") for i in range(1, 29)]
        pre_l_indices = [(i+28, f"Pre_L{i}") for i in range(32)]
        pre_s_indices = [(i+60, f"Pre_S{i}") for i in range(32)]

        # 가중치 계산을 GPU에서 수행
        for batch_idx, abcd_ratios in enumerate(abcd_ratios_batch):
            # Li, Pre_L, Pre_S 가중치를 텐서로 변환
            li_weights = torch.tensor(abcd_ratios["Li"], device=device)
            pre_l_weights = torch.tensor(abcd_ratios["Pre_L"], device=device)
            pre_s_weights = torch.tensor(abcd_ratios["Pre_S"], device=device)

            # 각 변수 그룹별로 한 번에 처리
            for idx_offset, var_name in li_indices:
                values = torch.tensor([li_vars.get(f"{var_name}_{suffix}", 0.0)
                                     for suffix in ['A', 'B', 'C', 'D']], device=device)
                input_data[batch_idx, idx_offset-1] = torch.sum(values * li_weights)

            for idx_offset, var_name in pre_l_indices:
                values = torch.tensor([pre_l_vars.get(f"{var_name}_{suffix}", 0.0)
                                     for suffix in ['A', 'B', 'C', 'D']], device=device)
                input_data[batch_idx, idx_offset] = torch.sum(values * pre_l_weights)

            for idx_offset, var_name in pre_s_indices:
                values = torch.tensor([pre_s_vars.get(f"{var_name}_{suffix}", 0.0)
                                     for suffix in ['A', 'B', 'C', 'D']], device=device)
                input_data[batch_idx, idx_offset] = torch.sum(values * pre_s_weights)

        # 배치 예측 수행 (GPU에서)
        with torch.no_grad():
            predictions = model(input_data)

        # 결과를 CPU로 이동 (마지막에 한 번만)
        return predictions.cpu().numpy()

    except Exception as e:
        st.error(f"MPS 예측 중 오류 발생: {e}")
        return None

def optimize_with_mps(model, li_vars, pre_l_vars, pre_s_vars, material_ratios, base_steps, batch_size=1000):
    """MPS를 활용한 최적화 프로세스 (최적화된 버전)"""
    device = get_device()
    if device.type == "cpu":
        st.warning("MPS를 사용할 수 없어 CPU로 실행됩니다.")
        return None, None

    st.success("Apple M1 GPU(MPS)를 사용하여 최적화를 수행합니다.")

    # 메모리 사용량 모니터링
    memory_metric = st.empty()
    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        # 모델을 GPU로 한 번만 이동
        model = model.to(device)
        model.device = device

        # 조합 생성 (CPU에서 한 번만)
        combinations = generate_combinations(base_steps)
        total_combinations = len(combinations)

        # 결과 저장용 텐서 (GPU에)
        best_prediction = torch.tensor(float('-inf'), device=device)
        best_ratios = None

        # 메모리 효율적인 배치 처리
        for i in range(0, total_combinations, batch_size):
            batch = combinations[i:i+batch_size]

            # 배치 예측 (GPU에서)
            predictions = predict_with_ratios_mps(
                model, li_vars, pre_l_vars, pre_s_vars,
                material_ratios, batch
            )

            # GPU에서 최적값 찾기
            predictions_tensor = torch.tensor(predictions, device=device)
            batch_best_idx = torch.argmax(predictions_tensor)

            if predictions_tensor[batch_best_idx] > best_prediction:
                best_prediction = predictions_tensor[batch_best_idx]
                best_ratios = batch[batch_best_idx]

            # 진행률 업데이트
            progress = (i + len(batch)) / total_combinations
            progress_bar.progress(progress)

            # MPS 메모리 사용량 표시
            memory_used = torch.mps.current_allocated_memory() / 1024**2  # MB 단위
            memory_metric.metric("MPS 메모리 사용량", f"{memory_used:.1f} MB")

            status_text.text(f"진행률: {progress*100:.1f}% (처리된 조합: {i + len(batch)}/{total_combinations})")

            # 메모리 최적화: 불필요한 텐서 제거
            del predictions_tensor
            torch.mps.empty_cache()

        return best_ratios, float(best_prediction.cpu().numpy())

    except Exception as e:
        st.error(f"최적화 중 오류 발생: {e}")
        return None, None

# PyTorch 모델 변환 함수 개선
def convert_model_to_pytorch(original_model):
    """기존 모델을 PyTorch 모델로 변환 (최적화된 버전)"""
    class PyTorchModel(torch.nn.Module):
        def __init__(self, original_model):
            super().__init__()
            self.original_model = original_model
            self.device = None

        def to(self, device):
            self.device = device
            return super().to(device)

        def forward(self, x):
            # 배치 처리 최적화
            if x.device.type == "mps":
                # GPU에서 CPU로 한 번만 이동
                numpy_input = x.cpu().numpy()

                # 모델 타입 확인
                if isinstance(self.original_model, xgb.Booster):
                    # XGBoost 모델
                    try:
                        # numpy 배열을 DataFrame으로 변환 (특성 이름 필요)
                        # 중요: self.original_model.feature_names가 설정되어 있어야 함
                        if hasattr(self.original_model, 'feature_names') and self.original_model.feature_names:
                            input_df = pd.DataFrame(numpy_input, columns=self.original_model.feature_names)
                            dmatrix = xgb.DMatrix(input_df)
                            prediction = self.original_model.predict(dmatrix)
                        else:
                            st.warning("XGBoost 모델에 특성 이름(feature_names)이 설정되지 않아 MPS 예측이 정확하지 않을 수 있습니다.")
                            # 특성 이름 없이 DMatrix 생성 시도 (순서 의존)
                            dmatrix = xgb.DMatrix(numpy_input)
                            prediction = self.original_model.predict(dmatrix)
                    except Exception as e:
                        st.error(f"XGBoost MPS 예측 오류: {e}")
                        # CPU 예측으로 fallback하거나 오류 처리
                        prediction = np.zeros(len(numpy_input)) # 예시: 0으로 반환
                elif hasattr(self.original_model, 'predict'):
                    # CatBoost 또는 다른 Scikit-learn 호환 모델
                    prediction = self.original_model.predict(numpy_input)
                else:
                    st.error(f"지원되지 않는 모델 타입(MPS): {type(self.original_model)}")
                    prediction = np.zeros(len(numpy_input)) # 예시: 0으로 반환

                # 결과를 다시 GPU로
                return torch.tensor(prediction, device=x.device)
            else: # CPU 예측
                numpy_input = x.numpy()
                if isinstance(self.original_model, xgb.Booster):
                    try:
                         # 특성 이름 없이 DMatrix 생성 시도 (순서 의존)
                         # 필요 시 feature_names 추가
                         dmatrix = xgb.DMatrix(numpy_input)
                         prediction = self.original_model.predict(dmatrix)
                    except Exception as e:
                         st.error(f"XGBoost CPU 예측 오류: {e}")
                         prediction = np.zeros(len(numpy_input))
                elif hasattr(self.original_model, 'predict'):
                    prediction = self.original_model.predict(numpy_input)
                else:
                    st.error(f"지원되지 않는 모델 타입(CPU): {type(self.original_model)}")
                    prediction = np.zeros(len(numpy_input))

                return torch.tensor(prediction)

    return PyTorchModel(original_model)

def generate_combinations(base_steps):
    """
    주어진 base_steps에 따라 가능한 모든 ABCD 비율 조합을 생성합니다.

    Args:
        base_steps (int): 0과 1 사이를 몇 개의 스텝으로 나눌지 결정하는 값

    Returns:
        list: 각 재료(Li, Pre_L, Pre_S)에 대한 ABCD 비율 조합을 담은 딕셔너리의 리스트
    """
    import numpy as np

    # 스텝 크기 계산
    step = 1.0 / base_steps

    # 0부터 1까지 step 간격으로 값 생성
    values = np.arange(0, 1 + step, step)

    # 모든 가능한 조합 생성
    combinations = []
    for a in values:
        for b in values:
            for c in values:
                # D는 1-(A+B+C)로 계산
                d = 1 - (a + b + c)
                # 유효한 조합만 선택 (모든 값이 0과 1 사이이고, 합이 1인 경우)
                if d >= 0 and abs(a + b + c + d - 1.0) < 1e-10:
                    ratio = [float(a), float(b), float(c), float(d)]
                    # 각 재료에 대해 동일한 비율 적용
                    combination = {
                        "Li": ratio,
                        "Pre_L": ratio,
                        "Pre_S": ratio
                    }
                    combinations.append(combination)

    return combinations

def run_simulation(model, X_test, y_test, simulation_factors, selected_features):
    """시뮬레이션을 실행하고 결과를 표시합니다."""

    if not model:
        st.error("먼저 모델을 훈련해주세요!")
        return

    st.write("## 🔮 시뮬레이션 실행")

    # 선택된 테스트 데이터 인덱스
    sample_idx = st.slider("테스트 샘플 인덱스 선택:", 0, len(X_test)-1, 0)

    # 선택된 샘플 데이터 출력
    st.write("### 선택된 샘플 데이터")
    sample = X_test.iloc[sample_idx].copy()
    original_pred = model.predict(sample.values.reshape(1, -1))[0]
    actual = y_test.iloc[sample_idx]

    # 샘플 정보 표시
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("원본 예측값", f"{original_pred:.4f}")
    with col2:
        st.metric("실제값", f"{actual:.4f}")
    with col3:
        error = abs(original_pred - actual)
        error_pct = (error / actual) * 100 if actual != 0 else 0
        st.metric("오차 (절대값)", f"{error:.4f}", f"{error_pct:.2f}%")

    # 시뮬레이션할 특성 선택
    st.write("### 시뮬레이션할 특성 선택")

    # 선택된 특성들 표시
    with st.expander("특성 선택 및 입력값 조정"):
        for feature in selected_features:
            if feature in sample:
                min_val = sample[feature] * 0.5
                max_val = sample[feature] * 1.5

                # 0 값은 범위를 다르게 설정
                if sample[feature] == 0:
                    min_val = -1
                    max_val = 1

                # 스텝 크기 계산
                step = (max_val - min_val) / 100

                # 값이 너무 작으면 스텝 크기 조정
                if abs(step) < 0.0001:
                    step = 0.0001

                # 수치 입력 슬라이더
                sample[feature] = st.slider(
                    f"{feature} (원본값: {X_test.iloc[sample_idx][feature]:.4f})",
                    float(min_val), float(max_val), float(sample[feature]),
                    step=float(step)
                )

    # 시뮬레이션 버튼
    if st.button("시뮬레이션 실행"):
        new_pred = model.predict(sample.values.reshape(1, -1))[0]

        # 결과 표시
        st.write("### 시뮬레이션 결과")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("원본 예측값", f"{original_pred:.4f}")
        with col2:
            st.metric("시뮬레이션 예측값", f"{new_pred:.4f}", f"{new_pred - original_pred:.4f}")
        with col3:
            # 변화율 계산
            change_pct = ((new_pred - original_pred) / original_pred) * 100 if original_pred != 0 else 0
            st.metric("변화율", f"{change_pct:.2f}%")

        # 차이를 보여주는 그래프
        st.write("### 예측 결과 비교")

        # 차트 데이터 준비
        chart_data = pd.DataFrame({
            "유형": ["원본 예측", "변경 후 예측", "실제값"],
            "값": [original_pred, new_pred, actual]
        })

        # 색상 맵 설정
        colors = [ECOPRO_COLORS['light_blue'], ECOPRO_COLORS['orange'], ECOPRO_COLORS['dark_blue']]

        # 차트 생성
        fig = px.bar(
            chart_data,
            x="유형",
            y="값",
            color="유형",
            color_discrete_sequence=colors,
            title="예측값 비교"
        )

        # 차트 스타일 업데이트
        fig.update_layout(
            font=dict(color=ECOPRO_COLORS['text']),
            title=dict(
                text="예측값 비교",
                font=dict(color=ECOPRO_COLORS['dark_blue'], size=20)
            ),
            showlegend=False
        )

        st.plotly_chart(fig)

        # 변경된 특성들을 표시
        changed_features = []
        for feature in selected_features:
            if feature in sample and abs(sample[feature] - X_test.iloc[sample_idx][feature]) > 1e-6:
                changed_features.append({
                    "특성": feature,
                    "원본값": X_test.iloc[sample_idx][feature],
                    "변경값": sample[feature],
                    "차이": sample[feature] - X_test.iloc[sample_idx][feature],
                    "변화율(%)": ((sample[feature] - X_test.iloc[sample_idx][feature]) / X_test.iloc[sample_idx][feature] * 100)
                             if X_test.iloc[sample_idx][feature] != 0 else float('inf')
                })

        if changed_features:
            st.write("### 변경된 특성 목록")
            changed_df = pd.DataFrame(changed_features)
            st.dataframe(changed_df.style.format({
                "원본값": "{:.4f}",
                "변경값": "{:.4f}",
                "차이": "{:.4f}",
                "변화율(%)": "{:.2f}%"
            }))

            # 변경된 특성들의 막대 그래프
            st.write("### 특성 변화 시각화")

            # 변화율이 무한대인 경우 처리 (0에서 변경된 경우)
            for i, row in enumerate(changed_features):
                if row["변화율(%)"] == float('inf'):
                    changed_features[i]["변화율(%)"] = 100  # 100%로 표시

            # 막대 그래프를 위한 데이터프레임 생성
            chart_df = pd.DataFrame(changed_features)

            # 특성 변화 막대 그래프
            fig_changes = px.bar(
                chart_df,
                x="특성",
                y="변화율(%)",
                color="변화율(%)",
                title="특성별 변화율 (%)",
                color_continuous_scale=[ECOPRO_COLORS['light_blue'], ECOPRO_COLORS['orange']]
            )

            # 그래프 스타일 업데이트
            fig_changes.update_layout(
                font=dict(color=ECOPRO_COLORS['text']),
                title=dict(
                    text="특성별 변화율 (%)",
                    font=dict(color=ECOPRO_COLORS['dark_blue'], size=20)
                )
            )

            st.plotly_chart(fig_changes)

            # 예측값에 영향을 주는 요인 분석 (간단한 민감도 분석)
            st.write("### 민감도 분석")
            st.write("각 특성의 변화가 예측값에 미치는 영향을 분석합니다.")

            # 민감도 분석 실행
            sensitivity_results = []
            base_sample = X_test.iloc[sample_idx].copy()
            base_pred = model.predict(base_sample.values.reshape(1, -1))[0]

            for feature in selected_features:
                if feature in sample:
                    # 각 특성을 1% 증가시켰을 때의 예측값 변화 계산
                    perturb_sample = base_sample.copy()
                    if perturb_sample[feature] != 0:  # 0이 아닌 경우만 계산
                        perturb_sample[feature] *= 1.01  # 1% 증가
                        perturb_pred = model.predict(perturb_sample.values.reshape(1, -1))[0]
                        pred_change = perturb_pred - base_pred
                        pred_change_pct = (pred_change / base_pred) * 100 if base_pred != 0 else 0

                        # 민감도 계산 (1% 특성 변화에 대한 예측값 변화율)
                        sensitivity = pred_change_pct  # 1% 변화에 대한 % 변화

                        sensitivity_results.append({
                            "특성": feature,
                            "민감도": sensitivity
                        })

            if sensitivity_results:
                # 민감도 결과를 데이터프레임으로 변환
                sens_df = pd.DataFrame(sensitivity_results)

                # 절대값 기준으로 정렬
                sens_df = sens_df.reindex(sens_df['민감도'].abs().sort_values(ascending=False).index)

                # 민감도 막대 그래프
                fig_sens = px.bar(
                    sens_df.head(10),  # 상위 10개만 표시
                    x="특성",
                    y="민감도",
                    color="민감도",
                    title="특성별 민감도 (예측값 변화율 %)",
                    color_continuous_scale=[ECOPRO_COLORS['light_blue'], ECOPRO_COLORS['dark_blue'], ECOPRO_COLORS['orange']]
                )

                # 그래프 스타일 업데이트
                fig_sens.update_layout(
                    font=dict(color=ECOPRO_COLORS['text']),
                    title=dict(
                        text="특성별 민감도 (상위 10개)",
                        font=dict(color=ECOPRO_COLORS['dark_blue'], size=20)
                    )
                )

                st.plotly_chart(fig_sens)

                # 민감도 지표 설명
                st.info("민감도는 각 특성이 1% 변화할 때 예측값의 변화율(%)을 나타냅니다. 절대값이 클수록 해당 특성이 예측에 미치는 영향이 큽니다.")
        else:
            st.info("변경된 특성이 없습니다. 특성값을 조정하고 시뮬레이션을 다시 실행해주세요.")

def show_simple_variable_inputs(selected_record, group_name):
    """단순 변수 입력 UI 생성 (A/B/C/D 비율 없음)"""
    st.markdown(f"### {group_name} 변수 입력")

    # 세션 상태 키
    CURRENT_SIM_MODE = st.session_state["current_sim_mode"]
    run_button_state_key = f"{CURRENT_SIM_MODE}_button_clicked"
    table_state_key = f"simulation_table_data_{group_name}"

    # 원본 레코드 1개 랜덤 로드 상태 확인
    is_new_record = st.session_state["new_record_selected"] if "new_record_selected" in st.session_state else False

    # 랜덤화 컨트롤
    randomize = st.button(f"{group_name} 변수 랜덤화", key=f"random_{group_name.lower()}")

    if randomize:
        # 실행 버튼 클릭 상태 초기화
        st.session_state[run_button_state_key] = False
        if CURRENT_SIM_MODE == "물질 혼합 예측":
            # `물질 혼합 예측` 모드에서 실제 Target_F 값 출력 필요 여부 초기화
            st.session_state["actual_target_f_needed"] = False

    values = {}

    # 테이블 데이터가 이미 세션에 있는지 확인
    # 랜덤화 버튼을 누르지 않았고, 새로운 랜덤 레코드를 선택하지 않았다면 세션에 저장된 데이터 사용
    if not randomize and not is_new_record and table_state_key in st.session_state:
        table_data = st.session_state[table_state_key]
    else:
        # 데이터프레임에서 해당 그룹의 변수 찾기
        var_names = [col for col in selected_record.index if col.startswith(group_name)]

        table_data = []

        # 테이블 데이터 생성
        for var_name in var_names:
            row_data = {"변수명": var_name}

            # 선택된 행 데이터를 사용
            if var_name in selected_record.index:
                value = float(selected_record[var_name])
            else:
                # 이전 형식(Qcp_1) 확인
                old_format_var = f"{var_name[:-1]}_{var_name[-1]}" if var_name[-1].isdigit() else var_name
                if old_format_var in selected_record.index:
                    value = float(selected_record[old_format_var])
                else:
                    # 기본값 설정
                    value = 0.0

            # 분포에 따른 랜덤값 생성
            if randomize:
                min_val, max_val, mean_val, std_val = 0.0, 1.0, 0.5, 0.1

                if st.session_state.get('rand_dist') == "정규 분포 (Normal)":
                    value = float(np.random.normal(mean_val, std_val))
                    value = np.clip(value, min_val, max_val)
                else:  # 균일 분포
                    value = float(np.random.uniform(min_val, max_val))

            row_data["Value"] = value
            values[var_name] = value
            table_data.append(row_data)

        # 테이블 데이터를 세션 상태에 저장
        st.session_state[table_state_key] = table_data

    # 테이블로 표시하고 수정 가능하게 만들기
    edited_df = st.data_editor(
        pd.DataFrame(table_data),
        column_config={
            "변수명": st.column_config.TextColumn(
                "변수명",
                disabled=True,
                width="medium"
            ),
            "Value": st.column_config.NumberColumn(
                "Value",
                min_value=0.0,
                max_value=1.0,
                format="%.4f"
            ),
        },
        hide_index=True,
        on_change=on_change_input_values
    )

    # 수정된 값을 저장
    updated_table_data = []
    for _, row in edited_df.iterrows():
        var_name = row["변수명"]
        value = row["Value"]
        values[var_name] = value
        updated_table_data.append({"변수명": var_name, "Value": value})

    # 업데이트된 테이블 데이터를 세션 상태에 저장
    st.session_state[table_state_key] = updated_table_data

    return values
