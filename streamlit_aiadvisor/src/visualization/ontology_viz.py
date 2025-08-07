"""
온톨로지 시각화 모듈
온톨로지(TTL) 파일을 3D 그래프로 시각화하는 기능 제공
"""
import networkx as nx
import plotly.graph_objects as go
import rdflib
from rdflib import Graph, URIRef, Literal, RDF, RDFS
from typing import Dict, List, Tuple, Any, Optional
import json
import re

def safe_json_text(text: str) -> str:
    """
    JSON 파싱 오류를 방지하기 위한 안전한 텍스트 처리
    
    Args:
        text (str): 처리할 텍스트
        
    Returns:
        str: JSON 안전한 텍스트
    """
    if not text:
        return ""
    
    try:
        # 문자열로 변환
        text = str(text)
        
        # 이모지를 안전한 텍스트로 대체
        emoji_replacements = {
            '🌐': 'GLOBE',
            '🎯': 'TARGET', 
            '📍': 'PIN',
            '🔗': 'LINK',
            '🏷️': 'TAG',
            '📊': 'CHART',
            '🌟': 'STAR',
            '⭐': 'STAR',
            '💫': 'STAR',
            '🔸': 'DIAMOND',
            '✅': 'OK',
            '❌': 'ERROR',
            '⚠️': 'WARNING',
            '🔍': 'SEARCH',
            '🎨': 'COLOR',
            '🔧': 'TOOL',
            '🔒': 'LOCK',
            '🆕': 'NEW',
            '🔴': 'RED',
            '🟡': 'YELLOW',
            '🟢': 'GREEN',
            '💡': 'BULB'
        }
        
        for emoji, replacement in emoji_replacements.items():
            text = text.replace(emoji, replacement)
        
        # 제어 문자 제거
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        
        # json.dumps를 사용해서 안전하게 이스케이프
        escaped = json.dumps(text, ensure_ascii=False)[1:-1]  # 양쪽 따옴표 제거
        
        return escaped
        
    except Exception as e:
        # 실패 시 기본 처리
        return escape_for_json(text)

def escape_for_json(text: str) -> str:
    """
    JSON 직렬화를 위한 안전한 문자열 이스케이프
    
    Args:
        text (str): 이스케이프할 텍스트
        
    Returns:
        str: 안전하게 이스케이프된 텍스트
    """
    if not text:
        return ""
    
    # 문자열로 변환
    text = str(text)
    
    # JSON에서 반드시 이스케이프해야 하는 문자들 처리
    text = text.replace('\\', '\\\\')  # 백슬래시
    text = text.replace('"', '\\"')   # 큰따옴표
    text = text.replace('\n', ' ')    # 개행문자는 공백으로 변경
    text = text.replace('\r', ' ')    # 캐리지 리턴도 공백으로
    text = text.replace('\t', ' ')    # 탭도 공백으로
    
    # 제어 문자 제거
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    
    # 유효하지 않은 유니코드 시퀀스 제거
    text = re.sub(r'\\u[0-9a-fA-F]{0,3}(?![0-9a-fA-F])', '', text)
    
    # NULL 문자 및 기타 문제 문자 제거
    text = text.replace('\x00', '')
    
    # 연속된 공백을 하나로 정리
    text = re.sub(r'\s+', ' ', text)
    
    # 앞뒤 공백 제거
    text = text.strip()
    
    return text

def load_ontology_graph(ttl_file_path: str) -> rdflib.Graph:
    """
    TTL 파일에서 온톨로지 그래프를 로드
    
    Args:
        ttl_file_path (str): TTL 파일 경로
        
    Returns:
        rdflib.Graph: 로드된 RDF 그래프
    """
    g = rdflib.Graph()
    g.parse(ttl_file_path, format="turtle")
    return g

def create_networkx_graph(g: rdflib.Graph) -> Tuple[nx.Graph, Dict[str, Any], Dict[str, str], Dict[Tuple[str, str], str]]:
    """
    RDF 그래프를 NetworkX 그래프로 변환
    
    Args:
        g (rdflib.Graph): RDF 그래프
        
    Returns:
        Tuple[nx.Graph, Dict[str, Any], Dict[str, str], Dict[Tuple[str, str], str]]: 
            NetworkX 그래프, 노드 타입 맵, 노드 레이블 맵, 엣지 레이블 맵
    """
    # NetworkX 그래프 생성
    G = nx.Graph()
    
    # 노드 및 엣지 정보 추출
    nodes = {}
    node_types = {}
    node_labels = {}
    
    # 노드 추가 (RDF.type이 있는 경우)
    for s, p, o in g.triples((None, RDF.type, None)):
        node_id = str(s)
        if node_id not in nodes:
            nodes[node_id] = len(nodes)
            G.add_node(node_id)
            node_types[node_id] = str(o).split('#')[-1]
            
            # 노드 레이블 가져오기 - 안전한 텍스트 처리 적용
            label = g.value(s, RDFS.label)
            if label:
                node_labels[node_id] = safe_json_text(str(label))
            else:
                extracted_label = node_id.split('#')[-1].split('/')[-1]
                node_labels[node_id] = safe_json_text(extracted_label)
    
    # 엣지 추가 (RDF.type과 RDFS.label이 아닌 모든 관계)
    edges = []
    edge_labels = {}
    for s, p, o in g:
        if p not in [RDF.type, RDFS.label]:
            source = str(s)
            target = str(o)
            relation = str(p).split('#')[-1]
            
            # 노드 중 하나라도 없으면 추가
            if source not in nodes and isinstance(s, URIRef):
                nodes[source] = len(nodes)
                G.add_node(source)
                node_types[source] = "Unknown"
                extracted_label = source.split('#')[-1].split('/')[-1]
                node_labels[source] = safe_json_text(extracted_label)
            
            if target not in nodes and isinstance(o, URIRef):
                nodes[target] = len(nodes)
                G.add_node(target)
                node_types[target] = "Unknown"
                extracted_label = target.split('#')[-1].split('/')[-1]
                node_labels[target] = safe_json_text(extracted_label)
            
            # target이 리터럴이 아닌 경우만 엣지 추가
            if isinstance(o, URIRef) and source in nodes and target in nodes:
                G.add_edge(source, target)
                edge_labels[(source, target)] = safe_json_text(relation)
                edges.append((source, target, relation))
    
    return G, node_types, node_labels, edge_labels

def get_node_color_map() -> Dict[str, str]:
    """
    노드 유형별 색상 매핑 반환 - 실제 온톨로지 엔티티 타입 반영
    
    Returns:
        Dict[str, str]: 노드 유형별 색상 매핑
    """
    return {
        # 제조/품질 관련 핵심 엔티티
        "ForeignMaterial": "red",           # 이물질 - 빨간색 (위험)
        "Defect": "orange",                 # 불량 - 주황색 (경고)
        "FailureMode": "crimson",           # 고장 모드 - 진한 빨간색
        "Equipment": "steelblue",           # 설비 - 강철 파란색
        "Process": "green",                 # 공정 - 초록색
        "Issue": "darkorange",              # 이슈 - 진한 주황색
        "Material": "brown",                # 재료 - 갈색
        "Component": "mediumpurple",        # 부품 - 중간 보라색
        "Parameter": "teal",                # 매개변수 - 청록색
        "Measurement": "navy",              # 측정값 - 진한 파란색
        
        # 조직/인력 관련
        "Organization": "royalblue",        # 조직 - 로열 블루
        "Person": "lightgreen",            # 인력 - 연한 초록색
        "Team": "mediumseagreen",          # 팀 - 중간 바다 초록색
        "Role": "olivedrab",               # 역할 - 올리브 초록색
        
        # 지역/정책 관련
        "Country": "darkred",              # 국가 - 진한 빨간색
        "Region": "indianred",             # 지역 - 인디언 빨간색
        "Policy": "purple",                # 정책 - 보라색
        "Regulation": "darkviolet",        # 규제 - 진한 보라색
        
        # 기술/제품 관련
        "Technology": "blue",              # 기술 - 파란색
        "Product": "gold",                 # 제품 - 금색
        "Innovation": "cyan",              # 혁신 - 청록색
        "Solution": "limegreen",           # 솔루션 - 라임 그린
        
        # 비즈니스/시장 관련
        "Industry": "darkslategray",       # 산업 - 진한 슬레이트 그레이
        "Market": "magenta",               # 시장 - 마젠타
        "Company": "darkblue",             # 회사 - 진한 파란색
        "Competitor": "firebrick",         # 경쟁사 - 벽돌색
        
        # 시간/이벤트 관련
        "Event": "pink",                   # 이벤트 - 핑크
        "Timeline": "lightpink",           # 타임라인 - 연한 핑크
        "Milestone": "hotpink",            # 마일스톤 - 진한 핑크
        
        # 기본/기타
        "Entity": "gray",                  # 일반 엔티티 - 회색
        "Node": "lightgray",               # 일반 노드 - 연한 회색
        "Unknown": "silver",               # 알 수 없음 - 은색
        "Other": "dimgray"                 # 기타 - 진한 회색
    }

def get_relation_color_map() -> Dict[str, str]:
    """
    관계 유형별 색상 매핑 반환 - 실제 온톨로지 관계 타입 반영
    
    Returns:
        Dict[str, str]: 관계 유형별 색상 매핑
    """
    return {
        # 제조/품질 관련 핵심 관계 - 투명도를 1.0으로 높임
        "caused_by": "rgba(220, 20, 60, 1.0)",     # 원인 관계 - 크림슨 레드 (중요)
        "resulted_in": "rgba(255, 140, 0, 1.0)",   # 결과 관계 - 다크 오렌지
        "leads_to": "rgba(255, 165, 0, 1.0)",      # 이어지는 관계 - 오렌지
        "triggers": "rgba(255, 69, 0, 1.0)",       # 트리거 관계 - 레드 오렌지
        "prevents": "rgba(0, 128, 0, 1.0)",        # 방지 관계 - 그린
        "resolves": "rgba(34, 139, 34, 1.0)",      # 해결 관계 - 포레스트 그린
        
        # 포함/구성 관계
        "includes": "rgba(30, 144, 255, 1.0)",     # 포함 관계 - 다지 블루
        "contains": "rgba(70, 130, 180, 1.0)",     # 내포 관계 - 스틸 블루
        "consists_of": "rgba(100, 149, 237, 1.0)", # 구성 관계 - 콘플라워 블루
        "part_of": "rgba(123, 104, 238, 1.0)",     # 부분 관계 - 미디엄 슬레이트 블루
        "belongs_to": "rgba(72, 61, 139, 1.0)",    # 소속 관계 - 다크 슬레이트 블루
        
        # 제조/생산 관계
        "manufactured_by": "rgba(139, 69, 19, 1.0)",   # 제조 관계 - 새들 브라운
        "produced_by": "rgba(160, 82, 45, 1.0)",       # 생산 관계 - 새들 브라운
        "processed_by": "rgba(210, 180, 140, 1.0)",    # 가공 관계 - 탄
        "assembled_by": "rgba(222, 184, 135, 1.0)",    # 조립 관계 - 버를리우드
        "tested_by": "rgba(184, 134, 11, 1.0)",        # 테스트 관계 - 다크 골든로드
        "inspected_by": "rgba(218, 165, 32, 1.0)",     # 검사 관리 - 골든로드
        
        # 사용/적용 관계
        "used_in": "rgba(128, 0, 128, 1.0)",       # 사용 관계 - 퍼플
        "applied_to": "rgba(147, 112, 219, 1.0)",  # 적용 관계 - 미디엄 퍼플
        "installed_in": "rgba(138, 43, 226, 1.0)", # 설치 관계 - 블루 바이올렛
        "operates_on": "rgba(153, 50, 204, 1.0)",  # 동작 관계 - 다크 오키드
        
        # 공급/제공 관계
        "supplies": "rgba(0, 64, 64, 1.0)",        # 공급 관계 - 다크 틸
        "provides": "rgba(32, 178, 170, 1.0)",     # 제공 관계 - 라이트 시 그린
        "delivers": "rgba(95, 158, 160, 1.0)",     # 전달 관계 - 카뎃 블루
        "receives": "rgba(175, 238, 238, 1.0)",    # 수신 관계 - 페일 터콰이즈
        
        # 영향/상호작용 관계
        "affects": "rgba(255, 20, 147, 1.0)",      # 영향 관계 - 딥 핑크
        "influences": "rgba(199, 21, 133, 1.0)",   # 영향력 관계 - 미디엄 바이올렛 레드
        "interacts_with": "rgba(219, 112, 147, 1.0)", # 상호작용 - 페일 바이올렛 레드
        "depends_on": "rgba(240, 128, 128, 1.0)",  # 의존 관계 - 라이트 코랄
        
        # 비교/경쟁 관계
        "competes_with": "rgba(25, 25, 112, 1.0)", # 경쟁 관계 - 미드나이트 블루
        "replaces": "rgba(65, 105, 225, 1.0)",     # 대체 관계 - 로열 블루
        "similar_to": "rgba(106, 90, 205, 1.0)",   # 유사 관계 - 슬레이트 블루
        "different_from": "rgba(72, 209, 204, 1.0)", # 차이 관계 - 미디엄 터콰이즈
        
        # 규제/관리 관계
        "regulated_by": "rgba(128, 0, 0, 1.0)",    # 규제 관계 - 마룬
        "controlled_by": "rgba(139, 0, 0, 1.0)",   # 통제 관계 - 다크 레드
        "managed_by": "rgba(165, 42, 42, 1.0)",    # 관리 관계 - 브라운
        "supervised_by": "rgba(178, 34, 34, 1.0)", # 감독 관계 - 파이어브릭
        
        # 기본/일반 관계 - 가시성을 위해 투명도 증가
        "related_to": "rgba(70, 70, 70, 0.95)",     # 관련 관계 - 진한 회색
        "associated_with": "rgba(105, 105, 105, 0.95)", # 연관 관계 - 딤 그레이
        "connected_to": "rgba(128, 128, 128, 0.95)", # 연결 관계 - 그레이
        "linked_to": "rgba(169, 169, 169, 0.95)",   # 링크 관계 - 다크 그레이
        "refers_to": "rgba(192, 192, 192, 0.95)",   # 참조 관계 - 실버
        
        # 기타/알 수 없음 - 최소 투명도 보장
        "unknown": "rgba(211, 211, 211, 0.8)",     # 알 수 없는 관계 - 라이트 그레이
        "other": "rgba(169, 169, 169, 0.8)"        # 기타 관계 - 다크 그레이
    }

def create_3d_ontology_plot(G: nx.Graph, node_types: Dict[str, str], 
                          node_labels: Dict[str, str], edge_labels: Dict[Tuple[str, str], str]) -> go.Figure:
    """
    NetworkX 그래프를 3D Plotly 그래프로 변환
    
    Args:
        G (nx.Graph): NetworkX 그래프
        node_types (Dict[str, str]): 노드 유형 매핑
        node_labels (Dict[str, str]): 노드 레이블 매핑
        edge_labels (Dict[Tuple[str, str], str]): 엣지 레이블 매핑
        
    Returns:
        go.Figure: Plotly 3D 그래프
    """
    # 색상 매핑 
    node_color_map = get_node_color_map()
    relation_color_map = get_relation_color_map()
    
    # 3D 좌표 계산
    pos = nx.spring_layout(G, dim=3, seed=42)
    
    # 데이터 목록 초기화 (모든 trace를 여기에 추가)
    data = []
    
    # 노드 중심성 계산
    degree_centrality = nx.degree_centrality(G)
    betweenness_centrality = nx.betweenness_centrality(G)
    closeness_centrality = nx.closeness_centrality(G)
    
    # 각 노드의 연결 정보 미리 계산
    node_connections = {}
    node_relations = {}
    
    for node in G.nodes():
        # 이 노드와 연결된 이웃 노드들
        neighbors = list(G.neighbors(node))
        node_connections[node] = neighbors
        
        # 이 노드가 가진 관계 유형들
        relations = {}
        for neighbor in neighbors:
            if (node, neighbor) in edge_labels:
                relation = edge_labels[(node, neighbor)]
            elif (neighbor, node) in edge_labels:
                relation = edge_labels[(neighbor, node)]
            else:
                relation = "관계없음"
                
            # 관계 방향 기록
            direction = "나가는" if (node, neighbor) in edge_labels else "들어오는"
            
            if relation not in relations:
                relations[relation] = []
            relations[relation].append((neighbor, direction))
        
        node_relations[node] = relations
    
    # 노드 유형별로 그룹화
    nodes_by_type = {}
    for node in G.nodes():
        node_type = node_types.get(node, "Unknown")
        if node_type not in nodes_by_type:
            nodes_by_type[node_type] = []
        nodes_by_type[node_type].append(node)
    
    # 관계 유형별로 그룹화
    edges_by_relation = {}
    for source, target in G.edges():
        relation = edge_labels.get((source, target), "관계없음")
        if relation not in edges_by_relation:
            edges_by_relation[relation] = []
        edges_by_relation[relation].append((source, target))
    
    # === 1. 엣지 그리기 (관계 유형별로) ===
    for relation, edges in edges_by_relation.items():
        edge_x = []
        edge_y = []
        edge_z = []
        edge_text = []
        
        for source, target in edges:
            x0, y0, z0 = pos[source]
            x1, y1, z1 = pos[target]
            
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
            edge_z.extend([z0, z1, None])
            
            # 엣지 호버 텍스트 추가 - 더 상세한 정보 포함 (안전한 텍스트 처리 적용)
            source_label = safe_json_text(node_labels.get(source, source))
            target_label = safe_json_text(node_labels.get(target, target))
            source_type = safe_json_text(node_types.get(source, "Unknown"))
            target_type = safe_json_text(node_types.get(target, "Unknown"))
            safe_relation = safe_json_text(relation)
            
            # 관계 방향성 정보
            direction_info = "단방향" if relation != "related_to" else "양방향"
            
            # 관계 중요도 계산 (제조/품질 관련 관계는 높은 중요도)
            critical_relations = ["caused_by", "resulted_in", "leads_to", "triggers", "prevents", "resolves"]
            importance = "RED 매우 중요" if relation in critical_relations else "YELLOW 중요" if relation in ["used_in", "manufactured_by", "tested_by"] else "GREEN 일반"
            
            # 풍부한 툴팁 생성 (안전한 텍스트 처리 적용)
            detailed_hover = (
                f"<b>LINK 관계 정보</b><br>"
                f"관계 유형: <b>{safe_relation}</b><br>"
                f"중요도: {importance}<br>"
                f"방향성: {direction_info}<br>"
                f"<br><b>PIN 출발점</b><br>"
                f"엔티티: <b>{source_label}</b><br>"
                f"유형: {source_type}<br>"
                f"<br><b>PIN 도착점</b><br>"
                f"엔티티: <b>{target_label}</b><br>"
                f"유형: {target_type}<br>"
                f"<br><b>BULB 관계 설명</b><br>"
                f"'{source_label}' {safe_relation} '{target_label}'"
            )
            
            edge_text.append(detailed_hover)
        
        # 관계 유형별 색상 설정
        relation_color = relation_color_map.get(relation, "rgba(150, 150, 150, 0.8)")
        
        # 관계 중요도에 따른 라인 두께 설정
        critical_relations = ["caused_by", "resulted_in", "leads_to", "triggers", "prevents", "resolves"]
        important_relations = ["used_in", "manufactured_by", "tested_by", "processed_by", "inspected_by"]
        
        if relation in critical_relations:
            line_width = 4  # 매우 중요한 관계는 굵게
        elif relation in important_relations:
            line_width = 3  # 중요한 관계는 중간 굵기
        else:
            line_width = 2  # 일반 관계는 기본 굵기
        
        # 이 관계 유형에 대한 trace 생성
        edge_trace = go.Scatter3d(
            x=edge_x, y=edge_y, z=edge_z,
            mode='lines',
            line=dict(
                width=line_width, 
                color=relation_color
            ),
            text=edge_text,
            hoverinfo='text',
            name=safe_json_text(f"관계: {relation} ({len(edges)}개)"),
            showlegend=True,
            legendgroup="relationships"
        )
        
        data.append(edge_trace)
    
    # === 2. 노드 그리기 (노드 유형별로) ===
    for node_type, nodes in nodes_by_type.items():
        node_x = []
        node_y = []
        node_z = []
        node_text = []
        node_size = []
        
        for node in nodes:
            x, y, z = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_z.append(z)
            
            # 노드 정보 수집 (안전한 텍스트 처리 적용)
            label = safe_json_text(node_labels.get(node, node))
            
            # 연결 정보
            neighbors = node_connections[node]
            connections_count = len(neighbors)
            
            # 관계 정보
            relations = node_relations[node]
            relation_info = ""
            
            # 최대 5개의 주요 관계만 표시
            for i, (relation, related_nodes) in enumerate(relations.items()):
                if i >= 5:
                    relation_info += f"<br>그 외 {len(relations) - 5}개 관계..."
                    break
                
                # 관계 당 최대 3개 노드만 표시
                related_node_labels = []
                for rel_node, direction in related_nodes[:3]:
                    rel_label = safe_json_text(node_labels.get(rel_node, rel_node))
                    # 레이블이 너무 길면 잘라냄
                    if len(rel_label) > 15:
                        rel_label = rel_label[:12] + "..."
                    related_node_labels.append(f"{rel_label} ({direction})")
                
                if len(related_nodes) > 3:
                    related_node_labels.append(f"외 {len(related_nodes) - 3}개...")
                
                safe_relation = safe_json_text(relation)
                relation_info += f"<br>- {safe_relation}: {', '.join(related_node_labels)}"
            
            # 중심성 정보
            degree = degree_centrality.get(node, 0)
            betweenness = betweenness_centrality.get(node, 0)
            closeness = closeness_centrality.get(node, 0)
            
            # 엔티티 중요도 계산
            critical_entities = ["ForeignMaterial", "Defect", "FailureMode", "Equipment"]
            important_entities = ["Process", "Issue", "Material", "Component"]
            
            if node_type in critical_entities:
                priority = "RED 핵심"
            elif node_type in important_entities:
                priority = "YELLOW 중요"
            else:
                priority = "GREEN 일반"
            
            # 네트워크 영향력 평가
            if betweenness > 0.1:
                influence = "STAR 매우 높음"
            elif betweenness > 0.05:
                influence = "STAR 높음"
            elif betweenness > 0.01:
                influence = "STAR 중간"
            else:
                influence = "DIAMOND 낮음"
            
            # 노드 ID 정보 (안전한 텍스트 처리 적용)
            node_id = safe_json_text(node.split('#')[-1].split('/')[-1] if '#' in node or '/' in node else node)
            safe_node_type = safe_json_text(node_type)
            
            # 풍부한 툴팁 생성 (안전한 텍스트 처리 적용)
            hover_text = (
                f"<b>TAG {label}</b><br>"
                f"ID: <code>{node_id}</code><br>"
                f"유형: <b>{safe_node_type}</b><br>"
                f"우선순위: {priority}<br>"
                f"네트워크 영향력: {influence}<br>"
                f"<br><b>CHART 연결 통계</b><br>"
                f"직접 연결: {connections_count}개<br>"
                f"연결 중심성: {degree:.3f}<br>"
                f"매개 중심성: {betweenness:.3f}<br>"
                f"근접 중심성: {closeness:.3f}<br>"
                f"<br><b>LINK 관계 상세</b>{relation_info}<br>"
                f"<br><b>BULB 분석 힌트</b><br>"
                f"이 노드는 {'핵심적인' if node_type in critical_entities else '중요한' if node_type in important_entities else '보조적인'} "
                f"역할을 하며, {influence.split(' ')[1]} 네트워크 영향력을 가집니다."
            )
            
            node_text.append(hover_text)
            
            # 유형 및 중심성에 따라 노드 크기 조정 - 제조/품질 중심 분류
            base_size = 15
            
            # 제조/품질 핵심 엔티티 (가장 큰 크기)
            if node_type in ["ForeignMaterial", "Defect", "FailureMode", "Equipment"]:
                base_size = 20
            # 중요 제조 관련 엔티티
            elif node_type in ["Process", "Issue", "Material", "Component"]:
                base_size = 18
            # 측정/매개변수 관련
            elif node_type in ["Parameter", "Measurement"]:
                base_size = 17
            # 조직/인력 관련
            elif node_type in ["Organization", "Person", "Team"]:
                base_size = 16
            # 기술/제품 관련
            elif node_type in ["Technology", "Product", "Innovation", "Solution"]:
                base_size = 16
            # 정책/규제 관련
            elif node_type in ["Policy", "Regulation", "Country"]:
                base_size = 15
            # 기본 크기
            else:
                base_size = 14
            
            # 노드 크기에 중심성 반영 (매개 중심성이 높을수록 더 크게)
            # 제조/품질 관련 엔티티는 중심성 가중치를 더 크게 적용
            centrality_weight = 40 if node_type in ["ForeignMaterial", "Defect", "FailureMode", "Equipment", "Process", "Issue"] else 30
            size = base_size + betweenness * centrality_weight
            node_size.append(size)
        
        # 이 유형의 노드에 대한 trace 생성
        node_trace = go.Scatter3d(
            x=node_x, y=node_y, z=node_z,
            mode='markers',
            marker=dict(
                size=node_size,
                color=node_color_map.get(node_type, "gray"),
                line=dict(width=0.5, color='white'),
                opacity=0.8  # 노드 투명도 약간 조정
            ),
            text=node_text,
            hoverinfo='text',
            name=safe_json_text(f"노드: {node_type} ({len(nodes)}개)"),
            showlegend=True,
            legendgroup="nodes"
        )
        
        data.append(node_trace)
    
    # 그래프 레이아웃 설정
    layout = go.Layout(
        title={
            'text': safe_json_text('온톨로지 3D 시각화'),
            'font': {'size': 16}
        },
        showlegend=True,
        legend=dict(
            title=safe_json_text("온톨로지 요소"),
            itemsizing="constant",
            bgcolor="rgba(255, 255, 255, 0.7)",
            bordercolor="gray",
            borderwidth=1,
            # 범례 그룹화 설정
            groupclick="toggleitem"
        ),
        scene=dict(
            xaxis=dict(showticklabels=False, title=''),
            yaxis=dict(showticklabels=False, title=''),
            zaxis=dict(showticklabels=False, title='')
        ),
        margin=dict(l=0, r=0, b=0, t=40),
        hovermode='closest'
    )
    
    # 그래프 생성 및 반환
    fig = go.Figure(data=data, layout=layout)
    
    # 범례를 노드 그룹과 관계 그룹으로 나누기 위한 버튼 추가 - 제조/품질 중심 필터링
    fig.update_layout(
        updatemenus=[{
            'buttons': [
                {
                    'method': 'update',
                    'label': '모두 표시',
                    'args': [{'visible': [True] * len(data)}]
                },
                {
                    'method': 'update',
                    'label': '제조/품질 핵심',
                    'args': [{'visible': [
                        (trace.legendgroup == "nodes" and 
                         any(key_type in trace.name for key_type in ["ForeignMaterial", "Defect", "FailureMode", "Equipment", "Process", "Issue"])) or
                        (trace.legendgroup == "relationships" and 
                         any(key_rel in trace.name for key_rel in ["caused_by", "resulted_in", "leads_to", "prevents", "resolves"]))
                        for trace in data
                    ]}]
                },
                {
                    'method': 'update',
                    'label': '노드만 표시',
                    'args': [{'visible': [True if trace.legendgroup == "nodes" else False for trace in data]}]
                },
                {
                    'method': 'update',
                    'label': '관계만 표시',
                    'args': [{'visible': [True if trace.legendgroup == "relationships" else False for trace in data]}]
                },
                {
                    'method': 'update',
                    'label': '원인-결과 관계',
                    'args': [{'visible': [
                        trace.legendgroup == "nodes" or
                        (trace.legendgroup == "relationships" and 
                         any(causal_rel in trace.name for causal_rel in ["caused_by", "resulted_in", "leads_to", "triggers"]))
                        for trace in data
                    ]}]
                }
            ],
            'direction': 'down',
            'showactive': True,
            'x': 0.02,
            'y': 1.15,
            'xanchor': 'left',
            'yanchor': 'top'
        }]
    )
    
    return fig

def get_node_type_statistics(node_types: Dict[str, str]) -> Dict[str, int]:
    """
    노드 유형별 통계 계산
    
    Args:
        node_types (Dict[str, str]): 노드 유형 매핑
        
    Returns:
        Dict[str, int]: 노드 유형별 개수
    """
    type_counts = {}
    for node, node_type in node_types.items():
        type_counts[node_type] = type_counts.get(node_type, 0) + 1
    
    return type_counts

def visualize_ontology_3d(ttl_file_path: str) -> Tuple[go.Figure, Dict[str, Any]]:
    """
    TTL 파일에서 온톨로지를 로드하고 3D 시각화 생성
    
    Args:
        ttl_file_path (str): TTL 파일 경로
        
    Returns:
        Tuple[go.Figure, Dict[str, Any]]: Plotly 그래프와 통계 정보
    """
    # TTL 파일에서 그래프 로드
    g = load_ontology_graph(ttl_file_path)
    
    # NetworkX 그래프 변환
    G, node_types, node_labels, edge_labels = create_networkx_graph(g)
    
    # 3D 그래프 생성
    fig = create_3d_ontology_plot(G, node_types, node_labels, edge_labels)
    
    # 통계 정보 생성
    stats = {
        "node_count": len(G.nodes()),
        "edge_count": len(G.edges()),
        "node_types": get_node_type_statistics(node_types)
    }
    
    return fig, stats 