# core/entities/queue_item.py
from dataclasses import dataclass
from datetime import datetime

@dataclass
class QueueItem:
    """Represents an item in the prediction processing queue."""
    id: int | None = None # Database ID
    prediction_id: int | None = None # Foreign key to Prediction (should be unique in this table)
    user_id: int | None = None # Foreign key to User (for fairness logic)
    priority: int = 0 # Priority level (higher value means higher priority, though we might not use it initially)
    status: str = 'waiting' # e.g., waiting, processing, completed, canceled
    queued_at: datetime | None = None # Timestamp when the item was added to the queue
