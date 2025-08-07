import streamlit as st
import pandas as pd
from datetime import datetime
import base64
from ..utils import get_equipment_type, get_sensor_type
from .insights_sections import (
    generate_summary_section, 
    generate_statistics_section, 
    generate_trend_section,
    generate_anomaly_section, 
    generate_patterns_section, 
    generate_recommendations_section
)


def generate_insights_report(df, equipment_type, sensor_type, report_type, include_visuals, analysis_depth, include_recommendations):
    """실제 인사이트 리포트를 생성하는 함수"""
    # 리포트 기본 정보
    report = {
        'title': f"{report_type} - {equipment_type} {sensor_type} 데이터",
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'equipment_type': equipment_type,
        'sensor_type': sensor_type,
        'data_range': {
            'start_date': df['timestamp'].min().strftime("%Y-%m-%d %H:%M:%S"),
            'end_date': df['timestamp'].max().strftime("%Y-%m-%d %H:%M:%S"),
            'duration_days': (df['timestamp'].max() - df['timestamp'].min()).total_seconds() / 86400,
            'total_records': len(df)
        },
        'sections': [],
        'markdown': ''  # 마크다운 형식의 전체 리포트
    }
    
    # 리포트 유형에 따른 섹션 구성
    section_generators = {
        "종합 분석 리포트": [
            generate_summary_section,
            generate_statistics_section,
            generate_trend_section,
            generate_anomaly_section,
            generate_patterns_section,
            generate_recommendations_section
        ],
        "이상치 분석 리포트": [
            generate_summary_section,
            generate_anomaly_section,
            generate_statistics_section,
            generate_recommendations_section
        ],
        "패턴 분석 리포트": [
            generate_summary_section,
            generate_patterns_section,
            generate_statistics_section,
            generate_recommendations_section
        ],
        "성능 추세 리포트": [
            generate_summary_section,
            generate_trend_section,
            generate_statistics_section,
            generate_recommendations_section
        ]
    }
    
    # 선택된 리포트 유형에 맞는 섹션 생성 함수 리스트 가져오기
    selected_section_generators = section_generators.get(report_type, section_generators["종합 분석 리포트"])
    
    # 섹션 생성
    for section_generator in selected_section_generators:
        # 권장 사항 섹션이고 사용자가 권장 사항 포함을 선택하지 않은 경우 건너뜀
        if section_generator == generate_recommendations_section and not include_recommendations:
            continue
        
        # 섹션 생성 호출
        section = section_generator(df, equipment_type, sensor_type, analysis_depth, include_visuals)
        report['sections'].append(section)
    
    # 마크다운 리포트 생성
    report['markdown'] = generate_markdown_report(report, include_visuals)
    
    # 세션 히스토리에 기록 저장
    # insights_analysis_history 키 확인 및 초기화
    if 'insights_analysis_history' not in st.session_state:
        st.session_state.insights_analysis_history = []
    
    # 히스토리에 현재 리포트 추가
    report_entry = {
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'report_type': report_type,
        'equipment_type': equipment_type,
        'sensor_type': sensor_type,
        'description': f"{report_type} - {equipment_type} {sensor_type}",
        'type': '인사이트 리포트'
    }
    st.session_state.insights_analysis_history.append(report_entry)
    
    # AI 분석을 위한 히스토리 형식으로도 저장
    history_key = "insights_analysis_history"
    if history_key not in st.session_state:
        st.session_state[history_key] = []
    
    st.session_state[history_key].append({
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'description': f"{report_type} - {equipment_type} {sensor_type}",
        'type': '인사이트 리포트'
    })
    
    return report


def display_insights_report(report):
    """생성된 인사이트 리포트를 표시하는 함수"""
    if not report:
        st.warning("표시할 리포트가 없습니다.")
        return
    
    st.markdown(f"## {report['title']}")
    st.caption(f"생성 시간: {report['timestamp']}")
    
    # 데이터 기간 정보
    st.markdown("### 데이터 정보")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("시작 날짜", report['data_range']['start_date'].split()[0])
    with col2:
        st.metric("종료 날짜", report['data_range']['end_date'].split()[0])
    with col3:
        st.metric("기간", f"{report['data_range']['duration_days']:.1f}일")
    
    # 각 섹션 표시
    for section in report['sections']:
        st.markdown(f"### {section['title']}")
        
        # 섹션 내용 표시
        st.markdown(section['content'])
        
        # 이미지가 있는 경우 표시
        if 'image' in section and section['image']:
            try:
                # base64 인코딩된 이미지 표시
                st.image(base64.b64decode(section['image']), use_container_width=True)
            except:
                st.warning("이미지를 표시할 수 없습니다.")
        
        # 표가 있는 경우 표시
        if 'table' in section and isinstance(section['table'], pd.DataFrame) and not section['table'].empty:
            st.dataframe(section['table'])
    
    # 전체 리포트 확인
    with st.expander("전체 마크다운 리포트 보기", expanded=False):
        # CSS 스타일 직접 적용
        
        # 마크다운용 CSS 스타일 적용
        st.markdown("""
        <style>
        .stMarkdown h1 {
            color: #0D47A1;
            padding-bottom: 10px;
            border-bottom: 2px solid #1976D2;
        }
        
        .stMarkdown h2 {
            color: #1976D2;
            padding-bottom: 5px;
            border-bottom: 1px solid #BBDEFB;
            margin-top: 30px;
        }
        
        .stMarkdown table {
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }
        
        .stMarkdown th, .stMarkdown td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        
        .stMarkdown th {
            background-color: #E3F2FD;
            color: #0D47A1;
        }
        
        .stMarkdown tr:nth-child(even) {
            background-color: #f2f2f2;
        }
        
        .stMarkdown img {
            max-width: 100%;
            display: block;
            margin: 20px auto;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        
        .stMarkdown code {
            background-color: #f5f5f5;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: monospace;
        }
        
        .stMarkdown blockquote {
            border-left: 4px solid #1976D2;
            margin: 20px 0;
            padding: 10px 20px;
            background-color: #E3F2FD;
        }
        
        .stMarkdown hr {
            border: 0;
            height: 1px;
            background-color: #ddd;
            margin: 30px 0;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # CSS 스타일 부분 제거하고 마크다운 내용만 표시
        markdown_content = report['markdown']
        # CSS 스타일 부분 제거 - <style>...</style> 태그 제거
        if markdown_content.startswith("<style>"):
            style_end_idx = markdown_content.find("</style>")
            if style_end_idx > 0:
                markdown_content = markdown_content[style_end_idx + 9:].strip()
        
        st.markdown(markdown_content)


def generate_markdown_report(report, include_visuals):
    """마크다운 형식의 전체 리포트를 생성하는 함수"""
    # 마크다운 내용만 포함 (스타일은 나중에 적용)
    md = ""
    
    md += f"# {report['title']}\n\n"
    md += f"생성 시간: {report['timestamp']}\n\n"
    
    # 데이터 범위 정보
    md += "## 데이터 정보\n\n"
    md += f"- 설비 유형: {report['equipment_type']}\n"
    md += f"- 센서 유형: {report['sensor_type']}\n"
    md += f"- 시작 날짜: {report['data_range']['start_date']}\n"
    md += f"- 종료 날짜: {report['data_range']['end_date']}\n"
    md += f"- 기간: {report['data_range']['duration_days']:.1f}일\n"
    md += f"- 총 레코드 수: {report['data_range']['total_records']:,}개\n\n"
    
    # 각 섹션 내용 추가
    for section in report['sections']:
        md += f"## {section['title']}\n\n"
        md += f"{section['content']}\n\n"
        
        # 이미지가 있고 include_visuals가 True인 경우
        if include_visuals and 'image' in section and section['image']:
            md += f"![{section['title']}](data:image/png;base64,{section['image']})\n\n"
    
    # 각주
    md += "---\n"
    md += f"이 리포트는 IoT Prism에서 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}에 자동 생성되었습니다."
    
    return md 