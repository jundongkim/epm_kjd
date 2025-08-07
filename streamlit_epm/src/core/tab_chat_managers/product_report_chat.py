"""
DX-AI Manufacturing Copilot - 제품 예측 모델링 보고서 전용 챗 매니저

제품 예측 모델링 결과 보고서 생성에 특화된 AI 어시스턴트 기능을 제공합니다.
"""

import streamlit as st
from typing import Dict, Any, List
from .base_tab_chat import BaseTabChatManager


class ProductReportChatManager(BaseTabChatManager):
    """제품 예측 모델링 보고서 전용 챗 매니저"""
    
    def __init__(self, chat_manager):
        super().__init__(
            tab_name="제품 모델링 보고서",
            chat_manager=chat_manager
        )
    
    def format_context_data(self, data: Dict[str, Any], date_filter: str) -> str:
        """컨텍스트 데이터 포맷팅"""
        if not data:
            return "현재 보고서 생성 데이터가 없습니다."
        
        summary = []
        
        # 모델 결과 정보
        if 'model_results' in data:
            model_results = data['model_results']
            summary.append(f"🤖 모델 결과:")
            summary.append(f"  - 모델 유형: {model_results.get('model_type', 'N/A')}")
            summary.append(f"  - 훈련 완료: {model_results.get('training_completed', False)}")
            
            # 성능 지표
            metrics = model_results.get('performance_metrics', {})
            if metrics:
                summary.append(f"📊 성능 지표:")
                summary.append(f"  - R² Score: {metrics.get('r2_score', 'N/A'):.4f}")
                summary.append(f"  - RMSE: {metrics.get('rmse', 'N/A'):.4f}")
                summary.append(f"  - MAE: {metrics.get('mae', 'N/A'):.4f}")
            
            # 피처 중요도
            importance = model_results.get('feature_importance', {})
            
            # 안전한 빈 값 체크
            has_importance = False
            if importance is not None:
                if hasattr(importance, 'empty'):
                    has_importance = not importance.empty
                elif isinstance(importance, dict):
                    has_importance = bool(importance)
                else:
                    has_importance = True
            
            if has_importance:
                summary.append(f"🔍 주요 피처:")
                
                # 피처 중요도 데이터 안전하게 처리
                processed_importance = {}
                for feature, score in importance.items():
                    # score가 dict 형태인 경우 (DataFrame.to_dict()의 경우)
                    if isinstance(score, dict):
                        # 첫 번째 value를 사용
                        if score:
                            processed_importance[feature] = list(score.values())[0]
                    # score가 숫자인 경우 (Series.to_dict()의 경우)
                    elif isinstance(score, (int, float)):
                        processed_importance[feature] = score
                
                # 상위 3개 피처 표시
                for i, (feature, score) in enumerate(list(processed_importance.items())[:3]):
                    try:
                        summary.append(f"  - {feature}: {float(score):.4f}")
                    except (ValueError, TypeError):
                        summary.append(f"  - {feature}: {score}")
        
        # 보고서 설정
        if 'report_settings' in data:
            report_settings = data['report_settings']
            summary.append(f"📋 보고서 설정:")
            summary.append(f"  - 보고서 유형: {report_settings.get('report_type', 'N/A')}")
            summary.append(f"  - 포함 섹션: {', '.join(report_settings.get('include_sections', []))}")
            summary.append(f"  - 보고서 길이: {report_settings.get('report_length', 'N/A')}")
        
        return "\n".join(summary) if summary else "보고서 생성 정보가 없습니다."
    
    def generate_analysis_questions(self) -> List[str]:
        """추천 질문 목록"""
        return [
            "모델 성능 결과를 경영진에게 어떻게 설명해야 하나요?",
            "기술 보고서에 꼭 포함해야 할 내용은 무엇인가요?",
            "모델의 비즈니스 가치를 어떻게 표현해야 하나요?",
            "피처 중요도 결과를 시각화하는 방법은?",
            "모델 성능 개선 방안을 보고서에 어떻게 작성해야 하나요?",
            "운영진을 위한 실행 요약은 어떻게 작성해야 하나요?",
            "모델 배포 계획을 보고서에 포함하는 방법은?",
            "ROI 분석을 보고서에 어떻게 반영해야 하나요?"
        ]
    
    def get_tab_specific_system_prompt(self) -> str:
        """탭별 특화 시스템 프롬프트"""
        return """
당신은 제품 예측 모델링 보고서 작성 전문가입니다. 제조업 제품의 예측 모델링 결과를 바탕으로 한 전문적인 보고서 생성에 특화된 AI 어시스턴트로 다음 영역에서 도움을 제공합니다:

### 핵심 전문 영역:
1. **기술 보고서 작성**
   - 모델 성능 지표 해석 및 설명
   - 피처 중요도 분석 결과 보고
   - 모델 검증 및 신뢰성 평가
   - 기술적 한계점 및 개선 방안

2. **비즈니스 보고서 작성**
   - 경영진 대상 실행 요약
   - 비즈니스 가치 및 ROI 분석
   - 운영 효율성 개선 제안
   - 의사결정 지원 자료 작성

3. **시각화 및 데이터 스토리텔링**
   - 효과적인 차트 및 그래프 활용
   - 데이터 기반 인사이트 도출
   - 복잡한 결과의 직관적 설명
   - 액션 아이템 도출 및 우선순위 제시

4. **보고서 구성 및 형식**
   - 대상 독자별 맞춤형 구성
   - 논리적 흐름 및 구조 설계
   - 핵심 메시지 강조 기법
   - 전문적인 문서 작성 스타일

### 보고서 유형별 특화:
- **실험 계획 요약**: 모델링 목표, 방법론, 기대 효과
- **결과 분석**: 성능 지표, 피처 분석, 모델 해석
- **최적화 제안**: 성능 개선 방안, 추가 실험 계획
- **종합 보고서**: 전체 프로젝트 요약, 결론, 다음 단계

### 대화 스타일:
- 명확하고 논리적인 설명
- 기술적 내용을 이해하기 쉽게 번역
- 실무진과 경영진 모두가 이해할 수 있는 언어 사용
- 구체적인 액션 아이템 제시

### 금지 사항:
- 단순한 데이터 분석 내용 (데이터 분석 페이지 참조)
- 모델 구현 세부사항 (모델링 페이지 참조)
- 실험 설계 관련 내용 (실험 설계 페이지 참조)

현재 모델링 결과와 보고서 설정을 바탕으로 전문적이고 실무에 활용할 수 있는 보고서 작성 도움을 제공하세요.
""" 