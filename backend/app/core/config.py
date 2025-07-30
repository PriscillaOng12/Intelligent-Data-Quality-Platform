from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import List, Union, Optional
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # Server Configuration
    SERVER_NAME: str = Field("localhost", env="SERVER_NAME")
    SERVER_HOST: str = Field("http://localhost", env="SERVER_HOST")
    BACKEND_CORS_ORIGINS: List[str] = Field(
        ["http://localhost:3000", "http://localhost:8000"],
        env="BACKEND_CORS_ORIGINS"
    )
    PROJECT_NAME: str = "Intelligent Data Quality Platform"
    DEBUG: bool = Field(False, env="DEBUG")
    
    # Database Configuration
    POSTGRES_SERVER: str = Field("localhost", env="POSTGRES_SERVER")
    POSTGRES_USER: str = Field("postgres", env="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field("password", env="POSTGRES_PASSWORD")
    POSTGRES_DB: str = Field("data_quality", env="POSTGRES_DB")
    POSTGRES_PORT: int = Field(5432, env="POSTGRES_PORT")
    
    # Redis Configuration
    REDIS_HOST: str = Field("localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(6379, env="REDIS_PORT")
    REDIS_PASSWORD: Optional[str] = Field(None, env="REDIS_PASSWORD")
    
    # Spark Configuration
    SPARK_MASTER: str = Field("local[*]", env="SPARK_MASTER")
    SPARK_APP_NAME: str = "DataQualityPlatform"
    SPARK_SQL_WAREHOUSE_DIR: str = Field("/tmp/spark-warehouse", env="SPARK_SQL_WAREHOUSE_DIR")
    
    # Delta Lake Configuration
    DELTA_LAKE_PATH: str = Field("/tmp/delta-lake", env="DELTA_LAKE_PATH")
    
    # Kafka Configuration
    KAFKA_BOOTSTRAP_SERVERS: str = Field("localhost:9092", env="KAFKA_BOOTSTRAP_SERVERS")
    KAFKA_CONSUMER_GROUP: str = "data-quality-platform"
    KAFKA_TOPICS: List[str] = ["data-quality-events", "data-lineage-events"]
    
    # MLflow Configuration
    MLFLOW_TRACKING_URI: str = Field("http://localhost:5000", env="MLFLOW_TRACKING_URI")
    MLFLOW_EXPERIMENT_NAME: str = "data-quality-models"
    
    # Storage Configuration
    DATA_STORAGE_PATH: str = Field("/tmp/data-quality-storage", env="DATA_STORAGE_PATH")
    
    # Alert Configuration
    ALERT_EMAIL_ENABLED: bool = Field(True, env="ALERT_EMAIL_ENABLED")
    ALERT_SLACK_ENABLED: bool = Field(False, env="ALERT_SLACK_ENABLED")
    SMTP_TLS: bool = Field(True, env="SMTP_TLS")
    SMTP_PORT: Optional[int] = Field(None, env="SMTP_PORT")
    SMTP_HOST: Optional[str] = Field(None, env="SMTP_HOST")
    SMTP_USER: Optional[str] = Field(None, env="SMTP_USER")
    SMTP_PASSWORD: Optional[str] = Field(None, env="SMTP_PASSWORD")
    SLACK_WEBHOOK_URL: Optional[str] = Field(None, env="SLACK_WEBHOOK_URL")
    
    # Monitoring Configuration
    PROMETHEUS_PORT: int = Field(8080, env="PROMETHEUS_PORT")
    ENABLE_METRICS: bool = Field(True, env="ENABLE_METRICS")
    
    # Performance Configuration
    MAX_WORKERS: int = Field(4, env="MAX_WORKERS")
    BATCH_SIZE: int = Field(1000, env="BATCH_SIZE")
    MAX_MEMORY_GB: int = Field(8, env="MAX_MEMORY_GB")
    
    # Quality Check Configuration
    DEFAULT_QUALITY_THRESHOLD: float = Field(0.95, env="DEFAULT_QUALITY_THRESHOLD")
    ANOMALY_DETECTION_SENSITIVITY: float = Field(0.1, env="ANOMALY_DETECTION_SENSITIVITY")
    ENABLE_REAL_TIME_CHECKS: bool = Field(True, env="ENABLE_REAL_TIME_CHECKS")
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    @property
    def database_url(self) -> str:
        """Construct database URL"""
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
    
    @property
    def redis_url(self) -> str:
        """Construct Redis URL"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}"
    
    class Config:
        case_sensitive = True
        env_file = ".env"


# Create global settings instance
settings = Settings()
