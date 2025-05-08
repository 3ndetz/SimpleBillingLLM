# core/use_cases/llm_use_cases.py

# TODO should divide logic for WORKER and for API!
# For API we do NOT need load LLMs and llm classes or methods!!!
import logging
import time
from datetime import datetime, timezone # Ensure timezone is imported

from core.entities.prediction import Prediction
from core.entities.transaction import Transaction
from core.repositories.user_repository import UserRepository
from core.repositories.model_repository import ModelRepository
from core.repositories.prediction_repository import PredictionRepository
from core.repositories.transaction_repository import TransactionRepository
# from infra.llm.gguf_llm import predict  # MOVED TO BOTTOM! NEED OTHER LOGIC!

class LLMUseCases:
    def __init__(
        self,
        user_repository: UserRepository,
        model_repository: ModelRepository,
        prediction_repository: PredictionRepository,
        transaction_repository: TransactionRepository
    ):
        """Initializes the LLMUseCases with necessary repositories."""
        self.user_repository = user_repository
        self.model_repository = model_repository
        self.prediction_repository = prediction_repository
        self.transaction_repository = transaction_repository
        
    async def create_prediction(self, prediction_id: int, user_id: int, input_text: str) -> Prediction:
        """Processes an existing prediction (billing, LLM call, status update)."""
        # 1. Load existing prediction record
        
        prediction = self.prediction_repository.get_by_id(prediction_id)
        if not prediction:
            logging.error(f"Use Case Error: Prediction not found for id={prediction_id}")
            raise ValueError(f"Prediction with id {prediction_id} not found.")
        logging.info(f"Use Case: Starting prediction for id={prediction_id}")

        # 2. Get User
        user = self.user_repository.get_by_id(prediction.user_id)
        if not user:
            logging.error(f"Use Case Error: User not found for id={prediction.user_id}")
            raise ValueError(f"User with id {prediction.user_id} not found.")

        # 3. Get Active Model
        model = self.model_repository.get_active_model()
        if not model:
            logging.error("Use Case Error: No active LLM model found.")
            raise ValueError("No active LLM model configured.")
        logging.info(f"Use Case: Using model '{model.name}' (ID: {model.id})")

        # 4. Check Balance
        # For now, let's assume a minimum cost or just check > 0
        if user.balance <= 0:
            logging.warning(f"Use Case Warning: User {user_id} has insufficient balance ({user.balance})")
            # In a real app, raise InsufficientFundsError
            raise ValueError("Insufficient balance to create prediction.")

        # 5. Mark prediction as processing
        prediction.status = 'processing'
        # Calculate queue_time before updating with 'processing' status
        if prediction.created_at:
            start_processing_time_utc = datetime.now(timezone.utc)

            # Ensure prediction.created_at is UTC
            if prediction.created_at.tzinfo is None:
                # If naive, assume it's UTC and make it aware
                created_at_utc = prediction.created_at.replace(tzinfo=timezone.utc)
            else:
                # If aware, convert to UTC
                created_at_utc = prediction.created_at.astimezone(timezone.utc)
            
            queue_duration = start_processing_time_utc - created_at_utc
            # Convert duration to milliseconds
            prediction.queue_time = int(queue_duration.total_seconds() * 1000)
        else:
            # Fallback if created_at is somehow not set
            logging.warning(
                f"Prediction ID {prediction.id} missing created_at "
                f"for queue_time calculation."
            )
            prediction.queue_time = None

        # Update with status 'processing' and calculated queue_time
        self.prediction_repository.update(prediction)
        
        start_time = time.time()  # For process_time calculation

        try:
            from infra.llm.openai_llm import predict
            # 5. Call the LLM (Dummy Implementation)
            llm_result = await predict(input_text)
            process_time_ms = int((time.time() - start_time) * 1000)
            logging.info(f"Use Case: Dummy LLM returned: {llm_result}")

            # 6. Calculate Cost
            input_cost = llm_result['input_tokens'] * model.input_token_price
            output_cost = llm_result['output_tokens'] * model.output_token_price
            total_cost = input_cost + output_cost
            logging.info(f"Use Case: Calculated cost: {total_cost:.6f}")

            # 6. Update Prediction Record with Results
            prediction.output_text = llm_result['output_text']
            prediction.input_tokens = llm_result['input_tokens']
            prediction.output_tokens = llm_result['output_tokens']
            prediction.total_cost = total_cost
            prediction.status = 'completed'
            prediction.process_time = process_time_ms
            prediction.completed_at = datetime.now(timezone.utc)  # Set completed_at as UTC
            # Original comment below is now addressed by the line above
            # completed_at is set automatically by the repository update method # TODO NEED TEST

            # 7. Update User Balance & Create Transaction
            new_balance = user.balance - total_cost
            if new_balance < 0:
                # This case should ideally be caught earlier,
                # but handle defensively
                logging.warning(
                    f"Use Case Warning: User {user_id} balance "
                    f"({user.balance}) insufficient for cost ({total_cost}). "
                    f"Setting balance to 0."
                )
                # For simplicity, cap at 0
                actual_cost = user.balance  # Charge only what they have
                new_balance = 0.0
                # Adjust prediction cost recorded
                prediction.total_cost = actual_cost
            else:
                actual_cost = total_cost

            # Update prediction in DB before charging
            self.prediction_repository.update(prediction)
            logging.info(
                f"Use Case: Updated prediction record {prediction.id} to 'completed'."
            )

            # Create transaction record
            transaction = Transaction(
                user_id=user.id,
                amount=-actual_cost,  # Cost is negative amount
                description=f"Cost for prediction {prediction.uuid}",
                prediction_id=prediction.id
            )
            self.transaction_repository.add(transaction)
            logging.info(
                f"Use Case: Created transaction for prediction {prediction.id}"
            )

            # Update user's balance in DB
            self.user_repository.update_balance(user.id, new_balance)
            logging.info(
                f"Use Case: Updated balance for user {user.id} to {new_balance:.2f}"
            )
            user.balance = new_balance  # Update user entity in memory

            return prediction

        except Exception as e:
            # 8. Handle Errors
            logging.exception(
                f"Use Case Error: Failed during prediction processing for "
                f"id {prediction.id}: {e}"
            )
            # Update prediction status to 'failed'
            prediction.status = 'failed'
            # Also set completed_at on failure as UTC
            prediction.completed_at = datetime.now(timezone.utc)
            # Optionally add error message to output_text or a new field
            prediction.output_text = f"Error: {e}"
            self.prediction_repository.update(prediction)
            # Do not charge the user if the process failed
            raise  # Re-raise the exception
