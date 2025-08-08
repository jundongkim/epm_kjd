"""
실험 설계 전용 AI 보고서 생성기 v2.0

DoE, 베이지안 최적화, RSM 등 실험 설계 도메인에 특화된
고품질 AI 보고서 생성 시스템
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json
import logging

# 보고서 생성기 제거됨
# from src.ai.core.ai_report_generator import (
#     EnhancedAIReportGenerator, 
#     ReportGenerationConfig,
#     ReportQualityMetrics
# )
from src.ai.core.llm_client import EnhancedOllamaClient
from src.ai.core.context_engineering import ContextEngineer

logger = logging.getLogger(__name__)

class ExperimentalDesignReportGenerator:
    # EnhancedAIReportGenerator 상속 제거됨
    """
    실험 설계 전용 AI 보고서 생성기 v2.0
    
    실험 설계 도메인에 특화된 보고서 생성:
    - DoE (Design of Experiments) 분석
    - 베이지안 최적화 결과 해석
    - 실험 계획 및 결과 검증
    - 통계적 유의성 분석
    - 반응표면분석 (RSM)
    - 실험 효율성 평가
    """
    
    def __init__(self, 
                 llm_client: Optional[EnhancedOllamaClient] = None,
                 context_engineer: Optional[ContextEngineer] = None):
        """실험 설계 전용 보고서 생성기 초기화 - 보고서 생성기 제거됨"""
        # super().__init__(llm_client, context_engineer, use_optimized_clients=True)  # 제거됨
        
        # 실험 설계 전용 보고서 템플릿
        self.experiment_report_types = {
            "실험 계획 요약": self._generate_experiment_plan_summary,
            "최적화 결과": self._generate_optimization_results,
            "DoE 분석": self._generate_doe_analysis,
            "종합 보고서": self._generate_comprehensive_report,
            "통계 분석": self._generate_statistical_analysis,
            "RSM 분석": self._generate_rsm_analysis
        }
        
        # 실험 설계 전용 품질 기준
        self.quality_criteria = {
            "statistical_validity": 0.8,      # 통계적 타당성
            "experimental_rigor": 0.8,        # 실험적 엄밀성  
            "optimization_insight": 0.7,      # 최적화 통찰력
            "practical_applicability": 0.9    # 실용적 적용성
        }
        
        logger.info("실험 설계 전용 AI 보고서 생성기 v2.0 초기화 완료")

    def generate_experiment_report(self, 
                                 report_type: str,
                                 experiment_data: Dict[str, Any],
                                 optimization_data: Optional[Dict[str, Any]] = None,
                                 include_sections: List[str] = None,
                                 report_length: str = "표준 (3-5페이지)",
                                 **kwargs) -> Dict[str, Any]:
        """
        실험 설계 보고서 생성 메인 메서드
        
        Args:
            report_type: 보고서 유형
            experiment_data: 실험 데이터
            optimization_data: 최적화 결과 데이터
            include_sections: 포함할 섹션 리스트
            report_length: 보고서 길이
            
        Returns:
            생성된 보고서와 메타데이터
        """
        start_time = datetime.now()
        
        try:
            # 설정 생성
            config = self._create_experiment_config(
                report_type, experiment_data, optimization_data,
                include_sections, report_length, **kwargs
            )
            
            # 실험 설계 컨텍스트 생성
            context = self._create_experiment_context(
                experiment_data, optimization_data, config
            )
            
            # 전용 생성 메서드 호출
            if report_type in self.experiment_report_types:
                generator_method = self.experiment_report_types[report_type]
                report_content = generator_method(context, config)
            else:
                # 범용 생성기 사용
                report_content = self._generate_generic_experiment_report(context, config)
            
            # 품질 평가
            quality_metrics = self._evaluate_experiment_report_quality(
                report_content, experiment_data, config
            )
            
            # 메타데이터 생성
            metadata = self._create_experiment_metadata(
                config, quality_metrics, start_time
            )
            
            return {
                "content": report_content,
                "metadata": metadata,
                "quality_metrics": quality_metrics,
                "generation_config": config.to_dict()
            }
            
        except Exception as e:
            logger.error(f"실험 설계 보고서 생성 실패: {e}")
            return self._create_error_response(str(e))

    def _create_experiment_config(self, 
                                report_type: str,
                                experiment_data: Dict[str, Any],
                                optimization_data: Optional[Dict[str, Any]],
                                include_sections: List[str],
                                report_length: str,
                                **kwargs) -> ReportGenerationConfig:
        """실험 설계 전용 보고서 설정 생성"""
        
        # 분석 깊이 결정
        analysis_depth = self._get_analysis_depth(report_length)
        
        # 실험 설계 전용 섹션 매핑
        section_mapping = {
            "실행 요약": "executive_summary",
            "실험 설계": "experimental_design", 
            "최적화 결과": "optimization_results",
            "통계 분석": "statistical_analysis",
            "결론 및 권장사항": "conclusions_recommendations",
            "DoE 분석": "doe_analysis",
            "RSM 분석": "rsm_analysis"
        }
        
        sections = [section_mapping.get(s, s) for s in (include_sections or [])]
        
        return ReportGenerationConfig(
            report_type=report_type,
            sections=sections,
            analysis_depth=analysis_depth,
            domain="experimental_design",
            language="korean",
            format="markdown",
            include_charts=kwargs.get("include_charts", True),
            include_recommendations=kwargs.get("include_recommendations", True),
            statistical_confidence=kwargs.get("statistical_confidence", 0.95),
            optimization_focus=kwargs.get("optimization_focus", True)
        )

    def _create_experiment_context(self, 
                                 experiment_data: Dict[str, Any],
                                 optimization_data: Optional[Dict[str, Any]],
                                 config: ReportGenerationConfig) -> str:
        """실험 설계 전용 컨텍스트 생성"""
        
        context_parts = [
            "# 실험 설계 보고서 생성 컨텍스트",
            "",
            "## 역할 정의",
            "당신은 실험 설계 및 최적화 전문가입니다.",
            "- DoE (Design of Experiments) 전문가",
            "- 베이지안 최적화 전문가", 
            "- 통계적 분석 및 품질 관리 전문가",
            "- 제조업 공정 최적화 전문가",
            "",
            "## 보고서 생성 지침",
            f"보고서 유형: {config.report_type}",
            f"분석 깊이: {config.analysis_depth}",
            f"통계적 신뢰도: {config.statistical_confidence}",
            "",
            "## 실험 데이터 분석"
        ]
        
        # 실험 계획 정보
        if "experiment_plan" in experiment_data:
            plan = experiment_data["experiment_plan"]
            context_parts.extend([
                "### 실험 계획",
                f"- 실험 유형: {plan.get('experiment_type', 'N/A')}",
                f"- 실행 횟수: {plan.get('number_of_runs', 'N/A')}",
                f"- 인수 개수: {len(plan.get('factors', []))}",
                f"- 목표 변수: {len(plan.get('targets', []))}",
                f"- 예상 효율성: {plan.get('efficiency', 'N/A')}%",
                f"- 통계적 검정력: {plan.get('statistical_power', 'N/A')}%",
                ""
            ])
            
            # 인수 정보
            if plan.get('factors'):
                context_parts.append("### 실험 인수")
                for factor in plan['factors']:
                    context_parts.append(f"- {factor.get('name', 'Unknown')}: {factor.get('range', 'N/A')}")
                context_parts.append("")
                
            # 목표 정보  
            if plan.get('targets'):
                context_parts.append("### 목표 변수")
                for target in plan['targets']:
                    context_parts.append(f"- {target.get('name', 'Unknown')}: {target.get('target', 'N/A')}")
                context_parts.append("")
        
        # 최적화 결과
        if optimization_data and "optimization_results" in optimization_data:
            results = optimization_data["optimization_results"]
            context_parts.extend([
                "### 최적화 결과",
                f"- 수렴률: {results.get('convergence_rate', 'N/A')}%",
                f"- 사용된 반복 수: {results.get('iterations_used', 'N/A')}",
                f"- 개선률: {results.get('improvement_rate', 'N/A')}%",
                ""
            ])
            
            # 최적 파라미터
            if results.get('optimal_parameters'):
                context_parts.append("### 최적 파라미터")
                for param, value in results['optimal_parameters'].items():
                    context_parts.append(f"- {param}: {value}")
                context_parts.append("")
        
        # 통계 정보
        if "experiment_stats" in experiment_data:
            stats = experiment_data["experiment_stats"]
            context_parts.extend([
                "### 실험 통계",
                f"- 총 실험 수: {stats.get('total', 0)}",
                f"- 진행 중: {stats.get('running', 0)}",
                f"- 완료됨: {stats.get('completed', 0)}",
                f"- 성공률: {stats.get('success_rate', 0)}%",
                ""
            ])
        
        context_parts.extend([
            "## 보고서 생성 요구사항",
            "1. 실험 설계의 통계적 타당성 평가",
            "2. 최적화 결과의 신뢰성 분석",
            "3. 실용적 적용 방안 제시",
            "4. 데이터 기반 의사결정 지원",
            "5. 명확하고 전문적인 한국어 작성",
            "",
            "보고서를 생성해주세요."
        ])
        
        return "\n".join(context_parts)

    def _generate_experiment_plan_summary(self, 
                                        context: str, 
                                        config: ReportGenerationConfig) -> str:
        """실험 계획 요약 보고서 생성"""
        
        prompt = f"""
{context}

다음 구조로 실험 계획 요약 보고서를 작성해주세요:

# 🔬 실험 계획 요약 보고서

## 1. 실행 요약
- 실험 목적 및 배경
- 주요 실험 인수와 목표
- 예상 결과 및 기대 효과

## 2. 실험 설계 개요
- 실험 설계 방법론 (DoE, 베이지안 최적화 등)
- 실험 계획의 통계적 근거
- 샘플 크기 및 검정력 분석

## 3. 실험 인수 및 수준
- 주요 제어 인수 분석
- 인수 간 상호작용 예측
- 최적화 범위 설정 근거

## 4. 실험 실행 계획
- 실험 순서 및 일정
- 품질 관리 방안
- 데이터 수집 프로토콜

## 5. 예상 결과 및 분석 방법
- 통계적 분석 계획
- 결과 해석 기준
- 의사결정 지원 방안

한국어로 전문적이고 실용적인 보고서를 작성해주세요.
"""
        
        return self._generate_with_langraph(prompt, config)

    def _generate_optimization_results(self, 
                                     context: str, 
                                     config: ReportGenerationConfig) -> str:
        """최적화 결과 보고서 생성"""
        
        prompt = f"""
{context}

다음 구조로 최적화 결과 보고서를 작성해주세요:

# 📊 최적화 결과 보고서

## 1. 최적화 개요
- 최적화 목표 및 제약조건
- 사용된 최적화 알고리즘
- 수렴 기준 및 성능 지표

## 2. 최적화 과정 분석
- 반복 과정 및 수렴 패턴
- 탐색 효율성 평가
- 지역 최적해 vs 전역 최적해 분석

## 3. 최적 조건 도출
- 최적 파라미터 조합
- 예측 성능 및 신뢰구간
- 민감도 분석 결과

## 4. 검증 및 확인
- 최적해의 안정성 검증
- 실험적 확인 결과
- 예측 정확도 평가

## 5. 실용화 방안
- 현장 적용 가이드라인
- 모니터링 지표
- 지속적 개선 방안

통계적 근거와 실무적 관점을 포함하여 한국어로 작성해주세요.
"""
        
        return self._generate_with_langraph(prompt, config)

    def _generate_doe_analysis(self, 
                             context: str, 
                             config: ReportGenerationConfig) -> str:
        """DoE 분석 보고서 생성"""
        
        prompt = f"""
{context}

다음 구조로 DoE (Design of Experiments) 분석 보고서를 작성해주세요:

# 🧪 DoE 분석 보고서

## 1. 실험 설계 평가
- 실험 설계의 적합성 평가
- 직교성 및 균형성 분석
- 해상도 및 별칭 구조 검토

## 2. 인수 효과 분석
- 주효과 (Main Effects) 분석
- 상호작용 효과 분석
- 효과 크기 및 유의성 검정

## 3. 모형 적합성 검토
- 회귀 모형 진단
- 잔차 분석 및 가정 검증
- 모형 개선 방안

## 4. 반응표면 분석 (해당시)
- 반응표면 모형 구축
- 최적점 탐색 및 예측
- 등고선 및 3D 시각화

## 5. 통계적 결론
- 유의한 인수 식별
- 최적 조건 추천
- 신뢰도 및 예측 구간

## 6. 실무 적용 지침
- 공정 개선 방향
- 추가 실험 제안
- 지속적 모니터링 방안

DoE 이론과 통계적 분석을 바탕으로 한국어로 작성해주세요.
"""
        
        return self._generate_with_langraph(prompt, config)

    def _generate_comprehensive_report(self, 
                                     context: str, 
                                     config: ReportGenerationConfig) -> str:
        """종합 실험 설계 보고서 생성"""
        
        prompt = f"""
{context}

다음 구조로 종합 실험 설계 보고서를 작성해주세요:

# 📋 종합 실험 설계 보고서

## 1. 실행 요약
- 프로젝트 배경 및 목적
- 주요 발견사항
- 핵심 권장사항

## 2. 실험 설계 방법론
- 실험 설계 접근법
- 통계적 근거 및 가정
- 품질 보증 방안

## 3. 실험 결과 종합
- 주요 실험 결과
- 통계적 분석 결과
- 최적화 성과

## 4. 기술적 분석
- DoE 분석 결과
- 베이지안 최적화 성과
- 반응표면 모델링

## 5. 경제성 분석
- 비용 절감 효과
- ROI 분석
- 장기적 효익

## 6. 위험 평가 및 관리
- 기술적 위험 요소
- 완화 방안
- 모니터링 계획

## 7. 실행 계획
- 단계별 실행 방안
- 자원 요구사항
- 일정 계획

## 8. 결론 및 향후 방향
- 핵심 성과 요약
- 추가 연구 방향
- 지속적 개선 방안

전문적이고 포괄적인 분석을 통해 한국어로 작성해주세요.
"""
        
        return self._generate_with_langraph(prompt, config)

    def _generate_statistical_analysis(self, 
                                     context: str, 
                                     config: ReportGenerationConfig) -> str:
        """통계 분석 보고서 생성"""
        
        prompt = f"""
{context}

다음 구조로 통계 분석 보고서를 작성해주세요:

# 📈 통계 분석 보고서

## 1. 데이터 개요 및 전처리
- 데이터 품질 평가
- 이상치 및 결측치 처리
- 변수 변환 및 정규화

## 2. 기술통계 분석
- 기본 통계량 (평균, 분산, 분포)
- 상관관계 분석
- 다변량 분석

## 3. 가설 검정
- 연구 가설 설정
- 적절한 검정 방법 선택
- p-값 및 효과 크기 해석

## 4. 회귀 분석
- 단순/다중 회귀 모형
- 모형 적합도 평가
- 예측 정확도 검증

## 5. 분산 분석 (ANOVA)
- 인수별 분산 분석
- 다중 비교 검정
- 효과 크기 계산

## 6. 신뢰성 분석
- 신뢰구간 계산
- 검정력 분석
- 표본 크기 적절성

## 7. 결과 해석 및 결론
- 통계적 유의성 해석
- 실용적 유의성 평가
- 제한사항 및 주의사항

통계학적 엄밀성을 바탕으로 한국어로 작성해주세요.
"""
        
        return self._generate_with_langraph(prompt, config)

    def _generate_rsm_analysis(self, 
                             context: str, 
                             config: ReportGenerationConfig) -> str:
        """반응표면분석 보고서 생성"""
        
        prompt = f"""
{context}

다음 구조로 반응표면분석 (RSM) 보고서를 작성해주세요:

# 🎯 반응표면분석 (RSM) 보고서

## 1. RSM 개요
- 반응표면분석의 목적
- 사용된 실험 설계
- 반응변수 및 인수 정의

## 2. 모형 구축
- 1차 모형 vs 2차 모형
- 모형 선택 기준
- 계수 추정 및 유의성

## 3. 모형 진단
- 적합결여 검정
- 잔차 분석
- 모형 가정 검증

## 4. 반응표면 분석
- 정준 분석 (Canonical Analysis)
- 능선 분석 (Ridge Analysis)
- 최적점 특성 (최대, 최소, 안장점)

## 5. 최적화 결과
- 최적 조건 도출
- 예측 반응값
- 신뢰구간 및 예측구간

## 6. 민감도 분석
- 인수별 영향도
- 상호작용 효과
- 로버스트 조건 탐색

## 7. 그래픽 분석
- 등고선도 해석
- 3D 반응표면도
- 슬라이스 플롯

## 8. 검증 및 확인
- 확인 실험 계획
- 모형 예측 정확도
- 실용화 가이드라인

RSM 이론과 실무 적용을 균형있게 한국어로 작성해주세요.
"""
        
        return self._generate_with_langraph(prompt, config)

    def _evaluate_experiment_report_quality(self, 
                                          content: str,
                                          experiment_data: Dict[str, Any],
                                          config: ReportGenerationConfig) -> ReportQualityMetrics:
        """실험 설계 보고서 품질 평가"""
        
        # 기본 품질 평가
        base_metrics = self._evaluate_report_quality(content, config)
        
        # 실험 설계 전용 품질 지표
        statistical_validity = self._assess_statistical_validity(content)
        experimental_rigor = self._assess_experimental_rigor(content)
        optimization_insight = self._assess_optimization_insight(content)
        practical_applicability = self._assess_practical_applicability(content)
        
        # 종합 점수 계산
        experiment_score = (
            statistical_validity * 0.3 +
            experimental_rigor * 0.25 +
            optimization_insight * 0.25 +
            practical_applicability * 0.2
        )
        
        return ReportQualityMetrics(
            overall_score=(base_metrics.overall_score + experiment_score) / 2,
            content_quality=base_metrics.content_quality,
            technical_accuracy=max(base_metrics.technical_accuracy, statistical_validity),
            clarity_score=base_metrics.clarity_score,
            completeness=base_metrics.completeness,
            custom_metrics={
                "statistical_validity": statistical_validity,
                "experimental_rigor": experimental_rigor,
                "optimization_insight": optimization_insight,
                "practical_applicability": practical_applicability,
                "experiment_domain_score": experiment_score
            }
        )

    def _assess_statistical_validity(self, content: str) -> float:
        """통계적 타당성 평가"""
        validity_keywords = [
            "통계적 유의성", "p-값", "신뢰구간", "검정력", "효과 크기",
            "가설검정", "분산분석", "ANOVA", "회귀분석", "상관관계"
        ]
        return self._calculate_keyword_score(content, validity_keywords)

    def _assess_experimental_rigor(self, content: str) -> float:
        """실험적 엄밀성 평가"""
        rigor_keywords = [
            "실험설계", "DoE", "직교성", "균형성", "반복", "블록",
            "임의화", "제어", "변수", "인수", "수준", "교락"
        ]
        return self._calculate_keyword_score(content, rigor_keywords)

    def _assess_optimization_insight(self, content: str) -> float:
        """최적화 통찰력 평가"""
        optimization_keywords = [
            "최적화", "베이지안", "반응표면", "RSM", "최적점", "수렴",
            "탐색", "개선", "효율", "성능", "파라미터", "조건"
        ]
        return self._calculate_keyword_score(content, optimization_keywords)

    def _assess_practical_applicability(self, content: str) -> float:
        """실용적 적용성 평가"""
        practical_keywords = [
            "적용", "실무", "현장", "구현", "가이드라인", "권장사항",
            "모니터링", "관리", "개선", "효과", "비용", "ROI"
        ]
        return self._calculate_keyword_score(content, practical_keywords)

    def _create_experiment_metadata(self, 
                                  config: ReportGenerationConfig,
                                  quality_metrics: ReportQualityMetrics,
                                  start_time: datetime) -> Dict[str, Any]:
        """실험 설계 보고서 메타데이터 생성"""
        
        generation_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "generator_version": "2.0",
            "generator_type": "experimental_design_specialized",
            "generation_time": generation_time,
            "timestamp": datetime.now().isoformat(),
            "config": {
                "report_type": config.report_type,
                "analysis_depth": config.analysis_depth,
                "statistical_confidence": config.statistical_confidence,
                "optimization_focus": config.optimization_focus
            },
            "quality_assessment": {
                "overall_score": quality_metrics.overall_score,
                "statistical_validity": quality_metrics.custom_metrics.get("statistical_validity", 0) if quality_metrics.custom_metrics else 0,
                "experimental_rigor": quality_metrics.custom_metrics.get("experimental_rigor", 0) if quality_metrics.custom_metrics else 0,
                "optimization_insight": quality_metrics.custom_metrics.get("optimization_insight", 0) if quality_metrics.custom_metrics else 0,
                "practical_applicability": quality_metrics.custom_metrics.get("practical_applicability", 0) if quality_metrics.custom_metrics else 0
            },
            "domain_expertise": {
                "doe_coverage": True,
                "optimization_methods": True,
                "statistical_analysis": True,
                "rsm_capability": True
            }
        }

    def _calculate_keyword_score(self, content: str, keywords: List[str]) -> float:
        """키워드 기반 점수 계산"""
        if not content or not keywords:
            return 0.0
        
        content_lower = content.lower()
        found_keywords = sum(1 for keyword in keywords if keyword.lower() in content_lower)
        return min(found_keywords / len(keywords), 1.0)

    def _get_analysis_depth(self, report_length: str) -> str:
        """보고서 길이에 따른 분석 깊이 결정"""
        depth_map = {
            "간단 (1-2페이지)": "basic",
            "표준 (3-5페이지)": "standard", 
            "상세 (5-10페이지)": "comprehensive"
        }
        return depth_map.get(report_length, "standard")

    def _generate_with_langraph(self, prompt: str, config: ReportGenerationConfig) -> str:
        """LangGraph를 사용한 보고서 생성"""
        try:
            if self.context_engineer:
                # 컨텍스트 엔지니어링 사용 - 올바른 파라미터 사용
                enhanced_prompt = self.context_engineer.create_context(
                    topic="experimental_design",
                    user_query=prompt,
                    simulation_params={"analysis_depth": config.analysis_depth}
                )
            else:
                enhanced_prompt = prompt
            
            # LLM 클라이언트로 생성
            if self.llm_client:
                response = self.llm_client.generate(
                    enhanced_prompt,
                    temperature=0.5,
                    max_tokens=2048
                )
                return response if isinstance(response, str) else str(response)
            else:
                # 폴백: 기본 응답
                return self._generate_fallback_content(config.report_type)
                
        except Exception as e:
            logger.error(f"LangGraph 생성 실패: {e}")
            return self._generate_fallback_content(config.report_type)

    def _generate_generic_experiment_report(self, context: str, config: ReportGenerationConfig) -> str:
        """범용 실험 설계 보고서 생성"""
        prompt = f"""
{context}

다음 구조로 {config.report_type} 보고서를 작성해주세요:

# 📊 {config.report_type}

## 1. 개요
- 실험 목적 및 배경
- 주요 목표 및 성과 지표

## 2. 실험 설계
- 사용된 실험 설계 방법
- 실험 인수 및 수준
- 통계적 근거

## 3. 결과 분석
- 주요 실험 결과
- 통계적 분석 결과
- 최적화 성과

## 4. 결론 및 권장사항
- 핵심 발견사항
- 실무 적용 방안
- 향후 개선 방향

전문적이고 실용적인 한국어 보고서를 작성해주세요.
"""
        return self._generate_with_langraph(prompt, config)

    def _generate_fallback_content(self, report_type: str) -> str:
        """폴백 콘텐츠 생성"""
        return f"""# {report_type}

## 개요
{report_type} 보고서가 생성되었습니다.

## 주요 내용
- 실험 설계 분석
- 결과 해석
- 권장사항

## 결론
추가적인 분석이 필요합니다.

*참고: 이 보고서는 기본 템플릿으로 생성되었습니다.*
"""

    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """오류 응답 생성"""
        return {
            "content": f"# 보고서 생성 오류\n\n{error_message}\n\n다시 시도해주세요.",
            "metadata": {
                "generator_version": "2.0",
                "generator_type": "experimental_design_error",
                "error": error_message,
                "timestamp": datetime.now().isoformat()
            },
            "quality_metrics": ReportQualityMetrics(
                overall_score=0.0,
                content_quality=0.0,
                technical_accuracy=0.0,
                clarity_score=0.0,
                completeness=0.0
            ),
            "generation_config": {}
        }

# 편의 함수
def create_experimental_design_report_generator(
    use_context_engineering: bool = True,
    use_optimized_clients: bool = True
) -> ExperimentalDesignReportGenerator:
    """실험 설계 전용 보고서 생성기 생성"""
    
    from src.ai.core.llm_client import get_report_client
    from src.ai.core.context_engineering import ContextEngineer
    
    llm_client = None
    context_engineer = None
    
    if use_optimized_clients:
        llm_client = get_report_client()
    
    if use_context_engineering:
        context_engineer = ContextEngineer()
    
    return ExperimentalDesignReportGenerator(
        llm_client=llm_client,
        context_engineer=context_engineer
    ) 