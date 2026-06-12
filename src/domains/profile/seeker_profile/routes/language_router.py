from fastapi import APIRouter, Depends, Path
from src.core.response import APIResponse

from src.domains.profile.seeker_profile.schema.sub_schema import LanguageRequest
import src.domains.profile.seeker_profile.services.language_service as lang_service
from src.dependencies.dependencies import require_seeker

router = APIRouter(
    prefix="/api/seeker/profile/languages",
    tags=["Mobile - Seeker Languages"],
    dependencies=[Depends(require_seeker)]
)

@router.post("/", response_model=APIResponse[dict])
async def add_language_route(payload: LanguageRequest, current_user: dict = Depends(require_seeker)):
    user_id = current_user.get("id") or current_user.get("_id")
    result = await lang_service.add_language(str(user_id), payload)
    
    return APIResponse(success=True, message="Language added successfully", data=result)

@router.put("/{lang_id}", response_model=APIResponse[dict])
async def update_language_route(
    payload: LanguageRequest,
    lang_id: str = Path(...),
    current_user: dict = Depends(require_seeker)
):
    user_id = current_user.get("id") or current_user.get("_id")
    result = await lang_service.update_language(str(user_id), lang_id, payload)
    
    return APIResponse(success=True, message="Language updated successfully", data=result)

@router.delete("/{lang_id}", response_model=APIResponse[bool])
async def delete_language_route(lang_id: str = Path(...), current_user: dict = Depends(require_seeker)):
    user_id = current_user.get("id") or current_user.get("_id")
    await lang_service.delete_language(str(user_id), lang_id)
    
    return APIResponse(success=True, message="Language deleted successfully", data=True)