# app/services/pulse_service.py
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.db.models import User, Pulse, Conversation, ChatMessage
from app.services.chatbot_client import call_lmstudio_chat
import logging

logger = logging.getLogger(__name__)

PULSE_GENERATION_PROMPT = """Your task is to generate a Professional Daily Pulse from the following chats, with the language that been used the most in these chats (French/English). Create a concise, structured summary focused exclusively on the user's professional activities and work-related conversations.

Focus on identifying:
✅ Key Projects & Meetings: What were the main projects, meetings, or professional topics discussed?
📌 Action Items & Deadlines: What are the specific tasks, follow-ups, or deadlines the user mentioned or was assigned?
💡 Key Decisions & Insights: What important decisions were made, strategies discussed, or professional insights gained?
🚫 Strictly Ignore: All personal, casual, or non-work-related conversations (e.g., small talk, personal plans, general news).

Output format:
🧭 Professional Pulse — [Date]
🔹 Main Projects / Meetings:
- ...
📋 Action Items / Deadlines:
- ...
💭 Key Decisions & Insights:
- ...
🕒 Summary Context:
(Brief sentence describing the user's primary work focus or challenges for the day)

If there is nothing important, respond with "Nothing important for now."
"""


async def generate_pulse_for_user(user_id: int, db_session: AsyncSession) -> Optional[str]:
    """
    Generate a daily pulse for a user by analyzing their last 10 conversations.
    
    Args:
        user_id: The user's ID
        db_session: Database session
        
    Returns:
        Generated pulse text or None if generation failed
    """
    try:
        logger.info(f"🔄 Generating pulse for user {user_id}")
        
        # Get last 5 conversations for this user (reduced from 10 to avoid context limits)
        conversations_result = await db_session.execute(
            select(Conversation)
            .where(
                Conversation.user_id == user_id,
                Conversation.is_active == True
            )
            .order_by(desc(Conversation.updated_at))
            .limit(5)
        )
        conversations = conversations_result.scalars().all()
        
        if not conversations:
            logger.info(f"No conversations found for user {user_id}")
            return "Nothing important for now."
        
        logger.info(f"Found {len(conversations)} conversations for user {user_id}")
        
        # Build context from all conversations
        conversations_text = ""
        total_messages = 0
        MAX_MESSAGE_LENGTH = 300  # Truncate long messages
        MAX_TOTAL_LENGTH = 4000   # Limit total context size (conservative to avoid 400 errors)
        
        for conv in conversations:
            # Get messages for this conversation
            messages_result = await db_session.execute(
                select(ChatMessage)
                .where(ChatMessage.conversation_id == conv.id)
                .order_by(ChatMessage.created_at)
            )
            messages = messages_result.scalars().all()
            
            if not messages:
                continue
            
            total_messages += len(messages)
            
            # Add conversation to context
            conv_title = conv.title or "Untitled Conversation"
            conversations_text += f"\n\n=== Conversation: {conv_title} ===\n"
            conversations_text += f"Date: {conv.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
            
            for msg in messages:
                if msg.role in ["user", "assistant"]:
                    role_label = "User" if msg.role == "user" else "Orion"
                    # Truncate long messages to avoid token limit
                    content = msg.content[:MAX_MESSAGE_LENGTH]
                    if len(msg.content) > MAX_MESSAGE_LENGTH:
                        content += "... (truncated)"
                    conversations_text += f"{role_label}: {content}\n\n"
                    
                    # Stop if context is getting too large
                    if len(conversations_text) > MAX_TOTAL_LENGTH:
                        conversations_text += "\n... (Additional conversations truncated to fit context limit)\n"
                        break
            
            # Break outer loop if we hit the limit
            if len(conversations_text) > MAX_TOTAL_LENGTH:
                break
        
        if not conversations_text.strip():
            logger.info(f"No messages found in conversations for user {user_id}")
            return "Nothing important for now."
        
        logger.info(f"Analyzing {total_messages} messages from {len(conversations)} conversations")
        logger.info(f"📊 Context size: {len(conversations_text)} characters (~{len(conversations_text)//4} tokens)")
        
        # Prepare messages for LLM
        messages = [
            {"role": "system", "content": PULSE_GENERATION_PROMPT},
            {"role": "user", "content": f"Here are all the conversations to analyze:\n{conversations_text}"}
        ]
        
        # Call LLM to generate pulse
        logger.info(f"Calling LLM to generate pulse...")
        try:
            response = await call_lmstudio_chat(messages, timeout=120)
        except Exception as llm_error:
            logger.error(f"LLM call failed: {llm_error}")
            # If it's a 400 error, likely context too large - return a message
            if "400" in str(llm_error):
                logger.error(f"Context size was {len(conversations_text)} chars - may be too large for model")
                return "Pulse generation failed: Context too large. Try reducing conversation history."
            raise
        
        # Extract pulse content
        if response and "choices" in response and len(response["choices"]) > 0:
            pulse_content = response["choices"][0].get("message", {}).get("content", "")
            
            if pulse_content:
                logger.info(f"✅ Pulse generated successfully ({len(pulse_content)} chars)")
                return pulse_content
            else:
                logger.warning("LLM returned empty pulse content")
                return "Nothing important for now."
        else:
            logger.error(f"Invalid LLM response structure: {response}")
            return "Nothing important for now."
            
    except Exception as e:
        logger.error(f"Failed to generate pulse for user {user_id}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None


async def update_user_pulse(user_id: int, db_session: AsyncSession) -> bool:
    """
    Generate and save/update pulse for a user.
    
    Args:
        user_id: The user's ID
        db_session: Database session
        
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"📊 Updating pulse for user {user_id}")
        
        # Generate pulse content
        pulse_content = await generate_pulse_for_user(user_id, db_session)
        
        if not pulse_content:
            logger.error(f"Failed to generate pulse for user {user_id}")
            return False
        
        # Check if user already has a pulse
        existing_pulse_result = await db_session.execute(
            select(Pulse).where(Pulse.user_id == user_id)
        )
        existing_pulse = existing_pulse_result.scalar_one_or_none()
        
        # Get conversation count for stats (match the generation limit)
        conv_count_result = await db_session.execute(
            select(Conversation)
            .where(
                Conversation.user_id == user_id,
                Conversation.is_active == True
            )
            .order_by(desc(Conversation.updated_at))
            .limit(5)
        )
        conversations = conv_count_result.scalars().all()
        
        # Count total messages
        total_messages = 0
        for conv in conversations:
            msg_count_result = await db_session.execute(
                select(ChatMessage).where(ChatMessage.conversation_id == conv.id)
            )
            total_messages += len(msg_count_result.scalars().all())
        
        now = datetime.utcnow()
        next_gen = now + timedelta(hours=24)
        
        if existing_pulse:
            # Update existing pulse
            existing_pulse.content = pulse_content
            existing_pulse.generated_at = now
            existing_pulse.next_generation = next_gen
            existing_pulse.conversations_analyzed = len(conversations)
            existing_pulse.messages_analyzed = total_messages
            logger.info(f"✅ Updated existing pulse for user {user_id}")
        else:
            # Create new pulse
            new_pulse = Pulse(
                user_id=user_id,
                content=pulse_content,
                generated_at=now,
                next_generation=next_gen,
                conversations_analyzed=len(conversations),
                messages_analyzed=total_messages
            )
            db_session.add(new_pulse)
            logger.info(f"✅ Created new pulse for user {user_id}")
        
        await db_session.commit()
        logger.info(f"💾 Pulse saved for user {user_id}. Next generation at {next_gen}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to update pulse for user {user_id}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        await db_session.rollback()
        return False


async def get_user_pulse(user_id: int, db_session: AsyncSession) -> Optional[dict]:
    """
    Get the current pulse for a user.
    
    Args:
        user_id: The user's ID
        db_session: Database session
        
    Returns:
        Pulse data dict or None if not found
    """
    try:
        result = await db_session.execute(
            select(Pulse).where(Pulse.user_id == user_id)
        )
        pulse = result.scalar_one_or_none()
        
        if not pulse:
            return None
        
        return {
            "content": pulse.content,
            "generated_at": pulse.generated_at.isoformat(),
            "next_generation": pulse.next_generation.isoformat(),
            "conversations_analyzed": pulse.conversations_analyzed,
            "messages_analyzed": pulse.messages_analyzed
        }
        
    except Exception as e:
        logger.error(f"Failed to get pulse for user {user_id}: {e}")
        return None

#This solution is designed totally by Liwa Cherif, an advanced AI solution
#You won't be able to understand it.