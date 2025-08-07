import streamlit as st
import os
import glob
import json

# 폴더 경로 변수 정의 (상단에 한 번만 정의)
ICP_DIR = "ICP"
VIS_DIR = os.path.join(ICP_DIR, "lot_visualization")

# 그래프 설정값 정의 (다른 스크립트에서 가져옴)
graph_settings = {
    "icp_trend_height": 800,
    "total_time_height": 800,
    "correlation_heatmap_height": 700, # analysis에서 사용하지만 참고용으로 유지
    "duration_comparison_height": 600,
    "gantt_chart_height": 800, # 기본값, 실제는 동적일 수 있음
    "pca_scatter_height": 700, # analysis에서 사용하지만 참고용으로 유지
    "boxplot_height": 600, # analysis에서 사용하지만 참고용으로 유지
    "default_width": 1200,
    "individual_icp_scatter_height": 800, # 개별 ICP 산점도 높이 추가 (analysis 생성)
    "font_family": "Arial, Malgun Gothic, sans-serif",
    "plot_bgcolor": "white",
    "grid_color": "lightgray"
}

from components.ai_utils import (
    init_session_state,
    display_analysis_ui,
    generate_ai_analysis
)

def show_icp_lot_visualization_gallery():
    """ICP LOT 데이터 시각화 갤러리 탭 표시"""
    init_session_state(key_prefix="icp_lot_visualization_gallery")

    st.header("ICP LOT 시각화 갤러리")
    st.markdown("--- ")

    st.subheader("시각화 결과 갤러리")
    
    # LOT 분석 시각화 디렉토리 (전역 변수 사용)
    st.write(f"생성된 시각화 파일 (`{VIS_DIR}` 폴더):")

    if not os.path.exists(VIS_DIR):
        st.warning(f"`{VIS_DIR}` 폴더를 찾을 수 없습니다. 데이터 생성 및 시각화 프로세스가 올바르게 완료되었는지 확인하세요.")
        
        # 디버깅 정보 추가
        st.error("디버깅 정보:")
        cwd = os.getcwd()
        st.code(f"현재 작업 디렉토리: {cwd}")
        st.code(f"찾으려는 폴더: {os.path.abspath(VIS_DIR)}")
        st.code(f"상위 폴더 존재 여부: {os.path.exists(ICP_DIR)}")
        
        if os.path.exists(ICP_DIR):
            st.code(f"ICP 폴더 내용: {os.listdir(ICP_DIR)}")
        return

    # 시각화 HTML 파일 목록 가져오기
    vis_html_files = glob.glob(os.path.join(VIS_DIR, "*.html"))

    if not vis_html_files:
        st.info(f"표시할 시각화 파일(*.html)이 없습니다. (`{VIS_DIR}` 폴더 확인)")
        
        # 디버깅 정보 추가
        st.error("디버깅 정보:")
        if os.path.exists(VIS_DIR):
            vis_dir_contents = os.listdir(VIS_DIR)
            st.code(f"폴더 내용: {vis_dir_contents}")
            
            # 폴더에 파일이 있지만 HTML 파일이 없는 경우 확장자 확인
            if len(vis_dir_contents) > 0:
                extensions = set([os.path.splitext(f)[1] for f in vis_dir_contents])
                st.code(f"발견된 파일 확장자: {extensions}")
                
                # 모든 파일 경로 상세 출력
                st.code("폴더 내 모든 파일:")
                for file in vis_dir_contents:
                    full_path = os.path.join(VIS_DIR, file)
                    file_size = os.path.getsize(full_path) if os.path.isfile(full_path) else "디렉토리"
                    st.code(f"- {file} (크기: {file_size} 바이트)")
        else:
            st.code(f"폴더가 존재하지 않습니다: {VIS_DIR}")
            
            # 상위 디렉토리 탐색
            parent_dir = os.path.dirname(VIS_DIR)
            if os.path.exists(parent_dir):
                st.code(f"상위 폴더({parent_dir}) 내용:")
                for item in os.listdir(parent_dir):
                    st.code(f"- {item}")
        return

    # 파일 이름만 추출하여 정렬 (선택적)
    vis_filenames = sorted([os.path.basename(f) for f in vis_html_files])
    
    # 시각화 유형별 분류 - 실제 파일 패턴에 맞게 수정
    vis_categories = {
        "종합 비교": [f for f in vis_filenames if "all_processes" in f], # 새로운 카테고리 추가
        "시계열 분석": [f for f in vis_filenames if ("total_time" in f or "icp_trend" in f) and "all_processes" not in f], # 종합 비교 제외
        "간트 차트": [f for f in vis_filenames if "gantt" in f],
        "기간 비교": [f for f in vis_filenames if "duration_comparison" in f],
        # "공정별 분석" 삭제 또는 유지 (파일 패턴에 따라) - 현재 패턴으로는 시계열, 간트, 기간 비교에 포함됨
        "기타": [f for f in vis_filenames if not any(x in f for x in ["all_processes", "total_time", "icp_trend", "gantt", "duration_comparison"])]
    }
    
    # 카테고리 선택 라디오 버튼 UI
    # 메인 페이지 상단에 설정 섹션 추가
    st.markdown("## 시각화 설정")
    # 설정을 위한 열 생성
    col1, col2 = st.columns([2, 1]) # 비율 조정 가능
    with col1:
        # 카테고리 선택
        # 카테고리 키 리스트 생성 (파일이 있는 카테고리만)
        available_categories = [cat for cat, files in vis_categories.items() if files]
        if not available_categories:
            st.warning("표시할 시각화 결과가 없습니다.")
            return

        selected_category = st.radio(
            "시각화 카테고리:",
            options=available_categories,
            key="select_vis_category_lot",
            horizontal=True
        )
    # col2는 일단 비워둠 (추후 다른 설정 추가 가능)

    # 해당 카테고리의 파일 목록
    category_files = vis_categories[selected_category]
    
    if not category_files:
        # 이 부분은 available_categories 체크로 인해 실행되지 않을 가능성이 높음
        st.info(f"'{selected_category}' 카테고리에 표시할 시각화 파일이 없습니다.")
        return
    
    st.markdown("---")
    st.subheader(f"{selected_category} 시각화")

    # 파일 선택 드롭다운
    selected_vis_filename = st.selectbox(
        "시각화 선택:",
        category_files,
        key="select_vis_html_lot_gallery"
    )

    # 선택된 파일 표시 및 AI 분석
    if selected_vis_filename:
        vis_path = os.path.join(VIS_DIR, selected_vis_filename)
        stats_path = vis_path.replace(".html", "_stats.json")
        stats_data = None
        try:
            if os.path.exists(stats_path):
                try:
                    with open(stats_path, 'r', encoding='utf-8') as f_stats:
                        stats_data = json.load(f_stats)
                    print(f"통계 파일 로드 성공: {stats_path}")
                except Exception as e:
                    st.warning(f"통계 파일 ({stats_path}) 로드 중 오류 발생: {e}")
            else:
                print(f"통계 파일 없음: {stats_path}")

            # HTML 파일 내용 읽기 및 높이 추정
            with open(vis_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            filename_lower = selected_vis_filename.lower()
            html_height = 600 # 기본값

            # 높이 추정 로직 업데이트 (all_processes_icp_trend 추가)
            if "all_processes_icp_trend" in filename_lower:
                html_height = graph_settings.get("icp_trend_height", 800)
            elif "gantt" in filename_lower:
                html_height = graph_settings.get("gantt_chart_height", 800)
            elif "icp_trend" in filename_lower:
                html_height = graph_settings.get("icp_trend_height", 800)
            elif "total_time" in filename_lower:
                html_height = graph_settings.get("total_time_height", 800)
            elif "duration_comparison" in filename_lower:
                html_height = graph_settings.get("duration_comparison_height", 600)
            # analysis 결과 파일 높이 추정 (필요시 추가)
            elif "correlation_heatmap" in filename_lower or "pca_components_heatmap" in filename_lower:
                 html_height = graph_settings.get("correlation_heatmap_height", 700)
            elif "icp_correlation_bar" in filename_lower:
                 html_height = graph_settings.get("correlation_heatmap_height", 700)
            elif "boxplot" in filename_lower:
                 html_height = graph_settings.get("boxplot_height", 600)
            elif "pca_scatter" in filename_lower:
                 html_height = graph_settings.get("pca_scatter_height", 700)
            elif "group_comparison_bar" in filename_lower:
                 html_height = graph_settings.get("duration_comparison_height", 600)
            elif "individual_icp_scatter" in filename_lower: # lot_3_analysis 결과
                 html_height = graph_settings.get("individual_icp_scatter_height", 800)

            # 컨테이너로 감싸기 및 HTML 표시
            vis_container = st.container()
            with vis_container:
                st.caption(f"파일: {selected_vis_filename}")
                st.components.v1.html(html_content, height=html_height + 50, scrolling=True)

            # --- 로드된 통계 정보 표시 (옵션) ---
            if stats_data:
                with st.expander("관련 통계 정보 보기"):
                    st.json(stats_data)

            st.markdown("--- ")
            st.subheader("🤖 iDSB AI 시각화 분석 요약")

            # --- 프롬프트 생성을 위한 정보 추출 ---
            process_num_str = "알 수 없음"
            vis_type_specific = "알 수 없음"
            vis_purpose = "일반적인 공정 데이터 시각화"
            is_comparison_chart = "all_processes" in filename_lower # 비교 차트 여부 플래그

            # 비교 차트가 아닐 경우에만 공정 번호 추출
            if not is_comparison_chart:
                if "process1" in filename_lower:
                    process_num_str = "1차"
                elif "process2" in filename_lower:
                    process_num_str = "2차"
                elif "process3" in filename_lower:
                    process_num_str = "3차"
            else:
                 process_num_str = "1, 2, 3차 전체" # 비교 차트 대상 명시

            # 시각화 종류 및 목적 설정 (비교 차트 포함)
            if is_comparison_chart and "icp_trend" in filename_lower:
                vis_type_specific = "공정별 일별 평균 Target ICP 트렌드 비교"
                vis_purpose = "시간에 따른 공정(1, 2, 3차) 간 Target ICP 값의 상대적 변화 추세 비교 분석 목적"
            elif "gantt" in filename_lower:
                 vis_type_specific = "간트 차트 (Gantt Chart)"
                 vis_purpose = f"{process_num_str} 공정의 Lot별 단계 진행 시간 및 설비 사용 현황 시각화 (병목 현상 파악 목적)"
            elif "icp_trend" in filename_lower:
                 vis_type_specific = f"{process_num_str} 공정 일별 평균 Target ICP 트렌드 및 이동 평균"
                 vis_purpose = f"{process_num_str} 공정의 시간에 따른 Target ICP 값 변화 추세 및 장기 경향성 파악 목적"
            elif "total_time" in filename_lower:
                 vis_type_specific = f"{process_num_str} 공정 Lot별 총 공정 소요 시간"
                 vis_purpose = f"{process_num_str} 공정의 개별 Lot 완료 시간 분포 및 이상치 탐지 목적"
            elif "duration_comparison" in filename_lower:
                 vis_type_specific = f"{process_num_str} 공정 설비 단계별 평균 소요 시간 비교"
                 vis_purpose = f"{process_num_str} 공정 단계의 평균 소요 시간을 비교하여 상대적 시간 부하 파악 목적"
            # 필요시 lot_3_analysis 결과 종류 추가
            elif "individual_icp_scatter" in filename_lower:
                 vis_type_specific = "시간에 따른 개별 Lot Target ICP 분포 (공정별)"
                 vis_purpose = "모든 공정의 개별 Lot ICP 값 분포와 이상치 발생 시점 파악 목적"


            analysis_info = {
                "선택된_파일": selected_vis_filename,
                "파일_경로": vis_path,
                "시각화_유형_일반": "Plotly HTML Chart",
                "카테고리": selected_category,
                "대상_공정": process_num_str,
                "시각화_종류_상세": vis_type_specific,
                "시각화_목적": vis_purpose,
                "비교_차트_여부": is_comparison_chart
            }

            # --- 통계 정보를 프롬프트에 추가할 문자열 생성 ---
            stats_prompt_section = ""
            if stats_data:
                stats_prompt_section += "\n\n### 3. 관련 통계 요약\n"
                stats_prompt_section += "이 시각화와 관련된 주요 통계는 다음과 같습니다:\n"
                stats_prompt_section += "```json\n"
                stats_prompt_section += json.dumps(stats_data, indent=2, ensure_ascii=False)
                stats_prompt_section += "\n```\n"
                stats_prompt_section += "위 통계 수치를 해석하고, 시각화에서 관찰되는 패턴과 어떤 연관성이 있는지 설명해주세요."
            else:
                stats_prompt_section = "\n\n(참고: 이 시각화에 대한 별도의 통계 요약 데이터는 제공되지 않았습니다.)"


            # --- 프롬프트 생성 (비교 차트 고려하여 수정) ---
            prompt = f"""
            다음은 {'**모든 공정 (1, 2, 3차)**의' if analysis_info['비교_차트_여부'] else analysis_info['대상_공정'] + ' 공정의'} '{analysis_info['시각화_종류_상세']}'를 보여주는 Plotly HTML 시각화 결과입니다.
            파일명: {selected_vis_filename}
            시각화 목적: {analysis_info['시각화_목적']}

            이 시각화는 {'**여러 공정**의 데이터를 종합 비교하거나,' if analysis_info['비교_차트_여부'] else analysis_info['대상_공정'] + ' 공정 데이터를 기반으로'} 생성되었습니다. 제공된 정보 (파일명, 시각화 종류, 목적)와 아래 제공될 수 있는 **관련 통계 요약**을 바탕으로, 이 시각화에서 관찰될 수 있는 내용과 그 의미를 전문적으로 분석하여 아래 구조에 맞춰 마크다운 리포트를 작성해주세요. (추론과 제공된 정보에 기반하여 답변해야 함)

            ### 1. 시각화 개요
            - 이 '{analysis_info['시각화_종류_상세']}'는 {'**어떤 공정들의 데이터를 비교**하고 있으며, 어떤 측면을 보여주고 있습니까?' if analysis_info['비교_차트_여부'] else analysis_info['대상_공정'] + ' 공정의 어떤 측면을 보여주고 있습니까?'}
            - '{analysis_info['시각화_목적']}'을 고려했을 때, 이 차트에서 중점적으로 봐야 할 부분은 무엇입니까? {'**특히 공정 간의 차이점이나 유사점**에 주목해야 합니다.' if analysis_info['비교_차트_여부'] else ''}

            ### 2. 예상되는 주요 관찰 사항 (시각화 기반)
            - {'**공정 간 비교 관점**에서' if analysis_info['비교_차트_여부'] else f'이 유형의 시각화에서 **{analysis_info["대상_공정"]} 공정**에 대해'} 잠재적으로 발견될 수 있는 중요한 패턴, 특징, 또는 이상점은 무엇일까요? {'(예: 특정 공정의 ICP 수준이 지속적으로 높거나 낮음, 변동성 차이 등)' if analysis_info['비교_차트_여부'] else f'(예: {vis_type_specific}의 경우 특정 단계의 긴 소요 시간, ICP 트렌드의 경우 특정 기간의 상승/하락 등)'}
            - 파일명을 통해 추론할 수 있는 특이사항이 있습니까?
            {stats_prompt_section}
            ### 4. 공정 관리 및 품질 관점 해석
            - (예상되는) 관찰 사항과 제공된 통계 정보를 종합할 때, {'**전체 공정 라인 운영 관점**이나 품질 관리 측면에서 어떤 의미를 가질 수 있습니까?' if analysis_info['비교_차트_여부'] else f'{analysis_info["대상_공정"]} 공정 관리나 품질 관리 측면에서 어떤 의미를 가질 수 있습니까?'}
            - {'**공정 간 성능 차이나 변동성 차이**를 바탕으로 어떤 질문을 던져볼 수 있습니까?' if analysis_info['비교_차트_여부'] else f'발견된 내용(시각적 패턴 및 통계 수치)을 바탕으로 {analysis_info["대상_공정"]} 공정의 안정성, 효율성 개선을 위해 어떤 질문을 던져볼 수 있습니까?'}

            ### 5. 추가 분석 제안
            - 이 {'**비교** ' if analysis_info['비교_차트_여부'] else ''}시각화 결과와 통계 정보를 바탕으로 더 깊게 탐색해 볼 수 있는 추가적인 분석 방향이나 데이터는 무엇이 있을까요?
            {'- 공정 간 차이의 원인을 파악하기 위한 추가 데이터 분석(예: 설비 노후도, 작업자)을 제안할 수 있습니다.' if analysis_info['비교_차트_여부'] else ''}

            리포트는 명확하고 간결하게 작성하고, 중요한 발견이나 인사이트는 **볼드체**로 강조해주세요.
            """

            try:
                is_running = display_analysis_ui(
                    prompt=prompt,
                    button_label="AI 시각화 분석 실행",
                    key_prefix="icp_lot_visualization_gallery",
                    info_message="AI 분석을 실행하려면 버튼을 클릭하세요."
                )

                if is_running:
                    with st.chat_message("assistant"):
                        message_placeholder = st.empty()
                        metadata_placeholder = st.empty()
                        with st.spinner("AI가 시각화를 분석하고 있습니다..."):
                            generate_ai_analysis(
                                prompt=prompt,
                                key_prefix="icp_lot_visualization_gallery",
                                message_placeholder=message_placeholder,
                                metadata_placeholder=metadata_placeholder
                            )

            except Exception as e:
                st.error(f"AI 시각화 분석 생성 중 오류가 발생했습니다: {str(e)}")

            # 시각화 메타데이터 표시 (주석 처리 또는 유지)
            # metadata_file = os.path.join(VIS_DIR, selected_vis_filename.replace('.html', '.json'))
            # if os.path.exists(metadata_file):
            #     with st.expander("시각화 메타데이터", expanded=False):
            #         try:
            #             with open(metadata_file, 'r', encoding='utf-8') as f:
            #                 metadata = json.load(f)
            #             st.json(metadata)
            #         except Exception as e:
            #             st.error(f"메타데이터 로드 오류: {str(e)}")

        except Exception as e:
            st.error(f"파일 로드 또는 처리 중 오류 발생: {e}")
            st.error(f"파일 경로: {vis_path}")

if __name__ == "__main__":
    show_icp_lot_visualization_gallery() 