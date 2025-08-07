"""
데이터 분석 모듈

이 모듈은 IoT 데이터의 특성을 분석하는 함수들을 제공합니다.
"""

import pandas as pd
import numpy as np
import streamlit as st
import logging
import traceback
from scipy import stats
from ...utils import get_sensor_type, get_equipment_type
from .recommendations import ANALYSIS_RECOMMENDATIONS

def analyze_data_characteristics(df):
    """데이터의 특성을 분석하여 권장 시각화 방법을 결정"""
    recommendations = []
    sensor_col = get_sensor_type()
    
    if sensor_col not in df.columns:
        sensor_col = "value"  # 기본값
    
    # 기본 통계값 계산
    try:
        mean = df[sensor_col].mean()
        std = df[sensor_col].std()
        min_val = df[sensor_col].min()
        max_val = df[sensor_col].max()
        cv = std / mean if mean != 0 else 0  # 변동 계수
        
        # 데이터 크기
        data_size = len(df)
        
        # 시계열 특성 확인 (최소 2개 이상의 타임스탬프 필요)
        is_time_series = 'timestamp' in df.columns and len(df['timestamp'].unique()) > 1
        
        # 정규성 검정 (샘플링하여 빠르게 계산)
        sample_size = min(1000, len(df))
        sample_data = df[sensor_col].sample(sample_size) if len(df) > sample_size else df[sensor_col]
        _, p_value = stats.normaltest(sample_data)
        is_normal = p_value > 0.05
        
        # 이상치 비율 추정
        q1 = df[sensor_col].quantile(0.25)
        q3 = df[sensor_col].quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        outliers_ratio = ((df[sensor_col] < lower_bound) | (df[sensor_col] > upper_bound)).mean()
        
        # 주기성 예비 검사 (샘플 데이터로 자기상관 확인)
        has_periodicity = False
        if is_time_series and len(df) >= 50:
            try:
                # 데이터를 균등한 시간 간격으로 리샘플링
                if 'timestamp' in df.columns:
                    # 숫자형 데이터 컬럼만 선택하여 작업
                    numeric_cols = df.select_dtypes(include=['number']).columns
                    if sensor_col in numeric_cols:
                        sample_df = df.set_index('timestamp')
                        # 시간 간격 추정
                        time_diff = (sample_df.index.max() - sample_df.index.min()).total_seconds() / len(sample_df)
                        freq = f"{int(max(60, time_diff))}S"  # 최소 60초 간격
                        
                        # 숫자형 컬럼만 리샘플링
                        resampled_df = sample_df[[sensor_col]].resample(freq).mean().dropna()
                        
                        if len(resampled_df) >= 30:
                            # 자기상관 계산
                            autocorr = pd.Series(resampled_df[sensor_col]).autocorr(lag=1)
                            has_periodicity = abs(autocorr) > 0.3
                    else:
                        print(f"주기성 검사: '{sensor_col}' 컬럼이 숫자형이 아니어서 분석을 건너뜁니다.")
                        has_periodicity = False
            except Exception as e:
                print(f"주기성 검사 중 오류: {str(e)}")
                traceback_info = traceback.format_exc()
                print(f"상세 오류 정보: {traceback_info}")
                has_periodicity = False
        
        # 특성에 따른 추천
        recommendations = []
        
        # 1. 기본 추천: 시계열 탐색
        if is_time_series:
            # 데이터 포인트 수에 따라 추천 내용 세분화
            if data_size > 5000:
                detail_text = f"대용량 시계열 데이터({data_size:,}개 포인트)에서 장기적 패턴과 추세를 파악하는 것이 중요합니다. "
                detail_text += "데이터 추세, 계절성, 예외적 변동을 식별하여 설비 성능의 점진적 변화를 감지할 수 있습니다."
                vis_options = ["시계열 차트", "트렌드 분석", "히트맵"]
            elif data_size > 1000:
                detail_text = f"중간 규모 시계열 데이터({data_size:,}개 포인트)에서 추세와 단기 패턴을 균형있게 분석하는 것이 효과적입니다. "
                detail_text += "이동 평균선을 활용한 노이즈 필터링과 추세 파악을 권장합니다."
                vis_options = ["시계열 차트", "트렌드 분석"]
            else:
                detail_text = f"소규모 시계열 데이터({data_size:,}개 포인트)에서는 세부 변동 패턴에 집중하는 것이 효과적입니다. "
                detail_text += "각 데이터 포인트의 변화에 주목하여 설비 상태 변화를 정밀하게 파악할 수 있습니다."
                vis_options = ["시계열 차트", "일별/시간별 패턴"]
            
            # 주기성 징후가 있으나 확정적이지 않은 경우 추가 설명
            try:
                weak_autocorr = 0
                if 'timestamp' in df.columns and sensor_col in df.select_dtypes(include=['number']).columns:
                    sample_df = df.set_index('timestamp')
                    time_diff = (sample_df.index.max() - sample_df.index.min()).total_seconds() / len(sample_df)
                    freq = f"{int(max(60, time_diff))}S"  # 최소 60초 간격
                    resampled_df = sample_df[[sensor_col]].resample(freq).mean().dropna()
                    
                    if len(resampled_df) >= 30:
                        weak_autocorr = abs(pd.Series(resampled_df[sensor_col]).autocorr(lag=1))
                
                if 0.2 < weak_autocorr < 0.3:
                    detail_text += " 또한, 약한 주기성 징후가 감지되어 시계열 분석 후 주파수 분석도 고려해볼 수 있습니다."
            except Exception as e:
                print(f"약한 주기성 검사 중 오류: {str(e)}")
            
            recommendations.append({
                "목적": "시계열 패턴 탐색",
                "추천 이유": "시간에 따른 데이터 패턴을 파악하기 위한 첫 단계입니다. " + detail_text,
                "우선순위": 1,
                "추천 시각화": vis_options,
                "추가 설명": "시계열 분석을 통해 장비의 일반적인 작동 패턴, 성능 변화 추세, 주기적 행동 등을 파악할 수 있습니다. 이동 평균선을 활용하면 단기 노이즈를 제거하고 중요한 패턴을 식별하는 데 도움이 됩니다."
            })
        
        # 2. 이상치가 많을 경우
        if outliers_ratio > 0.01:  # 1% 이상 이상치
            # 이상치 비율에 따른 세분화
            if outliers_ratio > 0.1:
                severity = "매우 높은"
                priority = 1  # 가장 높은 우선순위
                detail_text = f"데이터의 {outliers_ratio:.1%}가 통계적 이상치로 감지되어 즉각적인 분석이 필요합니다. "
                detail_text += "이는 센서 오작동, 심각한 설비 이상, 또는 데이터 품질 문제를 나타낼 수 있습니다."
                vis_options = ["이상치 분석", "박스 플롯", "히스토그램", "시계열 차트"]
            elif outliers_ratio > 0.05:
                severity = "높은"
                priority = 2
                detail_text = f"데이터의 {outliers_ratio:.1%}가 통계적 이상치로 감지되었습니다. "
                detail_text += "이는 설비의 불규칙한 작동 상태나 특정 조건에서의 이상 동작을 나타낼 수 있습니다."
                vis_options = ["이상치 분석", "박스 플롯", "히스토그램"]
            else:
                severity = "다소 높은"
                priority = 3
                detail_text = f"데이터의 {outliers_ratio:.1%}가 통계적 이상치로 감지되었습니다. "
                detail_text += "소수의 이상치는 특정 작동 조건이나 일시적인 변동에 기인할 수 있습니다."
                vis_options = ["이상치 분석", "박스 플롯"]
            
            recommendations.append({
                "목적": "이상치 탐지",
                "추천 이유": f"데이터에 {severity} 수준의 이상치가 포함되어 있습니다. " + detail_text,
                "우선순위": priority,
                "추천 시각화": vis_options,
                "추가 설명": "이상치 분석을 통해 비정상적인 설비 상태를 식별하고, 잠재적인 고장이나 이상 동작의 조기 징후를 포착할 수 있습니다. 이상치 발생 패턴과 시간적 분포를 분석하면 근본 원인을 추적하는 데 도움이 됩니다."
            })
            
            # 변동성이 높고 이상치가 많은 경우, 운전/중지 패턴 분리 이상치 분석 추가
            if cv > 0.25 and is_time_series:
                recommendations.append({
                    "목적": "이상치 탐지",
                    "추천 이유": f"데이터의 변동성({cv:.2f})과 이상치 비율({outliers_ratio:.1%})을 고려할 때, 장비의 운전/중지 상태를 구분하여 분석할 필요가 있습니다.",
                    "우선순위": priority + 1,
                    "추천 시각화": ["운전/중지 패턴 분리 이상치 분석"],
                    "추가 설명": "장비의 운전 상태와 중지 상태에서의 이상치 패턴은 다를 수 있습니다. 상태별로 분리하여 분석하면 각 작동 모드에 특화된 이상 징후를 더 정확하게 식별할 수 있습니다. 특히 시작, 종료 과정의 이상 또는 안정 상태의 이상을 구분하여 분석하는 데 유용합니다."
                })
        
        # 3. 주기성이 있는 경우
        if has_periodicity:
            # 자기상관 값에 따른 주기성 강도 판단
            try:
                if 'timestamp' in df.columns and sensor_col in df.select_dtypes(include=['number']).columns:
                    sample_df = df.set_index('timestamp')
                    time_diff = (sample_df.index.max() - sample_df.index.min()).total_seconds() / len(sample_df)
                    freq = f"{int(max(60, time_diff))}S"  # 최소 60초 간격
                    resampled_df = sample_df[[sensor_col]].resample(freq).mean().dropna()
                    
                    if len(resampled_df) >= 30:
                        autocorr_val = abs(pd.Series(resampled_df[sensor_col]).autocorr(lag=1))
                    else:
                        autocorr_val = 0.3
                else:
                    autocorr_val = 0.3
            except Exception as e:
                print(f"자기상관 계산 중 오류: {str(e)}")
                autocorr_val = 0.3
            
            if autocorr_val > 0.7:
                strength = "매우 강한"
                detail_text = "데이터에서 매우 뚜렷한 주기적 패턴이 감지되었습니다. 이는 설비의 정기적인 작동 주기나 생산 프로세스의 명확한 사이클을 나타냅니다."
                vis_options = ["주파수 분석(FFT)", "시간-주파수 분석", "시계열 차트"]
            elif autocorr_val > 0.5:
                strength = "강한"
                detail_text = "데이터에서 뚜렷한 주기적 패턴이 감지되었습니다. 이는 설비 작동의 반복적인 특성이나 정기적인 부하 변동을 나타낼 수 있습니다."
                vis_options = ["주파수 분석(FFT)", "시간-주파수 분석"]
            else:
                strength = "유의미한"
                detail_text = "데이터에서 주기적 패턴이 감지되었습니다. 이는 설비 작동이나 환경 조건의 규칙적인 변화를 나타낼 수 있습니다."
                vis_options = ["주파수 분석(FFT)", "시간-주파수 분석"]
            
            recommendations.append({
                "목적": "주기성 분석",
                "추천 이유": f"데이터에 {strength} 주기적 패턴이 감지되었습니다. " + detail_text,
                "우선순위": 2,
                "추천 시각화": vis_options,
                "추가 설명": "주파수 분석은 시간 도메인에서 명확히 보이지 않는 숨겨진 주기 패턴을 식별하는 데 효과적입니다. 이를 통해 설비의 고유 진동 특성, 공진 주파수, 반복적인 작동 사이클을 파악할 수 있으며, 특히 회전 기계나 진동이 중요한 설비에서 유용합니다."
            })
            
            # 주기성이 강할 경우 운전/정지 주기 분석도 추천
            if autocorr_val > 0.5 and is_time_series:
                recommendations.append({
                    "목적": "주기성 분석",
                    "추천 이유": f"강한 주기적 패턴이 감지되어 장비의 운전/정지 주기를 분석하는 것이 유용합니다. 작동 시간, 휴지 기간, 주기 반복성 등을 파악할 수 있습니다.",
                    "우선순위": 2,
                    "추천 시각화": ["운전/정지 주기 분석"],
                    "추가 설명": "운전/정지 주기 분석은 장비의 작동 패턴을 시간 단위로 분석하여 정상 주기와 비정상 주기를 구분합니다. 이를 통해 비효율적인 작동 주기, 예상치 못한 정지, 과도한 시작/종료 횟수 등을 식별하고 최적의 운영 패턴을 도출할 수 있습니다."
                })
            
            # 주기성이 강한 경우 자기상관 분석도 추천
            if autocorr_val > 0.5:
                recommendations.append({
                    "목적": "주기성 분석",
                    "추천 이유": f"강한 주기적 패턴에 대해 자기상관 분석이 유용합니다. 시간 지연에 따른 상관관계를 파악하여 정확한 주기를 식별할 수 있습니다.",
                    "우선순위": 3,
                    "추천 시각화": ["자기상관 분석"],
                    "추가 설명": "자기상관 분석(ACF/PACF)은 시계열 데이터의 주기성을 수치적으로 평가하여 정확한 주기 길이와 강도를 측정할 수 있습니다. 이를 통해 주파수 분석 결과를 검증하고 보완할 수 있습니다."
                })
                
        # 변동성이 높으나 주기성이 약한 경우에도 운전/정지 주기 분석 고려
        if not has_periodicity and cv > 0.4 and is_time_series:
            recommendations.append({
                "목적": "패턴 분석",
                "추천 이유": f"데이터의 변동성({cv:.2f})이 높아 장비의 운전/정지 주기가 존재할 가능성이 있습니다. 주기 분석을 통해 작동 패턴을 파악할 수 있습니다.",
                "우선순위": 4,
                "추천 시각화": ["운전/정지 주기 분석"],
                "추가 설명": "변동성이 높은 데이터는 장비가 여러 작동 상태 사이를 전환하고 있음을 나타낼 수 있습니다. 운전/정지 주기 분석을 통해 이러한 상태 전환의 패턴, 빈도, 지속 시간 등을 파악하여 장비 운영 최적화와 이상 상태 감지에 활용할 수 있습니다."
            })
        
        # 4. 분포 분석
        if not is_normal:
            # 분포 형태에 대한 추가 분석
            skewness = sample_data.skew()
            kurtosis = sample_data.kurtosis()
            
            distribution_type = ""
            detail_text = ""
            
            # 분포 형태 파악
            if abs(skewness) > 1:
                if skewness > 0:
                    distribution_type = "강한 양의 왜도(오른쪽으로 치우침)"
                    detail_text = "소수의 높은 값이 데이터 분포를 지배하고 있습니다. 이는 간헐적인 피크나 이벤트성 상승을 나타낼 수 있습니다."
                else:
                    distribution_type = "강한 음의 왜도(왼쪽으로 치우침)"
                    detail_text = "소수의 낮은 값이 데이터 분포에 영향을 주고 있습니다. 이는 드문 하락 이벤트나 성능 저하 상황을 나타낼 수 있습니다."
            elif abs(skewness) > 0.5:
                if skewness > 0:
                    distribution_type = "중간 정도의 양의 왜도"
                    detail_text = "데이터가 오른쪽으로 다소 치우쳐 있으며, 중앙값보다 평균이 높게 나타납니다."
                else:
                    distribution_type = "중간 정도의 음의 왜도"
                    detail_text = "데이터가 왼쪽으로 다소 치우쳐 있으며, 중앙값보다 평균이 낮게 나타납니다."
            else:
                distribution_type = "대칭에 가까운 분포"
                detail_text = "데이터가 중심을 기준으로 비교적 대칭적으로 분포되어 있지만, 정규분포는 아닙니다."
                
            # 첨도 분석 추가
            if kurtosis > 3:
                distribution_type += ", 높은 첨도(두꺼운 꼬리)"
                detail_text += " 분포의 꼬리가 두꺼워 극단값이 정규분포보다 자주 발생합니다."
            elif kurtosis < -1:
                distribution_type += ", 낮은 첨도(균일한 분포)"
                detail_text += " 값들이 넓은 범위에 비교적 균일하게 분포되어 있습니다."
                
            recommendations.append({
                "목적": "분포 분석",
                "추천 이유": f"데이터가 정규분포를 따르지 않고 {distribution_type}를 보입니다. {detail_text}",
                "우선순위": 3,
                "추천 시각화": ["히스토그램", "분포 비교", "QQ플롯"],
                "추가 설명": "분포 분석은 센서 값의 일반적인 범위와 발생 빈도를 이해하는 데 필수적입니다. 정규분포에서 벗어난 데이터는 특정 작동 모드, 다중 상태 작동, 또는 외부 요인의 영향을 나타낼 수 있습니다. 분포 형태를 분석하면 장비 상태 모니터링을 위한 적절한 통계적 접근 방식을 결정하는 데 도움이 됩니다."
            })
        
        # 5. 변동성이 큰 경우
        if cv > 0.2:  # 변동 계수가 20% 이상
            # 변동 계수에 따른 세분화
            if cv > 0.5:
                variability = "매우 높은"
                detail_text = f"변동 계수(CV={cv:.2f})가 매우 높아 데이터의 불안정성이 매우 큽니다. 이는 설비가 다양한 작동 모드를 가지거나, 외부 조건에 민감하게 반응하고 있음을 나타낼 수 있습니다."
                vis_options = ["패턴 클러스터링", "히트맵", "시계열 차트", "3D 데이터 시각화"]
            elif cv > 0.3:
                variability = "높은"
                detail_text = f"변동 계수(CV={cv:.2f})가 높아 데이터의 변동성이 상당합니다. 이는 설비 상태나 작동 조건의 유의미한 변화를 나타냅니다."
                vis_options = ["패턴 클러스터링", "히트맵", "상관관계 분석"]
            else:
                variability = "다소 높은"
                detail_text = f"변동 계수(CV={cv:.2f})가 다소 높습니다. 데이터 내 여러 패턴이나 그룹이 존재할 가능성이 있습니다."
                vis_options = ["패턴 클러스터링", "히트맵"]
            
            recommendations.append({
                "목적": "패턴 분류",
                "추천 이유": f"데이터의 변동성이 {variability} 수준입니다. " + detail_text,
                "우선순위": 4,
                "추천 시각화": vis_options,
                "추가 설명": "패턴 분류는 복잡한 데이터 세트에서 유사한 행동 특성을 갖는 데이터 포인트를 그룹화하여, 설비의 여러 작동 모드나 상태를 식별하는 데 유용합니다. 클러스터링을 통해 정상 작동의 여러 상태를 구분하고, 이상 패턴을 더 정확하게 감지할 수 있습니다."
            })
        
        # 6. 기본 분포 분석 (항상 포함)
        if "분포 분석" not in [r["목적"] for r in recommendations]:
            # 데이터 범위와 통계량 기반 설명 추가
            range_ratio = (max_val - min_val) / (std * 4) if std > 0 else 1
            
            if range_ratio > 1.5:
                detail_text = "데이터의 범위가 넓고 다양한 값을 포함하고 있어, 분포 특성을 이해하는 것이 중요합니다."
            else:
                detail_text = "데이터가 비교적 일정한 범위 내에 있으나, 세부적인 분포 특성을 파악하면 설비 상태에 대한 이해를 높일 수 있습니다."
            
            recommendations.append({
                "목적": "분포 분석",
                "추천 이유": "데이터의 전반적인 분포 특성을 파악하는 것이 중요합니다. " + detail_text,
                "우선순위": 4,
                "추천 시각화": ["히스토그램", "박스 플롯", "바이올린 플롯"],
                "추가 설명": "분포 분석은 센서 값의 일반적인 범위, 중심 경향, 산포도를 이해하는 데 기본이 됩니다. 이를 통해 정상 작동 범위를 정의하고, 알람 임계값 설정의 기초 자료로 활용할 수 있습니다."
            })
        
        # 7. 데이터 양이 충분한 경우 상관관계 분석 추가
        if data_size >= 100 and 'timestamp' in df.columns:
            # 다른 측정값이나 시간과의 상관관계 분석 추천
            recommendations.append({
                "목적": "상관관계 분석",
                "추천 이유": f"충분한 데이터({data_size:,}개 포인트)가 있어 시간이나 다른 변수와의 관계 분석이 가능합니다.",
                "우선순위": 5,
                "추천 시각화": ["상관관계 분석", "산점도"],
                "추가 설명": "상관관계 분석을 통해 센서 값에 영향을 미치는 요인(시간대, 온도, 부하 등)을 식별할 수 있습니다. 이는 설비 성능을 최적화하고 예측 모델을 개발하는 데 중요한 인사이트를 제공합니다."
            })
            
        # 8. 이상치와 변동성이 모두 있는 경우 결합 분석 추천
        if outliers_ratio > 0.03 and cv > 0.3:
            recommendations.append({
                "목적": "복합 분석",
                "추천 이유": f"데이터에 이상치({outliers_ratio:.1%})와 높은 변동성(CV={cv:.2f})이 동시에 존재합니다. 이는 복잡한 작동 패턴과 이상 상태가 혼재되어 있음을 시사합니다.",
                "우선순위": 3,
                "추천 시각화": ["이상-패턴 결합 분석", "다변량 시계열 분석"],
                "추가 설명": "일반적인 이상치 탐지 방법은 변동성이 큰 데이터에서 효과적이지 않을 수 있습니다. 패턴 기반 이상 탐지와 컨텍스트 기반 이상 탐지를 결합하면 여러 작동 모드를 구분하고, 각 모드 내에서의 이상 상태를 더 정확하게 식별할 수 있습니다."
            })
            
        # 9. 시계열 예측 추천 (충분한 데이터와 일정한 패턴이 있는 경우)
        if is_time_series and data_size >= 200:
            # 데이터 특성에 따른 예측 모델 추천
            if has_periodicity:
                detail_text = "주기적 패턴이 감지되어 계절성을 고려한 예측 모델이 효과적일 것입니다."
                vis_options = ["시계열 예측 모델", "계절성 예측"]
            elif cv < 0.3:  # 변동성이 낮은 경우
                detail_text = "데이터의 변동성이 비교적 낮아 추세 기반 예측이 효과적일 것입니다."
                vis_options = ["추세 예측", "시계열 예측 모델"]
            else:
                detail_text = "다양한 시계열 예측 모델을 비교하여 최적의 예측 방법을 찾는 것이 중요합니다."
                vis_options = ["시계열 예측 모델"]
                
            recommendations.append({
                "목적": "시계열 예측",
                "추천 이유": f"충분한 시계열 데이터({data_size:,}개 포인트)를 기반으로 미래 값을 예측할 수 있습니다. " + detail_text,
                "우선순위": 4,
                "추천 시각화": vis_options,
                "추가 설명": "시계열 예측 모델을 통해 센서 값의 미래 추세와 변동을 예측하여 선제적 대응이 가능합니다. 과거 패턴을 학습하여 미래 이상 상태를 미리 감지하거나, 자원 계획 및 유지보수 일정을 최적화하는 데 활용할 수 있습니다."
            })
            
        # 10. 데이터 분포가 다양하고 그룹화 가능성이 있는 경우 패턴 분류 추천
        if cv > 0.4 or (not is_normal and abs(sample_data.skew()) > 0.8):
            pattern_priority = 3 if cv > 0.5 else 4
            
            if data_size > 500:
                detail_text = f"데이터의 높은 변동성(CV={cv:.2f})과 비정규 분포 특성은 여러 작동 모드나 상태가 혼합되어 있을 가능성을 시사합니다."
                vis_options = ["패턴 클러스터링", "다차원 축소"]
                
                recommendations.append({
                    "목적": "패턴 분류",
                    "추천 이유": detail_text,
                    "우선순위": pattern_priority,
                    "추천 시각화": vis_options,
                    "추가 설명": "패턴 분류는 데이터를 유사한 그룹으로 자동 분류하여 설비의 여러 작동 모드나 상태를 식별합니다. 이를 통해 특정 조건이나 상황에 따른 센서 반응의 차이를 이해하고, 각 모드별 최적 운영 조건을 도출할 수 있습니다."
                })
                
                # 시계열 데이터인 경우 타임 시리즈 클러스터링도 추천
                if is_time_series:
                    recommendations.append({
                        "목적": "패턴 분류",
                        "추천 이유": "시간에 따른 패턴 변화를 분류하여 유사한 동작 시퀀스나 이벤트를 그룹화할 수 있습니다.",
                        "우선순위": pattern_priority + 1,
                        "추천 시각화": ["타임 시리즈 클러스터링"],
                        "추가 설명": "타임 시리즈 클러스터링은 시간에 따른 데이터 변화 패턴의 유사성을 기반으로 그룹화합니다. 이를 통해 반복되는 작업 사이클, 이벤트 시퀀스, 장비 상태 변화 등을 자동으로 식별하고 분류할 수 있습니다."
                    })
                    
        # 11. 이상치 비율이 높거나 중요한 모니터링 대상인 경우 알람 설정 추천
        if outliers_ratio > 0.02:
            alarm_priority = 2 if outliers_ratio > 0.05 else 3
            
            if is_time_series:
                detail_text = "시계열 데이터의 이상 패턴을 실시간으로 감지하는 알람 시스템 구축이 가능합니다."
                vis_options = ["경보 및 임계값 설정", "이상 패턴 알람"]
            else:
                detail_text = "데이터 분포를 기반으로 최적의 알람 임계값을 설정하여 이상 상태를 감지할 수 있습니다."
                vis_options = ["경보 및 임계값 설정"]
                
            recommendations.append({
                "목적": "알람 설정",
                "추천 이유": f"데이터의 이상치 비율({outliers_ratio:.1%})을 고려한 알람 시스템 구축이 필요합니다. " + detail_text,
                "우선순위": alarm_priority,
                "추천 시각화": vis_options,
                "추가 설명": "알람 시스템은 센서 데이터가 정상 범위를 벗어났을 때 즉각적인 조치가 가능하도록 합니다. 통계적으로 최적화된 임계값을 사용하면 거짓 알람은 최소화하고 중요한 이상 상태는 효과적으로 감지할 수 있습니다."
            })
            
            # 알람 시스템 성능 평가 추천
            if data_size > 1000 and outliers_ratio > 0.01:
                recommendations.append({
                    "목적": "알람 설정",
                    "추천 이유": "충분한 데이터와 이상치를 기반으로 알람 시스템의 성능을 평가하고 최적화할 수 있습니다.",
                    "우선순위": alarm_priority + 1,
                    "추천 시각화": ["ROC 분석"],
                    "추가 설명": "ROC 분석을 통해 알람 시스템의 민감도(재현율)와 특이도를 평가하고 최적의 운영 포인트를 찾을 수 있습니다. 이는 거짓 알람과 미감지 사이의 균형을 맞추는 데 중요합니다."
                })

        # 우선순위에 따라 정렬
        recommendations.sort(key=lambda x: x["우선순위"])
        
        return recommendations, {
            "is_time_series": is_time_series,
            "data_size": data_size,
            "mean": mean,
            "std": std,
            "cv": cv,
            "min": min_val,
            "max": max_val,
            "is_normal": is_normal,
            "outliers_ratio": outliers_ratio,
            "has_periodicity": has_periodicity
        }
    
    except Exception as e:
        st.error(f"데이터 분석 중 오류가 발생했습니다: {str(e)}")
        return [], {} 