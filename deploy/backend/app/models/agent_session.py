"""Agent session tracking — records every AI agent operation for audit and rollback."""

from sqlalchemy import Column, DateTime, Integer, String, Text, JSON
from sqlalchemy.sql import func

from ..database import Base


class AgentSession(Base):
    """Record of an AI agent operation with approval workflow status.

    Tracks the full lifecycle: proposed → approved/rejected → executed.
    Enables audit trail and rollback for AI-driven network operations.
    """

    __tablename__ = "agent_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), index=True, nullable=False)
    tool_name = Column(String(64), nullable=False)
    input_params = Column(JSON, nullable=True)
    output_result = Column(JSON, nullable=True)
    status = Column(String(16), default="pending", index=True)
    approved_by = Column(Integer, nullable=True)
    summary = Column(String(256), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)
