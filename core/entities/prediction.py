# core/entities/prediction.py
from dataclasses import dataclass, field
from datetime import datetime
import uuid

@dataclass
class Prediction:
    """Represents a prediction request and its result."""
    id: int | None = None # Database ID
    uuid: str = field(default_factory=lambda: str(uuid.uuid4())) # Unique identifier for API access
    user_id: int | None = None # Foreign key to User
    model_id: int | None = None # Foreign key to Model
    input_text: str | None = None
    output_text: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_cost: float | None = None
    status: str = 'pending' # e.g., pending, processing, completed, failed
    created_at: datetime | None = None
    completed_at: datetime | None = None
    queue_time: int | None = None # Time spent in queue (ms)
    process_time: int | None = None # Time spent processing (ms)
