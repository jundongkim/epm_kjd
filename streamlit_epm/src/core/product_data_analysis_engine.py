"""
DX-AI Manufacturing Copilot - 제품 데이터 분석 엔진

데이터 분석 및 전처리를 위한 핵심 엔진 클래스들
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.impute import SimpleImputer
from scipy import stats
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum


class OutlierDetectionMethod(Enum):
    """이상치 탐지 방법"""
    IQR = "iqr"
    Z_SCORE = "z_score"


class ImputationStrategy(Enum):
    """결측치 대체 전략"""
    MEAN = "mean"
    MEDIAN = "median"
    MODE = "most_frequent"
    CONSTANT = "constant"


@dataclass
class OutlierResult:
    """이상치 탐지 결과"""
    outliers: pd.DataFrame
    lower_bound: Optional[float]
    upper_bound: Optional[float]
    method_used: OutlierDetectionMethod
    outlier_count: int
    outlier_percentage: float


@dataclass
class CorrelationResult:
    """상관관계 분석 결과"""
    correlation_matrix: pd.DataFrame
    high_correlation_pairs: List[Dict[str, Any]]
    threshold: float
    total_pairs_above_threshold: int


@dataclass
class PreprocessingResult:
    """전처리 결과"""
    processed_data: pd.DataFrame
    original_shape: Tuple[int, int]
    final_shape: Tuple[int, int]
    steps: List[str]
    warnings: List[str]
    removed_columns: List[str]
    numeric_columns: List[str]
    categorical_columns: List[str]
    date_columns: List[str]
    outlier_info: Optional[Dict[str, Dict[str, Any]]]
    high_correlation_pairs: Optional[List[Dict[str, Any]]]
    label_encoders: Optional[Dict[str, LabelEncoder]]
    imputer: Optional[SimpleImputer]
    success_rate: float


class DataAnalysisEngine:
    """데이터 분석 엔진"""
    
    def __init__(self):
        self.correlation_threshold = 0.7
        self.outlier_method = OutlierDetectionMethod.IQR
    
    def detect_outliers(self, df: pd.DataFrame, column: str, 
                       method: OutlierDetectionMethod = OutlierDetectionMethod.IQR) -> OutlierResult:
        """이상치 탐지
        
        Args:
            df: 데이터프레임
            column: 분석할 컬럼명
            method: 탐지 방법 (IQR 또는 Z-Score)
            
        Returns:
            OutlierResult: 이상치 탐지 결과
        """
        if column not in df.columns:
            raise ValueError(f"컬럼 '{column}'이 데이터프레임에 존재하지 않습니다.")
        
        if not pd.api.types.is_numeric_dtype(df[column]):
            raise ValueError(f"컬럼 '{column}'은 수치형이 아닙니다.")
        
        # 결측치 제거
        clean_data = df[column].dropna()
        
        if len(clean_data) == 0:
            return OutlierResult(
                outliers=pd.DataFrame(),
                lower_bound=None,
                upper_bound=None,
                method_used=method,
                outlier_count=0,
                outlier_percentage=0.0
            )
        
        if method == OutlierDetectionMethod.IQR:
            Q1 = clean_data.quantile(0.25)
            Q3 = clean_data.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            outliers = df[(df[column] < lower_bound) | (df[column] > upper_bound)]
            
        elif method == OutlierDetectionMethod.Z_SCORE:
            z_scores = np.abs(stats.zscore(clean_data))
            outlier_indices = clean_data.index[z_scores > 3]
            outliers = df.loc[outlier_indices]
            lower_bound = None
            upper_bound = None
        
        else:
            raise ValueError(f"지원하지 않는 이상치 탐지 방법: {method}")
        
        outlier_count = len(outliers)
        outlier_percentage = (outlier_count / len(df)) * 100 if len(df) > 0 else 0
        
        return OutlierResult(
            outliers=outliers,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
            method_used=method,
            outlier_count=outlier_count,
            outlier_percentage=outlier_percentage
        )
    
    def analyze_correlation(self, df: pd.DataFrame, columns: List[str], 
                           threshold: float = 0.7) -> CorrelationResult:
        """상관관계 분석
        
        Args:
            df: 데이터프레임
            columns: 분석할 컬럼 리스트
            threshold: 높은 상관관계 임계값
            
        Returns:
            CorrelationResult: 상관관계 분석 결과
        """
        if not columns:
            raise ValueError("분석할 컬럼이 지정되지 않았습니다.")
        
        # 존재하지 않는 컬럼 확인
        missing_cols = [col for col in columns if col not in df.columns]
        if missing_cols:
            raise ValueError(f"다음 컬럼들이 데이터프레임에 존재하지 않습니다: {missing_cols}")
        
        # 수치형 컬럼만 필터링
        numeric_cols = [col for col in columns if pd.api.types.is_numeric_dtype(df[col])]
        if len(numeric_cols) < 2:
            raise ValueError("상관관계 분석을 위해서는 최소 2개의 수치형 컬럼이 필요합니다.")
        
        # 상관관계 계산
        correlation_matrix = df[numeric_cols].corr()
        
        # 높은 상관관계 찾기
        high_corr_pairs = []
        for i in range(len(correlation_matrix.columns)):
            for j in range(i+1, len(correlation_matrix.columns)):
                corr_val = correlation_matrix.iloc[i, j]
                if abs(corr_val) > threshold:
                    high_corr_pairs.append({
                        'var1': correlation_matrix.columns[i],
                        'var2': correlation_matrix.columns[j],
                        'correlation': corr_val,
                        'abs_correlation': abs(corr_val),
                        'strength': self._get_correlation_strength(abs(corr_val))
                    })
        
        return CorrelationResult(
            correlation_matrix=correlation_matrix,
            high_correlation_pairs=high_corr_pairs,
            threshold=threshold,
            total_pairs_above_threshold=len(high_corr_pairs)
        )
    
    def _get_correlation_strength(self, abs_corr: float) -> str:
        """상관계수 절댓값에 따른 강도 분류"""
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
    
    def get_basic_statistics(self, df: pd.DataFrame, columns: Optional[List[str]] = None) -> Dict[str, Dict[str, float]]:
        """기본 통계 정보 생성
        
        Args:
            df: 데이터프레임
            columns: 분석할 컬럼 리스트 (None이면 모든 수치형 컬럼)
            
        Returns:
            Dict: 컬럼별 기본 통계 정보
        """
        if columns is None:
            columns = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
        else:
            columns = [col for col in columns if col in df.columns and pd.api.types.is_numeric_dtype(df[col])]
        
        basic_statistics = {}
        for col in columns:
            try:
                basic_statistics[col] = {
                    'mean': df[col].mean(),
                    'std': df[col].std(),
                    'min': df[col].min(),
                    'max': df[col].max(),
                    'median': df[col].median(),
                    'count': df[col].count(),
                    'null_count': df[col].isnull().sum()
                }
            except Exception as e:
                basic_statistics[col] = {
                    'mean': 0, 'std': 0, 'min': 0, 'max': 0, 'median': 0,
                    'count': 0, 'null_count': len(df),
                    'error': str(e)
                }
        
        return basic_statistics
    
    def analyze_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """데이터 품질 분석
        
        Args:
            df: 데이터프레임
            
        Returns:
            Dict: 데이터 품질 정보
        """
        duplicate_rows = df.duplicated().sum()
        complete_rows = len(df) - df.isnull().any(axis=1).sum()
        completeness_rate = (complete_rows / len(df)) * 100 if len(df) > 0 else 0
        
        missing_info = {}
        for col in df.columns:
            missing_count = df[col].isnull().sum()
            missing_info[col] = {
                'count': missing_count,
                'percentage': (missing_count / len(df)) * 100 if len(df) > 0 else 0
            }
        
        return {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'duplicate_rows': duplicate_rows,
            'complete_rows': complete_rows,
            'completeness_rate': completeness_rate,
            'missing_info': missing_info,
            'memory_usage': df.memory_usage(deep=True).sum()
        }


class DataPreprocessingEngine:
    """데이터 전처리 엔진"""
    
    def __init__(self):
        self.imputation_strategy = ImputationStrategy.MEAN
        self.outlier_threshold = 0.95  # 상위 5%를 이상치로 간주
        self.correlation_threshold = 0.9  # 다중공선성 임계값
        
    def preprocess_for_modeling(self, df: pd.DataFrame) -> PreprocessingResult:
        """모델링을 위한 종합 데이터 전처리
        
        Args:
            df: 원본 데이터프레임
            
        Returns:
            PreprocessingResult: 전처리 결과
        """
        original_shape = df.shape
        processed_df = df.copy()
        steps = []
        warnings = []
        removed_columns = []
        
        # 1. 날짜/시간 컬럼 처리
        date_columns = self._identify_date_columns(processed_df)
        if date_columns:
            steps.append(f"날짜 컬럼 발견: {date_columns}")
            warnings.append("날짜 컬럼은 모델링에서 제외되었습니다. 필요시 추가 특성 엔지니어링을 수행하세요.")
            processed_df = processed_df.drop(columns=date_columns)
            removed_columns.extend(date_columns)
        
        # 2. 범주형 변수 인코딩
        categorical_columns = self._identify_categorical_columns(processed_df)
        label_encoders = {}
        if categorical_columns:
            steps.append(f"범주형 컬럼 발견: {categorical_columns}")
            
            for col in categorical_columns:
                le = LabelEncoder()
                non_null_mask = processed_df[col].notna()
                if non_null_mask.sum() > 0:
                    try:
                        processed_df.loc[non_null_mask, col] = le.fit_transform(processed_df.loc[non_null_mask, col])
                        label_encoders[col] = le
                    except Exception as e:
                        warnings.append(f"컬럼 '{col}' 인코딩 실패: {str(e)}")
            
            if label_encoders:
                steps.append("범주형 변수를 레이블 인코딩했습니다.")
        
        # 3. 수치형 컬럼 필터링
        numeric_columns = self._identify_numeric_columns(processed_df)
        if not numeric_columns:
            warnings.append("수치형 데이터가 없어서 추가 전처리를 수행할 수 없습니다.")
            return PreprocessingResult(
                processed_data=processed_df,
                original_shape=original_shape,
                final_shape=processed_df.shape,
                steps=steps,
                warnings=warnings,
                removed_columns=removed_columns,
                numeric_columns=numeric_columns,
                categorical_columns=categorical_columns,
                date_columns=date_columns,
                outlier_info=None,
                high_correlation_pairs=None,
                label_encoders=label_encoders if label_encoders else None,
                imputer=None,
                success_rate=0.0
            )
        
        # 4. 결측치 처리
        imputer = None
        missing_columns = self._identify_missing_columns(processed_df[numeric_columns])
        if missing_columns:
            steps.append(f"결측치 발견: {dict(processed_df[missing_columns].isnull().sum())}")
            
            try:
                imputer = SimpleImputer(strategy=self.imputation_strategy.value)
                processed_df[missing_columns] = imputer.fit_transform(processed_df[missing_columns])
                steps.append(f"결측치를 {self.imputation_strategy.value}으로 대체했습니다.")
            except Exception as e:
                warnings.append(f"결측치 처리 실패: {str(e)}")
        
        # 5. 분산이 0인 컬럼 제거
        zero_variance_cols = self._identify_zero_variance_columns(processed_df[numeric_columns])
        if zero_variance_cols:
            processed_df = processed_df.drop(columns=zero_variance_cols)
            steps.append(f"분산이 0인 컬럼 제거: {zero_variance_cols}")
            warnings.append("분산이 0인 변수들은 모델링에 기여하지 않아 제거되었습니다.")
            removed_columns.extend(zero_variance_cols)
            numeric_columns = [col for col in numeric_columns if col not in zero_variance_cols]
        
        # 6. 이상치 탐지
        outlier_info = self._detect_outliers_for_all_columns(processed_df, numeric_columns)
        if outlier_info:
            steps.append(f"이상치 탐지 완료: {len(outlier_info)}개 컬럼에서 이상치 발견")
            warnings.append("이상치가 발견되었습니다. 모델링 전에 처리 여부를 결정하세요.")
        
        # 7. 다중공선성 확인
        high_correlation_pairs = None
        if len(numeric_columns) > 1:
            high_correlation_pairs = self._check_multicollinearity(processed_df[numeric_columns])
            if high_correlation_pairs:
                steps.append(f"높은 상관관계 변수 쌍 발견: {len(high_correlation_pairs)}개")
                warnings.append("상관관계가 매우 높은 변수들이 있습니다. 다중공선성을 고려하여 일부 변수 제거를 고려하세요.")
        
        # 성공률 계산
        success_operations = len(steps) - len(warnings)
        total_operations = len(steps) if steps else 1
        success_rate = (success_operations / total_operations) * 100
        
        return PreprocessingResult(
            processed_data=processed_df,
            original_shape=original_shape,
            final_shape=processed_df.shape,
            steps=steps,
            warnings=warnings,
            removed_columns=removed_columns,
            numeric_columns=numeric_columns,
            categorical_columns=categorical_columns,
            date_columns=date_columns,
            outlier_info=outlier_info,
            high_correlation_pairs=high_correlation_pairs,
            label_encoders=label_encoders if label_encoders else None,
            imputer=imputer,
            success_rate=success_rate
        )
    
    def _identify_date_columns(self, df: pd.DataFrame) -> List[str]:
        """날짜/시간 컬럼 식별"""
        date_columns = []
        for col in df.columns:
            if df[col].dtype == 'object':
                sample_values = df[col].dropna().head(5)
                date_count = 0
                for val in sample_values:
                    try:
                        pd.to_datetime(val, errors='raise')
                        date_count += 1
                    except:
                        continue
                
                if date_count >= 3:  # 대부분이 날짜 형식
                    date_columns.append(col)
        
        return date_columns
    
    def _identify_categorical_columns(self, df: pd.DataFrame) -> List[str]:
        """범주형 컬럼 식별"""
        categorical_columns = []
        for col in df.columns:
            if df[col].dtype == 'object':
                categorical_columns.append(col)
        
        return categorical_columns
    
    def _identify_numeric_columns(self, df: pd.DataFrame) -> List[str]:
        """수치형 컬럼 식별"""
        numeric_columns = []
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                numeric_columns.append(col)
        
        return numeric_columns
    
    def _identify_missing_columns(self, df: pd.DataFrame) -> List[str]:
        """결측치가 있는 컬럼 식별"""
        missing_info = df.isnull().sum()
        return missing_info[missing_info > 0].index.tolist()
    
    def _identify_zero_variance_columns(self, df: pd.DataFrame) -> List[str]:
        """분산이 0인 컬럼 식별"""
        zero_variance_cols = []
        for col in df.columns:
            try:
                if df[col].var() == 0:
                    zero_variance_cols.append(col)
            except:
                continue
        
        return zero_variance_cols
    
    def _detect_outliers_for_all_columns(self, df: pd.DataFrame, columns: List[str]) -> Optional[Dict[str, Dict[str, Any]]]:
        """모든 수치형 컬럼에 대해 이상치 탐지"""
        analysis_engine = DataAnalysisEngine()
        outlier_info = {}
        
        for col in columns:
            try:
                result = analysis_engine.detect_outliers(df, col, OutlierDetectionMethod.IQR)
                if result.outlier_count > 0:
                    outlier_info[col] = {
                        'count': result.outlier_count,
                        'percentage': result.outlier_percentage,
                        'lower_bound': result.lower_bound,
                        'upper_bound': result.upper_bound
                    }
            except Exception as e:
                continue
        
        return outlier_info if outlier_info else None
    
    def _check_multicollinearity(self, df: pd.DataFrame) -> Optional[List[Dict[str, Any]]]:
        """다중공선성 확인"""
        try:
            correlation_matrix = df.corr()
            high_corr_pairs = []
            
            for i in range(len(correlation_matrix.columns)):
                for j in range(i+1, len(correlation_matrix.columns)):
                    corr_val = correlation_matrix.iloc[i, j]
                    if abs(corr_val) > self.correlation_threshold:
                        high_corr_pairs.append({
                            'var1': correlation_matrix.columns[i],
                            'var2': correlation_matrix.columns[j],
                            'correlation': corr_val
                        })
            
            return high_corr_pairs if high_corr_pairs else None
        
        except Exception as e:
            return None
    
    def remove_outliers(self, df: pd.DataFrame, column: str, 
                       method: OutlierDetectionMethod = OutlierDetectionMethod.IQR) -> Tuple[pd.DataFrame, int]:
        """이상치 제거
        
        Args:
            df: 데이터프레임
            column: 처리할 컬럼명
            method: 탐지 방법
            
        Returns:
            Tuple[pd.DataFrame, int]: (처리된 데이터프레임, 제거된 행 수)
        """
        analysis_engine = DataAnalysisEngine()
        result = analysis_engine.detect_outliers(df, column, method)
        
        if result.outlier_count == 0:
            return df, 0
        
        # 이상치 행 제거
        outlier_indices = result.outliers.index
        cleaned_df = df.drop(outlier_indices)
        
        return cleaned_df, len(outlier_indices)
    
    def remove_highly_correlated_features(self, df: pd.DataFrame, threshold: float = 0.9) -> Tuple[pd.DataFrame, List[str]]:
        """높은 상관관계 특성 제거
        
        Args:
            df: 데이터프레임
            threshold: 상관관계 임계값
            
        Returns:
            Tuple[pd.DataFrame, List[str]]: (처리된 데이터프레임, 제거된 컬럼 리스트)
        """
        numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
        
        if len(numeric_cols) < 2:
            return df, []
        
        correlation_matrix = df[numeric_cols].corr().abs()
        
        # 상삼각행렬만 고려 (중복 제거)
        upper_triangle = correlation_matrix.where(
            np.triu(np.ones(correlation_matrix.shape), k=1).astype(bool)
        )
        
        # 높은 상관관계를 가진 컬럼 찾기
        to_drop = [column for column in upper_triangle.columns if any(upper_triangle[column] > threshold)]
        
        # 컬럼 제거
        processed_df = df.drop(columns=to_drop)
        
        return processed_df, to_drop


class ProductDataAnalysisEngine:
    """제품 데이터 분석 통합 엔진"""
    
    def __init__(self):
        self.analysis_engine = DataAnalysisEngine()
        self.preprocessing_engine = DataPreprocessingEngine()
    
    def perform_comprehensive_analysis(self, df: pd.DataFrame, 
                                     correlation_columns: Optional[List[str]] = None,
                                     correlation_threshold: float = 0.7) -> Dict[str, Any]:
        """종합 데이터 분석 수행
        
        Args:
            df: 데이터프레임
            correlation_columns: 상관관계 분석할 컬럼 리스트
            correlation_threshold: 상관관계 임계값
            
        Returns:
            Dict: 종합 분석 결과
        """
        results = {}
        
        # 1. 기본 정보
        results['basic_info'] = {
            'shape': df.shape,
            'columns': list(df.columns),
            'dtypes': df.dtypes.astype(str).to_dict()
        }
        
        # 2. 데이터 품질 분석
        results['data_quality'] = self.analysis_engine.analyze_data_quality(df)
        
        # 3. 기본 통계
        results['basic_statistics'] = self.analysis_engine.get_basic_statistics(df)
        
        # 4. 상관관계 분석
        if correlation_columns:
            try:
                results['correlation_analysis'] = self.analysis_engine.analyze_correlation(
                    df, correlation_columns, correlation_threshold
                )
            except Exception as e:
                results['correlation_analysis'] = {'error': str(e)}
        
        # 5. 이상치 분석 (수치형 컬럼만)
        numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
        outlier_results = {}
        for col in numeric_cols[:5]:  # 처음 5개 컬럼만
            try:
                outlier_result = self.analysis_engine.detect_outliers(df, col)
                if outlier_result.outlier_count > 0:
                    outlier_results[col] = {
                        'count': outlier_result.outlier_count,
                        'percentage': outlier_result.outlier_percentage
                    }
            except Exception as e:
                continue
        
        if outlier_results:
            results['outlier_analysis'] = outlier_results
        
        return results
    
    def prepare_data_for_modeling(self, df: pd.DataFrame) -> PreprocessingResult:
        """모델링용 데이터 준비"""
        return self.preprocessing_engine.preprocess_for_modeling(df)
    
    def get_preprocessing_recommendations(self, df: pd.DataFrame) -> List[str]:
        """전처리 권장사항 생성"""
        recommendations = []
        
        # 데이터 품질 확인
        quality_info = self.analysis_engine.analyze_data_quality(df)
        
        if quality_info['completeness_rate'] < 80:
            recommendations.append("⚠️ 데이터 완성도가 낮습니다. 결측치 처리를 권장합니다.")
        
        if quality_info['duplicate_rows'] > 0:
            recommendations.append(f"⚠️ {quality_info['duplicate_rows']}개의 중복 행이 발견되었습니다.")
        
        # 수치형 컬럼 분석
        numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
        
        if len(numeric_cols) > 10:
            recommendations.append("💡 변수가 많습니다. 차원 축소나 특성 선택을 고려하세요.")
        
        # 상관관계 확인
        if len(numeric_cols) > 1:
            try:
                corr_result = self.analysis_engine.analyze_correlation(df, numeric_cols, 0.9)
                if corr_result.total_pairs_above_threshold > 0:
                    recommendations.append("⚠️ 높은 상관관계를 가진 변수들이 있습니다. 다중공선성을 확인하세요.")
            except:
                pass
        
        return recommendations 