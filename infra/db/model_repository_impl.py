# infra/db/model_repository_impl.py
import sqlite3
import os
import sys
from typing import Optional, List

# Adjust import paths
try:
    from core.entities.model import Model
    from core.repositories.model_repository import ModelRepository
except ImportError:
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    from core.entities.model import Model
    from core.repositories.model_repository import ModelRepository

# Define DB Path (consistent with user_repository_impl)
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data')
DB_PATH = os.path.join(DB_DIR, 'billing_llm.db')

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

class SQLiteModelRepository(ModelRepository):
    """SQLite implementation of the ModelRepository interface."""

    def _map_row_to_model(self, row: sqlite3.Row) -> Optional[Model]:
        """Helper method to map a database row to a Model entity."""
        if row:
            return Model(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                input_token_price=row['input_token_price'],
                output_token_price=row['output_token_price'],
                is_active=bool(row['is_active'])
            )
        return None

    def add(self, model: Model) -> Model:
        """Adds a new model to the database."""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """INSERT INTO models (name, description, input_token_price, output_token_price, is_active)
                   VALUES (?, ?, ?, ?, ?)""",
                (model.name, model.description, model.input_token_price, model.output_token_price, model.is_active)
            )
            model.id = cursor.lastrowid
            conn.commit()
        except Exception as e:
            print(f"Error adding model: {e}") # Replace with logging
            conn.rollback()
            raise # Re-raise the exception
        finally:
            conn.close()
        return model

    def get_by_id(self, model_id: int) -> Optional[Model]:
        """Retrieves a model by its database ID."""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM models WHERE id = ?", (model_id,))
            row = cursor.fetchone()
            return self._map_row_to_model(row)
        except Exception as e:
            print(f"Error getting model by id: {e}") # Replace with logging
            return None
        finally:
            conn.close()

    def get_by_name(self, name: str) -> Optional[Model]:
        """Retrieves a model by its name."""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM models WHERE name = ?", (name,))
            row = cursor.fetchone()
            return self._map_row_to_model(row)
        except Exception as e:
            print(f"Error getting model by name: {e}") # Replace with logging
            return None
        finally:
            conn.close()

    def get_active_model(self) -> Optional[Model]:
        """Retrieves the first active model found."""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # Simple approach: get the first active one
            cursor.execute("SELECT * FROM models WHERE is_active = 1 LIMIT 1")
            row = cursor.fetchone()
            return self._map_row_to_model(row)
        except Exception as e:
            print(f"Error getting active model: {e}") # Replace with logging
            return None
        finally:
            conn.close()

    def list_all(self) -> List[Model]:
        """Retrieves a list of all models."""
        conn = get_db_connection()
        cursor = conn.cursor()
        models = []
        try:
            cursor.execute("SELECT * FROM models")
            rows = cursor.fetchall()
            models = [self._map_row_to_model(row) for row in rows if row]
        except Exception as e:
            print(f"Error listing all models: {e}") # Replace with logging
        finally:
            conn.close()
        return models

# Example Usage (Optional)
if __name__ == '__main__':
    # Ensure correct imports when run as script
    project_root_for_test = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if project_root_for_test not in sys.path:
        sys.path.insert(0, project_root_for_test)
    try:
        from infra.db.initialize_db import initialize_database
        print("Initializing database for test (this will reset data)...")
        # initialize_database() # Uncomment to reset DB
        print("Database should be ready.")
    except ImportError as e:
        print(f"Could not import initialize_db: {e}. Make sure DB exists.")

    repo = SQLiteModelRepository()

    # Add a default model if it doesn't exist
    if not repo.get_by_name("dummy-echo-v1"):
        print("\nAdding default model...")
        default_model = Model(
            name="dummy-echo-v1",
            description="A simple model that echoes input.",
            input_token_price=0.001, # Example price
            output_token_price=0.002, # Example price
            is_active=True
        )
        try:
            added = repo.add(default_model)
            print(f"Added model: {added}")
        except Exception as e:
            print(f"Failed to add default model (maybe already exists?): {e}")

    print("\nTesting get_active_model...")
    active = repo.get_active_model()
    print(f"Active model: {active}")

    print("\nTesting list_all...")
    all_models = repo.list_all()
    print(f"Total models: {len(all_models)}")
    for m in all_models:
        print(m)

    print("\nTesting completed.")

