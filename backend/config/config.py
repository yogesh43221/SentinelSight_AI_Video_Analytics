"""
Configuration management for SentinelSight
"""
import yaml
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class SystemConfig(BaseModel):
    fps_target: int = 15
    max_cameras: int = 4
    snapshot_retention_days: int = 30
    log_level: str = "INFO"
    snapshot_dir: str = "../data/snapshots"


class InferenceConfig(BaseModel):
    model: str = "yolov8n.pt"
    confidence_threshold: float = 0.5
    device: str = "cpu"
    classes: List[int] = [0, 2]  # person, car


class MQTTConfig(BaseModel):
    enabled: bool = True
    broker: str = "localhost"
    port: int = 1883
    topic_prefix: str = "sentinelsight"
    qos: int = 1


class DatabaseConfig(BaseModel):
    url: str = "sqlite:///../data/sentinelsight.db"


class RuleConfig(BaseModel):
    enabled: bool = True
    priority: str = "medium"
    description: str = ""
    threshold_seconds: Optional[int] = None


class Config(BaseModel):
    system: SystemConfig = SystemConfig()
    inference: InferenceConfig = InferenceConfig()
    mqtt: MQTTConfig = MQTTConfig()
    database: DatabaseConfig = DatabaseConfig()
    cameras: List[dict] = []
    rules: dict = {}


def load_config(config_path: str = None) -> Config:
    """Load configuration from YAML file"""
    if config_path is None:
        # Try multiple possible locations
        possible_paths = [
            Path("config/config.yaml"),  # From project root
            Path("../config/config.yaml"),  # From backend dir
            Path(__file__).parent.parent.parent / "config" / "config.yaml",  # Absolute from this file
        ]
        config_file = None
        for p in possible_paths:
            if p.exists():
                config_file = p
                break
    else:
        config_file = Path(config_path)
    
    if config_file is None or not config_file.exists():
        logger.warning(f"Config file not found, using defaults")
        return Config()
    
    try:
        with open(config_file, 'r') as f:
            config_data = yaml.safe_load(f)
        
        config = Config(**config_data)
        logger.info(f"Configuration loaded from {config_path}")
        return config
    
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        logger.warning("Using default configuration")
        return Config()


# Global config instance
_config = None


def get_config() -> Config:
    """Get global configuration instance"""
    global _config
    if _config is None:
        _config = load_config()
    return _config
