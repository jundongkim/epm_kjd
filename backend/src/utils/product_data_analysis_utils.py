"""
DX-AI Manufacturing Copilot - 제품 데이터 분석 유틸리티

데이터 분석과 전처리 결과 표시를 위한 유틸리티 함수들
"""

import pandas as pd
import numpy as np
import streamlit as st
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass
from src.copilot.product_data_analysis_engine import (
    PreprocessingResult, 
    CorrelationResult, 
    OutlierResult,
    DataAnalysisEngine,
    DataPreprocessingEngine
)


class DataAnalysisFormatter:
    """데이터 분석 결과 포맷팅 클래스"""
    
    @staticmethod
    def get_correlation_strength(abs_corr: float) -> str:
        """상관계수 절댓값에 따른 강도 분류
        
        Args:
            abs_corr: 상관계수 절댓값
            
        Returns:
            str: 상관관계 강도 설명
        """
        if abs_corr >= 0.9:
            return "매우 강함"
        elif abs_corr >= 0.7:
            return "강함"
        elif abs_corr >= 0.5:
            return "보통"
        elif abs_corr >= 0.3:
            return "약함"
        else:
            return "매우 약함"
    
    @staticmethod
    def format_correlation_pairs(correlation_matrix: pd.DataFrame, threshold: float = 0.7) -> List[Dict[str, Any]]:
        """상관관계 행렬에서 높은 상관관계 쌍을 포맷팅
        
        Args:
            correlation_matrix: 상관관계 행렬
            threshold: 임계값
            
        Returns:
            List[Dict]: 포맷된 상관관계 쌍 리스트
        """
        high_corr_pairs = []
        for i in range(len(correlation_matrix.columns)):
            for j in range(i+1, len(correlation_matrix.columns)):
                corr_val = correlation_matrix.iloc[i, j]
                if abs(corr_val) > threshold:
                    high_corr_pairs.append({
                        '변수1': correlation_matrix.columns[i],
                        '변수2': correlation_matrix.columns[j],
                        '상관계수': corr_val,
                        '상관강도': DataAnalysisFormatter.get_correlation_strength(abs(corr_val))
                    })
        
        return high_corr_pairs
    
    @staticmethod
    def format_basic_statistics(stats_dict: Dict[str, Dict[str, float]]) -> pd.DataFrame:
        """기본 통계를 DataFrame으로 포맷팅
        
        Args:
            stats_dict: 통계 딕셔너리
            
        Returns:
            pd.DataFrame: 포맷된 통계 테이블
        """
        if not stats_dict:
            return pd.DataFrame()
        
        formatted_stats = {}
        for col, stats in stats_dict.items():
            formatted_stats[col] = {
                '평균': round(stats.get('mean', 0), 3),
                '표준편차': round(stats.get('std', 0), 3),
                '최솟값': round(stats.get('min', 0), 3),
                '최댓값': round(stats.get('max', 0), 3),
                '중앙값': round(stats.get('median', 0), 3),
                '개수': int(stats.get('count', 0)),
                '결측치': int(stats.get('null_count', 0))
            }
        
        return pd.DataFrame(formatted_stats).T
    
    @staticmethod
    def format_outlier_summary(outlier_info: Dict[str, Dict[str, Any]]) -> pd.DataFrame:
        """이상치 정보를 DataFrame으로 포맷팅
        
        Args:
            outlier_info: 이상치 정보 딕셔너리
            
        Returns:
            pd.DataFrame: 포맷된 이상치 테이블
        """
        if not outlier_info:
            return pd.DataFrame()
        
        formatted_outliers = {}
        for col, info in outlier_info.items():
            formatted_outliers[col] = {
                '이상치 개수': info.get('count', 0),
                '이상치 비율(%)': round(info.get('percentage', 0), 2),
                '하한값': round(info.get('lower_bound', 0), 3) if info.get('lower_bound') is not None else 'N/A',
                '상한값': round(info.get('upper_bound', 0), 3) if info.get('upper_bound') is not None else 'N/A'
            }
        
        return pd.DataFrame(formatted_outliers).T


class PreprocessingResultsDisplayer:
    """전처리 결과 표시 클래스"""
    
    @staticmethod
    def display_preprocessing_results(results: PreprocessingResult) -> None:
        """전처리 결과를 시각적으로 표시
        
        Args:
            results: 전처리 결과 객체
        """
        st.markdown("#### 🔧 데이터 전처리 결과")
        
        # 전처리 요약
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("원본 데이터 크기", f"{results.original_shape[0]} × {results.original_shape[1]}")
        with col2:
            st.metric("처리된 데이터 크기", f"{results.final_shape[0]} × {results.final_shape[1]}")
        with col3:
            removed_count = len(results.removed_columns)
            st.metric("제거된 컬럼 수", removed_count)
        
        # 전처리 단계별 설명
        if results.steps:
            st.markdown("**📋 전처리 단계:**")
            for i, step in enumerate(results.steps, 1):
                st.write(f"{i}. {step}")
        
        # 경고사항
        if results.warnings:
            st.markdown("**⚠️ 주의사항:**")
            for warning in results.warnings:
                st.warning(warning)
        
        # 제거된 컬럼
        if results.removed_columns:
            st.markdown("**🗑️ 제거된 컬럼:**")
            st.write(", ".join(results.removed_columns))
        
        # 이상치 정보
        if results.outlier_info:
            st.markdown("**🔍 이상치 정보:**")
            outlier_df = DataAnalysisFormatter.format_outlier_summary(results.outlier_info)
            st.dataframe(outlier_df, use_container_width=True)
        
        # 다중공선성 정보
        if results.high_correlation_pairs:
            st.markdown("**🔗 높은 상관관계 변수 쌍:**")
            corr_df = pd.DataFrame(results.high_correlation_pairs)
            if not corr_df.empty:
                corr_df['correlation'] = corr_df['correlation'].round(3)
                st.dataframe(corr_df, use_container_width=True)
        
        # 처리된 데이터 미리보기
        st.markdown("**👀 처리된 데이터 미리보기:**")
        st.dataframe(results.processed_data.head(10), use_container_width=True)
        
        # 성공률 표시
        if results.success_rate < 100:
            st.markdown(f"**📊 전처리 성공률: {results.success_rate:.1f}%**")
            if results.success_rate < 80:
                st.warning("전처리 성공률이 낮습니다. 경고사항을 확인해주세요.")
        else:
            st.success("✅ 모든 전처리 단계가 성공적으로 완료되었습니다!")
    
    @staticmethod
    def display_data_quality_metrics(quality_info: Dict[str, Any]) -> None:
        """데이터 품질 메트릭 표시
        
        Args:
            quality_info: 데이터 품질 정보
        """
        st.markdown("#### 📊 데이터 품질 평가")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("총 행 수", quality_info.get('total_rows', 0))
        
        with col2:
            st.metric("총 컬럼 수", quality_info.get('total_columns', 0))
        
        with col3:
            completeness = quality_info.get('completeness_rate', 0)
            st.metric("완성도", f"{completeness:.1f}%")
        
        with col4:
            duplicates = quality_info.get('duplicate_rows', 0)
            st.metric("중복 행", duplicates)
        
        # 완성도에 따른 품질 평가
        if completeness >= 95:
            st.success("🟢 데이터 품질이 우수합니다.")
        elif completeness >= 80:
            st.info("🟡 데이터 품질이 양호합니다.")
        else:
            st.warning("🔴 데이터 품질 개선이 필요합니다.")
    
    @staticmethod
    def display_correlation_analysis(correlation_result: CorrelationResult) -> None:
        """상관관계 분석 결과 표시
        
        Args:
            correlation_result: 상관관계 분석 결과
        """
        st.markdown("#### 🔗 상관관계 분석 결과")
        
        # 상관계수 행렬 표시
        st.markdown("**상관계수 행렬:**")
        st.dataframe(correlation_result.correlation_matrix.round(3), use_container_width=True)
        
        # 높은 상관관계 요약
        high_corr_count = correlation_result.total_pairs_above_threshold
        threshold = correlation_result.threshold
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("높은 상관관계 쌍", high_corr_count)
        with col2:
            st.metric("임계값", threshold)
        
        # 높은 상관관계 상세
        if high_corr_count > 0:
            st.markdown(f"**📊 임계값 {threshold} 이상의 상관관계:**")
            high_corr_df = pd.DataFrame(correlation_result.high_correlation_pairs)
            if not high_corr_df.empty:
                # 컬럼명 한글화
                display_df = high_corr_df.copy()
                display_df.columns = ['변수1', '변수2', '상관계수', '절댓값', '상관강도']
                display_df['상관계수'] = display_df['상관계수'].round(3)
                display_df['절댓값'] = display_df['절댓값'].round(3)
                st.dataframe(display_df, use_container_width=True)
        else:
            st.info(f"임계값 {threshold} 이상의 상관관계가 없습니다.")


class DataAnalysisHelper:
    """데이터 분석 도우미 클래스"""
    
    @staticmethod
    def identify_date_like_columns(df: pd.DataFrame, sample_size: int = 10) -> List[str]:
        """날짜 형식일 가능성이 있는 컬럼 식별
        
        Args:
            df: 데이터프레임
            sample_size: 샘플 크기
            
        Returns:
            List[str]: 날짜 형식일 가능성이 있는 컬럼 리스트
        """
        date_columns = []
        
        for col in df.columns:
            if df[col].dtype == 'object':
                sample_values = df[col].dropna().head(sample_size)
                
                if len(sample_values) == 0:
                    continue
                
                date_count = 0
                for value in sample_values:
                    if isinstance(value, str):
                        try:
                            pd.to_datetime(value, errors='raise')
                            date_count += 1
                        except (ValueError, TypeError):
                            continue
                
                # 50% 이상이 날짜 형식이면 날짜 컬럼으로 판단
                if date_count / len(sample_values) >= 0.5:
                    date_columns.append(col)
        
        return date_columns
    
    @staticmethod
    def get_column_type_summary(df: pd.DataFrame) -> Dict[str, List[str]]:
        """컬럼 타입별 요약 정보
        
        Args:
            df: 데이터프레임
            
        Returns:
            Dict[str, List[str]]: 타입별 컬럼 리스트
        """
        summary = {
            'numeric': [],
            'categorical': [],
            'datetime': [],
            'boolean': [],
            'text': []
        }
        
        for col in df.columns:
            dtype = df[col].dtype
            
            if pd.api.types.is_numeric_dtype(dtype):
                summary['numeric'].append(col)
            elif pd.api.types.is_bool_dtype(dtype):
                summary['boolean'].append(col)
            elif pd.api.types.is_datetime64_any_dtype(dtype):
                summary['datetime'].append(col)
            elif dtype == 'object':
                # 고유값이 적으면 범주형, 많으면 텍스트로 분류
                unique_count = df[col].nunique()
                total_count = len(df[col].dropna())
                
                if total_count == 0:
                    summary['text'].append(col)
                elif unique_count / total_count <= 0.1:  # 고유값 비율이 10% 이하
                    summary['categorical'].append(col)
                else:
                    # 날짜 형식인지 확인
                    if col in DataAnalysisHelper.identify_date_like_columns(df):
                        summary['datetime'].append(col)
                    else:
                        summary['text'].append(col)
            else:
                summary['text'].append(col)
        
        return summary
    
    @staticmethod
    def generate_data_summary_report(df: pd.DataFrame) -> str:
        """데이터 요약 리포트 생성
        
        Args:
            df: 데이터프레임
            
        Returns:
            str: 요약 리포트 텍스트
        """
        type_summary = DataAnalysisHelper.get_column_type_summary(df)
        missing_info = df.isnull().sum()
        
        report = f"""
# 데이터 분석 요약 리포트

## 기본 정보
- **데이터 크기**: {df.shape[0]}행 × {df.shape[1]}열
- **총 결측치**: {missing_info.sum()}개
- **메모리 사용량**: {df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB

## 컬럼 유형별 분포
- **수치형**: {len(type_summary['numeric'])}개
- **범주형**: {len(type_summary['categorical'])}개  
- **날짜형**: {len(type_summary['datetime'])}개
- **불린형**: {len(type_summary['boolean'])}개
- **텍스트형**: {len(type_summary['text'])}개

## 데이터 품질
- **완성도**: {((df.shape[0] * df.shape[1] - missing_info.sum()) / (df.shape[0] * df.shape[1]) * 100):.1f}%
- **중복 행**: {df.duplicated().sum()}개
"""
        
        # 결측치가 많은 컬럼 상위 5개
        top_missing = missing_info[missing_info > 0].sort_values(ascending=False).head(5)
        if not top_missing.empty:
            report += "\n## 결측치가 많은 컬럼 (상위 5개)\n"
            for col, count in top_missing.items():
                percentage = (count / len(df)) * 100
                report += f"- **{col}**: {count}개 ({percentage:.1f}%)\n"
        
        return report
    
    @staticmethod
    def get_modeling_readiness_score(preprocessing_result: PreprocessingResult) -> Tuple[float, List[str]]:
        """모델링 준비 상태 점수 계산
        
        Args:
            preprocessing_result: 전처리 결과
            
        Returns:
            Tuple[float, List[str]]: (준비도 점수, 개선 권장사항)
        """
        score = 0
        max_score = 100
        recommendations = []
        
        # 1. 데이터 크기 (20점)
        final_rows = preprocessing_result.final_shape[0]
        final_cols = preprocessing_result.final_shape[1]
        
        if final_rows >= 1000:
            score += 20
        elif final_rows >= 500:
            score += 15
            recommendations.append("데이터 양이 부족합니다. 더 많은 데이터 수집을 권장합니다.")
        elif final_rows >= 100:
            score += 10
            recommendations.append("데이터 양이 매우 부족합니다. 추가 데이터 수집이 필요합니다.")
        else:
            recommendations.append("데이터 양이 극히 부족합니다. 모델링이 어려울 수 있습니다.")
        
        # 2. 특성 수 (15점)
        if 5 <= final_cols <= 50:
            score += 15
        elif final_cols > 50:
            score += 10
            recommendations.append("특성이 많습니다. 차원 축소나 특성 선택을 고려하세요.")
        elif final_cols >= 2:
            score += 5
            recommendations.append("특성이 부족합니다. 특성 엔지니어링을 고려하세요.")
        else:
            recommendations.append("특성이 극히 부족합니다. 모델링이 불가능할 수 있습니다.")
        
        # 3. 전처리 성공률 (25점)
        success_rate = preprocessing_result.success_rate
        score += (success_rate / 100) * 25
        
        if success_rate < 80:
            recommendations.append("전처리 성공률이 낮습니다. 경고사항을 해결하세요.")
        
        # 4. 결측치 처리 (15점)
        if preprocessing_result.imputer is not None:
            score += 15
        else:
            score += 5  # 결측치가 없었던 경우
        
        # 5. 이상치 처리 (10점)
        if preprocessing_result.outlier_info:
            total_outlier_percentage = sum(
                info['percentage'] for info in preprocessing_result.outlier_info.values()
            )
            if total_outlier_percentage < 5:
                score += 10
            elif total_outlier_percentage < 15:
                score += 7
                recommendations.append("이상치 비율이 높습니다. 이상치 처리를 고려하세요.")
            else:
                score += 3
                recommendations.append("이상치 비율이 매우 높습니다. 데이터 검토가 필요합니다.")
        else:
            score += 10  # 이상치가 없었던 경우
        
        # 6. 다중공선성 (15점)
        if preprocessing_result.high_correlation_pairs:
            high_corr_count = len(preprocessing_result.high_correlation_pairs)
            if high_corr_count == 0:
                score += 15
            elif high_corr_count <= 3:
                score += 10
                recommendations.append("일부 높은 상관관계 변수가 있습니다. 검토를 권장합니다.")
            else:
                score += 5
                recommendations.append("다중공선성 문제가 있습니다. 변수 선택이 필요합니다.")
        else:
            score += 15  # 상관관계 분석이 수행되지 않았거나 문제없음
        
        return score, recommendations


# 편의 함수들
def get_correlation_strength(abs_corr: float) -> str:
    """상관계수 절댓값에 따른 강도 분류 (편의 함수)"""
    return DataAnalysisFormatter.get_correlation_strength(abs_corr)


def display_preprocessing_results(results: PreprocessingResult) -> None:
    """전처리 결과 표시 (편의 함수)"""
    PreprocessingResultsDisplayer.display_preprocessing_results(results)


def format_correlation_pairs(correlation_matrix: pd.DataFrame, threshold: float = 0.7) -> List[Dict[str, Any]]:
    """상관관계 쌍 포맷팅 (편의 함수)"""
    return DataAnalysisFormatter.format_correlation_pairs(correlation_matrix, threshold)


def generate_analysis_summary(df: pd.DataFrame) -> str:
    """데이터 분석 요약 생성 (편의 함수)"""
    return DataAnalysisHelper.generate_data_summary_report(df)


def calculate_modeling_readiness(preprocessing_result: PreprocessingResult) -> Tuple[float, List[str]]:
    """모델링 준비도 계산 (편의 함수)"""
    return DataAnalysisHelper.get_modeling_readiness_score(preprocessing_result) 