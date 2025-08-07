"""
DX-AI Manufacturing Copilot - 프로세스 관리 페이지

Lot 추적, 설비 모니터링, 실시간 이상탐지 및 알림 시스템 페이지입니다.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.core.chat_manager import ChatManager, setup_chat_sidebar
from src.core.tab_chat_managers import (
    LotTrackingChatManager, 
    EquipmentMonitoringChatManager, 
    AnomalyDetectionChatManager
)
from src.core.process_management_engine import (
    LotTrackingEngine,
    EquipmentMonitoringEngine,
    AnomalyDetectionEngine
)
from src.utils.process_utils import (
    ProcessDateFilter,
    ProcessDataFormatter,
    ProcessLotManager,
    ProcessMetricsCalculator,
    format_process_period_info,
    get_process_status_emoji,
    prepare_lot_display_data
)


def process_management_page():
    """프로세스 관리 페이지"""
    st.markdown("## ⚙️ 프로세스 관리")
    
    # 엔진 인스턴스 생성
    if 'lot_tracking_engine' not in st.session_state:
        st.session_state.lot_tracking_engine = LotTrackingEngine()
    
    if 'equipment_monitoring_engine' not in st.session_state:
        st.session_state.equipment_monitoring_engine = EquipmentMonitoringEngine()
    
    if 'anomaly_detection_engine' not in st.session_state:
        st.session_state.anomaly_detection_engine = AnomalyDetectionEngine()
    
    # ChatManager 인스턴스 생성
    if 'chat_manager' not in st.session_state:
        st.session_state.chat_manager = ChatManager()
    
    chat_manager = st.session_state.chat_manager
    
    # 탭별 챗봇 매니저 초기화
    if 'lot_tracking_chat' not in st.session_state:
        st.session_state.lot_tracking_chat = LotTrackingChatManager(chat_manager)
    
    if 'equipment_monitoring_chat' not in st.session_state:
        st.session_state.equipment_monitoring_chat = EquipmentMonitoringChatManager(chat_manager)
    
    if 'anomaly_detection_chat' not in st.session_state:
        st.session_state.anomaly_detection_chat = AnomalyDetectionChatManager(chat_manager)
    
    # 사이드바에 챗봇 설정 추가
    setup_chat_sidebar(chat_manager)
    
    # 공통 조회 조건
    st.markdown("### 📅 조회 조건")
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        common_date_filter = st.selectbox(
            "📅 조회 기간",
            ["오늘", "어제", "최근 3일", "최근 1주", "최근 1개월", "전체", "사용자 정의"],
            index=2,  # 기본값: 최근 3일
            help="모든 탭에서 동일한 날짜 기준으로 데이터를 조회합니다."
        )
    
    with col2:
        refresh_data = st.button("🔄 데이터 새로고침", help="최신 데이터로 업데이트")
    
    with col3:
        realtime_mode = st.checkbox("🔴 실시간 모드", help="실시간 데이터 업데이트")
    
    # 사용자 정의 날짜 필터
    common_start_date = None
    common_end_date = None
    if common_date_filter == "사용자 정의":
        col1, col2 = st.columns(2)
        with col1:
            common_start_date = st.date_input("시작 날짜", value=datetime.now() - timedelta(days=7))
        with col2:
            common_end_date = st.date_input("종료 날짜", value=datetime.now())
    
    # 조회 기간 정보 표시
    period_info = format_process_period_info(common_date_filter, common_start_date, common_end_date)
    st.info(period_info)
    
    # 실시간 모드 처리
    if realtime_mode:
        st.info("🔴 **실시간 모드 활성화** - 데이터가 자동으로 업데이트됩니다.")
        if common_date_filter == "전체":
            auto_refresh_time = 30  # 30초 간격
            st.info(f"⏰ 자동 새로고침: {auto_refresh_time}초 간격")
    
    st.markdown("---")
    
    # 엔진 인스턴스 가져오기
    lot_engine = st.session_state.lot_tracking_engine
    equipment_engine = st.session_state.equipment_monitoring_engine
    anomaly_engine = st.session_state.anomaly_detection_engine
    
    # 공통 데이터 로드
    try:
        sample_lots = lot_engine.load_lot_data()
        filtered_lots = lot_engine.filter_lots_by_date(sample_lots, common_date_filter, common_start_date, common_end_date)
        
        # 데이터 새로고침 처리
        if refresh_data:
            st.success("🔄 데이터가 새로고침되었습니다!")
            st.rerun() if hasattr(st, 'rerun') else None
    
    except Exception as e:
        st.error(f"❌ 데이터 로드 오류: {str(e)}")
        st.warning("⚠️ 샘플 데이터를 사용합니다.")
        sample_lots = lot_engine.generate_sample_lot_data()
        filtered_lots = lot_engine.filter_lots_by_date(sample_lots, common_date_filter, common_start_date, common_end_date)
    
    tab1, tab2, tab3 = st.tabs(["📊 Lot 추적", "🏭 설비 모니터링", "🚨 이상탐지"])
    
    with tab1:
        lot_tracking_tab(lot_engine, filtered_lots, common_date_filter, common_start_date, common_end_date)
    
    with tab2:
        equipment_monitoring_tab(equipment_engine, filtered_lots, common_date_filter, common_start_date, common_end_date)
    
    with tab3:
        anomaly_detection_tab(anomaly_engine, filtered_lots, common_date_filter, common_start_date, common_end_date)


def lot_tracking_tab(lot_engine, filtered_lots, common_date_filter, common_start_date, common_end_date):
    """Lot 추적 탭"""
    st.markdown("### 📊 Lot 추적 대시보드")
    
    # 현재 조회 조건에 따른 Lot 상태 메트릭
    lot_stats = lot_engine.get_lot_statistics(filtered_lots)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("🔄 활성 Lot", lot_stats["active_count"])
        
    with col2:
        st.metric("✅ 완료 Lot", lot_stats["completed_count"])
        
    with col3:
        st.metric("⏳ 대기 Lot", lot_stats["waiting_count"])
    
    # Lot 상태 설명
    with st.expander("📋 **Lot 상태별 정의 및 증감 기준**", expanded=False):
        st.markdown("### 🔍 **Lot 상태별 정의**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            #### 🔄 **활성 Lot**
            **정의:**
            - 현재 생산 공정이 진행 중인 Lot
            - 원료 투입부터 최종 제품 완료 전까지
            - 설비에서 실제 가공 중인 상태
            
            **포함 단계:**
            - 원료 투입 → 반응 → 정제 → 건조 → 포장 전
            
            **증감 기준:**
            - ↗️ **증가**: 새로운 Lot 생산 시작
            - ↘️ **감소**: Lot 생산 완료 시
            """)
        
        with col2:
            st.markdown("""
            #### ✅ **완료 Lot**
            **정의:**
            - 모든 생산 공정이 완료된 Lot
            - 품질 검사 통과 및 최종 포장 완료
            - 출하 대기 또는 출하 완료 상태
            
            **완료 조건:**
            - 순도 ≥ 95%
            - 수율 ≥ 85%
            - 품질 검사 PASS
            
            **증감 기준:**
            - ↗️ **증가**: 활성 Lot 생산 완료 시
            - ↘️ **감소**: 월말 통계 리셋 시
            """)
        
        with col3:
            st.markdown("""
            #### ⏳ **대기 Lot**
            **정의:**
            - 생산 예정이지만 아직 시작되지 않은 Lot
            - 원료 대기, 설비 대기, 일정 대기 상태
            - 생산 계획에 등록된 미착수 Lot
            
            **대기 원인:**
            - 원료 부족 또는 품질 불량
            - 설비 점검 또는 고장
            - 생산 일정 조정
            
            **증감 기준:**
            - ↗️ **증가**: 새로운 생산 계획 등록
            - ↘️ **감소**: 대기 Lot 생산 시작
            """)
    
    st.markdown("---")
    
    # Lot 검색 및 상태별 필터링
    st.markdown("#### 🔍 Lot 검색 및 필터링")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        search_lot = st.text_input("Lot ID 입력", placeholder="예: LOT-2024-001")
    
    with col2:
        lot_status_filter = st.selectbox(
            "상태별 필터",
            ["전체", "🔄 활성", "✅ 완료", "⏳ 대기"],
            index=0
        )
    
    # 상태별 필터링 적용
    current_filtered_lots = ProcessLotManager.filter_lots_by_status(filtered_lots, lot_status_filter)
    
    # Lot ID로 검색
    if search_lot:
        search_result = lot_engine.search_lot_by_id(filtered_lots, search_lot)
        
        if search_result:
            st.success(f"📋 {search_lot} 정보를 조회했습니다.")
            display_lot_details(search_result)
        else:
            st.error(f"❌ {search_lot}을 찾을 수 없습니다.")
    
    else:
        # 상태별 Lot 목록 표시
        st.markdown(f"#### 📋 {lot_status_filter} Lot 목록")
        
        if current_filtered_lots:
            # Lot 목록을 데이터프레임으로 표시
            df_lots = prepare_lot_display_data(current_filtered_lots)
            
            # 스타일링 적용
            styled_df = ProcessDataFormatter.highlight_lot_status(df_lots)
            
            st.dataframe(
                styled_df,
                use_container_width=True,
                hide_index=True
            )
            
            # 상태별 통계 요약
            st.markdown("#### 📊 상태별 통계")
            
            filtered_stats = lot_engine.get_lot_statistics(current_filtered_lots)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("🔄 활성 Lot", filtered_stats["active_count"])
            
            with col2:
                st.metric("✅ 완료 Lot", filtered_stats["completed_count"])
            
            with col3:
                st.metric("⏳ 대기 Lot", filtered_stats["waiting_count"])
            
            # 날짜별 통계
            if len(current_filtered_lots) > 0:
                st.markdown("#### 📅 날짜별 통계")
                
                date_counts = lot_engine.get_daily_statistics(current_filtered_lots)
                
                if date_counts:
                    # 필터 정보 표시
                    filter_info = f"**📊 표시 조건**: 날짜 필터 '{common_date_filter}'"
                    if lot_status_filter != "전체":
                        filter_info += f", 상태 필터 '{lot_status_filter}'"
                    st.markdown(filter_info)
                    
                    # 날짜별 분포 차트
                    chart_data = []
                    for date, counts in sorted(date_counts.items()):
                        chart_data.append({
                            "날짜": date,
                            "활성": counts["활성"],
                            "완료": counts["완료"],
                            "대기": counts["대기"]
                        })
                    
                    chart_df = pd.DataFrame(chart_data)
                    st.bar_chart(chart_df.set_index("날짜"))
                    
                    # 통계 요약
                    total_dates = len(date_counts)
                    date_range = f"{min(date_counts.keys())} ~ {max(date_counts.keys())}" if total_dates > 1 else min(date_counts.keys())
                    
                    summary_col1, summary_col2 = st.columns(2)
                    with summary_col1:
                        st.metric("📅 작업 일수", total_dates)
                    with summary_col2:
                        st.metric("📊 날짜 범위", date_range)
        
        else:
            st.info(f"📂 {lot_status_filter} 상태의 Lot이 없습니다.")
    
    # ChatBot 인터페이스 추가
    st.markdown("---")
    
    # Lot 추적 전용 챗봇 매니저 사용
    lot_chat_manager = st.session_state.lot_tracking_chat
    
    # Context 데이터 업데이트
    lot_data = {'filtered_lots': filtered_lots}
    lot_chat_manager.update_context_data(lot_data, common_date_filter)
    
    # 탭별 챗봇 인터페이스 생성
    lot_chat_manager.create_chat_interface()


def equipment_monitoring_tab(equipment_engine, filtered_lots, common_date_filter, common_start_date, common_end_date):
    """설비 모니터링 탭"""
    st.markdown("### 🏭 설비 모니터링")
    
    try:
        # 설비 현황 계산
        equipment_status = equipment_engine.calculate_equipment_status(filtered_lots)
        
        # 설비별 상세 통계 계산
        equipment_stats = equipment_engine.calculate_equipment_detailed_stats(
            filtered_lots, common_date_filter, common_start_date, common_end_date
        ) if equipment_status else {}
        
        if equipment_status:
            # 설비 현황 테이블
            df_equipment = pd.DataFrame(equipment_status)
            st.dataframe(df_equipment, use_container_width=True)
            
            # 가동률 차트
            st.markdown("#### 📈 설비별 가동률")
            chart_data = pd.DataFrame({
                "설비": [eq["ID"] for eq in equipment_status],
                "가동률": [eq["가동률"] for eq in equipment_status]
            })
            st.bar_chart(chart_data.set_index("설비"))
            
            # 설비별 상세 통계
            st.markdown("#### 📊 설비별 상세 통계")
            
            for eq_id, stats in equipment_stats.items():
                with st.expander(f"🔧 {eq_id} 상세 정보"):
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("총 Lot 수", stats["total_lots"])
                    with col2:
                        st.metric("평균 순도", f"{stats['avg_purity']:.1f}%")
                    with col3:
                        st.metric("평균 수율", f"{stats['avg_yield']:.1f}%")
                    with col4:
                        st.metric("완료율", f"{stats['completion_rate']:.1f}%")
                    
                    # 설비별 성능 차트
                    if stats['daily_performance']:
                        st.markdown("**📈 일별 성능 추이**")
                        perf_df = pd.DataFrame(stats['daily_performance'])
                        st.line_chart(perf_df.set_index('date'))
        else:
            st.info("📂 설비 현황 데이터가 없습니다.")
    
    except Exception as e:
        st.error(f"❌ 설비 모니터링 오류: {str(e)}")
        st.info("📂 설비 현황 데이터를 불러올 수 없습니다.")
        equipment_status = []
        equipment_stats = {}
    
    # ChatBot 인터페이스 추가
    st.markdown("---")
    
    # 설비 모니터링 전용 챗봇 매니저 사용
    equipment_chat_manager = st.session_state.equipment_monitoring_chat
    
    # Context 데이터 업데이트
    equipment_data = {
        'equipment_status': equipment_status,
        'equipment_stats': equipment_stats
    }
    equipment_chat_manager.update_context_data(equipment_data, common_date_filter)
    
    # 탭별 챗봇 인터페이스 생성
    equipment_chat_manager.create_chat_interface()


def anomaly_detection_tab(anomaly_engine, filtered_lots, common_date_filter, common_start_date, common_end_date):
    """이상탐지 탭"""
    st.markdown("### 🚨 이상탐지 시스템")
    
    # 알림 설정
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### ⚙️ 알림 설정")
        temp_threshold = st.slider("온도 임계값 (°C)", 100, 250, 200)
        pressure_threshold = st.slider("압력 임계값 (bar)", 1.0, 5.0, 3.0)
        purity_threshold = st.slider("순도 최소값 (%)", 70.0, 99.0, 95.0)
        yield_threshold = st.slider("수율 최소값 (%)", 70.0, 95.0, 85.0)
        
        enable_webhook = st.checkbox("웹훅 알림 활성화")
        enable_email = st.checkbox("이메일 알림 활성화")
    
    with col2:
        st.markdown("#### 📊 실시간 이상탐지")
        
        try:
            # 이상탐지 수행
            anomaly_alerts = anomaly_engine.detect_anomalies(
                filtered_lots, temp_threshold, pressure_threshold, 
                purity_threshold, yield_threshold, common_date_filter, 
                common_start_date, common_end_date
            )
            
            if anomaly_alerts:
                st.markdown(f"**🚨 발견된 이상 상황: {len(anomaly_alerts)}건**")
                
                for alert in anomaly_alerts:
                    status_emoji = get_process_status_emoji(alert["상태"])
                    if alert["상태"] == "정상":
                        st.success(f"{status_emoji} **{alert['lot_id']}** ({alert['설비']}) - {alert['내용']}")
                    elif alert["상태"] == "주의":
                        st.warning(f"{status_emoji} **{alert['lot_id']}** ({alert['설비']}) - {alert['내용']}")
                    else:
                        st.error(f"{status_emoji} **{alert['lot_id']}** ({alert['설비']}) - {alert['내용']}")
                    st.markdown("---")
            else:
                st.success("✅ 현재 모든 시스템이 정상 작동 중입니다.")
        
        except Exception as e:
            st.error(f"❌ 이상탐지 오류: {str(e)}")
            anomaly_alerts = []
    
    # 이상탐지 통계 요약
    st.markdown("#### 📈 이상탐지 통계")
    
    try:
        anomaly_stats = anomaly_engine.calculate_anomaly_statistics(
            filtered_lots, temp_threshold, pressure_threshold, 
            purity_threshold, yield_threshold, common_date_filter, 
            common_start_date, common_end_date
        )
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("총 검사 Lot", anomaly_stats["total_lots"])
        with col2:
            st.metric("이상 탐지", anomaly_stats["anomaly_count"], delta=f"{anomaly_stats['anomaly_rate']:.1f}%")
        with col3:
            st.metric("온도 이상", anomaly_stats["temp_anomalies"])
        with col4:
            st.metric("압력 이상", anomaly_stats["pressure_anomalies"])
        
        # 이상탐지 분포 차트
        if anomaly_stats["anomaly_distribution"]:
            st.markdown("#### 📊 이상 유형별 분포")
            
            dist_df = pd.DataFrame(list(anomaly_stats["anomaly_distribution"].items()), 
                                 columns=["이상 유형", "발생 건수"])
            
            st.bar_chart(dist_df.set_index("이상 유형"))
    
    except Exception as e:
        st.error(f"❌ 이상탐지 통계 계산 오류: {str(e)}")
        anomaly_stats = {
            "total_lots": 0,
            "anomaly_count": 0,
            "anomaly_rate": 0.0,
            "temp_anomalies": 0,
            "pressure_anomalies": 0,
            "anomaly_distribution": {}
        }
    
    # ChatBot 인터페이스 추가
    st.markdown("---")
    
    # 이상탐지 전용 챗봇 매니저 사용
    anomaly_chat_manager = st.session_state.anomaly_detection_chat
    
    # Context 데이터 업데이트
    anomaly_data = {
        'anomaly_alerts': anomaly_alerts,
        'anomaly_stats': anomaly_stats
    }
    anomaly_chat_manager.update_context_data(anomaly_data, common_date_filter)
    
    # 탭별 챗봇 인터페이스 생성
    anomaly_chat_manager.create_chat_interface()


def display_lot_details(lot):
    """Lot 상세 정보 표시"""
    lot_details = ProcessLotManager.get_lot_details_dict(lot)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📋 기본 정보**")
        for key, value in lot_details["기본정보"].items():
            st.write(f"**{key}**: {value}")
        
    with col2:
        st.markdown("**📊 품질 지표**")
        for key, value in lot_details["품질지표"].items():
            st.write(f"**{key}**: {value}")
        
        # 추가 정보가 있는 경우 표시
        if "추가정보" in lot_details:
            st.markdown("**🔧 추가 정보**")
            for key, value in lot_details["추가정보"].items():
                st.write(f"**{key}**: {value}")


