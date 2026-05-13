import yaml
from pathlib import Path


class Settings:
    """Settings class is currently unused and has no config.yaml to load.
    Disabled to prevent AttributeError on import (self._config was never defined).
    If needed in the future, provide a config.yaml and initialize self._config
    before referencing it.
    """
    def __init__(self):
        config_path = Path(__file__).parent / 'config.yaml'
        if config_path.exists():
            with open(config_path) as f:
                self._config = yaml.safe_load(f) or {}
        else:
            self._config = {'project': {'name': 'pdn_chat', 'version': '1.0'}}
        self.PROJECT_NAME: str = self._config['project']['name']
        self.VERSION: str = self._config['project']['version']


# Disabled: Settings class is not used anywhere in the project.
# Instantiation was causing AttributeError on import because self._config
# was never defined before being referenced.
# settings = Settings()
