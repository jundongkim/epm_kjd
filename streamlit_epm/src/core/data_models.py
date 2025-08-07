"""
DX-AI Manufacturing Copilot 데이터 모델
"""

from datetime import datetime, date
from typing import List, Optional, Dict, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, validator
import uuid

# 열거형 정의
class EquipmentStatus(str, Enum):
    """설비 상태"""
    RUNNING = "running"
    STOPPED = "stopped"
    MAINTENANCE = "maintenance"
    ERROR = "error"

class LotStatus(str, Enum):
    """Lot 상태"""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress" 
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class ExperimentStatus(str, Enum):
    """실험 상태"""
    DESIGNED = "designed"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class AlertLevel(str, Enum):
    """알림 수준"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class OptimizationObjective(str, Enum):
    """최적화 목표"""
    MINIMIZE_COST = "minimize_cost"
    MAXIMIZE_YIELD = "maximize_yield"
    MAXIMIZE_PURITY = "maximize_purity"
    MULTI_OBJECTIVE = "multi_objective"

# 기본 모델
class BaseDataModel(BaseModel):
    """기본 데이터 모델"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# 재료 및 원료 모델
class MaterialModel(BaseDataModel):
    """원료/재료 모델"""
    name: str = Field(..., description="재료명")
    code: str = Field(..., description="재료 코드") 
    category: str = Field(..., description="재료 카테고리")
    unit: str = Field(..., description="단위")
    unit_cost: float = Field(..., ge=0, description="단가")
    supplier: Optional[str] = Field(None, description="공급업체")
    specifications: Dict[str, Any] = Field(default_factory=dict, description="규격")
    
class MaterialUsageModel(BaseDataModel):
    """재료 사용량 모델"""
    material_id: str = Field(..., description="재료 ID")
    material_name: str = Field(..., description="재료명")
    quantity: float = Field(..., ge=0, description="사용량")
    unit: str = Field(..., description="단위")
    cost: float = Field(..., ge=0, description="비용")

# 설비 모델
class EquipmentModel(BaseDataModel):
    """설비 모델"""
    name: str = Field(..., description="설비명")
    code: str = Field(..., description="설비 코드")
    status: EquipmentStatus = Field(..., description="설비 상태")
    location: str = Field(..., description="설치 위치")
    capacity: float = Field(..., gt=0, description="처리 용량")
    utilization_rate: float = Field(..., ge=0, le=100, description="가동률 (%)")
    last_maintenance: Optional[datetime] = Field(None, description="최근 정비일")
    next_maintenance: Optional[datetime] = Field(None, description="다음 정비일")
    operating_conditions: Dict[str, Any] = Field(default_factory=dict, description="운전조건")
    
class EquipmentReadingModel(BaseDataModel):
    """설비 계측값 모델"""
    equipment_id: str = Field(..., description="설비 ID")
    parameter: str = Field(..., description="계측 파라미터")
    value: float = Field(..., description="계측값")
    unit: str = Field(..., description="단위")
    timestamp: datetime = Field(default_factory=datetime.now, description="측정 시간")
    is_anomaly: bool = Field(default=False, description="이상치 여부")

# Lot 모델
class LotModel(BaseDataModel):
    """Lot 모델"""
    lot_number: str = Field(..., description="Lot 번호")
    product_code: str = Field(..., description="제품 코드") 
    status: LotStatus = Field(..., description="Lot 상태")
    start_date: datetime = Field(..., description="시작일시")
    end_date: Optional[datetime] = Field(None, description="완료일시")
    target_quantity: float = Field(..., gt=0, description="목표 생산량")
    actual_quantity: Optional[float] = Field(None, ge=0, description="실제 생산량")
    equipment_id: str = Field(..., description="사용 설비 ID")
    materials_used: List[MaterialUsageModel] = Field(default_factory=list, description="사용 재료")
    quality_metrics: Dict[str, float] = Field(default_factory=dict, description="품질 지표")
    
    @validator("end_date")
    def validate_end_date(cls, v, values):
        if v and "start_date" in values and v < values["start_date"]:
            raise ValueError("완료일시는 시작일시보다 이후여야 합니다")
        return v

# 실험 모델
class ExperimentParameterModel(BaseModel):
    """실험 파라미터 모델"""
    name: str = Field(..., description="파라미터명")
    value: Union[float, str, bool] = Field(..., description="값")
    unit: Optional[str] = Field(None, description="단위")
    min_value: Optional[float] = Field(None, description="최솟값")
    max_value: Optional[float] = Field(None, description="최댓값")

class ExperimentModel(BaseDataModel):
    """실험 모델"""
    name: str = Field(..., description="실험명")
    description: Optional[str] = Field(None, description="실험 설명")
    status: ExperimentStatus = Field(..., description="실험 상태")
    objective: str = Field(..., description="실험 목적")
    parameters: List[ExperimentParameterModel] = Field(..., description="실험 파라미터")
    target_responses: List[str] = Field(..., description="목표 응답변수")
    actual_responses: Dict[str, float] = Field(default_factory=dict, description="실제 응답값")
    experiment_date: date = Field(..., description="실험일")
    operator: str = Field(..., description="실험자")
    notes: Optional[str] = Field(None, description="실험 노트")

class DOERunModel(BaseDataModel):
    """DOE 실험 런 모델"""
    experiment_id: str = Field(..., description="실험 ID")
    run_number: int = Field(..., gt=0, description="런 번호")
    factor_settings: Dict[str, float] = Field(..., description="인자 설정값")
    response_values: Dict[str, float] = Field(default_factory=dict, description="응답값")
    is_center_point: bool = Field(default=False, description="중심점 여부")

# 예측 모델
class PredictionModel(BaseDataModel):
    """예측 모델"""
    model_name: str = Field(..., description="모델명")
    model_type: str = Field(..., description="모델 타입")
    target_variable: str = Field(..., description="목표 변수")
    input_features: List[str] = Field(..., description="입력 특성")
    accuracy_score: Optional[float] = Field(None, ge=0, le=1, description="정확도")
    r2_score: Optional[float] = Field(None, description="R² 점수")
    rmse: Optional[float] = Field(None, ge=0, description="RMSE")
    training_date: datetime = Field(default_factory=datetime.now, description="훈련일시")
    model_path: Optional[str] = Field(None, description="모델 파일 경로")

class PredictionRequestModel(BaseModel):
    """예측 요청 모델"""
    model_id: str = Field(..., description="모델 ID")
    input_data: Dict[str, Union[float, str]] = Field(..., description="입력 데이터")
    confidence_interval: bool = Field(default=False, description="신뢰구간 포함 여부")

class PredictionResponseModel(BaseModel):
    """예측 응답 모델"""
    prediction: float = Field(..., description="예측값")
    confidence: float = Field(..., ge=0, le=1, description="신뢰도")
    lower_bound: Optional[float] = Field(None, description="신뢰구간 하한")
    upper_bound: Optional[float] = Field(None, description="신뢰구간 상한")
    feature_importance: Optional[Dict[str, float]] = Field(None, description="특성 중요도")

# 원가 모델
class CostItemModel(BaseDataModel):
    """원가 항목 모델"""
    category: str = Field(..., description="원가 카테고리")
    item_name: str = Field(..., description="항목명")
    unit_cost: float = Field(..., ge=0, description="단위 원가")
    quantity: float = Field(..., ge=0, description="수량")
    total_cost: float = Field(..., ge=0, description="총 원가")
    cost_date: date = Field(..., description="원가 발생일")

class OptimizationConstraintModel(BaseModel):
    """최적화 제약조건 모델"""
    parameter: str = Field(..., description="제약 파라미터")
    constraint_type: str = Field(..., description="제약 타입 (<=, >=, =)")
    value: float = Field(..., description="제약값")
    weight: float = Field(default=1.0, ge=0, description="가중치")

class OptimizationResultModel(BaseDataModel):
    """최적화 결과 모델"""
    objective: OptimizationObjective = Field(..., description="최적화 목표")
    optimal_values: Dict[str, float] = Field(..., description="최적값")
    objective_value: float = Field(..., description="목적함수 값")
    constraints: List[OptimizationConstraintModel] = Field(..., description="제약조건")
    solver_status: str = Field(..., description="솔버 상태")
    solve_time: float = Field(..., ge=0, description="해결 시간(초)")
    iterations: int = Field(..., ge=0, description="반복 횟수")

# 알림 모델
class AlertModel(BaseDataModel):
    """알림 모델"""
    title: str = Field(..., description="알림 제목")
    message: str = Field(..., description="알림 메시지")
    level: AlertLevel = Field(..., description="알림 수준")
    source: str = Field(..., description="알림 소스")
    source_id: Optional[str] = Field(None, description="소스 ID")
    is_read: bool = Field(default=False, description="읽음 여부")
    is_acknowledged: bool = Field(default=False, description="확인 여부")
    acknowledged_by: Optional[str] = Field(None, description="확인자")
    acknowledged_at: Optional[datetime] = Field(None, description="확인 시간")

# 보고서 모델  
class ReportModel(BaseDataModel):
    """보고서 모델"""
    title: str = Field(..., description="보고서 제목")
    report_type: str = Field(..., description="보고서 타입")
    content: str = Field(..., description="보고서 내용")
    generated_by: str = Field(..., description="생성자")
    data_sources: List[str] = Field(default_factory=list, description="데이터 소스")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="생성 파라미터")
    file_path: Optional[str] = Field(None, description="파일 경로")

# API 응답 모델
class ApiResponse(BaseModel):
    """API 응답 모델"""
    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="응답 메시지")
    data: Optional[Any] = Field(None, description="응답 데이터")
    error_code: Optional[str] = Field(None, description="에러 코드")
    timestamp: datetime = Field(default_factory=datetime.now, description="응답 시간")

class PaginatedResponse(BaseModel):
    """페이지네이션 응답 모델"""
    items: List[Any] = Field(..., description="항목 리스트")
    total: int = Field(..., ge=0, description="총 개수")
    page: int = Field(..., gt=0, description="현재 페이지")
    size: int = Field(..., gt=0, description="페이지 크기")
    pages: int = Field(..., ge=0, description="총 페이지 수")

# 파일 업로드 모델
class FileUploadModel(BaseDataModel):
    """파일 업로드 모델"""
    filename: str = Field(..., description="파일명")
    file_size: int = Field(..., ge=0, description="파일 크기")
    file_type: str = Field(..., description="파일 타입")
    upload_path: str = Field(..., description="업로드 경로")
    checksum: Optional[str] = Field(None, description="체크섬")

# 시스템 메트릭 모델
class SystemMetricModel(BaseDataModel):
    """시스템 메트릭 모델"""
    metric_name: str = Field(..., description="메트릭명")
    value: float = Field(..., description="값")
    unit: str = Field(..., description="단위")
    timestamp: datetime = Field(default_factory=datetime.now, description="측정 시간")
    tags: Dict[str, str] = Field(default_factory=dict, description="태그")

# 워크플로우 모델 (LangGraph용)
class WorkflowNodeModel(BaseDataModel):
    """워크플로우 노드 모델"""
    node_id: str = Field(..., description="노드 ID")
    node_type: str = Field(..., description="노드 타입")
    status: str = Field(..., description="노드 상태")
    input_data: Dict[str, Any] = Field(default_factory=dict, description="입력 데이터")
    output_data: Dict[str, Any] = Field(default_factory=dict, description="출력 데이터")
    execution_time: Optional[float] = Field(None, ge=0, description="실행 시간(초)")
    error_message: Optional[str] = Field(None, description="에러 메시지")

class WorkflowExecutionModel(BaseDataModel):
    """워크플로우 실행 모델"""
    workflow_id: str = Field(..., description="워크플로우 ID") 
    execution_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="실행 ID")
    status: str = Field(..., description="실행 상태")
    start_time: datetime = Field(default_factory=datetime.now, description="시작 시간")
    end_time: Optional[datetime] = Field(None, description="종료 시간")
    nodes_executed: List[WorkflowNodeModel] = Field(default_factory=list, description="실행된 노드들")
    final_result: Optional[Dict[str, Any]] = Field(None, description="최종 결과") 