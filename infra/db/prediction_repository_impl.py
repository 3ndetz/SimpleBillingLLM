# infra/db/prediction_repository_impl.py
import psycopg2  # Changed from sqlite3
from psycopg2.extras import DictCursor  # For dictionary-like row access
import os
import sys
from typing import Optional, List
from datetime import datetime

# Adjust import paths
try:
    from core.entities.prediction import Prediction
    from core.repositories.prediction_repository import PredictionRepository
    # Import the centralized get_db_connection
    from infra.db.initialize_db import get_db_connection
except ImportError:
    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    from core.entities.prediction import Prediction
    from core.repositories.prediction_repository import PredictionRepository
    # Import the centralized get_db_connection
    from infra.db.initialize_db import get_db_connection


# Removed DB_DIR, DB_PATH, and local get_db_connection
# as we use the centralized one

class PostgreSQLPredictionRepository(PredictionRepository):  # Renamed class
    """PostgreSQL implementation of the PredictionRepository interface."""

    def _map_row_to_prediction(  # Changed row type
        self, row: DictCursor
    ) -> Optional[Prediction]:
        """Helper method to map a database row to a Prediction entity."""
        if row:
            return Prediction(
                id=row['id'],
                uuid=row['uuid'],
                user_id=row['user_id'],
                model_id=row['model_id'],
                input_text=row['input_text'],
                output_text=row['output_text'],
                input_tokens=row['input_tokens'],
                output_tokens=row['output_tokens'],
                total_cost=row['total_cost'],
                status=row['status'],
                # PostgreSQL returns datetime objects directly
                # for TIMESTAMP WITH TIME ZONE
                created_at=row['created_at'],
                completed_at=row['completed_at'],
                queue_time=row['queue_time'],
                process_time=row['process_time']
            )
        return None

    def add(self, prediction: Prediction) -> Prediction:
        """Adds a new prediction record."""
        conn = get_db_connection()
        # Use DictCursor to access rows by column name
        cursor = conn.cursor(cursor_factory=DictCursor)
        try:
            cursor.execute("""
                INSERT INTO predictions (
                    uuid, user_id, model_id, input_text, output_text,
                    input_tokens, output_tokens, total_cost, status,
                    created_at, completed_at, queue_time, process_time
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, created_at;  -- Return id and created_at
            """, (
                prediction.uuid,
                prediction.user_id,
                prediction.model_id,
                prediction.input_text,
                prediction.output_text,
                prediction.input_tokens,
                prediction.output_tokens,
                prediction.total_cost,
                prediction.status,
                prediction.created_at,  # Explicitly pass created_at
                prediction.completed_at,
                prediction.queue_time,
                prediction.process_time
            ))
            inserted_row = cursor.fetchone()
            if inserted_row:
                prediction.id = inserted_row['id']
                # Update created_at from DB if it was set by default/trigger
                prediction.created_at = inserted_row['created_at']
            conn.commit()
        except psycopg2.Error as e:
            print(f"Database error in add prediction: {e}")
            if conn:
                conn.rollback()
            # Re-raise or handle as appropriate for your error strategy
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        return prediction

    def get_by_id(self, prediction_id: int) -> Optional[Prediction]:
        """Retrieves a prediction by its database ID."""
        conn = get_db_connection()
        # Use DictCursor for this connection if not default
        cursor = conn.cursor(cursor_factory=DictCursor)
        try:
            cursor.execute(
                "SELECT * FROM predictions WHERE id = %s",
                (prediction_id,)
            )  # Changed placeholder
            row = cursor.fetchone()
            return self._map_row_to_prediction(row)
        except psycopg2.Error as e:  # Changed error type
            # Replace with logging
            print(f"Error getting prediction by id: {e}")
            return None
        finally:
            conn.close()

    def get_by_uuid(self, uuid: str) -> Optional[Prediction]:
        """Retrieves a prediction by its unique UUID."""
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=DictCursor)  # Use DictCursor
        try:
            cursor.execute(
                "SELECT * FROM predictions WHERE uuid = %s",
                (uuid,)
            )  # Changed placeholder
            row = cursor.fetchone()
            return self._map_row_to_prediction(row)
        except psycopg2.Error as e:  # Changed error type
            # Replace with logging
            print(f"Error getting prediction by uuid: {e}")
            return None
        finally:
            conn.close()

    def update(self, prediction: Prediction) -> bool:
        """Updates an existing prediction record."""
        if not prediction.id:
            return False  # Cannot update without ID

        conn = get_db_connection()
        cursor = conn.cursor()
        # completed_at is updated by DB trigger or default if status changes
        # or can be set explicitly if needed.
        # Assuming DDL handles it or it's passed.
        try:
            cursor.execute(
                """UPDATE predictions SET
                       output_text = %s, input_tokens = %s,
                       output_tokens = %s, total_cost = %s,
                       status = %s, completed_at = %s,
                       queue_time = %s, process_time = %s
                   WHERE id = %s""",  # Changed placeholders
                (
                    prediction.output_text, prediction.input_tokens,
                    prediction.output_tokens, prediction.total_cost,
                    prediction.status, prediction.completed_at,
                    # Pass completed_at directly
                    prediction.queue_time, prediction.process_time,
                    prediction.id
                )
            )
            conn.commit()
            if cursor.rowcount == 0:
                print(
                    f"Warning: No prediction found with ID {prediction.id} "
                    f"to update."
                )
                return False
            # No need to update prediction.completed_at from now_iso,
            # it's passed or handled by DB
            return True
        except psycopg2.Error as e:  # Changed error type
            print(
                f"Error updating prediction {prediction.id}: {e}"
            )  # Replace with logging
            conn.rollback()
            return False
        finally:
            conn.close()

    def list_by_user(self, user_id: int) -> List[Prediction]:
        """Retrieves all predictions for a specific user."""
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=DictCursor)  # Use DictCursor
        predictions = []
        try:
            cursor.execute(
                "SELECT * FROM predictions WHERE user_id = %s "
                "ORDER BY created_at DESC",
                (user_id,)
            )  # Changed placeholder
            rows = cursor.fetchall()
            predictions = [
                self._map_row_to_prediction(row) for row in rows if row
            ]
        except psycopg2.Error as e:  # Changed error type
            print(
                f"Error listing predictions for user {user_id}: {e}"
            )  # Replace with logging
        finally:
            conn.close()
        return predictions


# Example Usage (Optional)
if __name__ == '__main__':
    # Ensure correct imports and DB setup
    project_root_for_test = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    if project_root_for_test not in sys.path:
        sys.path.insert(0, project_root_for_test)
    try:
        # Using the new PostgreSQL Repositories for testing
        from infra.db.user_repository_impl import PostgreSQLUserRepository
        from infra.db.model_repository_impl import PostgreSQLModelRepository
        # initialize_database is for the new PG setup - removed unused import
        # from infra.db.initialize_db import (
        # initialize_database_main_for_tests as initialize_database
        # )

        print("Initializing database for test (PostgreSQL)...")
        # initialize_database()  # Ensure this function exists and is for PG
        # Uncomment to reset, ensure it points to test DB if needed
        print("Database ready.")

        user_repo = PostgreSQLUserRepository()
        model_repo = PostgreSQLModelRepository()
        # Using a known test user telegram ID,
        # ensure this user exists in your PG test DB
        test_user_telegram_id = "test_tg_123_pg"  # Example, adjust as needed
        test_user = user_repo.get_by_telegram_id(test_user_telegram_id)

        if not test_user:
            print(
                f"WARNING: Test user '{test_user_telegram_id}' not found. "
                f"Creating one for test."
            )
            from core.entities.user import User
            # Create a new user for testing if not found
            new_user = User(
                telegram_id=test_user_telegram_id,
                username=f"test_user_{test_user_telegram_id}",
                balance=100.0
            )
            try:
                test_user = user_repo.add(new_user)
                print(f"Created test user: {test_user}")
            except Exception as e_user:
                print(f"Failed to create test user: {e_user}")
                test_user = None

        test_model = model_repo.get_active_model()
        if not test_model:
            print("WARNING: No active model found. Creating one for test.")
            from core.entities.model import Model
            # Create a new model for testing if not found
            new_model = Model(
                name="TestModel-GPT-PG",
                api_key="test_api_key_pg",
                input_token_price=0.001,
                output_token_price=0.002,
                is_active=True
            )
            try:
                test_model = model_repo.add(new_model)
                print(f"Created test model: {test_model}")
            except Exception as e_model:
                print(f"Failed to create test model: {e_model}")
                test_model = None

    except ImportError as e:
        print(
            f"Could not import dependencies: {e}. "
            f"Make sure DB is set up for PostgreSQL."
        )
        test_user = None
        test_model = None
    except psycopg2.Error as db_err:
        print(f"Database connection error during setup: {db_err}")
        test_user = None
        test_model = None

    if test_user and test_user.id and test_model and test_model.id:
        # Ensure IDs are present
        repo = PostgreSQLPredictionRepository()

        print("\\nTesting add...")
        # Ensure user_id and model_id are correctly passed
        # from the fetched/created entities
        pred = Prediction(
            user_id=test_user.id,
            model_id=test_model.id,
            input_text="Hello PostgreSQL?",
            status='pending',
            uuid=os.urandom(16).hex()
        )
        try:
            added_pred = repo.add(pred)
            print(f"Added prediction: {added_pred}")

            if added_pred and added_pred.uuid:  # Check if add was successful
                print("\\nTesting get_by_uuid...")
                fetched_pred = repo.get_by_uuid(added_pred.uuid)
                print(f"Fetched by UUID: {fetched_pred}")

                # Check if fetch was successful
                if fetched_pred and fetched_pred.id:
                    print("\\nTesting update...")
                    fetched_pred.status = 'completed'
                    fetched_pred.output_text = "Echo: Hello PostgreSQL?"
                    fetched_pred.input_tokens = 2
                    fetched_pred.output_tokens = 4
                    # (2 * 0.001) + (4 * 0.002)
                    fetched_pred.total_cost = 0.010
                    fetched_pred.process_time = 60  # ms
                    # Set completed_at for update
                    fetched_pred.completed_at = datetime.now()
                    update_success = repo.update(fetched_pred)
                    print(f"Update successful: {update_success}")

                    print("\\nTesting get_by_id after update...")
                    updated_pred = repo.get_by_id(fetched_pred.id)
                    print(f"Fetched after update: {updated_pred}")

            print("\\nTesting list_by_user...")
            # Ensure user_id is valid
            user_preds = repo.list_by_user(test_user.id)
            print(f"Predictions for user {test_user.id}: {len(user_preds)}")
            for p_item in user_preds:  # Renamed p to p_item
                print(p_item)

        except psycopg2.Error as e:  # Catch psycopg2 errors
            print(f"A database error occurred during testing: {e}")
        except Exception as e:
            print(f"An unexpected error occurred during testing: {e}")

    else:
        print(
            "\\nSkipping prediction repo tests due to missing user, model, "
            "or their IDs."
        )
        if not test_user or not test_user.id:
            print("Reason: Test user or user ID is missing.")
        if not test_model or not test_model.id:
            print("Reason: Test model or model ID is missing.")

    print("\\nPrediction repository testing completed.")

