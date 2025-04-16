# core/entities/user.py
from dataclasses import dataclass
from datetime import datetime

@dataclass
class User:
    """Represents a user in the system."""
    id: int | None = None  # Database ID, None if not yet persisted
    name: str | None = None # Name from Telegram
    telegram_id: str | None = None # Telegram User ID (unique)
    balance: float = 0.0
    created_at: datetime | None = None # Set when loaded from DB or upon creation logic
