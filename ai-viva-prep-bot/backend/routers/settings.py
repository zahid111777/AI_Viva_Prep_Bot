from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from schemas.llm import ProviderSettingsResponse, ProviderUpdateRequest, ProviderTestRequest, ProviderTestResponse, ProviderStatus
from services.auth_service import get_current_user
from services.llm_service import llm_service
from services.encryption_service import encrypt_value, decrypt_value

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("/providers", response_model=ProviderSettingsResponse)
def get_providers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    providers_info = llm_service.get_available_providers()
    provider_statuses = []
    for p in providers_info:
        has_user_key = False
        if p["name"] == "groq" and current_user.encrypted_groq_key:
            has_user_key = True
        elif p["name"] == "openrouter" and current_user.encrypted_openrouter_key:
            has_user_key = True
        elif p["name"] == "openai" and current_user.encrypted_openai_key:
            has_user_key = True
        elif p["name"] == "gemini" and current_user.encrypted_gemini_key:
            has_user_key = True

        provider_statuses.append(ProviderStatus(
            name=p["name"],
            is_active=p["is_active"] or has_user_key,
            model=p["model"],
            has_user_key=has_user_key,
        ))

    return ProviderSettingsResponse(
        providers=provider_statuses,
        preferred_provider=current_user.preferred_provider,
    )


@router.put("/providers", response_model=ProviderSettingsResponse)
def update_providers(
    data: ProviderUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if data.preferred_provider is not None:
        current_user.preferred_provider = data.preferred_provider

    if data.groq_api_key is not None:
        current_user.encrypted_groq_key = encrypt_value(data.groq_api_key) if data.groq_api_key else None
    if data.openrouter_api_key is not None:
        current_user.encrypted_openrouter_key = encrypt_value(data.openrouter_api_key) if data.openrouter_api_key else None
    if data.openai_api_key is not None:
        current_user.encrypted_openai_key = encrypt_value(data.openai_api_key) if data.openai_api_key else None
    if data.gemini_api_key is not None:
        current_user.encrypted_gemini_key = encrypt_value(data.gemini_api_key) if data.gemini_api_key else None

    db.commit()
    db.refresh(current_user)
    return get_providers(db=db, current_user=current_user)


@router.post("/providers/test", response_model=ProviderTestResponse)
def test_provider(
    data: ProviderTestRequest,
    current_user: User = Depends(get_current_user),
):
    api_key = data.api_key
    if not api_key:
        key_map = {
            "groq": current_user.encrypted_groq_key,
            "openrouter": current_user.encrypted_openrouter_key,
            "openai": current_user.encrypted_openai_key,
            "gemini": current_user.encrypted_gemini_key,
        }
        encrypted = key_map.get(data.provider)
        if encrypted:
            api_key = decrypt_value(encrypted)

    result = llm_service.test_provider(data.provider, api_key)
    return ProviderTestResponse(**result)
