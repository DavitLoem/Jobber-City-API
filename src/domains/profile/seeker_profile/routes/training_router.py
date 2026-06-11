from fastapi import APIRouter, Depends, Path
from src.core.response import APIResponse

from src.domains.profile.seeker_profile.schema.sub_schema import TrainingRequest
import src.domains.profile.seeker_profile.services.training_service as train_service
from src.dependencies.dependencies import require_seeker

router = APIRouter(
    prefix="/api/seeker/profile/trainings",
    tags=["Seeker - Profile Trainings"],
    dependencies=[Depends(require_seeker)]
)

@router.post("/", response_model=APIResponse[dict])
async def add_training_route(payload: TrainingRequest, current_user: dict = Depends(require_seeker)):
    user_id = current_user.get("id") or current_user.get("_id")
    result = await train_service.add_training(str(user_id), payload)
    return APIResponse(success=True, message="Training added successfully", data=result)

@router.put("/{train_id}", response_model=APIResponse[dict])
async def update_training_route(
    payload: TrainingRequest,
    train_id: str = Path(...),
    current_user: dict = Depends(require_seeker)
):
    user_id = current_user.get("id") or current_user.get("_id")
    result = await train_service.update_training(str(user_id), train_id, payload)
    return APIResponse(success=True, message="Training updated successfully", data=result)

@router.delete("/{train_id}", response_model=APIResponse[bool])
async def delete_training_route(train_id: str = Path(...), current_user: dict = Depends(require_seeker)):
    user_id = current_user.get("id") or current_user.get("_id")
    await train_service.delete_training(str(user_id), train_id)
    return APIResponse(success=True, message="Training deleted successfully", data=True)