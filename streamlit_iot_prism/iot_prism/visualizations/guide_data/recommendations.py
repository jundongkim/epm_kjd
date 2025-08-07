"""
분석 추천 정의 모듈

이 모듈은 목적별 분석 추천 정의를 포함합니다.
"""

# 목적별 분석 추천 정의
ANALYSIS_RECOMMENDATIONS = {
    "시계열 패턴 탐색": [
        {"type": "시계열 차트", "description": "시간에 따른 값의 변화를 확인하는 기본 분석", "module": "timeseries.py", "chart_types": ["선 그래프", "영역 차트", "산점도"]},
        {"type": "일별/시간별 패턴", "description": "특정 시간대나 요일별 패턴을 탐색하여 반복되는 사이클 식별", "module": "timeseries.py", "chart_types": ["선 그래프", "히트맵"]},
        {"type": "트렌드 분석", "description": "장기적인 추세와 계절성을 확인하여 데이터의 방향성 파악", "module": "trend.py", "chart_types": ["추세선", "이동평균", "계절성 분해"]},
        {"type": "히트맵", "description": "시간-요일 패턴을 한눈에 파악하는 2D 시각화", "module": "heatmap.py", "chart_types": ["시간대별 히트맵", "주기별 히트맵"]},
        {"type": "캔들스틱 차트", "description": "일별 데이터의 시작, 최고, 최저, 종료 값을 표시한 OHLC 분석", "module": "timeseries.py", "chart_types": ["캔들스틱"]},
        {"type": "운전/정지 주기 분석", "description": "장비의 운전/정지 주기를 탐지하고 이상 주기를 식별", "module": "cycle_analysis.py", "chart_types": ["주기 타임라인", "주기 분포", "이상 주기 분석"]}
    ],
    "이상치 탐지": [
        {"type": "이상치 분석", "description": "통계적 방법으로 이상점을 탐지하여 비정상 상태 식별", "module": "anomaly.py", "chart_types": ["Z-Score 분석", "IQR 분석", "DBSCAN", "Isolation Forest"]},
        {"type": "운전/중지 패턴 분리 이상치 분석", "description": "운전 상태와 중지 상태를 구분하여 각 상태별 이상치를 탐지", "module": "anomaly.py", "chart_types": ["상태별 Z-Score 분석", "상태별 이상치 분포"]},
        {"type": "박스 플롯", "description": "그룹별 분포와 이상치를 시각적으로 확인하고 비교", "module": "boxplot.py", "chart_types": ["기본 박스플롯", "그룹화 박스플롯", "시간별 박스플롯"]},
        {"type": "히스토그램", "description": "데이터 분포와 이상치를 식별하여 비정상 빈도 확인", "module": "histogram.py", "chart_types": ["기본 히스토그램", "정규화 히스토그램", "KDE 플롯"]},
        {"type": "변화점 감지", "description": "데이터 패턴의 급격한 변화를 감지하여 이벤트 식별", "module": "anomaly.py", "chart_types": ["CUSUM 분석", "PELT 알고리즘"]},
        {"type": "운전/정지 주기 분석", "description": "정상 주기에서 벗어난 이상 운전/정지 주기를 감지하고 분석", "module": "cycle_analysis.py", "chart_types": ["주기 이상치 분석", "주기 지속시간 분석", "Z-Score 분석"]}
    ],
    "주기성 분석": [
        {"type": "주파수 분석(FFT)", "description": "고속 푸리에 변환을 통한 숨겨진 주기적 패턴 분석", "module": "fft.py", "chart_types": ["주파수 스펙트럼", "파워 스펙트럼", "피크 검출"]},
        {"type": "시간-주파수 분석", "description": "시간에 따른 주파수 특성 변화를 분석하여 동적 패턴 파악", "module": "timefreq.py", "chart_types": ["스펙트로그램", "웨이블릿 변환", "STFT 분석"]},
        {"type": "자기상관 분석", "description": "시계열 데이터의 자기상관성을 측정하여 주기성 확인", "module": "trend.py", "chart_types": ["ACF 플롯", "PACF 플롯"]},
        {"type": "운전/정지 주기 분석", "description": "장비의 운전/정지 사이클을 감지하고 주기적 특성과 패턴을 분석", "module": "cycle_analysis.py", "chart_types": ["주기 타임라인", "주기 분포", "주기 통계 분석"]}
    ],
    "분포 분석": [
        {"type": "히스토그램", "description": "전체 데이터 분포를 확인하여 값의 분포 형태 파악", "module": "histogram.py", "chart_types": ["기본 히스토그램", "누적 히스토그램", "다중 히스토그램"]},
        {"type": "분포 비교", "description": "서로 다른 기간/조건의 분포를 비교하여 변화 감지", "module": "distribution.py", "chart_types": ["중첩 히스토그램", "KDE 중첩", "CDF 비교"]},
        {"type": "박스 플롯", "description": "그룹별 분포를 비교하여 통계적 차이 확인", "module": "boxplot.py", "chart_types": ["그룹화 박스플롯", "시간별 박스플롯"]},
        {"type": "바이올린 플롯", "description": "데이터의 분포 밀도와 형태를 시각적으로 표현하는 분석", "module": "distribution.py", "chart_types": ["기본 바이올린 플롯", "그룹화 바이올린 플롯", "박스-바이올린 결합 플롯"]},
        {"type": "QQ플롯", "description": "데이터의 분포가 정규분포와 얼마나 일치하는지 비교 분석", "module": "histogram.py", "chart_types": ["Normal QQ 플롯", "다양한 분포 QQ 플롯"]},
        {"type": "확률 분포 적합", "description": "데이터에 가장 적합한 확률 분포 모델 식별", "module": "distribution.py", "chart_types": ["분포 적합 테스트", "여러 분포 비교"]}
    ],
    "상관관계 분석": [
        {"type": "상관관계 분석", "description": "변수 간 관계성을 파악하여 상호작용 식별", "module": "correlation.py", "chart_types": ["상관계수 행렬", "히트맵", "산점도 행렬"]},
        {"type": "산점도", "description": "두 변수 간의 관계와 패턴을 시각적으로 확인하는 분석", "module": "correlation.py", "chart_types": ["기본 산점도", "버블 차트", "hexbin 플롯"]},
        {"type": "3D 데이터 시각화", "description": "3차원 공간에서 데이터 관계를 확인하는 심층 분석", "module": "threed.py", "chart_types": ["3D 산점도", "3D 표면 플롯", "3D 와이어프레임"]},
        {"type": "교차 상관 분석", "description": "시간 지연을 고려한 두 변수 간의 상관관계 분석", "module": "correlation.py", "chart_types": ["교차 상관 함수(CCF)", "지연 산점도"]}
    ],
    "패턴 분류": [
        {"type": "패턴 클러스터링", "description": "유사한 패턴을 자동으로 그룹화하여 데이터 세그먼트 식별", "module": "clustering.py", "chart_types": ["K-Means", "계층적 클러스터링", "DBSCAN", "GMM"]},
        {"type": "히트맵", "description": "그룹 간 차이를 시각화하여 패턴 차이 식별", "module": "heatmap.py", "chart_types": ["클러스터 히트맵", "상관관계 히트맵"]},
        {"type": "다차원 축소", "description": "고차원 데이터를 저차원으로 축소하여 패턴 시각화", "module": "clustering.py", "chart_types": ["PCA", "t-SNE", "UMAP"]},
        {"type": "타임 시리즈 클러스터링", "description": "유사한 시간 패턴을 그룹화하여 동작 모드 식별", "module": "pattern.py", "chart_types": ["DTW 클러스터링", "형태 기반 클러스터링"]}
    ],
    "알람 설정": [
        {"type": "경보 및 임계값 설정", "description": "최적의 경보 임계값을 도출하여 이상 상태 감지", "module": "alarm_threshold.py", "chart_types": ["정적 임계값", "동적 임계값", "통계적 공정 관리"]},
        {"type": "이상 패턴 알람", "description": "비정상 패턴 발생 시 알람을 생성하는 시스템 설정", "module": "alarm_threshold.py", "chart_types": ["패턴 기반 알람", "다변량 알람"]},
        {"type": "ROC 분석", "description": "알람 시스템의 성능을 평가하고 최적 임계값 도출", "module": "alarm_threshold.py", "chart_types": ["ROC 곡선", "Precision-Recall 곡선"]}
    ],
    "시계열 예측": [
        {"type": "시계열 예측 모델", "description": "과거 데이터를 기반으로 미래 값을 예측하는 모델 구축", "module": "trend.py", "chart_types": ["ARIMA", "Prophet", "지수 평활법"]},
        {"type": "추세 예측", "description": "장기적인 추세를 예측하여 미래 경향 파악", "module": "trend.py", "chart_types": ["선형 추세", "다항식 추세", "이동평균 기반 예측"]},
        {"type": "계절성 예측", "description": "반복되는 계절 패턴을 예측하여 주기적 변동 예상", "module": "trend.py", "chart_types": ["계절성 분해", "계절 ARIMA", "계절 조정 예측"]}
    ],
    "복합 분석": [
        {"type": "이상-패턴 결합 분석", "description": "이상치와 패턴을 함께 분석하여 복합적 인사이트 도출", "module": "anomaly.py", "chart_types": ["패턴 기반 이상 탐지", "컨텍스트 기반 이상 탐지"]},
        {"type": "다변량 시계열 분석", "description": "여러 센서 데이터를 동시에 분석하여 상호 관계 파악", "module": "correlation.py", "chart_types": ["다변량 시계열 플롯", "교차 상관 분석"]},
        {"type": "이벤트-영향 분석", "description": "특정 이벤트가 시계열 데이터에 미치는 영향 분석", "module": "pattern.py", "chart_types": ["이벤트 전후 비교", "인과 분석 플롯"]}
    ]
} 