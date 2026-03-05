from abc import ABC, abstractmethod
import base64
from typing import Dict, Any, Optional
from openai import AsyncOpenAI
from app.config import settings
from app.models.claim import TileType

class LLMProvider(ABC):
    @abstractmethod
    async def extract_from_tile(self, image_path: str, context: TileType) -> Dict[str, Any]:
        pass

class QwenLocalProvider(LLMProvider):
    def __init__(self):
        self.client = AsyncOpenAI(
            base_url=settings.LLM_BASE_URL,
            api_key=settings.LLM_API_KEY,
            timeout=300.0 # Increased timeout for slow local LLM
        )
        self.model = settings.LLM_MODEL

    def _encode_image(self, image_path: str) -> str:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def _get_context_prompt(self, context: TileType) -> str:
        if context == TileType.HEADER:
            return "Focus on extracting: Hospital Name, Patient ID, Date of Service. Ignore body line items."
        elif context == TileType.BODY:
            return "Focus on extracting: Detailed line items, service descriptions, and amounts. Ignore headers/footers."
        elif context == TileType.FOOTER:
            return "Focus on extracting: Physician signatures, diagnosis codes (ICD-10), and HANDWRITTEN notes."
        return "Extract all visible text and fields."

    async def extract_from_tile(self, image_path: str, context: TileType) -> Dict[str, Any]:
        base64_image = self._encode_image(image_path)
        context_instruction = self._get_context_prompt(context)

        system_prompt = (
            "You are a Forensic Claim Extractor. "
            "Your task is to extract structured data from the provided image tile. "
            f"{context_instruction} "
            "Double check that the sum of line items matches the total amount. "
            "\n\n"
            "### RULES:\n"
            "1. **Never return empty values** for fields that clearly exist in the text, even if messy.\n"
            "2. **Best Guess**: If text is ambiguous, provide your best guess and set `confidence` to 0.1.\n"
            "3. **Needs Review**: If you have to guess, set `needs_review: true`.\n"
            "4. **OMIT MISSING FIELDS**: Do NOT return keys for fields that are not present. Only return fields found in the document.\n"
            "\n"
            "### ONE-SHOT EXAMPLE:\n"
            "**Input Text**:\n"
            "'Doctor Referral Letter with diagnosis... Dermatologist (皮膚科)... 鑒明及授權書... I hereby declare...'\n"
            "**Correct Output**:\n"
            "{\n"
            "  'raw_transcription': 'Doctor Referral Letter...',\n"
            "  'fields': {\n"
            "    'Specialist_Consultation': { 'value': 'Dermatologist (皮膚科)', 'confidence': 0.9, 'needs_review': false },\n"
            "    'Declaration': { 'value': 'I hereby declare...', 'confidence': 0.95, 'needs_review': false }\n"
            "  }\n"
            "}\n"
            "\n"
            "Output strictly valid JSON with the following structure: "
            "{ 'raw_transcription': '...', 'fields': { 'field_name': { 'value': '...', 'confidence': 0.0-1.0, 'needs_review': bool } } }"
        )

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Extract data from this tile."},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                },
                            },
                        ],
                    }
                ],
                # response_format={"type": "json_object"}, 
                # Note: 'json_object' mode depends on backend support. 
                # If Qwen/Ollama doesn't support it strictly, we might need to rely on prompt engineering.
            )
            
            content = response.choices[0].message.content
            import json
            return json.loads(content)
        except Exception as e:
            # Log error
            print(f"LLM Extraction failed: {e}")
            return {"error": str(e), "fields": []}
