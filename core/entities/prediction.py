# core/entities/prediction.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
import uuid

class Prediction(BaseModel):
    """Represents a prediction request and its result."""
    id: Optional[int] = None  # Database ID
    # Unique identifier for API access
    uuid: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[int] = None  # Foreign key to User
    model_id: Optional[int] = None  # Foreign key to Model
    input_text: Optional[str] = None
    output_text: Optional[str] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_cost: Optional[float] = None
    status: str = 'pending'  # e.g., pending, processing, completed, failed
    # Automatically set on creation
    created_at: Optional[datetime] = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    queue_time: Optional[int] = None  # Time spent in queue (ms)
    process_time: Optional[int] = None  # Time spent processing (ms)

    # class Config:
    #     orm_mode = True
