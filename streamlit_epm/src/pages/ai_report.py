"""
DX-AI Manufacturing Copilot - AI 보고서 생성 페이지
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
from typing import Dict, Any, List

from src.core.ai_report_generator import (
    AIReportGenerator, 
    ReportGenerationConfig,
    create_report_generator
)
from src.core.llm_client import OllamaClient
from src.ui.styles import load_custom_css

# 페이지 설정은 메인 앱에서 이미 설정되므로 주석 처리
# st.set_page_config(
#     page_title="AI 보고서 생성",
#     page_icon="🤖",
#     layout="wide",
#     initial_sidebar_state="expanded"
# )

# 커스텀 스타일 적용
try:
    load_custom_css()
except:
    pass  # 스타일 적용이 실패해도 계속 진행

def show_ai_report_page():
    """AI 보고서 생성 페이지 표시"""
    st.title("🤖 AI 보고서 생성 시스템")
    st.markdown("LangGraph 기반 지능형 보고서 생성 도구")
    
    # 사이드바 - 보고서 설정
    with st.sidebar:
        st.header("📋 보고서 설정")
        
        # 보고서 유형 선택
        report_type = st.selectbox(
            "보고서 유형",
            options=[
                "production_summary",
                "quality_analysis", 
                "cost_analysis",
                "equipment_status"
            ],
            format_func=lambda x: {
                "production_summary": "생산 현황 보고서",
                "quality_analysis": "품질 분석 보고서",
                "cost_analysis": "비용 분석 보고서",
                "equipment_status": "설비 현황 보고서"
            }[x]
        )
        
        # 고급 설정
        with st.expander("고급 설정"):
            max_iterations = st.slider(
                "최대 반복 횟수",
                min_value=1,
                max_value=5,
                value=3,
                help="보고서 품질 개선을 위한 최대 반복 횟수"
            )
            
            quality_threshold = st.slider(
                "품질 임계값",
                min_value=0.5,
                max_value=1.0,
                value=0.7,
                step=0.1,
                help="보고서 품질 판정 기준"
            )
            
            temperature = st.slider(
                "창의성 수준",
                min_value=0.1,
                max_value=1.0,
                value=0.7,
                step=0.1,
                help="높을수록 창의적이지만 일관성이 떨어질 수 있음"
            )
            
            max_tokens = st.slider(
                "최대 토큰 수",
                min_value=512,
                max_value=4096,
                value=2048,
                step=256,
                help="생성되는 보고서의 최대 길이"
            )
    
    # 메인 영역
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📊 보고서 생성")
        
        # 보고서 매개변수 입력
        st.subheader("매개변수 설정")
        
        parameters = {}
        
        if report_type == "production_summary":
            parameters = _get_production_parameters()
        elif report_type == "quality_analysis":
            parameters = _get_quality_parameters()
        elif report_type == "cost_analysis":
            parameters = _get_cost_parameters()
        elif report_type == "equipment_status":
            parameters = _get_equipment_parameters()
        
        # 보고서 생성 버튼
        if st.button("🚀 보고서 생성", type="primary", use_container_width=True):
            _generate_report(
                report_type=report_type,
                parameters=parameters,
                max_iterations=max_iterations,
                quality_threshold=quality_threshold,
                temperature=temperature,
                max_tokens=max_tokens
            )
    
    with col2:
        st.header("🔄 워크플로우 시각화")
        
        # 그래프 시각화 표시
        _show_workflow_diagram()
        
        # 생성 기록
        st.subheader("📈 생성 기록")
        if "report_history" in st.session_state:
            history_df = pd.DataFrame(st.session_state.report_history)
            st.dataframe(history_df, use_container_width=True)
        else:
            st.info("아직 생성된 보고서가 없습니다.")
    
    # 생성된 보고서 표시
    if "current_report" in st.session_state:
        st.header("📄 생성된 보고서")
        _display_generated_report(st.session_state.current_report)


def _get_production_parameters() -> Dict[str, Any]:
    """생산 보고서 매개변수 설정"""
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input(
            "시작 날짜",
            value=datetime.now() - timedelta(days=30)
        )
        
        lot_numbers = st.text_area(
            "Lot 번호 (선택사항)",
            placeholder="LOT001, LOT002, ..."
        )
    
    with col2:
        end_date = st.date_input(
            "종료 날짜",
            value=datetime.now()
        )
        
        equipment_ids = st.text_area(
            "설비 ID (선택사항)",
            placeholder="EQ001, EQ002, ..."
        )
    
    include_metrics = st.multiselect(
        "포함할 지표",
        options=["생산량", "수율", "품질지표", "효율성", "가동률"],
        default=["생산량", "수율", "품질지표"]
    )
    
    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "lot_numbers": [x.strip() for x in lot_numbers.split(",") if x.strip()],
        "equipment_ids": [x.strip() for x in equipment_ids.split(",") if x.strip()],
        "include_metrics": include_metrics
    }


def _get_quality_parameters() -> Dict[str, Any]:
    """품질 분석 보고서 매개변수 설정"""
    col1, col2 = st.columns(2)
    
    with col1:
        quality_metrics = st.multiselect(
            "품질 지표",
            options=["순도", "일관성", "불순물", "물리적 특성", "화학적 특성"],
            default=["순도", "일관성"]
        )
        
        analysis_period = st.selectbox(
            "분석 기간",
            options=["1주일", "1개월", "3개월", "6개월", "1년"],
            index=1
        )
    
    with col2:
        test_types = st.multiselect(
            "시험 유형",
            options=["입고검사", "공정검사", "최종검사", "출하검사"],
            default=["공정검사", "최종검사"]
        )
        
        threshold_analysis = st.checkbox(
            "임계값 분석 포함",
            value=True
        )
    
    return {
        "quality_metrics": quality_metrics,
        "analysis_period": analysis_period,
        "test_types": test_types,
        "threshold_analysis": threshold_analysis
    }


def _get_cost_parameters() -> Dict[str, Any]:
    """비용 분석 보고서 매개변수 설정"""
    col1, col2 = st.columns(2)
    
    with col1:
        cost_categories = st.multiselect(
            "비용 범주",
            options=["원재료비", "노무비", "경비", "간접비", "품질비용"],
            default=["원재료비", "노무비", "경비"]
        )
        
        analysis_type = st.selectbox(
            "분석 유형",
            options=["월별", "분기별", "연별", "제품별", "Lot별"],
            index=0
        )
    
    with col2:
        comparison_period = st.selectbox(
            "비교 기간",
            options=["전월 대비", "전년 동월 대비", "목표 대비"],
            index=0
        )
        
        include_forecast = st.checkbox(
            "예측 분석 포함",
            value=False
        )
    
    return {
        "cost_categories": cost_categories,
        "analysis_type": analysis_type,
        "comparison_period": comparison_period,
        "include_forecast": include_forecast
    }


def _get_equipment_parameters() -> Dict[str, Any]:
    """설비 현황 보고서 매개변수 설정"""
    col1, col2 = st.columns(2)
    
    with col1:
        equipment_types = st.multiselect(
            "설비 유형",
            options=["반응기", "분리기", "건조기", "분쇄기", "포장기"],
            default=["반응기", "분리기"]
        )
        
        status_filter = st.multiselect(
            "상태 필터",
            options=["가동", "정지", "점검", "고장"],
            default=["가동", "정지", "점검"]
        )
    
    with col2:
        performance_metrics = st.multiselect(
            "성능 지표",
            options=["가동률", "효율성", "MTBF", "MTTR", "OEE"],
            default=["가동률", "효율성", "OEE"]
        )
        
        maintenance_analysis = st.checkbox(
            "정비 분석 포함",
            value=True
        )
    
    return {
        "equipment_types": equipment_types,
        "status_filter": status_filter,
        "performance_metrics": performance_metrics,
        "maintenance_analysis": maintenance_analysis
    }


def _generate_report(
    report_type: str,
    parameters: Dict[str, Any],
    max_iterations: int,
    quality_threshold: float,
    temperature: float,
    max_tokens: int
):
    """보고서 생성 실행"""
    
    # 생성 중 메시지 표시
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # 보고서 생성기 초기화
        status_text.text("보고서 생성기 초기화 중...")
        progress_bar.progress(10)
        
        generator = create_report_generator()
        
        # 설정 구성
        config = ReportGenerationConfig(
            report_type=report_type,
            parameters=parameters,
            max_iterations=max_iterations,
            quality_threshold=quality_threshold,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # 보고서 생성
        status_text.text("보고서 생성 중...")
        progress_bar.progress(30)
        
        report = generator.generate_report(config)
        
        progress_bar.progress(90)
        status_text.text("보고서 생성 완료!")
        
        # 세션 상태에 저장
        st.session_state.current_report = report
        
        # 생성 기록 업데이트
        if "report_history" not in st.session_state:
            st.session_state.report_history = []
        
        st.session_state.report_history.append({
            "생성시간": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "보고서타입": report_type,
            "제목": report.title,
            "길이": len(report.content)
        })
        
        progress_bar.progress(100)
        status_text.text("✅ 보고서 생성이 완료되었습니다!")
        
        # 성공 메시지
        st.success(f"🎉 보고서 '{report.title}'이 성공적으로 생성되었습니다!")
        
        # 페이지 새로고침 제거 - 보고서 생성 완료 후 자연스럽게 완료되도록 함
        # st.rerun()
        
    except Exception as e:
        st.error(f"❌ 보고서 생성 중 오류가 발생했습니다: {str(e)}")
        status_text.text("보고서 생성 실패")
        progress_bar.progress(0)


def _show_workflow_diagram():
    """워크플로우 다이어그램 표시"""
    st.markdown("""
    ```mermaid
    graph TD
        A[START] --> B[데이터 수집]
        B --> C[데이터 분석]
        C --> D[컨텍스트 생성]
        D --> E[보고서 생성]
        E --> F[보고서 검토]
        F --> G{품질 평가}
        G -->|품질 미달| E
        G -->|품질 통과| H[보고서 최종화]
        H --> I[END]
        
        style A fill:#e1f5fe
        style I fill:#e8f5e8
        style G fill:#fff3e0
        style E fill:#f3e5f5
        style F fill:#fff8e1
    ```
    """)
    
    # 워크플로우 단계 설명
    with st.expander("워크플로우 단계 설명"):
        st.markdown("""
        **1. 데이터 수집**: 선택된 보고서 유형에 따라 관련 데이터 수집
        
        **2. 데이터 분석**: LLM을 사용하여 수집된 데이터 분석 및 인사이트 도출
        
        **3. 컨텍스트 생성**: 분석 결과를 바탕으로 보고서 컨텍스트 생성
        
        **4. 보고서 생성**: LLM을 사용하여 구조화된 보고서 생성
        
        **5. 보고서 검토**: 생성된 보고서의 품질 검토 및 평가
        
        **6. 품질 평가**: 품질 점수가 임계값 이상인지 확인
        
        **7. 보고서 최종화**: 최종 보고서 모델 생성 및 저장
        """)


def _display_generated_report(report):
    """생성된 보고서 표시"""
    
    # 보고서 메타데이터
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("보고서 유형", report.report_type)
    
    with col2:
        st.metric("생성일시", report.created_at.strftime("%Y-%m-%d %H:%M"))
    
    with col3:
        st.metric("생성자", report.generated_by)
    
    # 보고서 내용
    st.subheader("📋 보고서 내용")
    
    # 탭으로 구분하여 표시
    tab1, tab2, tab3 = st.tabs(["📄 보고서", "📊 메타데이터", "🔧 매개변수"])
    
    with tab1:
        st.markdown(report.content)
    
    with tab2:
        metadata = {
            "ID": report.id,
            "제목": report.title,
            "유형": report.report_type,
            "생성일시": report.created_at.isoformat(),
            "생성자": report.generated_by,
            "데이터 소스": report.data_sources,
            "내용 길이": len(report.content)
        }
        
        for key, value in metadata.items():
            st.write(f"**{key}**: {value}")
    
    with tab3:
        if report.parameters:
            st.json(report.parameters)
        else:
            st.info("설정된 매개변수가 없습니다.")
    
    # 보고서 다운로드
    st.subheader("💾 보고서 다운로드")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 텍스트 파일 다운로드
        st.download_button(
            label="📄 텍스트 파일 다운로드",
            data=report.content,
            file_name=f"{report.title}.txt",
            mime="text/plain"
        )
    
    with col2:
        # JSON 파일 다운로드
        report_json = {
            "id": report.id,
            "title": report.title,
            "report_type": report.report_type,
            "content": report.content,
            "created_at": report.created_at.isoformat(),
            "generated_by": report.generated_by,
            "data_sources": report.data_sources,
            "parameters": report.parameters
        }
        
        st.download_button(
            label="📊 JSON 파일 다운로드",
            data=json.dumps(report_json, ensure_ascii=False, indent=2),
            file_name=f"{report.title}.json",
            mime="application/json"
        )


def _show_llm_status():
    """LLM 상태 표시"""
    try:
        client = OllamaClient()
        if client.is_available():
            st.success("✅ LLM 서버 연결됨")
            
            # 모델 정보 표시
            model_info = client.get_model_info()
            st.info(f"현재 모델: {model_info.get('model', 'Unknown')}")
        else:
            st.error("❌ LLM 서버 연결 실패")
            st.warning("Ollama 서버가 실행 중인지 확인해주세요.")
    except Exception as e:
        st.error(f"❌ LLM 상태 확인 실패: {str(e)}")


if __name__ == "__main__":
    show_ai_report_page() 