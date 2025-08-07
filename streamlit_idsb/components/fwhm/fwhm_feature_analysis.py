import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from components.ai_utils import (
    init_session_state,
    display_analysis_ui,
    generate_ai_analysis
)
from utils.style import ECOPRO_COLORS
import json

def show_feature_analysis(df):
    """특성 분석 탭 표시"""
    # 세션 상태 초기화
    init_session_state(key_prefix="feature_analysis")

    # 선택된 데이터셋 확인
    if 'selected_fwhm_dataset' in st.session_state:
        selected_dataset = st.session_state.selected_fwhm_dataset
    else:
        selected_dataset = "F28"  # 기본값

    st.header(f"특성 분석 (데이터셋: {selected_dataset})")

    # 특성 유형별 요약
    st.subheader("특성 유형별 요약")
    feature_groups = {
        "Li 특성": [col for col in df.columns if col.startswith('Li')],
        "Pre_L 특성": [col for col in df.columns if col.startswith('Pre_L')],
        "Pre_S 특성": [col for col in df.columns if col.startswith('Pre_S')],
        "Qcp 특성": [col for col in df.columns if col.startswith('Qcp')]
    }

    # 특성 유형별 통계 정보
    feature_stats = {}
    for group_name, features in feature_groups.items():
        group_df = df[features]

        # 빈 배열에 대한 연산 오류 방지
        if len(features) == 0 or group_df.empty:
            feature_stats[group_name] = {
                "개수": 0,
                "평균값": float('nan'),
                "최소값": float('nan'),
                "최대값": float('nan'),
                "표준편차": float('nan'),
            }
        else:
            feature_stats[group_name] = {
                "개수": len(features),
                "평균값": group_df.values.mean().round(4) if group_df.values.size > 0 else float('nan'),
                "최소값": group_df.values.min().round(4) if group_df.values.size > 0 else float('nan'),
                "최대값": group_df.values.max().round(4) if group_df.values.size > 0 else float('nan'),
                "표준편차": group_df.values.std().round(4) if group_df.values.size > 0 else float('nan'),
            }

    # 특성 통계 표시
    stats_df = pd.DataFrame(feature_stats).T
    st.dataframe(stats_df, use_container_width=True)

    # 특성 유형별 분포 시각화
    st.subheader("특성 유형별 분포")

    selected_group = st.selectbox(
        "특성 그룹 선택",
        list(feature_groups.keys())
    )

    # 선택된 그룹의 특성 중 일부 선택 (최대 5개만 표시)
    selected_features = feature_groups[selected_group][:5]

    # 특성 분포 시각화
    fig = make_subplots(
        rows=len(selected_features),
        cols=1,
        subplot_titles=[f"{feat} 분포" for feat in selected_features],
        vertical_spacing=0.04
    )

    # 그룹에 따라 다른 색상 적용
    group_colors = {
        "Li 특성": ECOPRO_COLORS['dark_blue'],
        "Pre_L 특성": ECOPRO_COLORS['light_blue'],
        "Pre_S 특성": ECOPRO_COLORS['orange'],
        "Qcp 특성": ECOPRO_COLORS['green']
    }

    for i, feat in enumerate(selected_features, 1):
        fig.add_trace(
            go.Histogram(
                x=df[feat],
                name=feat,
                showlegend=False,
                marker_color=group_colors[selected_group]
            ),
            row=i,
            col=1
        )

    fig.update_layout(
        height=200 * len(selected_features),
        width=800,
        template="plotly_white",
        margin=dict(t=30)
    )

    st.plotly_chart(fig, use_container_width=True)

    # 상관관계 분석
    st.subheader("특성 간 상관관계")

    # Target_F와 각 특성 그룹 간의 상관관계 계산
    correlations = {}
    for group_name, features in feature_groups.items():
        group_corr = df[features + ["Target_F"]].corr()["Target_F"].drop("Target_F").abs()
        top_corr = group_corr.sort_values(ascending=False).head(5)
        correlations[group_name] = top_corr.to_dict()

    # 상관관계 표시 방식 선택
    corr_display_type = st.radio(
        "상관관계 표시 방식",
        ["테이블", "히트맵"],
        key="corr_display_type"
    )

    if corr_display_type == "테이블":
        # 상관관계 표시 (테이블로)
        corr_df = pd.DataFrame.from_dict(correlations)
        st.dataframe(corr_df, use_container_width=True)
    else:
        # 히트맵으로 상관관계 표시
        # 각 그룹별 상위 5개 특성을 모아서 하나의 데이터프레임 생성
        all_top_features = []
        for group_name, corr_dict in correlations.items():
            # 각 그룹별로 상위 특성 추출
            top_features = list(corr_dict.keys())
            all_top_features.extend(top_features)

        # Target_F 추가
        all_top_features.append("Target_F")

        # 중복 제거 (혹시 다른 그룹에서 같은 특성이 선택된 경우)
        all_top_features = list(dict.fromkeys(all_top_features))

        # 선택된 특성들의 상관관계 행렬 계산
        corr_matrix = df[all_top_features].corr().round(3)

        # 히트맵 생성
        fig = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns,
            y=corr_matrix.columns,
            colorscale=[[0, ECOPRO_COLORS['light_blue']], [0.5, 'white'], [1.0, ECOPRO_COLORS['dark_blue']]],
            zmin=-1,
            zmax=1,
            text=corr_matrix.values.round(2),
            texttemplate="%{text}",
            colorbar=dict(title="상관계수")
        ))

        fig.update_layout(
            title=dict(
                text="Target_F와 주요 특성들 간의 상관관계 히트맵 (각 그룹별 상위 5개 특성)",
                font=dict(color=ECOPRO_COLORS['dark_blue'])
            ),
            height=800,
            width=900,
            template="plotly_white"
        )

        st.plotly_chart(fig, use_container_width=True)

    # 상관관계 시각화 방식 선택
    viz_type = st.radio(
        "시각화 방식",
        ["막대 그래프", "히트맵"],
        key="corr_viz_type"
    )

    # 상관관계 그룹 선택
    selected_corr_group = st.selectbox(
        "상관관계 그룹 선택",
        list(feature_groups.keys()),
        key="corr_group_select"
    )

    if viz_type == "막대 그래프":
        # 기존 막대 그래프 시각화
        # 선택된 그룹의 상관관계 시각화
        top_corr_features = list(correlations[selected_corr_group].keys())
        top_corr_values = list(correlations[selected_corr_group].values())

        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=top_corr_features,
                y=top_corr_values,
                marker_color=group_colors[selected_corr_group]
            )
        )

        fig.update_layout(
            title=dict(
                text=f"{selected_corr_group}의 Target_F와의 상관관계 (상위 5개)",
                font=dict(color=ECOPRO_COLORS['dark_blue'])
            ),
            xaxis_title="특성",
            yaxis_title="절대 상관계수",
            template="plotly_white"
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        # 히트맵 시각화
        # 선택된 그룹의 전체 상관관계 행렬 계산
        selected_features = feature_groups[selected_corr_group]

        # 선택된 특성 수가 많을 경우 상위 10개만 사용
        if len(selected_features) > 10:
            # Target_F와 상관관계가 높은 순으로 정렬된 상위 10개 특성 선택
            group_corr = df[selected_features + ["Target_F"]].corr()["Target_F"].drop("Target_F").abs()
            selected_features = list(group_corr.sort_values(ascending=False).head(10).index)

        # 선택된 특성과 Target_F의 상관관계 행렬 계산
        corr_matrix = df[selected_features + ["Target_F"]].corr().round(3)

        # 히트맵 생성
        fig = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns,
            y=corr_matrix.columns,
            colorscale=[[0, ECOPRO_COLORS['light_blue']], [0.5, 'white'], [1.0, ECOPRO_COLORS['dark_blue']]],
            zmin=-1,
            zmax=1,
            text=corr_matrix.values.round(2),
            texttemplate="%{text}",
            colorbar=dict(title="상관계수")
        ))

        fig.update_layout(
            title=dict(
                text=f"{selected_corr_group}과 Target_F 간의 상관관계 히트맵",
                font=dict(color=ECOPRO_COLORS['dark_blue'])
            ),
            height=600,
            width=800,
            template="plotly_white"
        )

        st.plotly_chart(fig, use_container_width=True)

    # AI 분석 요약
    st.subheader("🤖 AI 기반 특성 분석 리포트")

    # 분석 정보 수집
    analysis_info = {
        "특성 유형별 통계": feature_stats,
        "특성 유형별 개수": {name: len(features) for name, features in feature_groups.items()},
        "상관관계": correlations
    }

    if analysis_info:
        prompt = f"""
        **반가폭(FWHM) 데이터셋 특성 분석 전문가 리포트 요청**

        제공된 반가폭(FWHM) 데이터셋의 특성 분석 정보(기술 통계량, 상관 관계, 분포 등)를 심층적으로 검토하여, 전문적인 분석 리포트를 마크다운 형식으로 작성해주십시오.
        **리포트는 반드시 아래 제공된 [분석 정보] 섹션의 실제 수치 데이터를 명시적으로 인용하고, 각 수치와 분석 결과가 의미하는 바를 비전문가도 이해하기 쉽게 상세히 설명해야 합니다.**

        **리포트 포함 내용:**

        1.  **주요 특성 개요:**
            *   각 특성 그룹(Li, Pre_L, Pre_S, Qcp 등)의 데이터 분포 특성을 **실제 통계 수치(평균, 표준편차, 최소/최대값 등)를 언급하며** 요약해주십시오.
            *   예를 들어, 'Li 특성 그룹의 평균은 X.XX이며 이는...' 또는 'Pre_S 특성 YYY의 표준편차는 Z.ZZ로 나타나 변동성이 크다는 것을 의미합니다.' 와 같이 구체적으로 설명해주십시오.
            *   이상치 또는 특이 패턴이 관찰되는 특정 특성이 있다면, 해당 특성의 이름과 관찰된 내용을 기술해주십시오.

        2.  **특성 간 상관관계 분석:**
            *   `Target_F`(반가폭 추정치)와 **계산된 상관계수 값을 명시하며** 상관관계가 높은 주요 특성 상위/하위 N개를 식별하고, 그 의미를 해석해주십시오.
            *   예: '특성 AAA는 Target_F와 0.XX의 양의 상관관계를 보여, AAA가 증가할수록 Target_F도 증가하는 경향이 있음을 시사합니다.'
            *   같은 그룹 내 특성 간, 다른 그룹 간 특성의 주요 상관관계 패턴을 **구체적인 상관계수 값을 예시로 들어** 분석해주십시오.

        3.  **반가폭(Target_F) 영향 요인 분석:**
            *   앞서 분석한 기술 통계 및 상관관계 분석 결과를 바탕으로, 반가폭(`Target_F`)에 **긍정적/부정적 영향을 미치는 주요 특성을 명확히 제시**하고, **어떤 수치적 근거(예: 높은 상관계수, 특정 분포 패턴)로 판단했는지 상세히 설명**해주십시오.
            *   반가폭 예측 모델링 시 **왜 특정 특성들을 중요하게 고려해야 하는지** 그 이유를 분석 결과에 기반하여 제안해주십시오.

        4.  **종합 결론 및 제언:**
            *   지금까지의 분석 결과를 **핵심 수치들을 중심으로** 요약하고, 반가폭 관리 또는 개선을 위해 활용할 수 있는 **구체적인 데이터 기반 인사이트**를 제시해주십시오.
            *   추가 분석이 필요하거나 주의 깊게 모니터링해야 할 특성이 있다면, **그 이유와 함께** 제언해주십시오.

        **요구사항:**
        *   마크다운 형식 사용.
        *   명확한 섹션 구분 (e.g., `# 개요`, `## 주요 특성 분석`, `### Li 특성`).
        *   전문적이고 간결한 분석 용어 사용하되, **쉬운 설명** 병기.
        *   **제공된 데이터 분석 결과([분석 정보] 섹션의 수치)에 철저히 근거하여 작성.**
        *   중요 내용은 **볼드체**로 강조.

        ---
        **[분석 정보 시작]**
        {analysis_info}
        **[분석 정보 끝]**
        ---
        """
        try:
            is_running = display_analysis_ui(
                prompt=prompt,
                button_label="데이터 분석 시작",
                key_prefix="feature_analysis",
                info_message="AI 특성 분석을 실행하려면 '데이터 분석 시작' 버튼을 클릭하세요."
            )

            if is_running:
                with st.chat_message("assistant"):
                    message_placeholder = st.empty()
                    metadata_placeholder = st.empty()
                    with st.spinner("AI가 특성을 분석하고 있습니다..."):
                        generate_ai_analysis(
                            prompt=prompt,
                            key_prefix="feature_analysis",
                            message_placeholder=message_placeholder,
                            metadata_placeholder=metadata_placeholder
                        )
        except Exception as e:
            st.error(f"AI 특성 분석 리포트 생성 중 오류가 발생했습니다: {str(e)}")
    else:
        st.warning("분석 정보가 없습니다. 먼저 통계 계산 및 상관관계 분석을 실행해주세요.")