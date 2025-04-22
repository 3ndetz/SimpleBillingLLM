# core/use_cases/llm_use_cases.py
import logging
import time
from datetime import datetime

from core.entities.prediction import Prediction
from core.entities.transaction import Transaction
from core.repositories.user_repository import UserRepository
from core.repositories.model_repository import ModelRepository
from core.repositories.prediction_repository import PredictionRepository
from core.repositories.transaction_repository import TransactionRepository
from infra.llm.dummy_llm import dummy_llm_predict # Import the dummy LLM

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

    async def create_prediction(self, user_id: int, input_text: str) -> Prediction:
        """Handles the creation, processing, and billing of a prediction."""
        logging.info(f"Use Case: Starting prediction for user_id={user_id}")

        # 1. Get User
        user = self.user_repository.get_by_id(user_id)
        if not user:
            logging.error(f"Use Case Error: User not found for id={user_id}")
            # In a real app, raise a specific exception (e.g., UserNotFound)
            raise ValueError(f"User with id {user_id} not found.")

        # 2. Get Active Model (Simplification: use the first active one)
        model = self.model_repository.get_active_model()
        if not model:
            logging.error("Use Case Error: No active LLM model found.")
            raise ValueError("No active LLM model configured.")
        logging.info(f"Use Case: Using model '{model.name}' (ID: {model.id})")

        # 3. Check Balance (Basic Check - TODO: More robust check needed)
        # For now, let's assume a minimum cost or just check > 0
        if user.balance <= 0:
            logging.warning(f"Use Case Warning: User {user_id} has insufficient balance ({user.balance})")
            # In a real app, raise InsufficientFundsError
            raise ValueError("Insufficient balance to create prediction.")

        # 4. Create Initial Prediction Record
        prediction = Prediction(
            user_id=user.id,
            model_id=model.id,
            input_text=input_text,
            status='processing' # Start as processing
        )
        prediction = self.prediction_repository.add(prediction)
        logging.info(f"Use Case: Created initial prediction record (ID: {prediction.id}, UUID: {prediction.uuid})")
        start_time = time.time()

        try:
            # 5. Call the LLM (Dummy Implementation)
            llm_result = await dummy_llm_predict(input_text)
            process_time_ms = int((time.time() - start_time) * 1000)
            logging.info(f"Use Case: Dummy LLM returned: {llm_result}")

            # 6. Calculate Cost
            input_cost = llm_result['input_tokens'] * model.input_token_price
            output_cost = llm_result['output_tokens'] * model.output_token_price
            total_cost = input_cost + output_cost
            logging.info(f"Use Case: Calculated cost: {total_cost:.6f}")

            # 7. Update Prediction Record with Results
            prediction.output_text = llm_result['output_text']
            prediction.input_tokens = llm_result['input_tokens']
            prediction.output_tokens = llm_result['output_tokens']
            prediction.total_cost = total_cost
            prediction.status = 'completed'
            prediction.process_time = process_time_ms
            # completed_at is set automatically by the repository update method

            # 8. Update User Balance & Create Transaction
            new_balance = user.balance - total_cost
            if new_balance < 0:
                # This case should ideally be caught earlier, but handle defensively
                logging.warning(f"Use Case Warning: Prediction cost ({total_cost}) exceeds balance ({user.balance}) for user {user_id}. Setting balance to 0.")
                # Decide policy: allow negative balance or cap at 0?
                # For simplicity, let's not allow negative balance from prediction cost
                actual_cost = user.balance # Charge only what they have
                new_balance = 0.0
                prediction.total_cost = actual_cost # Adjust prediction cost recorded
                # Optionally, mark prediction as partially failed due to funds?
            else:
                actual_cost = total_cost

            # Update prediction in DB *before* charging user
            self.prediction_repository.update(prediction)
            logging.info(f"Use Case: Updated prediction record {prediction.id} to status 'completed'.")

            # Create transaction record
            transaction = Transaction(
                user_id=user.id,
                amount=-actual_cost, # Cost is negative amount
                description=f"Cost for prediction {prediction.uuid}",
                prediction_id=prediction.id
            )
            self.transaction_repository.add(transaction)
            logging.info(f"Use Case: Created transaction record for prediction {prediction.id}")

            # Update user's balance in DB
            self.user_repository.update_balance(user.id, new_balance)
            logging.info(f"Use Case: Updated balance for user {user.id} to {new_balance:.2f}")
            user.balance = new_balance # Update user entity in memory

            return prediction

        except Exception as e:
            # 9. Handle Errors
            logging.exception(f"Use Case Error: Failed during prediction processing for prediction {prediction.id}: {e}")
            # Update prediction status to 'failed'
            prediction.status = 'failed'
            # Optionally add error message to output_text or a new field
            prediction.output_text = f"Error: {e}"
            self.prediction_repository.update(prediction)
            # Do not charge the user if the process failed
            raise # Re-raise the exception to be handled by the controller
