import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def generate_recommendations_section(df, equipment_type, sensor_type, analysis_depth, include_visuals):
    """권장 사항 섹션을 생성하는 함수"""
    section = {
        'title': '권장 사항',
        'content': '',
        'image': None
    }
    
    # 데이터 기본 통계
    mean_val = df[sensor_type].mean()
    std_val = df[sensor_type].std()
    min_val = df[sensor_type].min()
    max_val = df[sensor_type].max()
    
    # 이상치 비율 계산
    q1 = df[sensor_type].quantile(0.25)
    q3 = df[sensor_type].quantile(0.75)
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    
    outliers = df[(df[sensor_type] < lower_bound) | (df[sensor_type] > upper_bound)]
    outlier_ratio = len(outliers) / len(df) * 100 if len(df) > 0 else 0
    
    # 추세 계산
    start_segment = df[sensor_type].iloc[:int(len(df)*0.1)] if len(df) > 10 else df[sensor_type].iloc[:1]
    end_segment = df[sensor_type].iloc[-int(len(df)*0.1):] if len(df) > 10 else df[sensor_type].iloc[-1:]
    
    start_avg = start_segment.mean()
    end_avg = end_segment.mean()
    trend_rate = ((end_avg - start_avg) / start_avg) * 100 if start_avg != 0 else 0
    
    # 권장 사항 생성
    recommendations = []
    
    # 1. 이상치 관련 권장 사항
    if outlier_ratio > 5:
        recommendations.append(f"""
**이상치 관리 강화**: 데이터의 {outlier_ratio:.1f}%가 이상치로 식별되었습니다. 이는 정상 범위({lower_bound:.2f}~{upper_bound:.2f})를 벗어난 값입니다. 이상치가 발생하는 패턴을 분석하고, 센서 오작동 또는 설비 이상 징후를 조기에 감지할 수 있는 모니터링 체계를 강화하세요.
""")
    elif outlier_ratio > 2:
        recommendations.append(f"""
**이상치 모니터링**: 데이터의 {outlier_ratio:.1f}%가 이상치로 식별되었습니다. 이상치 발생 시간과 패턴을 주기적으로 모니터링하고, 정상 범위({lower_bound:.2f}~{upper_bound:.2f})를 벗어나는 값이 지속적으로 발생하는지 확인하세요.
""")
    
    # 2. 추세 관련 권장 사항
    if abs(trend_rate) > 10:
        trend_direction = "증가" if trend_rate > 0 else "감소"
        recommendations.append(f"""
**추세 변화 대응**: {equipment_type}의 {sensor_type} 값이 관측 기간 동안 {abs(trend_rate):.1f}% {trend_direction}하는 추세를 보였습니다. 이러한 변화가 설비 성능에 미치는 영향을 평가하고, 필요한 경우 조정이나 유지보수 계획을 수립하세요.
""")
    
    # 3. 변동성 관련 권장 사항
    cv = std_val / mean_val * 100 if mean_val != 0 else 0
    if cv > 20:
        recommendations.append(f"""
**변동성 안정화**: {sensor_type} 값의 변동계수(CV)가 {cv:.1f}%로 높은 편입니다. 운영 조건을 안정화하고 급격한 변동을 줄이기 위한 제어 방안을 검토하세요. 높은 변동성은 설비 수명과 효율에 부정적인 영향을 미칠 수 있습니다.
""")
    
    # 4. 설비 유형별 특화 권장 사항
    equipment_recommendations = {
        "펌프": [
            f"**효율 최적화**: {sensor_type} 값이 가장 안정적인 운전 구간을 파악하고, 해당 구간에서 펌프를 운영하여 효율을 최적화하세요.",
            "**캐비테이션 방지**: 흡입압이 낮은 시간대에는 유량을 줄이거나 흡입 조건을 개선하여 캐비테이션 발생 가능성을 줄이세요.",
            "**정기적 점검**: 펌프 임펠러와 씰의 마모 상태를 정기적으로 점검하여 성능 저하를 방지하세요."
        ],
        "컴프레서": [
            f"**부하 관리**: {sensor_type} 값이 최대치에 근접하는 시간대에는 부하를 분산시켜 컴프레서의 과부하를 방지하세요.",
            "**냉각 시스템 점검**: 컴프레서의 냉각 시스템을 정기적으로 점검하여 과열로 인한 효율 저하를 방지하세요.",
            "**공기 필터 관리**: 흡입 필터를 정기적으로 교체하여 컴프레서의 효율을 유지하고 에너지 소비를 최적화하세요."
        ],
        "모터": [
            f"**부하 최적화**: {sensor_type} 값이 안정적인 구간에서 모터를 운영하여 효율을 극대화하고 에너지 소비를 줄이세요.",
            "**과열 방지**: 모터의 온도를 정기적으로 모니터링하고, 냉각 시스템의 성능을 유지하여 과열로 인한 손상을 방지하세요.",
            "**베어링 관리**: 모터 베어링의 상태를 정기적으로 점검하고 적절한 윤활을 유지하여 마모를 최소화하세요."
        ],
        "보일러": [
            f"**연소 최적화**: {sensor_type} 값과 연료 소비량의 관계를 분석하여 최적의 연소 조건을 유지하세요.",
            "**스케일 관리**: 열교환기의 스케일을 정기적으로 제거하여 열전달 효율을 유지하세요.",
            "**배기가스 모니터링**: 배기가스의 성분을 주기적으로 분석하여 연소 효율을 최적화하고 환경 영향을 최소화하세요."
        ]
    }
    
    # 설비 유형에 맞는 권장 사항 추가
    if equipment_type in equipment_recommendations:
        specific_recommendations = equipment_recommendations[equipment_type]
        # 분석 깊이에 따라 1-3개 권장 사항 선택
        num_specific = min(analysis_depth, len(specific_recommendations))
        for i in range(num_specific):
            recommendations.append(specific_recommendations[i])
    
    # 5. 센서 유형별 특화 권장 사항
    sensor_recommendations = {
        "온도": [
            "**온도 안정화**: 급격한 온도 변화는 설비 수명에 부정적인 영향을 미칩니다. 온도 변화율을 모니터링하고 급격한 변화를 방지하는 제어 방안을 마련하세요.",
            "**열 손실 최소화**: 설비의 단열 상태를 점검하고 개선하여 열 손실을 최소화하고 에너지 효율을 높이세요.",
            "**센서 위치 최적화**: 온도 센서의 위치가 대표성을 갖는지 확인하고, 필요한 경우 센서 위치를 조정하여 더 정확한 데이터를 수집하세요."
        ],
        "압력": [
            "**압력 맥동 감소**: 압력의 급격한 변동은 설비 손상의 원인이 될 수 있습니다. 압력 맥동을 줄이기 위한 댐퍼나 어큐뮬레이터 설치를 고려하세요.",
            "**압력 손실 최소화**: 배관 시스템의 압력 손실을 정기적으로 평가하고, 불필요한 압력 손실을 줄이기 위한 개선 방안을 마련하세요.",
            "**안전 여유 확보**: 최대 운전 압력과 설계 압력 간의 안전 여유를 확인하고, 필요한 경우 운전 조건을 조정하여 안전성을 높이세요."
        ],
        "전류": [
            "**부하 분산**: 전류 피크가 발생하는 시간대를 파악하고, 가능한 경우 부하를 분산시켜 전기 설비의 과부하를 방지하세요.",
            "**역률 개선**: 설비의 역률을 모니터링하고, 필요한 경우 역률 개선 장치를 설치하여 전력 효율을 높이세요.",
            "**고조파 관리**: 전류 파형의 고조파 성분을 분석하고, 필요한 경우 고조파 필터를 설치하여 전기 품질을 개선하세요."
        ],
        "전압": [
            "**전압 안정화**: 전압 변동이 큰 시간대를 파악하고, 전압 안정화 장치 설치를 고려하여 설비 보호 및 성능 안정화를 도모하세요.",
            "**접지 시스템 점검**: 접지 시스템의 상태를 정기적으로 점검하여 전기적 안전성을 확보하세요.",
            "**서지 보호**: 민감한 전자 장비에 서지 보호 장치를 설치하여 전압 스파이크로 인한 손상을 방지하세요."
        ],
        "회전수": [
            "**공진 회피**: 설비의 공진 주파수 대역을 파악하고, 해당 회전수 구간에서의 지속적인 운전을 피하여 진동으로 인한 손상을 방지하세요.",
            "**가속/감속 최적화**: 급격한 회전수 변화는 기계적 스트레스를 증가시킵니다. 가속 및 감속 패턴을 최적화하여 설비 수명을 연장하세요.",
            "**베어링 상태 모니터링**: 회전 설비의 베어링 상태를 정기적으로 모니터링하고, 진동 분석을 통해 초기 결함을 감지하세요."
        ]
    }
    
    # 센서 유형에 맞는 권장 사항 추가
    sensor_key = None
    if "온도" in sensor_type or "temperature" in sensor_type.lower():
        sensor_key = "온도"
    elif "압력" in sensor_type or "pressure" in sensor_type.lower():
        sensor_key = "압력"
    elif "전류" in sensor_type or "current" in sensor_type.lower():
        sensor_key = "전류"
    elif "전압" in sensor_type or "voltage" in sensor_type.lower():
        sensor_key = "전압"
    elif "회전" in sensor_type or "rpm" in sensor_type.lower() or "speed" in sensor_type.lower():
        sensor_key = "회전수"
    
    if sensor_key and sensor_key in sensor_recommendations:
        specific_recommendations = sensor_recommendations[sensor_key]
        # 분석 깊이에 따라 1-2개 권장 사항 선택
        num_specific = min(max(1, analysis_depth - 2), len(specific_recommendations))
        for i in range(num_specific):
            recommendations.append(specific_recommendations[i])
    
    # 6. 데이터 수집 및 분석 관련 권장 사항
    if analysis_depth >= 4:
        recommendations.append("""
**데이터 수집 개선**: 데이터 수집 주기와 정확도를 평가하고, 필요한 경우 센서 교정이나 데이터 수집 시스템 업그레이드를 고려하세요. 고품질 데이터는 더 정확한 분석과 의사결정의 기반이 됩니다.
""")
        
    if analysis_depth >= 5:
        recommendations.append("""
**예측 분석 도입**: 현재의 데이터 분석을 넘어 머신러닝 기반의 예측 분석을 도입하여 설비 고장이나 성능 저하를 사전에 예측하고 대응하세요. 이는 예방적 유지보수와 가동 시간 최적화에 도움이 됩니다.
""")
    
    # 권장 사항이 없는 경우 기본 메시지 추가
    if not recommendations:
        recommendations.append(f"""
**데이터 모니터링 지속**: {equipment_type}의 {sensor_type} 데이터는 현재 안정적인 상태를 보이고 있습니다. 지속적인 모니터링을 통해 이상 징후를 조기에 감지할 수 있도록 하세요.
""")
    
    # 최종 권장 사항 내용 생성
    recommendations_content = f"""
{equipment_type}의 {sensor_type} 데이터 분석을 기반으로 한 권장 사항입니다.

"""
    
    for i, recommendation in enumerate(recommendations):
        recommendations_content += f"### {i+1}. {recommendation.strip()}\n"
    
    section['content'] = recommendations_content
    return section 