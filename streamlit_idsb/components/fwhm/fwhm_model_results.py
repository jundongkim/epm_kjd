import streamlit as st
import os
from components.ai_utils import (
    init_session_state,
    display_analysis_ui,
    generate_ai_analysis
)
import json

def show_model_results(model_dir: str, plot_dir: str, model_type: str):
    """모델 결과 탭 표시"""
    # 세션 상태 초기화
    init_session_state(key_prefix="model_results")
    
    # 선택된 데이터셋 확인
    if 'selected_fwhm_dataset' in st.session_state:
        selected_dataset = st.session_state.selected_fwhm_dataset
    else:
        selected_dataset = "F28"  # 기본값

    st.header(f"{model_type} 모델 결과 (데이터셋: {selected_dataset})")

    # 모델 결과 파일 확인
    if not os.path.exists(plot_dir) or not os.listdir(plot_dir):
        st.warning(f"{selected_dataset} 데이터셋의 {model_type} 모델 결과 파일이 없습니다. 먼저 모델을 학습하세요.")
        return

    # 파일 이름 접두사 설정 (XGBoost는 'xgb_core_')
    file_prefix = "xgb_core_" if model_type == 'XGBoost' else ""

    # 학습 결과 요약 표시
    st.subheader("모델 학습 결과")

    # 학습 곡선
    history_file = f"{plot_dir}/{file_prefix}training_history.html"
    if os.path.exists(history_file):
        st.components.v1.html(open(history_file, 'r', encoding="utf-8").read(), height=650)
    else:
        st.info("학습 곡선 파일 없음")

    # 예측 대 실제 값
    st.subheader("예측 대 실제 값")
    # XGBoost는 xgb_core_prediction_vs_actual.html 이름 사용
    pred_actual_file_name = "xgb_core_prediction_vs_actual.html" if model_type == 'XGBoost' else "prediction_vs_actual.html"
    pred_actual_file = f"{plot_dir}/{pred_actual_file_name}"
    if os.path.exists(pred_actual_file):
        st.components.v1.html(open(pred_actual_file, 'r', encoding="utf-8").read(), height=750)
    else:
        st.info("예측 대 실제 값 파일 없음")

    # 잔차 분석
    st.subheader("잔차 분석")
    residual_file = f"{plot_dir}/{file_prefix}residual_analysis.html"
    if os.path.exists(residual_file):
        st.components.v1.html(open(residual_file, 'r', encoding="utf-8").read(), height=850)
    else:
        st.info("잔차 분석 파일 없음")

    # 특성 중요도
    st.subheader("특성 중요도")
    feature_imp_file = f"{plot_dir}/{file_prefix}feature_importance.html"
    if os.path.exists(feature_imp_file):
        st.components.v1.html(open(feature_imp_file, 'r', encoding="utf-8").read(), height=850)
    else:
        st.info("특성 중요도 파일 없음")

    # 특성 유형별 중요도
    st.subheader("특성 유형별 중요도")
    feature_type_imp_file = f"{plot_dir}/{file_prefix}feature_type_importance.html"
    if os.path.exists(feature_type_imp_file):
        st.components.v1.html(open(feature_type_imp_file, 'r', encoding="utf-8").read(), height=650)
    else:
        st.info("특성 유형별 중요도 파일 없음")

    # AI 분석 요약
    st.subheader("🤖 iDSB AI 모델 분석 요약")

    # 모델 결과 JSON 파일 로드
    results_data = None
    results_filename = f"{model_type.lower()}_results.json"
    results_file_path = os.path.join(model_dir, results_filename)
    
    if os.path.exists(results_file_path):
        try:
            with open(results_file_path, 'r', encoding='utf-8') as f:
                results_data = json.load(f)
            st.info(f"모델 결과 요약 정보 ({results_filename}) 로드 완료.")
        except Exception as e:
            st.warning(f"모델 결과 요약 파일 ({results_filename}) 로드 중 오류: {e}")
            results_data = None # 오류 발생 시 None으로 설정
    else:
        st.warning(f"모델 결과 요약 파일 ({results_filename})을 찾을 수 없습니다. AI 분석은 시각화 자료 기반으로만 진행됩니다.")

    # 분석 정보 수집
    analysis_info = {
        "모델_유형": f"{model_type} 회귀 모델",
        "시각화_유형_참고용": [ # Renamed to indicate it's for reference only
            "학습 곡선",
            "예측 대 실제 값",
            "잔차 분석",
            "특성 중요도",
            "특성 유형별 중요도"
        ],
        "모델_성능_및_주요_특성": results_data if results_data else "결과 요약 데이터 없음"
    }

    # --- 프롬프트 생성 로직 수정 --- 
    prompt = "" # Initialize prompt string
    if results_data:
        # Extract key data points from the loaded JSON
        try:
            eval_metrics = results_data.get("evaluation_metrics", {})
            r_squared = eval_metrics.get("R-squared", "N/A")
            mae = eval_metrics.get("MAE", "N/A")
            rmse = eval_metrics.get("RMSE", "N/A")
            mape = eval_metrics.get("MAPE", "N/A")

            learning_summary = results_data.get("learning_curve_summary", {})
            final_train_loss = learning_summary.get("final_training_loss (MAE)", "N/A")
            final_val_loss = learning_summary.get("final_validation_loss (MAE)", "N/A")
            best_iter = learning_summary.get("best_iteration", "N/A")

            residual_summary = results_data.get("residual_analysis_summary", {})
            residual_mean = residual_summary.get("mean", "N/A")
            residual_std = residual_summary.get("standard_deviation", "N/A")
            shapiro_p = residual_summary.get("shapiro_wilk_p_value", "N/A")

            feature_imp = results_data.get("feature_importance", {})
            top_10_features_dict = feature_imp.get("top_10_features", {})
            type_importance_dict = feature_imp.get("type_importance", {})
            
            # --- 수정: 중요도 정보를 쉼표 구분 문자열로 포맷 (소수점 2자리 반올림) ---
            top_10_features_str = ", ".join([f"{feat}: {imp:.2f}" for feat, imp in top_10_features_dict.items()])
            if not top_10_features_str:
                top_10_features_str = "상위 특성 정보 없음"

            type_importance_str = ", ".join([f"{ftype}: {imp:.2f}" for ftype, imp in type_importance_dict.items()])
            if not type_importance_str:
                type_importance_str = "유형별 중요도 정보 없음"
            # --- 수정 끝 ---
                
            # Format numeric values nicely or handle N/A
            r_squared_str = f"{r_squared:.2f}" if isinstance(r_squared, (int, float)) else "N/A" # 반올림 통일
            mae_str = f"{mae:.2f}" if isinstance(mae, (int, float)) else "N/A"         # 반올림 통일
            rmse_str = f"{rmse:.2f}" if isinstance(rmse, (int, float)) else "N/A"       # 반올림 통일
            mape_str = f"{mape:.2f}%" if isinstance(mape, (int, float)) else "N/A"     # MAPE 문자열 포맷팅
            final_train_loss_str = f"{final_train_loss:.2f}" if isinstance(final_train_loss, (int, float)) else "N/A" # 반올림 통일
            final_val_loss_str = f"{final_val_loss:.2f}" if isinstance(final_val_loss, (int, float)) else "N/A"   # 반올림 통일
            residual_mean_str = f"{residual_mean:.2f}" if isinstance(residual_mean, (int, float)) else "N/A"    # 반올림 통일
            residual_std_str = f"{residual_std:.2f}" if isinstance(residual_std, (int, float)) else "N/A"      # 반올림 통일
            shapiro_p_str = f"{shapiro_p:.2f}" if isinstance(shapiro_p, (int, float)) else ("정보 없음" if shapiro_p is None else str(shapiro_p))

            # Construct the detailed prompt with embedded values
            prompt = f"""
            **{model_type} 모델 성능 분석 전문가 리포트 요청**

            {model_type} 모델의 학습 및 평가 결과 주요 수치를 분석하여, 전문적인 리포트를 마크다운 형식으로 작성해주십시오.
            **주의: 실제 시각화 자료는 볼 수 없으므로, 아래 제공된 수치 데이터와 설명을 바탕으로만 분석해야 합니다.**
            **리포트는 아래 제공된 각 섹션의 실제 수치를 명시적으로 인용하고, 그 의미를 비전문가도 이해하기 쉽게 상세히 설명해야 합니다.**

            **[모델 성능 요약 지표]**
            - R-squared: {r_squared_str}
            - MAE: {mae_str}
            - RMSE: {rmse_str}
            - MAPE: {mape_str}

            **[학습 과정 요약]**
            - 최종 학습 손실 (MAE): {final_train_loss_str}
            - 최종 검증 손실 (MAE): {final_val_loss_str}
            - 최적 반복 횟수 (Best Iteration): {best_iter}

            **[잔차 분석 요약]**
            - 잔차 평균: {residual_mean_str}
            - 잔차 표준편차: {residual_std_str}
            - 잔차 정규성 (Shapiro-Wilk p-value): {shapiro_p_str} (p > 0.05 이면 정규성 만족으로 간주)

            **[특성 중요도 요약]**
            - 상위 10개 중요 특성 (특성명: 중요도 점수): {top_10_features_str}
            - 특성 유형별 총 중요도 (유형명: 총 중요도 점수): {type_importance_str}

            **리포트 작성 지침:**

            1.  **모델 성능 요약:**
                *   위 **[모델 성능 요약 지표]**의 **R-squared({r_squared_str}), MAE({mae_str}), RMSE({rmse_str}), MAPE({mape_str}) 값을 명시**하고, 이 값들이 모델의 전반적인 예측 정확도를 어떻게 나타내는지 **쉽게 설명**해주십시오.

            2.  **학습 과정 분석:**
                *   **[학습 과정 요약]**의 **최종 학습 손실({final_train_loss_str})과 최종 검증 손실({final_val_loss_str})을 비교**하여 모델의 학습 안정성, 과적합/과소적합 여부를 판단하고 **근거를 설명**해주십시오.
                *   (XGBoost의 경우) **최적 반복 횟수({best_iter})** 정보를 활용하여 조기 종료가 적절했는지 평가해주십시오.

            3.  **예측 정확도 및 경향성 분석:**
                *   **R-squared 값({r_squared_str})을 바탕으로** 모델의 전반적인 예측 정확도를 평가해주십시오. (참고: 실제 산점도 패턴은 볼 수 없음)

            4.  **잔차 분석 해석:**
                *   **[잔차 분석 요약]**의 **잔차 평균({residual_mean_str})이 0에 가까운지, 표준편차({residual_std_str})가 작은지, Shapiro-Wilk p-값({shapiro_p_str})이 유의수준(0.05)보다 커서 정규성을 만족하는지** 등을 평가하고, 이것이 모델 예측 오차의 특성(편향성, 분포 등) 및 신뢰도에 어떤 의미를 갖는지 설명해주십시오.

            5.  **중요 특성 분석:**
                *   **[특성 중요도 요약]에 제시된 상위 10개 중요 특성 문자열 '{top_10_features_str}' 에서 각 특성의 이름과 중요도 점수를 추출하여 리스트(예: 마크다운 목록) 형태로 명확히 나열**하고, 어떤 특성들이 {model_type} 모델의 반가폭 예측에 가장 큰 영향을 미치는지 설명해주십시오.
                *   **[특성 중요도 요약]**의 **유형별 총 중요도 문자열 '{type_importance_str}' 에서 각 유형과 해당 총 중요도 값을 추출하여 제시**하고, **어떤 공정 그룹(Li, Pre_L 등)의 특성들이 전반적으로 더 중요하게 작용했는지 구체적인 수치를 들어** 분석해주십시오.

            6.  **모델 개선 제안 (선택 사항):**
                *   지금까지 분석한 **수치 데이터**를 바탕으로, 모델 성능을 더욱 향상시키기 위한 구체적인 제안(예: 중요도가 낮은 특성 제거 고려, 특정 유형 특성 추가 탐색 등)이 있다면 제시해주십시오.

            7.  **종합 평가:**
                *   모델의 전반적인 성능, 안정성, 예측 신뢰도, 주요 영향 요인 등을 **위에 제시된 핵심 수치들을 종합하여** 평가하고, 현업 적용 가능성에 대한 의견을 제시해주십시오.

            **요구사항:**
            *   마크다운 형식 사용 및 명확한 섹션 구분.
            *   전문적이고 간결한 용어 사용 + **쉬운 설명** 병기.
            *   **위에 제시된 수치 데이터에 철저히 근거**하여 작성.
            *   중요 내용은 **볼드체**로 강조.
            """
        except Exception as e:
             st.error(f"결과 데이터 처리 중 오류 발생: {e}")
             prompt = f"오류: {model_type} 모델 결과 데이터를 처리하는 중 문제가 발생했습니다. AI 분석을 진행할 수 없습니다." 

    else: # results_data가 로드되지 않았거나 없는 경우
        st.warning(f"{model_type} 모델 결과 요약 파일({results_filename}) 로드 실패. AI 분석을 진행할 수 없습니다.")
        prompt = f"{model_type} 모델 결과 요약 파일이 없어 AI 분석을 진행할 수 없습니다." # 빈 프롬프트 또는 안내 메시지

    # --- 프롬프트 생성 로직 끝 ---

    # 분석 UI 표시 및 처리
    # (display_analysis_ui 호출 로직은 거의 동일하게 유지, 단 prompt 유효성 체크 추가 가능)
    if prompt and "오류" not in prompt and "없습니다" not in prompt: # 유효한 프롬프트가 생성된 경우에만 UI 표시
        try:
            is_running = display_analysis_ui(
                prompt=prompt,
                button_label="모델 분석 시작",
                key_prefix="model_results",
                info_message="AI 모델 분석을 실행하려면 \'모델 분석 시작\' 버튼을 클릭하세요."
            )

            if is_running:
                with st.chat_message("assistant"):
                    message_placeholder = st.empty()
                    metadata_placeholder = st.empty()
                    with st.spinner("AI가 모델 결과를 분석하고 있습니다..."):
                        generate_ai_analysis(
                            prompt=prompt,
                            key_prefix="model_results",
                            message_placeholder=message_placeholder,
                            metadata_placeholder=metadata_placeholder
                        )
        except Exception as e:
            st.error(f"AI 모델 분석 생성 중 오류가 발생했습니다: {str(e)}")
    elif "오류" in prompt or "없습니다" in prompt:
        # 이미 warning/error가 표시되었으므로 추가 작업 불필요 또는 간단한 메시지 표시
        pass # st.info("AI 분석을 위한 데이터가 부족합니다.")