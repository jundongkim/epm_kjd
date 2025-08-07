import streamlit as st

def show_landing_page():
    """DX-AI iDSB 소개 랜딩 페이지를 표시합니다."""

    # 메인 소개
    st.markdown("""
    <div style="text-align: center; padding: 20px; margin-bottom: 40px;">
        <h1 style="color: #164193; margin-bottom: 20px;">DX-AI iDSB</h1>
        <h3 style="color: #26A9E0; margin-bottom: 30px;">인터랙티브 데이터 분석 및 예측 시스템</h3>
        <p style="font-size: 18px; color: #444; max-width: 800px; margin: 0 auto;">
            DX-AI iDSB는 다양한 데이터 분석, 시각화 및 AI 기반 예측 기능을 통합하여
            배터리 소재 품질 관리 및 설비 운영 최적화를 위한 강력한 인사이트를 제공합니다.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # 선택된 메뉴 정보를 저장할 세션 상태 변수 초기화
    if 'selected_menu_info' not in st.session_state:
        st.session_state.selected_menu_info = None

    # Streamlit 네이티브 컴포넌트를 사용한 카드 레이아웃 구현
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        icp_card = st.container()
        with icp_card:
            st.markdown("""
            <div style="background-color: white; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); padding: 25px; text-align: center;">
                <div style="font-size: 48px; margin-bottom: 20px; color: #26A9E0;">🧪</div>
                <div style="font-size: 20px; font-weight: 600; color: #164193; margin-bottom: 15px;">ICP 분석</div>
                <div style="font-size: 15px; color: #555; margin-bottom: 15px;">공정별 QCP 데이터를 활용하여 ICP 값을 예측하고, 실시간 품질 모니터링 및 이상 탐지를 수행합니다. AI 기반 분석으로 품질 최적화를 지원합니다.</div>
                <div style="text-align: left; margin-top: 10px; margin-bottom: 20px;">
                    <div style="font-size: 14px; color: #666; margin-bottom: 8px; display: flex; align-items: center;">
                        <span style="color: #26A9E0; margin-right: 8px;">•</span>
                        <span>QCP 데이터 기반 ICP 불량 예측</span>
                    </div>
                    <div style="font-size: 14px; color: #666; margin-bottom: 8px; display: flex; align-items: center;">
                        <span style="color: #26A9E0; margin-right: 8px;">•</span>
                        <span>실시간 품질 이상 탐지</span>
                    </div>
                    <div style="font-size: 14px; color: #666; margin-bottom: 8px; display: flex; align-items: center;">
                        <span style="color: #26A9E0; margin-right: 8px;">•</span>
                        <span>Lot 데이터 시각화 및 분석</span>
                    </div>
                     <div style="font-size: 14px; color: #666; margin-bottom: 8px; display: flex; align-items: center;">
                        <span style="color: #26A9E0; margin-right: 8px;">•</span>
                        <span>AI 기반 예측 결과 분석</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("기능 보기", key="detail_icp"):
                st.session_state.selected_menu_info = "ICP"

    with col2:
        sem_eds_card = st.container()
        with sem_eds_card:
            st.markdown("""
            <div style="background-color: white; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); padding: 25px; text-align: center;">
                <div style="font-size: 48px; margin-bottom: 20px; color: #26A9E0;">🔬</div>
                <div style="font-size: 20px; font-weight: 600; color: #164193; margin-bottom: 15px;">SEM-EDS 분석</div>
                <div style="font-size: 15px; color: #555; margin-bottom: 15px;">iDSB는 복잡한 SEM 이미지와 EDS 스펙트럼 데이터를 통합하여 사용자가 소재의 미세 구조와 원소 조성을 직관적으로 이해하고 분석할 수 있도록 지원합니다.</div>
                 <div style="text-align: left; margin-top: 10px; margin-bottom: 20px;">
                    <div style="font-size: 14px; color: #666; margin-bottom: 8px; display: flex; align-items: center;">
                        <span style="color: #26A9E0; margin-right: 8px;">•</span>
                        <span>고해상도 이미지 뷰어</span>
                    </div>
                    <div style="font-size: 14px; color: #666; margin-bottom: 8px; display: flex; align-items: center;">
                        <span style="color: #26A9E0; margin-right: 8px;">•</span>
                        <span>EDS 스펙트럼 인터랙티브 분석</span>
                    </div>
                    <div style="font-size: 14px; color: #666; margin-bottom: 8px; display: flex; align-items: center;">
                        <span style="color: #26A9E0; margin-right: 8px;">•</span>
                        <span>원소 맵핑 및 중첩 시각화</span>
                    </div>
                     <div style="font-size: 14px; color: #666; margin-bottom: 8px; display: flex; align-items: center;">
                        <span style="color: #26A9E0; margin-right: 8px;">•</span>
                        <span>통합 분석 보고서 생성</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("기능 보기", key="detail_sem_eds"):
                st.session_state.selected_menu_info = "SEM-EDS"

    with col3:
        cmms_card = st.container()
        with cmms_card:
            st.markdown("""
            <div style="background-color: white; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); padding: 25px; text-align: center;">
                <div style="font-size: 48px; margin-bottom: 20px; color: #26A9E0;">🛠️</div>
                <div style="font-size: 20px; font-weight: 600; color: #164193; margin-bottom: 15px;">CMMS 시스템</div>
                <div style="font-size: 15px; color: #555; margin-bottom: 15px;">AI 기반 챗봇, 이미지 관리, 유사 사례 검색을 통해 설비 유지보수 업무를 효율화하고 지원합니다.</div>
                 <div style="text-align: left; margin-top: 10px; margin-bottom: 20px;">
                    <div style="font-size: 14px; color: #666; margin-bottom: 8px; display: flex; align-items: center;">
                        <span style="color: #26A9E0; margin-right: 8px;">•</span>
                        <span>AI 유지보수 챗봇 지원</span>
                    </div>
                    <div style="font-size: 14px; color: #666; margin-bottom: 8px; display: flex; align-items: center;">
                        <span style="color: #26A9E0; margin-right: 8px;">•</span>
                        <span>작업 이미지 관리 및 분석</span>
                    </div>
                    <div style="font-size: 14px; color: #666; margin-bottom: 8px; display: flex; align-items: center;">
                        <span style="color: #26A9E0; margin-right: 8px;">•</span>
                        <span>유사 유지보수 사례 검색</span>
                    </div>
                    <div style="font-size: 14px; color: #666; margin-bottom: 8px; display: flex; align-items: center;">
                        <span style="color: #26A9E0; margin-right: 8px;">•</span>
                        <span>의미론적 분석 및 통계</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("기능 보기", key="detail_cmms"):
                st.session_state.selected_menu_info = "CMMS"

    with col4:
        fwhm_card = st.container()
        with fwhm_card:
            st.markdown("""
            <div style="background-color: white; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); padding: 25px; text-align: center;">
                <div style="font-size: 48px; margin-bottom: 20px; color: #26A9E0;">📈</div>
                <div style="font-size: 20px; font-weight: 600; color: #164193; margin-bottom: 15px;">반가폭 분석</div>
                <div style="font-size: 15px; color: #555; margin-bottom: 15px;">XRD 데이터 기반 반가폭(FWHM) 분석, 시각화 및 AI 예측을 통해 소재 결정성, 입자 크기 등
                중요 품질 지표를 평가하고, 공정 조건과의 상관관계를 파악하여 품질 개선을 지원합니다.</div>
                 <div style="text-align: left; margin-top: 10px; margin-bottom: 20px;">
                    <div style="font-size: 14px; color: #666; margin-bottom: 8px; display: flex; align-items: center;">
                        <span style="color: #26A9E0; margin-right: 8px;">•</span>
                        <span>FWHM 데이터 개요 시각화</span>
                    </div>
                    <div style="font-size: 14px; color: #666; margin-bottom: 8px; display: flex; align-items: center;">
                        <span style="color: #26A9E0; margin-right: 8px;">•</span>
                        <span>품질 영향 요인 분석</span>
                    </div>
                    <div style="font-size: 14px; color: #666; margin-bottom: 8px; display: flex; align-items: center;">
                        <span style="color: #26A9E0; margin-right: 8px;">•</span>
                        <span>CatBoost/XGBoost 예측 모델</span>
                    </div>
                    <div style="font-size: 14px; color: #666; margin-bottom: 8px; display: flex; align-items: center;">
                        <span style="color: #26A9E0; margin-right: 8px;">•</span>
                        <span>대화형 시뮬레이션 도구</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("기능 보기", key="detail_fwhm"):
                st.session_state.selected_menu_info = "반가폭"

    with col5:
        process_history_card = st.container()
        with process_history_card:
            st.markdown("""
            <div style="background-color: white; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); padding: 25px; text-align: center;">
                <div style="font-size: 48px; margin-bottom: 20px; color: #26A9E0;">🏭</div>
                <div style="font-size: 20px; font-weight: 600; color: #164193; margin-bottom: 15px;">생산관리이력</div>
                <div style="font-size: 15px; color: #555; margin-bottom: 15px;">생산 관리 이력을 체계적으로 기록하고 분석하여 생산 변경에 따른 영향을 추적하고 품질 변동 원인을 파악합니다.</div>
                 <div style="text-align: left; margin-top: 10px; margin-bottom: 20px;">
                    <div style="font-size: 14px; color: #666; margin-bottom: 8px; display: flex; align-items: center;">
                        <span style="color: #26A9E0; margin-right: 8px;">•</span>
                        <span>생산 관리 챗봇 인터페이스</span>
                    </div>
                    <div style="font-size: 14px; color: #666; margin-bottom: 8px; display: flex; align-items: center;">
                        <span style="color: #26A9E0; margin-right: 8px;">•</span>
                        <span>유사 케이스 검색</span>
                    </div>
                    <div style="font-size: 14px; color: #666; margin-bottom: 8px; display: flex; align-items: center;">
                        <span style="color: #26A9E0; margin-right: 8px;">•</span>
                        <span>텍스트 기반 지식 검색</span>
                    </div>
                    <div style="font-size: 14px; color: #666; margin-bottom: 8px; display: flex; align-items: center;">
                        <span style="color: #26A9E0; margin-right: 8px;">•</span>
                        <span>생산 변화 영향 분석</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("기능 보기", key="detail_process_history"):
                st.session_state.selected_menu_info = "생산관리이력"

    # 선택된 메뉴에 대한 상세 정보 표시 (기능 중심으로 수정)
    if st.session_state.selected_menu_info:
        st.markdown("---")

        if st.session_state.selected_menu_info == "ICP":
            st.markdown("""
            <h2 style="color: #164193; margin-bottom: 20px; text-align: center;">🧪 ICP 분석 기능</h2>
            """, unsafe_allow_html=True)

            st.markdown("""
            iDSB의 ICP 분석 모듈은 QPC 데이터를 활용하여 비용과 시간이 소요되는 실제 ICP 측정을 보완하고,
            선제적인 품질 관리를 가능하게 합니다.

            ### 📌 핵심 기능

            - **🧠 AI 예측 모델:** 공정별 QPC 데이터를 기반으로 ICP 양호/불량 여부를 정확하게 예측합니다.
            - **📈 실시간 모니터링:** 예측된 ICP 값의 추이를 실시간으로 시각화하여 품질 변동성을 즉시 파악합니다.
            - **⚠️ 이상 탐지 알림:** 설정된 관리 기준을 벗어나는 예측값이 발생하면 자동으로 알림을 제공합니다.
            - **📊 Lot 데이터 분석:** 다양한 Lot 데이터를 시각화하고 비교 분석하여 경향성을 파악합니다.
            - **🚀 시뮬레이션:** 과거 예측 검증 및 미래 ICP 예측 시뮬레이션을 통해 품질 향상을 지원합니다.
            - **📊 XAI 분석:** 설명 가능한 AI로 예측 결과의 원인과 영향 요인을 해석합니다.
            """)

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("""
                ### 🔍 Level-2 상세 기능

                #### 1. 데이터 탐색 및 전처리
                - **데이터 필터링:** 공정, 날짜, 배치 ID 등 다양한 조건으로 데이터 필터링
                - **이상치 탐지:** 통계적 방법을 활용한 이상치 자동 식별 및 처리
                - **결측치 처리:** 고급 알고리즘을 통한 결측 데이터 보간
                - **데이터 정규화:** 다양한 스케일의 데이터를 표준화하여 분석 정확도 향상

                #### 2. 예측 모델 관리
                - **모델 선택:** Random Forest, XGBoost 등 다양한 알고리즘 지원
                - **하이퍼파라미터 최적화:** 베이지안 최적화를 통한 모델 성능 극대화
                - **앙상블 기법:** 다중 모델 앙상블을 통한 예측 안정성 향상
                - **모델 평가 대시보드:** 정확도, 정밀도, 재현율, F1 등 성능 지표 시각화

                #### 3. 시뮬레이션 기능
                - **과거 데이터 검증:** 기존 데이터로 모델 예측 성능 검증 및 분석
                - **미래 예측 시뮬레이션:** 신규 QCP 값 입력으로 ICP 불량 여부 예측
                - **AI 분석 리포트:** 예측 결과에 대한 AI 기반 심층 분석 제공
                - **영향 요인 분석:** 주요 영향 QCP 요인 식별 및 시각화
                """)

            with col2:
                st.markdown("""
                ### 💡 활용 예시

                #### 예시 1: 불량 예측 및 방지
                ```
                공정 QCP 데이터 입력
                → XGBoost 모델로 ICP 불량 가능성 예측
                → 불량 확률 85.3% 감지
                → 주요 영향 요인 식별: qcp_076, qcp_042
                → 공정 조건 조정으로 불량 예방
                → AI 분석 결과로 조치사항 확인
                ```

                #### 예시 2: 품질 변동성 분석
                ```
                과거 예측 데이터 검증 분석
                → 정확도 92.8%, 재현율 88.5% 확인
                → 불량 예측 신뢰성 분석
                → 오탐지(False Positive) 패턴 식별
                → 모델 재학습 방향 도출
                → 예측 성능 개선
                ```

                #### 예시 3: 실시간 품질 관리
                ```
                실시간 QCP 데이터 모니터링
                → 불량 확률 상승 추세 감지
                → 영향 요인 자동 분석
                → 특정 공정 변수 편차 확인
                → 생산라인 점검 및 조정
                → 품질 안정화 달성
                ```

                #### 예시 4: 공정 최적화
                ```
                다양한 QCP 조합 시뮬레이션
                → 최적의 QCP 프로파일 도출
                → 불량률 최소화 조건 식별
                → 공정 제어 변수 최적화
                → 품질 향상 및 원가 절감
                → AI 예측 정확도 검증
                ```
                """)

            with st.expander("💡 ICP 예측의 활용 방안"):
                st.write("""
                - **품질 향상:** 불량 원인 조기 식별로 품질 안정성 강화
                - **비용 절감:** 불필요한 검사 감소 및 불량률 감소로 원가 절감
                - **생산성 향상:** 실시간 불량 예측으로 생산 중단 최소화
                - **의사결정 지원:** 데이터 기반 품질 관리 의사결정 강화
                - **자원 최적화:** 검사 공정 최적화로 자원 효율성 증대
                - **신규 개발 지원:** 신제품/신공정 개발 시 품질 예측 지원
                - **공정 최적화:** 불량 발생 최소화를 위한 공정 조건 최적화
                - **AI 기반 분석:** 전문가 지식과 AI 분석의 결합으로 인사이트 도출
                """)

        elif st.session_state.selected_menu_info == "SEM-EDS":
            st.markdown("""
            <h2 style="color: #164193; margin-bottom: 20px; text-align: center;">🔬 SEM-EDS 분석 기능</h2>
            """, unsafe_allow_html=True)

            st.markdown("""
            iDSB는 복잡한 SEM 이미지와 EDS 스펙트럼 데이터를 통합하여 사용자가 소재의 미세 구조와
            원소 조성을 직관적으로 이해하고 분석할 수 있도록 지원합니다.

            ### 📌 핵심 기능

            - **🖼️ SEM 이물 분석:** 이물의 크기, 질감, 형태, 개수 등의 물리적 특성을 분석하여 발생 원인 설비를 유추합니다.
            - **📊 EDS 성분 분석:** 검출된 이물의 원소 조성을 정밀하게 분석하여 강종을 유추하고 오염원을 식별합니다.
            - **🗺️ 원소 맵핑 시각화:** 분석된 영역 내 원소들의 공간적 분포를 컬러 맵으로 시각화하여 직관적인 이해를 돕습니다.
            - **➕ 이미지/맵 중첩:** SEM 이미지 위에 특정 원소의 맵핑 결과를 중첩하여 형태와 조성의 관계를 분석합니다.
            - **📝 통합 분석 보고서:** SEM 이미지와 EDS 분석 결과를 종합한 맞춤형 보고서를 자동으로 생성합니다.
            """)

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("""
                ### 🔍 Level-2 상세 기능

                #### 1. 이물 형태 분석 (SEM)
                - **크기 측정:** 이물의 크기 분포 및 통계 분석
                - **형상 분석:** 이물의 형태 특성(원형도, 종횡비 등) 정량화
                - **표면 질감 분석:** 이물 표면의 미세 질감 특성 분석
                - **집계 분석:** 단위 면적당 이물 개수 및 분포 패턴 분석

                #### 2. 성분 분석 (EDS)
                - **원소 정량화:** 이물에 포함된 원소의 정확한 비율 측정
                - **강종 데이터베이스:** 다양한 강종별 표준 성분 DB와 비교
                - **미량 원소 감지:** 극미량으로 존재하는 특성 원소 검출
                - **성분 프로파일링:** 검출된 원소 패턴 기반 오염원 특성화

                #### 3. 원인 설비 추적
                - **설비 프로파일링:** 각 공정 설비별 특성 이물 데이터베이스 구축
                - **패턴 매칭:** 이물 특성과 설비 프로파일 간 패턴 매칭
                - **유사 사례 검색:** 과거 이물 발생 케이스와의 유사도 분석
                - **오염 경로 추적:** 이물 특성 기반 오염 경로 역추적
                """)

            with col2:
                st.markdown("""
                ### 💡 활용 예시

                #### 예시 1: 금속 이물 분석
                ```
                SEM 이미지에서 금속성 이물 영역 발견
                → 크기(25μm), 형태(선형), 표면(마모흔) 정량화
                → EDS 분석으로 Fe(69%), Cr(18%), Ni(9%) 성분 확인
                → SUS304 스테인리스강으로 유추
                → 설비 DB 대조 결과 믹서 교반 날 마모 추정
                → 설비 점검 및 교체로 이물 혼입 방지
                ```

                #### 예시 2: 복합 오염물 분석
                ```
                표면 이물 SEM 스캔 실시
                → 다양한 크기(0.5-20μm)의 입자 클러스터 발견
                → 이물 분포 패턴 분석(선형 분포)
                → EDS 맵핑으로 다중 원소 분포 확인
                → Al, Si 함량 기반 알루미나 실리케이트 판정
                → 특정 이송 벨트의 마모 추정
                → 예방 정비 일정 최적화
                ```

                #### 예시 3: 미량 이물 오염원 추적
                ```
                품질 이상 검출 샘플 SEM 분석
                → 미세 입자(1-5μm) 불규칙 분포 확인
                → 표면 형태로 기계 가공 잔여물 추정
                → EDS 분석 결과 텅스텐(W) 검출
                → 텅스텐 함유 부품/공구 목록 확인
                → 가공 공정 후 세척 공정 개선
                → 이물 검출률 90% 감소 확인
                ```

                #### 예시 4: 설비 마모 패턴 식별
                ```
                정기 검사에서 특이 이물 검출
                → SEM으로 형상 및 크기 분포 분석
                → 마모 패턴 기반 파쇄형 이물로 분류
                → EDS로 특수강 합금 성분 확인
                → 특정 펌프 임펠러 마모 패턴과 일치
                → 예방적 설비 교체로 대형 고장 방지
                → 설비 수명 패턴 데이터베이스 강화
                ```
                """)

            with st.expander("💡 SEM-EDS 분석의 활용 방안"):
                st.write("""
                - 이물 혼입 원인 설비의 신속한 식별 및 대응
                - 이물의 물리적/화학적 특성을 통한 오염원 추적
                - 강종별 특성 데이터베이스 구축 및 자동 판별
                - 설비 마모 패턴 분석을 통한 예방 정비 계획 수립
                - 공정별 이물 발생 패턴 모니터링 및 경향성 분석
                - 이물 혼입 메커니즘 이해를 통한 공정 개선
                - 설비 구성 요소의 마모 특성 및 수명 예측
                - 품질 검사 기준 및 방법 최적화
                """)

        elif st.session_state.selected_menu_info == "CMMS":
            st.markdown("""
            <h2 style="color: #164193; margin-bottom: 20px; text-align: center;">🛠️ CMMS 시스템 기능</h2>
            """, unsafe_allow_html=True)

            st.markdown("""
            iDSB의 CMMS는 AI 기술을 접목하여 설비 유지보수 기록을 체계적으로 관리하고,
            데이터 기반의 효율적인 유지보수 전략 수립을 지원합니다.

            ### 📌 핵심 기능

            - **🤖 AI 유지보수 챗봇:** 설비 문제 발생 시 자연어 질의를 통해 관련 매뉴얼, 과거 사례, 해결 절차 등의 정보를 신속하게 제공합니다.
            - **📸 작업 이미지 관리:** 유지보수 작업 전/후 사진 등 관련 이미지를 작업 기록과 함께 저장하고 시각적으로 관리합니다.
            - **🔎 유사 사례 검색:** 현재 발생한 문제와 유사한 과거 유지보수 사례를 시맨틱 검색 기술을 통해 빠르고 정확하게 찾아 제시합니다.
            - **📚 의미론적 분석:** 유지보수 텍스트 데이터의 의미론적 분석을 통해 패턴과 인사이트를 도출합니다.
            - **📊 유지보수 통계 분석:** 설비별 고장 빈도, 평균 수리 시간(MTTR), 평균 고장 간격(MTBF) 등 주요 지표를 시각화하고 분석 리포트를 제공합니다.
            """)

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("""
                ### 🔍 Level-2 상세 기능

                #### 1. AI 챗봇 지원 시스템
                - **자연어 처리:** 기술적 용어와 일상 언어를 모두 이해하는 지능형 인터페이스
                - **맥락 인식:** 대화 맥락을 고려한 정확한 정보 제공
                - **멀티모달 입출력:** 텍스트뿐만 아니라 이미지도 함께 분석하여 답변
                - **대화 흐름 관리:** 추가 질문 유도 및 문제 해결 가이드 제공

                #### 2. 이미지 관리 및 분석
                - **이미지 태깅:** AI 기반 자동 태깅으로 빠른 이미지 분류
                - **이미지 비교:** 작업 전/후 이미지 자동 비교 및 변화 감지
                - **결함 자동 감지:** 설비 이미지에서 잠재적 결함 자동 식별
                - **OCR 기능:** 이미지 내 텍스트 자동 인식 및 데이터 추출

                #### 3. 의미론적 분석
                - **토픽 모델링:** 유지보수 문서에서 주요 토픽 자동 추출
                - **패턴 인식:** 반복적 문제 및 해결 패턴 식별
                - **텍스트 마이닝:** 유지보수 텍스트의 키워드 및 용어 분석
                - **시각적 네트워크:** 문제-원인-해결책 간의 관계 시각화
                """)

            with col2:
                st.markdown("""
                ### 💡 활용 예시

                #### 예시 1: 트러블슈팅 지원
                ```
                "믹서 모터 과열 현상" 문제 챗봇에 입력
                → 유사 사례 3건 검색 및 제시
                → 가장 유사한 사례의 해결 방법 제안
                → 베어링 마모 의심, 점검 체크리스트 제공
                → 현장 점검으로 문제 확인 및 해결
                ```

                #### 예시 2: 예방 정비 계획 수립
                ```
                설비 A의 고장 이력 통계 분석
                → 주요 부품별 수명 주기 패턴 파악
                → 최적 교체 주기 예측 모델 생성
                → 계획 정비 일정 자동 생성
                → 가동률 8% 향상, 비계획 정지 63% 감소
                ```

                #### 예시 3: 지식 전수 및 교육
                ```
                신입 엔지니어가 난해한 문제 직면
                → 챗봇을 통한 문제 설명 및 이미지 업로드
                → 유사 사례 및 경험자 추천 제시
                → 단계별 해결 가이드 제공
                → 문제 해결 및 지식 습득으로 역량 향상
                ```

                #### 예시 4: 부품 재고 최적화
                ```
                주요 부품 사용 패턴 분석
                → 계절성, 설비 가동률 기반 수요 예측
                → 적정 재고 수준 계산 및 발주 시점 알림
                → 긴급 구매 비용 30% 절감
                → 재고 유지 비용 25% 감소
                ```
                """)

            with st.expander("💡 CMMS 시스템의 활용 방안"):
                st.write("""
                - 신속한 문제 해결 지원으로 설비 가동 중단 시간 최소화
                - 과거 사례 분석을 통한 동일 문제 재발 방지
                - 데이터 기반 예방 정비 계획 수립
                - 유지보수 작업 표준화 및 작업자 역량 상향 평준화
                - 부품 재고 관리 최적화
                - 설비 이력 관리를 통한 총소유비용(TCO) 최적화
                - 설비 수명 주기 분석 및 교체 시점 예측
                - 작업자별 전문성 관리 및 교육 계획 수립
                """)

        elif st.session_state.selected_menu_info == "반가폭":
            st.markdown("""
            <h2 style="color: #164193; margin-bottom: 20px; text-align: center;">📈 반가폭 분석 기능</h2>
            """, unsafe_allow_html=True)

            st.markdown("""
            iDSB는 X선 회절(XRD) 데이터로부터 계산된 반가폭(FWHM) 값을 분석하여 소재의 결정성, 입자 크기 등
            중요 품질 지표를 평가하고, 공정 조건과의 상관관계를 파악하여 품질 개선을 지원합니다.

            ### 📌 핵심 기능

            - **📉 데이터 시각화:** 반가폭 데이터의 분포, 추세, 공정 조건별 변화 등을 다양한 차트로 시각화합니다.
            - **🎯 품질 영향 요인 분석:** 다양한 공정 변수 중, 반가폭 값에 가장 큰 영향을 미치는 요인을 AI 모델(Feature Importance)을 통해 식별합니다.
            - **🔮 다중 AI 예측 모델:** CatBoost와 XGBoost 기반 모델을 통해 현재 공정 조건이나 새로운 조건에서 예상되는 반가폭 값을 예측합니다.
            - **⚙️ 공정 조건 최적화:** 목표 반가폭 값을 달성하기 위한 최적의 공정 조건 조합을 탐색하고 제안합니다.
            - **🔄 대화형 시뮬레이션:** 실시간으로 반가폭 데이터를 모니터링하고, 사용자가 직접 조건을 변경하며 결과를 시뮬레이션할 수 있습니다.
            """)

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("""
                ### 🔍 Level-2 상세 기능

                #### 1. 반가폭 데이터 관리 및 분석
                - **데이터 로드 및 정규화:** 외부 FWHM 데이터 로드 및 전처리
                - **다차원 데이터 시각화:** 다양한 차트로 반가폭 데이터 탐색
                - **데이터 개요 대시보드:** 핵심 통계 및 분포 한눈에 파악
                - **데이터 필터링 및 그룹화:** 조건별 데이터 추출 및 분석

                #### 2. 모델 학습 및 평가
                - **CatBoost 모델링:** 유연하고 강력한 부스팅 알고리즘 적용
                - **XGBoost 모델링:** 고성능 그래디언트 부스팅 구현
                - **모델 성능 비교:** 다양한 메트릭으로 모델 성능 평가
                - **교차 검증:** K-폴드 교차 검증으로 모델 안정성 검증

                #### 3. 시뮬레이션 환경
                - **대화형 파라미터 조정:** 슬라이더로 공정 변수 실시간 조정
                - **민감도 분석:** 변수별 반가폭 변화 민감도 시각화
                - **목표 기반 최적화:** 목표 반가폭에 맞는 조건 자동 탐색
                - **시뮬레이션 결과 비교:** 다양한 시나리오 결과 비교 분석
                """)

            with col2:
                st.markdown("""
                ### 💡 활용 예시

                #### 예시 1: 소재 특성 최적화
                ```
                목표 반가폭 값 설정: 0.25° ± 0.02°
                → 현재 공정 조건으로 예측 반가폭: 0.31°
                → 영향 요인 분석: 열처리 온도>시간>압력 순
                → 최적 공정 조건 도출: 850°C, 4시간, 5bar
                → 적용 결과: 반가폭 0.26° 달성
                ```

                #### 예시 2: 공정 변동성 관리
                ```
                최근 반가폭 데이터의 변동성 증가 감지
                → 주요 원인 변수 식별: 원료 혼합 비율 변동
                → 시간별, 작업자별, 설비별 편차 분석
                → 혼합 공정 표준화 방안 수립
                → 반가폭 표준편차 40% 감소
                ```

                #### 예시 3: 신규 조성 개발
                ```
                기존 소재의 반가폭-물성 관계 모델 구축
                → 신규 조성의 반가폭 예측: 0.29°
                → 결정자 크기 및 물성 예측
                → 실험 검증으로 예측 정확도 확인
                → 개발 주기 30% 단축
                ```

                #### 예시 4: 실시간 품질 관리
                ```
                생산 라인의 실시간 XRD 데이터 모니터링
                → 반가폭 값 추이 차트로 시각화
                → 관리 한계 이탈 조기 감지
                → 주요 공정 변수 자동 조정 제안
                → 불량률 25% 감소, 수율 8% 향상
                ```
                """)

            with st.expander("💡 반가폭 분석의 활용 방안"):
                st.write("""
                - 제품의 결정성 및 균일성 평가를 통한 품질 관리 강화
                - 공정 조건 변화가 제품 품질에 미치는 영향 분석 및 예측
                - 최적의 생산 조건 탐색을 통한 수율 향상 및 원가 절감
                - 신규 소재 개발 시 품질 목표 설정 및 달성 지원
                - R&D 단계에서의 실험 횟수 감소 및 개발 기간 단축
                - 원료 변경 시 품질 영향 사전 평가 및 대응 방안 수립
                - 결정학적 특성과 전기화학적 성능 간의 상관관계 분석
                - 배치간 일관성 평가 및 품질 편차 원인 분석
                """)

        elif st.session_state.selected_menu_info == "생산관리이력":
            st.markdown("""
            <h2 style="color: #164193; margin-bottom: 20px; text-align: center;">🏭 생산관리이력 기능</h2>
            """, unsafe_allow_html=True)

            st.markdown("""
            iDSB의 생산관리이력 모듈은 제품 생산 과정의 변경사항을 체계적으로 기록하고 추적하여,
            제품 및 공정 변화가 품질에 미치는 영향을 분석하고 최적 생산 조건을 유지하는데 도움을 줍니다.

            ### 📌 핵심 기능

            - **🤖 생산 관리 챗봇:** 생산 관련 질문에 자연어로 응답하고 관련 지식과 이력 정보를 제공합니다.
            - **🔍 유사 케이스 검색:** 현재 상황과 유사한 과거 생산 관리 사례를 검색하여 문제 해결을 지원합니다.
            - **📚 지식 베이스 검색:** 생산 문서, 매뉴얼, 절차서 등에서 필요한 정보를 신속하게 찾아 제공합니다.
            - **📊 생산 변화 영향 분석:** 생산 변경 전후의 품질 데이터를 비교하여 변경이 미친 영향을 정량적으로 평가합니다.
            - **📈 생산 성능 모니터링:** 기간별, 라인별 생산 성능 지표를 시각화하여 장기적인 추세와 계절성을 분석합니다.
            """)

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("""
                ### 🔍 Level-2 상세 기능

                #### 1. 생산 문서 관리
                - **문서 색인화:** 생산 관련 문서의 자동 색인 및 임베딩
                - **벡터 DB 구축:** 시맨틱 검색을 위한 벡터 데이터베이스 구축
                - **질의응답 시스템:** 문서 기반 Q&A를 통한 정보 추출
                - **문서 간 연결성:** 관련 문서 간의 자동 연결 및 탐색

                #### 2. 생산 챗봇 인터페이스
                - **자연어 이해:** 복잡한 생산 관련 질문 이해 및 처리
                - **맥락 유지:** 대화 흐름에 따른 맥락 인식 및 유지
                - **참조 제공:** 답변 출처 및 관련 문서 참조 제공
                - **제안 기능:** 관련 질문 및 탐색 방향 제안

                #### 3. 생산 변경 분석
                - **변경 이력 추적:** 생산 파라미터 변경 이력 시각화
                - **품질 영향 평가:** 변경 전후 품질 지표 비교 분석
                - **상관관계 분석:** 생산 변수와 품질 간의 상관관계 탐색
                - **리스크 평가:** 생산 변경에 따른 잠재적 리스크 분석
                """)

            with col2:
                st.markdown("""
                ### 💡 활용 예시

                #### 예시 1: 생산 지식 탐색
                ```
                "CDS183 제품의 최적 생산 조건은?" 질문
                → 관련 생산 문서 자동 검색
                → 전문가 지식과 운영 이력 분석
                → "5Line 최적 조건은 [조건값], 참조: 생산매뉴얼 p.42" 응답
                → 관련 생산 변경 이력 및 영향 제시
                ```

                #### 예시 2: 문제 해결 지원
                ```
                "금속이물 상승 원인" 질문
                → 유사 문제 발생 사례 3건 검색
                → 가장 유사한 케이스 상세 제시
                → 해결을 위한 점검 항목 자동 생성
                → 원인-해결책 매핑 제안
                ```

                #### 예시 3: 생산 최적화
                ```
                특정 제품의 최적 생산 조건 탐색
                → 과거 고품질 생산 시점의 설정 분석
                → 생산성과 품질 간의 트레이드오프 평가
                → 계절적 요인을 고려한 최적 파라미터 제안
                → 적용 결과 수율 3.5% 개선
                ```

                #### 예시 4: 생산 변경 이력 분석
                ```
                최근 6개월 생산 변경 요약 요청
                → 주요 변경 항목 자동 분류 및 요약
                → 변경별 품질 영향 정량화
                → 긍정적/부정적 영향 변경 구분
                → 향후 최적화 방향 제안
                ```
                """)

            with st.expander("💡 생산관리이력의 활용 방안"):
                st.write("""
                - 품질 문제 발생 시 신속한 원인 추적 및 해결
                - 생산 변경의 영향을 객관적으로 평가하여 의사결정 지원
                - 생산 변경 관리 프로세스 개선 및 표준화
                - 생산 최적화를 위한 성공 사례 데이터베이스 구축
                - 신규 라인 도입 시 초기 파라미터 설정 가이드 제공
                - 작업자별 생산 운영 패턴 분석 및 표준화
                - 품질 변동의 계절적 요인 분석 및 대응
                - 규제 대응 및 품질 감사를 위한 변경 이력 문서화
                """)

        else: # 기본 랜딩 페이지 내용 (선택된 메뉴 없을 시)
            st.markdown("""
            <h2 style="color: #164193; margin-bottom: 20px; text-align: center;">🚀 EcoPro BM iDSB 시작하기</h2>
            """, unsafe_allow_html=True)

            st.markdown("""
            > 데이터 기반 의사결정을 위한 통합 분석 환경

            EcoPro BM iDSB는 배터리 소재 생산 및 연구 과정에서 발생하는 다양한 데이터를
            효과적으로 분석하고 활용할 수 있도록 설계된 통합 플랫폼입니다.
            각 분석 모듈은 상호 연동되어 시너지를 창출하며, AI 기술을 통해 더 깊이 있는 인사이트를 제공합니다.

            **iDSB 통합 플랫폼의 강점:**

            - **⚡ 실시간 데이터 연동:** 분석 모듈 간 데이터가 실시간으로 연동되어 일관성 있는 분석 환경을 제공합니다.
            - **🔄 지능형 분석:** AI 모델이 데이터를 학습하여 예측 정확도를 지속적으로 향상시키고 새로운 패턴을 발견합니다.
            - **🛡️ 체계적인 관리:** 데이터 접근 권한 관리 및 분석 이력 추적 기능으로 데이터 보안과 신뢰성을 확보합니다.
            - **📱 유연한 접근성:** 데스크톱, 태블릿 등 다양한 환경에서 접근하여 언제 어디서든 데이터 기반 업무를 수행할 수 있습니다.

            **시작하려면 상단의 카드 메뉴에서 관심 있는 분석 기능을 선택하세요!**
            """)

    # 하단 정보 영역 (기존 유지)
    st.markdown("""
    <div style="margin-top: 30px; text-align: center; padding: 20px; background-color: #f8f9fa; border-radius: 8px;">
        <h4 style="color: #164193; margin-bottom: 15px;">DX-AI iDSB의 핵심 가치</h4>
        <div style="display: flex; flex-wrap: wrap; justify-content: center; gap: 20px; margin-bottom: 20px;">
            <div style="text-align: center; min-width: 120px;">
                <div style="font-size: 24px; color: #26A9E0; margin-bottom: 8px;">📊</div>
                <div style="font-weight: 600; margin-bottom: 5px;">데이터 시각화</div>
                <div style="font-size: 14px; color: #666;">직관적 이해 증진</div>
            </div>
            <div style="text-align: center; min-width: 120px;">
                <div style="font-size: 24px; color: #26A9E0; margin-bottom: 8px;">🤖</div>
                <div style="font-weight: 600; margin-bottom: 5px;">AI 기반 분석</div>
                <div style="font-size: 14px; color: #666;">심층 인사이트 도출</div>
            </div>
            <div style="text-align: center; min-width: 120px;">
                <div style="font-size: 24px; color: #26A9E0; margin-bottom: 8px;">🔄</div>
                <div style="font-weight: 600; margin-bottom: 5px;">실시간 상호작용</div>
                <div style="font-size: 14px; color: #666;">신속한 의사결정 지원</div>
            </div>
            <div style="text-align: center; min-width: 120px;">
                <div style="font-size: 24px; color: #26A9E0; margin-bottom: 8px;">🔗</div>
                <div style="font-weight: 600; margin-bottom: 5px;">데이터 통합</div>
                <div style="font-size: 14px; color: #666;">분석 효율성 극대화</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)