from pathlib import Path
from typing import Dict, Any

import yaml


class Settings:
    def __init__(self):
        self._config = self.load_config()
        self.PROJECT_NAME: str = self._config['project']['name']
        self.VERSION: str = self._config['project']['version']

    def load_config() -> Dict[str, Any]:
        """
        Load configuration from config.yaml file.
        """
        config_file = Path(__file__).parent / "config.yaml"
        with open(config_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)


settings = Settings()

# For backwards compatibility
load_config = settings.load_config
