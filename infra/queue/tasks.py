# filepath: infra/queue/tasks.py
# Defines Celery tasks for processing predictions asynchronously
import asyncio
import logging
from infra.queue.celery_app import app
from core.use_cases.llm_use_cases import LLMUseCases
from infra.db.user_repository_impl import SQLiteUserRepository
from infra.db.model_repository_impl import SQLiteModelRepository
from infra.db.prediction_repository_impl import SQLitePredictionRepository
from infra.db.transaction_repository_impl import SQLiteTransactionRepository


# Instantiate repositories and use cases
user_repo = SQLiteUserRepository()
model_repo = SQLiteModelRepository()
pred_repo = SQLitePredictionRepository()
trans_repo = SQLiteTransactionRepository()
use_cases = LLMUseCases(
    user_repository=user_repo,
    model_repository=model_repo,
    prediction_repository=pred_repo,
    transaction_repository=trans_repo,
)


def process_prediction(prediction_id: int, user_id: int, input_text: str):
    """
    Enqueue a prediction job into Celery queue.
    """
    _process_prediction_job.delay(prediction_id, user_id, input_text)


  
  
@app.task(name='infra.queue.tasks._process_prediction_job')
def _process_prediction_job(prediction_id: int, user_id: int, input_text: str):
    """
    Worker function to process a pending prediction.
    """
    logging.info(f"Worker: Starting processing prediction_id={prediction_id}")
    try:
        # Run async use case in fresh event loop
        result = asyncio.run(
            use_cases.create_prediction(prediction_id=prediction_id,
                                        user_id=user_id, input_text=input_text
                                       )
            # use_cases.create_prediction(user_id=user_id, input_text=input_text)
        )
        logging.info(f"Worker: Completed prediction {result.id}")
        return result.id
    except Exception as e:
        logging.exception(
            "Worker Error: Failed prediction %s: %s", prediction_id, e
        )
        raise
