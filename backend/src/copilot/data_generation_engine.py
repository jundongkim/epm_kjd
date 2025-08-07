"""
DX-AI Manufacturing Copilot - 데이터 생성 엔진

백엔드 비즈니스 로직을 담당하는 데이터 생성 엔진 클래스들
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
from itertools import product
from typing import Dict, Any, List, Tuple, Optional, Union
import scipy.stats as stats


class DataGenerationEngine:
    """데이터 생성 엔진 기본 클래스"""
    
    def __init__(self):
        self.data_dir = "data/generated"
        self.ensure_directories()
    
    def ensure_directories(self):
        """필요한 디렉터리 생성"""
        directories = [
            os.path.join(self.data_dir, "production"),
            os.path.join(self.data_dir, "experimental"),
            os.path.join(self.data_dir, "cost_production"),
            os.path.join(self.data_dir, "sensor")
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def generate_timestamp_filename(self, data_type: str, count: int, extra_info: str = "") -> str:
        """타임스탬프 기반 파일명 생성"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if extra_info:
            return f"manufacturing_copilot_{data_type}_{extra_info}_{count}records_{timestamp}.csv"
        else:
            return f"manufacturing_copilot_{data_type}_{count}records_{timestamp}.csv"
    
    def safe_type_conversion(self, value: Any, target_type: type, default_value: Any = None) -> Any:
        """안전한 타입 변환 메서드"""
        try:
            if value is None or (isinstance(value, str) and value.strip() == ""):
                return default_value
                
            if target_type == float:
                if isinstance(value, (int, float)):
                    return float(value)
                elif isinstance(value, str):
                    # 문자열에서 숫자 부분만 추출
                    import re
                    numeric_str = re.sub(r'[^\d.-]', '', value.strip())
                    if numeric_str:
                        return float(numeric_str)
                    else:
                        return default_value
                return default_value
            elif target_type == int:
                if isinstance(value, (int, float)):
                    return int(value)
                elif isinstance(value, str):
                    import re
                    numeric_str = re.sub(r'[^\d-]', '', value.strip())
                    if numeric_str:
                        return int(float(numeric_str))
                    else:
                        return default_value
                return default_value
            elif target_type == str:
                return str(value)
            else:
                return target_type(value)
        except (ValueError, TypeError) as e:
            print(f"WARNING - Type conversion failed for value '{value}' to {target_type.__name__}: {e}")
            return default_value
    
    def validate_numeric_range(self, value: Union[float, int], min_val: float, max_val: float, default_val: float) -> float:
        """숫자 범위 검증 및 보정"""
        try:
            numeric_val = float(value)
            if np.isnan(numeric_val) or np.isinf(numeric_val):
                return default_val
            return max(min_val, min(max_val, numeric_val))
        except (ValueError, TypeError):
            return default_val
    
    def save_data(self, data: pd.DataFrame, filepath: str) -> bool:
        """데이터 저장"""
        try:
            # 저장 전 데이터 타입 확인 및 정리
            print(f"DEBUG - Saving data with dtypes: {data.dtypes.to_dict()}")
            print(f"DEBUG - Data shape: {data.shape}")
            
            # 데이터 정리
            data_to_save = data.copy()
            
            # NaN 값 및 무한대 값 처리
            for col in data_to_save.columns:
                if data_to_save[col].dtype in ['float64', 'float32']:
                    # 숫자형 컬럼의 NaN, inf 값 처리
                    data_to_save[col] = data_to_save[col].replace([np.inf, -np.inf], np.nan)
                    data_to_save[col] = data_to_save[col].fillna(data_to_save[col].mean())
                elif data_to_save[col].dtype == 'object':
                    # 문자열 컬럼의 NaN 값 처리
                    data_to_save[col] = data_to_save[col].fillna('')
            
            data_to_save.to_csv(filepath, index=False, encoding='utf-8-sig')
            print(f"DEBUG - Data saved successfully to: {filepath}")
            return True
        except Exception as e:
            print(f"데이터 저장 오류: {str(e)}")
            print(f"ERROR - Save error details: {type(e).__name__}: {str(e)}")
            return False


class ProductionDataGenerator(DataGenerationEngine):
    """생산 데이터 생성기"""
    
    def __init__(self):
        super().__init__()
    
    def generate_production_data(self, 
                               lot_count: int,
                               equipment_count: int,
                               work_date_start: datetime,
                               work_date_end: datetime,
                               shift_config: Dict[str, Any],
                               purity_range: Tuple[float, float],
                               yield_range: Tuple[float, float],
                               add_noise: bool = True,
                               noise_level: float = 1.0,
                               add_anomalies: bool = False,
                               anomaly_ratio: int = 3) -> pd.DataFrame:
        """생산 데이터 생성"""
        
        # 타임스탬프 기반 시드 생성
        seed = int(datetime.now().timestamp()) % 1000
        np.random.seed(seed)
        
        # 작업 일자 및 시간 생성
        work_dates, work_times = self._generate_work_schedule(
            lot_count, work_date_start, work_date_end, shift_config
        )
        
        # 기본 데이터 생성
        data = {
            "Lot_ID": [f"LOT-2024-{i:03d}" for i in range(1, lot_count + 1)],
            "Equipment_ID": [f"EQ-{np.random.randint(1, equipment_count + 1):02d}" for _ in range(lot_count)],
            "Work_Date": work_dates,
            "Work_Time": work_times,
            "Purity_%": np.random.uniform(purity_range[0], purity_range[1], lot_count),
            "Yield_%": np.random.uniform(yield_range[0], yield_range[1], lot_count),
            "Temperature_C": np.random.uniform(150, 200, lot_count),
            "Pressure_bar": np.random.uniform(1.5, 3.0, lot_count),
            "Data_Type": ["Production"] * lot_count,
            "Generated_At": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")] * lot_count
        }
        
        # 노이즈 추가
        if add_noise:
            data["Purity_%"] += np.random.normal(0, noise_level * 0.1, lot_count)
            data["Yield_%"] += np.random.normal(0, noise_level * 0.1, lot_count)
        
        # 이상치 추가
        if add_anomalies:
            self._add_anomalies(data, lot_count, anomaly_ratio)
        
        return pd.DataFrame(data)
    
    def _generate_work_schedule(self, 
                              lot_count: int,
                              work_date_start: datetime,
                              work_date_end: datetime,
                              shift_config: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """작업 일정 생성"""
        work_dates = []
        work_times = []
        
        for i in range(lot_count):
            # 작업 일자 생성
            days_diff = (work_date_end - work_date_start).days
            if days_diff == 0:
                work_date = work_date_start
            else:
                random_days = np.random.randint(0, days_diff + 1)
                work_date = work_date_start + timedelta(days=random_days)
            
            # 작업 시간 생성
            work_hour, work_minute = self._generate_work_time(shift_config)
            work_datetime = datetime.combine(work_date, datetime.min.time()) + timedelta(hours=work_hour, minutes=work_minute)
            
            work_dates.append(work_date.strftime("%Y-%m-%d"))
            work_times.append(work_datetime.strftime("%Y-%m-%d %H:%M:%S"))
        
        return work_dates, work_times
    
    def _generate_work_time(self, shift_config: Dict[str, Any]) -> Tuple[int, int]:
        """작업 시간 생성"""
        shift_type = shift_config.get("shift_type", "주간(08:00-16:00)")
        
        if shift_type == "주간(08:00-16:00)":
            work_hour = np.random.randint(8, 16)
        elif shift_type == "야간(22:00-06:00)":
            work_hour = np.random.choice([22, 23, 0, 1, 2, 3, 4, 5])
        elif shift_type == "전체(24시간)":
            work_hour = np.random.randint(0, 24)
        else:  # 사용자 정의
            start_hour = shift_config.get("start_hour", 8)
            end_hour = shift_config.get("end_hour", 16)
            if start_hour <= end_hour:
                work_hour = np.random.randint(start_hour, end_hour + 1)
            else:
                work_hour = np.random.choice(list(range(start_hour, 24)) + list(range(0, end_hour + 1)))
        
        work_minute = np.random.randint(0, 60)
        return work_hour, work_minute
    
    def _add_anomalies(self, data: Dict[str, Any], lot_count: int, anomaly_ratio: int):
        """이상치 추가"""
        n_anomalies = int(lot_count * anomaly_ratio / 100)
        anomaly_indices = np.random.choice(lot_count, n_anomalies, replace=False)
        
        for idx in anomaly_indices:
            data["Purity_%"][idx] = np.random.uniform(85, 92)
            data["Yield_%"][idx] = np.random.uniform(70, 80)
    
    def save_production_data(self, data: pd.DataFrame, lot_count: int) -> str:
        """생산 데이터 저장"""
        filename = self.generate_timestamp_filename("production_data", lot_count, f"{lot_count}lots")
        filepath = os.path.join(self.data_dir, "production", filename)
        
        if self.save_data(data, filepath):
            return filepath
        else:
            raise Exception("생산 데이터 저장 실패")


class SensorDataGenerator(DataGenerationEngine):
    """센서 데이터 생성기"""
    
    def __init__(self):
        super().__init__()
    
    def _generate_safe_timestamps(self, 
                                 lot_count: int,
                                 work_date_start: datetime,
                                 collection_interval: str = "10초") -> List[str]:
        """안전한 타임스탬프 생성 - 연결 문제 방지"""
        timestamps = []
        
        # 수집 간격을 초 단위로 변환
        interval_seconds = self._parse_interval_to_seconds(collection_interval)
        
        # 시작 시간 설정
        current_time = datetime.combine(work_date_start.date(), datetime.min.time()) + timedelta(hours=8)
        
        print(f"DEBUG - Safe timestamp generation: {lot_count} records, interval: {interval_seconds}s")
        print(f"DEBUG - Starting from: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 대용량 데이터 처리 알림
        if lot_count > 20000:
            print(f"DEBUG - Generating large dataset ({lot_count} records), this may take a moment...")
        
        # 개별 타임스탬프 생성
        for i in range(lot_count):
            timestamp_str = current_time.strftime("%Y-%m-%d %H:%M:%S")
            timestamps.append(timestamp_str)
            current_time += timedelta(seconds=interval_seconds)
            
            # 디버깅: 처음 3개와 10000개 단위로만 출력 (대용량 데이터 고려)
            if i < 3 or (i > 0 and i % 10000 == 0):
                print(f"DEBUG - Generated timestamp {i}: '{timestamp_str}'")
        
        print(f"DEBUG - Total timestamps generated: {len(timestamps)}")
        print(f"DEBUG - Last timestamp: '{timestamps[-1] if timestamps else 'None'}'")
        
        # 각 타임스탬프가 개별 문자열인지 검증
        for i, ts in enumerate(timestamps[:3]):
            if len(ts) > 25:  # 정상적인 타임스탬프는 19자리 + 여유분
                print(f"ERROR - Timestamp {i} appears to be concatenated: '{ts[:50]}...'")
                raise Exception(f"타임스탬프 {i}가 연결된 상태로 생성됨")
        
        return timestamps

    def generate_sensor_data_by_interval(self, 
                                       lot_count: int,
                                       selected_sensors: List[str],
                                       work_date_start: datetime,
                                       work_date_end: datetime,
                                       shift_config: Dict[str, Any],
                                       sensor_ranges: Dict[str, Tuple[float, float]],
                                       collection_interval: str = "10초",
                                       add_noise: bool = True,
                                       noise_level: float = 1.0,
                                       add_anomalies: bool = False,
                                       anomaly_ratio: int = 3,
                                       add_missing_data: bool = False,
                                       missing_data_ratio: int = 5,
                                       data_pattern: str = "정상",
                                       variation_intensity: int = 3) -> pd.DataFrame:
        """센서 데이터 생성 - 안전한 타임스탬프 처리"""
        
        # 입력 매개변수 타입 검증 및 변환 (먼저 처리)
        lot_count = self.safe_type_conversion(lot_count, int, 15000)
        noise_level = self.safe_type_conversion(noise_level, float, 1.0)
        anomaly_ratio = self.safe_type_conversion(anomaly_ratio, int, 3)
        variation_intensity = self.safe_type_conversion(variation_intensity, int, 3)
        data_pattern = str(data_pattern) if data_pattern else "정상"
        
        print(f"DEBUG - PARAMETER CHECK: pattern='{data_pattern}', variation_intensity={variation_intensity} (type: {type(variation_intensity)})")
        
        # 변동폭 강도가 제대로 반영되는지 확인을 위한 강력한 시드
        base_seed = int(datetime.now().timestamp() * 1000000) % 1000000
        intensity_seed = variation_intensity * 77777  # 강도별 확실한 차이
        combined_seed = (base_seed + intensity_seed) % 2147483647
        np.random.seed(combined_seed)
        print(f"DEBUG - SEED INFO: base={base_seed}, intensity_multiplier={intensity_seed}, final_seed={combined_seed}")
        
        # 안전한 타임스탬프 생성
        try:
            timestamp_list = self._generate_safe_timestamps(
                lot_count, work_date_start, collection_interval
            )
            print(f"DEBUG - Safe timestamps generated successfully: {len(timestamp_list)} items")
        except Exception as ts_error:
            print(f"ERROR - Failed to generate safe timestamps: {ts_error}")
            # 기본 타임스탬프 생성
            timestamp_list = []
            start_time = datetime.combine(work_date_start, datetime.min.time()) + timedelta(hours=8)
            for i in range(lot_count):
                ts = (start_time + timedelta(seconds=i*10)).strftime("%Y-%m-%d %H:%M:%S") 
                timestamp_list.append(ts)
        
        # 센서 범위 검증 및 정리
        validated_sensor_ranges = {}
        for sensor, range_tuple in sensor_ranges.items():
            try:
                if isinstance(range_tuple, (list, tuple)) and len(range_tuple) >= 2:
                    min_val = self.safe_type_conversion(range_tuple[0], float, 0.0)
                    max_val = self.safe_type_conversion(range_tuple[1], float, 100.0)
                    # 범위 유효성 검증
                    if min_val >= max_val:
                        max_val = min_val + 10.0
                    validated_sensor_ranges[sensor] = (min_val, max_val)
                else:
                    # 기본 범위 사용
                    validated_sensor_ranges[sensor] = self._get_default_sensor_range(sensor)
            except Exception as e:
                print(f"WARNING - Invalid range for sensor {sensor}: {e}")
                validated_sensor_ranges[sensor] = self._get_default_sensor_range(sensor)
        
        # 기본 데이터 구조 생성 - timestamp 먼저 설정
        data = {
            "timestamp": timestamp_list.copy()  # 복사본 생성
        }
        
        print(f"DEBUG - Data initialized with {len(data['timestamp'])} timestamps")
        
        # 선택된 센서별 데이터 생성
        if not selected_sensors:
            selected_sensors = ['outlet_humidity', 'inlet_humidity', 'drying_temperature']
            
        for sensor_type in selected_sensors:
            print(f"DEBUG - Processing sensor: {sensor_type}")
            
            # 센서 범위 결정 - 타입 안전성 보장
            if sensor_type in validated_sensor_ranges:
                sensor_range = validated_sensor_ranges[sensor_type]
            else:
                sensor_range = self._get_default_sensor_range(sensor_type)
            
            try:
                # 센서별 고유 시드 생성 (단순화)
                sensor_offset = sum(ord(c) for c in sensor_type) % 1000
                combined_sensor_seed = (combined_seed + sensor_offset) % 1000000
                
                # 패턴과 변동폭을 고려한 센서 값 생성
                sensor_values = self._generate_pattern_based_values(
                    sensor_range, lot_count, data_pattern, variation_intensity, sensor_type, combined_sensor_seed
                )
                
                # 노이즈 추가 (변동폭 강도에 직접 연결)
                if add_noise:
                    # 노이즈용 별도 시드
                    noise_seed = (combined_sensor_seed + 99999) % 2147483647
                    np.random.seed(noise_seed)
                    
                    noise_factor = self._get_noise_factor(sensor_type)
                    # 변동폭 강도에 직접 비례하는 노이즈 (단순하고 확실한 방식)
                    intensity_multiplier = 0.2 + (variation_intensity / 10.0) * 2.5  # 0.2~2.7배
                    
                    adjusted_noise_level = noise_level * intensity_multiplier
                    noise = np.random.normal(0, adjusted_noise_level * noise_factor, lot_count)
                    sensor_values += noise
                    print(f"DEBUG - NOISE APPLIED: sensor={sensor_type}, intensity={variation_intensity}, multiplier={intensity_multiplier:.2f}, final_std={adjusted_noise_level * noise_factor:.4f}")
                
                # 값 검증 및 정리
                column_name = self._get_sensor_column_name(sensor_type)
                sensor_values_list = []
                
                for val in sensor_values:
                    # 안전한 float 변환 및 범위 검증
                    clean_val = self.validate_numeric_range(
                        val, sensor_range[0] * 0.8, sensor_range[1] * 1.2, 
                        (sensor_range[0] + sensor_range[1]) / 2
                    )
                    sensor_values_list.append(clean_val)
                
                data[column_name] = sensor_values_list
                # 대용량 데이터 고려하여 센서별 처리 로그 간소화
                if lot_count <= 10000:
                    print(f"DEBUG - Added sensor {sensor_type} -> {column_name}: {len(sensor_values_list)} values")
                else:
                    print(f"DEBUG - Added sensor {sensor_type} -> {column_name} (large dataset)")
            
            except Exception as sensor_error:
                print(f"ERROR - Failed to generate data for sensor {sensor_type}: {sensor_error}")
                # 기본값으로 대체
                default_range = self._get_default_sensor_range(sensor_type)
                default_value = (default_range[0] + default_range[1]) / 2
                column_name = self._get_sensor_column_name(sensor_type)
                data[column_name] = [default_value] * lot_count
        
        # 이상치 추가
        if add_anomalies:
            try:
                self._add_sensor_anomalies(data, lot_count, anomaly_ratio, selected_sensors)
            except Exception as anomaly_error:
                print(f"WARNING - Failed to add anomalies: {anomaly_error}")
        
        # 결측치 추가
        if add_missing_data:
            try:
                self._add_missing_data(data, lot_count, missing_data_ratio, selected_sensors)
            except Exception as missing_error:
                print(f"WARNING - Failed to add missing data: {missing_error}")
        
        # 최종 데이터 검증
        print(f"DEBUG - Final data validation:")
        print(f"DEBUG - Data keys: {list(data.keys())}")
        
        # 타임스탬프 검증
        if 'timestamp' in data:
            ts_list = data['timestamp']
            print(f"DEBUG - Timestamp list type: {type(ts_list)}, length: {len(ts_list)}")
            if isinstance(ts_list, list) and len(ts_list) > 0:
                first_ts = ts_list[0]
                print(f"DEBUG - First timestamp: '{first_ts}' (length: {len(str(first_ts))})")
                if len(str(first_ts)) > 25:
                    raise Exception("타임스탬프가 여전히 연결된 상태입니다")
        
        # 모든 데이터 길이 일치 확인
        expected_length = lot_count
        for key, value in data.items():
            if len(value) != expected_length:
                print(f"WARNING - Length mismatch for {key}: expected {expected_length}, got {len(value)}")
                if len(value) < expected_length:
                    if key == 'timestamp':
                        # 타임스탬프 부족시 마지막 시간 기반으로 추가
                        last_time = datetime.strptime(value[-1], "%Y-%m-%d %H:%M:%S") if value else datetime.now()
                        for i in range(len(value), expected_length):
                            next_time = last_time + timedelta(seconds=10)
                            value.append(next_time.strftime("%Y-%m-%d %H:%M:%S"))
                            last_time = next_time
                    else:
                        # 센서 데이터 부족시 마지막 값으로 채우기
                        last_val = value[-1] if value else 0.0
                        value.extend([last_val] * (expected_length - len(value)))
                elif len(value) > expected_length:
                    data[key] = value[:expected_length]
        
        try:
            # DataFrame 생성 - 안전한 방식
            df = pd.DataFrame(data)
            
            # 타입 변환 - timestamp는 문자열로 유지, 센서 데이터는 숫자형으로
            for col in df.columns:
                if col == 'timestamp':
                    df[col] = df[col].astype(str)
                    # 각 셀의 타임스탬프 길이 검증
                    for idx, val in enumerate(df[col].head(3)):
                        if len(str(val)) > 25:
                            raise Exception(f"DataFrame의 타임스탬프 {idx}가 연결된 상태: '{str(val)[:50]}...'")
                else:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    if df[col].isna().any():
                        mean_val = df[col].mean()
                        if pd.isna(mean_val):
                            mean_val = 0.0
                        df[col] = df[col].fillna(mean_val)
            
            print(f"DEBUG - DataFrame created successfully: shape={df.shape}")
            print(f"DEBUG - DataFrame dtypes: {df.dtypes.to_dict()}")
            
            # 대용량 데이터 고려하여 샘플 타임스탬프만 출력
            sample_timestamps = df['timestamp'].head(3).tolist()
            print(f"DEBUG - Sample timestamps from DataFrame: {sample_timestamps}")
            
            if len(df) > 10000:
                last_timestamp = df['timestamp'].iloc[-1]
                print(f"DEBUG - Large dataset generated successfully. Last timestamp: '{last_timestamp}'")
            
            return df
            
        except Exception as e:
            print(f"ERROR - Failed to create DataFrame: {str(e)}")
            print(f"DEBUG - Data sample: {dict(list(data.items())[:2])}")
            raise Exception(f"센서 데이터 DataFrame 생성 실패: {str(e)}")
    
    def generate_sensor_data_by_period(self, 
                                     lot_count: int,
                                     selected_sensors: List[str],
                                     work_date_start: datetime,
                                     work_date_end: datetime,
                                     shift_config: Dict[str, Any],
                                     sensor_ranges: Dict[str, Tuple[float, float]],
                                     add_noise: bool = True,
                                     noise_level: float = 1.0,
                                     add_anomalies: bool = False,
                                     anomaly_ratio: int = 3) -> pd.DataFrame:
        """센서 데이터 생성 - 기간 기반 균등 분배 방식, 안전한 타임스탬프 처리"""
        
        # 타임스탬프 기반 시드 생성
        seed = int(datetime.now().timestamp()) % 1000
        np.random.seed(seed)
        
        # 입력 매개변수 타입 검증 및 변환
        lot_count = self.safe_type_conversion(lot_count, int, 15000)
        noise_level = self.safe_type_conversion(noise_level, float, 1.0)
        anomaly_ratio = self.safe_type_conversion(anomaly_ratio, int, 3)
        
        # 안전한 센서 범위 검증 및 정리
        validated_sensor_ranges = {}
        for sensor, range_tuple in sensor_ranges.items():
            try:
                if isinstance(range_tuple, (list, tuple)) and len(range_tuple) >= 2:
                    min_val = self.safe_type_conversion(range_tuple[0], float, 0.0)
                    max_val = self.safe_type_conversion(range_tuple[1], float, 100.0)
                    # 범위 유효성 검증
                    if min_val >= max_val:
                        max_val = min_val + 10.0
                    validated_sensor_ranges[sensor] = (min_val, max_val)
                else:
                    # 기본 범위 사용
                    validated_sensor_ranges[sensor] = self._get_default_sensor_range(sensor)
            except Exception as e:
                print(f"WARNING - Period Invalid range for sensor {sensor}: {e}")
                validated_sensor_ranges[sensor] = self._get_default_sensor_range(sensor)
        
        # 안전한 타임스탬프 생성 (Period 방식도 간격 기반으로 통일)
        try:
            timestamp_list = self._generate_safe_timestamps(
                lot_count, work_date_start, "10초"  # Period 방식도 10초 간격으로 통일
            )
            print(f"DEBUG - Period Safe timestamps generated successfully: {len(timestamp_list)} items")
        except Exception as ts_error:
            print(f"ERROR - Period Failed to generate safe timestamps: {ts_error}")
            # 기본 타임스탬프 생성
            timestamp_list = []
            start_time = datetime.combine(work_date_start, datetime.min.time()) + timedelta(hours=8)
            for i in range(lot_count):
                ts = (start_time + timedelta(seconds=i*10)).strftime("%Y-%m-%d %H:%M:%S") 
                timestamp_list.append(ts)
        
        # 기본 데이터 구조 생성 (Period 방식)
        data = {
            "timestamp": timestamp_list.copy()  # 복사본 생성
        }
        
        print(f"DEBUG - Period Data initialized with {len(data['timestamp'])} timestamps")
        
        # 센서가 선택되지 않은 경우 기본 센서 사용
        if not selected_sensors:
            selected_sensors = ['outlet_humidity', 'inlet_humidity', 'drying_temperature']
            
        for sensor_type in selected_sensors:
            print(f"DEBUG - Period Processing sensor: {sensor_type}")
            
            # 센서 범위 결정 - 타입 안전성 보장 (Period 방식)
            if sensor_type in validated_sensor_ranges:
                sensor_range = validated_sensor_ranges[sensor_type]
            else:
                sensor_range = self._get_default_sensor_range(sensor_type)
            
            try:
                # 센서 값 생성 - 타입 안전성 보장 (Period 방식)
                sensor_values = np.random.uniform(sensor_range[0], sensor_range[1], lot_count)
                
                # 노이즈 추가
                if add_noise:
                    noise_factor = self._get_noise_factor(sensor_type)
                    noise = np.random.normal(0, noise_level * noise_factor, lot_count)
                    sensor_values += noise
                
                # 값 검증 및 정리 (Period 방식)
                column_name = self._get_sensor_column_name(sensor_type)
                sensor_values_list = []
                
                for val in sensor_values:
                    # 안전한 float 변환 및 범위 검증
                    clean_val = self.validate_numeric_range(
                        val, sensor_range[0] * 0.8, sensor_range[1] * 1.2, 
                        (sensor_range[0] + sensor_range[1]) / 2
                    )
                    sensor_values_list.append(clean_val)
                
                data[column_name] = sensor_values_list
                # 대용량 데이터 고려하여 센서별 처리 로그 간소화 (Period 방식)
                if lot_count <= 10000:
                    print(f"DEBUG - Period Added sensor {sensor_type} -> {column_name}: {len(sensor_values_list)} values")
                else:
                    print(f"DEBUG - Period Added sensor {sensor_type} -> {column_name} (large dataset)")
            
            except Exception as sensor_error:
                print(f"ERROR - Period Failed to generate data for sensor {sensor_type}: {sensor_error}")
                # 기본값으로 대체
                default_range = self._get_default_sensor_range(sensor_type)
                default_value = (default_range[0] + default_range[1]) / 2
                column_name = self._get_sensor_column_name(sensor_type)
                data[column_name] = [default_value] * lot_count
        
        # 이상치 추가
        if add_anomalies:
            try:
                self._add_sensor_anomalies(data, lot_count, anomaly_ratio, selected_sensors)
            except Exception as anomaly_error:
                print(f"WARNING - Period Failed to add anomalies: {anomaly_error}")
        
        # 최종 데이터 검증 (Period 방식)
        print(f"DEBUG - Period Final data validation:")
        print(f"DEBUG - Period Data keys: {list(data.keys())}")
        
        # 타임스탬프 검증 (Period 방식)
        if 'timestamp' in data:
            ts_list = data['timestamp']
            print(f"DEBUG - Period Timestamp list type: {type(ts_list)}, length: {len(ts_list)}")
            if isinstance(ts_list, list) and len(ts_list) > 0:
                first_ts = ts_list[0]
                print(f"DEBUG - Period First timestamp: '{first_ts}' (length: {len(str(first_ts))})")
                if len(str(first_ts)) > 25:
                    raise Exception("Period 타임스탬프가 여전히 연결된 상태입니다")
        
        # 모든 데이터 길이 일치 확인 (Period 방식)
        expected_length = lot_count
        for key, value in data.items():
            if len(value) != expected_length:
                print(f"WARNING - Period Length mismatch for {key}: expected {expected_length}, got {len(value)}")
                if len(value) < expected_length:
                    if key == 'timestamp':
                        # 타임스탬프 부족시 마지막 시간 기반으로 추가
                        last_time = datetime.strptime(value[-1], "%Y-%m-%d %H:%M:%S") if value else datetime.now()
                        for i in range(len(value), expected_length):
                            next_time = last_time + timedelta(seconds=10)
                            value.append(next_time.strftime("%Y-%m-%d %H:%M:%S"))
                            last_time = next_time
                    else:
                        # 센서 데이터 부족시 마지막 값으로 채우기
                        last_val = value[-1] if value else 0.0
                        value.extend([last_val] * (expected_length - len(value)))
                elif len(value) > expected_length:
                    data[key] = value[:expected_length]
        
        try:
            # DataFrame 생성 - 안전한 방식 (Period 방식)
            df = pd.DataFrame(data)
            
            # 타입 변환 - timestamp는 문자열로 유지, 센서 데이터는 숫자형으로 (Period 방식)
            for col in df.columns:
                if col == 'timestamp':
                    df[col] = df[col].astype(str)
                    # 각 셀의 타임스탬프 길이 검증 (Period 방식)
                    for idx, val in enumerate(df[col].head(3)):
                        if len(str(val)) > 25:
                            raise Exception(f"Period DataFrame의 타임스탬프 {idx}가 연결된 상태: '{str(val)[:50]}...'")
                else:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    if df[col].isna().any():
                        mean_val = df[col].mean()
                        if pd.isna(mean_val):
                            mean_val = 0.0
                        df[col] = df[col].fillna(mean_val)
            
            print(f"DEBUG - Period DataFrame created successfully: shape={df.shape}")
            print(f"DEBUG - Period DataFrame dtypes: {df.dtypes.to_dict()}")
            
            # 대용량 데이터 고려하여 샘플 타임스탬프만 출력 (Period 방식)
            sample_timestamps = df['timestamp'].head(3).tolist()
            print(f"DEBUG - Period Sample timestamps from DataFrame: {sample_timestamps}")
            
            if len(df) > 10000:
                last_timestamp = df['timestamp'].iloc[-1]
                print(f"DEBUG - Period Large dataset generated successfully. Last timestamp: '{last_timestamp}'")
            
            return df
            
        except Exception as e:
            print(f"ERROR - Failed to create Period DataFrame: {str(e)}")
            print(f"DEBUG - Period Data sample: {dict(list(data.items())[:2])}")
            raise Exception(f"Period 센서 데이터 DataFrame 생성 실패: {str(e)}")
    
    def _generate_period_schedule(self,
                                lot_count: int,
                                work_date_start: datetime,
                                work_date_end: datetime,
                                shift_config: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """기간 기반 균등 분배 일정 생성"""
        work_dates = []
        work_times = []
        
        print(f"DEBUG - Period mode: Distributing {lot_count} lots from {work_date_start.strftime('%Y-%m-%d')} to {work_date_end.strftime('%Y-%m-%d')}")
        
        # 전체 수집 기간 계산 (초 단위)
        total_seconds = (work_date_end - work_date_start).total_seconds()
        
        if total_seconds <= 0:
            print(f"WARNING - Invalid date range, using single day")
            work_date_end = work_date_start + timedelta(days=1)
            total_seconds = 86400  # 1일 = 86400초
        
        # LOT 개수에 따른 간격 계산
        if lot_count <= 1:
            interval_seconds = 0
        else:
            interval_seconds = total_seconds / (lot_count - 1)
        
        print(f"DEBUG - Total period: {total_seconds} seconds, Interval: {interval_seconds:.2f} seconds")
        
        # 시작 시간 설정 (시간대 고려)
        start_hour, start_minute = self._get_shift_start_time(shift_config)
        current_datetime = datetime.combine(work_date_start.date(), datetime.min.time()) + timedelta(hours=start_hour, minutes=start_minute)
        
        # 균등 분배로 시간 생성
        for i in range(lot_count):
            # 현재 시간이 시간대를 벗어나면 다음 근무 시간으로 조정
            while self._is_outside_shift(current_datetime, shift_config):
                current_datetime = self._get_next_shift_start(current_datetime, shift_config)
            
            work_dates.append(current_datetime.strftime("%Y-%m-%d"))
            work_times.append(current_datetime.strftime("%Y-%m-%d %H:%M:%S"))
            
            # 다음 수집 시간으로 이동
            if i < lot_count - 1:  # 마지막이 아닌 경우만
                current_datetime += timedelta(seconds=interval_seconds)
        
        print(f"DEBUG - Generated period schedule from {work_times[0]} to {work_times[-1]}")
        return work_dates, work_times
    
    def _generate_sensor_schedule(self, 
                                lot_count: int,
                                work_date_start: datetime,
                                work_date_end: datetime,
                                shift_config: Dict[str, Any],
                                collection_interval: str = "10초") -> Tuple[List[str], List[str]]:
        """센서 일정 생성 - 우선순위: 1)수집간격 2)시작날짜 3)시간대설정"""
        work_dates = []
        work_times = []
        
        # 1순위: 수집 간격을 초 단위로 변환
        interval_seconds = self._parse_interval_to_seconds(collection_interval)
        print(f"DEBUG - Collection interval: {collection_interval} ({interval_seconds} seconds)")
        
        # 2순위: 수집 시작 날짜 설정 (설정된 시작 날짜를 정확히 사용)
        start_date = work_date_start
        print(f"DEBUG - Start date: {start_date.strftime('%Y-%m-%d')}")
        
        # 3순위: 시간대 설정에 따른 시작 시간 결정
        start_hour, start_minute = self._get_shift_start_time(shift_config)
        current_datetime = datetime.combine(start_date, datetime.min.time()) + timedelta(hours=start_hour, minutes=start_minute)
        print(f"DEBUG - Start time: {current_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"DEBUG - Will generate {lot_count} records with {interval_seconds}s intervals")
        
        # 수집 간격에 따라 순차적으로 시간 생성
        for i in range(lot_count):
            work_dates.append(current_datetime.strftime("%Y-%m-%d"))
            work_times.append(current_datetime.strftime("%Y-%m-%d %H:%M:%S"))
            
            # 다음 수집 시간으로 이동
            current_datetime += timedelta(seconds=interval_seconds)
            
            # 시간대를 벗어나면 다음 날 같은 시간대 시작 시간으로 이동
            if self._is_outside_shift(current_datetime, shift_config):
                current_datetime = self._get_next_shift_start(current_datetime, shift_config)
        
        print(f"DEBUG - Generated schedule from {work_times[0]} to {work_times[-1]}")
        return work_dates, work_times
    
    def _parse_interval_to_seconds(self, interval: str) -> int:
        """수집 간격 문자열을 초 단위로 변환"""
        if interval == "1초":
            return 1
        elif interval == "5초":
            return 5
        elif interval == "10초":
            return 10
        elif interval == "30초":
            return 30
        elif interval == "1분":
            return 60
        else:
            return 10  # 기본값: 10초
    
    def _get_shift_start_time(self, shift_config: Dict[str, Any]) -> Tuple[int, int]:
        """시간대 설정에 따른 시작 시간 반환 (랜덤이 아닌 정확한 시작 시간)"""
        shift_type = shift_config.get("shift_type", "주간(08:00-16:00)")
        
        if shift_type == "주간(08:00-16:00)":
            return 8, 0  # 08:00 시작
        elif shift_type == "야간(22:00-06:00)":
            return 22, 0  # 22:00 시작
        elif shift_type == "전체(24시간)":
            return 0, 0  # 00:00 시작
        elif shift_type == "사용자 정의":
            start_hour = shift_config.get("start_hour", 8)
            return start_hour, 0
        else:
            return 8, 0  # 기본값: 08:00
    
    def _is_outside_shift(self, current_time: datetime, shift_config: Dict[str, Any]) -> bool:
        """현재 시간이 설정된 시간대를 벗어났는지 확인"""
        shift_type = shift_config.get("shift_type", "주간(08:00-16:00)")
        current_hour = current_time.hour
        
        if shift_type == "주간(08:00-16:00)":
            return current_hour >= 16 or current_hour < 8
        elif shift_type == "야간(22:00-06:00)":
            return current_hour >= 6 and current_hour < 22
        elif shift_type == "전체(24시간)":
            return False  # 24시간이므로 벗어날 수 없음
        elif shift_type == "사용자 정의":
            start_hour = shift_config.get("start_hour", 8)
            end_hour = shift_config.get("end_hour", 16)
            if start_hour <= end_hour:
                return current_hour >= end_hour or current_hour < start_hour
            else:  # 야간 시간대 (예: 22:00-06:00)
                return current_hour >= end_hour and current_hour < start_hour
        else:
            return current_hour >= 16 or current_hour < 8
    
    def _get_next_shift_start(self, current_time: datetime, shift_config: Dict[str, Any]) -> datetime:
        """다음 날 같은 시간대의 시작 시간 반환"""
        start_hour, start_minute = self._get_shift_start_time(shift_config)
        
        # 다음 날로 이동
        next_day = current_time.date() + timedelta(days=1)
        next_shift_start = datetime.combine(next_day, datetime.min.time()) + timedelta(hours=start_hour, minutes=start_minute)
        
        return next_shift_start
    
    def _generate_sensor_time(self, shift_config: Dict[str, Any]) -> Tuple[int, int]:
        """센서 시간 생성"""
        shift_type = shift_config.get("shift_type", "주간(08:00-16:00)")
        
        if shift_type == "주간(08:00-16:00)":
            work_hour = np.random.randint(8, 16)
        elif shift_type == "야간(22:00-06:00)":
            work_hour = np.random.choice([22, 23, 0, 1, 2, 3, 4, 5])
        elif shift_type == "전체(24시간)":
            work_hour = np.random.randint(0, 24)
        else:  # 사용자 정의
            start_hour = shift_config.get("start_hour", 8)
            end_hour = shift_config.get("end_hour", 16)
            if start_hour <= end_hour:
                work_hour = np.random.randint(start_hour, end_hour + 1)
            else:
                work_hour = np.random.choice(list(range(start_hour, 24)) + list(range(0, end_hour + 1)))
        
        work_minute = np.random.randint(0, 60)
        return work_hour, work_minute
    
    def _add_sensor_anomalies(self, data: Dict[str, Any], lot_count: int, anomaly_ratio: int, selected_sensors: List[str]):
        """센서 이상치 추가"""
        n_anomalies = int(lot_count * anomaly_ratio / 100)
        if n_anomalies > 0:
            anomaly_indices = np.random.choice(lot_count, n_anomalies, replace=False)
            
            for idx in anomaly_indices:
                for sensor_type in selected_sensors:
                    column_name = self._get_sensor_column_name(sensor_type)
                    if column_name in data:
                        anomaly_value = float(self._get_anomaly_value(sensor_type))  # 명시적 float 변환
                        data[column_name][idx] = anomaly_value
                        print(f"DEBUG - Added anomaly at index {idx} for {sensor_type}: {anomaly_value}")
    
    def _get_noise_factor(self, sensor_type: str) -> float:
        """센서 타입별 노이즈 팩터 반환"""
        noise_factors = {
            # 건조기 센서
            "outlet_humidity": 0.3,
            "inlet_humidity": 0.2,
            "drying_temperature": 0.5,
            "air_flow": 0.2,
            "pressure_diff": 0.1,
            # 분급기 센서
            "mill_rpm": 0.2,
            "crushing_pressure": 0.1,
            "classifier_speed": 0.2,
            "vacuum_pressure": 0.1,
            "particle_size": 0.3,
            # 펌프 센서
            "flow_rate": 0.3,
            "discharge_pressure": 0.1,
            "suction_pressure": 0.1,
            "vibration": 0.2,
            "temperature": 0.5,
            # 컴프레서 센서
            "discharge_temperature": 0.5,
            "current": 0.3,
            # 모터 센서
            "rpm": 0.2,
            "torque": 0.3,
            # 보일러 센서
            "steam_pressure": 0.1,
            "steam_temperature": 0.5,
            "feed_water_temp": 0.3,
            "fuel_pressure": 0.1,
            "oxygen_level": 0.2
        }
        return noise_factors.get(sensor_type, 0.2)
    
    def _get_sensor_column_name(self, sensor_type: str) -> str:
        """센서 타입별 컬럼명 반환"""
        column_names = {
            # 건조기 센서
            "outlet_humidity": "출구습도_%",
            "inlet_humidity": "입구습도_%", 
            "drying_temperature": "건조온도_C",
            "air_flow": "풍량_m3h",
            "pressure_diff": "압력차_Pa",
            "moisture_content": "수분값_wt%",
            "residence_time": "체류시간_s",
            # 분급기 센서
            "mill_rpm": "밀회전속도_RPM",
            "crushing_pressure": "분쇄압력_MPa",
            "classifier_speed": "분급기속도_RPM",
            "vacuum_pressure": "진공압_MPa",
            "particle_size": "입자크기_um",
            "particle_d50": "입도D50_um",
            # 펌프 센서
            "flow_rate": "유량_Lmin",
            "discharge_pressure": "토출압력_MPa",
            "suction_pressure": "흡입압력_MPa",
            "vibration": "진동_mms",
            "temperature": "온도_C",
            # 컴프레서 센서
            "discharge_temperature": "토출온도_C",
            "current": "전류_A",
            # 모터 센서
            "rpm": "회전속도_RPM",
            "torque": "토크_Nm",
            # 보일러 센서
            "steam_pressure": "증기압력_MPa",
            "steam_temperature": "증기온도_C",
            "feed_water_temp": "급수온도_C",
            "fuel_pressure": "연료압력_MPa",
            "oxygen_level": "산소농도_%"
        }
        return column_names.get(sensor_type, f"{sensor_type.capitalize()}_Value")
    
    def _get_anomaly_value(self, sensor_type: str) -> float:
        """센서 타입별 이상치 값 반환"""
        anomaly_values = {
            # 건조기 센서
            "outlet_humidity": np.random.uniform(25, 40),
            "inlet_humidity": np.random.uniform(5, 15),
            "drying_temperature": np.random.uniform(250, 300),
            "air_flow": np.random.uniform(6000, 8000),
            "pressure_diff": np.random.uniform(800, 1200),
            # 분급기 센서
            "mill_rpm": np.random.uniform(1000, 1400),
            "crushing_pressure": np.random.uniform(12, 18),
            "classifier_speed": np.random.uniform(2000, 2500),
            "vacuum_pressure": np.random.uniform(1.2, 1.8),
            "particle_size": np.random.uniform(180, 250),
            # 펌프 센서
            "flow_rate": np.random.uniform(250, 350),
            "discharge_pressure": np.random.uniform(18, 25),
            "suction_pressure": np.random.uniform(4, 6),
            "vibration": np.random.uniform(8, 15),
            "temperature": np.random.uniform(100, 150),
            # 컴프레서 센서
            "discharge_temperature": np.random.uniform(180, 250),
            "current": np.random.uniform(120, 180),
            # 모터 센서
            "rpm": np.random.uniform(3500, 4500),
            "torque": np.random.uniform(600, 1000),
            # 보일러 센서
            "steam_pressure": np.random.uniform(25, 35),
            "steam_temperature": np.random.uniform(350, 450),
            "feed_water_temp": np.random.uniform(180, 220),
            "fuel_pressure": np.random.uniform(6, 10),
            "oxygen_level": np.random.uniform(10, 15)
        }
        return anomaly_values.get(sensor_type, np.random.uniform(0, 1))
    
    def _get_default_sensor_range(self, sensor_type: str) -> Tuple[float, float]:
        """센서 타입별 기본 범위 반환"""
        default_ranges = {
            # 건조기 센서
            "outlet_humidity": (40.0, 80.0),
            "inlet_humidity": (5.0, 15.0),
            "drying_temperature": (80.0, 200.0),
            "air_flow": (1000, 5000),
            "pressure_diff": (50, 500),
            "moisture_content": (0.0, 1.0),
            "residence_time": (200.0, 300.0),
            # 분급기 센서
            "mill_rpm": (100, 800),
            "crushing_pressure": (2.0, 10.0),
            "classifier_speed": (300, 1500),
            "vacuum_pressure": (0.1, 0.8),
            "particle_size": (10, 100),
            "particle_d50": (5.0, 25.0),
            # 펌프 센서
            "flow_rate": (10, 200),
            "discharge_pressure": (2.0, 15.0),
            "suction_pressure": (0.5, 3.0),
            "vibration": (0.5, 5.0),
            "temperature": (20.0, 80.0),
            # 컴프레서 센서
            "discharge_temperature": (60.0, 150.0),
            "current": (10.0, 100.0),
            # 모터 센서
            "rpm": (500, 3000),
            "torque": (50, 500),
            # 보일러 센서
            "steam_pressure": (5.0, 20.0),
            "steam_temperature": (150.0, 300.0),
            "feed_water_temp": (80.0, 150.0),
            "fuel_pressure": (1.0, 5.0),
            "oxygen_level": (2.0, 8.0)
        }
        return default_ranges.get(sensor_type, (0.0, 100.0))
    
    def save_sensor_data(self, data: pd.DataFrame, data_count: int) -> str:
        """센서 데이터 저장"""
        filename = self.generate_timestamp_filename("sensor_data", data_count, f"{data_count}records")
        filepath = os.path.join(self.data_dir, "sensor", filename)
        
        if self.save_data(data, filepath):
            return filepath
        else:
            raise Exception("센서 데이터 저장 실패")
    
    def _generate_pattern_based_values(self, sensor_range: Tuple[float, float], lot_count: int, 
                                     data_pattern: str, variation_intensity: int, sensor_type: str, seed: int) -> np.ndarray:
        """패턴과 변동폭을 고려한 센서 값 생성 - 변동폭 강도에 따라 확실히 다른 데이터 생성"""
        
        min_val, max_val = sensor_range
        center_val = (min_val + max_val) / 2
        range_val = max_val - min_val
        
        # 변동폭 강도에 따라 완전히 다른 시작점과 범위 사용 (확실한 차이 보장)
        intensity_multiplier = variation_intensity * 12345  # 강도별 고유 값
        specific_seed = (int(datetime.now().timestamp() * 1000000) + intensity_multiplier) % 2147483647
        np.random.seed(specific_seed)
        
        print(f"DEBUG - VARIATION CHECK: sensor={sensor_type}, intensity={variation_intensity}, seed={specific_seed}, range={range_val:.2f}")
        
        # 각 강도별로 완전히 다른 특성 적용
        if variation_intensity == 1:
            # 강도 1: 매우 좁은 범위, 센터 근처
            actual_range = range_val * 0.05  # 5% 범위만 사용
            start_point = center_val - actual_range/2
            end_point = center_val + actual_range/2
            base_std = actual_range * 0.1
            
        elif variation_intensity == 2:
            # 강도 2: 좁은 범위
            actual_range = range_val * 0.15  # 15% 범위 사용
            start_point = center_val - actual_range/2
            end_point = center_val + actual_range/2
            base_std = actual_range * 0.2
            
        elif variation_intensity == 3:
            # 강도 3: 중간-좁은 범위
            actual_range = range_val * 0.3  # 30% 범위 사용
            start_point = min_val + range_val * 0.1
            end_point = start_point + actual_range
            base_std = actual_range * 0.25
            
        elif variation_intensity == 4:
            # 강도 4: 중간 범위
            actual_range = range_val * 0.45  # 45% 범위 사용
            start_point = min_val + range_val * 0.15
            end_point = start_point + actual_range
            base_std = actual_range * 0.3
            
        elif variation_intensity == 5:
            # 강도 5: 중간-큰 범위
            actual_range = range_val * 0.6  # 60% 범위 사용
            start_point = min_val + range_val * 0.2
            end_point = start_point + actual_range
            base_std = actual_range * 0.35
            
        elif variation_intensity == 6:
            # 강도 6: 큰 범위
            actual_range = range_val * 0.75  # 75% 범위 사용
            start_point = min_val + range_val * 0.1
            end_point = start_point + actual_range
            base_std = actual_range * 0.4
            
        elif variation_intensity == 7:
            # 강도 7: 매우 큰 범위
            actual_range = range_val * 0.85  # 85% 범위 사용
            start_point = min_val + range_val * 0.05
            end_point = start_point + actual_range
            base_std = actual_range * 0.45
            
        elif variation_intensity == 8:
            # 강도 8: 거의 전체 범위
            actual_range = range_val * 0.95  # 95% 범위 사용
            start_point = min_val + range_val * 0.025
            end_point = start_point + actual_range
            base_std = actual_range * 0.5
            
        elif variation_intensity == 9:
            # 강도 9: 전체 범위 + 높은 변동
            actual_range = range_val * 1.0  # 100% 범위 사용
            start_point = min_val
            end_point = max_val
            base_std = actual_range * 0.6
            
        else:  # variation_intensity == 10
            # 강도 10: 전체 범위 + 최대 변동
            actual_range = range_val * 1.0  # 100% 범위 사용
            start_point = min_val
            end_point = max_val
            base_std = actual_range * 0.8
        
        # 실제 사용되는 범위와 표준편차 출력
        print(f"DEBUG - RANGE DETAILS: start={start_point:.4f}, end={end_point:.4f}, std={base_std:.4f}, actual_range={actual_range:.4f}")
        
        if data_pattern == "정상":
            # 정상 패턴: 설정된 범위 내에서 정규분포
            pattern_center = (start_point + end_point) / 2
            values = np.random.normal(pattern_center, base_std, lot_count)
            
        elif data_pattern == "증가 추세":
            # 증가 추세: 시작점에서 끝점으로 선형 증가 + 노이즈
            trend = np.linspace(start_point, end_point, lot_count)
            noise = np.random.normal(0, base_std, lot_count)
            values = trend + noise
            
        elif data_pattern == "감소 추세":
            # 감소 추세: 끝점에서 시작점으로 선형 감소 + 노이즈
            trend = np.linspace(end_point, start_point, lot_count)
            noise = np.random.normal(0, base_std, lot_count)
            values = trend + noise
            
        elif data_pattern == "주기적 변동":
            # 주기적 변동: 사인파 패턴 + 강도별 진폭
            periods = 2 + variation_intensity // 3  # 강도에 따라 2~5개 주기
            x = np.linspace(0, 2 * np.pi * periods, lot_count)
            wave_amplitude = actual_range * 0.4  # 범위의 40%를 진폭으로 사용
            pattern_center = (start_point + end_point) / 2
            sine_wave = np.sin(x) * wave_amplitude
            base_values = np.random.normal(pattern_center, base_std * 0.3, lot_count)
            values = base_values + sine_wave
            
        elif data_pattern == "계단식 변화":
            # 계단식 변화: 단계별 구간 설정
            steps = 3 + variation_intensity // 2  # 강도에 따라 3~8단계
            step_size = lot_count // steps
            values = np.zeros(lot_count)
            
            for i in range(steps):
                start_idx = i * step_size
                end_idx = (i + 1) * step_size if i < steps - 1 else lot_count
                # 각 단계의 값은 전체 범위를 균등 분할
                step_progress = i / (steps - 1) if steps > 1 else 0
                step_val = start_point + (end_point - start_point) * step_progress
                step_noise = np.random.normal(0, base_std * 0.5, end_idx - start_idx)
                values[start_idx:end_idx] = step_val + step_noise
                
        elif data_pattern == "급격한 변화":
            # 급격한 변화: 랜덤 점프가 있는 패턴
            pattern_center = (start_point + end_point) / 2
            base_values = np.random.normal(pattern_center, base_std, lot_count)
            values = base_values.copy()
            
            # 점프 횟수와 크기는 강도에 비례
            jump_rate = 0.02 + 0.03 * (variation_intensity / 10.0)  # 2%~5%
            jump_count = max(1, int(lot_count * jump_rate))
            jump_points = np.random.choice(lot_count, jump_count, replace=False)
            
            for jump_idx in jump_points:
                jump_magnitude = np.random.choice([-1, 1]) * actual_range * (0.3 + 0.4 * variation_intensity / 10.0)
                jump_duration = np.random.randint(2, 10 + variation_intensity)
                end_idx = min(jump_idx + jump_duration, lot_count)
                
                for j in range(jump_idx, end_idx):
                    decay = 1.0 - (j - jump_idx) / jump_duration
                    values[j] += jump_magnitude * decay
                
        else:
            # 기본값: 정상 패턴
            pattern_center = (start_point + end_point) / 2
            values = np.random.normal(pattern_center, base_std, lot_count)
        
        # 센서 범위 내로 클리핑하되, 최대한 원래 분포 유지
        values = np.clip(values, min_val, max_val)
        
        # 결과 통계 출력 - 변동폭 강도가 실제로 반영되었는지 확인
        value_range = np.max(values) - np.min(values)
        coverage_percent = (value_range / range_val) * 100 if range_val > 0 else 0
        print(f"DEBUG - FINAL RESULT: sensor={sensor_type}, intensity={variation_intensity}")
        print(f"DEBUG - VALUES STATS: min={np.min(values):.4f}, max={np.max(values):.4f}, std={np.std(values):.4f}")
        print(f"DEBUG - RANGE INFO: used_range={value_range:.4f}, full_range={range_val:.4f}, coverage={coverage_percent:.1f}%")
        print(f"DEBUG - EXPECTED vs ACTUAL: expected_range={actual_range:.4f}, actual_std={np.std(values):.4f}")
        
        return values


class ExperimentalDataGenerator(DataGenerationEngine):
    """실험 데이터 생성기"""
    
    def __init__(self):
        super().__init__()
    
    def generate_experimental_data(self,
                                 experiment_config: Dict[str, Any],
                                 factor_ranges: Dict[str, Tuple[float, float]],
                                 experiment_schedule: Dict[str, Any],
                                 metadata: Dict[str, Any]) -> pd.DataFrame:
        """실험 데이터 생성"""
        
        # 실험 계획 생성
        experiment_plan = self.generate_experiment_plan(
            experiment_config, factor_ranges
        )
        
        # 실험 일정 생성
        experiment_dates, experiment_times = self._generate_experiment_schedule(
            len(experiment_plan["Run"]), experiment_schedule
        )
        
        # 실험 결과 시뮬레이션
        experiment_results = self.simulate_experiment_results(
            experiment_plan, metadata.get("experiment_objective", "순도 최대화")
        )
        
        # 메타데이터 추가
        experiment_results.update({
            "Experiment_Date": experiment_dates,
            "Experiment_Time": experiment_times,
            "Experimenter": metadata.get("experimenter", "연구원A"),
            "Experiment_Purpose": metadata.get("experiment_purpose", "공정 조건 최적화"),
            "Experiment_Objective": metadata.get("experiment_objective", "순도 최대화"),
            "Data_Type": "Experimental",
            "Generated_At": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        return pd.DataFrame(experiment_results)
    
    def generate_experiment_plan(self, 
                               experiment_config: Dict[str, Any],
                               factor_ranges: Dict[str, Tuple[float, float]]) -> Dict[str, Any]:
        """실험 계획 생성"""
        experiment_type = experiment_config.get("experiment_type", "Full Factorial")
        factors = experiment_config.get("selected_factors", [])
        levels = experiment_config.get("levels", 3)
        replications = experiment_config.get("replications", 1)
        num_experiments = experiment_config.get("num_experiments", 25)
        
        experiment_plan = {}
        
        if experiment_type == "Full Factorial":
            experiment_plan = self._generate_full_factorial(factors, factor_ranges, levels, replications)
        elif experiment_type == "Fractional Factorial":
            experiment_plan = self._generate_fractional_factorial(factors, factor_ranges, replications)
        else:
            experiment_plan = self._generate_custom_design(factors, factor_ranges, num_experiments)
        
        return experiment_plan
    
    def _generate_full_factorial(self, 
                               factors: List[str],
                               factor_ranges: Dict[str, Tuple[float, float]],
                               levels: int,
                               replications: int) -> Dict[str, Any]:
        """완전 요인 설계 생성"""
        factor_levels = []
        for factor in factors:
            min_val, max_val = factor_ranges[factor]
            factor_levels.append(np.linspace(min_val, max_val, levels))
        
        combinations = list(product(*factor_levels))
        
        # 반복 실험 추가
        all_combinations = []
        for _ in range(replications):
            all_combinations.extend(combinations)
        
        experiment_plan = {"Run": list(range(1, len(all_combinations) + 1))}
        
        for i, factor in enumerate(factors):
            experiment_plan[factor] = [combo[i] for combo in all_combinations]
        
        return experiment_plan
    
    def _generate_fractional_factorial(self,
                                     factors: List[str],
                                     factor_ranges: Dict[str, Tuple[float, float]],
                                     replications: int) -> Dict[str, Any]:
        """부분 요인 설계 생성"""
        factor_levels = []
        for factor in factors:
            min_val, max_val = factor_ranges[factor]
            factor_levels.append([min_val, max_val])
        
        n_factors = len(factors)
        n_runs = 2**(n_factors-1)  # 반분 설계
        
        runs = []
        for i in range(n_runs):
            run = []
            for j in range(n_factors):
                level_idx = (i >> j) & 1
                run.append(factor_levels[j][level_idx])
            runs.append(run)
        
        # 반복 실험 추가
        all_runs = []
        for _ in range(replications):
            all_runs.extend(runs)
        
        experiment_plan = {"Run": list(range(1, len(all_runs) + 1))}
        for i, factor in enumerate(factors):
            experiment_plan[factor] = [run[i] for run in all_runs]
        
        return experiment_plan
    
    def _generate_custom_design(self,
                              factors: List[str],
                              factor_ranges: Dict[str, Tuple[float, float]],
                              num_experiments: int) -> Dict[str, Any]:
        """사용자 정의 설계 생성"""
        np.random.seed(42)
        experiment_plan = {"Run": list(range(1, num_experiments + 1))}
        
        for factor in factors:
            min_val, max_val = factor_ranges[factor]
            experiment_plan[factor] = np.random.uniform(min_val, max_val, num_experiments)
        
        return experiment_plan
    
    def simulate_experiment_results(self, 
                                  experiment_plan: Dict[str, Any],
                                  objective: str) -> Dict[str, Any]:
        """실험 결과 시뮬레이션"""
        results = experiment_plan.copy()
        n_runs = len(results["Run"])
        
        np.random.seed(42)
        
        # 순도 계산
        if "온도" in results and "pH" in results:
            purity = 95 + 3 * (np.array(results["온도"]) - 150) / 50 + 2 * (np.array(results["pH"]) - 6.5) / 2
            purity += np.random.normal(0, 0.5, n_runs)
            results["Purity_%"] = np.clip(purity, 90, 99)
        else:
            results["Purity_%"] = np.random.uniform(95, 99, n_runs)
        
        # 수율 계산
        if "압력" in results and "반응시간" in results:
            yield_val = 85 + 8 * (np.array(results["압력"]) - 1.5) / 1.5 + 5 * (np.array(results["반응시간"]) - 60) / 120
            yield_val += np.random.normal(0, 1, n_runs)
            results["Yield_%"] = np.clip(yield_val, 80, 98)
        else:
            results["Yield_%"] = np.random.uniform(85, 95, n_runs)
        
        # 추가 응답 변수
        results["Reaction_Time_min"] = np.random.uniform(30, 300, n_runs)
        results["Byproduct_ppm"] = np.random.uniform(50, 500, n_runs)
        results["Energy_kWh"] = np.random.uniform(10, 100, n_runs)
        
        # 목적에 따른 조정
        if objective == "순도 최대화":
            results["Purity_%"] = np.array(results["Purity_%"]) + np.random.uniform(0, 1, n_runs)
        elif objective == "수율 최대화":
            results["Yield_%"] = np.array(results["Yield_%"]) + np.random.uniform(0, 2, n_runs)
        
        return results
    
    def _generate_experiment_schedule(self,
                                    total_runs: int,
                                    experiment_schedule: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """실험 일정 생성"""
        experiment_date_start = experiment_schedule.get("experiment_date_start")
        experiment_date_end = experiment_schedule.get("experiment_date_end")
        experiment_shift_type = experiment_schedule.get("experiment_shift_type", "일반 실험시간(09:00-17:00)")
        experiment_interval = experiment_schedule.get("experiment_interval", "동시 수행")
        
        experiment_dates = []
        experiment_times = []
        
        for i in range(total_runs):
            # 실험 일자 생성
            days_diff = (experiment_date_end - experiment_date_start).days
            if days_diff == 0:
                experiment_date = experiment_date_start
            else:
                if experiment_interval == "일별 수행":
                    day_offset = i % (days_diff + 1)
                else:
                    day_offset = int((i / total_runs) * days_diff)
                experiment_date = experiment_date_start + timedelta(days=day_offset)
            
            # 실험 시간 생성
            experiment_hour, experiment_minute = self._generate_experiment_time(
                experiment_shift_type, experiment_interval, i, total_runs
            )
            
            experiment_datetime = datetime.combine(experiment_date, datetime.min.time()) + timedelta(hours=experiment_hour, minutes=experiment_minute)
            
            experiment_dates.append(experiment_date.strftime("%Y-%m-%d"))
            experiment_times.append(experiment_datetime.strftime("%Y-%m-%d %H:%M:%S"))
        
        return experiment_dates, experiment_times
    
    def _generate_experiment_time(self,
                                shift_type: str,
                                interval: str,
                                run_index: int,
                                total_runs: int) -> Tuple[int, int]:
        """실험 시간 생성"""
        if shift_type == "일반 실험시간(09:00-17:00)":
            start_hour, end_hour = 9, 17
        elif shift_type == "연장 실험시간(09:00-21:00)":
            start_hour, end_hour = 9, 21
        elif shift_type == "24시간 연속실험":
            start_hour, end_hour = 0, 24
        else:
            start_hour, end_hour = 9, 17
        
        if interval == "동시 수행":
            experiment_hour = np.random.randint(start_hour, min(end_hour, 24))
            experiment_minute = np.random.randint(0, 60)
        elif interval == "1시간 간격":
            base_hour = start_hour + (run_index % (end_hour - start_hour))
            experiment_hour = min(base_hour, end_hour - 1)
            experiment_minute = 0
        elif interval == "2시간 간격":
            base_hour = start_hour + (run_index * 2) % (end_hour - start_hour)
            experiment_hour = min(start_hour + base_hour, end_hour - 1)
            experiment_minute = 0
        elif interval == "4시간 간격":
            base_hour = start_hour + (run_index * 4) % (end_hour - start_hour)
            experiment_hour = min(start_hour + base_hour, end_hour - 1)
            experiment_minute = 0
        else:  # 일별 수행
            experiment_hour = np.random.randint(start_hour, min(end_hour, 24))
            experiment_minute = np.random.randint(0, 60)
        
        return experiment_hour, experiment_minute
    
    def save_experimental_data(self, data: pd.DataFrame, experiment_type: str) -> str:
        """실험 데이터 저장"""
        filename = self.generate_timestamp_filename("experimental_data", len(data), f"{experiment_type}_{len(data)}runs")
        filepath = os.path.join(self.data_dir, "experimental", filename)
        
        if self.save_data(data, filepath):
            return filepath
        else:
            raise Exception("실험 데이터 저장 실패")


class CostProductionDataGenerator(DataGenerationEngine):
    """원가/생산 이력 데이터 생성기"""
    
    def __init__(self):
        super().__init__()
    
    def generate_cost_production_data(self, config: Dict[str, Any]) -> pd.DataFrame:
        """원가/생산 이력 데이터 생성"""
        record_count = config['record_count']
        start_date = config['start_date']
        end_date = config['end_date']
        
        # 시간 범위 생성
        date_range = pd.date_range(start=start_date, end=end_date, periods=record_count)
        
        # 기본 투입량 생성
        material_a = np.random.uniform(config['material_a_range'][0], config['material_a_range'][1], record_count)
        material_b = np.random.uniform(config['material_b_range'][0], config['material_b_range'][1], record_count)
        catalyst = np.random.uniform(config['catalyst_range'][0], config['catalyst_range'][1], record_count)
        
        # 운전 조건 생성
        temperature = np.random.uniform(config['temp_range'][0], config['temp_range'][1], record_count)
        pressure = np.random.uniform(config['pressure_range'][0], config['pressure_range'][1], record_count)
        flow_rate = np.random.uniform(config['flow_range'][0], config['flow_range'][1], record_count)
        
        # 유틸리티 사용량 생성
        steam = np.random.uniform(config['steam_range'][0], config['steam_range'][1], record_count)
        electricity = np.random.uniform(config['electricity_range'][0], config['electricity_range'][1], record_count)
        cooling_water = np.random.uniform(config['cooling_range'][0], config['cooling_range'][1], record_count)
        
        # 가격 변동성 적용
        material_a_price = self._apply_price_volatility(config['material_a_cost'], config['price_volatility'], record_count)
        material_b_price = self._apply_price_volatility(config['material_b_cost'], config['price_volatility'], record_count)
        catalyst_price = self._apply_price_volatility(config['catalyst_cost'], config['price_volatility'], record_count)
        
        steam_price = self._apply_price_volatility(config['steam_cost'], config['utility_volatility'], record_count)
        electricity_price = self._apply_price_volatility(config['electricity_cost'], config['utility_volatility'], record_count)
        cooling_price = self._apply_price_volatility(config['cooling_cost'], config['utility_volatility'], record_count)
        
        # 계절별 효과 적용
        if config.get('seasonal_effect', False):
            seasonal_factor = 1 + 0.1 * np.sin(2 * np.pi * np.arange(record_count) / record_count)
            material_a_price *= seasonal_factor
            material_b_price *= seasonal_factor
            steam_price *= seasonal_factor
        
        # 교대 근무 효과
        if config.get('include_shifts', False):
            shift_effect = np.random.choice([0.95, 1.0, 1.05], record_count, p=[0.3, 0.4, 0.3])
            material_a *= shift_effect
            material_b *= shift_effect
        
        # 설비 마모 효과
        if config.get('include_equipment_wear', False):
            wear_trend = 1 + 0.02 * np.arange(record_count) / record_count
            material_a *= wear_trend
            catalyst *= wear_trend
        
        # 품질 지표 계산
        purity, yield_rate = self._calculate_quality_metrics(
            material_a, material_b, catalyst, temperature, pressure,
            config['purity_range'], config['yield_range'],
            config['correlation_strength'], config['noise_level'], record_count
        )
        
        # 비용 계산
        material_cost = (material_a * material_a_price + material_b * material_b_price + catalyst * catalyst_price)
        utility_cost = (steam * steam_price + electricity * electricity_price + cooling_water * cooling_price)
        total_cost = material_cost + utility_cost
        
        # 생산율 계산
        production_rate = 95 + 10 * (yield_rate - np.mean(config['yield_range'])) / (config['yield_range'][1] - config['yield_range'][0])
        production_rate = np.clip(production_rate, 80, 100)
        
        # 데이터 구조 생성
        data = {
            'lot_number': [f'LOT_{i+1:04d}' for i in range(record_count)],
            'timestamp': date_range.strftime('%Y-%m-%d %H:%M:%S'),
            'material_a': np.round(material_a, 2),
            'material_b': np.round(material_b, 2),
            'catalyst': np.round(catalyst, 2),
            'temperature': np.round(temperature, 1),
            'pressure': np.round(pressure, 2),
            'flow_rate': np.round(flow_rate, 1),
            'steam': np.round(steam, 1),
            'electricity': np.round(electricity, 1),
            'cooling_water': np.round(cooling_water, 1),
            'purity': np.round(purity, 2),
            'yield': np.round(yield_rate, 2),
            'production_rate': np.round(production_rate, 1),
            'material_cost': np.round(material_cost, 0).astype(int),
            'utility_cost': np.round(utility_cost, 0).astype(int),
            'total_cost': np.round(total_cost, 0).astype(int),
            'material_a_price': np.round(material_a_price, 2),
            'material_b_price': np.round(material_b_price, 2),
            'catalyst_price': np.round(catalyst_price, 2),
            'steam_price': np.round(steam_price, 2),
            'electricity_price': np.round(electricity_price, 2),
            'cooling_price': np.round(cooling_price, 2),
            'data_type': ['Cost_Production_History'] * record_count,
            'generated_at': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')] * record_count
        }
        
        return pd.DataFrame(data)
    
    def _apply_price_volatility(self, base_price: float, volatility: float, count: int) -> np.ndarray:
        """가격 변동성 적용"""
        return base_price * (1 + np.random.normal(0, volatility/100, count))
    
    def _calculate_quality_metrics(self,
                                 material_a: np.ndarray,
                                 material_b: np.ndarray,
                                 catalyst: np.ndarray,
                                 temperature: np.ndarray,
                                 pressure: np.ndarray,
                                 purity_range: Tuple[float, float],
                                 yield_range: Tuple[float, float],
                                 correlation_strength: float,
                                 noise_level: float,
                                 count: int) -> Tuple[np.ndarray, np.ndarray]:
        """품질 지표 계산"""
        
        # 순도 계산
        purity_base = purity_range[0] + (purity_range[1] - purity_range[0]) * 0.5
        purity = (
            purity_base +
            correlation_strength * 0.1 * (material_a - np.mean(material_a)) / np.std(material_a) +
            correlation_strength * 0.05 * (catalyst - np.mean(catalyst)) / np.std(catalyst) +
            correlation_strength * 0.03 * (temperature - np.mean(temperature)) / np.std(temperature) +
            np.random.normal(0, noise_level * 0.5, count)
        )
        purity = np.clip(purity, purity_range[0], purity_range[1])
        
        # 수율 계산
        yield_base = yield_range[0] + (yield_range[1] - yield_range[0]) * 0.5
        yield_rate = (
            yield_base +
            correlation_strength * 0.08 * (material_b - np.mean(material_b)) / np.std(material_b) +
            correlation_strength * 0.06 * (catalyst - np.mean(catalyst)) / np.std(catalyst) +
            correlation_strength * 0.04 * (pressure - np.mean(pressure)) / np.std(pressure) +
            np.random.normal(0, noise_level * 0.3, count)
        )
        yield_rate = np.clip(yield_rate, yield_range[0], yield_range[1])
        
        return purity, yield_rate
    
    def _add_missing_data(self, data: Dict[str, Any], lot_count: int, missing_data_ratio: int, selected_sensors: List[str]):
        """센서 데이터에 결측치 추가"""
        n_missing = int(lot_count * missing_data_ratio / 100)
        if n_missing > 0:
            missing_indices = np.random.choice(lot_count, n_missing, replace=False)
            
            for idx in missing_indices:
                # 각 인덱스에서 랜덤하게 센서들 중 일부에만 결측치 적용
                sensors_to_apply = np.random.choice(
                    selected_sensors, 
                    np.random.randint(1, min(3, len(selected_sensors)) + 1), 
                    replace=False
                )
                
                for sensor_type in sensors_to_apply:
                    column_name = self._get_sensor_column_name(sensor_type)
                    if column_name in data:
                        data[column_name][idx] = None  # 결측치로 설정
                        print(f"DEBUG - Added missing data at index {idx} for {sensor_type}")

    def save_cost_production_data(self, data: pd.DataFrame) -> str:
        """원가/생산 이력 데이터 저장"""
        filename = self.generate_timestamp_filename("cost_production_history", len(data), f"{len(data)}records")
        filepath = os.path.join(self.data_dir, "cost_production", filename)
        
        if self.save_data(data, filepath):
            return filepath
        else:
            raise Exception("원가/생산 이력 데이터 저장 실패") 