import streamlit as st
import pandas as pd
import json
from datetime import datetime
from ..utils import get_equipment_type, get_sensor_type
from ..utils.ai_utils import init_session_state, display_chat_interface
from .insights_report import generate_insights_report, display_insights_report
from .insights_download import download_button_for_text, download_button_for_pdf
from .insights_qa import generate_suggested_questions, generate_answer_to_question
from .insights_plotly_style import apply_insights_plotly_style, create_insights_line_chart


def render_insights_generation_tab(df, equipment_type, sensor_type):
    """인사이트 생성 탭을 렌더링하는 함수"""
    st.header("데이터 인사이트 생성")
    
    # 인사이트 생성 옵션
    col1, col2 = st.columns(2)
    with col1:
        report_type = st.selectbox(
            "리포트 유형",
            ["종합 분석 리포트", "이상치 분석 리포트", "패턴 분석 리포트", "성능 추세 리포트"]
        )
    with col2:
        include_visuals = st.checkbox("시각화 포함", value=True)
    
    # 고급 설정 (심화 분석 설정)
    with st.expander("고급 설정", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            analysis_depth = st.slider("분석 깊이", 1, 5, 3, 
                                     help="분석 깊이가 높을수록 상세한 인사이트를 제공하지만 생성 시간이 길어집니다.")
        with col2:
            include_recommendations = st.checkbox("권장 사항 포함", value=True,
                                              help="센서 데이터 기반의 설비 개선 및 모니터링 권장 사항을 포함합니다.")
    
    # 인사이트 생성 버튼
    generate_btn = st.button("인사이트 생성하기")
    
    # 인사이트 생성 로직
    if generate_btn or st.session_state.insights_report_generated:
        if generate_btn:  # 버튼이 클릭된 경우에만 세션 상태 업데이트
            st.session_state.insights_analysis_running = True
            st.session_state.insights_report_generated = False
        
        if st.session_state.insights_analysis_running and not st.session_state.insights_report_generated:
            # 분석 실행
            with st.spinner("데이터 분석 중... 잠시만 기다려주세요."):
                # 여기서 실제 인사이트 생성 함수 호출
                insights_report = generate_insights_report(df, equipment_type, sensor_type, 
                                                        report_type, include_visuals, 
                                                        analysis_depth, include_recommendations)
                
                # 세션 상태 업데이트
                st.session_state.insights_analysis_cache['latest_report'] = insights_report
                st.session_state.insights_analysis_running = False
                st.session_state.insights_report_generated = True
                
                # 자동 질문 생성
                suggested_questions = generate_suggested_questions(df, equipment_type, sensor_type, report_type)
                for question in suggested_questions:
                    if question not in st.session_state.insights_questions:
                        st.session_state.insights_questions.append(question)
                
                st.success("인사이트 리포트가 생성되었습니다!")
                st.rerun()  # 화면 갱신
        
        # 이미 생성된 리포트 표시
        if st.session_state.insights_report_generated and 'latest_report' in st.session_state.insights_analysis_cache:
            display_insights_report(st.session_state.insights_analysis_cache['latest_report'])
            
            # 리포트 다운로드 버튼
            report_md = st.session_state.insights_analysis_cache['latest_report']['markdown']
            col1, col2 = st.columns(2)
            with col1:
                download_button_for_text(report_md, f"IoT_Insights_{equipment_type}_{datetime.now().strftime('%Y%m%d')}.md", "마크다운 리포트 다운로드")
            with col2:
                # wkhtmltopdf가 설치되어 있는지 확인
                try:
                    # wkhtmltopdf 실행 가능 여부 체크
                    import subprocess
                    try:
                        subprocess.run(['wkhtmltopdf', '-V'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
                        # wkhtmltopdf가 설치되어 있으면 PDF 다운로드 버튼 표시
                        download_button_for_pdf(report_md, f"IoT_Insights_{equipment_type}_{datetime.now().strftime('%Y%m%d')}.pdf", "PDF 리포트 다운로드")
                    except (subprocess.SubprocessError, FileNotFoundError):
                        st.warning("PDF 생성을 위해 wkhtmltopdf가 필요합니다. 설치 후 이용해주세요.")
                        st.markdown("[wkhtmltopdf 설치 방법](https://wkhtmltopdf.org/downloads.html)")
                except Exception as e:
                    st.warning(f"PDF 변환 기능을 사용할 수 없습니다: {str(e)}")
                    st.info("마크다운 파일을 다운로드하여 외부 도구로 PDF 변환이 가능합니다.")
            
            # 리포트 초기화 버튼
            if st.button("리포트 초기화"):
                st.session_state.insights_report_generated = False
                if 'latest_report' in st.session_state.insights_analysis_cache:
                    del st.session_state.insights_analysis_cache['latest_report']
                st.rerun()


def render_visualization_history_tab():
    """시각화 기록 탭을 렌더링하는 함수"""
    st.header("시각화 기록")
    
    # 세션에서 사용자가 본 시각화 내역 가져오기
    visualization_history = []
    
    # 다양한 모듈의 세션 상태를 검사하여 기록 구성
    modules = [
        ("시각화 가이드", "visualization_guide"),
        ("시계열 차트", "timeseries_analysis"),
        ("히스토그램", "histogram_analysis"),
        ("박스 플롯", "boxplot_analysis"),
        ("히트맵", "heatmap_analysis"),
        ("일별/시간별 패턴", "pattern_analysis"),
        ("이상치 분석", "anomaly_analysis"),
        ("주파수 분석", "fft_analysis"),
        ("시간-주파수 분석", "timefreq_analysis"),
        ("트렌드 분석", "trend_analysis"),
        ("상관관계 분석", "correlation_analysis"),
        ("분포 비교", "distribution_analysis"),
        ("3D 시각화", "threed_analysis"),
        ("패턴 클러스터링", "clustering_analysis"),
        ("경보 및 임계값 설정", "alarm_threshold_analysis"),
        ("운전/정지 주기 분석", "cycle_analysis"),
        ("종합 인사이트", "insights_analysis")
    ]
    
    for viz_name, module_prefix in modules:
        # 각 모듈별 히스토리 키 체크
        for history_key in [f"{module_prefix}_history", f"{module_prefix}_cache"]:
            if history_key in st.session_state and st.session_state[history_key]:
                # 히스토리가 리스트 형태인 경우
                if isinstance(st.session_state[history_key], list):
                    for entry in st.session_state[history_key]:
                        if isinstance(entry, dict) and 'timestamp' in entry:
                            # 설명 필드가 없는 경우 기본값 추가
                            description = entry.get('description', f"{viz_name} 분석")
                            visualization_history.append({
                                'category': viz_name,
                                'timestamp': entry.get('timestamp', 'N/A'),
                                'description': description
                            })
                # 캐시인 경우 (딕셔너리 형태)
                elif isinstance(st.session_state[history_key], dict):
                    # 캐시에서 각 항목을 가져와 히스토리로 변환
                    for cache_key, cache_value in st.session_state[history_key].items():
                        # None 체크 추가
                        if cache_value is None:
                            continue
                            
                        if isinstance(cache_value, dict) and 'metadata' in cache_value:
                            # None 체크 추가 - metadata가 없을 수 있음
                            metadata = cache_value.get('metadata', {})
                            if metadata is None:
                                metadata = {}
                                
                            timestamp = metadata.get('timestamp', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                            visualization_history.append({
                                'category': viz_name,
                                'timestamp': timestamp,
                                'description': f"{viz_name} AI 분석"
                            })
    
    # 추가: 종합 인사이트의 AI 질문-답변 기록 추가
    qa_key = "insights_qa_analysis_cache"
    if qa_key in st.session_state and st.session_state[qa_key]:
        for cache_key, cache_value in st.session_state[qa_key].items():
            # None 체크 추가
            if cache_value is None:
                continue
            
            if isinstance(cache_value, dict) and 'response' in cache_value:
                # None 체크 추가 - metadata가 없을 수 있음
                metadata = cache_value.get('metadata', {})
                if metadata is None:
                    metadata = {}
                
                timestamp = metadata.get('timestamp', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                visualization_history.append({
                    'category': '인사이트 질의응답',
                    'timestamp': timestamp,
                    'description': "데이터 질문 및 답변"
                })
    
    # 생성된 인사이트 리포트 히스토리 추가
    if "insights_analysis_history" in st.session_state:
        for entry in st.session_state.insights_analysis_history:
            visualization_history.append({
                'category': '인사이트 리포트',
                'timestamp': entry.get('timestamp', 'N/A'),
                'description': f"{entry.get('report_type', '종합 분석')} ({entry.get('equipment_type', 'N/A')})"
            })
    
    # 기록이 있을 경우 표시
    if visualization_history:
        # 시간 기준으로 정렬 (최신 항목이 맨 위)
        visualization_history.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # 데이터프레임으로 변환하여 표시
        history_df = pd.DataFrame(visualization_history)
        st.dataframe(
            history_df,
            column_config={
                "category": "시각화 유형",
                "timestamp": "생성 시간",
                "description": "설명"
            },
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("아직 시각화 기록이 없습니다. 다양한 시각화를 이용해보세요.")
    
    # 히스토리 내보내기
    if visualization_history:
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("기록 내보내기"):
                history_json = json.dumps(visualization_history, ensure_ascii=False, indent=2)
                download_button_for_text(history_json, f"IoT_Visualization_History_{datetime.now().strftime('%Y%m%d')}.json", "JSON 다운로드")


def render_questions_answers_tab(df, equipment_type, sensor_type):
    """질문 및 답변 탭을 렌더링하는 함수"""
    st.header("데이터 질문 및 답변")
    
    # AI 분석 키 접두사
    key_prefix = "insights_qa_analysis"
    
    # 세션 상태 초기화
    init_session_state(key_prefix=key_prefix)
    
    # 유형별 자동 생성 질문 표시
    with st.expander("자동 생성된 질문", expanded=True):
        if st.session_state.insights_questions:
            for i, question in enumerate(st.session_state.insights_questions):
                if st.button(f"Q: {question}", key=f"question_{i}"):
                    # 선택한 질문에 대한 답변 생성
                    with st.spinner("답변 생성 중..."):
                        answer = generate_answer_to_question(df, question, equipment_type, sensor_type)
                        
                        # 질문과 답변을 히스토리에 저장
                        if question not in [q for q, _ in st.session_state.insights_answers]:
                            st.session_state.insights_answers.append((question, answer))
                        st.rerun()
        else:
            st.info("인사이트 리포트를 생성하면 자동으로 데이터에 대한 질문이 생성됩니다.")
    
    # 사용자 정의 질문 입력
    st.subheader("데이터에 대한 질문")
    
    # AI 모델 정보 표시
    col1, col2 = st.columns([3, 1])
    with col1:
        model_info = f"사용 모델: {st.session_state.selected_model} | 온도: {st.session_state.temperature}"
        st.caption(model_info)
    
    user_question = st.text_input("데이터에 대해 질문하세요:")
    
    if user_question and st.button("질문하기"):
        # AI 분석 사용 설정
        if st.session_state.use_ai:
            # 프롬프트 구성
            prompt = f"""
당신은 IoT 센서 데이터 분석 전문가입니다. 다음 정보를 기반으로 질문에 답변해 주세요:

장비 유형: {equipment_type}
센서 유형: {sensor_type}
데이터 크기: {len(df)}개 레코드
기간: {df['timestamp'].min().strftime('%Y-%m-%d')} ~ {df['timestamp'].max().strftime('%Y-%m-%d')}
데이터 통계:
- 평균: {df[sensor_type].mean():.2f}
- 중앙값: {df[sensor_type].median():.2f}
- 최소값: {df[sensor_type].min():.2f}
- 최대값: {df[sensor_type].max():.2f}
- 표준편차: {df[sensor_type].std():.2f}

사용자 질문: {user_question}

답변은 간결하고 명확하게 제공하되, 전문적인 통찰력을 담아주세요.
"""
            # 챗 히스토리 키
            chat_history_key = f"{key_prefix}_history"
            cache_state_key = f"{key_prefix}_cache"
            
            with st.spinner("AI 답변 생성 중..."):
                message_placeholder = st.empty()
                metadata_placeholder = st.empty()
                
                # AI 응답 생성
                from ..utils.ai_utils import generate_ai_response
                generate_ai_response(
                    prompt=prompt,
                    key_prefix=key_prefix,
                    message_placeholder=message_placeholder,
                    metadata_placeholder=metadata_placeholder
                )
                
                # 응답이 생성된 후 저장 (메타데이터 포함)
                if cache_state_key in st.session_state:
                    # 캐시 키 생성
                    from ..utils.ai_utils import generate_cache_key
                    cache_key = generate_cache_key(
                        prompt=prompt,
                        model=st.session_state.selected_model,
                        temperature=st.session_state.temperature
                    )
                    
                    if cache_key in st.session_state[cache_state_key]:
                        cached_response = st.session_state[cache_state_key][cache_key]
                        # None 체크 추가
                        if cached_response is None:
                            answer = ""
                        else:
                            answer = cached_response.get("response", "")
                        
                        # 질문과 답변을 히스토리에 저장
                        if answer and user_question not in [q for q, _ in st.session_state.insights_answers]:
                            st.session_state.insights_answers.append((user_question, answer))
        else:
            # 기존 로직 사용
            with st.spinner("답변 생성 중..."):
                answer = generate_answer_to_question(df, user_question, equipment_type, sensor_type)
                
                # 질문과 답변을 히스토리에 저장
                if user_question not in [q for q, _ in st.session_state.insights_answers]:
                    st.session_state.insights_answers.append((user_question, answer))
    
    # 질문-답변 히스토리 표시
    if st.session_state.insights_answers:
        st.subheader("질문 및 답변 기록")
        
        for i, (question, answer) in enumerate(st.session_state.insights_answers):
            with st.expander(f"Q: {question}", expanded=(i == len(st.session_state.insights_answers) - 1)):
                st.markdown(f"**A:** {answer}")
    
    # 질문-답변 초기화 버튼
    if st.session_state.insights_answers and st.button("질문-답변 초기화"):
        st.session_state.insights_answers = []
        st.rerun() 