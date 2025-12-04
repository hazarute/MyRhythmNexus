from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from backend.api.deps import get_db, get_current_user
from backend.core.security import verify_password, create_access_token, hash_password
from backend.models.user import User, Role
from backend.schemas.token import Token
from backend.schemas.user import UserCreate, UserRead

router = APIRouter(tags=["auth"]) 

@router.post("/register", response_model=UserRead)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    # Check if user exists
    query = select(User).where(User.email == user_in.email)
    result = await db.execute(query)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    
    user = User(
        email=user_in.email,
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        phone_number=user_in.phone_number,
        password_hash=hash_password(user_in.password),
        is_active=user_in.is_active,
    )
    
    # Assign MEMBER role by default
    role_query = select(Role).where(Role.role_name == "MEMBER")
    role_result = await db.execute(role_query)
    role = role_result.scalar_one_or_none()
    if role:
        user.roles.append(role)
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # Load roles for response
    await db.execute(select(User).where(User.id == user.id).options(selectinload(User.roles)))
    return user

@router.post("/login/access-token", response_model=Token)
async def login_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).where(User.email == form_data.username, User.is_active == True)
    )
    user = result.scalar()
    if not user or not verify_password(form_data.password, str(user.password_hash)):
        raise HTTPException(
            status_code=400,
            detail="Incorrect email or password",
        )
    access_token = create_access_token(data={"sub": user.id})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/refresh-token", response_model=Token)
async def refresh_access_token(
    current_user: User = Depends(get_current_user),
):
    access_token = create_access_token(data={"sub": current_user.id})
    return {"access_token": access_token, "token_type": "bearer"}
