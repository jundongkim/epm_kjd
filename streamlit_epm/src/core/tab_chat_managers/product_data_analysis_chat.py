"""
DX-AI Manufacturing Copilot - 제품 데이터 분석 (EDA) 전용 챗 매니저

탐색적 데이터 분석(EDA)에 특화된 AI 어시스턴트 기능을 제공합니다.
"""

import streamlit as st
from typing import Dict, Any, List
from .base_tab_chat import BaseTabChatManager


class ProductDataAnalysisChatManager(BaseTabChatManager):
    """제품 데이터 분석 (EDA) 전용 챗 매니저"""
    
    def __init__(self, chat_manager):
        super().__init__(
            tab_name="제품 데이터 분석 (EDA)",
            chat_manager=chat_manager
        )
    
    def format_context_data(self, data: Dict[str, Any], date_filter: str) -> str:
        """EDA 전용 컨텍스트 데이터 포맷팅"""
        if not data:
            return "현재 분석 중인 데이터가 없습니다."
        
        # 데이터 없음 메시지 처리
        if 'message' in data:
            return data['message']
        
        summary = []
        
        # 데이터 소스 정보
        if 'data_info' in data:
            data_info = data['data_info']
            summary.append(f"📋 데이터 소스: {data_info.get('data_source', 'Unknown')}")
            if data_info.get('is_sample_data', False):
                summary.append(f"  ⚠️ 현재 예시 데이터를 사용중입니다. 실제 데이터 업로드를 권장합니다.")
        
        # 데이터 기본 정보
        if 'data_summary' in data:
            data_info = data['data_summary']
            summary.append(f"📊 데이터 기본 정보:")
            summary.append(f"  - 행 수: {data_info.get('rows', 'N/A')}")
            summary.append(f"  - 전체 컬럼 수: {len(data_info.get('columns', []))}")
            summary.append(f"  - 수치형 컬럼 수: {len(data_info.get('numeric_columns', []))}")
            summary.append(f"  - 컬럼 목록: {', '.join(data_info.get('columns', []))}")
            
            # 데이터 타입 정보
            data_types = data_info.get('data_types', {})
            if data_types:
                summary.append(f"  - 데이터 타입:")
                for col, dtype in data_types.items():
                    summary.append(f"    * {col}: {dtype}")
            
            # 결측치 정보
            missing_values = data_info.get('missing_values', {})
            total_missing = sum(missing_values.values())
            if total_missing > 0:
                summary.append(f"  - 총 결측치: {total_missing}")
                summary.append(f"  - 컬럼별 결측치:")
                for col, missing_count in missing_values.items():
                    if missing_count > 0:
                        percentage = (missing_count / data_info.get('rows', 1)) * 100
                        summary.append(f"    * {col}: {missing_count}개 ({percentage:.1f}%)")
            
            # 수치형 컬럼 통계 정보 추가
            numeric_columns = data_info.get('numeric_columns', [])
            if numeric_columns:
                summary.append(f"  - 수치형 컬럼 통계:")
                # 실제 데이터가 있는 경우 기본 통계 포함
                if 'basic_statistics' in data_info:
                    basic_stats = data_info['basic_statistics']
                    for col in numeric_columns[:5]:  # 최대 5개 컬럼만 표시
                        if col in basic_stats:
                            stats = basic_stats[col]
                            summary.append(f"    * {col}: 평균 {stats.get('mean', 0):.2f}, 표준편차 {stats.get('std', 0):.2f}")
        
        # 상관관계 분석 정보 (EDA의 핵심)
        if 'correlation_analysis' in data:
            corr_info = data['correlation_analysis']
            
            # 오류 메시지 처리
            if 'error' in corr_info:
                summary.append(f"📈 상관관계 분석:")
                summary.append(f"  - 오류: {corr_info['error']}")
                summary.append(f"  - 선택된 컬럼: {', '.join(corr_info.get('selected_columns', []))}")
            
            # 분석 불가능 메시지 처리
            elif 'message' in corr_info:
                summary.append(f"📈 상관관계 분석:")
                summary.append(f"  - {corr_info['message']}")
                summary.append(f"  - 수치형 컬럼 수: {corr_info.get('numeric_columns_count', 0)}")
            
            # 정상 분석 결과
            else:
                selected_cols = corr_info.get('selected_columns', [])
                threshold = corr_info.get('threshold_used', 0.7)
                high_corr = corr_info.get('high_correlations', [])
                
                summary.append(f"📈 상관관계 분석:")
                summary.append(f"  - 분석 대상 컬럼: {', '.join(selected_cols)}")
                summary.append(f"  - 사용된 임계값: {threshold}")
                summary.append(f"  - 높은 상관관계 발견: {len(high_corr)}개")
                
                if high_corr:
                    for corr in high_corr[:5]:  # 최대 5개까지만 표시
                        corr_val = corr.get('correlation', 0)
                        strength = corr.get('strength', '보통')
                        summary.append(f"    * {corr.get('var1', '')} ↔ {corr.get('var2', '')}: {corr_val:.3f} ({strength})")
                    if len(high_corr) > 5:
                        summary.append(f"    * ... 및 {len(high_corr) - 5}개 추가")
                else:
                    summary.append(f"  - 임계값 {threshold} 이상의 상관관계 없음")
        
        # 데이터 품질 정보 추가
        if 'data_quality' in data:
            quality_info = data['data_quality']
            summary.append(f"🔍 데이터 품질 정보:")
            summary.append(f"  - 중복 행 수: {quality_info.get('duplicate_rows', 0)}개")
            summary.append(f"  - 완전한 행 수: {quality_info.get('complete_rows', 0)}개")
            summary.append(f"  - 데이터 완성도: {quality_info.get('completeness_rate', 0):.1f}%")
        
        # 샘플 데이터 정보 추가
        if 'sample_data' in data:
            sample_info = data['sample_data']
            summary.append(f"👀 샘플 데이터 (상위 3행):")
            for i, row in enumerate(sample_info[:3]):
                summary.append(f"  - 행 {i+1}: {row}")
        
        # 현재 탭 정보
        current_tab = data.get('current_tab', 'unknown')
        summary.append(f"🎯 현재 탭: {current_tab}")
        
        return "\n".join(summary) if summary else "EDA 분석 정보가 없습니다."
    
    def generate_analysis_questions(self) -> List[str]:
        """EDA 전용 추천 질문 목록"""
        return [
            "데이터 분포가 정규분포를 따르는지 확인하는 방법은?",
            "상관관계 분석 결과를 어떻게 해석해야 하나요?",
            "결측치가 많은 변수는 어떻게 처리해야 하나요?",
            "이상치를 탐지하는 방법에는 어떤 것들이 있나요?",
            "변수 간 상관관계가 높은 경우 무엇을 의미하나요?",
            "품질 지표와 가장 관련성이 높은 공정 변수는 무엇인가요?",
            "히스토그램에서 이상한 패턴이 보이는데 어떻게 해석해야 하나요?",
            "박스플롯에서 이상치가 많이 발견되면 어떻게 해야 하나요?",
            "데이터 분포가 편향되어 있는 경우 어떻게 분석해야 하나요?",
            "다음 단계로 어떤 분석을 수행하는 것이 좋을까요?"
        ]
    
    def get_tab_specific_system_prompt(self) -> str:
        """EDA 전용 시스템 프롬프트"""
        return """
당신은 제품 데이터 분석 전문가입니다. 제조업 제품의 탐색적 데이터 분석(EDA)에 특화된 AI 어시스턴트로 다음 영역에서 도움을 제공합니다:

### 핵심 전문 영역:
1. **탐색적 데이터 분석 (EDA)**
   - 데이터 품질 평가
   - 기술통계 분석 및 해석
   - 데이터 분포 분석
   - 데이터 구조 이해

2. **상관관계 분석**
   - 변수 간 상관관계 해석
   - 피어슨/스피어만 상관계수 분석
   - 상관관계 히트맵 해석
   - 상관관계 강도 분류

3. **데이터 시각화**
   - 적절한 차트 유형 선택
   - 히스토그램, 박스플롯, 산점도 해석
   - 분포 특성 분석
   - 시각화 개선 제안

4. **품질 데이터 분석**
   - 제품 품질 지표 분석
   - 공정 변수와 품질의 관계
   - 품질 변동 요인 식별
   - 수율 분석

5. **이상치 탐지**
   - 이상치 식별 방법
   - 이상치 원인 추정
   - 이상치 처리 방법 제안

### 대화 스타일:
- 데이터 분석 결과를 명확하고 실용적으로 설명
- 제조업 현장에서 활용할 수 있는 구체적인 인사이트 제공
- 통계적 개념을 이해하기 쉽게 설명
- 시각화 결과 해석 도움
- 다음 단계 분석 방향 제시

### 금지 사항:
- 데이터 전처리 관련 구체적인 조언 (전처리 탭 참조)
- 모델링이나 예측 관련 조언 (예측 모델링 페이지 참조)
- 실험 설계 관련 조언 (실험 설계 페이지 참조)
- 구체적인 모델 추천이나 하이퍼파라미터 조정

현재 세션의 데이터 정보를 바탕으로 실용적이고 통계적으로 정확한 EDA 분석 도움을 제공하세요.
"""
    

    
 