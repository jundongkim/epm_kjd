"""
DX-AI Advisor - 온톨로지 관리 모듈

TTL 형식의 온톨로지 생성, 관리 및 SPARQL 쿼리 기능을 제공합니다.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging

# RDF/OWL libraries
from rdflib import Graph, Namespace, URIRef, Literal, BNode
from rdflib.namespace import RDF, RDFS, OWL, XSD
import networkx as nx

# Internal imports
from .utils import AIAdvisorConfig, get_config, AIAdvisorException

logger = logging.getLogger(__name__)


class OntologyGenerator:
    """온톨로지 생성 클래스 - 추출된 정보를 TTL 형식의 온톨로지로 변환"""
    
    def __init__(self, config: Optional[AIAdvisorConfig] = None):
        # config가 코루틴인 경우 처리
        if config is not None and hasattr(config, '__await__'):
            # 코루틴인 경우 기본 설정 사용
            self.config = get_config()
        else:
            self.config = config or get_config()
            
        self.namespace = Namespace(self.config.ontology_namespace)
        self.graph = None
        self._initialize_graph()
    
    def _initialize_graph(self):
        """RDF 그래프 초기화"""
        self.graph = Graph()
        
        # 기본 네임스페이스 바인딩
        self.graph.bind("dxai", self.namespace)
        self.graph.bind("rdf", RDF)
        self.graph.bind("rdfs", RDFS)
        self.graph.bind("owl", OWL)
        self.graph.bind("xsd", XSD)
        
        # 온톨로지 헤더 추가
        ontology_uri = URIRef(self.config.ontology_namespace.rstrip('#'))
        self.graph.add((ontology_uri, RDF.type, OWL.Ontology))
        self.graph.add((ontology_uri, RDFS.label, Literal("DX-AI Advisor Manufacturing Ontology")))
        self.graph.add((ontology_uri, RDFS.comment, Literal("제조업 특화 온톨로지 - 공정, 설비, 품질 관리 도메인")))
        self.graph.add((ontology_uri, OWL.versionInfo, Literal("1.0.0")))
        
        # 기본 클래스 정의
        self._define_base_classes()
        
        # 기본 속성 정의
        self._define_base_properties()
    
    def _define_base_classes(self):
        """기본 클래스들을 정의"""
        base_classes = {
            "Entity": "기본 엔티티 클래스",
            "ManufacturingEntity": "제조업 엔티티",
            "Product": "제품",
            "Material": "원자재/소재",
            "Component": "부품",
            "Chemical": "화학물질",
            "Equipment": "설비",
            "Process": "공정",
            "ProcessLine": "공정 라인",
            "Quality": "품질",
            "Defect": "결함",
            "FailureMode": "고장 모드",
            "RootCause": "근본 원인",
            "TestMethod": "시험 방법",
            "Measurement": "측정",
            "Location": "위치",
            "Person": "사람",
            "Role": "역할"
        }
        
        for class_name, description in base_classes.items():
            class_uri = self.namespace[class_name]
            self.graph.add((class_uri, RDF.type, OWL.Class))
            self.graph.add((class_uri, RDFS.label, Literal(class_name)))
            self.graph.add((class_uri, RDFS.comment, Literal(description)))
        
        # 클래스 계층 구조 정의
        hierarchies = [
            ("ManufacturingEntity", "Entity"),
            ("Product", "ManufacturingEntity"),
            ("Material", "ManufacturingEntity"),
            ("Component", "ManufacturingEntity"),
            ("Chemical", "Material"),
            ("Equipment", "ManufacturingEntity"),
            ("Process", "ManufacturingEntity"),
            ("ProcessLine", "Process"),
            ("Quality", "ManufacturingEntity"),
            ("Defect", "Quality"),
            ("FailureMode", "Quality"),
            ("RootCause", "Quality"),
            ("TestMethod", "ManufacturingEntity"),
            ("Measurement", "ManufacturingEntity")
        ]
        
        for subclass, superclass in hierarchies:
            self.graph.add((self.namespace[subclass], RDFS.subClassOf, self.namespace[superclass]))
    
    def _define_base_properties(self):
        """기본 속성들을 정의"""
        # Object Properties (관계)
        object_properties = {
            "causedBy": ("caused by", "원인 관계"),
            "resultedIn": ("resulted in", "결과 관계"),
            "contributesTo": ("contributes to", "기여 관계"),
            "processedIn": ("processed in", "처리 관계"),
            "usedIn": ("used in", "사용 관계"),
            "feedsInto": ("feeds into", "공급 관계"),
            "operatesWith": ("operates with", "운영 관계"),
            "detectedIn": ("detected in", "탐지 관계"),
            "exceedsLimit": ("exceeds limit", "한계 초과 관계"),
            "causesDefect": ("causes defect", "결함 유발 관계"),
            "reactsWith": ("reacts with", "반응 관계"),
            "dissolvesIn": ("dissolves in", "용해 관계"),
            "catalyzes": ("catalyzes", "촉매 관계"),
            "maintainedBy": ("maintained by", "유지보수 관계"),
            "replacedBy": ("replaced by", "교체 관계"),
            "calibratedBy": ("calibrated by", "보정 관계"),
            "hasComponent": ("has component", "구성 요소 관계"),
            "partOf": ("part of", "부분 관계"),
            "locatedAt": ("located at", "위치 관계"),
            "performedBy": ("performed by", "수행 관계")
        }
        
        for prop_name, (label, comment) in object_properties.items():
            prop_uri = self.namespace[prop_name]
            self.graph.add((prop_uri, RDF.type, OWL.ObjectProperty))
            self.graph.add((prop_uri, RDFS.label, Literal(label)))
            self.graph.add((prop_uri, RDFS.comment, Literal(comment)))
        
        # Data Properties (속성)
        data_properties = {
            "hasName": ("has name", "이름 속성", XSD.string),
            "hasDescription": ("has description", "설명 속성", XSD.string),
            "hasValue": ("has value", "값 속성", XSD.float),
            "hasUnit": ("has unit", "단위 속성", XSD.string),
            "hasDate": ("has date", "날짜 속성", XSD.dateTime),
            "hasVersion": ("has version", "버전 속성", XSD.string),
            "hasStatus": ("has status", "상태 속성", XSD.string),
            "hasPriority": ("has priority", "우선순위 속성", XSD.integer),
            "hasConfidence": ("has confidence", "신뢰도 속성", XSD.float),
            "hasTemperature": ("has temperature", "온도 속성", XSD.float),
            "hasPressure": ("has pressure", "압력 속성", XSD.float),
            "hasFlow": ("has flow", "유량 속성", XSD.float),
            "hasPurity": ("has purity", "순도 속성", XSD.float),
            "hasYield": ("has yield", "수율 속성", XSD.float)
        }
        
        for prop_name, (label, comment, datatype) in data_properties.items():
            prop_uri = self.namespace[prop_name]
            self.graph.add((prop_uri, RDF.type, OWL.DatatypeProperty))
            self.graph.add((prop_uri, RDFS.label, Literal(label)))
            self.graph.add((prop_uri, RDFS.comment, Literal(comment)))
            self.graph.add((prop_uri, RDFS.range, datatype))
    
    async def generate_ontology(self, extraction_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """추출된 정보들로부터 온톨로지 생성"""
        try:
            entities_added = 0
            relations_added = 0
            
            for result in extraction_results:
                if "extraction" in result and "ontology_information" in result["extraction"]:
                    ontology_info = result["extraction"]["ontology_information"]
                    
                    # 엔티티 추가
                    if "entities" in ontology_info:
                        for entity in ontology_info["entities"]:
                            self._add_entity(entity)
                            entities_added += 1
                    
                    # 관계 추가
                    if "relations" in ontology_info:
                        for relation in ontology_info["relations"]:
                            self._add_relation(relation)
                            relations_added += 1
            
            # 온톨로지 통계 생성
            stats = self._generate_statistics()
            
            return {
                "generation_status": "success",
                "entities_added": entities_added,
                "relations_added": relations_added,
                "statistics": stats,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"온톨로지 생성 오류: {str(e)}")
            raise AIAdvisorException(f"온톨로지 생성 중 오류 발생: {str(e)}")
    
    def _add_entity(self, entity: Dict[str, Any]):
        """엔티티를 온톨로지에 추가"""
        try:
            entity_name = entity.get("name", "").strip()
            entity_type = entity.get("type", "Entity").strip()
            description = entity.get("description", "")
            
            if not entity_name:
                return
            
            # URI 생성 (특수문자 제거)
            safe_name = self._sanitize_uri(entity_name)
            entity_uri = self.namespace[safe_name]
            
            # 클래스 URI
            class_uri = self.namespace[entity_type] if entity_type in self.config.entity_types else self.namespace.Entity
            
            # 트리플 추가
            self.graph.add((entity_uri, RDF.type, class_uri))
            self.graph.add((entity_uri, self.namespace.hasName, Literal(entity_name)))
            
            if description:
                self.graph.add((entity_uri, self.namespace.hasDescription, Literal(description)))
            
            # 추가 메타데이터
            self.graph.add((entity_uri, self.namespace.hasDate, Literal(datetime.now().isoformat(), datatype=XSD.dateTime)))
            
        except Exception as e:
            logger.warning(f"엔티티 추가 실패 - {entity}: {str(e)}")
    
    def _add_relation(self, relation: Dict[str, Any]):
        """관계를 온톨로지에 추가"""
        try:
            subject = relation.get("subject", "").strip()
            predicate = relation.get("predicate", "").strip()
            obj = relation.get("object", "").strip()
            confidence = relation.get("confidence", 1.0)
            
            if not all([subject, predicate, obj]):
                return
            
            # URI 생성
            subject_uri = self.namespace[self._sanitize_uri(subject)]
            object_uri = self.namespace[self._sanitize_uri(obj)]
            
            # 관계 속성 매핑
            predicate_mapping = {
                'caused_by': 'causedBy',
                'resulted_in': 'resultedIn',
                'contributes_to': 'contributesTo',
                'processed_in': 'processedIn',
                'used_in': 'usedIn',
                'feeds_into': 'feedsInto',
                'operates_with': 'operatesWith',
                'detected_in': 'detectedIn',
                'exceeds_limit': 'exceedsLimit',
                'causes_defect': 'causesDefect',
                'reacts_with': 'reactsWith',
                'dissolves_in': 'dissolvesIn',
                'catalyzes': 'catalyzes',
                'maintained_by': 'maintainedBy',
                'replaced_by': 'replacedBy',
                'calibrated_by': 'calibratedBy'
            }
            
            predicate_name = predicate_mapping.get(predicate.lower(), predicate)
            predicate_uri = self.namespace[predicate_name]
            
            # 관계 트리플 추가
            self.graph.add((subject_uri, predicate_uri, object_uri))
            
            # 신뢰도 정보 추가 (리이피케이션 사용)
            if confidence < 1.0:
                statement = BNode()
                self.graph.add((statement, RDF.type, RDF.Statement))
                self.graph.add((statement, RDF.subject, subject_uri))
                self.graph.add((statement, RDF.predicate, predicate_uri))
                self.graph.add((statement, RDF.object, object_uri))
                self.graph.add((statement, self.namespace.hasConfidence, Literal(confidence, datatype=XSD.float)))
            
        except Exception as e:
            logger.warning(f"관계 추가 실패 - {relation}: {str(e)}")
    
    def _sanitize_uri(self, name: str) -> str:
        """URI에 사용할 수 있도록 이름을 정리"""
        import re
        # 특수문자를 언더스코어로 변경, 공백 제거
        sanitized = re.sub(r'[^\w가-힣]', '_', name)
        sanitized = re.sub(r'_+', '_', sanitized)  # 연속된 언더스코어 하나로
        return sanitized.strip('_')
    
    def _generate_statistics(self) -> Dict[str, Any]:
        """온톨로지 통계 생성"""
        try:
            # 전체 트리플 수
            total_triples = len(self.graph)
            
            # 클래스별 인스턴스 수
            classes_query = """
            SELECT ?class (COUNT(?instance) as ?count)
            WHERE {
                ?instance rdf:type ?class .
                ?class rdfs:subClassOf* dxai:Entity .
            }
            GROUP BY ?class
            """
            
            # 관계별 사용 횟수
            relations_query = """
            SELECT ?predicate (COUNT(*) as ?count)
            WHERE {
                ?s ?predicate ?o .
                ?predicate rdf:type owl:ObjectProperty .
            }
            GROUP BY ?predicate
            """
            
            class_stats = {}
            relation_stats = {}
            
            try:
                # 클래스 통계
                for row in self.graph.query(classes_query):
                    class_name = str(getattr(row, "class")).split('#')[-1] if '#' in str(getattr(row, "class")) else str(getattr(row, "class"))
                    class_stats[class_name] = int(row.count)
                
                # 관계 통계
                for row in self.graph.query(relations_query):
                    relation_name = str(row.predicate).split('#')[-1] if '#' in str(row.predicate) else str(row.predicate)
                    relation_stats[relation_name] = int(row.count)
            
            except Exception as query_error:
                logger.warning(f"SPARQL 쿼리 실행 오류: {str(query_error)}")
            
            return {
                "total_triples": total_triples,
                "total_entities": sum(class_stats.values()),
                "total_relations": sum(relation_stats.values()),
                "entity_types": class_stats,
                "relation_types": relation_stats,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"통계 생성 오류: {str(e)}")
            return {"error": str(e)}
    
    async def save_ontology(self, filename: Optional[str] = None) -> str:
        """온톨로지를 TTL 파일로 저장"""
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"dxai_ontology_{timestamp}.ttl"
            
            file_path = self.config.ontology_dir / filename
            
            # TTL 형식으로 저장
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.graph.serialize(format='turtle'))
            
            logger.info(f"온톨로지 저장됨: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"온톨로지 저장 오류: {str(e)}")
            raise AIAdvisorException(f"온톨로지 저장 중 오류 발생: {str(e)}")
    
    async def load_ontology(self, file_path: Path) -> bool:
        """기존 온톨로지 파일 로드"""
        try:
            if not file_path.exists():
                raise AIAdvisorException(f"온톨로지 파일을 찾을 수 없습니다: {file_path}")
            
            self.graph.parse(str(file_path), format='turtle')
            logger.info(f"온톨로지 로드됨: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"온톨로지 로드 오류: {str(e)}")
            raise AIAdvisorException(f"온톨로지 로드 중 오류 발생: {str(e)}")


class OntologyManager:
    """온톨로지 관리 및 쿼리 클래스"""
    
    def __init__(self, config: Optional[AIAdvisorConfig] = None):
        # config가 코루틴인 경우 처리
        if config is not None and hasattr(config, '__await__'):
            # 코루틴인 경우 기본 설정 사용
            self.config = get_config()
        else:
            self.config = config or get_config()
            
        self.graphs = {}  # 여러 온톨로지 관리
        self.active_graph = None
    
    async def load_ontology_file(self, file_path: Path, graph_name: str = "default") -> bool:
        """온톨로지 파일을 로드하여 관리"""
        try:
            graph = Graph()
            graph.parse(str(file_path), format='turtle')
            
            self.graphs[graph_name] = {
                "graph": graph,
                "file_path": str(file_path),
                "loaded_at": datetime.now().isoformat()
            }
            
            self.active_graph = graph_name
            logger.info(f"온톨로지 로드됨: {file_path} -> {graph_name}")
            return True
            
        except Exception as e:
            logger.error(f"온톨로지 로드 실패: {str(e)}")
            return False
    
    def get_entity_relations(self, entity_name: str, graph_name: str = None) -> List[Dict[str, Any]]:
        """특정 엔티티의 관계들을 조회"""
        graph_name = graph_name or self.active_graph
        if not graph_name or graph_name not in self.graphs:
            return []
        
        graph = self.graphs[graph_name]["graph"]
        namespace = Namespace(self.config.ontology_namespace)
        
        try:
            sanitized_name = self._sanitize_uri(entity_name)
            entity_uri = namespace[sanitized_name]
            
            relations = []
            
            # 주어로서의 관계들
            for predicate, obj in graph.predicate_objects(entity_uri):
                relations.append({
                    "type": "outgoing",
                    "subject": entity_name,
                    "predicate": str(predicate).split('#')[-1],
                    "object": str(obj).split('#')[-1] if '#' in str(obj) else str(obj)
                })
            
            # 목적어로서의 관계들
            for subj, predicate in graph.subject_predicates(entity_uri):
                relations.append({
                    "type": "incoming",
                    "subject": str(subj).split('#')[-1] if '#' in str(subj) else str(subj),
                    "predicate": str(predicate).split('#')[-1],
                    "object": entity_name
                })
            
            return relations
            
        except Exception as e:
            logger.error(f"엔티티 관계 조회 오류: {str(e)}")
            return []
    
    def get_entities_by_type(self, entity_type: str, graph_name: str = None) -> List[Dict[str, Any]]:
        """특정 타입의 엔티티들을 조회"""
        graph_name = graph_name or self.active_graph
        if not graph_name or graph_name not in self.graphs:
            return []
        
        graph = self.graphs[graph_name]["graph"]
        namespace = Namespace(self.config.ontology_namespace)
        
        try:
            type_uri = namespace[entity_type]
            entities = []
            
            query = f"""
            SELECT ?entity ?name ?description
            WHERE {{
                ?entity rdf:type <{type_uri}> .
                OPTIONAL {{ ?entity dxai:hasName ?name }} .
                OPTIONAL {{ ?entity dxai:hasDescription ?description }} .
            }}
            """
            
            for row in graph.query(query):
                entity_name = str(row.entity).split('#')[-1] if '#' in str(row.entity) else str(row.entity)
                entities.append({
                    "uri": str(row.entity),
                    "name": str(row.name) if row.name else entity_name,
                    "description": str(row.description) if row.description else "",
                    "type": entity_type
                })
            
            return entities
            
        except Exception as e:
            logger.error(f"타입별 엔티티 조회 오류: {str(e)}")
            return []
    
    def check_entity_exists(self, entity_name: str, graph_name: str = None) -> bool:
        """엔티티 존재 여부 확인"""
        graph_name = graph_name or self.active_graph
        if not graph_name or graph_name not in self.graphs:
            return False
        
        graph = self.graphs[graph_name]["graph"]
        namespace = Namespace(self.config.ontology_namespace)
        
        try:
            sanitized_name = self._sanitize_uri(entity_name)
            entity_uri = namespace[sanitized_name]
            
            # 해당 URI가 주어로 있는 트리플이 있는지 확인
            for _ in graph.predicate_objects(entity_uri):
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"엔티티 존재 확인 오류: {str(e)}")
            return False
    
    def execute_sparql_query(self, query: str, graph_name: str = None) -> List[Dict[str, Any]]:
        """SPARQL 쿼리 실행"""
        graph_name = graph_name or self.active_graph
        if not graph_name or graph_name not in self.graphs:
            return []
        
        graph = self.graphs[graph_name]["graph"]
        
        try:
            results = []
            for row in graph.query(query):
                result_dict = {}
                for var in row.labels:
                    value = getattr(row, var)
                    if value:
                        # URI인 경우 로컬명만 추출
                        if '#' in str(value):
                            result_dict[var] = str(value).split('#')[-1]
                        else:
                            result_dict[var] = str(value)
                    else:
                        result_dict[var] = None
                results.append(result_dict)
            
            return results
            
        except Exception as e:
            logger.error(f"SPARQL 쿼리 실행 오류: {str(e)}")
            return []
    
    def get_ontology_statistics(self, graph_name: str = None) -> Dict[str, Any]:
        """온톨로지 통계 조회"""
        graph_name = graph_name or self.active_graph
        if not graph_name or graph_name not in self.graphs:
            return {}
        
        graph = self.graphs[graph_name]["graph"]
        
        try:
            stats = {
                "graph_name": graph_name,
                "total_triples": len(graph),
                "file_path": self.graphs[graph_name]["file_path"],
                "loaded_at": self.graphs[graph_name]["loaded_at"]
            }
            
            # 클래스별 인스턴스 수 조회
            classes_query = """
            SELECT ?class (COUNT(?instance) as ?count)
            WHERE {
                ?instance rdf:type ?class .
            }
            GROUP BY ?class
            """
            
            class_stats = {}
            for row in graph.query(classes_query):
                class_name = str(getattr(row, "class")).split('#')[-1] if '#' in str(getattr(row, "class")) else str(getattr(row, "class"))
                class_stats[class_name] = int(row.count)
            
            stats["entity_types"] = class_stats
            
            return stats
            
        except Exception as e:
            logger.error(f"온톨로지 통계 조회 오류: {str(e)}")
            return {"error": str(e)}
    
    def get_available_ontologies(self) -> List[Dict[str, Any]]:
        """로드된 온톨로지 목록 조회"""
        return [
            {
                "name": name,
                "file_path": info["file_path"],
                "loaded_at": info["loaded_at"],
                "is_active": name == self.active_graph,
                "triple_count": len(info["graph"])
            }
            for name, info in self.graphs.items()
        ]
    
    def set_active_ontology(self, graph_name: str) -> bool:
        """활성 온톨로지 설정"""
        if graph_name in self.graphs:
            self.active_graph = graph_name
            return True
        return False
    
    def _sanitize_uri(self, name: str) -> str:
        """URI 안전한 이름으로 변환"""
        import re
        # 특수문자 제거 및 공백을 언더스코어로 변환
        sanitized = re.sub(r'[^\w\s-]', '', name)
        sanitized = re.sub(r'[-\s]+', '_', sanitized)
        return sanitized.lower()

    def export_to_networkx(self, graph_name: str = None) -> nx.Graph:
        """NetworkX 그래프로 내보내기"""
        try:
            import networkx as nx
            
            graph_name = graph_name or self.active_graph
            if not graph_name or graph_name not in self.graphs:
                return nx.Graph()
            
            graph = self.graphs[graph_name]["graph"]
            nx_graph = nx.Graph()
            
            # 모든 트리플을 NetworkX 그래프에 추가
            for subj, pred, obj in graph:
                subj_name = str(subj).split('#')[-1] if '#' in str(subj) else str(subj)
                pred_name = str(pred).split('#')[-1] if '#' in str(pred) else str(pred)
                obj_name = str(obj).split('#')[-1] if '#' in str(obj) else str(obj)
                
                nx_graph.add_edge(subj_name, obj_name, predicate=pred_name)
            
            return nx_graph
            
        except Exception as e:
            logger.error(f"NetworkX 내보내기 오류: {str(e)}")
            return nx.Graph()

    async def get_entities(self, entity_type: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """엔티티 목록 조회"""
        try:
            if entity_type:
                return self.get_entities_by_type(entity_type)
            
            # 모든 엔티티 조회
            graph_name = self.active_graph
            if not graph_name or graph_name not in self.graphs:
                return []
            
            graph = self.graphs[graph_name]["graph"]
            namespace = Namespace(self.config.ontology_namespace)
            
            query = f"""
            SELECT DISTINCT ?entity ?type
            WHERE {{
                ?entity rdf:type ?type .
                FILTER(STRSTARTS(STR(?type), "{self.config.ontology_namespace}"))
            }}
            LIMIT {limit}
            """
            
            entities = []
            for row in graph.query(query):
                entity_name = str(row.entity).split('#')[-1] if '#' in str(row.entity) else str(row.entity)
                type_name = str(row.type).split('#')[-1] if '#' in str(row.type) else str(row.type)
                
                entities.append({
                    "uri": str(row.entity),
                    "name": entity_name,
                    "type": type_name
                })
            
            return entities
            
        except Exception as e:
            logger.error(f"엔티티 목록 조회 오류: {str(e)}")
            return []

    async def get_entity_count(self) -> int:
        """엔티티 개수 조회"""
        try:
            graph_name = self.active_graph
            if not graph_name or graph_name not in self.graphs:
                return 0
            
            graph = self.graphs[graph_name]["graph"]
            
            query = """
            SELECT (COUNT(DISTINCT ?entity) AS ?count)
            WHERE {
                ?entity rdf:type ?type .
            }
            """
            
            result = graph.query(query)
            for row in result:
                return int(row.count)
            
            return 0
            
        except Exception as e:
            logger.error(f"엔티티 개수 조회 오류: {str(e)}")
            return 0

    async def search_entities(self, query: str) -> List[Dict[str, Any]]:
        """엔티티 검색"""
        try:
            graph_name = self.active_graph
            if not graph_name or graph_name not in self.graphs:
                return []
            
            graph = self.graphs[graph_name]["graph"]
            namespace = Namespace(self.config.ontology_namespace)
            
            # 검색 쿼리 구성
            search_query = f"""
            SELECT DISTINCT ?entity ?type ?name
            WHERE {{
                ?entity rdf:type ?type .
                OPTIONAL {{ ?entity dxai:hasName ?name }} .
                FILTER(STRSTARTS(STR(?type), "{self.config.ontology_namespace}"))
                FILTER(
                    CONTAINS(LCASE(STR(?entity)), LCASE("{query}")) ||
                    CONTAINS(LCASE(STR(?name)), LCASE("{query}"))
                )
            }}
            LIMIT 10
            """
            
            entities = []
            for row in graph.query(search_query):
                entity_name = str(row.entity).split('#')[-1] if '#' in str(row.entity) else str(row.entity)
                type_name = str(row.type).split('#')[-1] if '#' in str(row.type) else str(row.type)
                display_name = str(row.name) if row.name else entity_name
                
                entities.append({
                    "uri": str(row.entity),
                    "name": entity_name,
                    "display_name": display_name,
                    "type": type_name,
                    "score": 1.0  # 기본 점수
                })
            
            return entities
            
        except Exception as e:
            logger.error(f"엔티티 검색 오류: {str(e)}")
            return []

    async def update_from_document(self, document_result: Dict[str, Any]) -> bool:
        """문서에서 추출된 정보로 온톨로지 업데이트"""
        try:
            # 문서에서 추출된 엔티티 정보 가져오기
            extraction_info = document_result.get("extraction", {})
            entities = extraction_info.get("entities", [])
            relations = extraction_info.get("relations", [])
            
            if not entities and not relations:
                return True  # 업데이트할 내용이 없음
            
            # 온톨로지 생성기 사용
            generator = OntologyGenerator(self.config)
            
            # 기존 온톨로지 로드
            if self.active_graph and self.active_graph in self.graphs:
                existing_graph = self.graphs[self.active_graph]["graph"]
                generator.graph = existing_graph
            
            # 새로운 정보 추가
            for entity in entities:
                generator._add_entity(entity)
            
            for relation in relations:
                generator._add_relation(relation)
            
            # 업데이트된 온톨로지 저장
            updated_graph = generator.graph
            if updated_graph:
                self.graphs[self.active_graph or "default"] = {
                    "graph": updated_graph,
                    "updated_at": datetime.now().isoformat()
                }
                
                logger.info(f"온톨로지 업데이트 완료: {len(entities)} 엔티티, {len(relations)} 관계")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"온톨로지 업데이트 오류: {str(e)}")
            return False

    async def remove_document_entities(self, document_id: str) -> bool:
        """문서 관련 엔티티 제거"""
        try:
            # 현재는 간단한 구현
            # 실제로는 문서 ID와 연결된 엔티티들을 식별하여 제거해야 함
            logger.info(f"문서 {document_id} 관련 엔티티 제거 요청")
            return True
            
        except Exception as e:
            logger.error(f"문서 엔티티 제거 오류: {str(e)}")
            return False 