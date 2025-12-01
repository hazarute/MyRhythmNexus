from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload

from backend.api.deps import get_db
from backend.core.security import hash_password
from backend.models.user import User, Role, Instructor, UserRole
from backend.schemas.user import UserCreate, UserRead, UserUpdate

router = APIRouter()

@router.get("/", response_model=List[UserRead])
async def list_staff(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List staff members with optional search"""
    # Filter users with role ADMIN or INSTRUCTOR
    query = (
        select(User)
        .join(UserRole, User.id == UserRole.user_id)
        .join(Role, UserRole.role_id == Role.id)
        .where(Role.role_name.in_(["ADMIN", "INSTRUCTOR"]))
        .options(selectinload(User.roles))
        .distinct()
    )
    
    # Apply search filter if provided
    if search:
        search_term = f"%{search.lower()}%"
        query = query.where(
            or_(
                User.first_name.ilike(search_term),
                User.last_name.ilike(search_term),
                User.email.ilike(search_term),
                User.phone_number.ilike(search_term)
            )
        )
    
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    users = result.scalars().all()
    return users

@router.post("/", response_model=UserRead)
async def create_staff(
    user_in: UserCreate,
    role_name: str = "INSTRUCTOR", # Default to INSTRUCTOR, can be ADMIN
    db: AsyncSession = Depends(get_db)
):
    if role_name not in ["ADMIN", "INSTRUCTOR"]:
        raise HTTPException(status_code=400, detail="Invalid role for staff.")

    # Check if user exists
    query = select(User).where(User.email == user_in.email)
    result = await db.execute(query)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists.",
        )
    
    user = User(
        email=user_in.email,
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        phone_number=user_in.phone_number,
        password_hash=hash_password(user_in.password),
        is_active=user_in.is_active,
    )
    
    # Assign Role
    role_query = select(Role).where(Role.role_name == role_name)
    role_result = await db.execute(role_query)
    role = role_result.scalar_one_or_none()
    
    if not role:
        # Create role if not exists (should exist from seed, but just in case)
        role = Role(role_name=role_name)
        db.add(role)
        await db.commit()
        await db.refresh(role)
        
    user.roles.append(role)
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # Load roles for response
    await db.execute(select(User).where(User.id == user.id).options(selectinload(User.roles)))
    return user

@router.get("/instructors", response_model=List[UserRead])
async def list_instructors(
    db: AsyncSession = Depends(get_db)
):
    """Get all instructors (users with INSTRUCTOR role)"""
    query = (
        select(User)
        .join(UserRole, User.id == UserRole.user_id)
        .join(Role, UserRole.role_id == Role.id)
        .where(Role.role_name == "INSTRUCTOR")
        .options(selectinload(User.roles))
        .distinct()
    )
    
    result = await db.execute(query)
    instructors = result.scalars().all()
    return instructors

@router.patch("/{staff_id}", response_model=UserRead)
async def update_staff(
    staff_id: str,
    user_in: UserUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a staff member"""
    # Get the staff member
    query = select(User).where(User.id == staff_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=404,
            detail="Staff member not found.",
        )
    
    # Check if new email is already used by another user
    if user_in.email and user_in.email != user.email:
        email_query = select(User).where(User.email == user_in.email)
        email_result = await db.execute(email_query)
        if email_result.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail="The user with this email already exists.",
            )
    
    # Update fields if provided
    if user_in.first_name is not None:
        user.first_name = user_in.first_name
    if user_in.last_name is not None:
        user.last_name = user_in.last_name
    if user_in.email is not None:
        user.email = user_in.email
    if user_in.phone_number is not None:
        user.phone_number = user_in.phone_number
    if user_in.is_active is not None:
        user.is_active = user_in.is_active
    if user_in.password is not None:
        user.password_hash = hash_password(user_in.password)
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # Load roles for response
    await db.execute(select(User).where(User.id == staff_id).options(selectinload(User.roles)))
    return user

@router.delete("/{staff_id}")
async def delete_staff(
    staff_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a staff member"""
    # Get the staff member
    query = select(User).where(User.id == staff_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=404,
            detail="Staff member not found.",
        )
    
    # Delete the user
    await db.delete(user)
    await db.commit()
    
    return {"message": "Staff member deleted successfully"}
