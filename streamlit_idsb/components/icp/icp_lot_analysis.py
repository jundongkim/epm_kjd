import streamlit as st
import pandas as pd
import os
import glob
import json
from components.ai_utils import (
    init_session_state,
    display_analysis_ui,
    generate_ai_analysis
)

# 필요한 상수 정의
ICP_DIR = "ICP"
ANALYSIS_DIR = os.path.join(ICP_DIR, "lot_analysis")

# 그래프 설정값 정의 (다른 스크립트에서 가져옴)
graph_settings = {
    "icp_trend_height": 800,
    "total_time_height": 800,
    "correlation_heatmap_height": 700,
    "duration_comparison_height": 600,
    "gantt_chart_height": 800, # 기본값, 실제는 동적일 수 있음
    "pca_scatter_height": 700,
    "boxplot_height": 600,
    "default_width": 1200,
    "individual_icp_scatter_height": 800, # 개별 ICP 산점도 높이 추가
    "font_family": "Arial, Malgun Gothic, sans-serif",
    "plot_bgcolor": "white",
    "grid_color": "lightgray"
}

def show_icp_lot_analysis(): # 함수 이름 변경
    """ICP 분석 결과 표시 및 AI 분석 탭"""
    # 세션 상태 초기화
    init_session_state(key_prefix="icp_lot_analysis") # key_prefix 변경

    st.header("ICP Lot 데이터 분석 결과") # 헤더 변경
    st.markdown("--- ")

    # --- 분석 결과 표시 섹션 ---
    st.subheader("생성된 분석 결과")
    st.write(f"분석 결과 파일 (`{ANALYSIS_DIR}` 폴더):")

    if not os.path.exists(ANALYSIS_DIR):
        st.warning(f"`{ANALYSIS_DIR}` 폴더를 찾을 수 없습니다. 데이터 생성 및 분석 프로세스가 올바르게 완료되었는지 확인하세요.")
        return

    # HTML, CSV, TXT 등 모든 결과 파일 찾기
    analysis_files = glob.glob(os.path.join(ANALYSIS_DIR, "*.*"))

    if not analysis_files:
        st.info(f"표시할 분석 결과가 없습니다. (`{ANALYSIS_DIR}` 폴더 확인)")
        return

    # 파일 선택 (HTML 파일을 우선적으로 보여주거나 정렬 방식 변경 가능)
    analysis_filenames = sorted([os.path.basename(f) for f in analysis_files])
    selected_file = st.selectbox("보고 싶은 분석 결과 선택:",
                                 analysis_filenames,
                                 key="select_analysis_file_lot") # key 변경

    file_content_for_ai = None # AI 분석에 사용할 파일 내용
    file_type_for_ai = "unknown" # AI 분석 프롬프트에 사용할 파일 유형

    if selected_file:
        file_path = os.path.join(ANALYSIS_DIR, selected_file)
        st.markdown("#### 선택된 파일 내용")
        try:
            # HTML 파일 렌더링
            if selected_file.lower().endswith('.html'):
                # 파일명 기반으로 높이 추정
                filename_lower = selected_file.lower()
                html_height = 600 # 기본 높이

                if "gantt" in filename_lower:
                    # 간트 차트는 Lot 수에 따라 변동성이 크므로 기본 설정값 사용
                    html_height = graph_settings.get("gantt_chart_height", 800)
                elif "icp_trend" in filename_lower:
                    html_height = graph_settings.get("icp_trend_height", 800)
                elif "total_time" in filename_lower:
                    html_height = graph_settings.get("total_time_height", 800)
                elif "duration_comparison" in filename_lower:
                    html_height = graph_settings.get("duration_comparison_height", 600)
                elif "correlation_heatmap" in filename_lower:
                    html_height = graph_settings.get("correlation_heatmap_height", 700)
                elif "icp_correlation_bar" in filename_lower:
                    html_height = graph_settings.get("correlation_heatmap_height", 700)
                elif "boxplot" in filename_lower:
                    html_height = graph_settings.get("boxplot_height", 600)
                elif "pca_scatter" in filename_lower:
                    html_height = graph_settings.get("pca_scatter_height", 700)
                elif "pca_components_heatmap" in filename_lower:
                    html_height = graph_settings.get("correlation_heatmap_height", 700)
                elif "group_comparison_bar" in filename_lower:
                    html_height = graph_settings.get("duration_comparison_height", 600)
                elif "individual_icp_scatter" in filename_lower:
                    html_height = graph_settings.get("individual_icp_scatter_height", 800)

                with open(file_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                # 추정된 높이에 약간의 여유를 더해 컴포넌트 높이 설정
                st.components.v1.html(html_content, height=html_height + 50, scrolling=True)
                file_content_for_ai = f"Plotly HTML 파일 경로: {file_path}" # AI에는 경로 정보 전달
                file_type_for_ai = "html"
            # PNG, JPG 등 이미지 파일 처리
            elif selected_file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                st.image(file_path, caption=selected_file, use_column_width=True)
                file_content_for_ai = f"이미지 파일 경로: {file_path}"
                file_type_for_ai = "image"
            # CSV 파일 처리
            elif selected_file.lower().endswith('.csv'):
                df_analysis = pd.read_csv(file_path)
                st.dataframe(df_analysis, use_container_width=True)
                file_content_for_ai = df_analysis.to_csv(index=False)
                file_type_for_ai = "csv"
            # TXT 파일 처리
            elif selected_file.lower().endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    st.text_area(f"{selected_file} 내용", content, height=300)
                    file_content_for_ai = content
                    file_type_for_ai = "text"
            # 기타 파일 형식
            else:
                st.info(f"`.{selected_file.split('.')[-1]}` 파일 형식은 미리보기를 지원하지 않습니다.")
                with open(file_path, "rb") as fp:
                    st.download_button(
                        label=f"{selected_file} 다운로드",
                        data=fp,
                        file_name=selected_file,
                        key=f"download_{selected_file}_lot" # key 변경
                    )
        except Exception as e:
            st.error(f"분석 결과 로드 오류: {e}")

    st.markdown("--- ")

    # --- AI 기반 분석 결과 분석 ---
    st.subheader("🤖 iDSB AI 분석 결과 해석")

    if file_content_for_ai:
        # 프롬프트 생성 (파일 유형에 따라 다르게)
        prompt_header = f"다음은 ICP 공정 데이터 분석 결과 파일입니다.\n파일명: {selected_file}\n파일 유형: {file_type_for_ai}\n\n"
        prompt_body = ""
        # HTML 파일 분석 프롬프트 추가
        if file_type_for_ai == "html":
            prompt_body = f"""이 Plotly HTML 파일({selected_file})은 ICP 공정 분석 결과(예: 상관관계 히트맵, 박스 플롯, PCA 산점도, 그룹 비교 바 차트 등)를 동적으로 시각화한 것입니다. 파일명을 기반으로 어떤 종류의 분석인지 추론하고, 해당 분석 결과에서 일반적으로 얻을 수 있는 인사이트와 해석에 대해 마크다운 리포트를 작성해주세요:

### 1. 분석 내용 추론
- 파일명 ({selected_file})을 볼 때, 이 HTML 파일은 어떤 종류의 분석 결과를 시각화한 것 같습니까?

### 2. 예상되는 주요 발견점
- 이 유형의 분석에서 일반적으로 발견될 수 있는 핵심 패턴, 추세, 이상치, 그룹 간 차이 등은 무엇입니까?

### 3. 해석 및 비즈니스 의미
- 이러한 발견점이 실제 공정 관점에서 어떤 의미를 가질 수 있습니까? (예: 특정 단계의 병목 가능성, ICP 값과 특정 시간 간의 관계, 공정 변동성 등)

### 4. 추가 탐색 질문
- 이 분석 결과를 바탕으로 어떤 추가적인 질문을 하거나 더 조사해볼 수 있습니까?

결과는 명확하고 간결하게 작성하고, 중요한 사항은 **볼드체**로 강조해주세요."""
        elif file_type_for_ai == "image":
            prompt_body = f"""이 이미지({selected_file})는 ICP 공정 분석 결과(예: 상관관계 히트맵, PCA, 이상치 탐지 등)를 시각화한 것입니다. 이미지를 분석하여 다음 내용을 포함하는 마크다운 리포트를 작성해주세요:

### 1. 시각화 내용 요약
- 이 이미지는 어떤 분석 결과를 보여줍니까?

### 2. 주요 발견점
- 이미지에서 관찰할 수 있는 핵심 패턴, 추세, 이상치 등은 무엇입니까?

### 3. 해석 및 인사이트
- 발견점을 바탕으로 어떤 결론을 내릴 수 있습니까? 공정 개선이나 추가 조사에 대한 제안이 있습니까?

결과는 명확하고 간결하게 작성하고, 중요한 사항은 **볼드체**로 강조해주세요."""
        elif file_type_for_ai == "csv":
            prompt_body = f"""다음 CSV 데이터는 ICP 공정 분석 결과(예: 상관관계 행렬, 통계 요약, 이상치 목록)입니다.

```csv
{file_content_for_ai[:2000]}... (데이터 일부)
```

이 데이터를 분석하여 다음 내용을 포함하는 마크다운 리포트를 작성해주세요:

### 1. 데이터 내용 요약
- 이 데이터는 어떤 분석 결과를 나타냅니까?

### 2. 주요 분석 결과
- 데이터에서 발견된 주요 수치, 관계, 패턴 등은 무엇입니까?

### 3. 결과 해석 및 인사이트
- 분석 결과를 통해 어떤 의미있는 결론을 도출할 수 있습니까?

결과는 명확하고 간결하게 작성하고, 중요한 사항은 **볼드체**로 강조해주세요."""
        elif file_type_for_ai == "text":
            prompt_body = f"""다음 텍스트는 ICP 공정 분석 결과(예: 통계 테스트 결과, 분석 요약 보고서)입니다.

```text
{file_content_for_ai[:2000]}... (내용 일부)
```

이 텍스트 내용을 분석하여 다음 내용을 포함하는 마크다운 리포트를 작성해주세요:

### 1. 내용 요약
- 이 텍스트는 어떤 분석 결과나 정보를 담고 있습니까?

### 2. 핵심 결과 및 주장
- 텍스트에서 제시하는 주요 결과, 결론, 주장은 무엇입니까?

### 3. 중요성 및 시사점
- 이 결과가 왜 중요하며, 어떤 시사점을 제공합니까?

결과는 명확하고 간결하게 작성하고, 중요한 사항은 **볼드체**로 강조해주세요."""
        else: # 기타 파일 형식 또는 내용 없는 경우
            prompt_body = f"파일 '{selected_file}'의 내용을 분석해주세요. 이 파일은 ICP 공정 분석의 결과물일 가능성이 높습니다. 파일 내용이나 파일명, 확장자 등을 바탕으로 가능한 분석과 해석을 제공해주세요."

        final_prompt = prompt_header + prompt_body

        try:
            # AI 분석 UI 표시 및 처리
            is_running = display_analysis_ui(
                prompt=final_prompt,
                button_label=f"AI '{selected_file}' 분석 실행",
                key_prefix="icp_lot_analysis", # key_prefix 통일
                info_message="AI 분석을 실행하려면 버튼을 클릭하세요."
            )

            # 분석 실행 중인 경우
            if is_running:
                with st.chat_message("assistant"):
                    message_placeholder = st.empty()
                    metadata_placeholder = st.empty()
                    with st.spinner(f"AI가 '{selected_file}' 분석 결과를 해석하고 있습니다..."):
                        generate_ai_analysis(
                            prompt=final_prompt,
                            key_prefix="icp_lot_analysis", # key_prefix 통일
                            message_placeholder=message_placeholder,
                            metadata_placeholder=metadata_placeholder
                        )

        except Exception as e:
            st.error(f"AI 분석 결과 해석 중 오류 발생: {str(e)}")
    else:
        st.info("분석 결과를 선택하면 AI 해석 기능을 사용할 수 있습니다.") 