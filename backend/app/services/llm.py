import ollama
from app.config import settings
from loguru import logger


class LLM:
    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.model_name = settings.model_name
        self.client = ollama.Client(host=self.base_url)

    async def chat_completion(self, messages: list[dict]) -> str:
        try:
            # Convert OpenAI format to Ollama format
            prompt = self._convert_messages_to_prompt(messages)
            
            response = self.client.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                stream=False
            )
            
            return response["message"]["content"].strip()
            
        except Exception as e:
            logger.error(f"Ollama LLM call failed: {e}")
            # Fallback to mock response
            return "This is a mock response for testing purposes. The actual Ollama service is not available."

    def _convert_messages_to_prompt(self, messages: list[dict]) -> str:
        """Convert OpenAI message format to a single prompt string for Ollama"""
        prompt_parts = []
        
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        
        return "\n\n".join(prompt_parts)


llm = LLM()
