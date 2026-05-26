import requests
import logging
import os
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class OpenAIProvider:
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.base_url = "https://api.openai.com/v1/chat/completions"
        self.name = "openai"

    @property
    def is_available(self) -> bool:
        return bool(self.api_key)

    def call(self, system_prompt: str, user_content: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "temperature": 0.7,
            "max_tokens": 8000,
        }
        response = requests.post(self.base_url, headers=headers, json=payload, timeout=120)
        if response.status_code == 429:
            raise Exception("Rate limited")
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
