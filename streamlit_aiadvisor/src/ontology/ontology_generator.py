"""
추출된 정보로부터 온톨로지(TTL) 파일을 생성하는 모듈
"""
import os
import json
from typing import List, Dict, Any, Optional, Set, Tuple
from collections import defaultdict

import rdflib
from rdflib import Graph, Literal, BNode, Namespace, URIRef
from rdflib.namespace import RDF, RDFS, XSD

from src.utils.config import TTL_DIR, RELATIONSHIPS

class OntologyGenerator:
    """온톨로지 생성 및 관리 클래스"""
    
    def __init__(self, output_dir: str = TTL_DIR):
        """
        온톨로지 생성기 초기화
        
        Args:
            output_dir (str): TTL 파일 저장 경로
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # 네임스페이스 정의
        self.NS = Namespace("http://dxai.advisor/ontology#")
        
        # 관계 정의 - 특수 문자가 있을 수 있는 관계명 처리
        self.RELATIONS = {}
        for rel in RELATIONSHIPS:
            try:
                # 관계명 정리 - 영문자, 숫자, 언더스코어만 허용
                import re
                clean_rel = re.sub(r'[^a-z0-9_]', '_', rel.lower())
                clean_rel = re.sub(r'_+', '_', clean_rel).strip('_')
                if not clean_rel:
                    clean_rel = f"relation_{hash(rel) % 10000:04d}"
                
                self.RELATIONS[rel] = self.NS[clean_rel]
                # 테스트를 위해 URI 문자열로 변환 시도
                str(self.RELATIONS[rel])
            except Exception as e:
                # 오류 발생 시 대체 이름 사용
                fallback_name = f"relation_{hash(rel) % 10000:04d}"
                self.RELATIONS[rel] = self.NS[fallback_name]
        
        # 엔티티 타입 정의
        self.ENTITY_TYPES = {
            # 일반 엔티티 타입
            "Organization": self.NS["Organization"],
            "Person": self.NS["Person"],
            "Country": self.NS["Country"],
            "Location": self.NS["Location"],           # 추가: 위치 정보

            # 제품 및 자재
            "Product": self.NS["Product"],             # 완제품
            "Material": self.NS["Material"],           # 원자재, 소재
            "Component": self.NS["Component"],         # 부품, 컴포넌트
            "Chemical": self.NS["Chemical"],           # 화학물질
            "Precursor": self.NS["Precursor"],         # 추가: 전구체
            "Dopant": self.NS["Dopant"],               # 추가: 도펀트
            "Batch": self.NS["Batch"],                 # 추가: 배치
            "Lot": self.NS["Lot"],                     # 추가: Lot
            
            # 공정 및 설비
            "Equipment": self.NS["Equipment"],         # 설비, 장비
            "Process": self.NS["Process"],             # 공정, 프로세스
            "ProcessLine": self.NS["ProcessLine"],     # 추가: 프로세스 라인
            "Instrument": self.NS["Instrument"],       # 계측기, 측정장비
            "Tool": self.NS["Tool"],                   # 도구, 작업도구
            "Sensor": self.NS["Sensor"],               # 추가: 센서
            "Filter": self.NS["Filter"],               # 추가: 필터
            "Valve": self.NS["Valve"],                 # 추가: 밸브
            "Mesh": self.NS["Mesh"],                   # 추가: 메쉬
            "Tank": self.NS["Tank"],                   # 추가: 탱크
            "Feeder": self.NS["Feeder"],               # 추가: 피더
            "Mixer": self.NS["Mixer"],                 # 추가: 믹서
            
            # 문제 및 품질
            "Defect": self.NS["Defect"],               # 결함, 불량
            "FailureMode": self.NS["FailureMode"],     # 고장 모드
            "RootCause": self.NS["RootCause"],         # 근본 원인
            "Parameter": self.NS["Parameter"],         # 파라미터, 측정값
            "Specification": self.NS["Specification"], # 추가: 스펙, 규격
            "Quality": self.NS["Quality"],             # 추가: 품질
            "Contaminant": self.NS["Contaminant"],     # 추가: 오염물질
            "ForeignMaterial": self.NS["ForeignMaterial"], # 추가: 이물질
            
            # 측정 및 분석
            "TestMethod": self.NS["TestMethod"],       # 추가: 테스트 방법
            "AnalysisResult": self.NS["AnalysisResult"], # 추가: 분석 결과
            "Measurement": self.NS["Measurement"],     # 추가: 측정
            "SamplePoint": self.NS["SamplePoint"],     # 추가: 샘플링 포인트
            
            # 기타
            "Technology": self.NS["Technology"],       # 기술
            "Policy": self.NS["Policy"],               # 정책, 규정
            "Event": self.NS["Event"],                 # 이벤트, 사건
            "Industry": self.NS["Industry"],           # 산업
            "Market": self.NS["Market"],               # 시장
            "Maintenance": self.NS["Maintenance"],     # 추가: 유지보수
            "Issue": self.NS["Issue"],                 # 추가: 이슈
            "Solution": self.NS["Solution"],           # 추가: 솔루션
            "Timeline": self.NS["Timeline"]            # 추가: 타임라인
        }
        
        # 그래프 초기화
        self.graph = Graph()
        self.graph.bind("dxai", self.NS)
    
    def _clean_entity_name(self, entity: str) -> str:
        """
        엔티티 이름 정리
        
        Args:
            entity (str): 원본 엔티티 이름
            
        Returns:
            str: 정리된 엔티티 이름
        """
        import re
        
        if not entity:
            return "unnamed_entity"
        
        # 소문자로 변환
        entity = entity.lower()
        
        # URI에 사용할 수 없는 특수 문자를 언더스코어로 변환
        # 영문자, 숫자, 언더스코어를 제외한 모든 문자를 언더스코어로 변환
        entity = re.sub(r'[^a-z0-9_]', '_', entity)
        
        # 다중 언더스코어를 단일 언더스코어로 변환
        entity = re.sub(r'_+', '_', entity)
        
        # 시작과 끝의 언더스코어 제거
        entity = entity.strip('_')
        
        # 빈 문자열이 되었다면 기본값 제공
        if not entity:
            entity = "unnamed_entity"
        
        return entity
    
    def _create_uri(self, entity: str) -> URIRef:
        """
        엔티티의 URI 생성
        
        Args:
            entity (str): 엔티티 이름
            
        Returns:
            URIRef: 엔티티 URI
        """
        clean_name = self._clean_entity_name(entity)
        
        # 한국어 문자가 포함된 경우를 위해 추가 처리
        # rdflib에서는 한글이 포함된 URI를 제대로 처리하지 못할 수 있음
        try:
            # 안전하게 URI 생성
            uri = self.NS[clean_name]
            # 테스트를 위해 URI 문자열로 변환 시도
            str(uri)
            return uri
        except Exception as e:
            # 오류 발생 시 영문자와 숫자만 남기고 모두 제거
            import re
            fallback_name = re.sub(r'[^a-z0-9]', '', clean_name)
            if not fallback_name:
                fallback_name = f"entity_{hash(entity) % 10000:04d}"
            return self.NS[fallback_name]
    
    def _get_entity_type(self, entity: str) -> URIRef:
        """
        엔티티의 유형을 추론
        
        Args:
            entity (str): 엔티티 이름
            
        Returns:
            URIRef: 엔티티 유형 URI
        """
        # 간단한 규칙 기반 추론 (향후 LLM 기반으로 확장 가능)
        entity_lower = entity.lower()
        
        # 국가/지역 추론
        countries = ["미국", "중국", "한국", "일본", "유럽", "영국", "독일", "프랑스", "인도"]
        if any(country in entity for country in countries):
            return self.ENTITY_TYPES["Country"]
        
        # 조직/기업 추론
        org_suffixes = ["주식회사", "inc", "corp", "corporation", "company", "co.,", "co", "ltd", "그룹"]
        if any(suffix in entity_lower for suffix in org_suffixes) or "테슬라" in entity_lower or "삼성" in entity_lower or "lg" in entity_lower:
            return self.ENTITY_TYPES["Organization"]
        
        # Lot 추론
        lot_keywords = ["lot", "로트", "p5", "batch", "배치"]
        if any(keyword in entity_lower for keyword in lot_keywords) and any(c.isdigit() for c in entity_lower):
            return self.ENTITY_TYPES["Lot"]
            
        # 공정라인 추론
        line_keywords = ["1line", "2line", "3line", "1l", "2l", "3l", "line", "라인", "cam5", "cam3", "cam4"]
        if any(keyword in entity_lower.replace(" ", "") for keyword in line_keywords):
            return self.ENTITY_TYPES["ProcessLine"]
            
        # 제품 모델명 추론 (특정 패턴 찾기)
        product_patterns = ["nca", "cds", "csg", "cam"]
        digit_pattern = any(c.isdigit() for c in entity)
        if any(pattern in entity_lower for pattern in product_patterns) and digit_pattern:
            return self.ENTITY_TYPES["Product"]
        
        # 설비/장비 추론
        equipment_keywords = ["라인", "line", "설비", "호퍼", "hopper", "mixer", "믹서", "feeder", "피더", "press", "탈철기", "분급기", "건조기", 
                            "filter", "필터", "valve", "밸브", "chamber", "챔버", "탱크", "tank", "오븐", "로", "furnace", "시스템", "system",
                            "colloid mill", "콜로이드 밀", "blender", "블렌더", "crusher", "크러셔", "reactor", "반응기", "cooler", "쿨링", "cooling",
                            "conveyor", "컨베이어", "cyclone", "싸이클론", "air knocker", "에어 노커", "packer", "포장기", "roc"]
        if any(keyword in entity_lower for keyword in equipment_keywords):
            # 특정 장비 서브타입 추론
            if any(kw in entity_lower for kw in ["feeder", "피더"]):
                return self.ENTITY_TYPES["Feeder"]
            elif any(kw in entity_lower for kw in ["mixer", "믹서", "blender", "블렌더"]):
                return self.ENTITY_TYPES["Mixer"]
            elif any(kw in entity_lower for kw in ["filter", "필터"]):
                return self.ENTITY_TYPES["Filter"]
            elif any(kw in entity_lower for kw in ["valve", "밸브"]):
                return self.ENTITY_TYPES["Valve"]
            elif any(kw in entity_lower for kw in ["tank", "탱크", "호퍼", "hopper"]):
                return self.ENTITY_TYPES["Tank"]
            else:
                return self.ENTITY_TYPES["Equipment"]
        
        # 공정 추론
        process_keywords = ["공정", "프로세스", "process", "mixing", "믹싱", "포장", "이송", "배출", "분급", "소성", "수세", "투입", "cleaning", "청소", "검사",
                           "분쇄", "건조", "소성", "포장", "계량", "검사", "분석", "측정", "sampling", "샘플링", "pressing", "프레싱", "cooling", "냉각"]
        if any(keyword in entity_lower for keyword in process_keywords):
            return self.ENTITY_TYPES["Process"]
        
        # 부품/컴포넌트 추론
        component_keywords = ["배관", "부품", "컴포넌트", "component", "파트", "part", "모터", "motor", "스크류", "screw", "로드셀", "로드쎌", "loadcell", 
                             "베어링", "bearing", "센서", "sensor", "매쉬", "mesh", "너트", "nut", "볼트", "bolt", "케이블", "cable", "스위치", "switch", 
                             "샘플러", "sampler", "실린더", "cylinder", "패킹", "packing", "가스켓", "gasket", "오링", "o-ring", "진동자", "vibrator", 
                             "체크호퍼", "check hopper", "matrix", "매트릭스", "영구자석", "자석", "magnet", "트라우프", "trough", "디버터", "diverter"]
        if any(keyword in entity_lower for keyword in component_keywords):
            if "sensor" in entity_lower or "센서" in entity_lower:
                return self.ENTITY_TYPES["Sensor"]
            elif "mesh" in entity_lower or "매쉬" in entity_lower:
                return self.ENTITY_TYPES["Mesh"]
            else:
                return self.ENTITY_TYPES["Component"]
        
        # 자재/소재 추론
        material_keywords = ["원료", "소재", "material", "powder", "분말", "입자", "particle", "전구체", "precursor", "화학", "chemical", "입도", "density", 
                            "밀도", "양극재", "양극", "cathode", "재공", "수세품", "소성품", "포장품", "1차소성", "2차소성", "최종품", "이송품", "도펀트", "dopant"]
        if any(keyword in entity_lower for keyword in material_keywords):
            if "전구체" in entity_lower or "precursor" in entity_lower:
                return self.ENTITY_TYPES["Precursor"]
            elif "도펀트" in entity_lower or "dopant" in entity_lower:
                return self.ENTITY_TYPES["Dopant"]
            else:
                return self.ENTITY_TYPES["Material"]
        
        # 화학물질 추론
        chemical_keywords = ["li", "al", "zr", "ti", "mn", "co", "ni", "na", "fe", "cr", "zn", "리튬", "알루미늄", "지르코늄", "티타늄", "망간", "코발트", 
                            "니켈", "철", "산화알루미늄", "lioh", "li2co3", "zro2", "tio2", "알루미나", "자성이물", "금속이물"]
        if any(keyword in entity_lower for keyword in chemical_keywords):
            if "이물" in entity_lower:
                return self.ENTITY_TYPES["ForeignMaterial"]
            else:
                return self.ENTITY_TYPES["Chemical"]
        
        # 결함/불량 추론
        defect_keywords = ["불량", "ng", "defect", "fault", "error", "이물", "crack", "크랙", "고착", "체류", "막힘", "누출", "leakage", "노이즈", 
                          "이탈", "부적합", "편차", "미흡", "소음", "파손", "오차", "불균일", "오염", "spec out", "스펙아웃", "상한", "하한", "품질사고", 
                          "이슈", "issue", "문제", "불량", "미투입"]
        if any(keyword in entity_lower for keyword in defect_keywords):
            if "이물" in entity_lower:
                return self.ENTITY_TYPES["ForeignMaterial"]
            elif "이슈" in entity_lower or "issue" in entity_lower:
                return self.ENTITY_TYPES["Issue"]
            else:
                return self.ENTITY_TYPES["Defect"]
        
        # 고장 모드 추론
        failure_keywords = ["고장", "failure", "파손", "손상", "마모", "wear", "변형", "deformation", "단선", "단락", "short", "오작동", "malfunction", 
                           "과열", "overheat", "탈조", "진동", "vibration", "부식", "corrosion", "미가동", "shutdown", "정지", "stop"]
        if any(keyword in entity_lower for keyword in failure_keywords):
            return self.ENTITY_TYPES["FailureMode"]
        
        # 파라미터/측정값 추론
        parameter_keywords = ["압력", "pressure", "온도", "temperature", "속도", "speed", "무게", "weight", "농도", "concentration", "전류", "current", 
                             "전압", "voltage", "용량", "capacity", "습도", "humidity", "값", "value", "레벨", "level", "경화도", "밀도", "density", 
                             "bet", "icp", "xrf", "함량", "함유량", "조성", "composition", "입도", "particle size", "d10", "d50", "d90", "dmax", 
                             "tension", "진폭", "amplitude", "hz", "주파수", "frequency"]
        if any(keyword in entity_lower for keyword in parameter_keywords):
            # 특정 분석/테스트 방법 추론
            if any(kw in entity_lower for kw in ["icp", "xrf", "bet"]):
                return self.ENTITY_TYPES["TestMethod"]
            else:
                return self.ENTITY_TYPES["Parameter"]
        
        # 샘플링 추론
        sample_keywords = ["sample", "샘플", "spl", "시료", "specimen", "샘플링", "sampling", "test", "테스트"]
        if any(keyword in entity_lower for keyword in sample_keywords):
            if "point" in entity_lower or "포인트" in entity_lower:
                return self.ENTITY_TYPES["SamplePoint"]
            else:
                return self.ENTITY_TYPES["TestMethod"]
        
        # 제품 추론 (가장 마지막에 체크)
        product_keywords = ["제품", "product", "최종품", "완제품", "양극재", "배터리", "battery", "전지", "cell"]
        if any(keyword in entity_lower for keyword in product_keywords):
            return self.ENTITY_TYPES["Product"]
        
        # 기술 추론
        tech_keywords = ["기술", "tech", "방식", "알고리즘", "방법", "process", "솔루션", "solution"]
        if any(keyword in entity_lower for keyword in tech_keywords):
            return self.ENTITY_TYPES["Technology"]
        
        # 정책 추론
        policy_keywords = ["정책", "규제", "관세", "법률", "제도", "규정", "세금", "지원금", "guideline", "가이드라인", "매뉴얼", "manual", "spec", "규격", "사양"]
        if any(keyword in entity_lower for keyword in policy_keywords):
            if "spec" in entity_lower or "규격" in entity_lower or "사양" in entity_lower:
                return self.ENTITY_TYPES["Specification"]
            else:
                return self.ENTITY_TYPES["Policy"]
        
        # 기본값 (분류 불가능)
        return self.NS["Entity"]
    
    def add_entity(self, entity: str, entity_type: Optional[str] = None) -> URIRef:
        """
        엔티티를 그래프에 추가
        
        Args:
            entity (str): 엔티티 이름
            entity_type (Optional[str]): 엔티티 유형 (없으면 자동 추론)
            
        Returns:
            URIRef: 생성된 엔티티 URI
        """
        if not entity or not isinstance(entity, str):
            return None
            
        uri = self._create_uri(entity)
        
        # 엔티티 유형 결정
        if entity_type and entity_type in self.ENTITY_TYPES:
            type_uri = self.ENTITY_TYPES[entity_type]
        else:
            type_uri = self._get_entity_type(entity)
        
        # 그래프에 추가
        self.graph.add((uri, RDF.type, type_uri))
        self.graph.add((uri, RDFS.label, Literal(entity, lang="ko")))
        
        return uri
    
    def add_relation(self, source: str, relation: str, target: str) -> bool:
        """
        관계를 그래프에 추가
        
        Args:
            source (str): 소스 엔티티
            relation (str): 관계 유형
            target (str): 타겟 엔티티
            
        Returns:
            bool: 성공 여부
        """
        if not source or not relation or not target:
            return False
            
        # 관계 유효성 확인
        if relation not in self.RELATIONS:
            return False
            
        # 엔티티 추가
        source_uri = self.add_entity(source)
        target_uri = self.add_entity(target)
        
        if not source_uri or not target_uri:
            return False
        
        # 관계 추가
        self.graph.add((source_uri, self.RELATIONS[relation], target_uri))
        
        return True
    
    def process_relations(self, relations_data: Dict[str, Any]) -> None:
        """
        추출된 관계 데이터를 처리하여 온톨로지에 추가
        
        Args:
            relations_data (Dict[str, Any]): 추출된 관계 데이터
        """
        if not relations_data:
            return
            
        # 엔티티 추가
        for entity in relations_data.get("entities", []):
            if entity and isinstance(entity, str) and entity.strip():
                entity_uri = self.add_entity(entity)
                if not entity_uri:
                    print(f"Warning: 관계 데이터의 엔티티 생성 실패: {entity}")
        
        # 관계 추가
        for relation in relations_data.get("relations", []):
            source = relation.get("source")
            rel_type = relation.get("relation")
            target = relation.get("target")
            
            if source and rel_type and target:
                success = self.add_relation(source, rel_type, target)
                if not success:
                    print(f"Warning: 관계 추가 실패: {source} -{rel_type}-> {target}")
    
    def process_metadata(self, metadata: Dict[str, Any]) -> None:
        """
        메타데이터에서 정보 추출하여 온톨로지에 추가
        
        Args:
            metadata (Dict[str, Any]): 추출된 메타데이터
        """
        if not metadata:
            return
            
        # 키워드를 엔티티로 추가
        for keyword in metadata.get("keywords", []):
            if keyword and isinstance(keyword, str) and keyword.strip():
                keyword_entity = self.add_entity(keyword)
                if not keyword_entity:
                    print(f"Warning: 키워드 엔티티 생성 실패: {keyword}")
        
        # 주제를 엔티티로 추가
        for topic in metadata.get("topics", []):
            if topic and isinstance(topic, str) and topic.strip():
                topic_uri = self.add_entity(topic)
                if not topic_uri:
                    print(f"Warning: 주제 엔티티 생성 실패: {topic}")
                    continue
                
                # 문서 제목을 엔티티로 추가하고 주제와 연결
                if "title" in metadata and metadata["title"]:
                    title = metadata["title"]
                    if isinstance(title, str) and title.strip():
                        title_uri = self.add_entity(title)
                        if title_uri:  # title_uri가 유효한 경우에만 관계 추가
                            self.graph.add((title_uri, self.RELATIONS["related"], topic_uri))
                        else:
                            print(f"Warning: 제목 엔티티 생성 실패: {title}")
    
    def process_structured_data(self, structured_data: Dict[str, Any]) -> None:
        """
        구조화된 데이터에서 정보 추출하여 온톨로지에 추가
        
        Args:
            structured_data (Dict[str, Any]): 추출된 구조화 데이터
        """
        if not structured_data:
            return
        
        # 테이블 데이터 처리
        for table in structured_data.get("tables", []):
            table_title = table.get("title", "")
            headers = table.get("headers", [])
            rows = table.get("rows", [])
            
            # 테이블 제목을 엔티티로 추가
            if table_title:
                table_entity = self.add_entity(table_title)
                
                # 행 데이터 처리
                for row in rows:
                    # 행이 비어 있거나 유효하지 않은 경우 건너뛰기
                    if not row or not isinstance(row, (list, tuple)) or len(row) == 0:
                        print(f"Warning: 비어있거나 유효하지 않은 행 데이터 건너뛰기: {row}")
                        continue
                        
                    # 첫 번째 열을 주요 엔티티로 간주
                    if not row[0] or not isinstance(row[0], str) or not row[0].strip():
                        print(f"Warning: 유효하지 않은 첫 번째 열 데이터 건너뛰기: {row[0]}")
                        continue
                        
                    entity1 = self.add_entity(row[0])
                    if not entity1:
                        print(f"Warning: 첫 번째 엔티티 생성 실패: {row[0]}")
                        continue
                    
                    # 두 번째 열부터 관계 또는 속성으로 처리
                    for i in range(1, min(len(row), len(headers))):
                        # 헤더가 있는 경우, 헤더를 관계 유형으로 사용
                        if i < len(headers) and headers[i]:
                            rel_name = headers[i]
                            # 가장 유사한 관계 유형 찾기
                            closest_rel = "related"  # 기본값
                            for rel in self.RELATIONS:
                                if rel.lower() in rel_name.lower():
                                    closest_rel = rel
                                    break
                            
                            # 값이 숫자나 날짜가 아닌 의미 있는 엔티티인 경우
                            if (row[i] and isinstance(row[i], str) and row[i].strip() and 
                                not row[i].isdigit() and "%" not in row[i]):
                                entity2 = self.add_entity(row[i])
                                if entity2:  # entity2가 유효한 경우에만 관계 추가
                                    self.graph.add((entity1, self.RELATIONS[closest_rel], entity2))
                                else:
                                    print(f"Warning: 두 번째 엔티티 생성 실패: {row[i]}")
        
        # 목록 데이터 처리
        for list_data in structured_data.get("lists", []):
            list_title = list_data.get("title", "")
            items = list_data.get("items", [])
            
            # 목록 제목을 엔티티로 추가
            if list_title:
                list_entity = self.add_entity(list_title)
                if not list_entity:
                    print(f"Warning: 목록 엔티티 생성 실패: {list_title}")
                    continue
                
                # 각 항목을 엔티티로 추가하고 목록과 연결
                for item in items:
                    if item and isinstance(item, str) and item.strip():
                        item_entity = self.add_entity(item)
                        if item_entity:  # item_entity가 유효한 경우에만 관계 추가
                            self.graph.add((list_entity, self.RELATIONS["include"], item_entity))
                        else:
                            print(f"Warning: 목록 항목 엔티티 생성 실패: {item}")
        
        # 통계 데이터 처리
        for stat in structured_data.get("statistics", []):
            stat_name = stat.get("name", "")
            stat_value = stat.get("value", "")
            stat_year = stat.get("year", "")
            
            if stat_name:
                stat_entity = self.add_entity(stat_name)
                if not stat_entity:
                    print(f"Warning: 통계 엔티티 생성 실패: {stat_name}")
                    continue
                
                # 값 추가
                if stat_value:
                    self.graph.add((stat_entity, self.NS["hasValue"], Literal(stat_value)))
                
                # 연도 추가
                if stat_year:
                    self.graph.add((stat_entity, self.NS["hasYear"], Literal(stat_year)))
    
    def process_extraction_result(self, result: Dict[str, Any]) -> None:
        """
        추출 결과를 처리하여 온톨로지에 추가
        
        Args:
            result (Dict[str, Any]): 파일 추출 결과
        """
        if not result:
            return
            
        # 메타데이터 처리
        metadata = result.get("metadata", {})
        self.process_metadata(metadata)
        
        # 온톨로지 관계 처리
        ontology = result.get("ontology", {})
        self.process_relations(ontology)
        
        # 구조화 데이터 처리
        structured_data = result.get("structured_data", {})
        self.process_structured_data(structured_data)
    
    def process_extraction_results(self, results: List[Dict[str, Any]]) -> None:
        """
        모든 추출 결과를 처리하여 온톨로지에 추가
        
        Args:
            results (List[Dict[str, Any]]): 추출 결과 목록
        """
        for result in results:
            self.process_extraction_result(result)
    
    def save_ttl(self, filename: str = "ontology.ttl") -> str:
        """
        온톨로지를 TTL 파일로 저장
        
        Args:
            filename (str): 저장할 파일명
            
        Returns:
            str: 저장된 파일 경로
        """
        output_path = os.path.join(self.output_dir, filename)
        self.graph.serialize(destination=output_path, format="turtle")
        return output_path
    
    def get_statistics(self, ttl_file_path: Optional[str] = None) -> Dict[str, Any]:
        """
        온톨로지 통계 정보 반환
        
        Args:
            ttl_file_path (Optional[str]): TTL 파일 경로 (지정된 경우 파일에서 로드하여 통계 생성)
            
        Returns:
            Dict[str, Any]: 통계 정보
        """
        # 파일 경로가 제공된 경우 해당 파일에서 그래프 로드
        if ttl_file_path and os.path.exists(ttl_file_path):
            # 임시 그래프 생성 (기존 그래프에 영향 없이 통계만 계산하기 위함)
            temp_graph = Graph()
            temp_graph.parse(ttl_file_path, format="turtle")
            
            # 타입별 엔티티 수
            entity_types = defaultdict(int)
            for s, p, o in temp_graph.triples((None, RDF.type, None)):
                type_name = str(o).split("#")[-1]
                entity_types[type_name] += 1
            
            # 관계 타입별 수
            relation_types = defaultdict(int)
            for s, p, o in temp_graph:
                if p not in [RDF.type, RDFS.label]:
                    rel_name = str(p).split("#")[-1]
                    relation_types[rel_name] += 1
            
            # 엔티티 및 관계 수 계산
            entity_count = len(list(temp_graph.subjects(RDF.type, None)))
            relation_count = sum(1 for s, p, o in temp_graph if p not in [RDF.type, RDFS.label])
            
            return {
                "entity_count": entity_count,
                "relation_count": relation_count,
                "entity_types": dict(entity_types),
                "relation_types": dict(relation_types)
            }
        else:
            # 기존 방식: 인메모리 그래프에서 통계 계산
            entity_count = len(list(self.graph.subjects(RDF.type, None)))
            relation_count = sum(1 for s, p, o in self.graph if p not in [RDF.type, RDFS.label])
            
            # 타입별 엔티티 수
            entity_types = defaultdict(int)
            for s, p, o in self.graph.triples((None, RDF.type, None)):
                type_name = str(o).split("#")[-1]
                entity_types[type_name] += 1
            
            # 관계 타입별 수
            relation_types = defaultdict(int)
            for s, p, o in self.graph:
                if p not in [RDF.type, RDFS.label]:
                    rel_name = str(p).split("#")[-1]
                    relation_types[rel_name] += 1
            
            return {
                "entity_count": entity_count,
                "relation_count": relation_count,
                "entity_types": dict(entity_types),
                "relation_types": dict(relation_types)
            }

    def get_entities_by_type(self, entity_type: str) -> List[str]:
        """
        특정 유형의 모든 엔티티를 가져옵니다
        
        Args:
            entity_type (str): 엔티티 유형 이름
            
        Returns:
            List[str]: 해당 유형의 엔티티 이름 목록
        """
        # entity_type에 해당하는 URI 찾기
        type_uri = None
        for type_name, uri in self.ENTITY_TYPES.items():
            if type_name.lower() == entity_type.lower():
                type_uri = uri
                break
        
        # 해당 유형의 URI가 없는 경우 빈 목록 반환
        if not type_uri:
            return []
        
        # 해당 유형의 모든 엔티티 찾기
        entities = []
        for subject in self.graph.subjects(RDF.type, type_uri):
            label = self.graph.value(subject, RDFS.label)
            if label:
                entities.append(str(label))
            else:
                # 라벨이 없는 경우 URI의 마지막 부분 사용
                entities.append(str(subject).split('#')[-1])
        
        return entities
    
    def check_entity_exists(self, entity_name: str) -> bool:
        """
        엔티티가 존재하는지 확인합니다
        
        Args:
            entity_name (str): 확인할 엔티티 이름
            
        Returns:
            bool: 존재하면 True, 아니면 False
        """
        # 모든 엔티티 라벨 가져오기
        all_labels = set()
        for s, p, o in self.graph.triples((None, RDFS.label, None)):
            all_labels.add(str(o))
        
        return entity_name in all_labels
    
    def find_similar_entities(self, entity_name: str, threshold: float = 0.7) -> List[str]:
        """
        유사한 이름을 가진 엔티티를 찾습니다
        
        Args:
            entity_name (str): 검색할 엔티티 이름
            threshold (float): 유사도 임계값 (0~1)
            
        Returns:
            List[str]: 유사한 엔티티 이름 목록
        """
        # 간단한 문자열 유사도 계산 함수
        def similarity(a: str, b: str) -> float:
            a = a.lower()
            b = b.lower()
            # 레벤슈타인 거리 기반 유사도 (Python 내장 라이브러리만 사용)
            import difflib
            return difflib.SequenceMatcher(None, a, b).ratio()
        
        # 모든 엔티티 라벨 가져오기
        all_labels = set()
        for s, p, o in self.graph.triples((None, RDFS.label, None)):
            all_labels.add(str(o))
        
        # 유사한 엔티티 찾기
        similar_entities = []
        for label in all_labels:
            if similarity(entity_name, label) >= threshold:
                similar_entities.append(label)
        
        # 유사도 순으로 정렬
        similar_entities.sort(key=lambda x: similarity(entity_name, x), reverse=True)
        return similar_entities
    
    def get_entity_relations(self, entity_name: str) -> List[Dict[str, str]]:
        """
        특정 엔티티와 관련된 모든 관계를 가져옵니다
        
        Args:
            entity_name (str): 엔티티 이름
            
        Returns:
            List[Dict[str, str]]: 관계 정보 목록 (주체, 관계, 객체)
        """
        relations = []
        
        # 엔티티 URI 찾기
        entity_uri = None
        for s, p, o in self.graph.triples((None, RDFS.label, Literal(entity_name, lang="ko"))):
            entity_uri = s
            break
        
        if not entity_uri:
            return []
        
        # 주체로서의 관계 찾기 (entity_name이 주어인 경우)
        for s, p, o in self.graph.triples((entity_uri, None, None)):
            if p not in [RDF.type, RDFS.label]:
                relation_name = str(p).split('#')[-1]
                
                # 객체의 라벨 가져오기
                object_label = self.graph.value(o, RDFS.label)
                if object_label:
                    object_name = str(object_label)
                else:
                    object_name = str(o).split('#')[-1]
                
                relations.append({
                    "subject": entity_name,
                    "relation": relation_name,
                    "object": object_name
                })
        
        # 객체로서의 관계 찾기 (entity_name이 목적어인 경우)
        for s, p, o in self.graph.triples((None, None, entity_uri)):
            if p not in [RDF.type, RDFS.label]:
                relation_name = str(p).split('#')[-1]
                
                # 주체의 라벨 가져오기
                subject_label = self.graph.value(s, RDFS.label)
                if subject_label:
                    subject_name = str(subject_label)
                else:
                    subject_name = str(s).split('#')[-1]
                
                relations.append({
                    "subject": subject_name,
                    "relation": relation_name,
                    "object": entity_name
                })
        
        return relations

def main():
    """테스트용 메인 함수"""
    import json
    
    # 임시 테스트 데이터
    test_data = {
        "metadata": {
            "title": "미국의 중국산 전기차 관세 인상 조치에 대한 분석",
            "keywords": ["관세", "전기차", "미국", "중국", "무역분쟁", "배터리"],
            "topics": ["무역정책", "전기차 시장", "국제 관계"]
        },
        "ontology": {
            "entities": ["미국", "중국", "관세", "전기차", "배터리", "테슬라", "BYD", "삼성SDI", "LG에너지솔루션"],
            "relations": [
                {"source": "미국", "relation": "regulated_by", "target": "관세"},
                {"source": "중국", "relation": "supply_to", "target": "배터리"},
                {"source": "배터리", "relation": "used_in", "target": "전기차"},
                {"source": "테슬라", "relation": "manufactured_by", "target": "전기차"},
                {"source": "BYD", "relation": "competes_with", "target": "테슬라"}
            ]
        },
        "structured_data": {
            "tables": [
                {
                    "title": "국가별 관세율",
                    "headers": ["국가", "제품", "기존 관세율", "신규 관세율", "적용일"],
                    "rows": [
                        ["미국", "중국산 전기차", "25%", "100%", "2025-04-27"],
                        ["미국", "중국산 배터리", "7.5%", "25%", "2025-04-27"]
                    ]
                }
            ],
            "lists": [
                {
                    "title": "주요 영향 받는 기업",
                    "items": ["테슬라", "GM", "현대자동차", "LG에너지솔루션"]
                }
            ]
        }
    }
    
    # 온톨로지 생성기 생성
    generator = OntologyGenerator()
    
    # 테스트 데이터 처리
    generator.process_extraction_result(test_data)
    
    # TTL 파일 저장
    ttl_path = generator.save_ttl("test_ontology.ttl")
    print(f"온톨로지 파일이 저장되었습니다: {ttl_path}")
    
    # 통계 출력
    stats = generator.get_statistics()
    print("\n--- 온톨로지 통계 ---")
    print(f"엔티티 수: {stats['entity_count']}")
    print(f"관계 수: {stats['relation_count']}")
    print("\n타입별 엔티티:")
    for type_name, count in stats['entity_types'].items():
        print(f"  - {type_name}: {count}개")
    print("\n관계 유형별 수:")
    for rel_name, count in stats['relation_types'].items():
        print(f"  - {rel_name}: {count}개")

if __name__ == "__main__":
    main() 