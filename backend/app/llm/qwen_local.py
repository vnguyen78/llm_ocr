import os
import httpx
from typing import List, Dict, Any
from .provider_interface import LLMProvider

class QwenLocalProvider(LLMProvider):
    """
    Concrete implementation for Local Qwen 2.5 VL via LM Studio.
    """
    
    def __init__(self):
        self.base_url = os.getenv("LLM_BASE_URL", "http://localhost:1234/v1")
        self.api_key = os.getenv("LLM_API_KEY", "lm-studio")
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=120.0  # Long timeout for Vision tasks
        )
        
    async def generate(self, prompt: str, images: List[str] = None) -> Dict[str, Any]:
        """
        Call Qwen 2.5 VL via OpenAI-compatible Chat Completions API.
        """
        messages = []
        
        # Construct User Message
        content = [{"type": "text", "text": prompt}]
        
        if images:
            for img in images:
                # Assuming img is a base64 string or URL
                content.append({
                    "type": "image_url",
                    "image_url": {"url": img}
                })
                
        messages.append({"role": "user", "content": content})
        
        try:
            response = await self.client.post(
                "/chat/completions",
                json={
                    "model": "qwen-2.5-vl",  # This might need adjustment based on LM Studio model name
                    "messages": messages,
                    "temperature": 0.1, # Low temperature for OCR
                    "max_tokens": 1000
                },
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPError as e:
            print(f"LLM Connection Error: {e}")
            raise e
