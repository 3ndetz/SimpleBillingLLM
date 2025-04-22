# infra/db/prediction_repository_impl.py
import sqlite3
import os
import sys
from typing import Optional, List
from datetime import datetime

# Adjust import paths
try:
    from core.entities.prediction import Prediction
    from core.repositories.prediction_repository import PredictionRepository
except ImportError:
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    from core.entities.prediction import Prediction
    from core.repositories.prediction_repository import PredictionRepository

# Define DB Path
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data')
DB_PATH = os.path.join(DB_DIR, 'billing_llm.db')

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

class SQLitePredictionRepository(PredictionRepository):
    """SQLite implementation of the PredictionRepository interface."""

    def _map_row_to_prediction(self, row: sqlite3.Row) -> Optional[Prediction]:
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
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                completed_at=datetime.fromisoformat(row['completed_at']) if row['completed_at'] else None,
                queue_time=row['queue_time'],
                process_time=row['process_time']
            )
        return None

    def add(self, prediction: Prediction) -> Prediction:
        """Adds a new prediction record."""
        conn = get_db_connection()
        cursor = conn.cursor()
        now_iso = datetime.now().isoformat()
        try:
            cursor.execute(
                """INSERT INTO predictions (uuid, user_id, model_id, input_text, status, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (prediction.uuid, prediction.user_id, prediction.model_id, prediction.input_text, prediction.status, now_iso)
            )
            prediction.id = cursor.lastrowid
            prediction.created_at = datetime.fromisoformat(now_iso) # Update entity with timestamp
            conn.commit()
        except Exception as e:
            print(f"Error adding prediction: {e}") # Replace with logging
            conn.rollback()
            raise
        finally:
            conn.close()
        return prediction

    def get_by_id(self, prediction_id: int) -> Optional[Prediction]:
        """Retrieves a prediction by its database ID."""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM predictions WHERE id = ?", (prediction_id,))
            row = cursor.fetchone()
            return self._map_row_to_prediction(row)
        except Exception as e:
            print(f"Error getting prediction by id: {e}") # Replace with logging
            return None
        finally:
            conn.close()

    def get_by_uuid(self, uuid: str) -> Optional[Prediction]:
        """Retrieves a prediction by its unique UUID."""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM predictions WHERE uuid = ?", (uuid,))
            row = cursor.fetchone()
            return self._map_row_to_prediction(row)
        except Exception as e:
            print(f"Error getting prediction by uuid: {e}") # Replace with logging
            return None
        finally:
            conn.close()

    def update(self, prediction: Prediction) -> bool:
        """Updates an existing prediction record."""
        if not prediction.id:
            return False # Cannot update without ID

        conn = get_db_connection()
        cursor = conn.cursor()
        now_iso = datetime.now().isoformat() if prediction.status in ['completed', 'failed'] else None
        try:
            cursor.execute(
                """UPDATE predictions SET
                       output_text = ?, input_tokens = ?, output_tokens = ?, total_cost = ?,
                       status = ?, completed_at = ?, queue_time = ?, process_time = ?
                   WHERE id = ?""",
                (
                    prediction.output_text, prediction.input_tokens, prediction.output_tokens, prediction.total_cost,
                    prediction.status, now_iso, prediction.queue_time, prediction.process_time,
                    prediction.id
                )
            )
            conn.commit()
            if cursor.rowcount == 0:
                print(f"Warning: No prediction found with ID {prediction.id} to update.")
                return False
            if now_iso:
                 prediction.completed_at = datetime.fromisoformat(now_iso) # Update entity
            return True
        except Exception as e:
            print(f"Error updating prediction {prediction.id}: {e}") # Replace with logging
            conn.rollback()
            return False
        finally:
            conn.close()

    def list_by_user(self, user_id: int) -> List[Prediction]:
        """Retrieves all predictions for a specific user."""
        conn = get_db_connection()
        cursor = conn.cursor()
        predictions = []
        try:
            cursor.execute("SELECT * FROM predictions WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
            rows = cursor.fetchall()
            predictions = [self._map_row_to_prediction(row) for row in rows if row]
        except Exception as e:
            print(f"Error listing predictions for user {user_id}: {e}") # Replace with logging
        finally:
            conn.close()
        return predictions

# Example Usage (Optional)
if __name__ == '__main__':
    # Ensure correct imports and DB setup
    project_root_for_test = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if project_root_for_test not in sys.path:
        sys.path.insert(0, project_root_for_test)
    try:
        from infra.db.initialize_db import initialize_database
        print("Initializing database for test...")
        # initialize_database() # Uncomment to reset
        print("Database ready.")
        # Need a user and model for testing
        from infra.db.user_repository_impl import SQLiteUserRepository
        from infra.db.model_repository_impl import SQLiteModelRepository
        user_repo = SQLiteUserRepository()
        model_repo = SQLiteModelRepository()
        test_user = user_repo.get_by_telegram_id("test_tg_123") # Assumes user exists
        test_model = model_repo.get_active_model()
        if not test_user: print("WARNING: Test user 'test_tg_123' not found.")
        if not test_model: print("WARNING: No active model found.")

    except ImportError as e:
        print(f"Could not import dependencies: {e}. Make sure DB exists.")
        test_user = None
        test_model = None

    if test_user and test_model:
        repo = SQLitePredictionRepository()

        print("\nTesting add...")
        pred = Prediction(user_id=test_user.id, model_id=test_model.id, input_text="Hello?", status='pending')
        try:
            added_pred = repo.add(pred)
            print(f"Added prediction: {added_pred}")

            print("\nTesting get_by_uuid...")
            fetched_pred = repo.get_by_uuid(added_pred.uuid)
            print(f"Fetched by UUID: {fetched_pred}")

            print("\nTesting update...")
            fetched_pred.status = 'completed'
            fetched_pred.output_text = "Echo: Hello?"
            fetched_pred.input_tokens = 1
            fetched_pred.output_tokens = 3
            fetched_pred.total_cost = 0.007 # (1 * 0.001) + (3 * 0.002)
            fetched_pred.process_time = 50 # ms
            update_success = repo.update(fetched_pred)
            print(f"Update successful: {update_success}")

            print("\nTesting get_by_id after update...")
            updated_pred = repo.get_by_id(fetched_pred.id)
            print(f"Fetched after update: {updated_pred}")

            print("\nTesting list_by_user...")
            user_preds = repo.list_by_user(test_user.id)
            print(f"Predictions for user {test_user.id}: {len(user_preds)}")
            for p in user_preds:
                print(p)

        except Exception as e:
            print(f"An error occurred during testing: {e}")

    else:
        print("\nSkipping prediction repo tests due to missing user or model.")

    print("\nTesting completed.")

