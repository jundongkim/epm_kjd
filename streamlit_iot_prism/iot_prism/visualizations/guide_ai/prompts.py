"""
AI 프롬프트 구성 모듈

이 모듈은 AI 분석을 위한 프롬프트를 구성하는 함수를 제공합니다.
"""

from ..guide_data.recommendations import ANALYSIS_RECOMMENDATIONS
from ...utils import get_equipment_type, get_sensor_type

def construct_ai_prompt(df_info, recommendations):
    """AI 분석을 위한 프롬프트 구성"""
    equipment_type = get_equipment_type()
    sensor_type = get_sensor_type()
    
    prompt = f"""
# IoT 데이터 분석 추천

## 데이터 정보
- 설비 유형: {equipment_type}
- 센서 유형: {sensor_type}
- 데이터 크기: {df_info.get('data_size', 'N/A'):,} 포인트
- 시계열 데이터: {'예' if df_info.get('is_time_series', False) else '아니오'}
- 평균값: {df_info.get('mean', 'N/A'):.2f}
- 표준편차: {df_info.get('std', 'N/A'):.2f}
- 변동계수(CV): {df_info.get('cv', 'N/A'):.2f}
- 최소값: {df_info.get('min', 'N/A'):.2f}
- 최대값: {df_info.get('max', 'N/A'):.2f}
- 정규분포 여부: {'예' if df_info.get('is_normal', False) else '아니오'}
- 이상치 비율: {df_info.get('outliers_ratio', 0)*100:.2f}%
- 주기성 감지: {'감지됨' if df_info.get('has_periodicity', False) else '감지되지 않음'}

## 자동 추천 분석 순서
"""
    
    for i, rec in enumerate(recommendations):
        prompt += f"\n### {i+1}. {rec['목적']}\n"
        prompt += f"- 추천 이유: {rec['추천 이유']}\n"
        prompt += "- 추천 시각화:\n"
        for viz_type in rec['추천 시각화']:
            # 추천 목적에 맞는 시각화 항목 가져오기
            viz_details = next((item for item in ANALYSIS_RECOMMENDATIONS.get(rec['목적'], []) 
                             if item['type'] == viz_type), None)
            
            if viz_details:
                prompt += f"  - {viz_details['type']}: {viz_details['description']}\n"
            else:
                prompt += f"  - {viz_type}\n"
    
    prompt += """
## 요청

IoT 센서 데이터에 대한 심층 분석 로드맵을 제공해주세요. 위 데이터 특성과 추천 사항을 고려하여:

1. 가장 효과적인 분석 순서를 제안해주세요
2. 각 분석 단계에서 얻을 수 있는 주요 인사이트와 해석 방법을 설명해주세요
3. 특히 위 데이터의 특성을 고려한 맞춤형 분석 조언을 제공해주세요
4. 효과적인 시각화 설정(차트 종류, 매개변수 등)도 제안해주세요

응답은 제조 현장 엔지니어가 이해하기 쉬운 명확한 한국어로 작성해주세요.
"""
    
    return prompt 