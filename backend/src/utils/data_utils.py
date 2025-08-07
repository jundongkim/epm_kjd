"""
DX-AI Manufacturing Copilot - 데이터 유틸리티

데이터 관리 및 공통 유틸리티 함수들
"""

import os
import glob
import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple


class DataFileManager:
    """데이터 파일 관리자"""
    
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
    
    def get_all_files(self, data_type_filter: Optional[str] = None) -> List[Tuple[str, str]]:
        """모든 데이터 파일 조회"""
        all_files = []
        
        # 생산 데이터 파일
        production_dir = os.path.join(self.data_dir, "production")
        if os.path.exists(production_dir):
            production_files = glob.glob(os.path.join(production_dir, "*.csv"))
            for filepath in production_files:
                all_files.append((filepath, "🏭 생산 데이터"))
        
        # 실험 데이터 파일
        experimental_dir = os.path.join(self.data_dir, "experimental")
        if os.path.exists(experimental_dir):
            experimental_files = glob.glob(os.path.join(experimental_dir, "*.csv"))
            for filepath in experimental_files:
                all_files.append((filepath, "🧪 실험 데이터"))
        
        # 원가 데이터 파일
        cost_production_dir = os.path.join(self.data_dir, "cost_production")
        if os.path.exists(cost_production_dir):
            cost_files = glob.glob(os.path.join(cost_production_dir, "*.csv"))
            for filepath in cost_files:
                all_files.append((filepath, "💰 원가 데이터"))
        
        # 최신 파일 순으로 정렬
        all_files.sort(key=lambda x: os.path.getmtime(x[0]), reverse=True)
        
        # 데이터 타입 필터링
        if data_type_filter:
            all_files = [(filepath, data_type) for filepath, data_type in all_files if data_type_filter in data_type]
        
        return all_files
    
    def get_file_info(self, filepath: str) -> Dict[str, Any]:
        """파일 정보 조회"""
        try:
            file_stat = os.stat(filepath)
            file_size = file_stat.st_size / 1024  # KB 단위
            create_time = datetime.fromtimestamp(file_stat.st_mtime)
            
            # 파일 내용 미리보기
            try:
                df = pd.read_csv(filepath)
                row_count = len(df)
                col_count = len(df.columns)
                preview_data = df.head(3)
            except Exception:
                row_count = 0
                col_count = 0
                preview_data = None
            
            return {
                "filename": os.path.basename(filepath),
                "filepath": filepath,
                "file_size_kb": file_size,
                "create_time": create_time,
                "row_count": row_count,
                "col_count": col_count,
                "preview_data": preview_data
            }
        except Exception as e:
            return {
                "filename": os.path.basename(filepath),
                "filepath": filepath,
                "error": str(e)
            }
    
    def get_data_statistics(self, data_type_filter: Optional[str] = None) -> Dict[str, Any]:
        """데이터 통계 정보 조회"""
        all_files = self.get_all_files(data_type_filter)
        
        stats = {
            "total_files": len(all_files),
            "total_size_mb": 0,
            "production_count": 0,
            "experimental_count": 0,
            "cost_production_count": 0,
            "latest_file": None,
            "date_counts": {}
        }
        
        if not all_files:
            return stats
        
        # 파일 통계 계산
        for filepath, data_type in all_files:
            file_size = os.path.getsize(filepath) / 1024 / 1024  # MB
            stats["total_size_mb"] += file_size
            
            if "생산" in data_type:
                stats["production_count"] += 1
            elif "실험" in data_type:
                stats["experimental_count"] += 1
            elif "원가" in data_type:
                stats["cost_production_count"] += 1
            
            # 날짜별 카운트
            create_time = datetime.fromtimestamp(os.path.getmtime(filepath))
            date_str = create_time.strftime('%Y-%m-%d')
            stats["date_counts"][date_str] = stats["date_counts"].get(date_str, 0) + 1
        
        # 최신 파일 정보
        if all_files:
            latest_filepath = all_files[0][0]
            stats["latest_file"] = {
                "filename": os.path.basename(latest_filepath),
                "create_time": datetime.fromtimestamp(os.path.getmtime(latest_filepath))
            }
        
        stats["total_size_mb"] = round(stats["total_size_mb"], 1)
        
        return stats
    
    def read_file_content(self, filepath: str) -> str:
        """파일 내용 읽기"""
        try:
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                return f.read()
        except Exception as e:
            return f"파일 읽기 오류: {str(e)}"
    
    def delete_file(self, filepath: str) -> bool:
        """파일 삭제"""
        try:
            os.remove(filepath)
            return True
        except Exception as e:
            print(f"파일 삭제 오류: {str(e)}")
            return False


class DataValidator:
    """데이터 유효성 검사기"""
    
    @staticmethod
    def validate_production_data(data: pd.DataFrame) -> Dict[str, Any]:
        """생산 데이터 유효성 검사"""
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "statistics": {}
        }
        
        required_columns = ["Lot_ID", "Equipment_ID", "Work_Date", "Work_Time", "Purity_%", "Yield_%"]
        
        # 필수 컬럼 확인
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            validation_result["is_valid"] = False
            validation_result["errors"].append(f"필수 컬럼 누락: {missing_columns}")
        
        # 데이터 범위 확인
        if "Purity_%" in data.columns:
            purity_stats = data["Purity_%"].describe()
            validation_result["statistics"]["purity"] = purity_stats
            
            if purity_stats['min'] < 80 or purity_stats['max'] > 100:
                validation_result["warnings"].append("순도 값이 예상 범위(80-100%)를 벗어남")
        
        if "Yield_%" in data.columns:
            yield_stats = data["Yield_%"].describe()
            validation_result["statistics"]["yield"] = yield_stats
            
            if yield_stats['min'] < 70 or yield_stats['max'] > 100:
                validation_result["warnings"].append("수율 값이 예상 범위(70-100%)를 벗어남")
        
        # 중복 데이터 확인
        if "Lot_ID" in data.columns:
            duplicate_lots = data["Lot_ID"].duplicated().sum()
            if duplicate_lots > 0:
                validation_result["warnings"].append(f"중복된 Lot ID: {duplicate_lots}개")
        
        return validation_result
    
    @staticmethod
    def validate_experimental_data(data: pd.DataFrame) -> Dict[str, Any]:
        """실험 데이터 유효성 검사"""
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "statistics": {}
        }
        
        required_columns = ["Run", "Purity_%", "Yield_%"]
        
        # 필수 컬럼 확인
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            validation_result["is_valid"] = False
            validation_result["errors"].append(f"필수 컬럼 누락: {missing_columns}")
        
        # 실험 번호 연속성 확인
        if "Run" in data.columns:
            run_numbers = sorted(data["Run"].unique())
            expected_runs = list(range(1, len(run_numbers) + 1))
            if run_numbers != expected_runs:
                validation_result["warnings"].append("실험 번호가 연속되지 않음")
        
        # 응답 변수 통계
        response_variables = ["Purity_%", "Yield_%", "Reaction_Time_min", "Byproduct_ppm", "Energy_kWh"]
        for var in response_variables:
            if var in data.columns:
                validation_result["statistics"][var] = data[var].describe()
        
        return validation_result
    
    @staticmethod
    def validate_cost_production_data(data: pd.DataFrame) -> Dict[str, Any]:
        """원가/생산 이력 데이터 유효성 검사"""
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "statistics": {}
        }
        
        required_columns = ["lot_number", "timestamp", "material_cost", "utility_cost", "total_cost"]
        
        # 필수 컬럼 확인
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            validation_result["is_valid"] = False
            validation_result["errors"].append(f"필수 컬럼 누락: {missing_columns}")
        
        # 비용 데이터 일관성 확인
        if all(col in data.columns for col in ["material_cost", "utility_cost", "total_cost"]):
            calculated_total = data["material_cost"] + data["utility_cost"]
            cost_difference = abs(calculated_total - data["total_cost"])
            
            if cost_difference.max() > 1:  # 1원 이상 차이
                validation_result["warnings"].append("총 비용 계산에 불일치가 있음")
        
        # 비용 통계
        cost_columns = ["material_cost", "utility_cost", "total_cost"]
        for col in cost_columns:
            if col in data.columns:
                validation_result["statistics"][col] = data[col].describe()
        
        return validation_result


class DataConverter:
    """데이터 변환기"""
    
    @staticmethod
    def convert_to_cost_format(data: pd.DataFrame) -> pd.DataFrame:
        """원가 관리 시스템 형식으로 변환"""
        # 원가 관리 시스템에서 요구하는 형식으로 변환
        converted_data = data.copy()
        
        # 컬럼명 매핑
        column_mapping = {
            "Lot_ID": "lot_number",
            "Work_Time": "timestamp",
            "Purity_%": "purity",
            "Yield_%": "yield",
            "Temperature_C": "temperature",
            "Pressure_bar": "pressure"
        }
        
        for old_name, new_name in column_mapping.items():
            if old_name in converted_data.columns:
                converted_data.rename(columns={old_name: new_name}, inplace=True)
        
        return converted_data
    
    @staticmethod
    def convert_to_ml_format(data: pd.DataFrame) -> pd.DataFrame:
        """머신러닝 모델 입력 형식으로 변환"""
        # 숫자형 컬럼만 선택하고 결측값 처리
        numeric_columns = data.select_dtypes(include=[np.number]).columns
        ml_data = data[numeric_columns].copy()
        
        # 결측값 처리
        ml_data = ml_data.fillna(ml_data.mean())
        
        return ml_data
    
    @staticmethod
    def aggregate_daily_data(data: pd.DataFrame, date_column: str) -> pd.DataFrame:
        """일별 데이터 집계"""
        if date_column not in data.columns:
            raise ValueError(f"날짜 컬럼 '{date_column}'이 존재하지 않음")
        
        # 날짜 컬럼을 datetime으로 변환
        data[date_column] = pd.to_datetime(data[date_column])
        data['date'] = data[date_column].dt.date
        
        # 숫자형 컬럼 집계
        numeric_columns = data.select_dtypes(include=[np.number]).columns
        aggregated_data = data.groupby('date')[numeric_columns].agg(['mean', 'std', 'count'])
        
        return aggregated_data


def get_available_data_files(data_type: str = "all") -> List[Dict[str, Any]]:
    """사용 가능한 데이터 파일 목록 조회"""
    file_manager = DataFileManager()
    
    if data_type == "all":
        files = file_manager.get_all_files()
    elif data_type == "production":
        files = file_manager.get_all_files("생산")
    elif data_type == "experimental":
        files = file_manager.get_all_files("실험")
    elif data_type == "cost_production":
        files = file_manager.get_all_files("원가")
    else:
        files = []
    
    file_info_list = []
    for filepath, data_type in files:
        file_info = file_manager.get_file_info(filepath)
        file_info["data_type"] = data_type
        file_info_list.append(file_info)
    
    return file_info_list


def load_data_file(filepath: str, validate: bool = True) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """데이터 파일 로드 및 검증"""
    try:
        data = pd.read_csv(filepath)
        
        result = {
            "success": True,
            "message": "데이터 로드 성공",
            "validation_result": None
        }
        
        if validate:
            # 데이터 타입에 따른 유효성 검사
            if "production" in filepath.lower():
                result["validation_result"] = DataValidator.validate_production_data(data)
            elif "experimental" in filepath.lower():
                result["validation_result"] = DataValidator.validate_experimental_data(data)
            elif "cost" in filepath.lower():
                result["validation_result"] = DataValidator.validate_cost_production_data(data)
        
        return data, result
        
    except Exception as e:
        result = {
            "success": False,
            "message": f"데이터 로드 실패: {str(e)}",
            "validation_result": None
        }
        return pd.DataFrame(), result


def get_data_summary(data: pd.DataFrame) -> Dict[str, Any]:
    """데이터 요약 정보 생성"""
    summary = {
        "shape": data.shape,
        "columns": list(data.columns),
        "dtypes": data.dtypes.to_dict(),
        "missing_values": data.isnull().sum().to_dict(),
        "numeric_summary": {},
        "categorical_summary": {}
    }
    
    # 숫자형 컬럼 요약
    numeric_columns = data.select_dtypes(include=[np.number]).columns
    for col in numeric_columns:
        summary["numeric_summary"][col] = {
            "mean": data[col].mean(),
            "std": data[col].std(),
            "min": data[col].min(),
            "max": data[col].max(),
            "median": data[col].median()
        }
    
    # 범주형 컬럼 요약
    categorical_columns = data.select_dtypes(include=['object']).columns
    for col in categorical_columns:
        summary["categorical_summary"][col] = {
            "unique_count": data[col].nunique(),
            "most_common": data[col].mode().iloc[0] if not data[col].mode().empty else None,
            "value_counts": data[col].value_counts().head(5).to_dict()
        }
    
    return summary 