from fastapi import APIRouter, Depends

from api.auth.dependencies import get_current_user
from api.models.user import User
from api.schemas.auth import UserOut

router = APIRouter(tags=["users"])


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(current_user)
