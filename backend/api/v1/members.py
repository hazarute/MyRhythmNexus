from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
from backend.core.time_utils import get_turkey_time

from backend.api.deps import get_db, get_current_active_admin
from backend.core.security import hash_password
from backend.models.user import User, Role
from backend.schemas.user import UserCreate, UserRead, UserUpdate

router = APIRouter()

@router.get("/pending", response_model=List[UserRead])
async def list_pending_members(
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_active_admin)
):
    """List pending member approvals (inactive users created within last 18 hours)"""
    # Calculate 18 hours ago using Turkey time
    turkey_now = get_turkey_time()
    eighteen_hours_ago = turkey_now - timedelta(hours=18)
    
    query = (
        select(User)
        .where(User.is_active == False, User.created_at >= eighteen_hours_ago)
        .order_by(User.created_at.desc())
        .options(selectinload(User.roles))  # Add this back for proper serialization
    )
    
    result = await db.execute(query)
    users = result.scalars().all()
    return users

@router.get("/", response_model=List[UserRead])
async def list_members(
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_db)
):
    # Filter by role="MEMBER", optionally include inactive users, order by updated_at DESC
    query = (
        select(User)
        .join(User.roles)
        .where(Role.role_name == "MEMBER")
        .order_by(User.updated_at.desc())
        .options(selectinload(User.roles))
    )
    
    if not include_inactive:
        query = query.where(User.is_active == True)

    if search:
        search_filter = or_(
            User.first_name.ilike(f"%{search}%"),
            User.last_name.ilike(f"%{search}%"),
            User.email.ilike(f"%{search}%"),
            User.phone_number.ilike(f"%{search}%")
        )
        query = query.where(search_filter)

    query = query.offset(skip).limit(limit).distinct()
    
    result = await db.execute(query)
    users = result.scalars().all()
    return users

@router.post("/", response_model=UserRead)
async def create_member(
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
    
    # Assign MEMBER role
    role_query = select(Role).where(Role.role_name == "MEMBER")
    role_result = await db.execute(role_query)
    member_role = role_result.scalar_one_or_none()
    
    if not member_role:
        # Create role if not exists
        member_role = Role(role_name="MEMBER")
        db.add(member_role)
        await db.flush()
        
    user.roles.append(member_role)
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # Load roles for response
    await db.execute(select(User).where(User.id == user.id).options(selectinload(User.roles)))
    return user

@router.get("/{user_id}", response_model=UserRead)
async def get_member(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    user = await db.get(User, user_id, options=[selectinload(User.roles)])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/{user_id}", response_model=UserRead)
async def update_member(
    user_id: str,
    user_in: UserUpdate,
    db: AsyncSession = Depends(get_db)
):
    user = await db.get(User, user_id, options=[selectinload(User.roles)])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    update_data = user_in.model_dump(exclude_unset=True)
    if "password" in update_data and update_data["password"]:
        hashed_password = hash_password(update_data["password"])
        del update_data["password"]
        user.password_hash = hashed_password
        
    # Eğer is_active güncelleniyorsa, updated_at'i Türkiye saati ile güncelle
    if "is_active" in update_data:
        user.updated_at = get_turkey_time()
    
    for field, value in update_data.items():
        setattr(user, field, value)
        
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # Load roles for response
    await db.execute(select(User).where(User.id == user.id).options(selectinload(User.roles)))
    return user

@router.delete("/{user_id}")
async def delete_member(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    user = await db.get(User, user_id, options=[selectinload(User.roles)])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        # Use the model's hard_delete method for proper separation of concerns
        await user.hard_delete(db)
        await db.commit()
        
        return {"message": "Member deleted successfully"}
    
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")
