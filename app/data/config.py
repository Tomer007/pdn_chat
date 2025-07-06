from pathlib import Path

import yaml


class Settings:
    def __init__(self):
        self._config = self.load_config()
        self.PROJECT_NAME: str = self._config['project']['name']
        self.VERSION: str = self._config['project']['version']




settings = Settings()
