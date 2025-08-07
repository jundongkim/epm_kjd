"""
DX-AI Manufacturing Copilot - 제품 데이터 전처리 전용 챗 매니저

데이터 전처리 및 모델링 준비에 특화된 AI 어시스턴트 기능을 제공합니다.
"""

import streamlit as st
from typing import Dict, Any, List
from .base_tab_chat import BaseTabChatManager


class ProductDataPreprocessingChatManager(BaseTabChatManager):
    """제품 데이터 전처리 전용 챗 매니저"""
    
    def __init__(self, chat_manager):
        super().__init__(
            tab_name="제품 데이터 전처리",
            chat_manager=chat_manager
        )
    
    def format_context_data(self, data: Dict[str, Any], date_filter: str) -> str:
        """전처리 전용 컨텍스트 데이터 포맷팅"""
        if not data:
            return "현재 전처리할 데이터가 없습니다."
        
        summary = []
        
        # 데이터 소스 정보
        if 'data_info' in data:
            data_info = data['data_info']
            summary.append(f"📊 현재 데이터 정보:")
            summary.append(f"  - 데이터 소스: {data_info.get('data_source', '알 수 없음')}")
            summary.append(f"  - 전처리 상태: {'완료' if data_info.get('is_preprocessed', False) else '원본 데이터'}")
            summary.append(f"  - 원본 크기: {data_info.get('original_data_shape', 'N/A')}")
            summary.append(f"  - 현재 크기: {data_info.get('current_data_shape', 'N/A')}")
        
        # 현재 데이터 상세 정보
        if 'data_summary' in data:
            data_summary = data['data_summary']
            summary.append(f"\n📈 데이터 구조:")
            summary.append(f"  - 행 수: {data_summary.get('rows', 'N/A'):,}")
            summary.append(f"  - 전체 컬럼 수: {len(data_summary.get('columns', []))}")
            summary.append(f"  - 수치형 컬럼: {len(data_summary.get('numeric_columns', []))}개")
            summary.append(f"  - 컬럼 목록: {', '.join(data_summary.get('columns', [])[:10])}{'...' if len(data_summary.get('columns', [])) > 10 else ''}")
            
            # 기본 통계 정보 (처음 3개 수치형 컬럼)
            basic_stats = data_summary.get('basic_statistics', {})
            if basic_stats:
                summary.append(f"\n📊 주요 통계 (상위 3개 변수):")
                for i, (col, stats) in enumerate(list(basic_stats.items())[:3]):
                    summary.append(f"  • {col}:")
                    summary.append(f"    - 평균: {stats.get('mean', 0):.2f}, 표준편차: {stats.get('std', 0):.2f}")
                    summary.append(f"    - 범위: {stats.get('min', 0):.2f} ~ {stats.get('max', 0):.2f}")
            
            # 결측치 정보 (전처리에서 중요)
            missing_values = data_summary.get('missing_values', {})
            total_missing = sum(missing_values.values())
            if total_missing > 0:
                summary.append(f"\n❓ 결측치 현황:")
                summary.append(f"  - 총 결측치: {total_missing:,}개")
                missing_cols = [(col, count) for col, count in missing_values.items() if count > 0]
                missing_cols.sort(key=lambda x: x[1], reverse=True)
                for col, count in missing_cols[:5]:
                    percentage = (count / data_summary.get('rows', 1)) * 100
                    summary.append(f"  • {col}: {count}개 ({percentage:.1f}%)")
                if len(missing_cols) > 5:
                    summary.append(f"  • 기타 {len(missing_cols) - 5}개 컬럼에도 결측치 존재")
            else:
                summary.append(f"\n✅ 결측치: 없음")
            
            # 범주형 변수 정보
            categorical_info = data_summary.get('categorical_info', {})
            if categorical_info:
                summary.append(f"\n📝 범주형 변수: {len(categorical_info)}개")
                for col, info in list(categorical_info.items())[:3]:
                    summary.append(f"  • {col}: {info.get('unique_count', 'N/A')}개 고유값 (최빈값: {info.get('most_frequent', 'N/A')})")
                if len(categorical_info) > 3:
                    summary.append(f"  • 기타 {len(categorical_info) - 3}개 범주형 변수")
        
        # 데이터 품질 정보
        if 'data_quality' in data:
            quality = data['data_quality']
            summary.append(f"\n🔍 데이터 품질:")
            summary.append(f"  - 중복 행: {quality.get('duplicate_rows', 0)}개")
            summary.append(f"  - 완전한 행: {quality.get('complete_rows', 0)}개")
            summary.append(f"  - 완성도: {quality.get('completeness_rate', 0):.1f}%")
            
            # 품질 등급 추가
            completeness_rate = quality.get('completeness_rate', 0)
            if completeness_rate >= 95:
                quality_grade = "우수"
            elif completeness_rate >= 85:
                quality_grade = "양호"
            elif completeness_rate >= 70:
                quality_grade = "보통"
            else:
                quality_grade = "개선필요"
            summary.append(f"  - 품질 등급: {quality_grade}")
        
        # 샘플 데이터 (상위 3행)
        if 'sample_data' in data:
            sample_data = data['sample_data']
            if sample_data:
                summary.append(f"\n📋 데이터 샘플 (상위 3행):")
                for i, row in enumerate(sample_data, 1):
                    summary.append(f"  행 {i}: " + ", ".join([f"{k}={v}" for k, v in list(row.items())[:5]]))
        
        # 전처리 결과 정보
        if 'preprocessing_results' in data:
            results = data['preprocessing_results']
            summary.append(f"\n🔧 전처리 결과 상세:")
            
            # 데이터 변화량
            if 'data_reduction' in results:
                reduction = results['data_reduction']
                summary.append(f"  📉 데이터 변화:")
                summary.append(f"    - 제거된 행: {reduction.get('rows_removed', 0)}개")
                summary.append(f"    - 제거된 컬럼: {reduction.get('columns_removed', 0)}개")
                summary.append(f"    - 데이터 보존율: {reduction.get('data_retention_rate', 0):.1f}%")
            
            # 품질 개선사항
            quality_improvements = results.get('quality_improvements', [])
            if quality_improvements:
                summary.append(f"  ✨ 품질 개선:")
                for improvement in quality_improvements:
                    summary.append(f"    • {improvement}")
            
            # 성공 메트릭스
            if 'success_metrics' in results:
                metrics = results['success_metrics']
                summary.append(f"  📈 성능 지표:")
                summary.append(f"    - 데이터 완성도: {metrics.get('data_completeness', 0):.1f}%")
                summary.append(f"    - 특성 수: {metrics.get('feature_count', 0)}개")
                summary.append(f"    - 샘플 수: {metrics.get('sample_count', 0):,}개")
                summary.append(f"    - 전처리 성공률: {metrics.get('preprocessing_success_rate', 0):.1f}%")
            
            # 이상치 정보
            if results.get('has_outliers', False):
                summary.append(f"  🔍 이상치 분석:")
                outlier_summary = results.get('outlier_summary', {})
                if outlier_summary:
                    for col, info in list(outlier_summary.items())[:3]:
                        if isinstance(info, dict):
                            summary.append(f"    • {col}: {info.get('count', 0)}개 ({info.get('percentage', 0):.1f}%)")
                        else:
                            summary.append(f"    • {col}: {info:.1f}%")
                
                recommendation = results.get('outlier_recommendation', '')
                if recommendation:
                    summary.append(f"    📋 권장사항: {recommendation}")
            
            # 다중공선성 정보
            if results.get('has_high_correlation', False):
                summary.append(f"  🔗 다중공선성 분석:")
                high_corr_count = results.get('high_correlation_count', 0)
                summary.append(f"    - 높은 상관관계 쌍: {high_corr_count}개")
                
                high_corr_details = results.get('high_correlation_details', [])
                if high_corr_details:
                    summary.append(f"    주요 상관관계:")
                    for pair in high_corr_details[:3]:
                        summary.append(f"    • {pair.get('var1', '')}-{pair.get('var2', '')}: r={pair.get('correlation', 0):.3f}")
                
                multicollinearity_rec = results.get('multicollinearity_recommendation', '')
                if multicollinearity_rec:
                    summary.append(f"    📋 권장사항: {multicollinearity_rec}")
            
            # 전처리 단계 요약
            processing_steps = results.get('processing_steps', [])
            if processing_steps:
                summary.append(f"  ⚙️ 실행된 단계: {', '.join(processing_steps)}")
            
            # 경고사항
            warnings_count = results.get('warnings_count', 0)
            if warnings_count > 0:
                summary.append(f"  ⚠️ 경고사항: {warnings_count}개")
            
            # 모델링 준비 상태
            if results.get('is_ready_for_modeling', False):
                summary.append(f"  ✅ 모델링 준비 완료")
            else:
                summary.append(f"  ⚠️ 추가 전처리 필요")
        
        # 현재 탭 정보
        current_tab = data.get('current_tab', 'unknown')
        summary.append(f"\n🎯 현재 탭: {current_tab}")
        
        return "\n".join(summary) if summary else "전처리 정보가 없습니다."
    
    def generate_analysis_questions(self) -> List[str]:
        """전처리 전용 추천 질문 목록"""
        return [
            "결측치를 처리하는 방법에는 어떤 것들이 있나요?",
            "이상치를 어떻게 처리해야 하나요?",
            "범주형 변수 인코딩 방법을 설명해주세요.",
            "다중공선성이 문제가 되는 이유는 무엇인가요?",
            "데이터 스케일링이 필요한 경우는 언제인가요?",
            "전처리 후 데이터 품질을 어떻게 검증하나요?",
            "분산이 0인 변수는 왜 제거해야 하나요?",
            "날짜/시간 데이터는 어떻게 처리해야 하나요?",
            "전처리 단계의 순서가 중요한가요?",
            "모델링 전에 추가로 확인해야 할 점은 무엇인가요?",
            "전처리된 데이터의 품질을 평가하는 방법은?",
            "어떤 경우에 데이터 변환이 필요한가요?"
        ]
    
    def get_tab_specific_system_prompt(self) -> str:
        """전처리 전용 시스템 프롬프트"""
        return """
당신은 데이터 전처리 전문가입니다. 제조업 제품 데이터의 전처리 및 모델링 준비에 특화된 AI 어시스턴트로 다음 영역에서 도움을 제공합니다:

### 핵심 전문 영역:
1. **결측치 처리**
   - 결측치 유형 분석
   - 적절한 대체 방법 선택
   - 결측치 패턴 분석
   - 결측치 처리 후 영향 평가

2. **이상치 처리**
   - 이상치 탐지 방법
   - 이상치 원인 분석
   - 이상치 처리 전략
   - 처리 후 데이터 검증

3. **범주형 변수 처리**
   - 레이블 인코딩
   - 원-핫 인코딩
   - 순서형 변수 처리
   - 인코딩 방법 선택 기준

4. **데이터 변환**
   - 정규화 vs 표준화
   - 로그 변환
   - 분포 변환
   - 스케일링 방법 선택

5. **특성 선택**
   - 분산 기반 특성 선택
   - 다중공선성 진단
   - 상관관계 기반 특성 제거
   - 중요도 기반 특성 선택

6. **데이터 품질 검증**
   - 전처리 후 데이터 검증
   - 데이터 완정성 확인
   - 변환 결과 검증
   - 모델링 준비 상태 평가

### 대화 스타일:
- 전처리 방법론을 체계적으로 설명
- 각 처리 방법의 장단점 제시
- 제조업 특성을 고려한 실용적 조언
- 전처리 순서와 주의사항 강조
- 데이터 품질 개선 방안 제시

### 금지 사항:
- 탐색적 데이터 분석 (EDA) 관련 조언 (EDA 탭 참조)
- 모델링이나 예측 관련 조언 (예측 모델링 페이지 참조)
- 실험 설계 관련 조언 (실험 설계 페이지 참조)
- 구체적인 모델 추천이나 하이퍼파라미터 조정

### 전처리 원칙:
- 데이터 손실 최소화
- 도메인 지식 활용
- 변환 과정 기록
- 검증 가능한 방법 사용
- 모델링 목적 고려

현재 세션의 데이터 정보를 바탕으로 실용적이고 통계적으로 정확한 전처리 도움을 제공하세요.
""" 