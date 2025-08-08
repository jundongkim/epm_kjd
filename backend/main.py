"""
DX-AI Manufacturing Copilot - FastAPI Backend

스마트 제조 공정 관리를 위한 AI 솔루션 백엔드 API
"""

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn
import logging
import os
import glob
import json
import pandas as pd
import numpy as np
import io
from pathlib import Path
from datetime import datetime, timedelta

# .env 파일 로드
from dotenv import load_dotenv
load_dotenv()  # .env 파일의 환경변수를 자동으로 로드

# 프로젝트 모듈 import
from src.copilot.data_generation_engine import DataGenerationEngine
from src.copilot.process_management_engine import ProcessManagementEngine  
from src.copilot.product_data_analysis_engine import ProductDataAnalysisEngine
from src.copilot.experimental_design_engine import ExperimentalDesignEngine
from src.copilot.cost_management_engine import CostManagementEngine
from src.copilot.cost_optimization_engine import CostOptimizationEngine
# AI 보고서 생성기 제거됨
# from src.ai.core.ai_report_generator import AIReportGenerator
from src.copilot.advanced_optimization import AdvancedOptimizationEngine
# from src.copilot.config import settings
# LLM Client는 이제 AI 모듈에서 import  
# from src.ai.core.llm_client import OllamaClient

# 챗봇 라우터 import
from routers import chatbot
from routers import experimental_design
from routers import workflow
from routers import dify_agent
from routers import product_modeling
from routers import chart_analysis
from routers import analysis
from routers import aiadvisor

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title="DX-AI Manufacturing Copilot API",
    description="스마트 제조 공정 관리를 위한 AI 솔루션 백엔드 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 챗봇 라우터 등록
app.include_router(chatbot.router, prefix="/api/v1/chatbot", tags=["chatbot"])
app.include_router(experimental_design.router, prefix="/api/v1")
app.include_router(workflow.router, prefix="/api/v1", tags=["workflow"])
app.include_router(dify_agent.router, prefix="/api/v1", tags=["dify-agent"])
app.include_router(product_modeling.router, prefix="/api/v1", tags=["product-modeling"])
app.include_router(chart_analysis.router, prefix="/api/v1", tags=["chart-analysis"])
app.include_router(analysis.router, tags=["analysis"])
app.include_router(aiadvisor.router, prefix="/api/v1", tags=["ai-advisor"])

# 정적 파일 서빙 제거 (Frontend에서 처리)

# 엔진 인스턴스들
engines = {}

@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작시 엔진들 초기화"""
    try:
        logger.info("🚀 엔진들을 초기화하는 중...")
        
        # ML 라이브러리 상태 확인
        try:
            from src.ml_models.error_handler import print_library_status, install_missing_libraries
            print_library_status()
            install_missing_libraries()
        except ImportError:
            logger.warning("⚠️ ML 라이브러리 에러 핸들러를 로드할 수 없습니다.")
        
        # 필수 디렉토리 생성
        import os
        from pathlib import Path
        
        required_dirs = [
            "data/generated/production",
            "data/generated/sensor", 
            "data/generated/experimental",
            "data/generated/cost_production",
            "logs",
            "temp",
            "fonts"
        ]
        
        for dir_path in required_dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
        
        logger.info("📁 필수 디렉토리 생성 완료")
        
        # 기본 엔진들 (의존성 없음) - 안전한 초기화
        engine_init_success = {}
        
        try:
            engines["data_generation"] = DataGenerationEngine()
            engine_init_success["data_generation"] = True
            logger.info("✅ 데이터 생성 엔진 초기화 완료")
        except Exception as e:
            logger.error(f"❌ 데이터 생성 엔진 초기화 실패: {e}")
            engine_init_success["data_generation"] = False
        
        try:
            engines["process_management"] = ProcessManagementEngine()
            engine_init_success["process_management"] = True
            logger.info("✅ 프로세스 관리 엔진 초기화 완료")
        except Exception as e:
            logger.error(f"❌ 프로세스 관리 엔진 초기화 실패: {e}")
            engine_init_success["process_management"] = False
        
        try:
            engines["product_analysis"] = ProductDataAnalysisEngine()
            engine_init_success["product_analysis"] = True
            logger.info("✅ 제품 분석 엔진 초기화 완료")
        except Exception as e:
            logger.error(f"❌ 제품 분석 엔진 초기화 실패: {e}")
            engine_init_success["product_analysis"] = False
        
        try:
            engines["experimental_design"] = ExperimentalDesignEngine()
            engine_init_success["experimental_design"] = True
            logger.info("✅ 실험 설계 엔진 초기화 완료")
        except Exception as e:
            logger.error(f"❌ 실험 설계 엔진 초기화 실패: {e}")
            engine_init_success["experimental_design"] = False
        
        try:
            engines["cost_management"] = CostManagementEngine()
            engine_init_success["cost_management"] = True
            logger.info("✅ 원가 관리 엔진 초기화 완료")
        except Exception as e:
            logger.error(f"❌ 원가 관리 엔진 초기화 실패: {e}")
            engine_init_success["cost_management"] = False
        
        # 의존성이 있는 엔진들 - 안전한 초기화
        try:
            engines["cost_optimization"] = CostOptimizationEngine()
            engine_init_success["cost_optimization"] = True
            logger.info("✅ 원가 최적화 엔진 초기화 완료")
        except Exception as e:
            logger.error(f"❌ 원가 최적화 엔진 초기화 실패: {e}")
            engine_init_success["cost_optimization"] = False
        
        # AI 보고서 생성 엔진 제거됨
        # try:
        #     engines["ai_report"] = AIReportGenerator(llm_client=None)
        #     engine_init_success["ai_report"] = True
        #     logger.info("✅ AI 보고서 생성 엔진 초기화 완료")
        # except Exception as e:
        #     logger.error(f"❌ AI 보고서 생성 엔진 초기화 실패: {e}")
        #     engine_init_success["ai_report"] = False
        
        try:
            if engine_init_success.get("cost_optimization", False):
                engines["advanced_optimization"] = AdvancedOptimizationEngine(
                    cost_engine=engines["cost_optimization"]
                )
                engine_init_success["advanced_optimization"] = True
                logger.info("✅ 고급 최적화 엔진 초기화 완료")
            else:
                logger.warning("⚠️ 원가 최적화 엔진 오류로 고급 최적화 엔진을 건너뜁니다.")
                engine_init_success["advanced_optimization"] = False
        except Exception as e:
            logger.error(f"❌ 고급 최적화 엔진 초기화 실패: {e}")
            engine_init_success["advanced_optimization"] = False
        
        # 초기화 결과 요약
        success_count = sum(engine_init_success.values())
        total_count = len(engine_init_success)
        
        logger.info(f"🎯 엔진 초기화 완료: {success_count}/{total_count}개 성공")
        
        if success_count == total_count:
            logger.info("🎉 모든 엔진이 성공적으로 초기화되었습니다!")
        else:
            logger.warning(f"⚠️ 일부 엔진 초기화 실패. 기본 기능은 사용 가능합니다.")
            
        # 실패한 엔진들 나열
        failed_engines = [name for name, success in engine_init_success.items() if not success]
        if failed_engines:
            logger.warning(f"❌ 실패한 엔진들: {', '.join(failed_engines)}")
            
    except Exception as e:
        logger.error(f"💥 엔진 초기화 중 심각한 오류 발생: {e}")
        import traceback
        logger.error(traceback.format_exc())
        logger.info("🔄 기본 모드로 계속 실행합니다...")

# Pydantic 모델들
class HealthResponse(BaseModel):
    status: str
    message: str
    engines_status: Dict[str, str]

class DataGenerationRequest(BaseModel):
    dataType: str
    config: Dict[str, Any]

class ProcessAnalysisRequest(BaseModel):
    process_data: Dict[str, Any]
    analysis_type: str = "performance"

class ExperimentRequest(BaseModel):
    factors: List[Dict[str, Any]]
    responses: List[str]
    design_type: str = "factorial"

class CostAnalysisRequest(BaseModel):
    cost_data: Dict[str, Any]
    analysis_type: str = "basic"

# API 엔드포인트들

@app.get("/", response_model=HealthResponse)
async def root():
    """API 상태 확인"""
    engine_status = {}
    for name, engine in engines.items():
        try:
            # 간단한 상태 확인
            engine_status[name] = "healthy"
        except:
            engine_status[name] = "error"
    
    return HealthResponse(
        status="healthy",
        message="DX-AI Manufacturing Copilot API is running",
        engines_status=engine_status
    )

@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {"status": "healthy", "message": "API is running normally"}

# 데이터 생성 엔드포인트들
@app.post("/api/data/generate")
async def generate_data(request: DataGenerationRequest):
    """데이터 생성"""
    try:
        # 데이터 생성 및 저장
        if request.dataType == "production":
            # 기존 데이터 생성 엔진 사용
            from src.copilot.data_generation_engine import ProductionDataGenerator
            prod_generator = ProductionDataGenerator()
            
            # 설정 파라미터 변환
            lot_count = request.config.get('lotCount', 100)
            equipment_count = request.config.get('equipmentCount', 10)
            
            # 날짜 파라미터 변환
            work_date_start = datetime.strptime(request.config.get('workDateStart', '2024-01-01'), '%Y-%m-%d')
            work_date_end = datetime.strptime(request.config.get('workDateEnd', '2024-12-31'), '%Y-%m-%d')
            
            shift_config = {
                "shift_type": request.config.get('shiftType', '주간(08:00-16:00)')
            }
            
            purity_range = tuple(request.config.get('purityRange', [95.0, 98.5]))
            yield_range = tuple(request.config.get('yieldRange', [85.0, 95.0]))
            
            # 생산 데이터 생성
            df = prod_generator.generate_production_data(
                lot_count=lot_count,
                equipment_count=equipment_count,
                work_date_start=work_date_start,
                work_date_end=work_date_end,
                shift_config=shift_config,
                purity_range=purity_range,
                yield_range=yield_range,
                add_noise=request.config.get('addNoise', True),
                noise_level=request.config.get('noiseLevel', 1.0),
                add_anomalies=request.config.get('addAnomalies', False),
                anomaly_ratio=request.config.get('anomalyRatio', 3)
            )
            
            # 파일 저장
            filepath = prod_generator.save_production_data(df, lot_count)
            filename = os.path.basename(filepath)
            data = df.to_dict('records')
        elif request.dataType == "sensor":
            # 센서 데이터 생성 엔진 사용
            from src.copilot.data_generation_engine import SensorDataGenerator
            sensor_generator = SensorDataGenerator()
            
            # 설정 파라미터 변환 - 타입 안전성 보장
            try:
                data_count = int(request.config.get('dataCount', 15000))
            except (ValueError, TypeError):
                print(f"WARNING - Invalid dataCount type, using default 15000")
                data_count = 15000
            
            selected_equipment = str(request.config.get('selectedEquipment', 'dryer'))
            selected_sensors = list(request.config.get('selectedSensors', ['outlet_humidity', 'inlet_humidity', 'drying_temperature']))
            collection_interval = str(request.config.get('collectionInterval', '10초'))
            
            # 디버깅을 위한 로그 출력
            print(f"DEBUG - Raw request.config type: {type(request.config)}")
            print(f"DEBUG - Raw request.config: {request.config}")
            print(f"DEBUG - data_count from config: {data_count}")
            print(f"DEBUG - data_count type: {type(data_count)}")
            print(f"DEBUG - selected_equipment: {selected_equipment}")
            print(f"DEBUG - selected_sensors: {selected_sensors}")
            print(f"DEBUG - collection_interval: {collection_interval}")
            
            # dataCount 범위 검증 (1~100,000개)
            if data_count < 1:
                print(f"WARNING - data_count {data_count} is below minimum, using 1")
                data_count = 1
            elif data_count > 100000:
                print(f"WARNING - data_count {data_count} is above maximum, using 100000")
                data_count = 100000
            
            # 날짜 파라미터 변환 - 안전한 타입 변환
            try:
                work_date_start_str = str(request.config.get('workDateStart', '2024-01-01'))
                work_date_start = datetime.strptime(work_date_start_str, '%Y-%m-%d')
            except (ValueError, TypeError) as e:
                print(f"WARNING - Invalid workDateStart format: {e}, using default")
                work_date_start = datetime.strptime('2024-01-01', '%Y-%m-%d')
            
            try:
                work_date_end_str = str(request.config.get('workDateEnd', '2024-12-31'))
                work_date_end = datetime.strptime(work_date_end_str, '%Y-%m-%d')
            except (ValueError, TypeError) as e:
                print(f"WARNING - Invalid workDateEnd format: {e}, using default")
                work_date_end = datetime.strptime('2024-12-31', '%Y-%m-%d')
            
            shift_config = {
                "shift_type": request.config.get('shiftType', '주간(08:00-16:00)')
            }
            
            # 사용자 정의 시간 파싱 - 안전한 타입 변환
            if shift_config["shift_type"] == "사용자 정의":
                try:
                    custom_start = request.config.get('customShiftStart')
                    if custom_start:
                        custom_start_str = str(custom_start)
                        shift_config["start_hour"] = int(custom_start_str.split(':')[0])
                    else:
                        shift_config["start_hour"] = 8
                        
                    custom_end = request.config.get('customShiftEnd')
                    if custom_end:
                        custom_end_str = str(custom_end)
                        shift_config["end_hour"] = int(custom_end_str.split(':')[0])
                    else:
                        shift_config["end_hour"] = 16
                except (ValueError, AttributeError, TypeError, IndexError) as e:
                    print(f"WARNING - Invalid custom shift time: {e}, using default")
                    shift_config["start_hour"] = 8
                    shift_config["end_hour"] = 16
            
            # 센서별 범위 설정 - 안전한 타입 변환
            raw_sensor_ranges = request.config.get('sensorRanges', {})
            sensor_ranges = {}
            
            # 각 센서 범위를 안전하게 float로 변환
            for sensor_key, range_value in raw_sensor_ranges.items():
                try:
                    if isinstance(range_value, (list, tuple)) and len(range_value) == 2:
                        min_val = float(range_value[0])
                        max_val = float(range_value[1])
                        sensor_ranges[sensor_key] = [min_val, max_val]
                    else:
                        print(f"WARNING - Invalid range format for sensor {sensor_key}: {range_value}")
                except (ValueError, TypeError, IndexError) as e:
                    print(f"WARNING - Failed to convert sensor range for {sensor_key}: {e}")
            
            print(f"DEBUG - Converted sensor_ranges: {sensor_ranges}")
            
            # 부가 설정 파라미터 안전 변환
            try:
                add_noise = bool(request.config.get('addNoise', True))
            except (ValueError, TypeError):
                add_noise = True
                
            try:
                noise_level = float(request.config.get('noiseLevel', 1.0))
            except (ValueError, TypeError):
                noise_level = 1.0
                
            try:
                add_anomalies = bool(request.config.get('addAnomalies', False))
            except (ValueError, TypeError):
                add_anomalies = False
                
            try:
                anomaly_ratio = int(request.config.get('anomalyRatio', 3))
            except (ValueError, TypeError):
                anomaly_ratio = 3
            
            try:
                add_missing_data = bool(request.config.get('addMissingData', False))
            except (ValueError, TypeError):
                add_missing_data = False
                
            try:
                missing_data_ratio = int(request.config.get('missingDataRatio', 5))
            except (ValueError, TypeError):
                missing_data_ratio = 5
            
            try:
                data_pattern = str(request.config.get('dataPattern', '정상'))
            except (ValueError, TypeError):
                data_pattern = '정상'
                
            try:
                variation_intensity = int(request.config.get('variationIntensity', 3))
                print(f"DEBUG - Received variationIntensity: {request.config.get('variationIntensity')} -> converted to: {variation_intensity}")
            except (ValueError, TypeError):
                variation_intensity = 3
                print(f"DEBUG - Failed to convert variationIntensity, using default: {variation_intensity}")
            
            print(f"DEBUG - Final parameters: noise={add_noise}, noise_level={noise_level}, anomalies={add_anomalies}, anomaly_ratio={anomaly_ratio}, missing_data={add_missing_data}, missing_ratio={missing_data_ratio}, pattern='{data_pattern}', variation_intensity={variation_intensity}")
            
            # 센서 데이터 생성 (간격 방식으로 통일)
            df = sensor_generator.generate_sensor_data_by_interval(
                lot_count=data_count,
                selected_sensors=selected_sensors,
                work_date_start=work_date_start,
                work_date_end=work_date_end,
                shift_config=shift_config,
                sensor_ranges=sensor_ranges,
                collection_interval=collection_interval,
                add_noise=add_noise,
                noise_level=noise_level,
                add_anomalies=add_anomalies,
                anomaly_ratio=anomaly_ratio,
                add_missing_data=add_missing_data,
                missing_data_ratio=missing_data_ratio,
                data_pattern=data_pattern,
                variation_intensity=variation_intensity
            )
            
            # 디버깅을 위한 로그 출력 (대용량 데이터 고려)
            print(f"DEBUG - Generated DataFrame shape: {df.shape}")
            print(f"DEBUG - DataFrame columns: {list(df.columns)}")
            print(f"DEBUG - DataFrame dtypes: {df.dtypes.to_dict()}")
            
            # 타임스탬프 컬럼 안전성 검증
            if 'timestamp' in df.columns:
                first_timestamp = df['timestamp'].iloc[0] if len(df) > 0 else ""
                print(f"DEBUG - First timestamp: '{first_timestamp}' (length: {len(str(first_timestamp))})")
                if len(str(first_timestamp)) > 30:
                    print(f"ERROR - Timestamp appears to be concatenated in DataFrame")
                    raise Exception("DataFrame에서 타임스탬프가 연결된 상태입니다")
                
                # 대용량 데이터의 경우 처음과 마지막 타임스탬프만 추가 확인
                if len(df) > 10000:
                    last_timestamp = df['timestamp'].iloc[-1]
                    print(f"DEBUG - Last timestamp (large dataset): '{last_timestamp}'")
            
            # 파일 저장
            filepath = sensor_generator.save_sensor_data(df, data_count)
            filename = os.path.basename(filepath)
            
            # 안전한 딕셔너리 변환
            try:
                # DataFrame을 딕셔너리로 변환 전 타임스탬프 확인
                df_copy = df.copy()
                if 'timestamp' in df_copy.columns:
                    # 타임스탬프 컬럼을 명시적으로 문자열로 변환
                    df_copy['timestamp'] = df_copy['timestamp'].astype(str)
                    # 대용량 데이터 고려하여 샘플만 출력
                    sample_timestamps = df_copy['timestamp'].head(3).tolist()
                    print(f"DEBUG - Sample converted timestamps: {sample_timestamps}")
                
                print(f"DEBUG - Converting DataFrame to records...")
                data = df_copy.to_dict('records')
                print(f"DEBUG - Successfully converted to {len(data)} records")
                
                # 첫 번째 레코드의 타임스탬프 확인
                if data and 'timestamp' in data[0]:
                    first_record_timestamp = data[0]['timestamp']
                    print(f"DEBUG - First record timestamp: '{first_record_timestamp}' (length: {len(str(first_record_timestamp))})")
                    if len(str(first_record_timestamp)) > 30:
                        raise Exception("레코드 변환 후에도 타임스탬프가 연결된 상태입니다")
                    
                    # 대용량 데이터의 경우 마지막 레코드도 확인
                    if len(data) > 10000:
                        last_record_timestamp = data[-1]['timestamp']
                        print(f"DEBUG - Last record timestamp (large dataset): '{last_record_timestamp}'")
                        
            except Exception as dict_error:
                print(f"ERROR - Failed to convert DataFrame to dict: {dict_error}")
                raise Exception(f"센서 데이터 딕셔너리 변환 실패: {str(dict_error)}")
        elif request.dataType == "experimental":
            # 기존 실험 데이터 생성 엔진 사용
            from src.copilot.data_generation_engine import ExperimentalDataGenerator
            exp_generator = ExperimentalDataGenerator()
            
            # 실험 설정 변환
            experiment_config = {
                "experiment_type": request.config.get('experimentType', 'Full Factorial'),
                "selected_factors": request.config.get('selectedFactors', ['온도', '압력', 'pH']),
                "levels": request.config.get('levels', 3),
                "replications": request.config.get('replications', 2),
                "num_experiments": request.config.get('numExperiments', 25)
            }
            
            factor_ranges = request.config.get('factorRanges', {
                "온도": (150, 200),
                "압력": (1.5, 3.0),
                "pH": (6.5, 8.5)
            })
            
            experiment_schedule = {
                "experiment_date_start": datetime.strptime(request.config.get('experimentDateStart', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d'),
                "experiment_date_end": datetime.strptime(request.config.get('experimentDateEnd', (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')), '%Y-%m-%d'),
                "experiment_shift_type": request.config.get('experimentShiftType', '일반 실험시간(09:00-17:00)'),
                "experiment_interval": request.config.get('experimentInterval', '동시 수행')
            }
            
            metadata = {
                "experimenter": request.config.get('experimenter', '연구원A'),
                "experiment_purpose": request.config.get('experimentPurpose', '공정 조건 최적화'),
                "experiment_objective": request.config.get('experimentObjective', '순도 최대화')
            }
            
            # 실험 데이터 생성
            df = exp_generator.generate_experimental_data(
                experiment_config=experiment_config,
                factor_ranges=factor_ranges,
                experiment_schedule=experiment_schedule,
                metadata=metadata
            )
            
            # 파일 저장
            filepath = exp_generator.save_experimental_data(df, experiment_config["experiment_type"])
            filename = os.path.basename(filepath)
            data = df.to_dict('records')
        elif request.dataType == "cost_production":
            # 기존 원가 데이터 생성 엔진 사용
            from src.copilot.data_generation_engine import CostProductionDataGenerator
            cost_generator = CostProductionDataGenerator()
            
            # 설정 파라미터 변환 및 기본값 설정
            cost_config = {
                'record_count': request.config.get('recordCount', 100),
                'start_date': request.config.get('startDate', '2024-01-01'),
                'end_date': request.config.get('endDate', '2024-12-31'),
                
                # 원료 투입량 범위
                'material_a_range': tuple(request.config.get('materialARange', [100, 500])),
                'material_b_range': tuple(request.config.get('materialBRange', [50, 200])),
                'catalyst_range': tuple(request.config.get('catalystRange', [5, 20])),
                
                # 운전 조건 범위
                'temp_range': tuple(request.config.get('tempRange', [150, 200])),
                'pressure_range': tuple(request.config.get('pressureRange', [1.5, 3.0])),
                'flow_range': tuple(request.config.get('flowRange', [180, 220])),
                
                # 유틸리티 사용량 범위
                'steam_range': tuple(request.config.get('steamRange', [500, 800])),
                'electricity_range': tuple(request.config.get('electricityRange', [200, 400])),
                'cooling_range': tuple(request.config.get('coolingRange', [300, 600])),
                
                # 단가 정보
                'material_a_cost': request.config.get('materialACost', 1000),
                'material_b_cost': request.config.get('materialBCost', 1500),
                'catalyst_cost': request.config.get('catalystCost', 5000),
                'steam_cost': request.config.get('steamCost', 150),
                'electricity_cost': request.config.get('electricityCost', 120),
                'cooling_cost': request.config.get('coolingCost', 80),
                
                # 변동성 설정
                'price_volatility': request.config.get('priceVolatility', 5.0),
                'utility_volatility': request.config.get('utilityVolatility', 3.0),
                
                # 품질 지표 범위
                'purity_range': tuple(request.config.get('purityRange', [95.0, 98.5])),
                'yield_range': tuple(request.config.get('yieldRange', [85.0, 95.0])),
                
                # 상관관계 및 노이즈
                'correlation_strength': request.config.get('correlationStrength', 0.3),
                'noise_level': request.config.get('noiseLevel', 1.0),
                
                # 시장 변동성 옵션
                'seasonal_effect': request.config.get('seasonalEffect', False),
                'include_shifts': request.config.get('includeShifts', False),
                'include_equipment_wear': request.config.get('includeEquipmentWear', False)
            }
            
            # 원가 데이터 생성
            df = cost_generator.generate_cost_production_data(cost_config)
            
            # 파일 저장
            filepath = cost_generator.save_cost_production_data(df)
            filename = os.path.basename(filepath)
            data = df.to_dict('records')
        else:
            raise HTTPException(status_code=400, detail=f"Unknown data type: {request.dataType}")
        
        # 디버깅: 실제 생성된 데이터 확인
        print(f"DEBUG - Final DataFrame info before response:")
        print(f"DEBUG - Shape: {df.shape}")
        print(f"DEBUG - Total records: {len(df)}")
        print(f"DEBUG - Request data type: {request.dataType}")
        
        # 요약 통계 계산
        summary = calculate_summary_stats(df, request.dataType)
        
        # 데이터 타입별 미리보기 데이터 선택
        preview_data = get_preview_data(df, request.dataType)
        
        # numpy 타입을 Python 기본 타입으로 변환
        preview_data = convert_numpy_types(preview_data)
        summary = convert_numpy_types(summary)
        
        # 디버깅: 응답 데이터 확인
        print(f"DEBUG - Preview data length: {len(preview_data)}")
        print(f"DEBUG - Total data length: {len(data)}")
        print(f"DEBUG - Summary total records: {summary.get('totalRecords', 'N/A')}")
        print(f"DEBUG - Returning data with {len(data)} records to frontend")
        
        return {
            "success": True,
            "message": f"{request.dataType} 데이터가 성공적으로 생성되었습니다.",
            "filename": filename,
            "data": data,
            "preview": preview_data,
            "summary": summary
        }
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"데이터 생성 오류: {e}")
        logger.error(f"상세 에러 정보:\n{error_details}")
        
        # 더 구체적인 에러 메시지 제공
        if "Could not convert string" in str(e):
            error_msg = f"데이터 타입 변환 오류: {str(e)}. 입력 데이터의 형식을 확인해주세요."
        elif "DataFrame" in str(e):
            error_msg = f"데이터 생성 오류: {str(e)}. 센서 설정을 확인해주세요."
        elif "datetime" in str(e):
            error_msg = f"날짜 형식 오류: {str(e)}. 날짜 형식이 YYYY-MM-DD인지 확인해주세요."
        else:
            error_msg = f"데이터 생성 실패: {str(e)}"
        
        return {
            "success": False,
            "message": error_msg,
            "error_details": str(e)
        }



def convert_numpy_types(obj):
    """numpy 타입을 Python 기본 타입으로 재귀적 변환"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        try:
            return obj.tolist()
        except (AttributeError, TypeError):
            return list(obj) if hasattr(obj, '__iter__') else obj
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif hasattr(obj, 'tolist'):
        try:
            return obj.tolist()
        except (AttributeError, TypeError):
            return obj
    else:
        return obj

def calculate_summary_stats(df, data_type):
    """데이터 타입별 요약 통계 계산"""
    summary = {
        'totalRecords': len(df),
        'dataType': data_type
    }
    
    if data_type == "production":
        # 생산 데이터 전용 통계
        if 'Purity_%' in df.columns:
            summary['averagePurity'] = round(df['Purity_%'].mean(), 2)
            summary['maxPurity'] = round(df['Purity_%'].max(), 2)
            summary['minPurity'] = round(df['Purity_%'].min(), 2)
        
        if 'Yield_%' in df.columns:
            summary['averageYield'] = round(df['Yield_%'].mean(), 2)
            summary['maxYield'] = round(df['Yield_%'].max(), 2)
            summary['minYield'] = round(df['Yield_%'].min(), 2)
        
        if 'Temperature_C' in df.columns:
            summary['averageTemperature'] = round(df['Temperature_C'].mean(), 1)
        
        if 'Pressure_bar' in df.columns:
            summary['averagePressure'] = round(df['Pressure_bar'].mean(), 2)
        
        # 설비별 Lot 개수
        if 'Equipment_ID' in df.columns:
            summary['equipmentCounts'] = df['Equipment_ID'].value_counts().to_dict()
        
        summary['keyColumns'] = ['Lot_ID', 'Equipment_ID', 'Work_Date', 'Purity_%', 'Yield_%', 'Temperature_C', 'Pressure_bar']
        
    elif data_type == "experimental":
        # 실험 데이터 전용 통계
        experiment_cols = [col for col in df.columns if col in ['온도', '압력', 'pH', 'Temperature', 'Pressure']]
        response_cols = [col for col in df.columns if col in ['순도', '수율', 'Purity', 'Yield']]
        
        summary['experimentFactors'] = experiment_cols
        summary['responseVariables'] = response_cols
        
        # 실험 조건별 통계
        for col in experiment_cols:
            if col in df.columns:
                summary[f'average_{col}'] = round(df[col].mean(), 2)
                summary[f'range_{col}'] = [round(df[col].min(), 2), round(df[col].max(), 2)]
        
        # 응답변수별 통계
        for col in response_cols:
            if col in df.columns:
                summary[f'average_{col}'] = round(df[col].mean(), 2)
                summary[f'best_{col}'] = round(df[col].max(), 2)
        
        if 'Run' in df.columns:
            summary['totalRuns'] = df['Run'].nunique()
        
        summary['keyColumns'] = ['Run'] + experiment_cols + response_cols + ['Experiment_Date']
        
    elif data_type == "cost_production":
        # 원가 데이터 전용 통계
        if 'total_cost' in df.columns:
            summary['averageTotalCost'] = round(df['total_cost'].mean(), 0)
            summary['maxTotalCost'] = round(df['total_cost'].max(), 0)
            summary['minTotalCost'] = round(df['total_cost'].min(), 0)
        
        if 'material_cost' in df.columns:
            summary['averageMaterialCost'] = round(df['material_cost'].mean(), 0)
        
        if 'utility_cost' in df.columns:
            summary['averageUtilityCost'] = round(df['utility_cost'].mean(), 0)
        
        if 'purity' in df.columns:
            summary['averagePurity'] = round(df['purity'].mean(), 2)
        
        if 'yield' in df.columns:
            summary['averageYield'] = round(df['yield'].mean(), 2)
        
        if 'production_rate' in df.columns:
            summary['averageProductionRate'] = round(df['production_rate'].mean(), 1)
        
        # 비용 구성비 계산
        if all(col in df.columns for col in ['material_cost', 'utility_cost', 'total_cost']):
            total_material = df['material_cost'].sum()
            total_utility = df['utility_cost'].sum()
            total_cost = df['total_cost'].sum()
            
            summary['costBreakdown'] = {
                'materialRatio': round((total_material / total_cost) * 100, 1),
                'utilityRatio': round((total_utility / total_cost) * 100, 1)
            }
        
        summary['keyColumns'] = ['lot_number', 'timestamp', 'material_a', 'material_b', 'catalyst', 
                               'temperature', 'pressure', 'purity', 'yield', 'total_cost']
                               
    elif data_type == "sensor":
        # 센서 데이터 전용 통계 - timestamp 컬럼 제외
        excluded_columns = ['Lot_ID', 'Work_Date', 'Work_Time', 'Data_Type', 'Generated_At', 'timestamp']
        sensor_columns = [col for col in df.columns if col not in excluded_columns]
        
        # 숫자형 컬럼만 선별 (타임스탬프 관련 오류 방지)
        numeric_sensor_columns = []
        for col in sensor_columns:
            try:
                # 숫자형 변환 가능한지 테스트
                pd.to_numeric(df[col], errors='raise')
                numeric_sensor_columns.append(col)
            except (ValueError, TypeError):
                print(f"DEBUG - Skipping non-numeric column: {col}")
                continue
        
        summary['sensorTypes'] = []
        for col in numeric_sensor_columns:
            try:
                if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
                    column_stats = {
                        'name': col,
                        'average': round(df[col].mean(), 2),
                        'max': round(df[col].max(), 2),
                        'min': round(df[col].min(), 2),
                        'unit': col.split('_')[-1] if '_' in col else ''
                    }
                    summary['sensorTypes'].append(column_stats)
                    
                    # 개별 센서별 평균도 추가
                    summary[f'average_{col}'] = round(df[col].mean(), 2)
            except Exception as col_error:
                print(f"WARNING - Failed to calculate stats for column {col}: {col_error}")
                continue
        
        summary['totalLots'] = len(df)
        summary['totalRecords'] = len(df)
        summary['keyColumns'] = ['timestamp'] + numeric_sensor_columns
    
    return summary

def get_preview_data(df, data_type):
    """데이터 타입별 미리보기 데이터 선택"""
    if data_type == "production":
        # 생산 데이터 주요 컬럼 선택
        key_columns = ['Lot_ID', 'Equipment_ID', 'Work_Date', 'Work_Time', 'Purity_%', 'Yield_%', 'Temperature_C', 'Pressure_bar']
        available_columns = [col for col in key_columns if col in df.columns]
        preview_df = df[available_columns].head(10)
        
    elif data_type == "experimental":
        # 실험 데이터 주요 컬럼 선택
        key_columns = ['Run']
        # 실험 인자들 추가
        factor_columns = [col for col in df.columns if col in ['온도', '압력', 'pH', 'Temperature', 'Pressure', 'Flow_Rate']]
        # 응답 변수들 추가
        response_columns = [col for col in df.columns if col in ['순도', '수율', 'Purity', 'Yield', 'Quality_Score']]
        # 날짜/시간 컬럼 추가
        date_columns = [col for col in df.columns if col in ['Experiment_Date', 'Experiment_Time']]
        
        available_columns = key_columns + factor_columns + response_columns + date_columns
        available_columns = [col for col in available_columns if col in df.columns]
        preview_df = df[available_columns].head(10)
        
    elif data_type == "cost_production":
        # 원가 데이터 주요 컬럼 선택
        key_columns = ['lot_number', 'timestamp', 'material_a', 'material_b', 'catalyst', 
                      'temperature', 'pressure', 'purity', 'yield', 'production_rate',
                      'material_cost', 'utility_cost', 'total_cost']
        available_columns = [col for col in key_columns if col in df.columns]
        preview_df = df[available_columns].head(10)
        
    elif data_type == "sensor":
        # 센서 데이터 주요 컬럼 선택
        key_columns = ['Lot_ID', 'Work_Date', 'Work_Time']
        # 센서 데이터 컬럼들 추가
        sensor_columns = [col for col in df.columns if col not in ['Lot_ID', 'Work_Date', 'Work_Time', 'Data_Type', 'Generated_At']]
        
        available_columns = key_columns + sensor_columns
        available_columns = [col for col in available_columns if col in df.columns]
        preview_df = df[available_columns].head(10)
        
    else:
        # 기본값: 모든 컬럼의 처음 10개 레코드
        preview_df = df.head(10)
    
    return preview_df.to_dict('records')

@app.post("/api/data/generate/lot")
async def generate_lot_numbers(request: dict):
    """생성된 데이터를 8개씩 그룹으로 나누어 LOT 번호 생성"""
    try:
        print(f"DEBUG - LOT 생성 요청 받음: {request}")
        
        filename = request.get('filename')
        if not filename:
            print("ERROR - 파일명이 제공되지 않음")
            raise HTTPException(status_code=400, detail="파일명이 필요합니다")
        
        print(f"DEBUG - 요청된 파일명: {filename}")
        
        # 파일 경로 구성 - 더 많은 디렉토리 검색
        file_path = None
        data_directories = [
            "data/sensor",
            "data/production", 
            "data/experimental",
            "data/cost",
            "data/generated/sensor",
            "data/generated/production", 
            "data/generated/experimental",
            "data/generated/cost_production",
            "backend/data/sensor",
            "backend/data/production",
            "backend/data/experimental", 
            "backend/data/cost",
            "backend/data/generated/sensor",
            "backend/data/generated/production",
            "backend/data/generated/experimental", 
            "backend/data/generated/cost_production",
            "./data/sensor",
            "./data/production",
            "./data/experimental",
            "./data/cost",
            "./data/generated/sensor",
            "./data/generated/production",
            "./data/generated/experimental",
            "./data/generated/cost_production"
        ]
        
        print(f"DEBUG - 검색할 디렉토리들: {data_directories}")
        
        for data_dir in data_directories:
            potential_path = os.path.join(data_dir, filename)
            absolute_path = os.path.abspath(potential_path)
            print(f"DEBUG - 검색 중: {potential_path} (절대경로: {absolute_path}) - 존재: {os.path.exists(potential_path)}")
            if os.path.exists(potential_path):
                file_path = potential_path
                print(f"DEBUG - 파일 발견: {file_path}")
                break
        
        if not file_path:
            print(f"ERROR - 파일을 찾을 수 없음: {filename}")
            # 현재 디렉토리 구조 출력
            current_dir = os.getcwd()
            print(f"DEBUG - 현재 작업 디렉토리: {current_dir}")
            
            # data 디렉토리 구조 상세 출력
            if os.path.exists("data"):
                print("DEBUG - data 디렉토리 내용:")
                for item in os.listdir("data"):
                    item_path = os.path.join("data", item)
                    if os.path.isdir(item_path):
                        print(f"  - {item}/ (디렉토리)")
                        try:
                            for subitem in os.listdir(item_path):
                                subitem_path = os.path.join(item_path, subitem)
                                if os.path.isfile(subitem_path):
                                    print(f"    - {subitem}")
                                elif os.path.isdir(subitem_path):
                                    print(f"    - {subitem}/ (디렉토리)")
                                    try:
                                        for subsubitem in os.listdir(subitem_path):
                                            print(f"      - {subsubitem}")
                                    except:
                                        pass
                        except:
                            print(f"    (접근 불가)")
                    else:
                        print(f"  - {item}")
            
            # 특정 파일명으로 전체 시스템 검색
            print(f"DEBUG - '{filename}' 파일 전체 검색:")
            search_paths = [".", "data", "backend", "../"]
            for search_path in search_paths:
                if os.path.exists(search_path):
                    try:
                        for root, dirs, files in os.walk(search_path):
                            if filename in files:
                                found_path = os.path.join(root, filename)
                                print(f"  ✓ 발견: {found_path}")
                    except:
                        pass
            
            raise HTTPException(status_code=404, detail=f"파일을 찾을 수 없습니다: {filename}")
        
        # 데이터 읽기
        print(f"DEBUG - 파일 읽기 시작: {file_path}")
        try:
            df = pd.read_csv(file_path)
            print(f"DEBUG - 파일 읽기 완료: {len(df)} 행")
        except Exception as read_error:
            print(f"ERROR - 파일 읽기 실패: {read_error}")
            raise HTTPException(status_code=400, detail=f"파일을 읽을 수 없습니다: {str(read_error)}")
        
        if df.empty:
            print("ERROR - 데이터가 비어있음")
            raise HTTPException(status_code=400, detail="데이터가 비어있습니다")
        
        # LOT 번호 생성
        total_rows = len(df)
        lot_count = (total_rows + 7) // 8  # 8개씩 나누어 올림
        print(f"DEBUG - 총 데이터: {total_rows}개, LOT 수: {lot_count}개")
        
        # 현재 날짜로 LOT 이름 생성
        from datetime import datetime
        current_date = datetime.now().strftime("%Y%m%d")
        print(f"DEBUG - 현재 날짜: {current_date}")
        
        # LOT 컬럼 추가
        df['lot_number'] = ''
        for i in range(total_rows):
            lot_index = i // 8 + 1
            lot_number = f"LOT-{current_date}-{lot_index:03d}"
            df.loc[i, 'lot_number'] = lot_number
        
        print("DEBUG - LOT 번호 할당 완료")
        
        # 새 파일명 생성 (원본 파일명 + _with_lots)
        base_name = filename.rsplit('.', 1)[0]
        extension = filename.rsplit('.', 1)[1] if '.' in filename else 'csv'
        new_filename = f"{base_name}_with_lots.{extension}"
        
        # 새 파일로 저장
        new_file_path = os.path.join(os.path.dirname(file_path), new_filename)
        print(f"DEBUG - 새 파일 저장 경로: {new_file_path}")
        
        try:
            # 디렉토리 생성 (존재하지 않는 경우)
            os.makedirs(os.path.dirname(new_file_path), exist_ok=True)
            df.to_csv(new_file_path, index=False, encoding='utf-8-sig')
            print("DEBUG - 파일 저장 완료")
        except Exception as save_error:
            print(f"ERROR - 파일 저장 실패: {save_error}")
            raise HTTPException(status_code=500, detail=f"파일 저장 실패: {str(save_error)}")
        
        # LOT별 통계 계산
        lot_summary = []
        for lot_index in range(1, lot_count + 1):
            lot_number = f"LOT-{current_date}-{lot_index:03d}"
            lot_data = df[df['lot_number'] == lot_number]
            
            lot_info = {
                'lot_number': lot_number,
                'record_count': len(lot_data),
                'start_index': (lot_index - 1) * 8 + 1,
                'end_index': min(lot_index * 8, total_rows)
            }
            lot_summary.append(lot_info)
        
        # 미리보기 데이터 생성 (처음 10행)
        preview_data = []
        try:
            preview_df = df.head(10)
            preview_data = preview_df.to_dict('records')
            print(f"DEBUG - 미리보기 데이터 생성: {len(preview_data)}행")
        except Exception as preview_error:
            print(f"WARNING - 미리보기 데이터 생성 실패: {preview_error}")
            preview_data = []
        
        result = {
            "success": True,
            "message": f"LOT 번호가 성공적으로 생성되었습니다. 총 {lot_count}개의 LOT가 생성되었습니다.",
            "filename": new_filename,
            "original_filename": filename,
            "total_records": total_rows,
            "total_lots": lot_count,
            "lot_summary": lot_summary,
            "preview_data": preview_data
        }
        
        print("DEBUG - LOT 생성 성공적으로 완료")
        return result
        
    except HTTPException:
        # HTTPException은 그대로 전달
        raise
    except Exception as e:
        print(f"ERROR - LOT 생성 중 예상치 못한 오류: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"LOT 생성 중 오류가 발생했습니다: {str(e)}")

@app.get("/api/data/files")
async def get_stored_files():
    """저장된 파일 목록 조회"""
    try:
        base_dir = Path("data/generated")
        files = []
        
        # 각 데이터 타입별 폴더에서 파일 검색
        data_types = {
            'production': 'production',
            'sensor': 'sensor',
            'experimental': 'experimental', 
            'cost_production': 'cost'
        }
        
        for folder_name, data_type in data_types.items():
            data_dir = base_dir / folder_name
            if data_dir.exists():
                for filepath in data_dir.glob("*.csv"):
                    # 파일 정보 수집
                    stat = filepath.stat()
                    filename = filepath.name
                    
                    # CSV 파일 정보 읽기
                    try:
                        df = pd.read_csv(filepath)
                        row_count = len(df)
                        col_count = len(df.columns)
                        # 미리보기 데이터 (처음 3행)
                        preview_data = df.head(3).to_dict('records') if not df.empty else []
                    except Exception as e:
                        logger.warning(f"CSV 파일 읽기 실패 {filepath}: {e}")
                        row_count = 0
                        col_count = 0
                        preview_data = []
                    
                    files.append({
                        'filepath': str(filepath),
                        'dataType': data_type,
                        'filename': filename,
                        'createTime': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'fileSizeKb': round(stat.st_size / 1024, 1),
                        'rowCount': row_count,
                        'colCount': col_count,
                        'previewData': preview_data
                    })
        
        return {"files": files}
    except Exception as e:
        logger.error(f"파일 목록 조회 오류: {e}")
        return {"files": []}

@app.get("/api/data/files/{filename}/data")
async def get_file_data(filename: str):
    """특정 파일의 전체 데이터 조회"""
    try:
        # 파일 경로 찾기
        base_dir = Path("data/generated")
        file_path = None
        
        # 각 데이터 타입별 폴더에서 파일 검색
        for folder_name in ['production', 'sensor', 'experimental', 'cost_production']:
            data_dir = base_dir / folder_name
            if data_dir.exists():
                potential_path = data_dir / filename
                if potential_path.exists():
                    file_path = potential_path
                    break
        
        if not file_path:
            raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다")
        
        # CSV 파일 읽기
        try:
            df = pd.read_csv(file_path)
            data = df.to_dict('records')
            
            return {
                "filename": filename,
                "rowCount": len(df),
                "colCount": len(df.columns),
                "columns": df.columns.tolist(),
                "data": data
            }
        except Exception as e:
            logger.error(f"CSV 파일 읽기 실패 {file_path}: {e}")
            raise HTTPException(status_code=500, detail=f"파일 읽기 실패: {str(e)}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"파일 데이터 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=f"파일 데이터 조회 중 오류가 발생했습니다: {str(e)}")

def find_file_path(filename: str) -> Path:
    """파일명으로 실제 파일 경로 찾기"""
    base_dir = Path("data/generated")
    folders = ['production', 'experimental', 'cost_production']
    
    for folder in folders:
        filepath = base_dir / folder / filename
        if filepath.exists():
            return filepath
    
    raise FileNotFoundError(f"File {filename} not found in any data folder")

@app.get("/api/data/preview/{filename}")
async def get_file_preview(filename: str):
    """파일 미리보기"""
    try:
        filepath = find_file_path(filename)
        
        # 파일 경로로부터 데이터 타입 추정
        data_type = "unknown"
        if "production" in str(filepath):
            data_type = "production"
        elif "experimental" in str(filepath):
            data_type = "experimental"
        elif "cost_production" in str(filepath):
            data_type = "cost_production"
        
        # CSV 파일 읽기
        df = pd.read_csv(filepath)
        
        # 데이터 타입별 미리보기 데이터 선택
        preview_data = get_preview_data(df, data_type)
        
        # numpy 타입을 Python 기본 타입으로 변환
        preview_data = convert_numpy_types(preview_data)
        
        return {"data": preview_data, "dataType": data_type}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        logger.error(f"파일 미리보기 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/data/download/{filename}")
async def download_file(filename: str):
    """생성된 데이터 파일 다운로드"""
    try:
        # 파일 경로 구성
        file_path = None
        data_directories = [
            "data/sensor",
            "data/production",
            "data/experimental",
            "data/cost",
            "data/generated/sensor",
            "data/generated/production", 
            "data/generated/experimental",
            "data/generated/cost_production",
            "backend/data/sensor",
            "backend/data/production",
            "backend/data/experimental", 
            "backend/data/cost",
            "backend/data/generated/sensor",
            "backend/data/generated/production",
            "backend/data/generated/experimental", 
            "backend/data/generated/cost_production"
        ]
        
        for data_dir in data_directories:
            potential_path = os.path.join(data_dir, filename)
            if os.path.exists(potential_path):
                file_path = potential_path
                break
        
        if not file_path:
            raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다")
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type='application/octet-stream'
        )
        
    except Exception as e:
        print(f"파일 다운로드 오류: {e}")
        raise HTTPException(status_code=500, detail=f"파일 다운로드 중 오류가 발생했습니다: {str(e)}")

@app.delete("/api/data/files/{filename}")
async def delete_file(filename: str):
    """파일 삭제"""
    try:
        filepath = find_file_path(filename)
        
        filepath.unlink()
        return {"message": f"File {filename} deleted successfully"}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        logger.error(f"파일 삭제 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 프로세스 관리 엔드포인트들
class ProcessAnalysisRequest(BaseModel):
    analysis_type: str
    process_data: Dict[str, Any]

class DateFilterRequest(BaseModel):
    date_filter: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None

@app.post("/api/process/lots")
async def get_lots(request: DateFilterRequest):
    """Lot 데이터 조회"""
    try:
        from src.copilot.process_management_engine import LotTrackingEngine
        engine = LotTrackingEngine()
        
        # Lot 데이터 로드
        lots, is_sample_data = engine.load_lot_data()
        
        # 날짜 필터링 적용
        start_date = datetime.strptime(request.start_date, '%Y-%m-%d').date() if request.start_date else None
        end_date = datetime.strptime(request.end_date, '%Y-%m-%d').date() if request.end_date else None
        
        filtered_lots = engine.filter_lots_by_date(lots, request.date_filter, start_date, end_date)
        
        # 통계 계산
        stats = engine.get_lot_statistics(filtered_lots)
        daily_stats = engine.get_daily_statistics(filtered_lots)
        
        return {
            "success": True,
            "lots": filtered_lots,
            "statistics": stats,
            "daily_statistics": daily_stats,
            "is_sample_data": is_sample_data
        }
    
    except Exception as e:
        logger.error(f"Lot 데이터 조회 오류: {e}")
        return {"success": False, "message": str(e)}

@app.post("/api/process/equipment")
async def get_equipment_status(request: DateFilterRequest):
    """설비 모니터링 데이터 조회"""
    try:
        from src.copilot.process_management_engine import LotTrackingEngine, EquipmentMonitoringEngine
        
        # Lot 데이터 먼저 로드
        lot_engine = LotTrackingEngine()
        lots, is_sample_data = lot_engine.load_lot_data()
        
        start_date = datetime.strptime(request.start_date, '%Y-%m-%d').date() if request.start_date else None
        end_date = datetime.strptime(request.end_date, '%Y-%m-%d').date() if request.end_date else None
        
        filtered_lots = lot_engine.filter_lots_by_date(lots, request.date_filter, start_date, end_date)
        
        # 설비 모니터링 엔진
        equipment_engine = EquipmentMonitoringEngine()
        equipment_status, _ = equipment_engine.calculate_equipment_status(filtered_lots, is_sample_data)
        equipment_stats, _ = equipment_engine.calculate_equipment_detailed_stats(
            filtered_lots, request.date_filter, start_date, end_date
        )
        
        return {
            "success": True,
            "equipment_status": equipment_status,
            "equipment_stats": equipment_stats,
            "is_sample_data": is_sample_data
        }
    
    except Exception as e:
        logger.error(f"설비 모니터링 데이터 조회 오류: {e}")
        return {"success": False, "message": str(e)}

@app.post("/api/process/anomaly")
async def get_anomaly_detection(request: Dict[str, Any]):
    """이상탐지 데이터 조회"""
    try:
        from src.copilot.process_management_engine import LotTrackingEngine, AnomalyDetectionEngine
        
        # 파라미터 추출
        date_filter = request.get('date_filter', '최근 3일')
        start_date = request.get('start_date')
        end_date = request.get('end_date')
        temp_threshold = request.get('temp_threshold', 200)
        pressure_threshold = request.get('pressure_threshold', 3.0)
        purity_threshold = request.get('purity_threshold', 95.0)
        yield_threshold = request.get('yield_threshold', 85.0)
        
        # Lot 데이터 로드
        lot_engine = LotTrackingEngine()
        lots, is_sample_data = lot_engine.load_lot_data()
        
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None
        
        filtered_lots = lot_engine.filter_lots_by_date(lots, date_filter, start_date_obj, end_date_obj)
        
        # 이상탐지 엔진
        anomaly_engine = AnomalyDetectionEngine()
        anomaly_alerts, _ = anomaly_engine.detect_anomalies(
            filtered_lots, temp_threshold, pressure_threshold,
            purity_threshold, yield_threshold, date_filter,
            start_date_obj, end_date_obj
        )
        
        anomaly_stats, _ = anomaly_engine.calculate_anomaly_statistics(
            filtered_lots, temp_threshold, pressure_threshold,
            purity_threshold, yield_threshold, date_filter,
            start_date_obj, end_date_obj
        )
        
        return {
            "success": True,
            "anomaly_alerts": anomaly_alerts,
            "anomaly_stats": anomaly_stats,
            "is_sample_data": is_sample_data
        }
    
    except Exception as e:
        logger.error(f"이상탐지 데이터 조회 오류: {e}")
        return {"success": False, "message": str(e)}

@app.post("/api/process/analyze")
async def analyze_process(request: ProcessAnalysisRequest):
    """프로세스 분석"""
    try:
        engine = engines.get("process_management")
        if not engine:
            raise HTTPException(status_code=500, detail="Process management engine not available")
        
        # 간단한 프로세스 분석 결과 반환
        result = {
            "analysis_type": request.analysis_type,
            "process_metrics": {
                "temperature": request.process_data.get("temperature", 175),
                "pressure": request.process_data.get("pressure", 2.5),
                "efficiency": 85.5,
                "quality_score": 92.3,
                "throughput": 120.0
            },
            "recommendations": [
                "온도를 175-180°C 범위로 유지하세요",
                "압력을 2.3-2.7 bar 범위로 조절하세요",
                "품질 지표가 양호합니다"
            ],
            "status": "analysis_completed",
            "timestamp": "2025-01-11T18:50:00"
        }
        
        return {"status": "success", "analysis": result}
    except Exception as e:
        logger.error(f"프로세스 분석 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 제품 데이터 분석 엔드포인트들
@app.post("/api/product/upload-data")
async def upload_product_data(file: UploadFile = File(...)):
    """제품 데이터 파일 업로드 및 분석"""
    try:
        # 파일 형식 검증
        if not file.filename.endswith(('.csv', '.xlsx')):
            raise HTTPException(status_code=400, detail="CSV 또는 Excel 파일만 업로드 가능합니다.")
        
        # 파일 내용 읽기
        contents = await file.read()
        
        # 파일 형식에 따라 데이터프레임 생성
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        else:
            df = pd.read_excel(io.BytesIO(contents))
        
        # 데이터 분석 엔진 사용
        engine = engines.get("product_analysis")
        if not engine:
            raise HTTPException(status_code=500, detail="Product analysis engine not available")
        
        # 기본 정보 추출
        data_info = {
            "rows": len(df),
            "columns": len(df.columns),
            "missing_values": df.isnull().sum().sum(),
            "numeric_columns": len(df.select_dtypes(include=[np.number]).columns)
        }
        
        # 컬럼 정보
        column_info = []
        for col in df.columns:
            column_info.append({
                "name": col,
                "type": str(df[col].dtype),
                "missing": int(df[col].isnull().sum()),
                "unique": int(df[col].nunique())
            })
        
        # 수치형 컬럼에 대한 기본 통계
        numeric_df = df.select_dtypes(include=[np.number])
        basic_stats = {}
        if len(numeric_df.columns) > 0:
            stats_result = engine.get_basic_statistics(numeric_df)
            basic_stats = stats_result
        
        # 상관관계 분석 (수치형 컬럼이 2개 이상인 경우)
        correlation_data = {}
        if len(numeric_df.columns) > 1:
            try:
                correlation_result = engine.analysis_engine.analyze_correlation(
                    numeric_df, list(numeric_df.columns), 0.7
                )
                correlation_data = correlation_result.correlation_matrix.to_dict()
            except Exception as e:
                logger.warning(f"상관관계 분석 오류: {e}")
        
        # 데이터 미리보기 (상위 10행)
        data_preview = df.head(10).to_dict('records')
        
        return {
            "success": True,
            "message": f"파일 '{file.filename}' 업로드 및 분석 완료",
            "data_info": data_info,
            "column_info": column_info,
            "basic_stats": basic_stats,
            "correlation_data": correlation_data,
            "data_preview": data_preview,
            "filename": file.filename
        }
        
    except Exception as e:
        logger.error(f"제품 데이터 업로드 오류: {e}")
        raise HTTPException(status_code=500, detail=f"파일 처리 중 오류: {str(e)}")

@app.post("/api/product/preprocess")
async def preprocess_product_data(request: Dict[str, Any]):
    """제품 데이터 전처리"""
    try:
        engine = engines.get("product_analysis")
        if not engine:
            raise HTTPException(status_code=500, detail="Product analysis engine not available")
        
        # 요청에서 데이터 추출 (실제로는 세션이나 임시 저장소에서 가져와야 함)
        data = request.get('data', [])
        if not data:
            raise HTTPException(status_code=400, detail="전처리할 데이터가 없습니다.")
        
        df = pd.DataFrame(data)
        
        # 데이터 전처리 엔진 사용
        preprocessing_engine = engine.preprocessing_engine
        preprocessing_result = preprocessing_engine.preprocess_for_modeling(df)
        
        # 결과 반환
        return {
            "success": True,
            "message": "데이터 전처리 완료",
            "original_shape": preprocessing_result.original_shape,
            "final_shape": preprocessing_result.final_shape,
            "removed_columns": preprocessing_result.removed_columns,
            "warnings": preprocessing_result.warnings,
            "steps": preprocessing_result.steps,
            "processed_data_preview": preprocessing_result.processed_data.head(5).to_dict('records') if preprocessing_result.processed_data is not None else []
        }
        
    except Exception as e:
        logger.error(f"제품 데이터 전처리 오류: {e}")
        raise HTTPException(status_code=500, detail=f"전처리 중 오류: {str(e)}")

@app.post("/api/product/analyze")
async def analyze_product_data(request: Dict[str, Any]):
    """제품 데이터 분석"""
    try:
        engine = engines.get("product_analysis")
        if not engine:
            raise HTTPException(status_code=500, detail="Product analysis engine not available")
        
        # 샘플 데이터로 분석 수행 (실제로는 request 데이터를 사용)
        try:
            import pandas as pd
            import numpy as np
            
            # 샘플 데이터 생성 (실제로는 request에서 받은 데이터 사용)
            sample_data = {
                'temperature': np.random.normal(175, 10, 100),
                'pressure': np.random.normal(2.5, 0.3, 100), 
                'quality': np.random.normal(95, 5, 100),
                'yield': np.random.normal(85, 8, 100)
            }
            df = pd.DataFrame(sample_data)
            
            # 기본 통계 분석
            result = engine.get_basic_statistics(df)
            
            # 데이터 품질 분석 추가
            quality_analysis = engine.analyze_data_quality(df)
            result.update({"data_quality": quality_analysis})
            
        except Exception as e:
            result = {"message": f"Product analysis error: {str(e)}", "request_data": request}
        
        return {"status": "success", "analysis": result}
    except Exception as e:
        logger.error(f"제품 데이터 분석 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 실험 설계 엔드포인트들
@app.post("/api/experiment/design")
async def design_experiment(request: ExperimentRequest):
    """실험 설계"""
    try:
        engine = engines.get("experimental_design")
        if not engine:
            raise HTTPException(status_code=500, detail="Experimental design engine not available")
        
        # 실험 설계 결과 반환
        result = {
            "design_type": request.design_type,
            "factors": request.factors,
            "responses": request.responses,
            "experiment_plan": [
                {"run": i+1, "temperature": 150 + i*10, "pressure": 2.0 + i*0.2, "flow_rate": 180 + i*8}
                for i in range(min(5, len(request.factors) * 2))
            ],
            "design_efficiency": 0.87,
            "total_runs": min(5, len(request.factors) * 2),
            "estimated_duration": "3 days",
            "recommendations": [
                "실험 순서를 랜덤화하세요",
                "각 조건당 3회 반복 실험 권장",
                "온도와 압력을 동시에 변경하지 마세요"
            ]
        }
        
        return {"status": "success", "design": result}
    except Exception as e:
        logger.error(f"실험 설계 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 원가 관리 엔드포인트들
@app.post("/api/cost/analyze")
async def analyze_cost(request: CostAnalysisRequest):
    """원가 분석"""
    try:
        engine = engines.get("cost_management")
        if not engine:
            raise HTTPException(status_code=500, detail="Cost management engine not available")
        
        # 원가 분석 결과 반환
        result = {
            "analysis_type": request.analysis_type,
            "cost_breakdown": {
                "material_cost": sum([v for k, v in request.cost_data.items() if "material" in k.lower()]),
                "labor_cost": request.cost_data.get("labor_cost", 20000),
                "energy_cost": request.cost_data.get("energy_cost", 3000),
                "overhead": request.cost_data.get("overhead", 8000),
                "total_cost": sum(request.cost_data.values())
            },
            "cost_optimization": {
                "potential_savings": "15-20%",
                "target_areas": ["원자재 구매 최적화", "에너지 효율 개선", "공정 자동화"],
                "roi_projection": "6-12개월"
            },
            "recommendations": [
                "원자재 비용이 전체의 33%를 차지합니다",
                "에너지 효율을 10% 개선하면 연간 3000만원 절약 가능",
                "공정 자동화 투자 검토 권장"
            ]
        }
        
        return {"status": "success", "analysis": result}
    except Exception as e:
        logger.error(f"원가 분석 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/cost/optimize")
async def optimize_cost(request: Dict[str, Any]):
    """원가 최적화"""
    try:
        engine = engines.get("cost_optimization")
        if not engine:
            raise HTTPException(status_code=500, detail="Cost optimization engine not available")
        
        result = engine.optimize_cost(request)
        
        return {"status": "success", "optimization": result}
    except Exception as e:
        logger.error(f"원가 최적화 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# AI 보고서 생성 엔드포인트들 - 제거됨
# @app.post("/api/report/generate")
# async def generate_report(request: Dict[str, Any]):
#     """AI 보고서 생성"""
#     try:
#         engine = engines.get("ai_report")
#         if not engine:
#             raise HTTPException(status_code=500, detail="AI report engine not available")
#         
#         result = engine.generate_comprehensive_report(request)
#         
#         return {"status": "success", "report": result}
#     except Exception as e:
#         logger.error(f"AI 보고서 생성 오류: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

# 고급 최적화 엔드포인트들
@app.post("/api/optimization/advanced")
async def advanced_optimize(request: Dict[str, Any]):
    """고급 최적화"""
    try:
        engine = engines.get("advanced_optimization")
        if not engine:
            raise HTTPException(status_code=500, detail="Advanced optimization engine not available")
        
        result = engine.optimize_advanced(request)
        
        return {"status": "success", "optimization": result}
    except Exception as e:
        logger.error(f"고급 최적화 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))



if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 