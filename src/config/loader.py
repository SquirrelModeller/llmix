import logging
import yaml
from src.config.settings import AppConfig

logger = logging.getLogger(__name__)

def load_config(path: str) -> AppConfig:
    try:
        with open(path, 'r', encoding="utf-8") as f:
            config_dict = yaml.safe_load(f)
        return AppConfig(**config_dict)
    except Exception as e:
        logger.error("Failed to load configuration: %s", e)
        raise
