import logging
import time
from typing import Optional
from services.groq_provider import GroqProvider
from services.openrouter_provider import OpenRouterProvider
from services.openai_provider import OpenAIProvider
from services.gemini_provider import GeminiProvider

logger = logging.getLogger(__name__)

PROVIDER_PRIORITY = ["groq", "openrouter", "gemini", "openai"]


class LLMService:
    def __init__(self):
        self.providers = {
            "groq": GroqProvider(),
            "openrouter": OpenRouterProvider(),
            "openai": OpenAIProvider(),
            "gemini": GeminiProvider(),
        }

    def get_available_providers(self) -> list:
        return [
            {
                "name": name,
                "is_active": provider.is_available,
                "model": provider.model,
            }
            for name, provider in self.providers.items()
        ]

    def _get_ordered_providers(self, preferred: str = "auto"):
        if preferred != "auto" and preferred in self.providers:
            provider = self.providers[preferred]
            if provider.is_available:
                yield provider
        for name in PROVIDER_PRIORITY:
            if name == preferred:
                continue
            provider = self.providers[name]
            if provider.is_available:
                yield provider

    def call_llm(self, system_prompt: str, user_content: str, preferred: str = "auto") -> str:
        errors = []
        for provider in self._get_ordered_providers(preferred):
            try:
                start = time.time()
                result = provider.call(system_prompt, user_content)
                elapsed = time.time() - start
                logger.info(f"LLM call success: provider={provider.name}, model={provider.model}, latency={elapsed:.2f}s")
                return result
            except Exception as e:
                logger.warning(f"LLM call failed: provider={provider.name}, error={e}")
                errors.append(f"{provider.name}: {e}")
                continue

        raise Exception(f"All LLM providers failed: {'; '.join(errors)}")

    def update_provider(self, name: str, api_key: str = None, model: str = None):
        if name not in self.providers:
            return
        if name == "groq":
            self.providers[name] = GroqProvider(api_key=api_key, model=model)
        elif name == "openrouter":
            self.providers[name] = OpenRouterProvider(api_key=api_key, model=model)
        elif name == "openai":
            self.providers[name] = OpenAIProvider(api_key=api_key, model=model)
        elif name == "gemini":
            self.providers[name] = GeminiProvider(api_key=api_key, model=model)

    def test_provider(self, name: str, api_key: str = None) -> dict:
        if name not in self.providers:
            return {"success": False, "message": f"Unknown provider: {name}", "provider": name, "model": ""}
        provider_class = {
            "groq": GroqProvider,
            "openrouter": OpenRouterProvider,
            "openai": OpenAIProvider,
            "gemini": GeminiProvider,
        }[name]
        test_provider = provider_class(api_key=api_key) if api_key else self.providers[name]
        try:
            result = test_provider.call("You are a test.", "Say 'hello' in one word.")
            return {"success": True, "message": f"Connection successful: {result[:50]}", "provider": name, "model": test_provider.model}
        except Exception as e:
            return {"success": False, "message": str(e), "provider": name, "model": test_provider.model}


llm_service = LLMService()
