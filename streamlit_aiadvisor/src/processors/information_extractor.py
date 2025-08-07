"""
문서 내용에서 주요 정보를 추출하는 모듈
"""
import json
import re
import traceback
from typing import List, Dict, Any, Optional
import os

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_ollama import OllamaLLM
from langchain.schema import HumanMessage, SystemMessage, AIMessage

from src.utils.config import DEFAULT_LLM_MODEL, LLM_TIMEOUT

class InformationExtractor:
    """문서에서 주요 정보 추출 클래스"""
    
    def __init__(self, model_name: str = DEFAULT_LLM_MODEL):
        """
        정보 추출기 초기화
        
        Args:
            model_name (str): 사용할 LLM 모델 이름
        """
        self.model_name = model_name
        self.llm = OllamaLLM(
            model=model_name,
            temperature=0.1,
            top_p=0.9, 
            top_k=40,
            repeat_penalty=1.1,
            # num_ctx=4096,
            timeout=LLM_TIMEOUT,  # 타임아웃 설정
        )
        self.json_parser = JsonOutputParser()
    
    def _extract_json_from_text(self, text: str) -> Dict[str, Any]:
        """
        텍스트에서 JSON 부분을 추출
        
        Args:
            text (str): LLM 응답 텍스트
            
        Returns:
            Dict[str, Any]: 추출된 JSON 데이터
        """
        if not text:
            print("응답 텍스트가 비어 있습니다.")
            return {}
            
        print(f"JSON 추출 시도. 텍스트 길이: {len(text)}")
        print(f"원본 텍스트 시작 부분: {text[:100].replace(chr(10), ' ')}...")
        
        # 추출 시도 방법 여러 개 시도
        json_result = {}
        
        # 1. JSON 블록 추출 시도 (```json 패턴)
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', text)
        if json_match:
            json_str = json_match.group(1).strip()
            try:
                json_result = json.loads(json_str)
                print(f"```json 패턴으로 JSON 추출 성공: {list(json_result.keys())}")
                return json_result
            except json.JSONDecodeError as e:
                print(f"```json 패턴에서 JSON 디코드 오류: {e}")
        
        # 2. 중괄호로 둘러싸인 부분 추출 시도
        json_match = re.search(r'({[\s\S]*?})', text)
        if json_match:
            json_str = json_match.group(1).strip()
            json_str = self._clean_json_string(json_str)
            try:
                json_result = json.loads(json_str)
                print(f"중괄호 패턴으로 JSON 추출 성공: {list(json_result.keys())}")
                return json_result
            except json.JSONDecodeError as e:
                print(f"중괄호 패턴에서 JSON 디코드 오류: {e}")
        
        # 3. 키-값 패턴 찾아서 JSON 구성하기
        try:
            properties = {}
            # 문자열 값 패턴
            string_matches = re.findall(r'"([^"]+)":\s*"([^"]*)"', text)
            for key, value in string_matches:
                properties[key] = value
            
            # 배열 값 패턴
            array_matches = re.findall(r'"([^"]+)":\s*\[(.*?)\]', text)
            for key, value in array_matches:
                items = re.findall(r'"([^"]*)"', value)
                if items:
                    properties[key] = items
            
            # 숫자 값 패턴
            number_matches = re.findall(r'"([^"]+)":\s*(\d+)', text)
            for key, value in number_matches:
                if key not in properties:  # 이미 처리된 키는 건너뛰기
                    properties[key] = int(value)
            
            # 불리언/널 값 패턴
            bool_matches = re.findall(r'"([^"]+)":\s*(true|false|null)', text, re.IGNORECASE)
            for key, value in bool_matches:
                if key not in properties:  # 이미 처리된 키는 건너뛰기
                    if value.lower() == 'true':
                        properties[key] = True
                    elif value.lower() == 'false':
                        properties[key] = False
                    else:  # null
                        properties[key] = None
            
            if properties:
                print(f"키-값 패턴으로 JSON 구성 성공: {list(properties.keys())}")
                return properties
        except Exception as e:
            print(f"키-값 패턴 추출 중 오류: {e}")
        
        # 4. 마지막 시도: 수동 파싱
        try:
            manual_result = self._manual_json_parsing(text)
            if manual_result:
                print(f"수동 파싱으로 JSON 추출 성공: {list(manual_result.keys())}")
                return manual_result
        except Exception as e:
            print(f"수동 파싱 중 오류: {e}")
        
        print("모든 JSON 추출 방법이 실패했습니다.")
        return {}
    
    def _clean_json_string(self, json_str: str) -> str:
        """JSON 문자열을 정리하는 도우미 함수"""
        # 줄바꿈과 탭 제거
        cleaned = re.sub(r'[\n\r\t]', ' ', json_str)
        # 중복 공백 제거
        cleaned = re.sub(r'\s+', ' ', cleaned)
        # 이스케이프 문자 처리
        cleaned = cleaned.replace('\\"', '"').replace("\\'", "'")
        # 불필요한 콤마 제거
        cleaned = re.sub(r',\s*}', '}', cleaned)
        cleaned = re.sub(r',\s*]', ']', cleaned)
        # 잘못된 콤마 추가
        cleaned = re.sub(r'}\s*{', '},{', cleaned)
        cleaned = re.sub(r']\s*\[', '],[', cleaned)
        return cleaned
    
    def _manual_json_parsing(self, json_str: str) -> Dict[str, Any]:
        """JSON 문자열을 수동으로 파싱하는 함수"""
        properties = {}
        
        # 1. 각 필드 추출 시도
        # "필드명": "값" 패턴
        string_pattern = r'"([^"]+)"\s*:\s*"([^"]*)"'
        for key, value in re.findall(string_pattern, json_str):
            properties[key] = value
        
        # "필드명": [배열] 패턴
        array_pattern = r'"([^"]+)"\s*:\s*\[(.*?)\]'
        for key, array_content in re.findall(array_pattern, json_str):
            # 배열 내 항목 추출
            items = []
            # 문자열 항목
            string_items = re.findall(r'"([^"]*)"', array_content)
            if string_items:
                items = string_items
            # 객체 항목 (간단한 객체만 처리)
            elif '{' in array_content:
                obj_pattern = r'{([^{}]*?)}'
                for obj_match in re.findall(obj_pattern, array_content):
                    obj_dict = {}
                    # 객체 내 키-값 추출
                    for obj_key, obj_value in re.findall(string_pattern, '{' + obj_match + '}'):
                        obj_dict[obj_key] = obj_value
                    if obj_dict:
                        items.append(obj_dict)
            
            properties[key] = items
        
        # "필드명": 숫자 패턴
        number_pattern = r'"([^"]+)"\s*:\s*(\d+)'
        for key, value in re.findall(number_pattern, json_str):
            if key not in properties:  # 이미 처리된 키는 건너뛰기
                properties[key] = int(value)
        
        # "필드명": true/false/null 패턴
        bool_pattern = r'"([^"]+)"\s*:\s*(true|false|null)'
        for key, value in re.findall(bool_pattern, json_str, re.IGNORECASE):
            if key not in properties:  # 이미 처리된 키는 건너뛰기
                if value.lower() == 'true':
                    properties[key] = True
                elif value.lower() == 'false':
                    properties[key] = False
                else:
                    properties[key] = None
        
        return properties
    
    def _prepare_document_summary(self, document: Dict[str, Any]) -> str:
        """
        문서 요약을 준비
        
        Args:
            document (Dict[str, Any]): 파싱된 문서
            
        Returns:
            str: 요약을 위한 문서 내용
        """
        content_items = document.get("content", [])
        
        # 내용 길이 제한 (토큰 제한 고려)
        max_items = 10
        max_length_per_item = 1000
        
        content_text = ""
        for i, item in enumerate(content_items):
            if i >= max_items:
                break
            
            if len(item) > max_length_per_item:
                item = item[:max_length_per_item] + "..."
            
            content_text += f"\n--- 내용 부분 {i+1} ---\n{item}"
        
        filename = document.get("filename", "알 수 없는 파일")
        return f"파일명: {filename}\n\n{content_text}"
    
    def extract_metadata(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        문서에서 메타데이터 추출
        
        Args:
            document (Dict[str, Any]): 파싱된 문서
            
        Returns:
            Dict[str, Any]: 추출된 메타데이터
        """
        # 기본 메타데이터 구성 (실패 시 폴백용)
        default_metadata = {
            "filename": document.get("filename", "알 수 없는 제목"),
            "file_path": document.get("file_path", ""),
            "title": document.get("filename", "알 수 없는 제목"),
            "date": document.get("modified_date", None),
            "keywords": [],
            "summary": "메타데이터 추출 실패",
            "topics": []
        }
        
        try:
            document_summary = self._prepare_document_summary(document)
            
            prompt_template = ChatPromptTemplate.from_messages([
                (
                    "system", 
                    """당신은 제조 공정 및 품질 관련 문서에서 메타데이터를 추출하는 전문가입니다. 
                    주어진 문서 내용을 분석하여 다음 정보를 JSON 형식으로 추출해주세요:
                    
                    - title: 문서의 제목 (가능한 정확하게, 제품명, 공정명, 이슈 타입 등 포함)
                    - date: 작성일 또는 이슈 발생일 (YYYY-MM-DD 형식, 알 수 없는 경우 "")
                    - keywords: 주요 키워드 목록 (제품명, 설비명, 이슈명, 화학물질명 등 10개 내외)
                    - summary: 200~250자 내외의 요약 (문제 현상, 원인, 조치사항 등 포함)
                    - topics: 다루고 있는 주요 주제 카테고리 (5개 내외)
                    
                    주요 주제 카테고리 예시:
                    - 품질 관리
                    - 설비 점검
                    - 공정 개선
                    - 문제 분석
                    - 원인 규명
                    - 유지보수
                    - 원자재 관리
                    - 이물 검출
                    - 생산성 향상
                    - 안전 관리
                    
                    누락된 정보가 있으면 빈 문자열이나 빈 배열로 표시하지 말고 
                    가능한 한 문서 내용에서 추론하여 채워주세요.
                    
                    반드시 유효한 JSON 형식으로 응답해주세요. 코드 블록이나 설명 없이 JSON만 반환하세요.
                    
                    예시 형식:
                    {{
                      "title": "CAM5 2Line 탈철기 자성이물 검출 증가 Issue",
                      "date": "2023-04-15",
                      "keywords": ["탈철기", "자성이물", "Matrix", "ICP", "2Line", "품질이슈", "Fe", "탈철효율", "설비점검", "영구자석"],
                      "summary": "CAM5 2Line 탈철기에서 자성이물 검출량이 증가하는 현상이 발생했습니다. 원인 분석 결과, Matrix 고정 상부 너트 채결 상태 이상으로 인한 것으로 확인되었으며, Matrix 교체 및 점검 주기 변경 등의 조치가 취해졌습니다. ICP 분석 결과 Fe 함량이 정상범위로 회복되었습니다.",
                      "topics": ["품질 관리", "설비 점검", "이물 검출", "원인 분석", "개선 조치"]
                    }}
                    """
                ),
                ("human", "{document}")
            ])
            
            # LLM에게 요청
            print(f"메타데이터 추출 시작: {document.get('filename', '알 수 없는 파일')}")
            result_text = self.llm.invoke(prompt_template.format(document=document_summary))
            
            # 결과 텍스트에서 JSON 추출
            # OllamaLLM은 string을 직접 반환함
            if hasattr(result_text, 'content'):
                # LangChain 호환성을 위한 처리
                text_to_parse = result_text.content
            else:
                # OllamaLLM은 string 직접 반환
                text_to_parse = result_text
                
            result = self._extract_json_from_text(text_to_parse)
            
            if not result:
                print(f"JSON 파싱 실패, 기본 메타데이터 사용: {document.get('filename', '')}")
                return default_metadata
            
            # 필수 필드 확인 및 보완
            for key in ["title", "date", "keywords", "summary", "topics"]:
                if key not in result or result[key] is None:
                    result[key] = default_metadata.get(key, "")
                    
            # 배열 타입 확인
            for key in ["keywords", "topics"]:
                if not isinstance(result[key], list):
                    result[key] = []
            
            # 파일명 정보 추가
            result["filename"] = document.get("filename", "")
            result["file_path"] = document.get("file_path", "")
            
            print(f"메타데이터 추출 성공: {result.get('title', '')}")
            return result
            
        except Exception as e:
            error_msg = str(e)
            print(f"메타데이터 추출 중 오류 발생: {error_msg}")
            print(traceback.format_exc())
            
            # 오류 발생 시 기본 메타데이터 반환
            return default_metadata
    
    def extract_ontology_relations(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        문서에서 온톨로지 관계를 추출
        
        Args:
            document (Dict[str, Any]): 파싱된 문서
            
        Returns:
            Dict[str, Any]: 추출된 온톨로지 관계
        """
        # 기본 온톨로지 구성 (실패 시 폴백용)
        default_ontology = {
            "filename": document.get("filename", ""),
            "entities": [],
            "relations": []
        }
        
        try:
            document_summary = self._prepare_document_summary(document)
            
            prompt_template = ChatPromptTemplate.from_messages([
                (
                    "system", 
                    """당신은 제조 공정 및 품질 문서 내용에서 온톨로지 관계를 추출하는 전문가입니다.
                    주어진 문서를 분석하여 등장하는 엔티티들과 그들 간의 관계를 파악해주세요.
                    
                    특히 다음과 같은 엔티티 유형에 주목해주세요:
                    - 설비/장비: 탈철기, 분급기, 믹서, 피더, 밸브, 배관, 메쉬, 필터, 센서 등
                    - 공정/프로세스: 소성, 이송, 분급, 수세, 포장, 계량, 청소 등
                    - 제품/자재: 양극재, 도펀트, 전구체, 소성품, 최종품, 이송품, 배치, 로트 등
                    - 화학물질: 리튬, 알루미늄, 지르코늄, 니켈, 망간, 코발트 등
                    - 품질 이슈: 불량, NG, 이물, 파손, 마모, 누출, 막힘, 부적합, 편차 등
                    - 측정/분석: ICP, XRF, BET, 입도, 조성, 샘플링, 테스트 등
                    
                    다음 관계 유형을 사용할 수 있습니다:
                    
                    기본 관계:
                    - related: 일반적인 관련성
                    - include: 포함 관계 (컴포넌트/부품)
                    - contains: 포함 관계 (물질/성분)
                    - belongs_to: 소속 관계
                    
                    인과 관계:
                    - caused_by: 원인-결과 관계 (문제 원인)
                    - resulted_in: 결과 관계 (문제 결과)
                    - affected_by: 영향 관계
                    - contributes_to: 기여 관계
                    
                    제조/설비 관계:
                    - manufactured_by: 제조 관계
                    - supply_to: 공급 관계
                    - receive_from: 수신 관계
                    - used_in: 사용 관계 (장비/도구)
                    - part_of: 부분-전체 관계 (장비 구성)
                    - connected_to: 연결 관계 (배관/장비)
                    - measured_by: 측정 관계 (센서/계측기)
                    - feeds_into: 투입 관계
                    
                    품질/문제 관계:
                    - detected_in: 불량 발견 관계
                    - improved_by: 개선 관계
                    - failed_due_to: 고장 원인 관계
                    - contaminated_by: 오염 관계
                    - causes_defect: 불량 유발 관계
                    - exceeds_limit: 한계치 초과 관계
                    - regulated_by: 규제 관계
                    
                    반드시 유효한 JSON 형식으로 응답해주세요. 코드 블록이나 설명 없이 JSON만 반환하세요.
                    
                    예시 형식:
                    {{
                      "entities": ["분급기", "메쉬", "자성이물", "ICP", "최종품", "탈철기"],
                      "relations": [
                        {{"source": "자성이물", "relation": "detected_in", "target": "최종품"}},
                        {{"source": "분급기", "relation": "used_in", "target": "메쉬"}},
                        {{"source": "자성이물", "relation": "caused_by", "target": "탈철기"}},
                        {{"source": "ICP", "relation": "measured_by", "target": "자성이물"}}
                      ]
                    }}
                    
                    문서 내용을 깊이 있게 분석하여 최소 5개 이상의 의미 있는 관계를 추출해주세요.
                    특히 제조 공정, 설비 사이의 관계, 품질 문제의 원인-결과 관계에 집중해주세요.
                    """
                ),
                ("human", "{document}")
            ])
            
            # LLM에게 요청
            print(f"온톨로지 관계 추출 시작: {document.get('filename', '알 수 없는 파일')}")
            result_text = self.llm.invoke(prompt_template.format(document=document_summary))
            
            # 결과 텍스트에서 JSON 추출
            # OllamaLLM은 string을 직접 반환함
            if hasattr(result_text, 'content'):
                # LangChain 호환성을 위한 처리
                text_to_parse = result_text.content
            else:
                # OllamaLLM은 string 직접 반환
                text_to_parse = result_text
                
            result = self._extract_json_from_text(text_to_parse)
            
            if not result:
                print(f"온톨로지 JSON 파싱 실패, 기본값 사용: {document.get('filename', '')}")
                return default_ontology
            
            # 필수 필드 확인
            if "entities" not in result or not isinstance(result["entities"], list):
                result["entities"] = []
                
            if "relations" not in result or not isinstance(result["relations"], list):
                result["relations"] = []
                
            # 관계 형식 검증
            valid_relations = []
            for rel in result.get("relations", []):
                if isinstance(rel, dict) and "source" in rel and "relation" in rel and "target" in rel:
                    valid_relations.append(rel)
            
            result["relations"] = valid_relations
            
            # 파일명 정보 추가
            result["filename"] = document.get("filename", "")
            
            print(f"온톨로지 관계 추출 성공: {len(result.get('entities', []))} 엔티티, {len(result.get('relations', []))} 관계")
            return result
            
        except Exception as e:
            print(f"온톨로지 관계 추출 중 오류 발생: {str(e)}")
            print(traceback.format_exc())
            
            return default_ontology
    
    def extract_structured_data(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        문서에서 구조화된 데이터 추출 (테이블, 목록 등)
        
        Args:
            document (Dict[str, Any]): 파싱된 문서
            
        Returns:
            Dict[str, Any]: 추출된 구조화 데이터
        """
        # 기본 구조화 데이터 (실패 시 폴백용)
        default_structured = {
            "filename": document.get("filename", ""),
            "tables": [],
            "lists": [],
            "statistics": [],
            "timeline": []
        }
        
        try:
            document_summary = self._prepare_document_summary(document)
            
            prompt_template = ChatPromptTemplate.from_messages([
                (
                    "system", 
                    """당신은 제조 공정 및 품질 관련 문서에서 구조화된 데이터를 추출하는 전문가입니다.
                    주어진 문서 내용을 분석하여 표, 목록, 수치 데이터 등을 추출해주세요.
                    
                    특히 다음과 같은 정보에 집중해주세요:
                    - 설비 파라미터 및 측정값 (온도, 압력, 속도 등)
                    - 제품 품질 측정 결과 (ICP, XRF, BET, 입도 등)
                    - 공정별 불량률 및 통계 데이터
                    - 설비 점검 및 유지보수 기록
                    - 시간에 따른 품질 변화/추세
                    - 문제 발생 및 조치 이력
                    - LOT별 테스트 결과 및 측정값
                    - 설비 구성 요소 및 사양
                    
                    다음과 같은 구조로 데이터를 추출해주세요:
                    
                    반드시 유효한 JSON 형식으로 응답해주세요. 코드 블록이나 설명 없이 JSON만 반환하세요.
                    
                    예시 형식:
                    {{
                      "tables": [
                        {{
                          "title": "LOT별 ICP 측정 결과",
                          "headers": ["LOT No", "Fe (ppb)", "Cr (ppb)", "Zn (ppb)", "합계", "판정"],
                          "rows": [
                            ["P501LU1H-23010393", "0.9", "0.1", "0", "1.1", "OK"],
                            ["P501LU1H-23010415", "7.7", "0.8", "0", "8.5", "관리선 이탈"]
                          ]
                        }}
                      ],
                      "lists": [
                        {{
                          "title": "발생 원인",
                          "items": ["탈철기 Matrix 고정 상부 너트 채결 상태 이상", "배관 체류"]
                        }},
                        {{
                          "title": "개선 조치 사항",
                          "items": ["탈철기 점검 주기 변경", "Matrix 교체"]
                        }}
                      ],
                      "statistics": [
                        {{
                          "name": "불량 발생률",
                          "value": "3.9%",
                          "cycle": "1",
                          "date": "2023-01-26"
                        }},
                        {{
                          "name": "탈철기 온도",
                          "value": "25~26℃",
                          "unit": "℃",
                          "spec": "12~20℃"
                        }}
                      ],
                      "timeline": [
                        {{
                          "date": "2023-01-26",
                          "event": "최초 발생"
                        }},
                        {{
                          "date": "2023-02-01", 
                          "event": "싸이클론 청소 완료"
                        }}
                      ]
                    }}
                    
                    문서 내용에 근거하여 최대한 정확하고 상세한 정보를 추출해주세요.
                    특히 수치 데이터와 공정/품질 관련 구체적인 정보를 누락 없이 추출하는 것이 중요합니다.
                    """
                ),
                ("human", "{document}")
            ])
            
            # LLM에게 요청
            print(f"구조화 데이터 추출 시작: {document.get('filename', '알 수 없는 파일')}")
            result_text = self.llm.invoke(prompt_template.format(document=document_summary))
            
            # 결과 텍스트에서 JSON 추출
            # OllamaLLM은 string을 직접 반환함
            if hasattr(result_text, 'content'):
                # LangChain 호환성을 위한 처리
                text_to_parse = result_text.content
            else:
                # OllamaLLM은 string 직접 반환
                text_to_parse = result_text
                
            result = self._extract_json_from_text(text_to_parse)
            
            if not result:
                print(f"구조화 데이터 JSON 파싱 실패, 기본값 사용: {document.get('filename', '')}")
                return default_structured
            
            # 필수 필드 확인
            for key in ["tables", "lists", "statistics", "timeline"]:
                if key not in result or not isinstance(result[key], list):
                    result[key] = []
            
            # 각 필드 유효성 검증
            # 테이블 검증
            valid_tables = []
            for table in result.get("tables", []):
                if isinstance(table, dict) and "headers" in table and "rows" in table:
                    if isinstance(table["headers"], list) and isinstance(table["rows"], list):
                        valid_tables.append(table)
            result["tables"] = valid_tables
            
            # 목록 검증
            valid_lists = []
            for list_item in result.get("lists", []):
                if isinstance(list_item, dict) and "title" in list_item and "items" in list_item:
                    if isinstance(list_item["items"], list):
                        valid_lists.append(list_item)
            result["lists"] = valid_lists
            
            # 통계 검증
            valid_stats = []
            for stat in result.get("statistics", []):
                if isinstance(stat, dict) and "name" in stat and "value" in stat:
                    valid_stats.append(stat)
            result["statistics"] = valid_stats
            
            # 타임라인 검증
            valid_timeline = []
            for event in result.get("timeline", []):
                if isinstance(event, dict) and "date" in event and "event" in event:
                    valid_timeline.append(event)
            result["timeline"] = valid_timeline
                
            # 파일명 정보 추가
            result["filename"] = document.get("filename", "")
            
            print(f"구조화 데이터 추출 성공: 테이블 {len(result.get('tables', []))}, 목록 {len(result.get('lists', []))}, 통계 {len(result.get('statistics', []))}, 타임라인 {len(result.get('timeline', []))}")
            return result
            
        except Exception as e:
            print(f"구조화 데이터 추출 중 오류 발생: {str(e)}")
            print(traceback.format_exc())
            
            return default_structured
    
    def extract_full_content(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        문서의 전체 내용을 그대로 추출
        
        Args:
            document (Dict[str, Any]): 파싱된 문서
            
        Returns:
            Dict[str, Any]: 추출된 전체 내용
        """
        try:
            content_items = document.get("content", [])
            full_content = {
                "filename": document.get("filename", ""),
                "file_path": document.get("file_path", ""),
                "full_text": "\n\n".join(content_items),
                "content_items": content_items,
                "content_count": len(content_items)
            }
            print(f"전체 내용 추출 완료: {document.get('filename', '')} ({len(content_items)} 항목)")
            return full_content
        except Exception as e:
            print(f"전체 내용 추출 중 오류 발생: {str(e)}")
            return {
                "filename": document.get("filename", ""),
                "file_path": document.get("file_path", ""),
                "full_text": "",
                "content_items": [],
                "content_count": 0
            }
    
    def process_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        문서 전체 처리 (모든 추출 작업 수행)
        
        Args:
            document (Dict[str, Any]): 파싱된 문서
            
        Returns:
            Dict[str, Any]: 추출된 모든 정보
        """
        print(f"문서 '{document.get('filename', '')}' 처리 중...")
        
        result = {
            "metadata": self.extract_metadata(document),
            "ontology": self.extract_ontology_relations(document),
            "structured_data": self.extract_structured_data(document),
            "full_content": self.extract_full_content(document)  # 전체 내용 추가
        }
        
        return result
    
    def process_documents(self, documents: List[Dict[str, Any]], output_dir: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        여러 문서 일괄 처리
        
        Args:
            documents (List[Dict[str, Any]]): 파싱된 문서 목록
            output_dir (Optional[str]): 결과 저장 경로
            
        Returns:
            List[Dict[str, Any]]: 처리 결과 목록
        """
        results = []
        
        if not documents:
            print("처리할 문서가 없습니다. 빈 결과를 반환합니다.")
            return results
        
        print(f"총 {len(documents)}개 문서 처리 시작")
        
        for i, doc in enumerate(documents, 1):
            try:
                print(f"[{i}/{len(documents)}] '{doc.get('filename', 'unknown')}' 문서 처리 시작")
                
                if not doc or not isinstance(doc, dict):
                    print(f"잘못된 문서 형식: {type(doc)}. 건너뜁니다.")
                    continue
                
                if "content" not in doc or not doc["content"]:
                    print(f"문서 내용이 없습니다: {doc.get('filename', 'unknown')}. 건너뜁니다.")
                    continue
                
                # 문서의 기본 정보 구성
                file_info = {
                    "filename": doc.get("filename", "unknown"),
                    "file_path": doc.get("file_path", ""),
                    "file_extension": doc.get("file_extension", ""),
                    "file_size_kb": doc.get("file_size_kb", 0),
                    "modified_date": doc.get("modified_date", "")
                }
                
                # 실제 정보 추출 처리
                extraction_result = self.process_document(doc)
                
                # 파일 정보 추가
                extraction_result["file_info"] = file_info
                
                # 결과에 추가
                results.append(extraction_result)
                print(f"'{doc.get('filename', 'unknown')}' 문서 처리 완료")
                
                # 개별 결과 저장 (output_dir이 지정된 경우)
                if output_dir is not None:
                    os.makedirs(output_dir, exist_ok=True)
                    filename = file_info.get("filename", "unknown").split(".")[0]
                    output_path = os.path.join(output_dir, f"{filename}_extracted.json")
                    
                    with open(output_path, 'w', encoding='utf-8') as f:
                        json.dump(extraction_result, f, ensure_ascii=False, indent=2)
                    
                    print(f"결과 저장 완료: {output_path}")
                
            except Exception as e:
                print(f"문서 '{doc.get('filename', '')}' 처리 중 오류 발생: {str(e)}")
                import traceback
                print(traceback.format_exc())
        
        print(f"총 {len(results)}/{len(documents)} 문서 처리 완료")
        return results

def main():
    """테스트용 메인 함수"""
    from src.processors.document_parser import DocumentParser
    
    # 문서 파싱
    parser = DocumentParser()
    docs = parser.parse_directory()
    
    if not docs:
        print("파싱된 문서가 없습니다.")
        return
    
    # 정보 추출
    extractor = InformationExtractor()
    
    # 첫 번째 문서 테스트
    test_doc = docs[0]
    print(f"\n--- '{test_doc.get('filename', '')}' 처리 결과 ---")
    
    # 메타데이터 추출
    metadata = extractor.extract_metadata(test_doc)
    print("\n--- 메타데이터 ---")
    print(json.dumps(metadata, ensure_ascii=False, indent=2))
    
    # 온톨로지 관계 추출
    ontology = extractor.extract_ontology_relations(test_doc)
    print("\n--- 온톨로지 관계 ---")
    print(json.dumps(ontology, ensure_ascii=False, indent=2))
    
    # 구조화 데이터 추출
    structured = extractor.extract_structured_data(test_doc)
    print("\n--- 구조화 데이터 ---")
    print(json.dumps(structured, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main() 