import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field  # For request body validation


from core.use_cases.user_use_cases import UserUseCases
from infra.db.user_repository_impl import SQLiteUserRepository
from core.entities.user import User as UserEntity


class UserTGCreateRequest(BaseModel):
    """Request model for creating/getting a user via Telegram info."""
    telegram_id: str = Field(..., description="The user's unique Telegram ID")
    name: str = Field(..., description="The user's full name from Telegram")

class UserCreateRequest(BaseModel):
    """Request model for creating/getting a user via Telegram info."""
    password: str = Field(..., description="The user's password")
    name: str = Field(..., description="The user's full name from Telegram")

class UserResponse(UserEntity):
    """Response model for user details."""
    pass  # Inherits fields from core.entities.user.User


class BalanceResponse(BaseModel):
    """Response model for user balance."""
    balance: float


# --- Router Setup ---
router = APIRouter()
# Initialize repository and use cases
user_repository = SQLiteUserRepository()
user_use_cases = UserUseCases(user_repository)


# --- API Endpoints ---

@router.post("/users/", response_model=UserResponse)
async def get_or_create_user(user_request: UserCreateRequest):
    """Gets a user by name and password, creating one if they don't exist."""
    log_msg = (
        "API: Received request to get/create user for "
        f"name={user_request.name}"
    )
    logging.info(log_msg)
    try:
        user = user_use_cases.get_or_create_user(
            name=user_request.name,
            password=user_request.password
        )
        return user
    except Exception as e:
        log_err_msg = (
            "API Error: Failed to get or create user for "
            f"name={user_request.name}: {e}"
        )
        logging.exception(log_err_msg)
        raise HTTPException(
            status_code=500, detail="Internal server error processing user."
        )


# NEW Endpoint: Get User by Telegram ID
@router.get("/users/by-telegram/{telegram_id}", response_model=UserResponse)
async def get_user_by_telegram_id_endpoint(telegram_id: str):
    """Gets user details (including internal ID) by their Telegram ID."""
    logging.info(
        "API: Received request for user details for "
        f"telegram_id={telegram_id}"
    )
    try:
        user = user_use_cases.get_user_by_telegram_id(telegram_id)
        if user:
            return user
        else:
            logging.warning(
                "API: User not found for details request: "
                f"telegram_id={telegram_id}"
            )
            raise HTTPException(
                status_code=404,
                detail=f"User with Telegram ID {telegram_id} not found."
            )
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.exception(
            "API Error: Failed to get user details for "
            f"telegram_id={telegram_id}: {e}"
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error retrieving user details."
        )


# MODIFIED Endpoint: Get Balance by Internal User ID
# TODO: Implement endpoint - *DONE* -> *MODIFIED*
@router.get(
    "/users/{user_id}/balance",  # Changed path parameter
    response_model=BalanceResponse
)
async def get_user_balance(user_id: int):  # Changed parameter to user_id: int
    """Gets the balance for a user based on their internal database ID."""
    logging.info(f"API: Received request for balance for user_id={user_id}")
    try:
        # Use the new use case method
        balance = user_use_cases.get_user_balance_by_id(user_id)
        if balance is not None:
            return BalanceResponse(balance=balance)
        else:
            # User not found by internal ID
            logging.warning(
                "API: User not found for balance check: "
                f"user_id={user_id}"
            )
            raise HTTPException(
                status_code=404,
                detail=f"User with ID {user_id} not found."
            )
    except HTTPException as e:
        # Re-raise HTTPExceptions directly
        raise e
    except Exception as e:
        logging.exception(
            "API Error: Failed to get balance for "
            f"user_id={user_id}: {e}"
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error retrieving balance."
        )


# NEW Endpoint: Get User by Name
@router.get("/users/by-name/{name}", response_model=UserResponse)
async def get_user_by_name(name: str):
    """Gets user details (including internal ID) by their name."""

    logging.info(f"API: Received request for user details for name={name}")
    try:
        user = user_use_cases.get_user_by_name(name)
        if user:
            return user
        else:
            logging.warning(
                "API: User not found for details request: "
                f"name={name}"
            )
            raise HTTPException(
                status_code=404,
                detail=f"User with name {name} not found."
            )
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.exception(
            "API Error: Failed to get user details for "
            f"name={name}: {e}"
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error retrieving user details."
        )

# Note: The original register_user(name: str, email: str) endpoint is removed
# as it doesn't align with the current Telegram-based workflow.
# If needed for other purposes, it should be added back with appropriate logic.
