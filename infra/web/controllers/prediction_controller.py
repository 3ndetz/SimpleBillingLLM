# infra/web/controllers/prediction_controller.py
import logging

from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel, Field

from core.entities.prediction import Prediction as PredictionEntity
# Import repository implementations to instantiate use cases
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

# --- API Endpoints ---

@router.post(
    "/predictions/",
    response_model=PredictionResponse,
    status_code=202,  # 202 Accepted as it's async
)
async def create_prediction_endpoint(
    request: PredictionCreateRequest,
) -> PredictionResponse:
    """
    Enqueues a prediction request and returns its initial
    pending details.
    """
    logging.info(
        f"API: Received prediction request for user_id="
        f"{request.user_id}"
    )
    # 1. Verify user exists and has balance
    user = user_repo.get_by_id(request.user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail=(
                f"User with ID {request.user_id} not found."
            )
        )
    if user.balance <= 0:
        raise HTTPException(
            status_code=402,
            detail=(
                "Insufficient balance to enqueue prediction."
            )
        )
    # 2. Get active model
    model = model_repo.get_active_model()
    if not model:
        raise HTTPException(
            status_code=503,
            detail="No active model available."
        )
    # 3. Create prediction record with status 'pending'
    pred = PredictionEntity(
        user_id=request.user_id,
        model_id=model.id,
        input_text=request.input_text,
        status="pending",
    )
    pred = prediction_repo.add(pred)
    # Enqueue async processing task
    from infra.queue.tasks import process_prediction

    process_prediction(
        pred.id,
        request.user_id,
        request.input_text,
    )
    # Return pending prediction
    return pred

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
