"""
DX-AI Manufacturing Copilot - 프로세스 관리 엔진

프로세스 관리 관련 백엔드 비즈니스 로직을 처리하는 엔진 클래스들입니다.
"""

import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass


@dataclass
class LotInfo:
    """Lot 정보 데이터 클래스"""
    lot_id: str
    status: str
    equipment: str
    start_time: str
    work_date: str
    progress: str
    purity: str
    yield_rate: str
    expected_completion: str


@dataclass
class EquipmentStatus:
    """설비 상태 정보 데이터 클래스"""
    id: str
    status: str
    utilization: float
    last_maintenance: str
    total_lots: int


@dataclass
class AnomalyAlert:
    """이상탐지 알림 데이터 클래스"""
    lot_id: str
    equipment: str
    content: str
    status: str
    timestamp: str


class ProcessManagementEngine:
    """프로세스 관리 기본 엔진"""
    
    def __init__(self):
        self.data_dir = os.path.join("data", "generated")
        self.production_dir = os.path.join(self.data_dir, "production")
        
    def get_production_data_files(self) -> List[str]:
        """생산 데이터 파일 목록 반환"""
        if not os.path.exists(self.production_dir):
            return []
        return glob.glob(os.path.join(self.production_dir, "*.csv"))
    
    def load_raw_production_data(self) -> List[Dict]:
        """원시 생산 데이터 로드"""
        production_files = self.get_production_data_files()
        
        if not production_files:
            return []
        
        all_data = []
        
        try:
            for filepath in production_files:
                df = pd.read_csv(filepath)
                all_data.extend(df.to_dict('records'))
            
            return all_data
        except Exception as e:
            print(f"원시 데이터 로드 오류: {str(e)}")
            return []
    
    def filter_data_by_date(self, data: List[Dict], date_filter: str, 
                           start_date: Optional[datetime] = None, 
                           end_date: Optional[datetime] = None) -> List[Dict]:
        """날짜 필터링"""
        if date_filter == "전체":
            return data
        
        today = datetime.now().date()
        filtered_data = []
        
        for row in data:
            work_date_str = row.get('Work_Date', '')
            if not work_date_str:
                continue
                
            try:
                work_date = datetime.strptime(work_date_str, "%Y-%m-%d").date()
            except:
                continue
                
            if date_filter == "오늘":
                if work_date == today:
                    filtered_data.append(row)
            elif date_filter == "어제":
                yesterday = today - timedelta(days=1)
                if work_date == yesterday:
                    filtered_data.append(row)
            elif date_filter == "최근 3일":
                start_date = today - timedelta(days=3)
                if start_date <= work_date <= today:
                    filtered_data.append(row)
            elif date_filter == "최근 1주":
                start_date = today - timedelta(days=7)
                if start_date <= work_date <= today:
                    filtered_data.append(row)
            elif date_filter == "최근 1개월":
                start_date = today - timedelta(days=30)
                if start_date <= work_date <= today:
                    filtered_data.append(row)
            elif date_filter == "사용자 정의":
                if start_date and end_date:
                    if start_date <= work_date <= end_date:
                        filtered_data.append(row)
        
        return filtered_data
    
    def generate_sample_lot_data(self) -> List[Dict]:
        """샘플 Lot 데이터 생성"""
        np.random.seed(42)
        lots = []
        
        # 활성 Lot (24개)
        for i in range(1, 25):
            work_date = datetime.now() - timedelta(days=np.random.randint(0, 5))
            lots.append({
                "Lot_ID": f"LOT-2024-{i:03d}",
                "상태": "활성",
                "설비": f"EQ-{np.random.randint(1, 5):02d}",
                "시작시간": (datetime.now() - timedelta(hours=np.random.randint(1, 48))).strftime("%m-%d %H:%M"),
                "작업일자": work_date.strftime("%Y-%m-%d"),
                "진행률": f"{np.random.randint(10, 95)}%",
                "순도": f"{np.random.uniform(95.0, 98.5):.1f}%",
                "수율": f"{np.random.uniform(85.0, 95.0):.1f}%",
                "예상완료": (datetime.now() + timedelta(hours=np.random.randint(2, 24))).strftime("%m-%d %H:%M")
            })
        
        # 완료 Lot (최근 10개만 표시)
        for i in range(140, 150):
            work_date = datetime.now() - timedelta(days=np.random.randint(1, 7))
            lots.append({
                "Lot_ID": f"LOT-2024-{i:03d}",
                "상태": "완료",
                "설비": f"EQ-{np.random.randint(1, 5):02d}",
                "시작시간": (datetime.now() - timedelta(days=np.random.randint(1, 7))).strftime("%m-%d %H:%M"),
                "작업일자": work_date.strftime("%Y-%m-%d"),
                "진행률": "100%",
                "순도": f"{np.random.uniform(96.0, 99.0):.1f}%",
                "수율": f"{np.random.uniform(88.0, 97.0):.1f}%",
                "예상완료": "완료"
            })
        
        # 대기 Lot (12개)
        for i in range(200, 212):
            work_date = datetime.now() + timedelta(days=np.random.randint(1, 5))
            lots.append({
                "Lot_ID": f"LOT-2024-{i:03d}",
                "상태": "대기",
                "설비": "미배정",
                "시작시간": "미시작",
                "작업일자": work_date.strftime("%Y-%m-%d"),
                "진행률": "0%",
                "순도": "-",
                "수율": "-",
                "예상완료": (datetime.now() + timedelta(days=np.random.randint(1, 5))).strftime("%m-%d %H:%M")
            })
        
        return lots


class LotTrackingEngine(ProcessManagementEngine):
    """Lot 추적 엔진"""
    
    def __init__(self):
        super().__init__()
    
    def load_lot_data(self) -> List[Dict]:
        """Lot 데이터 로드"""
        production_files = self.get_production_data_files()
        
        if not production_files:
            return self.generate_sample_lot_data()
        
        all_lots = []
        
        try:
            for filepath in production_files:
                df = pd.read_csv(filepath)
                
                for _, row in df.iterrows():
                    purity = float(row.get('Purity_%', 0))
                    yield_val = float(row.get('Yield_%', 0))
                    
                    if purity >= 95 and yield_val >= 85:
                        status = "완료"
                        progress = "100%"
                        expected_completion = "완료"
                    elif purity < 90 or yield_val < 80:
                        status = "대기"
                        progress = "0%"
                        expected_completion = "품질 검토 중"
                    else:
                        status = "활성"
                        progress = f"{np.random.randint(30, 95)}%"
                        expected_completion = (datetime.now() + timedelta(hours=np.random.randint(2, 24))).strftime("%m-%d %H:%M")
                    
                    work_date = row.get('Work_Date', datetime.now().strftime("%Y-%m-%d"))
                    work_time = row.get('Work_Time', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    
                    if pd.notna(work_time):
                        try:
                            start_time = datetime.strptime(work_time, "%Y-%m-%d %H:%M:%S").strftime("%m-%d %H:%M")
                        except:
                            start_time = datetime.now().strftime("%m-%d %H:%M")
                    else:
                        start_time = datetime.now().strftime("%m-%d %H:%M")
                    
                    lot_info = {
                        "Lot_ID": row.get('Lot_ID', f"LOT-UNKNOWN-{len(all_lots)+1:03d}"),
                        "상태": status,
                        "설비": row.get('Equipment_ID', "EQ-01"),
                        "시작시간": start_time,
                        "작업일자": work_date,
                        "진행률": progress,
                        "순도": f"{purity:.1f}%",
                        "수율": f"{yield_val:.1f}%",
                        "예상완료": expected_completion
                    }
                    
                    all_lots.append(lot_info)
            
            return all_lots if all_lots else self.generate_sample_lot_data()
            
        except Exception as e:
            print(f"Lot 데이터 로드 오류: {str(e)}")
            return self.generate_sample_lot_data()
    
    def filter_lots_by_date(self, lots: List[Dict], date_filter: str, 
                           custom_start_date: Optional[datetime] = None, 
                           custom_end_date: Optional[datetime] = None) -> List[Dict]:
        """날짜 필터링 함수"""
        if date_filter == "전체":
            return lots
        
        today = datetime.now().date()
        
        if date_filter == "오늘":
            target_date = today
            return [lot for lot in lots if lot["작업일자"] == target_date.strftime("%Y-%m-%d")]
        elif date_filter == "어제":
            target_date = today - timedelta(days=1)
            return [lot for lot in lots if lot["작업일자"] == target_date.strftime("%Y-%m-%d")]
        elif date_filter == "최근 3일":
            start_date = today - timedelta(days=3)
            return [lot for lot in lots if start_date <= datetime.strptime(lot["작업일자"], "%Y-%m-%d").date() <= today]
        elif date_filter == "최근 1주":
            start_date = today - timedelta(days=7)
            return [lot for lot in lots if start_date <= datetime.strptime(lot["작업일자"], "%Y-%m-%d").date() <= today]
        elif date_filter == "최근 1개월":
            start_date = today - timedelta(days=30)
            return [lot for lot in lots if start_date <= datetime.strptime(lot["작업일자"], "%Y-%m-%d").date() <= today]
        elif date_filter == "사용자 정의":
            if custom_start_date and custom_end_date:
                return [lot for lot in lots if custom_start_date <= datetime.strptime(lot["작업일자"], "%Y-%m-%d").date() <= custom_end_date]
            else:
                return lots
        
        return lots
    
    def get_lot_statistics(self, lots: List[Dict]) -> Dict[str, int]:
        """Lot 상태별 통계 계산"""
        stats = {
            "active_count": len([lot for lot in lots if lot["상태"] == "활성"]),
            "completed_count": len([lot for lot in lots if lot["상태"] == "완료"]),
            "waiting_count": len([lot for lot in lots if lot["상태"] == "대기"]),
            "total_count": len(lots)
        }
        return stats
    
    def get_daily_statistics(self, lots: List[Dict]) -> Dict[str, Dict]:
        """날짜별 통계 계산"""
        date_counts = {}
        for lot in lots:
            date = lot["작업일자"]
            if date not in date_counts:
                date_counts[date] = {"활성": 0, "완료": 0, "대기": 0}
            date_counts[date][lot["상태"]] += 1
        
        return date_counts
    
    def search_lot_by_id(self, lots: List[Dict], lot_id: str) -> Optional[Dict]:
        """Lot ID로 검색"""
        return next((lot for lot in lots if lot["Lot_ID"].upper() == lot_id.upper()), None)


class EquipmentMonitoringEngine(ProcessManagementEngine):
    """설비 모니터링 엔진"""
    
    def __init__(self):
        super().__init__()
    
    def calculate_equipment_status(self, lots: List[Dict]) -> List[Dict]:
        """설비별 상태 계산"""
        equipment_data = {}
        
        for lot in lots:
            eq_id = lot["설비"]
            if eq_id not in equipment_data:
                equipment_data[eq_id] = {
                    "total_lots": 0,
                    "active_lots": 0,
                    "completed_lots": 0,
                    "waiting_lots": 0,
                    "last_work_date": None
                }
            
            equipment_data[eq_id]["total_lots"] += 1
            
            if lot["상태"] == "활성":
                equipment_data[eq_id]["active_lots"] += 1
            elif lot["상태"] == "완료":
                equipment_data[eq_id]["completed_lots"] += 1
            elif lot["상태"] == "대기":
                equipment_data[eq_id]["waiting_lots"] += 1
            
            # 최근 작업 날짜 업데이트
            work_date = lot["작업일자"]
            if equipment_data[eq_id]["last_work_date"] is None or work_date > equipment_data[eq_id]["last_work_date"]:
                equipment_data[eq_id]["last_work_date"] = work_date
        
        # 설비 상태 결정
        equipment_status = []
        for eq_id, data in equipment_data.items():
            if data["active_lots"] > 0:
                status = "가동 중"
                utilization = (data["active_lots"] / data["total_lots"]) * 100
            elif data["completed_lots"] > 0 and data["waiting_lots"] == 0:
                status = "대기"
                utilization = 0.0
            else:
                status = "점검 필요"
                utilization = 0.0
            
            equipment_status.append({
                "ID": eq_id,
                "상태": status,
                "가동률": round(utilization, 1),
                "마지막 점검": data["last_work_date"] or "데이터 없음",
                "총 Lot": data["total_lots"]
            })
        
        return sorted(equipment_status, key=lambda x: x["ID"])
    
    def calculate_equipment_detailed_stats(self, lots: List[Dict], date_filter: str = "전체", 
                                         start_date: Optional[datetime] = None, 
                                         end_date: Optional[datetime] = None) -> Dict[str, Dict]:
        """설비별 상세 통계 계산"""
        equipment_stats = {}
        
        # 실제 생산 데이터에서 원시 데이터 로드
        raw_data = self.load_raw_production_data()
        
        # 날짜 필터링 적용
        if date_filter != "전체":
            raw_data = self.filter_data_by_date(raw_data, date_filter, start_date, end_date)
        
        for lot in lots:
            eq_id = lot["설비"]
            if eq_id not in equipment_stats:
                equipment_stats[eq_id] = {
                    "total_lots": 0,
                    "completed_lots": 0,
                    "purity_values": [],
                    "yield_values": [],
                    "daily_performance": []
                }
            
            equipment_stats[eq_id]["total_lots"] += 1
            
            if lot["상태"] == "완료":
                equipment_stats[eq_id]["completed_lots"] += 1
            
            # 순도, 수율 값 추출 (% 제거)
            purity = float(lot["순도"].replace('%', ''))
            yield_val = float(lot["수율"].replace('%', ''))
            
            equipment_stats[eq_id]["purity_values"].append(purity)
            equipment_stats[eq_id]["yield_values"].append(yield_val)
        
        # 일별 성능 데이터 계산
        for eq_id in equipment_stats:
            eq_raw_data = [row for row in raw_data if row.get('Equipment_ID') == eq_id]
            
            daily_perf = {}
            for row in eq_raw_data:
                date = row.get('Work_Date', '')
                if date not in daily_perf:
                    daily_perf[date] = {'purity': [], 'yield': []}
                
                daily_perf[date]['purity'].append(float(row.get('Purity_%', 0)))
                daily_perf[date]['yield'].append(float(row.get('Yield_%', 0)))
            
            # 일별 평균 계산
            daily_performance = []
            for date, values in sorted(daily_perf.items()):
                if values['purity'] and values['yield']:
                    daily_performance.append({
                        'date': date,
                        'purity': sum(values['purity']) / len(values['purity']),
                        'yield': sum(values['yield']) / len(values['yield'])
                    })
            
            equipment_stats[eq_id]["daily_performance"] = daily_performance
        
        # 통계 계산
        final_stats = {}
        for eq_id, stats in equipment_stats.items():
            avg_purity = sum(stats["purity_values"]) / len(stats["purity_values"]) if stats["purity_values"] else 0
            avg_yield = sum(stats["yield_values"]) / len(stats["yield_values"]) if stats["yield_values"] else 0
            completion_rate = (stats["completed_lots"] / stats["total_lots"]) * 100 if stats["total_lots"] > 0 else 0
            
            final_stats[eq_id] = {
                "total_lots": stats["total_lots"],
                "avg_purity": avg_purity,
                "avg_yield": avg_yield,
                "completion_rate": completion_rate,
                "daily_performance": stats["daily_performance"]
            }
        
        return final_stats


class AnomalyDetectionEngine(ProcessManagementEngine):
    """이상탐지 엔진"""
    
    def __init__(self):
        super().__init__()
    
    def detect_anomalies(self, lots: List[Dict], temp_threshold: float, 
                        pressure_threshold: float, purity_threshold: float, 
                        yield_threshold: float, date_filter: str = "전체",
                        start_date: Optional[datetime] = None, 
                        end_date: Optional[datetime] = None) -> List[Dict]:
        """실제 생산 데이터에서 이상탐지 수행"""
        raw_data = self.load_raw_production_data()
        
        # 날짜 필터링 적용
        if date_filter != "전체":
            raw_data = self.filter_data_by_date(raw_data, date_filter, start_date, end_date)
        
        anomaly_alerts = []
        
        for row in raw_data:
            lot_id = row.get('Lot_ID', 'UNKNOWN')
            eq_id = row.get('Equipment_ID', 'UNKNOWN')
            
            alerts = []
            
            # 온도 이상 탐지
            temp = float(row.get('Temperature_C', 0))
            if temp > temp_threshold:
                alerts.append({
                    'lot_id': lot_id,
                    '설비': eq_id,
                    '내용': f'온도 {temp:.1f}°C (임계값: {temp_threshold}°C)',
                    '상태': '경고' if temp > temp_threshold * 1.1 else '주의'
                })
            
            # 압력 이상 탐지
            pressure = float(row.get('Pressure_bar', 0))
            if pressure > pressure_threshold:
                alerts.append({
                    'lot_id': lot_id,
                    '설비': eq_id,
                    '내용': f'압력 {pressure:.1f} bar (임계값: {pressure_threshold} bar)',
                    '상태': '경고' if pressure > pressure_threshold * 1.2 else '주의'
                })
            
            # 순도 이상 탐지
            purity = float(row.get('Purity_%', 0))
            if purity < purity_threshold:
                alerts.append({
                    'lot_id': lot_id,
                    '설비': eq_id,
                    '내용': f'순도 {purity:.1f}% (최소값: {purity_threshold}%)',
                    '상태': '경고' if purity < purity_threshold * 0.9 else '주의'
                })
            
            # 수율 이상 탐지
            yield_val = float(row.get('Yield_%', 0))
            if yield_val < yield_threshold:
                alerts.append({
                    'lot_id': lot_id,
                    '설비': eq_id,
                    '내용': f'수율 {yield_val:.1f}% (최소값: {yield_threshold}%)',
                    '상태': '경고' if yield_val < yield_threshold * 0.9 else '주의'
                })
            
            anomaly_alerts.extend(alerts)
        
        return anomaly_alerts[:10]  # 최대 10개만 반환
    
    def calculate_anomaly_statistics(self, lots: List[Dict], temp_threshold: float, 
                                   pressure_threshold: float, purity_threshold: float, 
                                   yield_threshold: float, date_filter: str = "전체",
                                   start_date: Optional[datetime] = None, 
                                   end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """이상탐지 통계 계산"""
        raw_data = self.load_raw_production_data()
        
        # 날짜 필터링 적용
        if date_filter != "전체":
            raw_data = self.filter_data_by_date(raw_data, date_filter, start_date, end_date)
        
        total_lots = len(raw_data)
        anomaly_count = 0
        temp_anomalies = 0
        pressure_anomalies = 0
        purity_anomalies = 0
        yield_anomalies = 0
        
        anomaly_distribution = {}
        
        for row in raw_data:
            has_anomaly = False
            
            # 온도 이상
            temp = float(row.get('Temperature_C', 0))
            if temp > temp_threshold:
                temp_anomalies += 1
                has_anomaly = True
                anomaly_distribution["온도 이상"] = anomaly_distribution.get("온도 이상", 0) + 1
            
            # 압력 이상
            pressure = float(row.get('Pressure_bar', 0))
            if pressure > pressure_threshold:
                pressure_anomalies += 1
                has_anomaly = True
                anomaly_distribution["압력 이상"] = anomaly_distribution.get("압력 이상", 0) + 1
            
            # 순도 이상
            purity = float(row.get('Purity_%', 0))
            if purity < purity_threshold:
                purity_anomalies += 1
                has_anomaly = True
                anomaly_distribution["순도 이상"] = anomaly_distribution.get("순도 이상", 0) + 1
            
            # 수율 이상
            yield_val = float(row.get('Yield_%', 0))
            if yield_val < yield_threshold:
                yield_anomalies += 1
                has_anomaly = True
                anomaly_distribution["수율 이상"] = anomaly_distribution.get("수율 이상", 0) + 1
            
            if has_anomaly:
                anomaly_count += 1
        
        anomaly_rate = (anomaly_count / total_lots) * 100 if total_lots > 0 else 0
        
        return {
            "total_lots": total_lots,
            "anomaly_count": anomaly_count,
            "anomaly_rate": anomaly_rate,
            "temp_anomalies": temp_anomalies,
            "pressure_anomalies": pressure_anomalies,
            "purity_anomalies": purity_anomalies,
            "yield_anomalies": yield_anomalies,
            "anomaly_distribution": anomaly_distribution
        } 