"""
DX-AI Manufacturing Copilot 설정 파일
"""

import os
from typing import List, Optional, Dict, Any
from pydantic import Field, validator, BaseModel
from pydantic_settings import BaseSettings
from pathlib import Path

# Slack 설정
class SlackConfig(BaseModel):
    """Slack 설정 모델"""
    
    enabled: bool = Field(default=False, env="SLACK_ENABLED")
    bot_token: str = Field(default="", env="SLACK_BOT_TOKEN")
    app_token: str = Field(default="", env="SLACK_APP_TOKEN")
    webhook_url: str = Field(default="", env="SLACK_WEBHOOK_URL")
    channel: str = Field(default="#manufacturing-copilot", env="SLACK_CHANNEL")
    user_token: str = Field(default="", env="SLACK_USER_TOKEN")
    webhook_secret: str = Field(default="manufacturing-copilot-secret-key", env="WEBHOOK_SECRET")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# 앱 설정
class AppConfig(BaseModel):
    """앱 설정 모델"""
    
    app_name: str = Field(default="DX-AI Manufacturing Copilot", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    app_description: str = Field(default="스마트 제조 공정 관리를 위한 AI 솔루션", env="APP_DESCRIPTION")
    debug: bool = Field(default=False, env="DEBUG")
    testing: bool = Field(default=False, env="TESTING")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# 서버 설정
class ServerConfig(BaseModel):
    """서버 설정 모델"""
    
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    workers: int = Field(default=1, env="WORKERS")
    reload: bool = Field(default=False, env="RELOAD")
    secret_key: str = Field(default="manufacturing-copilot-super-secret-key", env="SECRET_KEY")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# 로그 설정
class LogConfig(BaseModel):
    """로그 설정 모델"""
    
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="logs/manufacturing-copilot.log", env="LOG_FILE")
    log_rotation: str = Field(default="midnight", env="LOG_ROTATION")
    log_retention: int = Field(default=30, env="LOG_RETENTION")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# 데이터베이스 설정
class DatabaseConfig(BaseModel):
    """데이터베이스 설정 모델"""
    
    database_url: str = Field(default="sqlite:///data/manufacturing-copilot.db", env="DATABASE_URL")
    database_pool_size: int = Field(default=10, env="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=20, env="DATABASE_MAX_OVERFLOW")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class Settings(BaseSettings):
    """애플리케이션 설정 클래스"""
    
    # 기본 애플리케이션 설정
    app_name: str = "DX-AI Manufacturing Copilot"
    app_version: str = "0.1.0"
    debug: bool = Field(default=False, env="DEBUG")
    environment: str = Field(default="development", env="ENVIRONMENT")
    
    # 프로젝트 경로
    project_root: Path = Path(__file__).parent.parent.parent
    data_dir: Path = project_root / "data"
    fonts_dir: Path = project_root / "fonts"
    temp_dir: Path = project_root / "temp"
    
    # Ollama LLM 설정
    ollama_base_url: str = Field(default="http://localhost:11434", env="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="gemma3:12b-it-qat", env="OLLAMA_MODEL")
    ollama_timeout: int = Field(default=300, env="OLLAMA_TIMEOUT")
    ollama_max_retries: int = Field(default=3, env="OLLAMA_MAX_RETRIES")
    ollama_max_tokens: int = Field(default=4000, env="OLLAMA_MAX_TOKENS") 
    
    # 기본 LLM 모델
    default_llm_model: str = "gemma3:4b-it-qat"
    
    # 사용 가능한 LLM 모델 목록
    @property
    def available_llm_models(self) -> Dict[str, str]:
        """사용 가능한 LLM 모델 목록 반환"""
        return {
            "Gemma 3 (1B)": "gemma3:1b",
            "Gemma 3 (1B-QAT)": "gemma3:1b-it-qat",
            "Gemma 3 (4B)": "gemma3:4b",
            "Gemma 3 (4B-QAT)": "gemma3:4b-it-qat",
            "Gemma 3 (12B)": "gemma3:12b",
            "Gemma 3 (12B-QAT)": "gemma3:12b-it-qat",
            "Gemma 3 (27B)": "gemma3:27b",
            "Gemma 3 (27B-QAT)": "gemma3:27b-it-qat"
        }
    
    # LangChain 설정
    langchain_cache_enabled: bool = Field(default=True, env="LANGCHAIN_CACHE_ENABLED")
    langchain_verbose: bool = Field(default=False, env="LANGCHAIN_VERBOSE")
    langchain_debug: bool = Field(default=False, env="LANGCHAIN_DEBUG")
    
    # FAISS 벡터 스토어 설정
    faiss_index_path: str = Field(default="data/faiss_index", env="FAISS_INDEX_PATH")
    embedding_model: str = Field(default="all-MiniLM-L6-v2", env="EMBEDDING_MODEL")
    vector_dimension: int = Field(default=384, env="VECTOR_DIMENSION")
    
    # FastAPI 웹훅 설정
    webhook_host: str = Field(default="localhost", env="WEBHOOK_HOST")
    webhook_port: int = Field(default=8000, env="WEBHOOK_PORT")
    webhook_secret: str = Field(default="manufacturing-copilot-secret-key", env="WEBHOOK_SECRET")
    webhook_enabled: bool = Field(default=True, env="WEBHOOK_ENABLED")
    
    # Streamlit 설정
    streamlit_port: int = Field(default=8501, env="STREAMLIT_PORT")
    streamlit_host: str = Field(default="localhost", env="STREAMLIT_HOST")
    
    # 데이터 생성 설정
    default_lot_count: int = Field(default=100, env="DEFAULT_LOT_COUNT")
    default_equipment_count: int = Field(default=10, env="DEFAULT_EQUIPMENT_COUNT")
    max_data_points: int = Field(default=10000, env="MAX_DATA_POINTS")
    
    # 프로세스 관리 설정
    anomaly_threshold: float = Field(default=2.0, env="ANOMALY_THRESHOLD")
    alert_cooldown_minutes: int = Field(default=30, env="ALERT_COOLDOWN_MINUTES")
    equipment_check_interval: int = Field(default=60, env="EQUIPMENT_CHECK_INTERVAL")
    
    # 제품 개발 설정
    max_experiment_params: int = Field(default=20, env="MAX_EXPERIMENT_PARAMS")
    model_retrain_threshold: float = Field(default=0.1, env="MODEL_RETRAIN_THRESHOLD")
    prediction_confidence_threshold: float = Field(default=0.8, env="PREDICTION_CONFIDENCE_THRESHOLD")
    
    # 원가 관리 설정
    cost_optimization_iterations: int = Field(default=1000, env="COST_OPTIMIZATION_ITERATIONS")
    price_volatility_threshold: float = Field(default=0.15, env="PRICE_VOLATILITY_THRESHOLD")
    
    # 보안 설정
    secret_key: str = Field(default="manufacturing-copilot-super-secret-key", env="SECRET_KEY")
    access_token_expire_minutes: int = Field(default=1440, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # 로깅 설정
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="logs/manufacturing-copilot.log", env="LOG_FILE")
    log_rotation: str = Field(default="1 week", env="LOG_ROTATION")
    
    # 외부 API 설정
    external_api_timeout: int = Field(default=30, env="EXTERNAL_API_TIMEOUT")
    external_api_max_retries: int = Field(default=3, env="EXTERNAL_API_MAX_RETRIES")
    
    # 캐싱 설정
    cache_enabled: bool = Field(default=True, env="CACHE_ENABLED")
    cache_ttl: int = Field(default=3600, env="CACHE_TTL")  # 1시간
    
    # 데이터베이스 설정 (SQLite for demo)
    database_url: str = Field(default="sqlite:///data/manufacturing-copilot.db", env="DATABASE_URL")
    
    # 메트릭 및 모니터링
    metrics_enabled: bool = Field(default=True, env="METRICS_ENABLED")
    metrics_port: int = Field(default=8002, env="METRICS_PORT")
    
    # AI/ML 모델 설정
    model_save_path: str = Field(default="data/models", env="MODEL_SAVE_PATH")
    auto_model_save: bool = Field(default=True, env="AUTO_MODEL_SAVE")
    model_evaluation_interval: int = Field(default=24, env="MODEL_EVALUATION_INTERVAL")  # 시간
    
    # 실험 설계 설정
    doe_default_runs: int = Field(default=50, env="DOE_DEFAULT_RUNS")
    bayesian_opt_iterations: int = Field(default=25, env="BAYESIAN_OPT_ITERATIONS")
    
    # 알림 설정
    notification_channels: List[str] = Field(default=["console", "webhook"], env="NOTIFICATION_CHANNELS")
    email_notifications: bool = Field(default=False, env="EMAIL_NOTIFICATIONS")
    
    # 파일 업로드 설정
    max_file_size: int = Field(default=50 * 1024 * 1024, env="MAX_FILE_SIZE")  # 50MB
    allowed_file_types: List[str] = Field(
        default=[".csv", ".xlsx", ".json", ".txt"], 
        env="ALLOWED_FILE_TYPES"
    )
    
    # UI 설정
    default_theme: str = Field(default="light", env="DEFAULT_THEME")
    items_per_page: int = Field(default=20, env="ITEMS_PER_PAGE")
    chart_height: int = Field(default=400, env="CHART_HEIGHT")
    
    @validator("data_dir", "fonts_dir", "temp_dir", always=True)
    def create_directories(cls, v):
        """필요한 디렉토리 생성"""
        if isinstance(v, str):
            v = Path(v)
        v.mkdir(parents=True, exist_ok=True)
        return v
    
    @validator("log_level")
    def validate_log_level(cls, v):
        """로그 레벨 검증"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.upper()
    
    @validator("environment")
    def validate_environment(cls, v):
        """환경 설정 검증"""
        valid_envs = ["development", "staging", "production"]
        if v.lower() not in valid_envs:
            raise ValueError(f"Environment must be one of {valid_envs}")
        return v.lower()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        
    def get_ollama_config(self) -> Dict[str, Any]:
        """Ollama 설정 반환"""
        return {
            "base_url": self.ollama_base_url,
            "model": self.ollama_model,
            "timeout": self.ollama_timeout,
            "max_retries": self.ollama_max_retries,
            "available_models": self.available_llm_models
        }
    
    def get_model_display_name(self, model_id: str) -> str:
        """모델 ID로부터 표시 이름 반환"""
        for display_name, model_name in self.available_llm_models.items():
            if model_name == model_id:
                return display_name
        return model_id
    
    def is_ollama_model(self, model_id: str) -> bool:
        """Ollama 모델인지 확인"""
        return model_id.startswith("gemma3:")
    
    def is_external_model(self, model_id: str) -> bool:
        """외부 API 모델인지 확인 (Gemini, GPT 등)"""
        return model_id in ["gemini-2.5-pro", "gpt-4o-mini"]
    
    def get_model_size_category(self, model_id: str) -> str:
        """모델 크기 카테고리 반환"""
        if "1b" in model_id.lower():
            return "경량 (1B)"
        elif "4b" in model_id.lower():
            return "표준 (4B)"
        elif "12b" in model_id.lower():
            return "고성능 (12B)"
        elif "27b" in model_id.lower():
            return "최고성능 (27B)"
        elif "gemini" in model_id.lower():
            return "클라우드 (Gemini)"
        elif "gpt" in model_id.lower():
            return "클라우드 (GPT)"
        return "알 수 없음"
    
    def get_webhook_config(self) -> Dict[str, Any]:
        """웹훅 설정 반환"""
        return {
            "host": self.webhook_host,
            "port": self.webhook_port,
            "secret": self.webhook_secret,
            "enabled": self.webhook_enabled
        }
    
    def get_faiss_config(self) -> Dict[str, Any]:
        """FAISS 설정 반환"""
        return {
            "index_path": self.faiss_index_path,
            "embedding_model": self.embedding_model,
            "vector_dimension": self.vector_dimension
        }
    
    def is_production(self) -> bool:
        """프로덕션 환경 여부 확인"""
        return self.environment == "production"
    
    def is_development(self) -> bool:
        """개발 환경 여부 확인"""
        return self.environment == "development"


# 전역 설정 인스턴스
settings = Settings()

# 환경별 설정 오버라이드
if settings.is_development():
    settings.debug = True
    settings.langchain_verbose = True
    settings.log_level = "DEBUG"

# 필요한 디렉토리 생성
settings.data_dir.mkdir(parents=True, exist_ok=True)
settings.temp_dir.mkdir(parents=True, exist_ok=True)
(settings.project_root / "logs").mkdir(parents=True, exist_ok=True)
(settings.project_root / settings.model_save_path).mkdir(parents=True, exist_ok=True) 