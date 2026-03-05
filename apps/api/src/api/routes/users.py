import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.dependencies import get_current_user, require_role
from api.db.session import get_session
from api.models.user import User
from api.schemas.auth import UserOut
from api.schemas.pagination import PaginatedResponse
from api.schemas.user import (
    AcceptInviteRequest,
    UserAdminOut,
    UserInviteCreate,
    UserInviteResponse,
    UserUpdate,
)
from api.services.user import _svc

router = APIRouter(tags=["users"])


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(current_user)


@router.post("/users/invite", response_model=UserInviteResponse, status_code=201)
async def invite_user(
    payload: UserInviteCreate,
    actor: User = Depends(require_role(["admin"])),
    session: AsyncSession = Depends(get_session),
) -> UserInviteResponse:
    return await _svc.invite_user(session, payload, actor)


@router.post("/users/accept-invite", response_model=UserAdminOut, status_code=201)
async def accept_invite(
    payload: AcceptInviteRequest,
    session: AsyncSession = Depends(get_session),
) -> UserAdminOut:
    return await _svc.accept_invite(session, payload)


@router.get("/users", response_model=PaginatedResponse[UserAdminOut])
async def list_users(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _actor: User = Depends(require_role(["admin"])),
    session: AsyncSession = Depends(get_session),
) -> PaginatedResponse[UserAdminOut]:
    return await _svc.list_users(session, limit=limit, offset=offset)


@router.patch("/users/{user_id}", response_model=UserAdminOut)
async def update_user(
    user_id: uuid.UUID,
    payload: UserUpdate,
    actor: User = Depends(require_role(["admin"])),
    session: AsyncSession = Depends(get_session),
) -> UserAdminOut:
    return await _svc.update_user(session, user_id, payload, actor)
