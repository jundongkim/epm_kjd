"""
LangChain과 LangGraph를 활용한 어드바이저 에이전트 모듈
"""
import os
import json
import re
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime

from langchain.agents import Tool, AgentExecutor
from langchain.agents.format_scratchpad import format_to_openai_functions
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.tools import tool
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import BaseModel, Field
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain.schema.runnable import RunnablePassthrough
from langchain_ollama import ChatOllama
from langchain.callbacks.manager import CallbackManagerForToolRun
from langchain.memory import ConversationBufferMemory
from langchain.schema.vectorstore import VectorStore
from rdflib import Graph

from src.utils.config import DEFAULT_LLM_MODEL, DEFAULT_REPORT_SECTIONS
from src.embeddings.embedding_manager import EmbeddingManager
from src.ontology.ontology_generator import OntologyGenerator

# 모델 인스턴스 생성
def get_llm(model_name=DEFAULT_LLM_MODEL, streaming=False):
    """
    대화 모델 인스턴스 생성
    
    Args:
        model_name (str): 모델명
        streaming (bool): 스트리밍 모드 활성화 여부
        
    Returns:
        ChatOllama: 모델 인스턴스
    """
    return ChatOllama(
        model=model_name, 
        temperature=0.2,
        streaming=streaming,
        request_timeout=60.0  # 요청 타임아웃 설정
    )


class AdvisorAgent:
    """LangChain 기반 어드바이저 에이전트 클래스"""
    
    def __init__(self, 
                 model_name: str = DEFAULT_LLM_MODEL,
                 embedding_manager: Optional[EmbeddingManager] = None,
                 ontology_generator: Optional[OntologyGenerator] = None,
                 index_name: str = "document_index",
                 vector_db_path: Optional[str] = None,
                 ontology_path: Optional[str] = None,
                 streaming: bool = False):
        """
        어드바이저 에이전트 초기화
        
        Args:
            model_name (str): 사용할 LLM 모델명
            embedding_manager (EmbeddingManager, optional): 임베딩 관리자
            ontology_generator (OntologyGenerator, optional): 온톨로지 생성기
            index_name (str): 사용할 벡터 DB 인덱스명
            vector_db_path (str, optional): 벡터 DB 경로
            ontology_path (str, optional): 온톨로지 파일 경로
            streaming (bool): 스트리밍 모드 활성화 여부
        """
        self.model_name = model_name
        self.streaming = streaming
        self.llm = get_llm(model_name, streaming=streaming)
        
        # 스트리밍용 별도 LLM 인스턴스 생성
        self.streaming_llm = get_llm(model_name, streaming=True)
        
        # 벡터 DB 경로 저장
        self.vector_db_path = vector_db_path
        
        # 벡터 DB 경로가 지정된 경우 해당 경로에서 인덱스명 추출
        if vector_db_path:
            self.index_name = os.path.basename(vector_db_path)
        else:
            self.index_name = index_name
        
        # 임베딩 관리자 초기화
        self.embedding_manager = embedding_manager or EmbeddingManager()
        
        # 온톨로지 경로 저장
        self.ontology_path = ontology_path
        
        # 온톨로지 생성기 초기화
        self.ontology_generator = ontology_generator or OntologyGenerator()
        
        # 온톨로지 경로가 지정된 경우 해당 파일 로드
        if self.ontology_path and os.path.exists(self.ontology_path):
            self.ontology_generator.get_statistics(ttl_file_path=self.ontology_path)
        
        # 벡터 DB 로드
        self.vectorstore = self.embedding_manager.load_vector_db(self.index_name)
        
        # 대화 메모리 초기화
        self.memory = ConversationBufferMemory(
            return_messages=True,
            memory_key="chat_history",
            output_key="output"
        )
        
        # 에이전트 초기화
        self.agent = self._initialize_agent()
    
    def _initialize_agent(self) -> AgentExecutor:
        """
        에이전트 초기화
        
        Returns:
            AgentExecutor: 에이전트 실행기
        """
        # 도구 정의
        print("[AGENT] 에이전트 초기화 시작")
        tools = [
            Tool(
                name="search_documents",
                func=self._search_documents,
                description="문서 검색 도구. 질의와 관련된 문서를 검색할 때 사용합니다."
            ),
            Tool(
                name="search_with_filter",
                func=self._search_with_filter,
                description="필터를 적용하여 문서 검색. 특정 조건(예: 파일 유형, 날짜)을 만족하는 문서를 검색할 때 사용합니다."
            ),
            Tool(
                name="query_ontology",
                func=self._query_ontology,
                description="온톨로지 정보 조회. 엔티티 관계, 특성 등의 온톨로지 정보를 조회할 때 사용합니다."
            ),
            Tool(
                name="generate_report",
                func=self._generate_report,
                description="보고서 생성 도구. 사용자가 질의한 주제에 대한 심층 분석 보고서를 생성할 때 사용합니다."
            ),
            Tool(
                name="get_entity_relationships",
                func=self._get_entity_relationships,
                description="특정 엔티티와 관련된 관계 조회. 특정 엔티티의 모든 관계를 조회할 때 사용합니다."
            ),
            Tool(
                name="get_embedding_statistics",
                func=self._get_embedding_statistics,
                description="임베딩 데이터베이스 통계 조회. 임베딩된 문서 수, 유형별 통계 등을 조회할 때 사용합니다."
            )
        ]
        print(f"[AGENT] {len(tools)}개 도구 정의 완료")
        
        # 시스템 메시지 및 프롬프트 템플릿 정의
        system_message = """You are an AI advisor specialized in manufacturing processes, quality control, and industrial problem-solving.

Beyond simply providing information, please offer the following types of in-depth analysis:
1. Detailed explanation of manufacturing processes, equipment functions, and technical specifications
2. Root cause analysis for quality issues and production problems
3. Statistical interpretation of quality data and performance metrics
4. Specific solutions and improvement strategies for manufacturing challenges
5. Industry best practices and technological innovations in manufacturing

When discussing manufacturing topics, please:
- Describe processes step-by-step with technical accuracy
- Explain quality control parameters and their significance
- Identify potential failure modes and their impacts
- Connect issues to specific equipment, materials, or process steps
- Provide actionable recommendations for improvement

IMPORTANT: 
1. ALWAYS cite the exact source filenames for your information. Use the format: "According to '[FILENAME]'..." or "As mentioned in '[FILENAME]'..."
2. If information comes from multiple sources, cite each one separately.
3. If you're unsure about any information, clearly state this and suggest what additional data might be needed.
4. Detect the language of the user's question and respond in that language. If the user asks in English, respond in English. If the user asks in Korean, respond in Korean.

Maintain a professional and technical tone, especially when discussing manufacturing and quality topics. Provide thorough, practical responses that would be valuable to manufacturing professionals."""
        
        human_message = "{input}"
        
        # 프롬프트 템플릿 정의
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", human_message),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        print("[AGENT] 프롬프트 템플릿 정의 완료")
        
        # 에이전트 정의
        agent_chain = (
            {
                "input": lambda x: x["input"],
                "chat_history": lambda x: x["chat_history"],
                "agent_scratchpad": lambda x: format_to_openai_functions(x["intermediate_steps"])
            }
            | prompt
            | self.llm
            | OpenAIFunctionsAgentOutputParser()
        )
        print("[AGENT] 에이전트 체인 정의 완료")
        
        # 에이전트 실행기 설정
        print("[AGENT] 에이전트 실행기 생성")
        return AgentExecutor(
            agent=agent_chain,
            tools=tools,
            verbose=True,
            memory=self.memory,
            handle_parsing_errors=True,
            max_iterations=5  # 반복 횟수 제한 추가
        )
    
    def _search_documents(self, query: str, k: int = 5) -> str:
        """
        문서 검색 도구
        
        Args:
            query (str): 검색 쿼리
            k (int): 반환할 결과 수
            
        Returns:
            str: 검색 결과
        """
        print(f"[TOOL] search_documents 호출됨 - 쿼리: {query}, k: {k}")
        if not self.vector_db_path:
            print("[TOOL] search_documents 실패 - 벡터 DB 경로 없음")
            return "벡터 데이터베이스 경로가 설정되지 않았습니다."
            
        if not self.vectorstore:
            self.vectorstore = self.embedding_manager.load_vector_db(self.index_name)
            if not self.vectorstore:
                print("[TOOL] search_documents 실패 - 벡터 DB 로드 실패")
                return "벡터 데이터베이스를 로드할 수 없습니다."
        
        docs_with_scores = self.embedding_manager.similarity_search(query, k=k, index_name=self.index_name)
        
        if not docs_with_scores:
            print("[TOOL] search_documents - 검색 결과 없음")
            return "검색 결과가 없습니다."
        
        results = []
        for i, (doc, score) in enumerate(docs_with_scores, 1):
            content = doc.page_content
            source = doc.metadata.get("source", "")
            doc_type = doc.metadata.get("type", "문서")
            
            # 결과 포맷팅 및 메타데이터 처리
            result_str = f"[결과 {i} (관련도: {score:.4f})]\n"
            result_str += f"출처: {source}\n"
            result_str += f"유형: {doc_type}\n"
            result_str += f"내용: {content}\n"
            
            results.append(result_str)
        
        print(f"[TOOL] search_documents 완료 - {len(results)}개 결과 반환")
        return "\n\n".join(results)
    
    def _search_with_filter(self, query: str, filter_str: str, k: int = 5) -> str:
        """
        필터를 적용한 문서 검색 도구
        
        Args:
            query (str): 검색 쿼리
            filter_str (str): 필터 문자열 (JSON 형식)
            k (int): 반환할 결과 수
            
        Returns:
            str: 검색 결과
        """
        print(f"[TOOL] search_with_filter 호출됨 - 쿼리: {query}, 필터: {filter_str}, k: {k}")
        if not self.vector_db_path:
            print("[TOOL] search_with_filter 실패 - 벡터 DB 경로 없음")
            return "벡터 데이터베이스 경로가 설정되지 않았습니다."
            
        if not self.vectorstore:
            self.vectorstore = self.embedding_manager.load_vector_db(self.index_name)
            if not self.vectorstore:
                print("[TOOL] search_with_filter 실패 - 벡터 DB 로드 실패")
                return "벡터 데이터베이스를 로드할 수 없습니다."
        
        # 필터 파싱
        try:
            filter_dict = json.loads(filter_str)
            print(f"[TOOL] 필터 파싱 성공: {filter_dict}")
        except:
            print("[TOOL] 필터 파싱 실패")
            return "필터 형식이 올바르지 않습니다. JSON 형식으로 작성해주세요."
        
        # 필터링된 검색 수행
        docs_with_scores = self.embedding_manager.similarity_search_with_filter(
            query, filter_dict, k=k, index_name=self.index_name
        )
        
        if not docs_with_scores:
            print("[TOOL] search_with_filter - 검색 결과 없음")
            return "검색 결과가 없습니다."
        
        results = []
        for i, (doc, score) in enumerate(docs_with_scores, 1):
            content = doc.page_content
            source = doc.metadata.get("source", "")
            doc_type = doc.metadata.get("type", "문서")
            
            # 결과 포맷팅 및 메타데이터 처리
            result_str = f"[결과 {i} (관련도: {score:.4f})]\n"
            result_str += f"출처: {source}\n"
            result_str += f"유형: {doc_type}\n"
            result_str += f"내용: {content}\n"
            
            results.append(result_str)
        
        print(f"[TOOL] search_with_filter 완료 - {len(results)}개 결과 반환")
        return "\n\n".join(results)
    
    def _query_ontology(self, query: str) -> str:
        """
        온톨로지 조회 도구
        
        Args:
            query (str): 조회 쿼리
            
        Returns:
            str: 조회 결과
        """
        print(f"[TOOL] query_ontology 호출됨 - 쿼리: {query}")
        try:
            # 온톨로지 경로가 지정된 경우 해당 파일 로드
            if self.ontology_path and os.path.exists(self.ontology_path):
                # 이미 초기화 시 로드했는지 확인
                if not hasattr(self.ontology_generator, 'graph') or len(self.ontology_generator.graph) == 0:
                    self.ontology_generator.get_statistics(ttl_file_path=self.ontology_path)
                
                # 통계 가져오기
                stats = self.ontology_generator.get_statistics(ttl_file_path=self.ontology_path)
                
                # 구체적 엔티티/관계 질의인지 확인
                if "관계" in query or "엔티티" in query or "온톨로지" in query:
                    if "통계" in query or "개수" in query or "수" in query:
                        result = json.dumps({
                            "entity_count": stats.get("entity_count", 0),
                            "relation_count": stats.get("relation_count", 0),
                            "entity_types": stats.get("entity_types", {}),
                            "relation_types": stats.get("relation_types", {}),
                        }, ensure_ascii=False, indent=2)
                        print(f"[TOOL] query_ontology - 통계 정보 반환")
                        return result
                    
                    # 특정 엔티티 유형 관련 질의
                    for entity_type in stats.get("entity_types", {}).keys():
                        if entity_type.lower() in query.lower():
                            entities = self.ontology_generator.get_entities_by_type(entity_type)
                            result = f"{entity_type} 유형 엔티티 목록 (총 {len(entities)}개):\n" + \
                                   "\n".join([f"- {e}" for e in entities[:20]]) + \
                                   (f"\n... 외 {len(entities) - 20}개" if len(entities) > 20 else "")
                            print(f"[TOOL] query_ontology - {entity_type} 유형 엔티티 목록 반환")
                            return result
                
                # 일반적인 온톨로지 통계 반환
                result = f"온톨로지 통계:\n" + \
                       f"- 총 엔티티 수: {stats.get('entity_count', 0)}개\n" + \
                       f"- 총 관계 수: {stats.get('relation_count', 0)}개\n" + \
                       f"- 엔티티 유형: {', '.join(stats.get('entity_types', {}).keys())}\n" + \
                       f"- 관계 유형: {', '.join(stats.get('relation_types', {}).keys())}"
                print("[TOOL] query_ontology - 기본 통계 정보 반환")
                return result
            else:
                print("[TOOL] query_ontology 실패 - 온톨로지 파일 없음")
                return "온톨로지 파일이 로드되지 않았습니다."
        except Exception as e:
            print(f"[TOOL] query_ontology 오류 발생: {str(e)}")
            return f"온톨로지 조회 중 오류 발생: {str(e)}"
    
    def _search_ontology_detailed(self, topic: str, doc_references: dict = None) -> tuple:
        """
        주제 기반 상세 온톨로지 검색
        
        Args:
            topic (str): 검색 주제
            doc_references (dict): 문서 참조 딕셔너리 (있으면 업데이트, 없으면 새로 생성)
            
        Returns:
            tuple: (ontology_info, doc_references, stats)
        """
        print(f"[ONTOLOGY] 상세 온톨로지 검색 시작 - 주제: {topic}")
        
        if doc_references is None:
            doc_references = {}
        
        # doc_references 구조 검증
        print(f"[ONTOLOGY] doc_references 타입: {type(doc_references)}, 크기: {len(doc_references)}")
        if doc_references:
            # 첫 번째 항목의 구조 확인
            first_key = next(iter(doc_references))
            first_value = doc_references[first_key]
            print(f"[ONTOLOGY] doc_references 샘플 - 키: '{first_key}', 값 타입: {type(first_value)}")
            if isinstance(first_value, str):
                print(f"[ONTOLOGY] 경고: doc_references 값이 str입니다. 새로 초기화합니다.")
                doc_references = {}
        
        ontology_info = ""
        stats = None
        
        if not self.ontology_path or not os.path.exists(self.ontology_path):
            print("[ONTOLOGY] 온톨로지 파일이 없음")
            return "", doc_references, None
        
        try:
            # 온톨로지 통계 가져오기
            stats = self.ontology_generator.get_statistics(ttl_file_path=self.ontology_path)
            
            # stats 타입 검증
            if not isinstance(stats, dict):
                print(f"[ONTOLOGY] 경고: get_statistics 반환 타입이 dict가 아님 - {type(stats)}")
                if isinstance(stats, str):
                    print(f"[ONTOLOGY] get_statistics 반환값(str): {stats[:200]}...")
                return "", doc_references, None
            
            print(f"[ONTOLOGY] 온톨로지 통계 로드 완료 - 엔티티: {stats.get('entity_count', 0)}개, 관계: {stats.get('relation_count', 0)}개")
            
            # *** 핵심 수정: 인메모리 그래프에 TTL 파일 로드 ***
            if hasattr(self.ontology_generator, 'graph') and self.ontology_path:
                # 기존 그래프 초기화
                self.ontology_generator.graph = Graph()
                self.ontology_generator.graph.bind("dxai", self.ontology_generator.NS)
                
                # TTL 파일에서 그래프 로드
                print(f"[ONTOLOGY] TTL 파일을 인메모리 그래프에 로드 중: {self.ontology_path}")
                self.ontology_generator.graph.parse(self.ontology_path, format="turtle")
                
                # 로드 확인
                graph_size = len(self.ontology_generator.graph)
                print(f"[ONTOLOGY] 그래프 로드 완료 - 총 {graph_size}개 트리플")
                
                # 실제 라벨 수 확인
                from rdflib.namespace import RDFS
                label_count = len(list(self.ontology_generator.graph.triples((None, RDFS.label, None))))
                print(f"[ONTOLOGY] 라벨 수: {label_count}개")
            else:
                print(f"[ONTOLOGY] 경고: 그래프 로드 실패 - graph 속성 없음 또는 ontology_path 없음")
            
            # 실제 온톨로지 엔티티 샘플 확인
            entity_types = stats.get("entity_types", {})
            if entity_types:
                print(f"[ONTOLOGY] 온톨로지 엔티티 유형들: {list(entity_types.keys())}")
                # 각 유형별로 몇 개 엔티티 샘플 출력
                for entity_type, count in list(entity_types.items())[:3]:  # 처음 3개 유형만
                    try:
                        sample_entities = self.ontology_generator.get_entities_by_type(entity_type)
                        if sample_entities:
                            print(f"[ONTOLOGY] {entity_type} 유형 샘플 ({len(sample_entities)}개): {sample_entities[:5]}")
                        else:
                            print(f"[ONTOLOGY] {entity_type} 유형: 엔티티 없음")
                    except Exception as e:
                        print(f"[ONTOLOGY] {entity_type} 샘플 가져오기 실패: {str(e)}")
            else:
                print(f"[ONTOLOGY] 경고: entity_types가 비어있음")
            
            # 한국어 조사 제거 함수
            def remove_korean_particles(text):
                """한국어 조사 제거"""
                particles = ['은', '는', '이', '가', '을', '를', '에', '의', '도', '만', '부터', '까지', '와', '과', '나', '나', '야', '아']
                for particle in particles:
                    if text.endswith(particle):
                        return text[:-len(particle)]
                return text
            
            # 주제 관련 엔티티와 관계 가져오기 - 키워드 전처리 개선
            topic_keywords = topic.lower().split()
            print(f"[ONTOLOGY] 원본 주제 키워드: {topic_keywords}")
            
            # 키워드 전처리: 조사 제거, 특수문자 제거, 길이 필터링
            cleaned_keywords = []
            for keyword in topic_keywords:
                # 특수문자 제거
                clean_word = re.sub(r'[^\w가-힣]', '', keyword)
                if len(clean_word) > 1:  # 1글자 이하 제외
                    # 한국어 조사 제거
                    clean_word = remove_korean_particles(clean_word)
                    if len(clean_word) > 1:  # 조사 제거 후에도 1글자 이상
                        cleaned_keywords.append(clean_word)
            
            print(f"[ONTOLOGY] 전처리된 키워드: {cleaned_keywords}")
            
            # 관계 정보 추출
            key_entities = []
            for keyword in cleaned_keywords:
                print(f"[ONTOLOGY] '{keyword}' 키워드로 유사 엔티티 검색 중...")
                found_entities = []
                
                try:
                    # 1. 기존 find_similar_entities 시도 (임계값 낮춤)
                    similar_entities = self.ontology_generator.find_similar_entities(keyword, threshold=0.3)
                    print(f"[ONTOLOGY] '{keyword}' find_similar_entities 반환 타입: {type(similar_entities)}, 값: {similar_entities}")
                    
                    if similar_entities and len(similar_entities) > 0:
                        # 각 키워드별로 최대 2개 엔티티만 사용
                        limited_similar = similar_entities[:2]
                        print(f"[ONTOLOGY] '{keyword}' -> {len(similar_entities)}개 유사 엔티티 중 {len(limited_similar)}개 선택: {limited_similar}")
                        found_entities.extend(limited_similar)
                    else:
                        print(f"[ONTOLOGY] '{keyword}' -> find_similar_entities 결과 없음")
                    
                    # 2. 직접 그래프에서 라벨 검색 (언어 태그 고려) - 항상 실행
                    print(f"[ONTOLOGY] '{keyword}' -> 직접 그래프 검색 시작")
                    direct_matches = []
                    if hasattr(self.ontology_generator, 'graph') and self.ontology_generator.graph:
                        # 모든 라벨을 가져와서 매칭
                        from rdflib.namespace import RDFS
                        label_count = 0
                        for s, p, o in self.ontology_generator.graph.triples((None, RDFS.label, None)):
                            label_count += 1
                            label_str = str(o)
                            # 언어 태그 제거
                            if '@' in label_str:
                                label_str = label_str.split('@')[0]
                            # 따옴표 제거
                            label_str = label_str.strip('"\'')
                            
                            # 키워드가 라벨에 포함되는지 확인 (대소문자 무시)
                            if keyword.lower() in label_str.lower():
                                direct_matches.append(label_str)
                        
                        print(f"[ONTOLOGY] '{keyword}' -> 총 {label_count}개 라벨 검사 완료")
                        
                        if direct_matches:
                            # 중복 제거하고 최대 2개만 사용
                            direct_matches = list(set(direct_matches))[:2]
                            print(f"[ONTOLOGY] '{keyword}' -> 직접 검색 {len(direct_matches)}개 매칭: {direct_matches}")
                            found_entities.extend(direct_matches)
                        else:
                            print(f"[ONTOLOGY] '{keyword}' -> 직접 검색 결과 없음")
                    else:
                        print(f"[ONTOLOGY] '{keyword}' -> 그래프가 없거나 비어있음")
                    
                    # 3. 마지막으로 get_entities_by_type을 통한 검색 - 항상 실행
                    print(f"[ONTOLOGY] '{keyword}' -> 타입별 엔티티 검색 시작")
                    all_entities = []
                    for entity_type in entity_types.keys():
                        try:
                            type_entities = self.ontology_generator.get_entities_by_type(entity_type)
                            if type_entities:
                                all_entities.extend(type_entities)
                        except Exception as type_error:
                            print(f"[ONTOLOGY] '{entity_type}' 타입 엔티티 가져오기 실패: {str(type_error)}")
                            continue
                    
                    print(f"[ONTOLOGY] '{keyword}' -> 총 {len(all_entities)}개 엔티티 수집됨")
                    
                    # 부분 매칭 시도 - 최대 2개만 사용
                    matching_entities = [e for e in all_entities if keyword.lower() in e.lower()]
                    if matching_entities:
                        limited_matching = matching_entities[:2]
                        print(f"[ONTOLOGY] '{keyword}' 부분 매칭 엔티티 중 {len(limited_matching)}개 선택: {limited_matching}")
                        found_entities.extend(limited_matching)
                    else:
                        print(f"[ONTOLOGY] '{keyword}' -> 부분 매칭 결과 없음")
                    
                    # 중복 제거하여 key_entities에 추가 - 전체적으로도 제한
                    unique_found = list(set(found_entities))[:3]  # 키워드별 최대 3개
                    key_entities.extend(unique_found)
                    print(f"[ONTOLOGY] '{keyword}' 최종 발견 엔티티: {len(unique_found)}개 - {unique_found}")
                        
                except Exception as e:
                    print(f"[ONTOLOGY] '{keyword}' 검색 중 오류: {str(e)}")
                    import traceback
                    print(f"[ONTOLOGY] 검색 오류 상세: {traceback.format_exc()}")
            
            # 중복 제거
            key_entities = list(set(key_entities))
            # *** 전체 엔티티 수 제한 ***
            max_total_entities = 5
            key_entities = key_entities[:max_total_entities]
            print(f"[ONTOLOGY] 추출된 주요 엔티티: {len(key_entities)}개 (제한: {max_total_entities}개) - {key_entities}")
            
            # 각 주요 엔티티에 대한 관계 정보 추출
            relation_count = 0
            max_relations_total = 10  # *** 전체 관계 수 제한 ***
            max_entities_to_process = 3  # *** 처리할 엔티티 수 제한 ***
            
            for entity in key_entities[:max_entities_to_process]:  # 처음 3개 엔티티만 처리
                if relation_count >= max_relations_total:
                    print(f"[ONTOLOGY] 관계 정보 한도 도달 ({max_relations_total}개), 추가 처리 중단")
                    break
                    
                try:
                    print(f"[ONTOLOGY] '{entity}' 엔티티의 관계 검색 중...")
                    relations = self.ontology_generator.get_entity_relations(entity)
                    if relations:
                        # 각 엔티티당 최대 3개 관계만 사용
                        limited_relations = relations[:3]
                        print(f"[ONTOLOGY] '{entity}' -> {len(relations)}개 관계 중 {len(limited_relations)}개 선택")
                        
                        # 주체 관계 (엔티티가 주어인 경우)
                        subject_relations = [r for r in limited_relations if r.get("subject") == entity]
                        for i, r in enumerate(subject_relations):
                            if relation_count >= max_relations_total:
                                break
                                
                            # 더 명확한 참조 이름 사용
                            ref_name = f"{r.get('subject', 'unknown')}_{r.get('relation', 'unknown')}_{r.get('object', 'unknown')}"
                            # 특수문자 제거 
                            ref_name = re.sub(r'[^\w가-힣]', '_', ref_name)
                            # 길이 제한 (너무 긴 이름 방지)
                            if len(ref_name) > 50:
                                ref_name = ref_name[:50]
                            # 중복 방지를 위한 번호 부여
                            if ref_name in doc_references:
                                ref_name = f"{ref_name}_{i+1}"
                            
                            content = f"{r.get('subject', 'unknown')} {r.get('relation', 'unknown')} {r.get('object', 'unknown')}"
                            doc_references[ref_name] = {
                                "type": "ontology_relation",
                                "relation": r
                            }
                            ontology_info += f"문서 '{ref_name}':\n{content}\n\n"
                            relation_count += 1
                    else:
                        print(f"[ONTOLOGY] '{entity}' -> 관계 없음")
                except Exception as e:
                    print(f"[ONTOLOGY] '{entity}' 관계 검색 중 오류: {str(e)}")
            
            print(f"[ONTOLOGY] 추출된 관계 정보: {relation_count}개 (제한: {max_relations_total}개)")
            
            # 온톨로지 유형 정보 추가 - 더 명확한 이름 사용
            entity_type_count = 0
            entity_types = stats.get("entity_types", {})
            
            if not isinstance(entity_types, dict):
                print(f"[ONTOLOGY] 경고: entity_types가 dict가 아님 - {type(entity_types)}")
                entity_types = {}
            
            # *** 온톨로지 정보 제한: 관련성 높은 유형만 선택 ***
            relevant_types = []
            topic_lower = topic.lower()
            
            # 주제와 관련성이 높은 엔티티 유형 우선 선택
            priority_types = ['ForeignMaterial', 'Defect', 'FailureMode', 'Equipment', 'Process', 'Issue']
            
            # 우선순위 유형 중 데이터가 있는 것들 선택
            for entity_type in priority_types:
                if entity_type in entity_types and entity_types[entity_type] > 0:
                    relevant_types.append(entity_type)
            
            # 최대 3개 유형까지만 처리 (과도한 온톨로지 정보 방지)
            relevant_types = relevant_types[:2]  # 3개 → 2개로 더 제한
            print(f"[ONTOLOGY] 선택된 관련 엔티티 유형: {relevant_types}")
            
            for entity_type in relevant_types:
                count = entity_types[entity_type]
                if count > 0:
                    try:
                        entities = self.ontology_generator.get_entities_by_type(entity_type)
                        if entities and len(entities) > 0:
                            # 각 유형당 최대 5개 엔티티만 사용
                            entities_to_use = entities[:3]  # 5개 → 3개로 더 제한
                            ref_name = f"{entity_type}_엔티티"
                            
                            content = f"{entity_type} 유형 엔티티: {', '.join(entities_to_use)}"
                            doc_references[ref_name] = {
                                "type": "ontology_entity_list",
                                "entity_type": entity_type,
                                "entities": entities_to_use
                            }
                            ontology_info += f"문서 '{ref_name}':\n{content}\n\n"
                            entity_type_count += 1
                            
                            print(f"[ONTOLOGY] {entity_type} 유형 처리 완료: {len(entities_to_use)}개 엔티티")
                    except Exception as e:
                        print(f"[ONTOLOGY] 엔티티 유형 '{entity_type}' 처리 중 오류: {str(e)}")
            
            print(f"[ONTOLOGY] 추출된 엔티티 유형 정보: {entity_type_count}개")
            
            # 안전한 doc_references 크기 계산
            ontology_doc_count = 0
            for k, v in doc_references.items():
                if isinstance(v, dict) and v.get('type', '').startswith('ontology'):
                    ontology_doc_count += 1
            
            print(f"[ONTOLOGY] 상세 온톨로지 검색 완료 - 총 {ontology_doc_count}개 온톨로지 문서 생성")
            
            return ontology_info, doc_references, stats
            
        except Exception as e:
            print(f"[ONTOLOGY] 상세 온톨로지 검색 오류: {str(e)}")
            import traceback
            print(f"[ONTOLOGY] 상세 오류 트레이스: {traceback.format_exc()}")
            return "", doc_references, None
    
    def _get_entity_relationships(self, entity: str) -> str:
        """
        엔티티 관계 조회 도구
        
        Args:
            entity (str): 엔티티 이름
            
        Returns:
            str: 관계 정보
        """
        print(f"[TOOL] get_entity_relationships 호출됨 - 엔티티: {entity}")
        try:
            # 온톨로지 경로가 지정된 경우 해당 파일 로드
            if self.ontology_path and os.path.exists(self.ontology_path):
                # 이미 초기화 시 로드했는지 확인
                if not hasattr(self.ontology_generator, 'graph') or len(self.ontology_generator.graph) == 0:
                    self.ontology_generator.get_statistics(ttl_file_path=self.ontology_path)
                
                # 엔티티가 존재하는지 확인
                entity_exists = self.ontology_generator.check_entity_exists(entity)
                
                if not entity_exists:
                    # 비슷한 이름의 엔티티 찾기
                    similar_entities = self.ontology_generator.find_similar_entities(entity)
                    
                    if similar_entities:
                        result = f"'{entity}' 엔티티를 찾을 수 없습니다. 다음과 같은 유사한 엔티티가 있습니다:\n" + \
                               "\n".join([f"- {e}" for e in similar_entities[:10]])
                        print(f"[TOOL] get_entity_relationships - 유사 엔티티 {len(similar_entities[:10])}개 반환")
                        return result
                    else:
                        print(f"[TOOL] get_entity_relationships - 엔티티 없음")
                        return f"'{entity}' 엔티티를 찾을 수 없습니다."
                
                # 엔티티 관계 가져오기
                relations = self.ontology_generator.get_entity_relations(entity)
                
                if not relations:
                    print(f"[TOOL] get_entity_relationships - 관계 없음")
                    return f"'{entity}' 엔티티에 관련된 관계가 없습니다."
                
                # 결과 출력 포맷팅
                formatted_relations = []
                
                # 주체 관계 (엔티티가 주어인 경우)
                subject_relations = [r for r in relations if r["subject"] == entity]
                if subject_relations:
                    formatted_relations.append("주체 관계:")
                    for r in subject_relations:
                        formatted_relations.append(f"- {r['relation']} -> {r['object']}")
                
                # 객체 관계 (엔티티가 목적어인 경우)
                object_relations = [r for r in relations if r["object"] == entity]
                if object_relations:
                    formatted_relations.append("\n객체 관계:")
                    for r in object_relations:
                        formatted_relations.append(f"- {r['subject']} -> {r['relation']} -> {entity}")
                
                result = "\n".join(formatted_relations)
                print(f"[TOOL] get_entity_relationships - {len(relations)}개 관계 반환")
                return f"'{entity}' 엔티티의 관계:\n{result}"
            else:
                print("[TOOL] get_entity_relationships 실패 - 온톨로지 파일 없음")
                return "온톨로지 파일이 로드되지 않았습니다."
        except Exception as e:
            print(f"[TOOL] get_entity_relationships 오류 발생: {str(e)}")
            return f"엔티티 관계 조회 중 오류 발생: {str(e)}"
    
    def _get_embedding_statistics(self) -> str:
        """
        임베딩 데이터베이스 통계 조회 도구
        
        Returns:
            str: 통계 정보
        """
        print("[TOOL] get_embedding_statistics 호출됨")
        try:
            if not self.vector_db_path:
                print("[TOOL] get_embedding_statistics 실패 - 벡터 DB 경로 없음")
                return "벡터 데이터베이스 경로가 설정되지 않았습니다."
                
            # 임베딩 통계 가져오기
            stats = self.embedding_manager.generate_embeddings_report(self.index_name)
            
            document_count = stats.get('document_count', 0)
            document_types = stats.get('document_types', {})
            file_statistics = stats.get('file_statistics', {})
            
            result = f"임베딩 데이터베이스 통계 ({self.index_name}):\n\n"
            result += f"총 문서 수: {document_count}개\n\n"
            
            if document_types:
                result += "문서 유형별 통계:\n"
                for doc_type, count in document_types.items():
                    result += f"- {doc_type}: {count}개\n"
                result += "\n"
            
            if file_statistics:
                result += "파일별 통계:\n"
                for filename, count in file_statistics.items():
                    result += f"- {filename}: {count}개\n"
            
            print(f"[TOOL] get_embedding_statistics 완료 - {document_count}개 문서, {len(document_types)}개 유형")
            return result
        except Exception as e:
            print(f"[TOOL] get_embedding_statistics 오류 발생: {str(e)}")
            return f"임베딩 통계 조회 중 오류 발생: {str(e)}"
    
    def _generate_report(self, topic: str, sections: str = None) -> str:
        """
        분석 보고서 생성 도구
        
        Args:
            topic (str): 보고서 주제
            sections (str): 보고서 섹션 (JSON 형식 문자열 또는 쉼표로 구분된 문자열)
            
        Returns:
            str: 생성된 보고서
        """
        print(f"[TOOL] generate_report 호출됨 - 주제: {topic}, 섹션: {sections}")
        if not sections:
            sections = DEFAULT_REPORT_SECTIONS
        else:
            try:
                # 1. JSON 문자열을 리스트로 변환 시도
                sections = json.loads(sections)
                print(f"[TOOL] 섹션 JSON 파싱 성공: {sections}")
            except:
                try:
                    # 2. 쉼표로 구분된 문자열로 처리 시도
                    if isinstance(sections, str) and ',' in sections:
                        sections = [s.strip() for s in sections.split(',') if s.strip()]
                        print(f"[TOOL] 섹션 쉼표 구분 파싱 성공: {sections}")
                    else:
                        # 3. 단일 문자열인 경우 리스트로 변환
                        sections = [sections.strip()] if sections.strip() else DEFAULT_REPORT_SECTIONS
                        print(f"[TOOL] 섹션 단일 문자열 처리: {sections}")
                except:
                    # 4. 모든 파싱 실패 시 기본 섹션 사용
                    print("[TOOL] 섹션 파싱 실패, 기본 섹션 사용")
                    sections = DEFAULT_REPORT_SECTIONS
        
        # 섹션 텍스트 생성
        sections_text = "\n".join([f"{i+1}. {section}" for i, section in enumerate(sections)])
        print(f"[TOOL] 섹션 텍스트 생성 완료: {len(sections)}개 섹션")
        
        # 관련 문서 검색 (검색 결과 수 증가: 기본 5개 → 15개)
        docs = self.vectorstore.similarity_search(topic, k=15)
        print(f"[TOOL] 관련 문서 {len(docs)}개 검색됨")
        
        # 문서 내용 요약
        context_summary = "\n\n".join([f"문서 {i+1}:\n{doc.page_content}" for i, doc in enumerate(docs)])
        
        # 보고서 생성 프롬프트
        raw_prompt = f"""
            Topic: {topic}

            Please create an in-depth analysis report with the following structure:
            {sections_text}

            Reference information:
            {context_summary}

            Requirements:
            1. Divide each section with Markdown headings (##)
            2. Provide deep insights (cause-effect analysis, stakeholder impact, etc.) rather than just listing facts
            3. Use data and statistics to support your claims
            4. Organize numerical information into tables
            5. Cite sources and evidence for all analyses
            6. IMPORTANT: Detect the language of the topic and write the report in that language. If the topic is in English, write the report in English. If the topic is in Korean, write the report in Korean.
            """
            
        # 스트리밍 모드가 아닌 경우 직접 LLM 호출 (문자열로 직접 전달)
        print("[TOOL] LLM 호출 중...")
        response = self.llm.invoke(raw_prompt)
        
        # AI 메시지 내용 반환
        print(f"[TOOL] generate_report 완료 - 보고서 길이: {len(response.content)}자")
        return response.content
    
    def run(self, query: str) -> str:
        """
        에이전트 실행
        
        Args:
            query (str): 사용자 질의
            
        Returns:
            str: 에이전트 응답
        """
        try:
            print(f"[AGENT] 에이전트 실행 시작: {query}")
            # 입력 변수를 명시적으로 지정하고 문자열 정리
            cleaned_query = query.strip()
            if not cleaned_query:
                return "질문을 입력해주세요."
                
            # 입력값 직접 전달
            print(f"[AGENT] AgentExecutor 호출 시작")
            response = self.agent.invoke(
                {
                    "input": cleaned_query,
                    "chat_history": self.memory.chat_memory.messages
                }
            )
            
            # 툴 사용 로그 출력
            if "intermediate_steps" in response:
                print("\n[AGENT] 사용된 툴 목록:")
                for i, step in enumerate(response["intermediate_steps"]):
                    action, output = step
                    print(f"[TOOL-{i+1}] 사용된 툴: {action.tool}")
                    print(f"[TOOL-{i+1}] 툴 입력: {action.tool_input}")
                    truncated_output = output[:200] + "..." if len(output) > 200 else output
                    print(f"[TOOL-{i+1}] 툴 출력: {truncated_output}")
            
            # 출력값 확인 및 후처리
            output = response.get("output", "죄송합니다, 응답을 생성하는 중 오류가 발생했습니다.")
            
            # 불필요한 설명이나 오류 메시지 제거
            if "질문이나 요청을 입력해주시면" in output or "질문해주세요" in output:
                return "죄송합니다, 질문을 제대로 이해하지 못했습니다. 다시 질문해주시겠어요?"
            
            truncated_output = output[:100] + "..." if len(output) > 100 else output
            print(f"[AGENT] 최종 응답: {truncated_output}")
                
            return output
        except Exception as e:
            print(f"[ERROR] 에이전트 오류: {str(e)}")
            return f"에이전트 실행 중 오류가 발생했습니다: {str(e)}"

    def stream_response(self, query: str, message_placeholder) -> str:
        """
        스트리밍 방식으로 에이전트 응답 생성
        
        Args:
            query (str): 사용자 질의
            message_placeholder: Streamlit 메시지 플레이스홀더
            
        Returns:
            str: 생성된 전체 응답
        """
        try:
            print(f"[STREAM] ===== 스트리밍 응답 생성 시작 =====")
            print(f"[STREAM] 사용자 쿼리: {query}")
            cleaned_query = query.strip()
            if not cleaned_query:
                print(f"[STREAM] 오류: 빈 쿼리")
                message_placeholder.markdown("질문을 입력해주세요.")
                return "질문을 입력해주세요."
            
            # 관련 문서 검색
            context = ""
            docs = []
            doc_sources = {}  # 문서별 출처 정보 저장
            vector_db_docs = []  # 벡터 DB 문서 저장
            ontology_docs = []   # 온톨로지 문서 저장
            
            # 벡터 DB 검색 결과 처리
            print(f"[STREAM] 벡터 DB에서 관련 문서 검색 시작")
            if self.vectorstore:
                print(f"[STREAM] 검색 파라미터 - 인덱스: {self.index_name}, k=12")
                docs_with_scores = self.embedding_manager.similarity_search(
                    query, k=12, index_name=self.index_name)  # 8개 → 12개로 증가
                if docs_with_scores:
                    docs = [doc for doc, _ in docs_with_scores]
                    print(f"[STREAM] 검색 결과: {len(docs)}개 문서 발견")
                    
                    # 각 문서별로 명확한 파일명 추출 및 포맷팅
                    formatted_docs = []
                    
                    # 모든 검색 결과 로깅 (처음 3개가 아닌 전체)
                    for i, (doc, score) in enumerate(docs_with_scores):
                        # 메타데이터 디버깅 로그
                        print(f"[DEBUG] 문서 {i+1} 메타데이터: {doc.metadata}")
                        
                        # 소스 식별 로직 개선 - 실제 JSON 구조에 맞춘 메타데이터 처리
                        source = f"문서_{i+1}"  # 기본 소스명
                        
                        if hasattr(doc, 'metadata') and doc.metadata:
                            print(f"[DEBUG] 문서 {i+1} 전체 메타데이터: {doc.metadata}")
                            
                            # 1. 온톨로지 관계 데이터인 경우 특별 처리
                            if (doc.metadata.get('entity_type') == 'relation' and 
                                doc.metadata.get('source_entity') and 
                                doc.metadata.get('relation_type') and 
                                doc.metadata.get('target_entity')):
                                
                                source_entity = doc.metadata.get('source_entity')
                                relation_type = doc.metadata.get('relation_type')
                                target_entity = doc.metadata.get('target_entity')
                                source = f"{source_entity}_{relation_type}_{target_entity}"
                                print(f"[DEBUG] 문서 {i+1} 온톨로지 관계로 소스 생성: {source}")
                                
                            # 2. 실제 문서의 경우 - 다층 구조 메타데이터에서 파일명 검색
                            else:
                                # 우선순위 1: 최상위 메타데이터 필드들
                                primary_fields = ['filename', 'title', 'file_path', 'source']
                                found_source = False
                                
                                for field in primary_fields:
                                    if doc.metadata.get(field):
                                        field_value = doc.metadata.get(field)
                                        print(f"[DEBUG] 문서 {i+1} 최상위 필드 발견 ({field}): {field_value}")
                                        
                                        # 파일 경로인 경우 파일명만 추출
                                        if isinstance(field_value, str) and ('/' in field_value or '\\' in field_value):
                                            field_value = os.path.basename(field_value)
                                        
                                        # PDF 확장자 제거
                                        if isinstance(field_value, str) and field_value.lower().endswith('.pdf'):
                                            field_value = field_value[:-4]
                                        
                                        # 유의미한 소스명이면 사용하고 루프 종료
                                        if isinstance(field_value, str) and len(field_value) > 0 and field_value != 'ontology':
                                            source = field_value
                                            print(f"[DEBUG] 문서 {i+1} 최상위에서 소스명 설정: {source}")
                                            found_source = True
                                            break
                                
                                # 우선순위 2: file_info 섹션에서 검색 (최상위에서 찾지 못한 경우)
                                if not found_source and doc.metadata.get('file_info'):
                                    file_info = doc.metadata.get('file_info')
                                    if isinstance(file_info, dict):
                                        for field in ['filename', 'file_path']:
                                            if file_info.get(field):
                                                field_value = file_info.get(field)
                                                print(f"[DEBUG] 문서 {i+1} file_info 필드 발견 ({field}): {field_value}")
                                                
                                                # 파일 경로인 경우 파일명만 추출
                                                if isinstance(field_value, str) and ('/' in field_value or '\\' in field_value):
                                                    field_value = os.path.basename(field_value)
                                                
                                                # PDF 확장자 제거
                                                if isinstance(field_value, str) and field_value.lower().endswith('.pdf'):
                                                    field_value = field_value[:-4]
                                                
                                                if isinstance(field_value, str) and len(field_value) > 0:
                                                    source = field_value
                                                    print(f"[DEBUG] 문서 {i+1} file_info에서 소스명 설정: {source}")
                                                    found_source = True
                                                    break
                                
                                # 우선순위 3: full_content 섹션에서 검색 (앞에서 찾지 못한 경우)
                                if not found_source and doc.metadata.get('full_content'):
                                    full_content = doc.metadata.get('full_content')
                                    if isinstance(full_content, dict):
                                        for field in ['filename', 'file_path']:
                                            if full_content.get(field):
                                                field_value = full_content.get(field)
                                                print(f"[DEBUG] 문서 {i+1} full_content 필드 발견 ({field}): {field_value}")
                                                
                                                # 파일 경로인 경우 파일명만 추출
                                                if isinstance(field_value, str) and ('/' in field_value or '\\' in field_value):
                                                    field_value = os.path.basename(field_value)
                                                
                                                # PDF 확장자 제거
                                                if isinstance(field_value, str) and field_value.lower().endswith('.pdf'):
                                                    field_value = field_value[:-4]
                                                
                                                if isinstance(field_value, str) and len(field_value) > 0:
                                                    source = field_value
                                                    print(f"[DEBUG] 문서 {i+1} full_content에서 소스명 설정: {source}")
                                                    found_source = True
                                                    break
                                
                                # 우선순위 4: 기타 메타데이터 필드들
                                if not found_source:
                                    for field in ['document_type', 'type', 'path', 'origin']:
                                        if doc.metadata.get(field):
                                            field_value = doc.metadata.get(field)
                                            print(f"[DEBUG] 문서 {i+1} 기타 필드 발견 ({field}): {field_value}")
                                            
                                            if isinstance(field_value, str) and len(field_value) > 0 and field_value != 'ontology':
                                                source = field_value
                                                print(f"[DEBUG] 문서 {i+1} 기타 필드에서 소스명 설정: {source}")
                                                break
                        
                        # 소스 이름 정리 - 특수문자와 공백 처리
                        source = re.sub(r'[^\w가-힣\s\-_.]', '_', source)  # 한글, 영문, 숫자, 하이픈, 언더스코어, 점만 허용
                        source = re.sub(r'\s+', '_', source)  # 공백을 언더스코어로 변경
                        source = re.sub(r'_{2,}', '_', source)  # 연속된 언더스코어 줄이기
                        source = source.strip('_')  # 앞뒤 언더스코어 제거
                        
                        # 소스 이름이 너무 길면 적절히 줄이기
                        if len(source) > 50:
                            source = source[:50]
                            print(f"[DEBUG] 문서 {i+1} 소스명 길이 조정: {source}")
                        
                        # 문서 내용에 소스 태그 추가하여 저장
                        doc_id = f"{source}"  # 소스 ID 설정
                        formatted_content = f">>> 문서 출처: '{doc_id}' <<<\n{doc.page_content}"
                        formatted_docs.append(formatted_content)
                        doc_sources[doc_id] = doc_id  # 키와 값을 동일하게 유지
                        vector_db_docs.append(formatted_content)  # 벡터 DB 문서 목록에 추가
                        
                        # 모든 문서 로깅 (유사도 점수 포함)
                        doc_content = doc.page_content[:100] + "..." if len(doc.page_content) > 100 else doc.page_content
                        print(f"[STREAM] 문서 {i+1} (소스: '{doc_id}'), 유사도: {score:.4f}, 내용: {doc_content}")
                        
                    print(f"[STREAM] 총 {len(vector_db_docs)}개 벡터 DB 문서가 컨텍스트에 추가됨")
                else:
                    print(f"[STREAM] 검색 결과: 문서 없음")
            else:
                print(f"[STREAM] 경고: 벡터 DB가 로드되지 않음")
            
            # 온톨로지 정보 추가
            print(f"[STREAM] 온톨로지 정보 조회 시작")
            ontology_info, doc_sources, ontology_stats = self._search_ontology_detailed(query, doc_sources)
            
            # 온톨로지 정보 처리
            if ontology_info:
                print(f"[STREAM] 유효한 온톨로지 정보 발견 (길이: {len(ontology_info)}자)")
                
                # 온톨로지 정보를 문서 목록에 추가
                ontology_lines = ontology_info.strip().split('\n\n')
                for line_block in ontology_lines:
                    if line_block.strip() and "문서 '" in line_block:
                        ontology_docs.append(line_block.strip())
                
                print(f"[STREAM] 총 {len(ontology_docs)}개 온톨로지 문서가 컨텍스트에 추가됨")
            else:
                print(f"[STREAM] 관련 온톨로지 정보 없음")
                
            # 벡터 DB와 온톨로지 정보 교차 배치하여 컨텍스트 구성
            # 정보 소스를 균형있게 배치하여 두 소스가 모두 활용되도록 함
            merged_docs = []
            max_len = max(len(vector_db_docs), len(ontology_docs))
            
            # *** 벡터 DB 우선 배치: 2:1 비율로 벡터 DB 문서를 더 많이 배치 ***
            vector_idx = 0
            ontology_idx = 0
            
            while vector_idx < len(vector_db_docs) or ontology_idx < len(ontology_docs):
                # 벡터 DB 문서 2개 추가
                for _ in range(2):
                    if vector_idx < len(vector_db_docs):
                        merged_docs.append(vector_db_docs[vector_idx])
                        vector_idx += 1
                
                # 온톨로지 문서 1개 추가
                if ontology_idx < len(ontology_docs):
                    merged_docs.append(ontology_docs[ontology_idx])
                    ontology_idx += 1
            
            context = "\n\n".join(merged_docs)
            print(f"[STREAM] 최종 컨텍스트: 총 {len(merged_docs)}개 문서 ({len(vector_db_docs)}개 벡터DB + {len(ontology_docs)}개 온톨로지, 2:1 비율 배치)")
            
            # 프롬프트 생성
            print(f"[STREAM] 프롬프트 생성 시작")
            system_message = """당신은 제조 공정, 품질 관리, 산업 문제 해결 분야의 전문 어드바이저입니다.

단순히 정보를 제공하는 것을 넘어, 다음과 같은 깊이 있는 분석을 제공해야 합니다:
1. 제조 공정, 장비 기능, 기술 사양에 대한 상세 설명
2. 품질 문제 및 생산 문제의 근본 원인 분석
3. 품질 데이터 및 성능 지표의 통계적 해석
4. 제조 과정의 문제에 대한 구체적인 해결책과 개선 전략
5. 제조 분야의 산업 모범 사례와 기술 혁신

제조 주제를 논의할 때는 다음과 같은 접근 방식을 사용하세요:
- 기술적 정확성을 갖춘 단계별 프로세스 설명
- 품질 관리 매개변수와 그 중요성 설명
- 잠재적 고장 모드와 그 영향 식별
- 특정 장비, 재료 또는 공정 단계와 문제 연결
- 개선을 위한 실행 가능한 권장 사항 제공

또한 현장 작업자의 관점에서 실용적인 정보를 제공해야 합니다:
- 복잡한 개념을 공장 현장 작업자가 이해할 수 있는 간단한 용어로 설명
- 실제 제조 환경에 적용할 수 있는 실용적인 조언 제공
- 일상 운영에 이 정보를 적용하는 방법에 대한 구체적인 예시 포함
- 생산 환경에서 신속하게 구현할 수 있는 핵심 사항 강조

### 인용 요구사항 - 주의 깊게 읽으세요 ###

모든 정보에 대해 정확한 출처를 반드시 인용해야 합니다:

1. 다음 형식을 사용하여 출처를 인용하세요: "According to '소스명'..." 또는 "'소스명'에 따르면..."
   예: "According to '양극재_주체관계', 인과관계가 존재합니다..."
   예: "'Mesh_터짐'에 따르면, 분급기의 Mesh는..."

2. 컨텍스트에서 ">>> 문서 출처: '소스명' <<<" 표시를 찾아 정확한 소스명을 사용하세요.
   - 따옴표 안에 있는 정확한 소스 이름을 사용하세요
   - 소스 이름을 변경하거나 약어를 사용하지 마세요
   - "[FILENAME]"이나 "documents"와 같은 일반적인 참조를 사용하지 마세요

3. 여러 소스의 정보를 사용할 때는 각 소스를 개별적으로 인용하세요
   예: "'공정_불량'에 따르면 불량률은 5%입니다. 또한, '품질_관리'에 따르면..."

4. 한 단락에 최소 하나 이상의 인용을 포함하세요

5. 벡터 데이터베이스 문서와 온톨로지 정보를 균형 있게 활용하세요

사용자 질문 언어를 감지하여 해당 언어로 응답하세요. 영어로 질문하면 영어로, 한국어로 질문하면 한국어로 답변하세요."""
            
            history = self.memory.chat_memory.messages
            print(f"[STREAM] 대화 기록: {len(history)}개 메시지")
            
            # 문서 출처 목록 추가 (클리어하게 정리)
            if doc_sources:
                # 소스 타입별로 구분하여 정리
                vector_sources = []
                ontology_sources = []
                
                for source_name in doc_sources.values():
                    if "온톨로지" in source_name or "_엔티티" in source_name or "_주체관계" in source_name or "_객체관계" in source_name:
                        ontology_sources.append(source_name)
                    else:
                        vector_sources.append(source_name)
                
                print(f"[STREAM] 벡터 DB 소스: {len(vector_sources)}개, 온톨로지 소스: {len(ontology_sources)}개")
                
                source_list = "# 문서 소스 (실제 문서):\n" + "\n".join([f"- '{source}'" for source in vector_sources])
                source_list += "\n\n# 온톨로지 소스 (구조화된 지식):\n" + "\n".join([f"- '{source}'" for source in ontology_sources])
                
                citation_guide = f"""중요: 다음 소스들에서 정보를 인용할 때는 반드시 "According to '소스명'" 또는 "'소스명'에 따르면" 형식을 사용하세요:

{source_list}

*** 균형잡힌 인용 규칙 (벡터 DB 우선) ***
1. 🔺 문서 소스(실제 문서)를 우선적으로 사용하세요 - 구체적인 사실, 데이터, 분석 결과
2. 🔹 온톨로지 소스(구조화된 지식)는 보조적으로 사용하세요 - 엔티티 관계와 분류 정보 
3. 각 단락에서 문서 소스를 먼저 인용하고, 필요시 온톨로지로 보완하세요
4. 전체 답변에서 문서 소스 60% 이상, 온톨로지 소스 40% 이하 비율을 유지하세요

올바른 예:
✅ "'241101_v0.1_CAM5_3L_금속이물_NG_발생_件'에 따르면 구체적인 불량 발생 원인이 있으며, 'ForeignMaterial_엔티티'에서 관련 분류 정보를 확인할 수 있습니다."
✅ "'기술분석보고서'의 데이터 분석 결과 X%의 불량률이 확인되었고, 'Equipment_엔티티'에서 관련 설비 정보를 참조할 수 있습니다."

잘못된 예:
❌ 온톨로지만 사용: "'ForeignMaterial_엔티티'에 따르면... 'Equipment_엔티티'에서..."
❌ 문서 소스 생략: "일반적으로 금속이물은..."
❌ 일반적인 참조: "제공된 정보에 의하면..."

중요 요구사항:
1. 모든 단락의 첫 번째 인용은 문서 소스로 시작하세요
2. 구체적인 수치, 날짜, 분석 결과는 반드시 문서 소스에서 인용하세요
3. 현장 작업자를 위한 실용적인 내용에 중점을 두세요
4. 절대로 인용을 생략하거나 일반적인 참조를 사용하지 마세요"""
                context = f"{citation_guide}\n\n{context}"
                
                # 인용 출처 목록 로깅
                print(f"[STREAM] 사용 가능한 인용 출처 목록 ({len(doc_sources)}개):")
                for idx, source_name in enumerate(doc_sources.values(), 1):
                    print(f"[STREAM] 출처 {idx}: '{source_name}'")
            
            # 스트리밍 응답 생성
            full_response = ""
            
            # 스트리밍 생성 함수
            from langchain.schema.runnable import RunnableMap, RunnablePassthrough
            from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
            
            # 수정: 히스토리를 포함하는 프롬프트 템플릿
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_message),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{question}")
            ])
            
            # 현재 모델 인스턴스의 temperature 설정 변경
            # 더 결정적인 답변을 위해 temperature 낮춤
            original_temperature = self.streaming_llm.temperature if hasattr(self.streaming_llm, 'temperature') else None
            if hasattr(self.streaming_llm, 'temperature'):
                self.streaming_llm.temperature = 0.1  # 낮은 temperature로 설정
                print(f"[STREAM] LLM temperature 조정: {original_temperature} -> 0.1")
                
            chain = prompt | self.streaming_llm
            
            # 최종 쿼리 로깅
            final_query = f"""다음 정보와 지침을 바탕으로 제조 전문가로서 질문에 답변해주세요:

[제조 전문가 지침]
1. 제조 공정, 품질, 설비에 대한 전문적 분석을 제공하세요
2. 현장 작업자 관점에서 실용적인 내용을 제공하세요
3. 기술적 개념을 쉽게 설명하고 구체적인 예시와 해결책을 제시하세요
4. 모든 정보에 정확한 출처를 명시하세요

[정보]
{context}

[질문]
{query}

[답변 작성 규칙]
1. 모든 단락에 반드시 하나 이상의 출처를 "'소스명'에 따르면" 형식으로 인용하세요
2. 벡터 DB 문서와 온톨로지 정보를 균형있게 활용하세요
3. 이론적 설명과 함께 현장에서 적용 가능한 실용적인 해결책을 제시하세요
4. 단계별 지침이나 구체적인 예시를 포함하세요
5. 전문 용어는 반드시 쉽게 풀어서 설명하세요"""
            print(f"[STREAM] LLM 호출 준비 완료, 컨텍스트 길이: {len(context)}자")
            print(f"[STREAM] 스트리밍 응답 생성 시작")
            
            # 토큰 수 추적 변수
            token_count = 0
            
            for chunk in chain.stream({
                "question": final_query,
                "chat_history": history  # 수정: 히스토리 전달
            }):
                content = chunk.content if hasattr(chunk, 'content') else str(chunk)
                full_response += content
                token_count += 1
                message_placeholder.markdown(full_response + "▌")
                
                # 로그 지나치게 많이 출력되지 않도록 매 50 글자마다만 출력
                if len(full_response) % 100 == 0:
                    print(f"[STREAM] 응답 생성 중... ({len(full_response)}자)")
            
            # 원래 temperature 복원
            if original_temperature is not None and hasattr(self.streaming_llm, 'temperature'):
                self.streaming_llm.temperature = original_temperature
                print(f"[STREAM] LLM temperature 복원: 0.1 -> {original_temperature}")
            
            # 최종 응답 표시 (커서 제거)
            message_placeholder.markdown(full_response)
            
            # 응답에서 인용 분석
            citations_used = []
            citation_pattern = r"According to ['\"]([^'\"]+)['\"]|['\"]([^'\"]+)['\"]에 따르면"
            citation_matches = re.finditer(citation_pattern, full_response, re.IGNORECASE)
            
            for match in citation_matches:
                if match.group(1):  # "According to" 패턴
                    citations_used.append(match.group(1))
                elif match.group(2):  # "에 따르면" 패턴
                    citations_used.append(match.group(2))
            
            # 중복 제거
            unique_citations = list(set(citations_used))
            citation_str = ", ".join(["'" + c + "'" for c in unique_citations])
            print(f"[STREAM] 응답에서 사용된 인용 소스 ({len(unique_citations)}개): {citation_str}")
            
            # 메모리에 대화 추가
            self.memory.chat_memory.add_user_message(query)
            self.memory.chat_memory.add_ai_message(full_response)
            
            print(f"[STREAM] 응답 생성 완료, 총 길이: {len(full_response)}자")
            print(f"[STREAM] ===== 스트리밍 응답 생성 종료 =====")
            
            return full_response
        except Exception as e:
            error_message = f"응답 생성 중 오류가 발생했습니다: {str(e)}"
            print(f"[STREAM-ERROR] {error_message}")
            import traceback
            print(f"[STREAM-ERROR] 상세 오류: {traceback.format_exc()}")
            message_placeholder.markdown(error_message)
            return error_message

    def stream_report(self, topic: str, sections_json: str, report_placeholder) -> str:
        """
        스트리밍 방식으로 보고서 생성
        
        Args:
            topic (str): 보고서 주제
            sections_json (str): 보고서 섹션 (JSON 형식 문자열)
            report_placeholder: Streamlit 보고서 플레이스홀더
            
        Returns:
            str: 생성된 보고서
        """
        try:
            print(f"[REPORT] ===== 스트리밍 보고서 생성 시작 =====")
            print(f"[REPORT] 보고서 주제: {topic}")
            print(f"[REPORT] 섹션 JSON: {sections_json}")
            
            # 섹션 파싱
            print(f"[REPORT] 섹션 파싱 시작")
            try:
                # 1. JSON 문자열을 리스트로 변환 시도
                sections = json.loads(sections_json)
                print(f"[REPORT] 섹션 JSON 파싱 성공: {len(sections)}개 섹션 - {sections}")
            except:
                try:
                    # 2. 쉼표로 구분된 문자열로 처리 시도
                    if isinstance(sections_json, str) and ',' in sections_json:
                        sections = [s.strip() for s in sections_json.split(',') if s.strip()]
                        print(f"[REPORT] 섹션 쉼표 구분 파싱 성공: {len(sections)}개 섹션 - {sections}")
                    else:
                        # 3. 단일 문자열인 경우 리스트로 변환
                        sections = [sections_json.strip()] if sections_json.strip() else DEFAULT_REPORT_SECTIONS
                        print(f"[REPORT] 섹션 단일 문자열 처리: {sections}")
                except:
                    # 4. 모든 파싱 실패 시 기본 섹션 사용
                    print(f"[REPORT] 모든 섹션 파싱 실패, 기본 섹션 사용")
                    sections = DEFAULT_REPORT_SECTIONS
                    print(f"[REPORT] 기본 섹션 적용: {sections}")
            
            # 섹션이 비어있거나 잘못된 경우 기본 섹션 사용
            if not sections or not isinstance(sections, list) or len(sections) == 0:
                print(f"[REPORT] 섹션이 비어있거나 잘못됨, 기본 섹션 사용")
                sections = DEFAULT_REPORT_SECTIONS
            
            # 섹션 텍스트 생성 - 마크다운 형식으로 명확하게 변경
            sections_text = "\n".join([f"## {section}" for section in sections])
            print(f"[REPORT] 섹션 텍스트 생성 완료")
            
            # 관련 문서 검색 (검색 결과 수 증가: 기본 5개 → 20개)
            print(f"[REPORT] 벡터 DB에서 관련 문서 검색 시작")
            docs = []
            docs_with_scores = []
            
            if self.vectorstore:
                print(f"[REPORT] 검색 파라미터 - 주제: '{topic}', 인덱스: {self.index_name}, k=20")
                docs_with_scores = self.embedding_manager.similarity_search(
                    topic, k=20, index_name=self.index_name)
                if docs_with_scores:
                    docs = [doc for doc, _ in docs_with_scores]
                    print(f"[REPORT] 검색 결과: {len(docs)}개 문서 발견")
                    
                    # 검색 결과 샘플 로깅 (상위 5개)
                    for i, (doc, score) in enumerate(docs_with_scores[:5]):
                        doc_preview = doc.page_content[:100] + "..." if len(doc.page_content) > 100 else doc.page_content
                        source = doc.metadata.get('filename', doc.metadata.get('source', f'문서{i+1}'))
                        print(f"[REPORT] 상위 문서 {i+1} (유사도: {score:.4f}): '{source}' - {doc_preview}")
                else:
                    print(f"[REPORT] 검색 결과: 문서 없음")
            else:
                print(f"[REPORT] 경고: 벡터 DB가 로드되지 않음")
            
            # 검색 결과 없을 경우
            if not docs:
                error_message = f"'{topic}' 주제에 관한 정보를 찾을 수 없습니다."
                print(f"[REPORT] 오류: {error_message}")
                report_placeholder.markdown(error_message)
                return error_message
            
            # 문서 참조 정보를 저장할 사전
            print(f"[REPORT] 문서 참조 정보 처리 시작")
            doc_references = {}
            context_summary = ""

            # 1. 일반 문서 처리 - 파일명 정보 포함하도록 수정 및 강화
            print(f"[REPORT] 일반 문서 {len(docs)}개 처리 시작")
            for i, doc in enumerate(docs):
                # 문서 메타데이터에서 파일명 가져오는 로직 강화
                filename = None
                metadata = doc.metadata if hasattr(doc, 'metadata') else {}
                
                print(f"[REPORT] 문서 {i+1} 메타데이터 처리 중: {list(metadata.keys())}")
                
                # 1. 직접 filename 키 확인
                if metadata.get('filename'):
                    filename = metadata.get('filename')
                    print(f"[REPORT] 문서 {i+1} filename 직접 발견: {filename}")
                # 2. 소스 경로에서 파일명 추출
                elif metadata.get('source'):
                    source_path = metadata.get('source')
                    if isinstance(source_path, str) and source_path:
                        filename = os.path.basename(source_path)
                        print(f"[REPORT] 문서 {i+1} 소스 경로에서 추출: {filename}")
                # 3. 제목 확인
                elif metadata.get('title'):
                    filename = metadata.get('title')
                    print(f"[REPORT] 문서 {i+1} 제목 사용: {filename}")
                # 4. 그래도 없으면 기본값
                if not filename or filename == "알 수 없는 파일":
                    filename = f"문서{i+1}"
                    print(f"[REPORT] 문서 {i+1} 기본값 사용: {filename}")
                
                # 같은 파일명이 있는 경우 번호 부여
                base_filename = filename
                counter = 1
                while filename in doc_references:
                    counter += 1
                    # 확장자가 있는 경우와 없는 경우 처리
                    if '.' in base_filename:
                        name_part, ext_part = base_filename.rsplit('.', 1)
                        filename = f"{name_part}_{counter}.{ext_part}"
                    else:
                        filename = f"{base_filename}_{counter}"
                    print(f"[REPORT] 문서 {i+1} 중복 방지 이름 변경: {filename}")
                
                # 문서 참조 목록에 추가 - 실제 파일명으로 저장
                doc_references[filename] = {
                    "index": i,
                    "type": "document",
                    "metadata": metadata
                }
                
                # 문서 내용 추가 - 파일명을 명확하게 표시
                context_summary += f"문서 '{filename}':\n{doc.page_content}\n\n"
                
                if (i + 1) % 5 == 0:  # 5개마다 진행상황 로깅
                    print(f"[REPORT] 일반 문서 처리 진행: {i+1}/{len(docs)}개 완료")
            
            print(f"[REPORT] 일반 문서 처리 완료: 총 {len(doc_references)}개 문서 참조 생성")
            
            # 2. 온톨로지 정보 처리 - 구체적인 명칭 사용
            print(f"[REPORT] 온톨로지 정보 조회 시작")
            ontology_info, doc_references, stats = self._search_ontology_detailed(topic, doc_references)
            
            # 온톨로지 정보가 있으면 추가
            if ontology_info:
                print(f"[REPORT] 유효한 온톨로지 정보 발견 (길이: {len(ontology_info)}자)")
                context_summary += ontology_info
                
                # 온톨로지에서 추가된 참조 개수 계산
                ontology_ref_count = sum(1 for ref_data in doc_references.values() 
                                       if ref_data.get('type', '').startswith('ontology'))
                print(f"[REPORT] 온톨로지 참조 {ontology_ref_count}개 추가됨")
            else:
                print(f"[REPORT] 관련 온톨로지 정보 없음")
            
            # 파일명 참조 목록 생성 - 명확하고 구조화된 형태로
            print(f"[REPORT] 문서 참조 목록 생성 시작")
            reference_list = []
            document_refs = 0
            ontology_refs = 0
            
            for ref_name, ref_data in doc_references.items():
                ref_type = ref_data.get("type", "unknown")
                if ref_type == "document":
                    ref_desc = f"일반 문서: {ref_name}"
                    document_refs += 1
                elif ref_type == "ontology_relation":
                    rel = ref_data.get("relation", {})
                    ref_desc = f"온톨로지 관계: {rel.get('subject', '')} {rel.get('relation', '')} {rel.get('object', '')}"
                    ontology_refs += 1
                elif ref_type == "ontology_entity":
                    ref_desc = f"온톨로지 엔티티: {ref_data.get('entity', '')} (유형: {ref_data.get('entity_type', '')})"
                    ontology_refs += 1
                elif ref_type == "ontology_entity_list":
                    ref_desc = f"온톨로지 엔티티 목록: {ref_data.get('entity_type', '')}"
                    ontology_refs += 1
                else:
                    ref_desc = "기타 참조"
                
                reference_list.append(f"- '{ref_name}': {ref_desc}")
            
            print(f"[REPORT] 참조 목록 생성 완료: 총 {len(reference_list)}개 ({document_refs}개 문서 + {ontology_refs}개 온톨로지)")
            
            file_reference_guide = "## 문서 참조 목록\n" + "\n".join(reference_list) + "\n\n"
            
            # 프롬프트 생성 - 참조 방식에 대한 명확한 지침
            print(f"[REPORT] 프롬프트 생성 시작")
            raw_prompt = f"""
            주제: {topic}

            ⚠️ 중요: 아래에 제공된 정확한 섹션 구조를 그대로 사용해야 합니다. 섹션 제목이나 순서를 절대 변경하지 마세요!

            === 사용해야 할 섹션 구조 ===
            {sections_text}
            === 섹션 구조 끝 ===

            {file_reference_guide}

            참고 정보:
            {context_summary}

            ⚠️ 매우 중요한 섹션 규칙:
            - 위에 제공된 섹션 구조를 100% 그대로 따라야 합니다
            - 섹션 제목을 임의로 변경하거나 새로운 섹션을 추가하지 마세요
            - 예를 들어 "## 1. 개요"가 제공되었으면 "## 개요" 또는 "## 1. 배경"으로 바꾸지 마세요
            - 각 섹션은 정확히 제공된 마크다운 헤딩(## 섹션명)으로 시작해야 합니다

            필수 요구사항:
            1. 제공된 섹션 구조를 그대로 따라야 합니다 (순서나 제목 변경 금지)
            2. 각 섹션은 이미 '##' 마크다운 형식으로 제공되었으니 그대로 사용하세요
            3. 각 섹션에서는 단순 사실 나열이 아닌 심층 통찰(원인-결과 분석, 이해관계자 영향 등)을 제공하세요
            4. 주장을 뒷받침하기 위해 데이터와 통계를 사용하세요
            5. 수치 정보는 표로 정리하세요
            6. 중요 - 인용 요구사항:
               - 문서 인용 시 반드시 제공된 참조 목록에 있는 정확한 문서명을 사용해야 합니다
               - 올바른 인용 예시: "'배터리_제조공정.pdf' 문서에 따르면..." 또는 "'설비_탈철기' 문서에 의하면..."
               - 잘못된 인용 예시: "문서_3에 따르면..." 또는 "ontology_4에 의하면..."
               - 절대로 '문서_1', '문서_2', 'ontology_3' 등과 같은 일반적인 번호 형식으로 인용하지 마세요
               - 항상 완전한 참조명을 사용하세요(예: '온톨로지_Entity_Type', '금속이물_caused_by_탈철기' 등)
            7. 주제의 언어를 감지하여 해당 언어로 보고서를 작성하세요. 영어 주제면 영어로, 한국어 주제면 한국어로 작성하세요.
            """
            
            print(f"[REPORT] 프롬프트 길이: {len(raw_prompt)}자")
            print(f"[REPORT] 컨텍스트 요약 길이: {len(context_summary)}자")
            
            # 스트리밍 응답 생성
            print(f"[REPORT] 보고서 헤더 생성")
            full_report = f"# {topic} 심층 분석 보고서\n\n"
            
            # 시스템 메시지 추가 - 문서 참조 관련 강력한 지침
            print(f"[REPORT] 시스템 프롬프트 설정")
            from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate
            
            system_template = """당신은 정확한 섹션 구조를 따라 심층 분석 보고서를 작성하는 전문가입니다.

🚨 절대적인 섹션 규칙:
- 사용자가 제공한 섹션 구조를 100% 정확히 따라야 합니다
- 섹션 제목을 단 한 글자도 변경하지 마세요
- 섹션 순서를 바꾸지 마세요
- 새로운 섹션을 추가하거나 기존 섹션을 생략하지 마세요
- 예: "## 1. 개요"가 주어지면 반드시 "## 1. 개요"로 시작하세요
- 예: "## 2. 기록"이 주어지면 반드시 "## 2. 기록"으로 시작하세요
- 절대로 "## 개요", "## 배경", "## 이슈 분석" 등으로 임의 변경하지 마세요

매우 중요한 인용 요구사항: 
- 출처 인용 시 반드시 제공된 정확한 파일명을 사용해야 합니다
- 절대로 일반적인 번호로 출처를 인용하지 마세요 (예: 'document_1', 'document_3')
- 절대로 일반적인 접두어로 출처를 인용하지 마세요 (예: '문서_1', '문서_2', 'ontology_3', 'ontology_4')
- 올바른 인용 형식: "'battery_report_2023.pdf'에 따르면" 또는 "'탈철기_caused_by_금속이물'에 의하면"
- 참조 목록에 제공된 정확한 문서명을 사용하세요
- 모든 사실은 적절한 문서명으로 인용되어야 합니다
- 인용은 따옴표로 묶인 전체 파일명을 사용해야 합니다 (예: '설비_탈철기')

주제의 언어를 감지하여 해당 언어로 보고서를 작성하세요. 영어 주제면 영어로, 한국어 주제면 한국어로 작성하세요."""
            system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)
            
            human_message_prompt = HumanMessagePromptTemplate.from_template("{raw_prompt}")
            
            chat_prompt = ChatPromptTemplate.from_messages([
                system_message_prompt,
                human_message_prompt
            ])
            
            # LLM temperature 설정
            original_temperature = self.streaming_llm.temperature if hasattr(self.streaming_llm, 'temperature') else None
            if hasattr(self.streaming_llm, 'temperature'):
                self.streaming_llm.temperature = 0.1  # 보고서는 더 정확성을 위해 낮은 temperature
                print(f"[REPORT] LLM temperature 조정: {original_temperature} -> 0.1")
            
            chain = chat_prompt | self.streaming_llm
            
            # 보고서 스트리밍
            print(f"[REPORT] 스트리밍 보고서 생성 시작")
            token_count = 0
            
            for chunk in chain.stream({"raw_prompt": raw_prompt}):
                content = chunk.content if hasattr(chunk, 'content') else str(chunk)
                full_report += content
                token_count += 1
                report_placeholder.markdown(full_report + "▌")
                
                # 진행 상황 로깅 (매 100자마다)
                if len(full_report) % 100 == 0:
                    print(f"[REPORT] 보고서 생성 중... ({len(full_report)}자)")
            
            # 원래 temperature 복원
            if original_temperature is not None and hasattr(self.streaming_llm, 'temperature'):
                self.streaming_llm.temperature = original_temperature
                print(f"[REPORT] LLM temperature 복원: 0.1 -> {original_temperature}")
            
            # 보고서 마무리
            print(f"[REPORT] 보고서 마무리 작업")
            full_report += f"\n\n---\n*이 심층 분석 보고서는 DX-AI Advisor에 의해 자동 생성되었습니다.*\n*생성 날짜: {datetime.now().strftime('%Y-%m-%d')}*"
            
            # 최종 보고서 표시 (커서 제거)
            report_placeholder.markdown(full_report)
            
            # 보고서에서 인용 분석
            print(f"[REPORT] 인용 분석 시작")
            citations_used = []
            citation_pattern = r"['\"]([^'\"]+)['\"]에 따르면|['\"]([^'\"]+)['\"] 문서에 따르면|According to ['\"]([^'\"]+)['\"]"
            citation_matches = re.finditer(citation_pattern, full_report, re.IGNORECASE)
            
            for match in citation_matches:
                if match.group(1):  # "에 따르면" 패턴
                    citations_used.append(match.group(1))
                elif match.group(2):  # "문서에 따르면" 패턴
                    citations_used.append(match.group(2))
                elif match.group(3):  # "According to" 패턴
                    citations_used.append(match.group(3))
            
            # 중복 제거
            unique_citations = list(set(citations_used))
            citation_str = ", ".join(["'" + c + "'" for c in unique_citations])
            print(f"[REPORT] 보고서에서 사용된 인용 소스 ({len(unique_citations)}개): {citation_str}")
            
            # 문서 타입별 인용 분석
            document_citations = 0
            ontology_citations = 0
            for citation in unique_citations:
                if any(citation == ref_name for ref_name, ref_data in doc_references.items() 
                      if ref_data.get('type') == 'document'):
                    document_citations += 1
                elif any(citation == ref_name for ref_name, ref_data in doc_references.items() 
                        if ref_data.get('type', '').startswith('ontology')):
                    ontology_citations += 1
            
            print(f"[REPORT] 인용 분석: 문서 {document_citations}개, 온톨로지 {ontology_citations}개")
            print(f"[REPORT] 최종 보고서 길이: {len(full_report)}자")
            print(f"[REPORT] ===== 스트리밍 보고서 생성 종료 =====")
            
            return full_report
        except Exception as e:
            error_message = f"보고서 생성 중 오류가 발생했습니다: {str(e)}"
            print(f"[REPORT-ERROR] {error_message}")
            import traceback
            print(f"[REPORT-ERROR] 상세 오류: {traceback.format_exc()}")
            report_placeholder.markdown(error_message)
            return error_message


def main():
    """테스트용 메인 함수"""
    agent = AdvisorAgent()
    
    # 테스트 쿼리 실행
    test_queries = [
        "미국의 중국산 전기차 관세 정책에 대해 알려주세요.",
        "관세 정책이 한국 배터리 산업에 미치는 영향은 무엇인가요?",
        "중국과 미국 간 무역 분쟁의 최근 상황을 요약해주세요.",
        "배터리 산업에 대한 분석 보고서를 생성해주세요."
    ]
    
    for query in test_queries:
        print(f"\n{'='*50}")
        print(f"사용자 질의: {query}")
        print(f"{'='*50}")
        response = agent.run(query)
        print(f"에이전트 응답: {response}")

if __name__ == "__main__":
    main() 