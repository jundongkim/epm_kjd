"""
DX-AI Manufacturing Copilot - 데이터 생성 엔진

백엔드 비즈니스 로직을 담당하는 데이터 생성 엔진 클래스들
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
from itertools import product
from typing import Dict, Any, List, Tuple, Optional
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
            os.path.join(self.data_dir, "cost_production")
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
    
    def save_data(self, data: pd.DataFrame, filepath: str) -> bool:
        """데이터 저장"""
        try:
            data.to_csv(filepath, index=False, encoding='utf-8-sig')
            return True
        except Exception as e:
            print(f"데이터 저장 오류: {str(e)}")
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
    
    def save_cost_production_data(self, data: pd.DataFrame) -> str:
        """원가/생산 이력 데이터 저장"""
        filename = self.generate_timestamp_filename("cost_production_history", len(data), f"{len(data)}records")
        filepath = os.path.join(self.data_dir, "cost_production", filename)
        
        if self.save_data(data, filepath):
            return filepath
        else:
            raise Exception("원가/생산 이력 데이터 저장 실패") 