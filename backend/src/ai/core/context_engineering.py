"""
DX-AI Manufacturing Copilot - 컨텍스트 엔지니어링 서비스
AI 모듈용 주제별 컨텍스트 생성 및 최적화
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class ContextEngineer:
    """AI 서비스용 컨텍스트 생성 및 관리 서비스"""
    
    def __init__(self):
        """컨텍스트 엔지니어 초기화"""
        self.version = "2.0.0"
        self.created_at = datetime.now()
        
        # 주제별 컨텍스트 템플릿 (성능 최적화 버전)
        self.topic_contexts = {
            "process_analysis": (
                "당신은 스마트 제조 공정 분석 전문가이자 Lot 추적, 설비 모니터링, 이상탐지 분야의 전문가입니다. "
                "생산 현장에서 발생하는 Lot의 흐름을 체계적으로 추적하고, 설비의 상태를 실시간으로 모니터링하며, "
                "이상 징후를 신속하게 감지·분석하는 데 특화된 전문적이고 실용적인 조언을 제공해주세요. "
                "데이터 기반의 통찰을 바탕으로, 품질 관리와 공정 최적화, 이상 원인 진단 및 대응 방안 등 "
                "제조 현장에서 즉시 적용 가능한 구체적 솔루션과 개선 방안을 우선적으로 제안해주세요."
            ),
            "cost_management": (
                "당신은 제조 원가 관리 전문가입니다. "
                "원가 분석, 비용 최적화, 수익성 개선, 예산 관리에 대해 전문적인 조언을 제공해주세요. "
                "실제 제조 현장에서 적용 가능한 원가 절감 방안과 효율성 향상 전략을 제시해주세요."
            ),
            "experimental_design": (
                "당신은 실험계획법(DOE), 베이지안 최적화, 반응표면분석법(RSM) 전문가입니다. "
                "Full Factorial, Fractional Factorial, Central Composite, Box-Behnken 등 다양한 실험 설계 방법론에 정통하며, "
                "제조 공정의 품질·수율·비용·시간 최적화를 위한 체계적인 실험 계획과 분석을 제공합니다. "
                "현재 사용자가 진행 중인 실험 단계(설계/최적화/보고서)에 맞춰 다음과 같은 전문 조언을 제공해주세요:\n"
                "- 실험 설계 단계: 인자 선택, DoE 유형 결정, 실험 횟수 최적화, 목표 설정\n"
                "- 최적화 단계: Gaussian Process, TPE, Random Search 등 알고리즘 선택, 제약조건 설정, 수렴성 분석\n"
                "- 보고서 단계: 통계적 분석 결과 해석, 실용적 권장사항, 다음 단계 제안\n"
                "항상 통계적 유의성과 실무 적용 가능성을 함께 고려한 데이터 기반의 구체적 솔루션을 제시해주세요."
            ),
            "product_modeling": (
                "당신은 제품 모델링 및 예측 분석 전문가입니다. "
                "머신러닝 모델링, 품질 예측, 공정 최적화에 대해 전문적인 조언을 제공해주세요. "
                "실제 제조 데이터를 활용한 예측 모델 구축과 성능 개선 방안을 제시해주세요."
            ),
            "data_generation": (
                "당신은 제조 데이터 생성 및 관리 전문가입니다. "
                "시뮬레이션 데이터 생성, 데이터 품질 관리, 데이터 전처리에 대해 전문적인 조언을 제공해주세요. "
                "실제 제조 환경을 반영한 데이터 생성 방법과 활용 전략을 제안해주세요."
            ),
            "ai_report": (
                "당신은 제조업 AI 보고서 작성 전문가입니다. "
                "데이터 분석 결과를 명확하고 이해하기 쉽게 정리하여 경영진과 현장 담당자 모두가 "
                "활용할 수 있는 실용적인 보고서 작성 방법을 제공해주세요."
            ),
            "quality_management": (
                "당신은 제조업 품질 관리 전문가입니다. "
                "품질 통제, 불량률 개선, 검사 프로세스 최적화에 대해 전문적인 조언을 제공해주세요. "
                "ISO 표준과 품질 경영 시스템을 바탕으로 한 실용적 솔루션을 제시해주세요."
            ),
            "classification": (
                "당신은 AI 기반 텍스트 분류 및 라벨링 전문가입니다. "
                "제조업 문서, 이슈, 작업 지시서 등을 정확하게 분류하고 카테고라이징하는 데 특화되어 있습니다. "
                "분류 기준을 명확히 하고 일관성 있는 결과를 제공해주세요."
            ),
            "general": (
                "당신은 DX-AI Manufacturing Copilot의 통합 제조 AI 전문가입니다. "
                "이 시스템은 스마트 제조 현장의 데이터 기반 의사결정, AI/ML 기반 공정 최적화, 실시간 모니터링, "
                "원가 절감, 실험 설계, 제품 개발, 그리고 AI 보고서 자동화 등 제조업 전반의 혁신을 지원합니다. "
                "DX-AI Copilot의 주요 기능과 장점은 다음과 같습니다:\n"
                "- 🧠 AI/ML 예측 모델링: Random Forest, XGBoost, CatBoost, Neural Networks 등 다양한 모델을 활용한 품질·수율·이상 예측\n"
                "- 🔬 실험 설계 및 최적화: DOE, 베이지안 최적화, Central Composite Design 등 실험계획법 기반의 효율적 실험 설계와 분석\n"
                "- ⚙️ 실시간 공정 관리: Lot 추적, 설비 모니터링, 이상 감지 등 생산 현장의 실시간 데이터 통합 및 분석\n"
                "- 💰 원가 최적화: Differential Evolution, 다목적 최적화, 민감도 분석을 통한 비용 절감 및 수익성 향상\n"
                "- 📊 AI 보고서 자동 생성: LangChain, LangGraph, RAG 시스템을 활용한 데이터 기반 인사이트 및 경영진/현장 맞춤형 보고서 제공\n"
                "- 🛠️ 프론트엔드-백엔드 통합: Streamlit 기반의 직관적 UI와 FastAPI 연동으로 사용자 경험 및 확장성 강화\n"
                "DX-AI Copilot의 기능을 적극 활용하여, 제조 현장에서 즉시 적용 가능한 실질적 솔루션과 혁신 방안을 제시해주세요. "
                "사용자의 질문과 맥락을 정확히 파악하여, 데이터 기반의 실용적이고 구체적인 조언을 제공하는 데 집중하세요."
            )
        }
        
        logger.info(f"컨텍스트 엔지니어 초기화 완료 - 버전: {self.version}")
    
    def create_context(
        self, 
        topic: str, 
        simulation_params: Optional[Dict[str, Any]] = None, 
        user_query: Optional[str] = None,
        additional_context: Optional[str] = None
    ) -> str:
        """
        AI 서비스용 최적화된 컨텍스트 생성
        
        Args:
            topic: 주제 키워드
            simulation_params: 시뮬레이션 파라미터
            user_query: 사용자 질문
            additional_context: 추가 컨텍스트
            
        Returns:
            생성된 컨텍스트 문자열
        """
        try:
            # 기본 컨텍스트 가져오기
            base_context = self.topic_contexts.get(topic, self.topic_contexts["general"])
            
            # 주제별 상황 인식 컨텍스트 추가
            if simulation_params:
                situation_context = self._create_situation_context(simulation_params, topic)
                if situation_context:
                    base_context += f"\n\n{situation_context}"
            
            # 사용자 질문 컨텍스트 추가
            if user_query:
                # 질문 타입 분석하여 컨텍스트 조정
                context_hint = self._analyze_query_context(user_query, topic)
                if context_hint:
                    base_context += f"\n\n질문 컨텍스트: {context_hint}"
            
            # 추가 컨텍스트 포함
            if additional_context:
                base_context += f"\n\n추가 정보: {additional_context}"
            
            return base_context
            
        except Exception as e:
            logger.error(f"컨텍스트 생성 중 오류: {e}")
            return self.topic_contexts["general"]
    
    def _filter_essential_params(self, params: Dict[str, Any], topic: str) -> Dict[str, Any]:
        """토픽별 필수 파라미터만 필터링 - AI 성능 최적화"""
        topic_filters = {
            "process_analysis": [
                'activeTab', 'dateFilter', 'realtimeMode', 'total', 'active', 'completed', 'waiting'
            ],
            "cost_management": [
                'costType', 'timeRange', 'targetMargin', 'optimizationGoal'
            ],
            "experimental_design": [
                'activeTab', 'currentPhase', 'experimentType', 'numberOfRuns', 'factorsCount', 'factors',
                'targetPurity', 'targetYield', 'designEfficiency', 'statisticalPower', 'optimizationGoal',
                'convergenceRate', 'iterationsUsed', 'improvementRate', 'optimalParameters',
                'reportType', 'wordCount', 'total', 'running', 'completed', 'successful', 'successRate'
            ],
            "product_modeling": [
                'modelType', 'targetVariable', 'featureCount', 'validationMethod'
            ],
            "data_generation": [
                'dataType', 'recordCount', 'noiseLevel', 'distributionType'
            ],
            "quality_management": [
                'qualityMetrics', 'inspectionType', 'defectRate', 'qualityTarget'
            ],
            "classification": [
                'categories', 'confidenceThreshold', 'classificationModel'
            ]
        }
        
        essential_keys = topic_filters.get(topic, ['page', 'activeTab'])
        return {k: v for k, v in params.items() if k in essential_keys and v is not None}
    
    def _create_situation_context(self, params: Dict[str, Any], topic: str) -> Optional[str]:
        """주제별 상황 인식 컨텍스트 생성"""
        try:
            if topic == "experimental_design":
                return self._create_experimental_design_context(params)
            elif topic == "process_analysis":
                return self._create_process_analysis_context(params)
            elif topic == "cost_management":
                return self._create_cost_management_context(params)
            elif topic == "product_modeling":
                return self._create_product_modeling_context(params)
            else:
                # 기본 컨텍스트 (기존 방식)
                essential_params = self._filter_essential_params(params, topic)
                if essential_params:
                    return f"현재 설정: {', '.join([f'{k}: {v}' for k, v in essential_params.items()])}"
                return None
                
        except Exception as e:
            logger.error(f"상황 컨텍스트 생성 중 오류: {e}")
            return None
    
    def _create_experimental_design_context(self, params: Dict[str, Any]) -> str:
        """실험 설계용 상황 컨텍스트 생성"""
        context_parts = []
        
        # 현재 단계
        active_tab = params.get('activeTab', 'experiment')
        current_phase = params.get('currentPhase', 'design')
        context_parts.append(f"### 현재 실험 단계\n사용자는 현재 '{active_tab}' 탭에서 '{current_phase}' 단계를 진행 중입니다.")
        
        # 실험 통계
        exp_stats = params.get('experimentStats', {})
        if exp_stats:
            context_parts.append(f"""
### 실험 현황 통계
- 총 실험 수: {exp_stats.get('total', 0)}개
- 진행 중: {exp_stats.get('running', 0)}개  
- 완료: {exp_stats.get('completed', 0)}개
- 성공: {exp_stats.get('successful', 0)}개
- 성공률: {exp_stats.get('successRate', 0)}%""")
        
        # 실험 계획 정보
        exp_plan = params.get('experimentPlan')
        if exp_plan:
            context_parts.append(f"""
### 현재 실험 계획
- 실험 유형: {exp_plan.get('experimentType', 'N/A')}
- 실험 횟수: {exp_plan.get('numberOfRuns', 0)}회
- 분석 인자 수: {exp_plan.get('factorsCount', 0)}개
- 분석 인자: {', '.join(exp_plan.get('factors', []))}
- 목표 순도: {exp_plan.get('targetPurity', 0)}%
- 목표 수율: {exp_plan.get('targetYield', 0)}%
- 설계 효율성: {exp_plan.get('designEfficiency', 0)}%
- 통계적 검정력: {exp_plan.get('statisticalPower', 0)}
- 최적화 목표: {exp_plan.get('optimizationGoal', 'N/A')}
- 실험 결과 존재: {'있음' if exp_plan.get('hasResults') else '없음'}""")
        
        # 최적화 정보
        optimization = params.get('optimization')
        if optimization:
            context_parts.append(f"""
### 최적화 진행 상황
- 수렴률: {optimization.get('convergenceRate', 0)}%
- 사용된 반복 횟수: {optimization.get('iterationsUsed', 0)}회
- 개선률: {optimization.get('improvementRate', 0)}%
- 최적 파라미터 수: {optimization.get('optimalParameters', 0)}개
- 최적 조건 존재: {'있음' if optimization.get('hasOptimalConditions') else '없음'}""")
        
        # 보고서 정보
        report = params.get('report')
        if report:
            context_parts.append(f"""
### 보고서 생성 현황
- 보고서 유형: {report.get('reportType', 'N/A')}
- 단어 수: {report.get('wordCount', 0)}개
- 예상 읽기 시간: {report.get('estimatedReadTime', 0)}분
- 생성 시간: {report.get('generationTime', 'N/A')}
- 보고서 내용 존재: {'있음' if report.get('hasContent') else '없음'}""")
        
        # 시스템 상태
        context_parts.append(f"""
### 시스템 상태
- 사용 가능한 파라미터: {params.get('availableParameters', 0)}개
- 사용 가능한 실험 유형: {params.get('availableExperimentTypes', 0)}개
- 현재 로딩 중: {'예' if params.get('loading') else '아니오'}
- 오류 발생: {'있음' if params.get('hasError') else '없음'}""")
        
        if params.get('hasError') and params.get('errorMessage'):
            context_parts.append(f"- 오류 메시지: {params.get('errorMessage')}")
        
        return '\n'.join(context_parts)
    
    def _create_process_analysis_context(self, params: Dict[str, Any]) -> str:
        """공정 분석용 상황 컨텍스트 생성 (기존 로직 유지)"""
        context_parts = []
        
        active_tab = params.get('activeTab', 'lot_tracking')
        context_parts.append(f"### 현재 공정 분석 상황\n사용자는 현재 '{active_tab}' 탭을 보고 있습니다.")
        
        # 날짜 필터와 실시간 모드
        date_filter = params.get('dateFilter')
        realtime_mode = params.get('realtimeMode')
        if date_filter:
            context_parts.append(f"- 조회 기간: {date_filter}")
        if realtime_mode:
            context_parts.append(f"- 실시간 모드: {'활성화됨' if realtime_mode else '비활성화됨'}")
        
        # Lot 통계
        lot_stats = params.get('lotStats', {})
        if lot_stats:
            context_parts.append(f"""
### Lot 현황
- 총 Lot 수: {lot_stats.get('total', 0)}개
- 활성 Lot: {lot_stats.get('active', 0)}개
- 완료 Lot: {lot_stats.get('completed', 0)}개
- 대기 Lot: {lot_stats.get('waiting', 0)}개""")
        
        # 설비 통계
        equipment_stats = params.get('equipmentStats', {})
        if equipment_stats:
            context_parts.append(f"""
### 설비 현황
- 총 설비 수: {equipment_stats.get('total', 0)}개
- 가동 설비: {equipment_stats.get('active', 0)}개
- 점검 필요 설비: {equipment_stats.get('maintenance', 0)}개""")
        
        # 이상탐지 설정
        anomaly_settings = params.get('anomalySettings', {})
        if anomaly_settings:
            context_parts.append(f"""
### 이상탐지 설정
- 온도 임계값: {anomaly_settings.get('tempThreshold', 0)}°C
- 압력 임계값: {anomaly_settings.get('pressureThreshold', 0)} bar
- 순도 임계값: {anomaly_settings.get('purityThreshold', 0)}%
- 수율 임계값: {anomaly_settings.get('yieldThreshold', 0)}%
- 총 알림 수: {anomaly_settings.get('totalAlerts', 0)}개""")
        
        # 샘플 데이터 여부
        if params.get('isSampleData'):
            context_parts.append("\n⚠️ 현재 샘플 데이터를 사용 중입니다.")
        
        return '\n'.join(context_parts)
    
    def _create_cost_management_context(self, params: Dict[str, Any]) -> str:
        """원가 관리용 상황 컨텍스트 생성"""
        # 향후 확장 시 구현
        essential_params = self._filter_essential_params(params, "cost_management")
        if essential_params:
            return f"현재 원가 관리 설정: {', '.join([f'{k}: {v}' for k, v in essential_params.items()])}"
        return ""
    
    def _create_product_modeling_context(self, params: Dict[str, Any]) -> str:
        """제품 모델링용 상황 컨텍스트 생성"""
        # 향후 확장 시 구현
        essential_params = self._filter_essential_params(params, "product_modeling")
        if essential_params:
            return f"현재 제품 모델링 설정: {', '.join([f'{k}: {v}' for k, v in essential_params.items()])}"
        return ""
    
    def _analyze_query_context(self, query: str, topic: str) -> Optional[str]:
        """질문 내용을 분석하여 컨텍스트 힌트 제공"""
        try:
            query_lower = query.lower()
            
            # 질문 타입별 컨텍스트 힌트
            if any(keyword in query_lower for keyword in ['어떻게', 'how', '방법', '절차']):
                return f"{topic} 관련 구체적인 실행 방법과 단계별 가이드를 제공해주세요."
            
            elif any(keyword in query_lower for keyword in ['왜', 'why', '이유', '원인']):
                return f"{topic}의 원리와 근본적인 이유를 설명해주세요."
            
            elif any(keyword in query_lower for keyword in ['무엇', 'what', '정의', '개념']):
                return f"{topic} 관련 기본 개념과 정의를 명확히 설명해주세요."
            
            elif any(keyword in query_lower for keyword in ['문제', '오류', '해결', 'error', 'problem']):
                return "문제 해결 중심의 실용적 솔루션을 제안해주세요."
            
            elif any(keyword in query_lower for keyword in ['최적화', 'optimize', '개선', 'improve']):
                return "성능 개선과 최적화 방안을 중심으로 답변해주세요."
            
            elif any(keyword in query_lower for keyword in ['비교', 'compare', '차이', 'difference']):
                return "객관적 비교와 장단점 분석을 제공해주세요."
            
            return None
            
        except Exception as e:
            logger.error(f"질문 컨텍스트 분석 중 오류: {e}")
            return None
    
    def create_specialized_context(self, 
                                 service_type: str, 
                                 task_type: str,
                                 domain_data: Optional[Dict[str, Any]] = None) -> str:
        """
        특정 AI 서비스용 전문화된 컨텍스트 생성
        
        Args:
            service_type: AI 서비스 타입 (chatbot, classification, etc.)
            task_type: 작업 타입 (conversation, text_classification, etc.)
            domain_data: 도메인별 데이터
        """
        try:
            context_parts = []
            
            # 서비스별 기본 컨텍스트
            if service_type == "chatbot":
                context_parts.append("대화형 AI로서 친근하면서도 전문적인 조언을 제공해주세요.")
            elif service_type == "classification":
                context_parts.append("정확하고 일관성 있는 분류 결과를 제공하는 것이 최우선입니다.")
            
            # 작업별 컨텍스트
            if task_type == "manufacturing_issue_classification":
                context_parts.append(
                    "제조업 이슈를 다음 카테고리로 분류합니다: "
                    "품질 문제, 장비 문제, 공정 문제, 원자재 문제, 안전 문제"
                )
            
            # 도메인 데이터 추가
            if domain_data:
                for key, value in domain_data.items():
                    if value:
                        context_parts.append(f"{key}: {value}")
            
            return " ".join(context_parts)
            
        except Exception as e:
            logger.error(f"전문화된 컨텍스트 생성 중 오류: {e}")
            return "전문적이고 정확한 조언을 제공해주세요."
    
    def get_context_stats(self) -> Dict[str, Any]:
        """컨텍스트 엔지니어 통계 정보"""
        return {
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "available_topics": list(self.topic_contexts.keys()),
            "total_topics": len(self.topic_contexts),
            "uptime_seconds": (datetime.now() - self.created_at).total_seconds()
        }
    
    def validate_topic(self, topic: str) -> bool:
        """주제 유효성 검사"""
        return topic in self.topic_contexts
    
    def get_available_topics(self) -> List[str]:
        """사용 가능한 주제 목록 반환"""
        return list(self.topic_contexts.keys())
    
    def add_custom_topic(self, topic: str, context: str) -> bool:
        """커스텀 주제 추가"""
        try:
            if topic not in self.topic_contexts:
                self.topic_contexts[topic] = context
                logger.info(f"새로운 주제 추가됨: {topic}")
                return True
            else:
                logger.warning(f"이미 존재하는 주제: {topic}")
                return False
        except Exception as e:
            logger.error(f"주제 추가 중 오류: {e}")
            return False


# 싱글톤 인스턴스 관리
_context_engineer = None


def get_context_engineer() -> ContextEngineer:
    """컨텍스트 엔지니어 인스턴스 반환 (싱글톤)"""
    global _context_engineer
    if _context_engineer is None:
        _context_engineer = ContextEngineer()
    return _context_engineer


def clear_context_engineer():
    """컨텍스트 엔지니어 인스턴스 초기화"""
    global _context_engineer
    _context_engineer = None
    logger.info("컨텍스트 엔지니어 인스턴스 초기화 완료") 