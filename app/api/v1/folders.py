from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.db.database import get_db
from app.db.models import Folder, Conversation, User
from app.api.v1.auth import get_current_user
from app.utils.logging import logger

router = APIRouter()

# --- Schemas ---

class FolderCreate(BaseModel):
    name: str

class FolderUpdate(BaseModel):
    name: str

class FolderResponse(BaseModel):
    id: int
    name: str
    created_at: datetime
    updated_at: datetime
    # Optionally include conversation IDs or count if needed
    
    class Config:
        from_attributes = True

# --- Endpoints ---

@router.get("/", response_model=List[FolderResponse])
async def get_folders(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all folders for the authenticated user and their conversations."""
    result = await db.execute(
        select(Folder)
        .where(Folder.user_id == current_user.id)
        .order_by(Folder.created_at.desc())
    )
    folders = result.scalars().all()
    return folders

@router.post("/", response_model=FolderResponse)
async def create_folder(
    folder_data: FolderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new folder."""
    if not folder_data.name.strip():
        raise HTTPException(status_code=400, detail="Folder name cannot be empty")
        
    folder = Folder(
        user_id=current_user.id,
        name=folder_data.name.strip()
    )
    db.add(folder)
    try:
        await db.commit()
        await db.refresh(folder)
        return folder
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create folder: {e}")
        raise HTTPException(status_code=500, detail="Failed to create folder")

@router.put("/{folder_id}", response_model=FolderResponse)
async def update_folder(
    folder_id: int,
    folder_data: FolderUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Rename a folder."""
    result = await db.execute(
        select(Folder).where(
            Folder.id == folder_id,
            Folder.user_id == current_user.id
        )
    )
    folder = result.scalar_one_or_none()
    
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
        
    if not folder_data.name.strip():
        raise HTTPException(status_code=400, detail="Folder name cannot be empty")
        
    folder.name = folder_data.name.strip()
    folder.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(folder)
    return folder

@router.delete("/{folder_id}")
async def delete_folder(
    folder_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a folder.
    DEFAULT BEHAVIOR: Preserves conversations by setting their folder_id to NULL.
    """
    # 1. Verify existence
    result = await db.execute(
        select(Folder).where(
            Folder.id == folder_id,
            Folder.user_id == current_user.id
        )
    )
    folder = result.scalar_one_or_none()
    
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")

    try:
        # 2. Unlink conversations (Set folder_id = NULL)
        # Using UPDATE statement for efficiency
        await db.execute(
            update(Conversation)
            .where(Conversation.folder_id == folder_id)
            .values(folder_id=None)
        )
        
        # 3. Delete folder
        await db.delete(folder)
        await db.commit()
        
        return {"status": "ok", "message": "Folder deleted, conversations preserved"}
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to delete folder {folder_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete folder")
