"""
카드 UI 렌더링 모듈

이 모듈은 시각화 추천 카드를 렌더링하는 함수를 제공합니다.
"""

import streamlit as st
import os
import base64
import json
from ..guide_data.recommendations import ANALYSIS_RECOMMENDATIONS
from iot_prism.utils import get_font_path  # 폰트 경로 가져오기

def render_recommendation_card(recommendation, index):
    """추천 카드를 렌더링합니다"""
    # 추천 시각화 HTML 구성
    viz_html = ""
    
    # 시각화 항목 수 계산
    viz_count = len(recommendation['추천 시각화'])
    
    # 전체 시각화 항목 길이 계산 (설명 텍스트 길이에 따른 추가 높이 계산용)
    total_viz_description_length = 0
    
    # 시각화 타입과 메뉴 매핑
    visualization_menu_mapping = {
        "시계열 차트": "시계열 차트",
        "시계열 플롯": "시계열 차트",
        "이동 평균선": "시계열 차트",
        "히스토그램": "히스토그램",
        "확률 분포": "히스토그램",
        "정규분포 비교": "히스토그램",
        "박스 플롯": "박스 플롯",
        "박스 다이어그램": "박스 플롯",
        "히트맵": "히트맵",
        "주파수 분석": "주파수 분석(FFT)",
        "FFT": "주파수 분석(FFT)",
        "시간-주파수 분석": "시간-주파수 분석",
        "웨이블릿 분석": "시간-주파수 분석",
        "클러스터링": "패턴 클러스터링",
        "패턴 클러스터링": "패턴 클러스터링",
        "상관관계": "상관관계 분석",
        "상관 분석": "상관관계 분석",
        "분포 비교": "분포 비교",
        "이상치": "이상치 분석",
        "이상치 분석": "이상치 분석",
        "운전/중지 패턴 분리 이상치 분석": "이상치 분석",
        "상태별 이상치 분석": "이상치 분석",
        "운전/정지 주기 분석": "운전/정지 주기 분석",
        "운전 주기 분석": "운전/정지 주기 분석",
        "정지 주기 분석": "운전/정지 주기 분석",
        "작동 주기 패턴": "운전/정지 주기 분석",
        "주기 감지": "운전/정지 주기 분석",
        "주기 타임라인": "운전/정지 주기 분석",
        "주기 분포": "운전/정지 주기 분석",
        "주기 이상치 분석": "운전/정지 주기 분석",
        "주기 지속시간 분석": "운전/정지 주기 분석",
        "주기 통계 분석": "운전/정지 주기 분석",
        "3D 시각화": "3D 데이터 시각화",
        "3D 플롯": "3D 데이터 시각화",
        "경보": "경보 및 임계값 설정",
        "임계값": "경보 및 임계값 설정",
        "QQ플롯": "히스토그램",
        "바이올린 플롯": "분포 비교",
        "산점도": "상관관계 분석",
        "일별 패턴": "일별/시간별 패턴",
        "시간별 패턴": "일별/시간별 패턴",
        "추세 분석": "트렌드 분석",
        "트렌드 분석": "트렌드 분석"
    }
    
    for viz_type in recommendation['추천 시각화']:
        # 추천 목적에 맞는 시각화 항목 가져오기
        viz_details = next((item for item in ANALYSIS_RECOMMENDATIONS.get(recommendation['목적'], []) 
                          if item['type'] == viz_type), None)
        
        # 설명 텍스트 길이 누적
        if viz_details and 'description' in viz_details:
            total_viz_description_length += len(viz_details['description'])
        
        # 시각화 유형에 따른 아이콘 결정 - 텍스트 기호로 변경
        if "시계열" in viz_type:
            icon = "📈"
        elif "히스토그램" in viz_type:
            icon = "📊"
        elif "박스" in viz_type:
            icon = "📦"
        elif "히트맵" in viz_type:
            icon = "🎨"
        elif "주파수" in viz_type or "FFT" in viz_type:
            icon = "〰️"
        elif "클러스터링" in viz_type:
            icon = "🔄"
        elif "상관관계" in viz_type:
            icon = "🔗"
        elif "분포" in viz_type:
            icon = "📉"
        elif "이상치" in viz_type:
            icon = "⚠️"
        elif "3D" in viz_type:
            icon = "🧊"
        elif "경보" in viz_type or "임계값" in viz_type:
            icon = "🔔"
        elif "QQ" in viz_type:
            icon = "📏"
        elif "바이올린" in viz_type:
            icon = "🎻"
        elif "산점도" in viz_type:
            icon = "🔹"
        else:
            icon = "📊"  # 기본 아이콘
        
        # 시각화 메뉴와 매핑 확인
        menu_value = None
        
        # 1. 먼저 정확한 일치 확인 (exact match)
        if viz_type in visualization_menu_mapping:
            menu_value = visualization_menu_mapping[viz_type]
        else:
            # 2. 정확한 일치가 없을 경우, 가장 긴 부분 문자열 매칭 시도
            # 매칭된 키의 길이와 값을 저장할 변수
            max_match_length = 0
            max_match_value = None
            
            for key, value in visualization_menu_mapping.items():
                if key in viz_type and len(key) > max_match_length:
                    max_match_length = len(key)
                    max_match_value = value
            
            # 가장 긴 매칭이 있으면 사용
            if max_match_value:
                menu_value = max_match_value
            else:
                menu_value = "시각화 가이드"  # 기본값
        
        # 클릭 가능한 항목으로 변경
        if viz_details:
            viz_html += f"""
            <div class="viz-item clickable" onclick="changeVisualization('{menu_value}')">
                <div class="viz-icon">{icon}</div>
                <div class="viz-content">
                    <div class="viz-title">{viz_details['type']}</div>
                    <div class="viz-desc">{viz_details['description']}</div>
                </div>
            </div>
            """
        else:
            # 기본 정의에 없는 경우, 타입명과 기본 설명 추가
            default_desc = "데이터 특성을 시각적으로 분석"
            viz_html += f"""
            <div class="viz-item clickable" onclick="changeVisualization('{menu_value}')">
                <div class="viz-icon">{icon}</div>
                <div class="viz-content">
                    <div class="viz-title">{viz_type}</div>
                    <div class="viz-desc">{default_desc}</div>
                </div>
            </div>
            """
    
    # 파스텔 톤 레인보우 색상 팔레트 (빨주노초파남보 순서)
    rainbow_pastel_colors = [
        "#FFCCCC",  # Pastel Red
        "#FFE5CC",  # Pastel Orange
        "#FFFFCC",  # Pastel Yellow
        "#E5FFCC",  # Pastel Lime
        "#CCFFCC",  # Pastel Green
        "#CCFFE5",  # Pastel Mint
        "#CCFFFF",  # Pastel Cyan
        "#CCE5FF",  # Pastel Light Blue
        "#CCCCFF",  # Pastel Blue
        "#E5CCFF",  # Pastel Purple
        "#FFCCFF",  # Pastel Pink
        "#FFCCE5",  # Pastel Rose
        "#CCEEFF",  # Pastel Sky Blue
        "#DDDDFF",  # Pastel Lavender
        "#FFDDDD",  # Pastel Coral
        "#DDFFDD",  # Pastel Mint Green
        "#DDBAFF",  # Pastel Indigo/Purple
        "#E6C0FF"   # Pastel Violet
    ]
    
    # 추천 순서에 따라 색상 결정 (무지개 순서 반복)
    card_color = rainbow_pastel_colors[index % len(rainbow_pastel_colors)]
        
    # Paperlogy 폰트 CSS 직접 포함
    font_path = get_font_path()
    font_css = ""
    
    if os.path.exists(font_path):
        try:
            # 폰트 파일을 base64로 인코딩
            with open(font_path, "rb") as font_file:
                encoded_font = base64.b64encode(font_file.read()).decode()
                
            # 폰트 CSS 생성
            font_css = f"""
            @font-face {{
                font-family: 'Paperlogy';
                src: url(data:font/ttf;base64,{encoded_font});
                font-weight: normal;
                font-style: normal;
            }}

            * {{
                font-family: 'Paperlogy', sans-serif !important;
            }}

            /* 모든 텍스트 요소에 강제 적용 */
            p, h1, h2, h3, h4, h5, h6, div, span, button, a, input, textarea, select, label, code {{
                font-family: 'Paperlogy', sans-serif !important;
            }}

            /* 시각화 카드 스타일 통일 */
            .recommendation-card {{
                font-family: 'Paperlogy', sans-serif !important;
            }}
            
            .card-title {{
                font-family: 'Paperlogy', sans-serif !important;
                font-weight: 700;
            }}
            
            .viz-title {{
                font-family: 'Paperlogy', sans-serif !important;
                font-weight: 500;
            }}
            
            .viz-desc {{
                font-family: 'Paperlogy', sans-serif !important;
                font-weight: 300;
            }}
            """
        except Exception:
            # 오류 발생 시 웹 폰트 사용
            font_css = """
            @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');
            """
    else:
        # 폰트 파일이 없는 경우 웹 폰트 사용
        font_css = """
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');
        """
    
    # 추가 설명 HTML 구성 (있는 경우)
    additional_info_html = ""
    if "추가 설명" in recommendation:
        additional_info_html = f"""
        <div class="additional-info">
            <div class="additional-info-header">
                분석 인사이트
            </div>
            <div class="additional-info-content">
                {recommendation['추가 설명']}
            </div>
        </div>
        """
    
    # JavaScript 함수 추가 (시각화 변경 기능)
    js_code = """
    <script>
    function changeVisualization(vizType) {
        try {
            // 직접 URL 변경하여 페이지 이동
            let currentURL = location.href;
            let mainWindow = window;
            
            // 최상위 창으로 이동 시도 (iframe 내에서 실행될 경우)
            try {
                if (window.parent && window.parent !== window) {
                    mainWindow = window.parent;
                }
                if (window.top && window.top !== window) {
                    mainWindow = window.top;
                }
                currentURL = mainWindow.location.href;
            } catch (e) {
                console.log("최상위 창 접근 실패, 현재 창 사용:", e);
            }
            
            console.log("선택한 시각화:", vizType);
            
            // 사용자에게 직접 시각화 메뉴 선택 안내
            alert("시각화 메뉴를 직접 선택해 주세요: " + vizType);
            
        } catch (error) {
            console.error("시각화 변경 중 오류 발생:", error);
            alert("죄송합니다. 시각화 메뉴 '" + vizType + "'를 직접 선택해 주세요.");
        }
    }
    </script>
    """
    
    # 카드 HTML
    card_html = f"""
    <style>
        {font_css}
        
        .recommendation-card {{
            margin-bottom: 15px;  /* 일관된 하단 간격 적용 */
            margin-top: 0px; /* 상단 마진 제거 */
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            border-left: 5px solid {card_color};
            background: white;
            font-family: 'Paperlogy', 'Noto Sans KR', sans-serif !important;
        }}
        .card-header {{
            padding: 15px 20px;
            background-color: {card_color};
            color: #444;
            display: flex;
            align-items: center;
            font-family: 'Paperlogy', 'Noto Sans KR', sans-serif !important;
        }}
        .card-number {{
            font-size: 24px;
            font-weight: bold;
            margin-right: 15px;
            background: rgba(255,255,255,0.5);
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: 'Paperlogy', 'Noto Sans KR', sans-serif !important;
        }}
        .card-title {{
            font-size: 20px;
            font-weight: bold;
            font-family: 'Paperlogy', 'Noto Sans KR', sans-serif !important;
        }}
        .card-reason {{
            padding: 12px 20px;
            background: #f9f9f9;
            border-bottom: 1px solid #eee;
            font-family: 'Paperlogy', 'Noto Sans KR', sans-serif !important;
        }}
        .viz-container {{
            padding: 12px 20px;
            font-family: 'Paperlogy', 'Noto Sans KR', sans-serif !important;
        }}
        .viz-header {{
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 12px;
            color: #555;
            font-family: 'Paperlogy', 'Noto Sans KR', sans-serif !important;
        }}
        .viz-item {{
            display: flex;
            margin-bottom: 8px;
            padding: 8px;
            background: #f5f5f5;
            border-radius: 5px;
            border-left: 3px solid {card_color};
            font-family: 'Paperlogy', 'Noto Sans KR', sans-serif !important;
        }}
        .viz-item:hover {{
            background: #efefef;
        }}
        /* 클릭 가능한 항목 스타일 */
        .clickable {{
            cursor: pointer;
            transition: all 0.2s ease;
            position: relative;
            border: 1px solid #ddd;
            border-radius: 6px;
            margin-bottom: 10px;
            background: linear-gradient(to bottom, #f8f8f8, #f0f0f0);
        }}
        .clickable:hover {{
            background: linear-gradient(to bottom, #fff, #e8e8e8);
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            border: 1px solid #aaa;
        }}
        .clickable::before {{
            content: "\\1F517";  /* 링크 아이콘 */
            position: absolute;
            left: 8px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 14px;
            color: #007bff;
            opacity: 0.8;
        }}
        .clickable::after {{
            content: "클릭하여 선택";
            position: absolute;
            right: 10px;
            top: 50%;
            transform: translateY(-50%);
            background-color: #007bff;
            color: white;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 11px;
            opacity: 0;
            transition: opacity 0.3s ease;
            pointer-events: none;
            font-weight: bold;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }}
        .clickable:hover::after {{
            opacity: 1;
        }}
        .viz-icon {{
            margin-right: 15px;
            width: 30px;
            height: 30px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #444;
        }}
        .viz-content {{
            flex: 1;
        }}
        .viz-title {{
            font-weight: bold;
            margin-bottom: 4px;
            font-family: 'Paperlogy', 'Noto Sans KR', sans-serif !important;
            color: #007bff;
        }}
        .viz-desc {{
            font-size: 14px;
            color: #666;
            font-family: 'Paperlogy', 'Noto Sans KR', sans-serif !important;
        }}
        .additional-info {{
            margin-top: 8px;
            padding: 12px;
            background-color: #f0f7ff;
            border-radius: 5px;
            border-left: 3px solid {card_color};
        }}
        .additional-info-header {{
            font-weight: bold;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            color: #444;
        }}
        .additional-info-content {{
            font-size: 14px;
            line-height: 1.5;
            color: #555;
        }}
    </style>
    {js_code}
    <div class="recommendation-card">
        <div class="card-header">
            <div class="card-number">{index+1}</div>
            <div class="card-title">{recommendation['목적']}</div>
        </div>
        <div class="card-reason">
            <strong>추천 이유:</strong> {recommendation['추천 이유']}
        </div>
        <div class="viz-container">
            <div class="viz-header">추천 시각화 <small style="color:#666;font-weight:normal;">(클릭하여 해당 메뉴로 이동)</small>:</div>
            {viz_html}
            {additional_info_html}
        </div>
    </div>
    """
    
    # 각 시각화 항목당 높이 계산 (설명 텍스트 길이에 따라 조정)
    # 기본 카드 높이 + 각 시각화 항목당 추가 높이 + 추가 설명 높이
    base_height = 170  # 기본 높이
    
    # 항목당 기본 높이 + 설명 길이에 따른 추가 높이
    viz_item_base_height = 65  # 항목당 기본 높이
    
    # 전체 아이템 높이 계산
    viz_items_height = 0
    for viz_type in recommendation['추천 시각화']:
        # 각 아이템별 높이 계산
        item_height = viz_item_base_height
        viz_details = next((item for item in ANALYSIS_RECOMMENDATIONS.get(recommendation['목적'], []) 
                          if item['type'] == viz_type), None)
        
        # 설명 텍스트가 길 경우 추가 높이 부여
        if viz_details and 'description' in viz_details:
            desc_length = len(viz_details['description'])
            if desc_length > 30:
                item_height += min(70, (desc_length - 30) // 8 * 5)  # 8자마다 5px 추가, 최대 70px
        
        viz_items_height += item_height
    
    # 추가 설명과 추천 이유 높이 계산
    additional_info_height = 100 if "추가 설명" in recommendation else 0
    
    # 추천 이유 텍스트 길이에 따른 추가 높이
    reason_length = len(recommendation['추천 이유'])
    reason_additional_height = max(0, (reason_length - 70) // 15 * 12)  # 15자마다 12px 추가
    
    # 여백을 위한 추가 높이 (축소)
    padding_height = 15
    
    # 전체 높이 계산
    total_height = base_height + viz_items_height + additional_info_height + reason_additional_height + padding_height
    
    # 높이 최소값 보장
    total_height = max(total_height, 200 + viz_count * 40)  # 최소 높이 보장
    
    # HTML 렌더링
    st.components.v1.html(card_html, height=total_height) 