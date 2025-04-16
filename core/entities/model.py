# core/entities/model.py
from dataclasses import dataclass

@dataclass
class Model:
    """Represents an LLM model available in the system."""
    id: int | None = None # Database ID
    name: str | None = None # Model name (e.g., 'gpt-3.5-turbo')
    description: str | None = None # Optional description
    input_token_price: float = 0.0 # Price per input token
    output_token_price: float = 0.0 # Price per output token
    is_active: bool = True # Whether the model is currently available for use
