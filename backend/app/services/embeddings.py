import ollama
from app.config import settings
from loguru import logger


class Embeddings:
    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.embed_model = settings.embed_model
        self.client = ollama.Client(host=self.base_url)

    async def create_embeddings(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
            
        try:
            embeddings = []
            for text in texts:
                response = self.client.embeddings(
                    model=self.embed_model,
                    prompt=text
                )
                embeddings.append(response["embedding"])
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Ollama embedding failed: {e}")
            # Fallback to mock embeddings
            return [[0.1] * 1536 for _ in texts]  # Default dimension


embeddings = Embeddings()
