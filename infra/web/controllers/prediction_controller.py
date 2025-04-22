# infra/web/controllers/prediction_controller.py
import logging
import os
import sys
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel, Field

# Adjust import paths
try:
    # Module imports
    from core.use_cases.llm_use_cases import LLMUseCases
    from core.entities.prediction import Prediction as PredictionEntity
    # Import repository implementations to instantiate use cases
    from infra.db.user_repository_impl import SQLiteUserRepository
    from infra.db.model_repository_impl import SQLiteModelRepository
    from infra.db.prediction_repository_impl import SQLitePredictionRepository
    from infra.db.transaction_repository_impl import SQLiteTransactionRepository
except ImportError:
    # Script execution imports
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    from core.use_cases.llm_use_cases import LLMUseCases
    from core.entities.prediction import Prediction as PredictionEntity
    from infra.db.user_repository_impl import SQLiteUserRepository
    from infra.db.model_repository_impl import SQLiteModelRepository
    from infra.db.prediction_repository_impl import SQLitePredictionRepository
    from infra.db.transaction_repository_impl import SQLiteTransactionRepository

# --- Pydantic Models ---

class PredictionCreateRequest(BaseModel):
    """Request model for creating a new prediction."""
    user_id: int = Field(..., description="The internal ID of the user requesting the prediction.")
    input_text: str = Field(..., description="The input text/prompt for the LLM.")

# Use the core Prediction entity for the response
class PredictionResponse(PredictionEntity):
    """Response model for prediction details."""
    pass

# --- Router Setup ---
router = APIRouter()

# --- Dependency Injection (Manual for now) ---
# Instantiate repositories
user_repo = SQLiteUserRepository()
model_repo = SQLiteModelRepository()
prediction_repo = SQLitePredictionRepository()
transaction_repo = SQLiteTransactionRepository()

# Instantiate use cases
llm_use_cases = LLMUseCases(
    user_repository=user_repo,
    model_repository=model_repo,
    prediction_repository=prediction_repo,
    transaction_repository=transaction_repo
)

# --- API Endpoints ---

@router.post("/predictions/", response_model=PredictionResponse, status_code=202) # 202 Accepted as it's async
async def create_prediction_endpoint(request: PredictionCreateRequest):
    """Accepts a prediction request, processes it, and returns the initial prediction details."""
    logging.info(f"API: Received prediction request for user_id={request.user_id}")
    try:
        # Call the use case to handle the prediction creation and processing
        prediction_result = await llm_use_cases.create_prediction(
            user_id=request.user_id,
            input_text=request.input_text
        )
        # Return the completed prediction details
        # Note: In a truly async system with a queue, this might return the initial
        # prediction object with status 'pending' or 'queued'.
        # Since our dummy LLM is fast, we return the completed one.
        return prediction_result
    except ValueError as ve:
        # Handle specific known errors like UserNotFound, InsufficientBalance
        logging.warning(f"API Validation Error: {ve}")
        # Determine appropriate status code based on error
        if "not found" in str(ve).lower():
            raise HTTPException(status_code=404, detail=str(ve))
        elif "insufficient balance" in str(ve).lower():
            raise HTTPException(status_code=402, detail=str(ve)) # 402 Payment Required
        else:
            raise HTTPException(status_code=400, detail=str(ve)) # Generic bad request
    except Exception as e:
        logging.exception(f"API Error: Failed to create prediction for user_id={request.user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error processing prediction.")

@router.get("/predictions/{uuid}", response_model=PredictionResponse)
async def get_prediction_status_endpoint(uuid: str):
    """Gets the status and details of a specific prediction by its UUID."""
    logging.info(f"API: Received request for prediction status uuid={uuid}")
    try:
        prediction = prediction_repo.get_by_uuid(uuid)
        if prediction:
            return prediction
        else:
            logging.warning(f"API: Prediction not found for status request: uuid={uuid}")
            raise HTTPException(status_code=404, detail=f"Prediction with UUID {uuid} not found.")
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.exception(f"API Error: Failed to get prediction status for uuid={uuid}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error retrieving prediction status.")
