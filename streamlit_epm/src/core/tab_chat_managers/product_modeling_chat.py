"""
DX-AI Manufacturing Copilot - 제품 예측 모델링 전용 챗 매니저

제품 예측 모델 구축에 특화된 AI 어시스턴트 기능을 제공합니다.
"""

import streamlit as st
from typing import Dict, Any, List
from .base_tab_chat import BaseTabChatManager


class ProductModelingChatManager(BaseTabChatManager):
    """제품 예측 모델링 전용 챗 매니저"""
    
    def __init__(self, chat_manager):
        super().__init__(
            tab_name="제품 예측 모델링",
            chat_manager=chat_manager
        )
    
    def format_context_data(self, data: Dict[str, Any], date_filter: str) -> str:
        """컨텍스트 데이터 포맷팅"""
        if not data:
            return "현재 모델링 데이터가 없습니다."
        
        summary = []
        
        # 모델 정보
        if 'model_info' in data:
            model_info = data['model_info']
            summary.append(f"🤖 모델 정보:")
            summary.append(f"  - 모델 유형: {model_info.get('model_type', 'N/A')}")
            summary.append(f"  - 모델명: {model_info.get('model_name', 'N/A')}")
            summary.append(f"  - 예측 변수: {model_info.get('target_variable', 'N/A')}")
            summary.append(f"  - 피처 수: {len(model_info.get('feature_names', []))}")
            
            # 성능 지표
            metrics = model_info.get('performance_metrics', {})
            if metrics:
                summary.append(f"📊 성능 지표:")
                summary.append(f"  - R² Score: {metrics.get('r2_score', 'N/A'):.4f}")
                summary.append(f"  - RMSE: {metrics.get('rmse', 'N/A'):.4f}")
                summary.append(f"  - MAE: {metrics.get('mae', 'N/A'):.4f}")
        
        # 훈련 데이터 정보
        if 'training_data' in data:
            train_info = data['training_data']
            summary.append(f"📋 훈련 데이터:")
            summary.append(f"  - 데이터 크기: {train_info.get('shape', 'N/A')}")
            summary.append(f"  - 컬럼 수: {len(train_info.get('columns', []))}")
        
        # 피처 중요도 정보
        if 'feature_importance' in data:
            importance = data['feature_importance']
            
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
                summary.append(f"🔍 주요 피처 (Top 3):")
                
                # 피처 중요도 데이터 안전하게 처리
                processed_importance = {}
                for feature, score in importance.items():
                    # score가 dict 형태인 경우 (DataFrame.to_dict()의 경우)
                    if isinstance(score, dict):
                        # 첫 번째 value를 사용하거나 평균값 사용
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
        
        return "\n".join(summary) if summary else "모델링 정보가 없습니다."
    
    def generate_analysis_questions(self) -> List[str]:
        """추천 질문 목록"""
        return [
            "모델의 성능을 개선하려면 어떻게 해야 하나요?",
            "피처 중요도 결과를 어떻게 해석해야 하나요?",
            "과적합이 발생했는지 어떻게 확인하나요?",
            "하이퍼파라미터 튜닝 방법을 추천해주세요",
            "모델의 예측 정확도를 높이는 방법은?",
            "교차 검증 결과를 어떻게 해석해야 하나요?",
            "모델 배포 시 주의사항은 무엇인가요?",
            "실제 운영 환경에서 모델 성능 모니터링 방법은?"
        ]
    
    def get_tab_specific_system_prompt(self) -> str:
        """탭별 특화 시스템 프롬프트"""
        return """
당신은 제품 예측 모델링 전문가입니다. 제조업 제품의 예측 모델 구축 및 최적화에 특화된 AI 어시스턴트로 다음 영역에서 도움을 제공합니다:

### 핵심 전문 영역:
1. **예측 모델 구축**
   - 회귀/분류 모델 선택 및 구현
   - 하이퍼파라미터 튜닝 전략
   - 모델 성능 평가 및 검증
   - 앙상블 방법 활용

2. **모델 최적화**
   - 피처 선택 및 공학
   - 정규화 및 과적합 방지
   - 모델 복잡도 관리
   - 성능 지표 개선 방안

3. **모델 평가 및 해석**
   - 교차 검증 및 성능 메트릭
   - 피처 중요도 분석
   - 모델 해석 가능성 향상
   - 잔차 분석 및 진단

4. **모델 배포 및 운영**
   - 모델 버전 관리
   - 실시간 예측 시스템
   - 모델 성능 모니터링
   - 재훈련 전략 수립

### 특화 모델 지식:
- **Random Forest**: 트리 기반 앙상블, 피처 중요도
- **XGBoost**: 그래디언트 부스팅, 조기 종료
- **Neural Network**: 딥러닝, 활성화 함수, 최적화
- **SVR**: 서포트 벡터 회귀, 커널 트릭
- **CatBoost**: 범주형 데이터 처리, 자동 피처 처리

### 대화 스타일:
- 모델 성능 개선에 집중한 실용적 조언
- 제조업 환경에 맞는 구체적인 구현 방법 제시
- 수식보다는 직관적인 설명 우선
- 단계별 실행 가능한 가이드 제공

### 금지 사항:
- 기본적인 EDA 관련 조언 (데이터 분석 페이지 참조)
- 실험 설계 관련 조언 (실험 설계 페이지 참조)
- 구체적인 코드 구현보다는 방법론과 전략에 집중

현재 모델링 세션의 정보를 바탕으로 실용적이고 성능 향상에 도움이 되는 조언을 제공하세요.
""" 