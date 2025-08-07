import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff
from scipy import stats
from ..utils import get_equipment_type, get_sensor_type
from ..utils.style import load_iot_font_css, apply_custom_style
from ..utils.ai_utils import init_session_state, display_analysis_ui, generate_ai_response, display_chat_interface
from ..utils.ai_settings import render_ai_settings_ui, init_ai_settings
import json

def render_distribution_ui(df_processed):
    """분포 비교 시각화 UI를 렌더링합니다."""
    # 폰트 적용
    load_iot_font_css()
    apply_custom_style()
    
    st.subheader("그룹별 분포 비교")
    
    # 센서 컬럼 이름 가져오기
    sensor_col = get_sensor_type()
    if sensor_col not in df_processed.columns:
        sensor_col = "value"  # 기본값으로 fallback
    
    # 센서 타입 표시용 이름
    sensor_type_display = sensor_col
    
    # 분포 비교 옵션
    group_var = st.selectbox(
        "그룹화 기준",
        ["월", "요일", "시간대", "분기", "주말/평일"]
    )
    
    # 데이터 준비
    df_groups = df_processed.copy()
    
    # 그룹화 기준에 따라 설정
    if group_var == "월":
        group_col = 'month'
        group_labels = [f"{i}월" for i in range(1, 13)]
        group_values = list(range(1, 13))
    elif group_var == "요일":
        group_col = 'day_name'
        group_labels = ['월', '화', '수', '목', '금', '토', '일']
        group_values = ['월', '화', '수', '목', '금', '토', '일']
    elif group_var == "시간대":
        group_col = 'time_of_day'
        time_labels = ['새벽(0-6시)', '오전(6-12시)', '오후(12-18시)', '저녁(18-24시)']
        group_labels = time_labels
        group_values = time_labels
    elif group_var == "분기":
        group_col = 'quarter'
        group_labels = [f"Q{i}" for i in range(1, 5)]
        group_values = list(range(1, 5))
    else:  # "주말/평일"
        group_col = 'is_weekend'
        group_labels = ['평일', '주말']
        group_values = ['평일', '주말']
    
    # 분포 비교 시각화 방법 선택
    compare_method = st.radio(
        "비교 방식",
        ["히스토그램", "커널 밀도", "누적 분포", "박스플롯", "바이올린"]
    )
    
    # 그룹별 데이터 준비
    groups = []
    valid_group_labels = []
    
    for val, label in zip(group_values, group_labels):
        if group_col in ['month', 'quarter']:
            group_data = df_groups[df_groups[group_col] == val][sensor_col]
        else:
            group_data = df_groups[df_groups[group_col] == val][sensor_col]
        
        # 데이터가 있는 그룹만 추가
        if len(group_data) > 0:
            # 데이터가 너무 많으면 샘플링
            if len(group_data) > 10000:
                group_data = group_data.sample(10000)
            
            groups.append(group_data)
            valid_group_labels.append(label)
    
    # 시각화 생성
    fig = go.Figure()
    
    # 선택된 방법에 따라 시각화
    if compare_method == "히스토그램":
        for i, (group_data, label) in enumerate(zip(groups, valid_group_labels)):
            fig.add_trace(go.Histogram(
                x=group_data,
                name=label,
                opacity=0.7,
                nbinsx=30
            ))
        
        fig.update_layout(
            barmode='overlay',
            title=f"{group_var}별 {sensor_type_display} 히스토그램 비교",
            xaxis_title=f"{sensor_type_display} 값",
            yaxis_title="빈도",
            height=500
        )
        
    elif compare_method == "커널 밀도":
        for i, (group_data, label) in enumerate(zip(groups, valid_group_labels)):
            if len(group_data.dropna()) > 0:
                # KDE 계산
                kde = stats.gaussian_kde(group_data.dropna())
                x_vals = np.linspace(group_data.min(), group_data.max(), 1000)
                y_vals = kde(x_vals)
                
                # 플롯 추가
                fig.add_trace(go.Scatter(
                    x=x_vals,
                    y=y_vals,
                    mode='lines',
                    name=label,
                    line=dict(width=2)
                ))
        
        fig.update_layout(
            title=f"{group_var}별 {sensor_type_display} 밀도 비교",
            xaxis_title=f"{sensor_type_display} 값",
            yaxis_title="밀도",
            height=500
        )
        
    elif compare_method == "누적 분포":
        for i, (group_data, label) in enumerate(zip(groups, valid_group_labels)):
            # 누적 분포 계산
            sorted_data = np.sort(group_data)
            cumulative = np.arange(1, len(sorted_data) + 1) / len(sorted_data)
            
            fig.add_trace(go.Scatter(
                x=sorted_data,
                y=cumulative,
                mode='lines',
                name=label,
                line=dict(width=2)
            ))
        
        fig.update_layout(
            title=f"{group_var}별 {sensor_type_display} 누적 분포 비교",
            xaxis_title=f"{sensor_type_display} 값",
            yaxis_title="누적 확률",
            height=500
        )
        
    elif compare_method == "박스플롯":
        for i, (group_data, label) in enumerate(zip(groups, valid_group_labels)):
            fig.add_trace(go.Box(
                y=group_data,
                name=label,
                boxmean=True
            ))
        
        fig.update_layout(
            title=f"{group_var}별 {sensor_type_display} 박스플롯 비교",
            yaxis_title=f"{sensor_type_display} 값",
            height=500
        )
        
    else:  # "바이올린"
        for i, (group_data, label) in enumerate(zip(groups, valid_group_labels)):
            fig.add_trace(go.Violin(
                y=group_data,
                name=label,
                box_visible=True,
                meanline_visible=True
            ))
        
        fig.update_layout(
            title=f"{group_var}별 {sensor_type_display} 바이올린 플롯 비교",
            yaxis_title=f"{sensor_type_display} 값",
            height=500
        )
    
    # 차트 표시
    st.plotly_chart(fig, use_container_width=True)
    
    # 통계적 검정 결과를 저장할 변수
    test_results = None
    shapiro_results = None
    
    # 통계적 검정
    with st.expander("통계적 검정"):
        st.write("#### 그룹 간 차이 검정")
        
        # 검정 방법 선택
        test_method = st.selectbox(
            "검정 방법",
            ["ANOVA (분산 분석)", "Kruskal-Wallis (비모수 검정)"]
        )
        
        try:
            if len(groups) < 2:
                st.warning("통계적 검정을 위한 유효한 그룹이 부족합니다.")
            else:
                # 빈 그룹이 있는지 확인하고 데이터가 있는 그룹만 사용
                valid_groups = [group.dropna() for group in groups if len(group.dropna()) > 0]
                valid_labels = [label for i, label in enumerate(valid_group_labels) if len(groups[i].dropna()) > 0]
                
                if test_method == "ANOVA (분산 분석)":
                    # ANOVA 수행
                    if len(valid_groups) >= 2:  # 최소 2개 이상의 그룹이 필요
                        f_stat, p_val = stats.f_oneway(*valid_groups)
                        
                        st.write(f"ANOVA 결과: F = {f_stat:.4f}, p-value = {p_val:.4e}")
                        
                        # 검정 결과 저장
                        test_results = {
                            "method": "ANOVA (분산 분석)",
                            "statistic": f_stat,
                            "p_value": p_val,
                            "significant": p_val < 0.05
                        }
                        
                        if p_val < 0.05:
                            st.write("결론: 그룹 간 통계적으로 유의미한 차이가 있습니다 (p < 0.05)")
                            
                            # 사후 검정 (Tukey's HSD)
                            try:
                                from statsmodels.stats.multicomp import pairwise_tukeyhsd
                                
                                st.write("#### 사후 검정 (그룹 간 쌍별 비교)")
                                
                                # 데이터 준비
                                post_hoc_data = []
                                group_names = []
                                
                                for i, (group_data, label) in enumerate(zip(valid_groups, valid_labels)):
                                    post_hoc_data.extend(group_data.values)
                                    group_names.extend([label] * len(group_data))
                                
                                # Tukey's HSD 수행
                                tukey_result = pairwise_tukeyhsd(
                                    np.array(post_hoc_data),
                                    np.array(group_names),
                                    alpha=0.05
                                )
                                
                                # 결과 출력
                                tukey_df = pd.DataFrame(
                                    data=tukey_result._results_table.data[1:],
                                    columns=tukey_result._results_table.data[0]
                                )
                                
                                st.dataframe(tukey_df)
                                
                                # 유의미한 차이가 있는 그룹 쌍 찾기
                                significant_pairs = tukey_df[tukey_df['p-adj'] < 0.05]
                                
                                # 사후 검정 결과 저장
                                post_hoc_results = []
                                if len(significant_pairs) > 0:
                                    st.write("#### 유의미한 차이가 있는 그룹 쌍:")
                                    for _, row in significant_pairs.iterrows():
                                        st.write(f"- {row['group1']} vs {row['group2']}: 차이 = {row['meandiff']:.4f}, p = {row['p-adj']:.4e}")
                                        post_hoc_results.append({
                                            "group1": row['group1'],
                                            "group2": row['group2'],
                                            "diff": row['meandiff'],
                                            "p": row['p-adj']
                                        })
                                
                                # 사후 검정 결과 저장
                                if post_hoc_results:
                                    test_results["post_hoc"] = post_hoc_results
                                
                            except ImportError:
                                st.warning("사후 검정을 위해 statsmodels 패키지가 필요합니다.")
                            except Exception as e:
                                st.error(f"사후 검정 중 오류가 발생했습니다: {str(e)}")
                        else:
                            st.write("결론: 그룹 간 통계적으로 유의미한 차이가 없습니다 (p >= 0.05)")
                    else:
                        st.warning("ANOVA 분석을 위한 유효한 그룹이 충분하지 않습니다.")
                
                else:  # Kruskal-Wallis
                    # Kruskal-Wallis 수행
                    if len(valid_groups) >= 2:
                        h_stat, p_val = stats.kruskal(*valid_groups)
                        
                        st.write(f"Kruskal-Wallis 결과: H = {h_stat:.4f}, p-value = {p_val:.4e}")
                        
                        # 검정 결과 저장
                        test_results = {
                            "method": "Kruskal-Wallis (비모수 검정)",
                            "statistic": h_stat,
                            "p_value": p_val,
                            "significant": p_val < 0.05
                        }
                        
                        if p_val < 0.05:
                            st.write("결론: 그룹 간 통계적으로 유의미한 차이가 있습니다 (p < 0.05)")
                            
                            # Mann-Whitney U test로 pairwise 비교 (사후 검정 대체)
                            st.write("#### 그룹 간 개별 비교 (Mann-Whitney U)")
                            
                            # 그룹 쌍 생성
                            post_hoc_results = []
                            for i in range(len(valid_groups)):
                                for j in range(i+1, len(valid_groups)):
                                    # Mann-Whitney U test
                                    u_stat, p_val_mw = stats.mannwhitneyu(
                                        valid_groups[i], 
                                        valid_groups[j],
                                        alternative='two-sided'
                                    )
                                    
                                    # Bonferroni 보정 (다중 비교 문제 해결)
                                    alpha_bonferroni = 0.05 / (len(valid_groups) * (len(valid_groups) - 1) / 2)
                                    
                                    st.write(f"- {valid_labels[i]} vs {valid_labels[j]}: ")
                                    st.write(f"  U = {u_stat:.1f}, p = {p_val_mw:.4e}")
                                    
                                    # 사후 검정 결과 저장
                                    is_significant = p_val_mw < alpha_bonferroni
                                    post_hoc_results.append({
                                        "group1": valid_labels[i],
                                        "group2": valid_labels[j],
                                        "diff": u_stat,  # Mann-Whitney U 통계량
                                        "p": p_val_mw,
                                        "significant_bonferroni": is_significant,
                                        "significant_raw": p_val_mw < 0.05
                                    })
                                    
                                    if is_significant:
                                        st.write(f"  결론: 유의미한 차이 있음 (Bonferroni 보정 적용)")
                                    elif p_val_mw < 0.05:
                                        st.write(f"  결론: 유의미한 차이 있음 (보정 전)")
                                    else:
                                        st.write(f"  결론: 유의미한 차이 없음")
                            
                            # 사후 검정 결과 저장
                            if post_hoc_results:
                                test_results["post_hoc"] = post_hoc_results
                        else:
                            st.write("결론: 그룹 간 통계적으로 유의미한 차이가 없습니다 (p >= 0.05)")
                    else:
                        st.warning("Kruskal-Wallis 검정을 위한 유효한 그룹이 충분하지 않습니다.")
        
        except Exception as e:
            st.error(f"통계적 검정 중 오류가 발생했습니다: {str(e)}")
    
    # 분포 적합성 분석
    with st.expander("분포 적합성 분석", expanded=False):
        st.write("#### 데이터 분포 특성 분석")
        
        # 백분위수 표시
        percentiles = [0.1, 1, 5, 10, 25, 50, 75, 90, 95, 99, 99.9]
        percentile_values = np.percentile(df_processed[sensor_col], percentiles)
        
        percentile_df = pd.DataFrame({
            '백분위수': [f"{p}%" for p in percentiles],
            '값': percentile_values
        })
        
        st.dataframe(percentile_df)
        
        # 정규성 검정 결과
        try:
            # Shapiro-Wilk test (sample)
            shapiro_sample = df_processed[sensor_col].sample(min(5000, len(df_processed)))
            shapiro_stat, shapiro_p = stats.shapiro(shapiro_sample)
            
            st.write("#### 정규성 검정 (Shapiro-Wilk)")
            st.write(f"통계량: {shapiro_stat:.4f}, p-value: {shapiro_p:.4e}")
            
            # 정규성 검정 결과 저장
            shapiro_results = {
                "statistic": shapiro_stat,
                "p_value": shapiro_p,
                "is_normal": shapiro_p >= 0.05
            }
            
            if shapiro_p < 0.05:
                st.write("결론: 데이터가 정규 분포를 따르지 않습니다 (p < 0.05)")
                st.write("*비모수적 통계 방법을 사용하는 것이 적합할 수 있습니다.*")
            else:
                st.write("결론: 데이터가 정규 분포를 따를 가능성이 있습니다 (p >= 0.05)")
                st.write("*모수적 통계 방법을 사용하는 것이 적합할 수 있습니다.*")
        except Exception as e:
            st.error(f"정규성 검정을 수행할 수 없습니다: {str(e)}")
    
    # AI 분석 부분 호출
    render_ai_analysis(
        df=df_processed,
        group_var=group_var,
        compare_method=compare_method,
        valid_group_labels=valid_group_labels,
        groups=groups,
        sensor_type_display=sensor_type_display,
        test_results=test_results,
        shapiro_results=shapiro_results
    )

def render_ai_analysis(df, group_var, compare_method, valid_group_labels, groups, sensor_type_display, test_results=None, shapiro_results=None):
    """분포 비교 분석을 위한 AI 분석 부분을 구현합니다."""
    # 세션 상태 초기화 (AI 분석용)
    from ..utils.ai_settings import init_ai_settings
    init_ai_settings()  # 먼저 AI 설정 초기화
    
    # 장비 유형 가져오기
    equipment_type = get_equipment_type(df)
    
    # 분포 분석 전용 키 접두사 사용
    key_prefix = "distribution_analysis"
    init_session_state(key_prefix=key_prefix)
    
    # 현재 비교 방법을 세션 상태에 저장
    current_method_key = f"{key_prefix}_current_method"
    
    # 비교 방법이 변경되었는지 확인
    method_changed = False
    if current_method_key in st.session_state:
        if st.session_state[current_method_key] != compare_method:
            method_changed = True
    else:
        # 최초 실행 시
        method_changed = True
    
    # 현재 방법 업데이트
    st.session_state[current_method_key] = compare_method
    
    # AI 분석 프롬프트 키
    dist_prompt_key = f"{key_prefix}_specific_prompt"
    
    # 비교 방법이 변경되었거나 프롬프트가 없으면 새로 생성
    if method_changed or dist_prompt_key not in st.session_state:
        # 비교 방법에 대한 설명 추가
        method_description = ""
        method_context = ""
        
        if compare_method == "히스토그램":
            method_description = "히스토그램은 데이터의 빈도 분포를 시각화하는 방법으로, 데이터가 특정 범위에 얼마나 분포되어 있는지 확인할 수 있습니다."
            method_context = "히스토그램은 데이터의 전반적인 분포 형태, 중심 경향성, 이상치 존재 여부 등을 파악하는 데 유용합니다."
        elif compare_method == "커널 밀도":
            method_description = "커널 밀도 추정은 데이터의 확률 밀도 함수를 부드럽게 추정하는 방법으로, 연속적인 분포 형태를 보여줍니다."
            method_context = "커널 밀도는 히스토그램보다 부드러운 곡선으로 표현되어 다중 모드(여러 봉우리)가 있는 분포를 식별하기 쉽습니다."
        elif compare_method == "누적 분포":
            method_description = "누적 분포 함수(CDF)는 특정 값 이하의 데이터 비율을 보여주는 그래프로, 분포의 누적된 확률을 나타냅니다."
            method_context = "누적 분포는 특정 값에 대한 백분위수를 쉽게 파악할 수 있으며, 분포 간의 위치 차이를 명확하게 보여줍니다."
        elif compare_method == "박스플롯":
            method_description = "박스플롯은 데이터의 사분위수, 중앙값, 이상치 등 데이터의 분포 특성을 요약해서 보여주는 시각화 방법입니다."
            method_context = "박스플롯은 여러 그룹의 분포를 비교하기에 적합하며, 중앙 경향성과 퍼짐 정도를 한눈에 파악할 수 있습니다."
        else:  # "바이올린"
            method_description = "바이올린 플롯은 박스플롯과 커널 밀도 추정을 결합한 방법으로, 데이터의 분포 형태와 통계적 요약을 모두 보여줍니다."
            method_context = "바이올린 플롯은 데이터의 밀도 정보를 제공하여 다중 모드 분포나 비대칭 분포 등 복잡한 분포 특성을 파악하는 데 유용합니다."
            
        # 그룹별 통계 요약 및 시각화 컨텍스트 추가
        group_stats = []
        for i, (group_data, label) in enumerate(zip(groups, valid_group_labels)):
            if len(group_data) > 0:
                group_stats.append({
                    "label": label,
                    "count": len(group_data),
                    "mean": group_data.mean(),
                    "median": group_data.median(),
                    "std": group_data.std(),
                    "min": group_data.min(),
                    "max": group_data.max(),
                    "q1": group_data.quantile(0.25),
                    "q3": group_data.quantile(0.75)
                })
                
        # 통계 검정 결과 추가
        test_summary = ""
        if test_results:
            test_method = test_results.get("method", "")
            test_stat = test_results.get("statistic", "")
            test_p = test_results.get("p_value", "")
            test_sig = test_results.get("significant", False)
            
            test_summary = f"""
통계 검정 방법: {test_method}
통계량: {test_stat:.4f}
p-value: {test_p:.4e}
결론: {'그룹 간 통계적으로 유의미한 차이가 있습니다' if test_sig else '그룹 간 통계적으로 유의미한 차이가 없습니다'}
"""
            
            # 사후 검정 정보 추가
            if test_sig and "post_hoc" in test_results:
                test_summary += "\n사후 검정 결과:\n"
                for pair in test_results["post_hoc"]:
                    test_summary += f"- {pair['group1']} vs {pair['group2']}: 차이 = {pair['diff']:.4f}, p = {pair['p']:.4e}\n"
        
        # 정규성 검정 결과 추가
        normality_summary = ""
        if shapiro_results:
            shapiro_stat = shapiro_results.get("statistic", "")
            shapiro_p = shapiro_results.get("p_value", "")
            shapiro_norm = shapiro_results.get("is_normal", False)
            
            normality_summary = f"""
정규성 검정 (Shapiro-Wilk):
통계량: {shapiro_stat:.4f}
p-value: {shapiro_p:.4e}
결론: {'데이터가 정규 분포를 따를 가능성이 있습니다' if shapiro_norm else '데이터가 정규 분포를 따르지 않습니다'}
"""
        
        # 분석 데이터의 통계 및 특성 요약
        stats_summary = f"""
- 장비 유형: {equipment_type}
- 센서 유형: {sensor_type_display}
- 비교 그룹 기준: {group_var}
- 비교 방법: {compare_method} ({method_description})
- 유효 그룹 수: {len(valid_group_labels)}개
- 유효 그룹: {', '.join(valid_group_labels)}
"""
        
        # 그룹별 통계 요약 추가
        if group_stats:
            stats_summary += "\n그룹별 통계 요약:\n"
            for stat in group_stats:
                stats_summary += f"""* {stat['label']}:
  - 개수: {stat['count']}
  - 평균: {stat['mean']:.4f}
  - 중앙값: {stat['median']:.4f}
  - 표준편차: {stat['std']:.4f}
  - 범위: {stat['min']:.4f} ~ {stat['max']:.4f}
  - IQR: {stat['q1']:.4f} ~ {stat['q3']:.4f}
"""
        
        # 통계 검정 결과 추가
        if test_summary:
            stats_summary += f"\n통계 검정 결과:\n{test_summary}"
            
        # 정규성 검정 결과 추가
        if normality_summary:
            stats_summary += f"\n정규성 검정 결과:\n{normality_summary}"
            
        # 시스템 프롬프트 부분 추가
        system_prompt = f"""당신은 IoT 센서 데이터 분석 전문가입니다. 다양한 그룹별 데이터 분포 비교 분석을 통해 인사이트를 제공합니다.

분석 중인 데이터는 {equipment_type}의 {sensor_type_display} 값으로, {compare_method} 방법으로 {group_var}별 분포를 비교 분석하였습니다.
이 분석은 {method_description}

분석 컨텍스트: {method_context}

주요 분석 포인트:
1. 그룹별 분포의 주요 특성 비교 (중심 경향성, 분산, 형태)
2. 그룹 간 통계적 차이의 유의성과 실제적 의미
3. 센서 값의 그룹별 패턴과 특이사항
4. 이상치 또는 특이 패턴이 있는 그룹 식별
5. 장비 운영 최적화를 위한 실용적인 인사이트
"""
        
        # 분석 프롬프트 생성
        analysis_prompt = f"""{system_prompt}

다음은 IoT {sensor_type_display} 데이터의 {group_var}별 분포 비교 분석 결과입니다.

## 데이터 정보
{stats_summary}

## 분석 과제
위 분포 비교 분석 데이터에 대한 인사이트를 마크다운 형식으로 제공해주세요. 다음 내용을 포함해주세요:

1. {group_var}별 {sensor_type_display} 분포의 주요 특성 파악
   - 각 그룹의 분포 형태 (정규 분포, 치우침, 다중 모드 등)
   - 그룹별 중심 경향성(평균, 중앙값)과 분산 비교
   - 이상치 존재 여부와 특이 그룹 식별

2. 통계적 차이의 유의성 해석
   - 통계 검정 결과의 의미와 실용적 관점에서의 중요성
   - 사후 검정 결과에 따른 그룹 간 차이의 구체적 패턴
   - 통계적으로 유의한 차이가 있는 그룹 쌍의 실질적 의미

3. {group_var}에 따른 {sensor_type_display} 값의 패턴 분석
   - 주요 패턴(시간대별, 요일별, 월별 등)의 원인과 의미
   - 특정 그룹에서 나타나는 특이 현상 설명
   - 분포 형태가 센서의 작동 환경 또는 장비 상태와 관련된 인사이트

4. 정규성 검정 결과의 활용
   - 데이터의 정규/비정규 분포 특성이 분석에 미치는 영향
   - 적절한 통계적 방법 선택에 대한 제안
   - 비정규 분포인 경우 가능한 변환 방법이나 대안적 분석 접근법

5. 장비 운영 최적화를 위한 실용적인 제안
   - 분포 분석에 기반한 최적의 운영 조건 제시
   - 특정 그룹에서 성능 향상을 위한 구체적인 권장사항
   - 이상 상황이 발생할 가능성이 높은 조건과 예방 조치

결과는 명확하고 간결하게 작성하고, 중요한 사항은 **볼드체**로 강조해주세요. 특히 그룹 간의 실제 통계값 차이를 언급하여 인사이트에 신뢰성을 더해주세요.
"""
        # 분포 분석 전용 프롬프트로 저장
        st.session_state[dist_prompt_key] = analysis_prompt
        
        # 방법이 변경되면 캐시도 초기화
        if method_changed:
            cache_state_key = f"{key_prefix}_cache"
            if cache_state_key in st.session_state:
                st.session_state[cache_state_key] = {}
                print(f"분포 비교 방법이 변경되어 캐시 초기화: {compare_method}")
        
        # 디버깅용 로깅
        print(f"분포 비교 분석 프롬프트 생성 완료 (길이: {len(analysis_prompt)})")
        if method_changed:
            print(f"분포 비교 방법 변경: {compare_method}")
    else:
        # 캐시된 분포 분석 전용 프롬프트 사용
        analysis_prompt = st.session_state[dist_prompt_key]
        print(f"캐시된 분포 비교 프롬프트 사용 (길이: {len(analysis_prompt)})")

    # AI 분석 섹션 추가
    st.markdown("---")
    st.subheader("🤖 AI 분포 비교 분석")

    # 세션 상태 키 정의 - 모두 분포 분석 전용 키 사용
    chat_history_key = f"{key_prefix}_history"
    cache_state_key = f"{key_prefix}_cache"
    running_key = f"{key_prefix}_running"
    
    # 메모리 길이 확인 및 설정 (대화 기억을 위해 메모리 길이 설정 강제)
    if st.session_state.memory_length < 2:
        print(f"메모리 길이가 너무 작음: {st.session_state.memory_length}. 5로 설정합니다.")
        st.session_state.memory_length = 5
    
    # 분석 실행 여부 확인 - 분포 분석 전용 키 사용
    if running_key in st.session_state:
        is_running = st.session_state[running_key]
    else:
        is_running = False
    
    # 분석 버튼 클릭 콜백 함수 - 분포 분석 전용
    def on_distribution_analyze_click():
        # 캐시 초기화
        if cache_state_key in st.session_state:
            # 캐시 키 생성
            from ..utils.ai_utils import generate_cache_key
            cache_key = generate_cache_key(
                prompt=analysis_prompt,
                model=st.session_state.selected_model,
                temperature=st.session_state.temperature
            )
            st.session_state[cache_state_key].pop(cache_key, None)
        # 대화 기록 초기화
        if chat_history_key in st.session_state:
            st.session_state[chat_history_key] = []
        # 실행 상태 설정
        st.session_state[running_key] = True
        
        # 디버깅용 로깅
        print(f"분포 비교 분석 버튼 클릭됨. 캐시 초기화 및 분석 시작.")
    
    # 최초 AI 분석 결과 요청에 대한 UI 표시 - 분포 분석 전용 버튼
    col1, col2 = st.columns([3, 1])
    with col1:
        model_info = f"사용 모델: {st.session_state.selected_model} | 온도: {st.session_state.temperature}"
        st.caption(model_info)
    with col2:
        analyze_button = st.button(
            "AI 분포 비교 분석 실행", 
            key=f"{key_prefix}_button", 
            on_click=on_distribution_analyze_click,
            use_container_width=True
        )
    
    # 이전 분석 결과가 있는 경우 (캐시에 있는 경우)
    if cache_state_key in st.session_state and len(st.session_state[cache_state_key]) > 0:
        # 캐시 키 생성
        from ..utils.ai_utils import generate_cache_key
        cache_key = generate_cache_key(
            prompt=analysis_prompt,
            model=st.session_state.selected_model,
            temperature=st.session_state.temperature
        )
        
        if cache_key in st.session_state[cache_state_key]:
            cached_response = st.session_state[cache_state_key][cache_key]
            with st.chat_message("assistant"):
                st.markdown(cached_response["response"])
                if cached_response.get("metadata"):
                    metadata_text = "\n\n---\n**처리 정보**\n```json\n"
                    metadata_text += json.dumps(cached_response["metadata"], indent=2, ensure_ascii=False)
                    metadata_text += "\n```"
                    st.markdown(metadata_text)
            # 실행 상태 업데이트
            st.session_state[running_key] = False
            print(f"분포 비교 분석: 캐시된 결과를 사용함")
    
    # 분석 실행 중인 경우
    elif is_running:
        # 대화 기록 초기화 (새로운 분석 시작)
        if chat_history_key in st.session_state:
            st.session_state[chat_history_key] = []
            print(f"분포 비교 분석: 대화 기록 초기화됨")
            
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            metadata_placeholder = st.empty()
            with st.spinner("AI가 분포 비교 데이터를 분석하고 있습니다..."):
                print(f"분포 비교 분석: generate_ai_response 함수 호출 전")
                generate_ai_response(
                    prompt=analysis_prompt,
                    key_prefix=key_prefix,
                    message_placeholder=message_placeholder,
                    metadata_placeholder=metadata_placeholder
                )
                print(f"분포 비교 분석: generate_ai_response 함수 호출 후")
        
        # 실행 완료 후 상태 업데이트
        st.session_state[running_key] = False
    
    # 분석 전 안내 메시지
    else:
        st.info("AI 분석을 실행하려면 'AI 분포 비교 분석 실행' 버튼을 클릭하세요. 그룹별 분포 데이터와 인사이트를 분석합니다.")
    
    # 대화형 인터페이스는 분석이 한 번 이상 실행된 경우에만 표시
    # 캐시에 결과가 있으면 분석이 실행된 것으로 간주
    has_previous_analysis = (
        cache_state_key in st.session_state and 
        len(st.session_state[cache_state_key]) > 0
    )
    
    if has_previous_analysis:
        # 대화형 인터페이스 표시
        st.markdown("---")
        st.subheader("🤖 분포 비교 데이터에 대해 질문하기")
        
        # 이 시점에서 대화 기록의 상태 로깅 (디버깅용)
        if chat_history_key in st.session_state:
            print(f"분포 비교: 대화 인터페이스 표시 전 대화 기록 길이: {len(st.session_state[chat_history_key])}")
        
        # 대화형 인터페이스 표시
        display_chat_interface(key_prefix=key_prefix)
    elif not is_running:
        # 분석이 아직 실행되지 않았고 현재 실행 중도 아닌 경우 안내 메시지 표시
        st.info("AI 데이터 분석을 먼저 실행하여 분포 비교 데이터에 대한 인사이트를 얻은 후 질문할 수 있습니다.") 