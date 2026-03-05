from abc import ABC, abstractmethod
from typing import List, Dict, Any

class LLMProvider(ABC):
    """
    Abstract Base Class for LLM Providers (Local vs Cloud).
    """
    
    @abstractmethod
    async def generate(self, prompt: str, images: List[str] = None) -> Dict[str, Any]:
        """
        Generate response from LLM.
        
        Args:
            prompt: Text prompt
            images: List of base64 encoded strings or URLs
            
        Returns:
            Dict containing the structured response
        """
        pass
