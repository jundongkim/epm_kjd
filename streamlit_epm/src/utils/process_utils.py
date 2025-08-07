"""
DX-AI Manufacturing Copilot - 프로세스 관리 유틸리티

프로세스 관리 관련 공통 유틸리티 함수들을 제공합니다.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any


class ProcessDateFilter:
    """프로세스 관리 날짜 필터링 유틸리티"""
    
    @staticmethod
    def display_period_info(date_filter: str, start_date: Optional[datetime] = None, 
                          end_date: Optional[datetime] = None) -> str:
        """조회 기간 정보 표시 텍스트 생성"""
        today = datetime.now().date()
        
        if date_filter == "오늘":
            return f"📅 **조회 기간**: {today.strftime('%Y-%m-%d')} (오늘)"
        elif date_filter == "어제":
            yesterday = today - timedelta(days=1)
            return f"📅 **조회 기간**: {yesterday.strftime('%Y-%m-%d')} (어제)"
        elif date_filter == "최근 3일":
            start_date = today - timedelta(days=3)
            return f"📅 **조회 기간**: {start_date.strftime('%Y-%m-%d')} ~ {today.strftime('%Y-%m-%d')} (최근 3일)"
        elif date_filter == "최근 1주":
            start_date = today - timedelta(days=7)
            return f"📅 **조회 기간**: {start_date.strftime('%Y-%m-%d')} ~ {today.strftime('%Y-%m-%d')} (최근 1주)"
        elif date_filter == "최근 1개월":
            start_date = today - timedelta(days=30)
            return f"📅 **조회 기간**: {start_date.strftime('%Y-%m-%d')} ~ {today.strftime('%Y-%m-%d')} (최근 1개월)"
        elif date_filter == "전체":
            return "📅 **조회 기간**: 전체 데이터"
        elif date_filter == "사용자 정의":
            if start_date and end_date:
                return f"📅 **조회 기간**: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')} (사용자 정의)"
            else:
                return "📅 **조회 기간**: 사용자 정의 (날짜 선택 필요)"
        else:
            return "📅 **조회 기간**: 알 수 없음"
    
    @staticmethod
    def get_date_range_for_filter(date_filter: str, 
                                 custom_start_date: Optional[datetime] = None,
                                 custom_end_date: Optional[datetime] = None) -> Tuple[Optional[datetime], Optional[datetime]]:
        """날짜 필터에 따른 날짜 범위 반환"""
        today = datetime.now().date()
        
        if date_filter == "오늘":
            return today, today
        elif date_filter == "어제":
            yesterday = today - timedelta(days=1)
            return yesterday, yesterday
        elif date_filter == "최근 3일":
            start_date = today - timedelta(days=3)
            return start_date, today
        elif date_filter == "최근 1주":
            start_date = today - timedelta(days=7)
            return start_date, today
        elif date_filter == "최근 1개월":
            start_date = today - timedelta(days=30)
            return start_date, today
        elif date_filter == "사용자 정의":
            return custom_start_date, custom_end_date
        else:  # "전체"
            return None, None


class ProcessDataFormatter:
    """프로세스 관리 데이터 포맷팅 유틸리티"""
    
    @staticmethod
    def get_status_emoji(status: str) -> str:
        """상태별 이모지 반환"""
        emoji_map = {
            "활성": "🔄",
            "완료": "✅", 
            "대기": "⏳",
            "가동 중": "🟢",
            "점검 필요": "🔴",
            "정상": "✅",
            "주의": "⚠️",
            "경고": "🚨"
        }
        return emoji_map.get(status, "❓")
    
    @staticmethod
    def format_percentage(value: float, decimal_places: int = 1) -> str:
        """백분율 포맷팅"""
        return f"{value:.{decimal_places}f}%"
    
    @staticmethod
    def format_metric_value(value: Any, unit: str = "") -> str:
        """메트릭 값 포맷팅"""
        if isinstance(value, (int, float)):
            if unit:
                return f"{value:.1f}{unit}"
            else:
                return f"{value:.1f}"
        else:
            return str(value)
    
    @staticmethod
    def highlight_lot_status(dataframe: pd.DataFrame) -> pd.DataFrame:
        """Lot 상태별 색상 구분을 위한 스타일링"""
        def apply_color(row):
            if row["상태"] == "활성":
                return ['background-color: #e3f2fd'] * len(row)
            elif row["상태"] == "완료":
                return ['background-color: #e8f5e8'] * len(row)
            elif row["상태"] == "대기":
                return ['background-color: #fff3e0'] * len(row)
            return [''] * len(row)
        
        return dataframe.style.apply(apply_color, axis=1)


class ProcessLotManager:
    """Lot 관리 유틸리티"""
    
    @staticmethod
    def filter_lots_by_status(lots: List[Dict], status_filter: str) -> List[Dict]:
        """상태별 Lot 필터링"""
        if status_filter == "전체":
            return lots
        
        status_map = {
            "🔄 활성": "활성",
            "✅ 완료": "완료", 
            "⏳ 대기": "대기"
        }
        
        target_status = status_map.get(status_filter, status_filter)
        return [lot for lot in lots if lot["상태"] == target_status]
    
    @staticmethod
    def get_lot_details_dict(lot: Dict) -> Dict[str, Any]:
        """Lot 상세 정보 딕셔너리 생성"""
        details = {
            "기본정보": {
                "Lot ID": lot['Lot_ID'],
                "상태": f"{ProcessDataFormatter.get_status_emoji(lot['상태'])} {lot['상태']}",
                "설비": lot['설비'],
                "시작시간": lot['시작시간'],
                "작업일자": lot['작업일자'],
                "진행률": lot['진행률']
            },
            "품질지표": {
                "순도": lot['순도'],
                "수율": lot['수율'],
                "예상완료": lot['예상완료']
            }
        }
        
        # 상태별 추가 정보
        if lot['상태'] == '활성':
            details["추가정보"] = {
                "온도": "175°C",
                "압력": "2.1 bar"
            }
        elif lot['상태'] == '완료':
            details["추가정보"] = {
                "완료시간": "2024-01-15 18:30",
                "품질등급": "A+"
            }
        elif lot['상태'] == '대기':
            details["추가정보"] = {
                "대기사유": "원료 대기",
                "우선순위": "높음"
            }
        
        return details
    
    @staticmethod
    def prepare_lot_dataframe(lots: List[Dict], column_order: Optional[List[str]] = None) -> pd.DataFrame:
        """Lot 데이터를 DataFrame으로 변환"""
        if not lots:
            return pd.DataFrame()
        
        df = pd.DataFrame(lots)
        
        if column_order:
            # 존재하는 컬럼만 선택
            available_columns = [col for col in column_order if col in df.columns]
            df = df[available_columns]
        
        return df


class ProcessAnomalyAnalyzer:
    """이상탐지 분석 유틸리티"""
    
    @staticmethod
    def categorize_anomaly_severity(anomaly_data: Dict) -> str:
        """이상 상황 심각도 분류"""
        if anomaly_data['상태'] == '경고':
            return "높음"
        elif anomaly_data['상태'] == '주의':
            return "보통"
        else:
            return "낮음"
    
    @staticmethod
    def get_anomaly_recommendations(anomaly_type: str, value: float, threshold: float) -> List[str]:
        """이상 상황별 권장사항 생성"""
        recommendations = []
        
        if "온도" in anomaly_type:
            recommendations.extend([
                "냉각 시스템 점검 필요",
                "온도 센서 교정 확인",
                "열 교환기 성능 점검"
            ])
        elif "압력" in anomaly_type:
            recommendations.extend([
                "압력 밸브 점검 필요",
                "압력 릴리프 시스템 확인",
                "배관 누설 점검"
            ])
        elif "순도" in anomaly_type:
            recommendations.extend([
                "정제 공정 점검 필요",
                "원료 품질 확인",
                "불순물 제거 시스템 점검"
            ])
        elif "수율" in anomaly_type:
            recommendations.extend([
                "반응 조건 최적화 필요",
                "촉매 활성도 확인",
                "공정 파라미터 조정"
            ])
        
        return recommendations
    
    @staticmethod
    def calculate_anomaly_trend(anomaly_history: List[Dict]) -> Dict[str, Any]:
        """이상 상황 트렌드 분석"""
        if not anomaly_history:
            return {"trend": "안정", "change_rate": 0.0}
        
        # 최근 7일간 데이터 분석
        recent_data = anomaly_history[-7:]
        
        if len(recent_data) < 2:
            return {"trend": "데이터 부족", "change_rate": 0.0}
        
        # 간단한 선형 트렌드 계산
        x = np.arange(len(recent_data))
        y = [data.get('count', 0) for data in recent_data]
        
        if len(y) > 1:
            slope = np.polyfit(x, y, 1)[0]
            
            if slope > 0.1:
                trend = "증가"
            elif slope < -0.1:
                trend = "감소"
            else:
                trend = "안정"
            
            return {"trend": trend, "change_rate": abs(slope)}
        
        return {"trend": "안정", "change_rate": 0.0}


class ProcessMetricsCalculator:
    """프로세스 메트릭 계산 유틸리티"""
    
    @staticmethod
    def calculate_overall_efficiency(lots: List[Dict]) -> Dict[str, float]:
        """전체 효율성 계산"""
        if not lots:
            return {"efficiency": 0.0, "utilization": 0.0, "quality_score": 0.0}
        
        total_lots = len(lots)
        completed_lots = len([lot for lot in lots if lot["상태"] == "완료"])
        
        # 효율성 = 완료율
        efficiency = (completed_lots / total_lots) * 100 if total_lots > 0 else 0.0
        
        # 가동률 = 활성 + 완료 / 전체
        active_completed = len([lot for lot in lots if lot["상태"] in ["활성", "완료"]])
        utilization = (active_completed / total_lots) * 100 if total_lots > 0 else 0.0
        
        # 품질 점수 = 평균 순도 + 평균 수율 / 2
        purity_values = []
        yield_values = []
        
        for lot in lots:
            if lot["순도"] != "-":
                purity_values.append(float(lot["순도"].replace('%', '')))
            if lot["수율"] != "-":
                yield_values.append(float(lot["수율"].replace('%', '')))
        
        avg_purity = sum(purity_values) / len(purity_values) if purity_values else 0.0
        avg_yield = sum(yield_values) / len(yield_values) if yield_values else 0.0
        quality_score = (avg_purity + avg_yield) / 2
        
        return {
            "efficiency": efficiency,
            "utilization": utilization,
            "quality_score": quality_score
        }
    
    @staticmethod
    def calculate_equipment_performance(equipment_data: List[Dict]) -> Dict[str, Any]:
        """설비 성능 계산"""
        if not equipment_data:
            return {"avg_utilization": 0.0, "best_performer": None, "worst_performer": None}
        
        utilizations = [eq["가동률"] for eq in equipment_data]
        avg_utilization = sum(utilizations) / len(utilizations)
        
        best_performer = max(equipment_data, key=lambda x: x["가동률"])
        worst_performer = min(equipment_data, key=lambda x: x["가동률"])
        
        return {
            "avg_utilization": avg_utilization,
            "best_performer": best_performer,
            "worst_performer": worst_performer
        }
    
    @staticmethod
    def calculate_daily_throughput(lots: List[Dict], target_date: str) -> Dict[str, int]:
        """일일 처리량 계산"""
        daily_lots = [lot for lot in lots if lot["작업일자"] == target_date]
        
        return {
            "total": len(daily_lots),
            "completed": len([lot for lot in daily_lots if lot["상태"] == "완료"]),
            "active": len([lot for lot in daily_lots if lot["상태"] == "활성"]),
            "waiting": len([lot for lot in daily_lots if lot["상태"] == "대기"])
        }


# 편의 함수들
def format_process_period_info(date_filter: str, start_date: Optional[datetime] = None, 
                             end_date: Optional[datetime] = None) -> str:
    """조회 기간 정보 포맷팅 (편의 함수)"""
    return ProcessDateFilter.display_period_info(date_filter, start_date, end_date)


def get_process_status_emoji(status: str) -> str:
    """상태 이모지 반환 (편의 함수)"""
    return ProcessDataFormatter.get_status_emoji(status)


def calculate_process_metrics(lots: List[Dict]) -> Dict[str, float]:
    """프로세스 메트릭 계산 (편의 함수)"""
    return ProcessMetricsCalculator.calculate_overall_efficiency(lots)


def prepare_lot_display_data(lots: List[Dict]) -> pd.DataFrame:
    """Lot 표시 데이터 준비 (편의 함수)"""
    column_order = ["Lot_ID", "상태", "설비", "시작시간", "작업일자", "진행률", "순도", "수율", "예상완료"]
    return ProcessLotManager.prepare_lot_dataframe(lots, column_order)


def get_anomaly_recommendations(anomaly_type: str, value: float, threshold: float) -> List[str]:
    """이상 상황 권장사항 생성 (편의 함수)"""
    return ProcessAnomalyAnalyzer.get_anomaly_recommendations(anomaly_type, value, threshold) 