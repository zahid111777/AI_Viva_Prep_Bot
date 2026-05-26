from pydantic import BaseModel
from typing import Optional, List


class ProviderStatus(BaseModel):
    name: str
    is_active: bool
    model: str
    has_user_key: bool = False


class ProviderSettingsResponse(BaseModel):
    providers: List[ProviderStatus]
    preferred_provider: str


class ProviderUpdateRequest(BaseModel):
    preferred_provider: Optional[str] = None
    groq_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None


class ProviderTestRequest(BaseModel):
    provider: str  # groq | openrouter | openai | gemini
    api_key: Optional[str] = None  # if not provided, uses stored key


class ProviderTestResponse(BaseModel):
    success: bool
    message: str
    provider: str
    model: str
