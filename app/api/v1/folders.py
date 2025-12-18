from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.db.database import get_db
from app.db.models import Folder, Conversation, User
from app.utils.logging import logger

router = APIRouter()

# --- Schemas ---

class FolderCreate(BaseModel):
    user_id: int
    name: str

class FolderUpdate(BaseModel):
    name: Optional[str] = None
    conversation_ids: Optional[List[int]] = None  # Optional - replace entire array

class FolderResponse(BaseModel):
    id: int
    user_id: int
    name: str
    conversation_ids: List[int]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class AddConversationRequest(BaseModel):
    conversation_id: int

# --- Helper Functions ---

async def get_folder_with_conversations(folder: Folder, db: AsyncSession) -> FolderResponse:
    """Build FolderResponse with conversation_ids from the relationship."""
    # Get conversations for this folder
    result = await db.execute(
        select(Conversation.id).where(
            Conversation.folder_id == folder.id,
            Conversation.is_active == True
        )
    )
    conversation_ids = [row[0] for row in result.fetchall()]
    
    return FolderResponse(
        id=folder.id,
        user_id=folder.user_id,
        name=folder.name,
        conversation_ids=conversation_ids,
        created_at=folder.created_at,
        updated_at=folder.updated_at
    )

# --- Endpoints ---

@router.get("/{user_id}", response_model=List[FolderResponse])
async def get_user_folders(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get all folders for a user."""
    # Verify user exists
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get folders
    result = await db.execute(
        select(Folder)
        .where(Folder.user_id == user_id)
        .order_by(Folder.created_at.desc())
    )
    folders = result.scalars().all()
    
    # Build response with conversation_ids
    response = []
    for folder in folders:
        folder_response = await get_folder_with_conversations(folder, db)
        response.append(folder_response)
    
    return response


@router.post("", response_model=FolderResponse)
async def create_folder(
    folder_data: FolderCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new folder."""
    # Verify user exists
    user_result = await db.execute(select(User).where(User.id == folder_data.user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not folder_data.name.strip():
        raise HTTPException(status_code=400, detail="Folder name cannot be empty")
        
    folder = Folder(
        user_id=folder_data.user_id,
        name=folder_data.name.strip()
    )
    db.add(folder)
    try:
        await db.commit()
        await db.refresh(folder)
        
        return FolderResponse(
            id=folder.id,
            user_id=folder.user_id,
            name=folder.name,
            conversation_ids=[],
            created_at=folder.created_at,
            updated_at=folder.updated_at
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create folder: {e}")
        raise HTTPException(status_code=500, detail="Failed to create folder")


@router.put("/{user_id}/{folder_id}", response_model=FolderResponse)
async def update_folder(
    user_id: int,
    folder_id: int,
    folder_update: FolderUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a folder (name and/or conversation_ids)."""
    # Get folder and verify ownership
    result = await db.execute(
        select(Folder).where(
            Folder.id == folder_id,
            Folder.user_id == user_id
        )
    )
    folder = result.scalar_one_or_none()
    
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    # Update name if provided
    if folder_update.name is not None:
        if not folder_update.name.strip():
            raise HTTPException(status_code=400, detail="Folder name cannot be empty")
        folder.name = folder_update.name.strip()
    
    # Update conversation_ids if provided (replace entire array)
    if folder_update.conversation_ids is not None:
        # First, remove all conversations from this folder
        await db.execute(
            update(Conversation)
            .where(Conversation.folder_id == folder_id)
            .values(folder_id=None)
        )
        
        # Then, add the new conversations to this folder
        if folder_update.conversation_ids:
            # Verify conversations exist and belong to the user
            for conv_id in folder_update.conversation_ids:
                conv_result = await db.execute(
                    select(Conversation).where(
                        Conversation.id == conv_id,
                        Conversation.user_id == user_id,
                        Conversation.is_active == True
                    )
                )
                conv = conv_result.scalar_one_or_none()
                if conv:
                    conv.folder_id = folder_id
    
    folder.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(folder)
    
    return await get_folder_with_conversations(folder, db)


@router.delete("/{user_id}/{folder_id}")
async def delete_folder(
    user_id: int,
    folder_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a folder.
    Conversations are NOT deleted - they just become unfiled (folder_id = NULL).
    """
    # Verify folder exists and belongs to user
    result = await db.execute(
        select(Folder).where(
            Folder.id == folder_id,
            Folder.user_id == user_id
        )
    )
    folder = result.scalar_one_or_none()
    
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")

    try:
        # Unlink conversations (Set folder_id = NULL)
        await db.execute(
            update(Conversation)
            .where(Conversation.folder_id == folder_id)
            .values(folder_id=None)
        )
        
        # Delete folder
        await db.delete(folder)
        await db.commit()
        
        return {"status": "ok", "message": "Folder deleted successfully"}
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to delete folder {folder_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete folder")


@router.post("/{user_id}/{folder_id}/conversations", response_model=FolderResponse)
async def add_conversation_to_folder(
    user_id: int,
    folder_id: int,
    request: AddConversationRequest,
    db: AsyncSession = Depends(get_db)
):
    """Add a conversation to a folder."""
    # Verify folder exists and belongs to user
    folder_result = await db.execute(
        select(Folder).where(
            Folder.id == folder_id,
            Folder.user_id == user_id
        )
    )
    folder = folder_result.scalar_one_or_none()
    
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    # Verify conversation exists and belongs to user
    conv_result = await db.execute(
        select(Conversation).where(
            Conversation.id == request.conversation_id,
            Conversation.user_id == user_id,
            Conversation.is_active == True
        )
    )
    conversation = conv_result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Add conversation to folder (update folder_id)
    conversation.folder_id = folder_id
    folder.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(folder)
    
    return await get_folder_with_conversations(folder, db)


@router.delete("/{user_id}/{folder_id}/conversations/{conversation_id}", response_model=FolderResponse)
async def remove_conversation_from_folder(
    user_id: int,
    folder_id: int,
    conversation_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Remove a conversation from a folder (unfiled, not deleted)."""
    # Verify folder exists and belongs to user
    folder_result = await db.execute(
        select(Folder).where(
            Folder.id == folder_id,
            Folder.user_id == user_id
        )
    )
    folder = folder_result.scalar_one_or_none()
    
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    # Verify conversation exists and belongs to this folder
    conv_result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id,
            Conversation.folder_id == folder_id,
            Conversation.is_active == True
        )
    )
    conversation = conv_result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found in this folder")
    
    # Remove conversation from folder (set folder_id to NULL)
    conversation.folder_id = None
    folder.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(folder)
    
    return await get_folder_with_conversations(folder, db)
