"""
DX-AI Manufacturing Copilot - 제품 예측 모델링 API

제품 예측 모델링 관련 API 엔드포인트
"""

from fastapi import APIRouter, HTTPException, File, UploadFile
from fastapi.responses import JSONResponse
import pandas as pd
import io
import logging
from typing import Dict, List, Any, Optional
from pydantic import BaseModel

from src.copilot.product_modeling_engine import (
    ProductModelingEngine,
    ModelType,
    TaskType,
    create_model_configuration,
    create_prediction_request,
    create_report_request
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/product-modeling", tags=["product-modeling"])

# 전역 엔진 인스턴스
modeling_engine = ProductModelingEngine()


# Pydantic 모델들
class TrainingDataRequest(BaseModel):
    """훈련 데이터 설정 요청"""
    data: List[Dict[str, Any]]
    preprocessing_info: Optional[Dict[str, Any]] = None


class ModelConfigRequest(BaseModel):
    """모델 설정 요청"""
    model_type: str
    model_name: str
    target_variable: str = "quality_score"
    hyperparameters: Dict[str, Any] = {}
    task_type: str = "regression"
    test_size: float = 0.2
    random_state: int = 42


class PredictionRequestModel(BaseModel):
    """예측 요청 모델"""
    model_name: str
    input_data: Dict[str, float]
    confidence_interval: bool = True


class ReportRequestModel(BaseModel):
    """보고서 생성 요청"""
    report_type: str = "comprehensive"
    include_sections: List[str] = ["model_performance", "feature_importance", "predictions", "recommendations"]
    report_length: str = "detailed"
    model_name: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None


@router.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "healthy", "service": "product-modeling"}


@router.post("/data/upload")
async def upload_training_data(file: UploadFile = File(...)):
    """
    훈련 데이터 파일 업로드
    """
    try:
        # 파일 내용 읽기
        contents = await file.read()
        
        # CSV 파일 파싱
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        elif file.filename.endswith('.xlsx'):
            df = pd.read_excel(io.BytesIO(contents))
        else:
            raise HTTPException(status_code=400, detail="지원되지 않는 파일 형식입니다. CSV 또는 Excel 파일을 업로드해주세요.")
        
        # 훈련 데이터 설정
        result = modeling_engine.set_training_data(df)
        
        if result["success"]:
            return {
                "success": True,
                "message": "훈련 데이터가 성공적으로 업로드되었습니다.",
                "data_info": {
                    "filename": file.filename,
                    "shape": result["data_shape"],
                    "numeric_columns": result["numeric_columns"],
                    "categorical_columns": result["categorical_columns"]
                }
            }
        else:
            raise HTTPException(status_code=400, detail=result["message"])
            
    except Exception as e:
        logger.error(f"훈련 데이터 업로드 실패: {e}")
        raise HTTPException(status_code=500, detail=f"데이터 업로드 중 오류가 발생했습니다: {str(e)}")


@router.post("/data/set")
async def set_training_data(request: TrainingDataRequest):
    """
    훈련 데이터 설정 (JSON 형태)
    """
    try:
        # JSON 데이터를 DataFrame으로 변환
        df = pd.DataFrame(request.data)
        
        # 훈련 데이터 설정
        result = modeling_engine.set_training_data(df, request.preprocessing_info)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["message"])
            
    except Exception as e:
        logger.error(f"훈련 데이터 설정 실패: {e}")
        raise HTTPException(status_code=500, detail=f"데이터 설정 중 오류가 발생했습니다: {str(e)}")


@router.get("/data/sample")
async def get_sample_data():
    """
    예시 데이터 반환
    """
    try:
        sample_data = modeling_engine.get_sample_data()
        
        return {
            "success": True,
            "data": sample_data.to_dict('records'),
            "columns": list(sample_data.columns),
            "shape": sample_data.shape,
            "message": "예시 데이터가 생성되었습니다."
        }
        
    except Exception as e:
        logger.error(f"예시 데이터 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=f"예시 데이터 생성 중 오류가 발생했습니다: {str(e)}")


@router.post("/models/create")
async def create_model(request: ModelConfigRequest):
    """
    모델 생성
    """
    try:
        # 모델 설정 생성
        config = create_model_configuration(
            model_type=request.model_type,
            model_name=request.model_name,
            target_variable=request.target_variable,
            hyperparameters=request.hyperparameters,
            task_type=request.task_type
        )
        
        # 모델 생성
        result = modeling_engine.create_model(config)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["message"])
            
    except Exception as e:
        logger.error(f"모델 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=f"모델 생성 중 오류가 발생했습니다: {str(e)}")


@router.post("/models/train")
async def train_model(request: ModelConfigRequest):
    """
    모델 훈련
    """
    try:
        # 모델 설정 생성
        config = create_model_configuration(
            model_type=request.model_type,
            model_name=request.model_name,
            target_variable=request.target_variable,
            hyperparameters=request.hyperparameters,
            task_type=request.task_type
        )
        
        # 모델 생성
        create_result = modeling_engine.create_model(config)
        if not create_result["success"]:
            raise HTTPException(status_code=400, detail=create_result["message"])
        
        # 모델 훈련
        train_result = modeling_engine.train_model(config)
        
        if train_result["success"]:
            training_result = train_result["training_result"]
            
            # 안전한 feature_importance 처리
            feature_importance_data = None
            if hasattr(training_result, 'feature_importance') and training_result.feature_importance is not None:
                try:
                    if hasattr(training_result.feature_importance, 'to_dict'):
                        feature_importance_data = training_result.feature_importance.to_dict('records')
                    else:
                        # DataFrame이 아닌 경우 None으로 설정
                        feature_importance_data = None
                except Exception as e:
                    logger.warning(f"Feature importance 변환 실패: {e}")
                    feature_importance_data = None
            
            return {
                "success": True,
                "message": train_result["message"],
                "training_result": {
                    "model_name": training_result.model_name,
                    "model_type": training_result.model_type,
                    "target_variable": training_result.target_variable,
                    "feature_names": training_result.feature_names,
                    "metrics": training_result.metrics,
                    "training_time": training_result.training_time,
                    "data_shape": training_result.data_shape,
                    "feature_importance": feature_importance_data,
                    "predictions": {
                        "test_actual": training_result.predictions.get('test_actual', []),
                        "test_predictions": training_result.predictions.get('test_predictions', [])
                    }
                }
            }
        else:
            raise HTTPException(status_code=400, detail=train_result["message"])
            
    except HTTPException:
        # HTTP 예외는 그대로 재발생
        raise
    except Exception as e:
        logger.error(f"모델 훈련 실패: {e}")
        import traceback
        logger.error(f"상세 오류: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"모델 훈련 중 오류가 발생했습니다: {str(e)}")


@router.post("/models/predict")
async def predict(request: PredictionRequestModel):
    """
    예측 수행
    """
    try:
        logger.info(f"예측 요청: 모델={request.model_name}, 입력특성={list(request.input_data.keys())}")
        
        # 예측 요청 생성
        prediction_request = create_prediction_request(
            model_name=request.model_name,
            input_data=request.input_data,
            confidence_interval=request.confidence_interval
        )
        
        # 예측 수행
        result = modeling_engine.predict(prediction_request)
        
        if result["success"]:
            prediction_result = result["prediction_result"]
            
            return {
                "success": True,
                "message": result["message"],
                "prediction": prediction_result.prediction,
                "confidence_interval": prediction_result.confidence_interval,
                "model_name": prediction_result.model_name,
                "timestamp": prediction_result.timestamp
            }
        else:
            logger.error(f"예측 실패: {result.get('message', result.get('error', 'Unknown error'))}")
            raise HTTPException(status_code=400, detail=result.get("message", result.get("error", "예측에 실패했습니다.")))
            
    except HTTPException:
        # HTTP 예외는 그대로 재발생
        raise
    except Exception as e:
        logger.error(f"예측 실패: {e}")
        import traceback
        logger.error(f"상세 오류: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"예측 중 오류가 발생했습니다: {str(e)}")


@router.post("/reports/generate")
async def generate_ai_report(request: ReportRequestModel):
    """
    AI 보고서 생성
    """
    try:
        # 모델 결과 가져오기
        model_results = None
        if request.model_name:
            model_results = modeling_engine.get_training_result(request.model_name)
        
        # 보고서 요청 생성
        report_request = create_report_request(
            report_type=request.report_type,
            include_sections=request.include_sections,
            report_length=request.report_length,
            model_results=model_results,
            additional_data=request.additional_data
        )
        
        # 보고서 생성
        result = modeling_engine.generate_ai_report(report_request)
        
        if result["success"]:
            return {
                "success": True,
                "message": result["message"],
                "report_content": result["report_content"],
                "report_metadata": result["report_metadata"]
            }
        else:
            raise HTTPException(status_code=400, detail="보고서 생성에 실패했습니다.")
            
    except Exception as e:
        logger.error(f"AI 보고서 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=f"보고서 생성 중 오류가 발생했습니다: {str(e)}")


@router.get("/models")
async def get_models():
    """
    등록된 모델 목록 조회
    """
    try:
        models = modeling_engine.get_available_models()
        return {
            "success": True,
            "models": models,
            "count": len(models)
        }
        
    except Exception as e:
        logger.error(f"모델 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"모델 목록 조회 중 오류가 발생했습니다: {str(e)}")


@router.get("/models/{model_name}")
async def get_model_info(model_name: str):
    """
    특정 모델 정보 조회
    """
    try:
        model_info = modeling_engine.get_model_info(model_name)
        training_result = modeling_engine.get_training_result(model_name)
        
        return {
            "success": True,
            "model_info": model_info,
            "training_result": (
                {
                    "model_name": training_result.model_name,
                    "model_type": training_result.model_type,
                    "target_variable": training_result.target_variable,
                    "metrics": training_result.metrics,
                    "training_time": training_result.training_time,
                    "data_shape": training_result.data_shape
                } if training_result else None
            )
        }
        
    except Exception as e:
        logger.error(f"모델 정보 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"모델 정보 조회 중 오류가 발생했습니다: {str(e)}")


@router.get("/models/recommendations/{target_variable}")
async def get_model_recommendations(target_variable: str):
    """
    모델 추천
    """
    try:
        # 현재 설정된 훈련 데이터 사용
        if modeling_engine.training_data is None:
            raise HTTPException(status_code=400, detail="훈련 데이터가 설정되지 않았습니다.")
        
        recommendations = modeling_engine.get_model_recommendations(
            modeling_engine.training_data, target_variable
        )
        
        return {
            "success": True,
            "recommendations": recommendations,
            "target_variable": target_variable
        }
        
    except Exception as e:
        logger.error(f"모델 추천 실패: {e}")
        raise HTTPException(status_code=500, detail=f"모델 추천 중 오류가 발생했습니다: {str(e)}") 