from pathlib import Path

import yaml


class Settings:
    def __init__(self):
        self._config = self.load_config()
        self.PROJECT_NAME: str = self._config['project']['name']
        self.VERSION: str = self._config['project']['version']
        
        # RAG Configuration
        self.CHROMA_DB_PERSIST_DIR: str = self._config['rag']['chroma_db_persist_dir']
        self.RAG_CHUNK_SIZE: int = self._config['rag']['chunk_size']
        self.RAG_CHUNK_OVERLAP: int = self._config['rag']['chunk_overlap']
        self.RAG_SEARCH_K: int = self._config['rag']['search_k']

    def load_config(self):
        config_path = Path(__file__).parent / "config.yaml"
        with open(config_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)


settings = Settings()
