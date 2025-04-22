import logging
import os
import sys

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field  # For request body validation

# --- Start of fix ---
# Adjust import paths for direct script execution vs. module import
try:
    # This works when imported as a module (e.g., by uvicorn)
    from core.use_cases.user_use_cases import UserUseCases
    from infra.db.user_repository_impl import SQLiteUserRepository
    # Rename to avoid conflict
    from core.entities.user import User as UserEntity
except ImportError:
    # This works when run as a script (less common for controllers)
    # Go up three levels to the project root
    # (from infra/web/controllers -> infra/web -> infra -> root)
    project_root = os.path.dirname(
        os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
    )
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    from core.use_cases.user_use_cases import UserUseCases
    from infra.db.user_repository_impl import SQLiteUserRepository
    # Rename to avoid conflict
    from core.entities.user import User as UserEntity
# --- End of fix ---


# --- Pydantic Models ---


class UserCreateRequest(BaseModel):
    """Request model for creating/getting a user via Telegram info."""
    telegram_id: str = Field(..., description="The user's unique Telegram ID")
    name: str = Field(..., description="The user's full name from Telegram")


# Use the core User entity for the response, but make it a Pydantic model
# if it isn't already, or create a specific response model.
# Assuming UserEntity is already a Pydantic model or similar (like dataclass)
class UserResponse(UserEntity):
    """Response model for user details."""
    pass  # Inherits fields from core.entities.user.User


class BalanceResponse(BaseModel):
    """Response model for user balance."""
    balance: float


# --- Router Setup ---
router = APIRouter()
# Initialize repository and use cases
# (dependency injection could be used later)
user_repository = SQLiteUserRepository()
user_use_cases = UserUseCases(user_repository)


# --- API Endpoints ---

# TODO: Implement Web API controllers in infra/web/controllers/
# - *Partially DONE*

@router.post("/users/", response_model=UserResponse)
async def get_or_create_user(user_request: UserCreateRequest):
    """Gets a user by Telegram ID, creating one if they don't exist."""
    log_msg = (
        f"API: Received request to get/create user for "
        f"telegram_id={user_request.telegram_id}"
    )
    logging.info(log_msg)
    try:
        user = user_use_cases.get_or_create_user_by_telegram_id(
            telegram_id=user_request.telegram_id,
            name=user_request.name
        )
        # Convert the core entity to the response model if necessary
        # If UserEntity is already Pydantic, this works directly
        return user
    except Exception as e:
        log_err_msg = (
            f"API Error: Failed to get or create user for "
            f"telegram_id={user_request.telegram_id}: {e}"
        )
        logging.exception(log_err_msg)
        # Use HTTPException for standard FastAPI error responses
        raise HTTPException(
            status_code=500, detail="Internal server error processing user."
        )


# NEW Endpoint: Get User by Telegram ID
@router.get("/users/by-telegram/{telegram_id}", response_model=UserResponse)
async def get_user_by_telegram_id_endpoint(telegram_id: str):
    """Gets user details (including internal ID) by their Telegram ID."""
    logging.info(f"API: Received request for user details for telegram_id={telegram_id}")
    try:
        user = user_use_cases.get_user_by_telegram_id(telegram_id)
        if user:
            return user
        else:
            logging.warning(f"API: User not found for details request: telegram_id={telegram_id}")
            raise HTTPException(status_code=404, detail=f"User with Telegram ID {telegram_id} not found.")
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.exception(f"API Error: Failed to get user details for telegram_id={telegram_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error retrieving user details.")


# MODIFIED Endpoint: Get Balance by Internal User ID
# TODO: Implement endpoint - *DONE* -> *MODIFIED*
@router.get(
    "/users/{user_id}/balance", # Changed path parameter
    response_model=BalanceResponse
)
async def get_user_balance(user_id: int): # Changed parameter to user_id: int
    """Gets the balance for a user based on their internal database ID."""
    logging.info(f"API: Received request for balance for user_id={user_id}")
    try:
        # Use the new use case method
        balance = user_use_cases.get_user_balance_by_id(user_id)
        if balance is not None:
            return BalanceResponse(balance=balance)
        else:
            # User not found by internal ID
            logging.warning(f"API: User not found for balance check: user_id={user_id}")
            raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found.")
    except HTTPException as e:
        # Re-raise HTTPExceptions directly
        raise e
    except Exception as e:
        logging.exception(f"API Error: Failed to get balance for user_id={user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error retrieving balance.")

# Note: The original register_user(name: str, email: str) endpoint is removed
# as it doesn't align with the current Telegram-based workflow.
# If needed for other purposes, it should be added back with appropriate logic.
