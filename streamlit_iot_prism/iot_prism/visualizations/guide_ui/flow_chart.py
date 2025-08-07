"""
분석 흐름도 렌더링 모듈

이 모듈은 시각화 추천의 분석 흐름도를 렌더링하는 함수를 제공합니다.
"""

import streamlit as st
import os
import base64
import json
from iot_prism.utils import get_font_path  # 폰트 경로 가져오기

def render_analysis_flow_chart(recommendations):
    """
    시각화 흐름도 차트를 렌더링합니다.
    
    Args:
        recommendations (list): 추천 항목 목록
        
    Returns:
        str: 차트를 렌더링할 HTML 코드
    """
    # 빈 목록이면 빈 문자열 반환
    if not recommendations:
        return ""
    
    # 노드와 엣지 데이터
    nodes = []
    edges = []
    
    # 색상 정의 (파스텔 색상)
    pastel_colors = {
        "start": "#B5EAD7",  # 연한 녹색
        "recommendation": "#FDFD96",  # 연한 노랑
        "visualization": "#A7C7E7",  # 연한 파랑
        "end": "#FFB3BA"  # 연한 분홍
    }
    
    # 시작 노드
    nodes.append({
        "id": "start",
        "label": "데이터 분석 시작",
        "color": pastel_colors["start"]
    })
    
    # 추천 분석 노드
    for i, rec in enumerate(recommendations):
        node_id = f"rec_{i}"
        nodes.append({
            "id": node_id,
            "label": rec['목적'],
            "color": pastel_colors["recommendation"]
        })
        
        # 엣지 연결
        if i == 0:
            # 첫 번째 추천은 시작에서 연결
            edges.append({
                "from": "start",
                "to": node_id
            })
        else:
            # 이전 추천에서 연결
            edges.append({
                "from": f"rec_{i-1}",
                "to": node_id
            })
        
        # 세부 시각화 노드
        for j, viz_type in enumerate(rec['추천 시각화']):
            viz_id = f"viz_{i}_{j}"
            nodes.append({
                "id": viz_id,
                "label": viz_type,
                "color": pastel_colors["visualization"]
            })
            
            # 추천에서 시각화로 연결
            edges.append({
                "from": node_id,
                "to": viz_id
            })
    
    # 종료 노드
    nodes.append({
        "id": "end",
        "label": "분석 완료",
        "color": pastel_colors["end"]
    })
    
    # 마지막 추천에서 종료로 연결
    if recommendations:
        edges.append({
            "from": f"rec_{len(recommendations)-1}",
            "to": "end"
        })
    
    # Network 차트 생성을 위한 HTML 코드
    # JSON 문자열로 변환하고, 따옴표 처리를 올바르게 수행
    nodes_json = json.dumps(nodes)
    edges_json = json.dumps(edges)
    
    # Paperlogy 폰트 포함
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
            
            #analysis-flow-container, .vis-network, .vis-node, .vis-label {{
                font-family: 'Paperlogy', sans-serif !important;
            }}
            """
        except Exception as e:
            # 오류 시 Noto Sans KR 폰트 사용
            font_css = """
            @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');
            
            #analysis-flow-container, .vis-network, .vis-node, .vis-label {
                font-family: 'Noto Sans KR', sans-serif !important;
            }
            """
    else:
        # 폰트 파일이 없는 경우
        font_css = """
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');
        
        #analysis-flow-container, .vis-network, .vis-node, .vis-label {
            font-family: 'Noto Sans KR', sans-serif !important;
        }
        """
    
    html_code = f"""
    <style>
        {font_css}
        
        #analysis-flow-container {{
            width: 100%;
            height: 600px;
            border: 1px solid #ccc;
            border-radius: 5px;
            background-color: #fafafa;
        }}
        
        .vis-node {{
            border-width: 2px !important;
            box-shadow: 3px 3px 5px rgba(0,0,0,0.1) !important;
        }}
        
        .vis-node .vis-label {{
            font-weight: 500;
        }}
    </style>
    
    <div id="analysis-flow-container"></div>
    
    <script src="https://cdnjs.cloudflare.com/ajax/libs/vis/4.21.0/vis.min.js"></script>
    <script>
        // 노드와 엣지 데이터
        var nodes = new vis.DataSet({nodes_json});
        var edges = new vis.DataSet({edges_json});
        
        // 컨테이너 엘리먼트
        var container = document.getElementById('analysis-flow-container');
        
        // 데이터 및 옵션
        var data = {{
            nodes: nodes,
            edges: edges
        }};
        
        var options = {{
            nodes: {{
                shape: 'box',
                size: 30,
                font: {{
                    size: 14,
                    color: '#333',
                    face: '{("Paperlogy" if os.path.exists(font_path) else "Noto Sans KR")}'
                }},
                borderWidth: 2,
                shadow: true,
                shapeProperties: {{
                    borderRadius: 8
                }}
            }},
            edges: {{
                width: 2,
                color: {{
                    color: '#999',
                    highlight: '#555'
                }},
                arrows: {{
                    to: {{
                        enabled: true,
                        scaleFactor: 1
                    }}
                }},
                smooth: {{
                    type: 'curvedCW',
                    roundness: 0.2
                }}
            }},
            layout: {{
                hierarchical: {{
                    direction: 'UD',
                    sortMethod: 'directed',
                    levelSeparation: 120,
                    nodeSpacing: 170
                }}
            }},
            physics: false,
            interaction: {{
                hover: true,
                zoomView: true
            }}
        }};
        
        // 네트워크 생성
        var network = new vis.Network(container, data, options);
        
        // CSS 정의가 적용되도록 노드 리드로우 실행
        setTimeout(function() {{
            network.redraw();
        }}, 100);
    </script>
    """
    
    return html_code 