import yaml
from pathlib import Path


class Settings:
    def __init__(self):
        self._config = self.load_config()
        self.PROJECT_NAME: str = self._config['project']['name']
        self.VERSION: str = self._config['project']['version']


    def load_config(self):
        config_path = Path(__file__).parent / "config.yaml"
        with open(config_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)


settings = Settings()
