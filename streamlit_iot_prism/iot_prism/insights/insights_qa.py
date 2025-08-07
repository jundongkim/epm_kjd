import pandas as pd
from datetime import datetime


def generate_suggested_questions(df, equipment_type, sensor_type, report_type):
    """데이터 기반 추천 질문을 생성하는 함수"""
    
    # 공통 질문
    common_questions = [
        f"{equipment_type}의 {sensor_type} 데이터 평균값은 얼마인가요?",
        f"{equipment_type}의 {sensor_type} 데이터에서 가장 높은 값은 언제 발생했나요?",
        f"{equipment_type}의 {sensor_type} 데이터에서 가장 낮은 값은 언제 발생했나요?"
    ]
    
    # 리포트 유형별 추가 질문
    report_specific_questions = {
        "종합 분석 리포트": [
            f"{equipment_type}의 {sensor_type} 값이 안정적으로 유지되고 있나요?",
            f"{equipment_type}의 {sensor_type} 값의 전체적인 추세는 어떻게 되나요?",
            f"{equipment_type}의 {sensor_type} 값의 일반적인 패턴은 무엇인가요?"
        ],
        "이상치 분석 리포트": [
            f"{equipment_type}의 {sensor_type} 데이터에서 이상치가 얼마나 발견되었나요?",
            f"{equipment_type}의 {sensor_type} 데이터에서 발견된 이상치의 원인은 무엇인가요?",
            f"{equipment_type}의 {sensor_type} 이상치를 줄이기 위한 방법은 무엇인가요?"
        ],
        "패턴 분석 리포트": [
            f"{equipment_type}의 {sensor_type} 값은 시간대별로 어떻게 변하나요?",
            f"{equipment_type}의 {sensor_type} 값은 요일별로 다른 패턴을 보이나요?",
            f"{equipment_type}의 {sensor_type} 값의 주기성이 있나요?"
        ],
        "성능 추세 리포트": [
            f"{equipment_type}의 {sensor_type} 값이 시간에 따라 어떻게 변하고 있나요?",
            f"{equipment_type}의 {sensor_type} 값의 장기적인 추세는 어떻게 되나요?",
            f"{equipment_type}의 {sensor_type} 값의 변화율은 얼마인가요?"
        ]
    }
    
    # 기본 질문과 리포트 유형별 질문 결합
    suggested_questions = common_questions.copy()
    suggested_questions.extend(report_specific_questions.get(report_type, []))
    
    # 설비 유형에 따른 추가 질문
    equipment_questions = {
        "펌프": [
            f"펌프의 {sensor_type} 값이 특정 조건에서 불안정한가요?",
            f"펌프의 {sensor_type} 값과 효율 간의 관계는 어떻게 되나요?"
        ],
        "컴프레서": [
            f"컴프레서의 {sensor_type} 값이 주변 온도에 따라 어떻게 변하나요?",
            f"컴프레서의 {sensor_type} 값이 부하 상태에 따라 어떻게 변하나요?"
        ],
        "모터": [
            f"모터의 {sensor_type} 값이 시동 시와 정상 운전 시 어떻게 다른가요?",
            f"모터의 {sensor_type} 값이 노화에 따라 어떻게 변하나요?"
        ],
        "보일러": [
            f"보일러의 {sensor_type} 값이 연료 소비량과 어떤 관계가 있나요?",
            f"보일러의 {sensor_type} 값이 계절에 따라 어떻게 변하나요?"
        ]
    }
    
    # 설비 유형별 질문 추가
    if equipment_type in equipment_questions:
        suggested_questions.extend(equipment_questions[equipment_type])
    
    # 센서 유형에 따른 추가 질문
    sensor_questions = {
        "온도": [
            f"{equipment_type}의 온도가 안전 범위를 벗어난 빈도는 얼마인가요?",
            f"{equipment_type}의 온도 상승률이 가장 높은 운전 조건은 무엇인가요?"
        ],
        "압력": [
            f"{equipment_type}의 압력이 정상 범위를 벗어난 경우가 있나요?",
            f"{equipment_type}의 압력 변동이 설비 효율에 어떤 영향을 미치나요?"
        ],
        "전류": [
            f"{equipment_type}의 전류 스파이크가 발생한 시점이 있나요?",
            f"{equipment_type}의 전류 소비량과 부하 간의 관계는 어떻게 되나요?"
        ],
        "전압": [
            f"{equipment_type}의 전압 변동이 가장 큰 시간대는 언제인가요?",
            f"{equipment_type}의 전압 안정성을 개선하기 위한 방법은 무엇인가요?"
        ],
        "회전수": [
            f"{equipment_type}의 회전수 변화가 다른 센서 값에 어떤 영향을 미치나요?",
            f"{equipment_type}의 최적 회전수 범위는 어떻게 되나요?"
        ]
    }
    
    # 센서 유형별 질문 추가
    if sensor_type in sensor_questions:
        suggested_questions.extend(sensor_questions[sensor_type])
    elif "temperature" in sensor_type.lower():
        suggested_questions.extend(sensor_questions["온도"])
    elif "pressure" in sensor_type.lower():
        suggested_questions.extend(sensor_questions["압력"])
    elif "current" in sensor_type.lower():
        suggested_questions.extend(sensor_questions["전류"])
    elif "voltage" in sensor_type.lower():
        suggested_questions.extend(sensor_questions["전압"])
    elif "rpm" in sensor_type.lower() or "speed" in sensor_type.lower():
        suggested_questions.extend(sensor_questions["회전수"])
    
    # 중복 제거 및 최대 10개 질문 선택
    unique_questions = list(set(suggested_questions))
    selected_questions = unique_questions[:min(10, len(unique_questions))]
    
    return selected_questions


def generate_answer_to_question(df, question, equipment_type, sensor_type):
    """사용자 질문에 대한 답변을 생성하는 함수"""
    
    # 기본 통계 계산
    sensor_values = df[sensor_type]
    mean_val = sensor_values.mean()
    min_val = sensor_values.min()
    max_val = sensor_values.max()
    std_val = sensor_values.std()
    
    # 최대/최소값 발생 시점
    max_idx = sensor_values.idxmax()
    min_idx = sensor_values.idxmin()
    max_time = df.loc[max_idx, 'timestamp'].strftime('%Y-%m-%d %H:%M:%S')
    min_time = df.loc[min_idx, 'timestamp'].strftime('%Y-%m-%d %H:%M:%S')
    
    # 추세 계산
    if len(df) > 1:
        first_avg = df[sensor_type].iloc[:int(len(df)*0.1)].mean()  # 첫 10% 평균
        last_avg = df[sensor_type].iloc[-int(len(df)*0.1):].mean()  # 마지막 10% 평균
        trend_change = ((last_avg - first_avg) / first_avg) * 100 if first_avg != 0 else 0
        
        if trend_change > 5:
            trend = "뚜렷한 상승"
        elif trend_change > 1:
            trend = "약한 상승"
        elif trend_change < -5:
            trend = "뚜렷한 하락"
        elif trend_change < -1:
            trend = "약한 하락"
        else:
            trend = "안정적 유지"
    else:
        trend = "판단 불가"
    
    # 이상치 비율 계산
    z_threshold = 3.0
    z_scores = abs((sensor_values - mean_val) / std_val)
    anomalies = df[z_scores > z_threshold]
    anomaly_pct = len(anomalies) / len(df) * 100
    
    # 시간 패턴 계산
    df_copy = df.copy()
    df_copy['hour'] = df_copy['timestamp'].dt.hour
    hourly_pattern = df_copy.groupby('hour')[sensor_type].mean()
    peak_hour = hourly_pattern.idxmax()
    low_hour = hourly_pattern.idxmin()
    
    # 질문 패턴 매칭 및 답변 생성
    answer = ""
    
    # 평균값 관련 질문
    if "평균" in question or "평균값" in question:
        answer = f"{equipment_type}의 {sensor_type} 데이터 평균값은 {mean_val:.2f}입니다. 이는 전체 데이터 범위({min_val:.2f} ~ {max_val:.2f}) 내에서 상대적으로 {'높은' if mean_val > (max_val + min_val)/2 else '낮은'} 수준입니다."
    
    # 최대값/최고값 관련 질문
    elif any(term in question for term in ["최대", "최고", "가장 높은", "maximum"]):
        answer = f"{equipment_type}의 {sensor_type} 데이터 중 가장 높은 값은 {max_val:.2f}이며, 이 값은 {max_time}에 발생했습니다. 평균보다 {(max_val-mean_val)/std_val:.1f}배 표준편차만큼 높은 값입니다."
    
    # 최소값/최저값 관련 질문
    elif any(term in question for term in ["최소", "최저", "가장 낮은", "minimum"]):
        answer = f"{equipment_type}의 {sensor_type} 데이터 중 가장 낮은 값은 {min_val:.2f}이며, 이 값은 {min_time}에 발생했습니다. 평균보다 {(mean_val-min_val)/std_val:.1f}배 표준편차만큼 낮은 값입니다."
    
    # 안정성 관련 질문
    elif any(term in question for term in ["안정", "변동", "일정"]):
        if std_val / mean_val < 0.1:
            answer = f"{equipment_type}의 {sensor_type} 값은 상대적으로 안정적으로 유지되고 있습니다. 변동계수(CV)는 {std_val/mean_val*100:.1f}%로 낮은 편입니다."
        else:
            answer = f"{equipment_type}의 {sensor_type} 값은 다소 변동성이 있습니다. 변동계수(CV)는 {std_val/mean_val*100:.1f}%이며, 전체적인 추세는 {trend} 상태입니다."
    
    # 추세 관련 질문
    elif any(term in question for term in ["추세", "트렌드", "경향"]):
        answer = f"{equipment_type}의 {sensor_type} 값은 전체 기간 동안 {trend} 추세를 보이고 있습니다. 초기 대비 {abs(trend_change):.1f}% {'증가' if trend_change > 0 else '감소'}했으며, {'지속적인 모니터링이 필요합니다.' if abs(trend_change) > 5 else '비교적 안정적인 범위 내에서 변화하고 있습니다.'}"
    
    # 이상치 관련 질문
    elif any(term in question for term in ["이상", "비정상", "anomaly"]):
        if anomaly_pct > 0.5:
            answer = f"{equipment_type}의 {sensor_type} 데이터에서 이상치는 전체의 {anomaly_pct:.1f}%({len(anomalies)}개)가 발견되었습니다. 이는 {'정상적인 수준을 초과하는 수치로' if anomaly_pct > 2 else '일반적인 범위 내에 있는 수치로'} 나타납니다."
        else:
            answer = f"{equipment_type}의 {sensor_type} 데이터에서 뚜렷한 이상치는 거의 발견되지 않았습니다. 전체 데이터의 {anomaly_pct:.2f}%만이 이상치로 판단되어 안정적인 운영 상태를 보여줍니다."
    
    # 패턴 관련 질문
    elif any(term in question for term in ["패턴", "시간대", "주기"]):
        answer = f"{equipment_type}의 {sensor_type} 값은 하루 중 {peak_hour}시에 가장 높고, {low_hour}시에 가장 낮은 패턴을 보입니다. 시간대별 차이는 최대 {(hourly_pattern.max() - hourly_pattern.min()):.2f} 정도이며, {'뚜렷한 일일 패턴이 관찰됩니다.' if (hourly_pattern.max() - hourly_pattern.min()) > std_val else '시간대별 차이가 크지 않습니다.'}"
    
    # 기타 질문에 대한 일반적인 응답
    else:
        answer = f"{equipment_type}의 {sensor_type} 데이터는 평균 {mean_val:.2f}, 표준편차 {std_val:.2f}의 분포를 가지며, 전체적으로 {trend} 추세를 보이고 있습니다. 데이터의 범위는 {min_val:.2f}에서 {max_val:.2f}까지이며, 이상치는 전체의 {anomaly_pct:.1f}%가 발견되었습니다."
    
    return answer 