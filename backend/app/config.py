from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_env: str = "dev"
    host: str = "0.0.0.0"
    port: int = 8000

    # LLM settings (Ollama - Self Hosted)
    ollama_base_url: str = "http://localhost:11434"
    model_name: str = "llama3.2:3b"
    embed_model: str = "nomic-embed-text"

    vector_store: str = "qdrant"
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = None
    qdrant_collection: str = "chunks"
    embedding_dim: int = 1536
    qdrant_distance: str = "Cosine"

    jwt_secret: str = "dev_secret_key_change_in_production"
    jwt_expire_min: int = 60

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
