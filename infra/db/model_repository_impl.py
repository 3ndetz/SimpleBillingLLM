# infra/db/model_repository_impl.py
import psycopg2  # Changed from sqlite3
import os
import sys
from typing import Optional, List
from psycopg2.extras import DictCursor  # For dictionary-like row access

# Adjust import paths
try:
    from core.entities.model import Model
    from core.repositories.model_repository import ModelRepository
    # Import the new get_db_connection function
    from infra.db.initialize_db import get_db_connection
except ImportError:
    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    from core.entities.model import Model
    from core.repositories.model_repository import ModelRepository
    # Import the new get_db_connection function
    from infra.db.initialize_db import get_db_connection

# DB_DIR and DB_PATH are no longer needed for SQLite connection


# Consider renaming to PostgreSQLModelRepository
class PostgreSQLModelRepository(ModelRepository):  # Renamed
    """PostgreSQL implementation of the ModelRepository interface."""

    def _map_row_to_model(self, row: DictCursor) -> Optional[Model]:
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
        cursor = None
        try:
            cursor = conn.cursor(cursor_factory=DictCursor)
            cursor.execute(
                """INSERT INTO models (name, description, input_token_price,
                                   output_token_price, is_active)
                   VALUES (%s, %s, %s, %s, %s) RETURNING id""",
                (
                    model.name, model.description, model.input_token_price,
                    model.output_token_price, model.is_active
                )
            )
            model.id = cursor.fetchone()['id']  # Get id from RETURNING
            conn.commit()
        except psycopg2.Error as e:  # Catch psycopg2.Error
            print(f"Error adding model: {e}")  # Replace with logging
            if conn:
                conn.rollback()
            raise  # Re-raise the exception
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        return model

    def get_by_id(self, model_id: int) -> Optional[Model]:
        """Retrieves a model by its database ID."""
        conn = get_db_connection()
        cursor = None
        try:
            cursor = conn.cursor(cursor_factory=DictCursor)
            cursor.execute(
                "SELECT * FROM models WHERE id = %s", (model_id,)
            )
            row = cursor.fetchone()
            return self._map_row_to_model(row)
        except psycopg2.Error as e:  # Catch psycopg2.Error
            print(f"Error getting model by id: {e}")  # Replace with logging
            return None
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def get_by_name(self, name: str) -> Optional[Model]:
        """Retrieves a model by its name."""
        conn = get_db_connection()
        cursor = None
        try:
            cursor = conn.cursor(cursor_factory=DictCursor)
            cursor.execute(
                "SELECT * FROM models WHERE name = %s", (name,)
            )
            row = cursor.fetchone()
            return self._map_row_to_model(row)
        except psycopg2.Error as e:  # Catch psycopg2.Error
            print(f"Error getting model by name: {e}")  # Replace with logging
            return None
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def get_active_model(self) -> Optional[Model]:
        """Retrieves the first active model found."""
        conn = get_db_connection()
        cursor = None
        try:
            cursor = conn.cursor(cursor_factory=DictCursor)
            # Simple approach: get the first active one
            cursor.execute(
                "SELECT * FROM models WHERE is_active = TRUE LIMIT 1"
            )
            row = cursor.fetchone()
            return self._map_row_to_model(row)
        except psycopg2.Error as e:  # Catch psycopg2.Error
            print(f"Error getting active model: {e}")  # Replace with logging
            return None
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def list_all(self) -> List[Model]:
        """Retrieves a list of all models."""
        conn = get_db_connection()
        cursor = None
        models = []
        try:
            cursor = conn.cursor(cursor_factory=DictCursor)
            cursor.execute("SELECT * FROM models")
            rows = cursor.fetchall()
            models = [self._map_row_to_model(row) for row in rows if row]
        except psycopg2.Error as e:  # Catch psycopg2.Error
            print(f"Error listing all models: {e}")  # Replace with logging
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        return models


# Example Usage (Optional) - Needs adaptation for PostgreSQL
if __name__ == '__main__':
    project_root_for_test = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    if project_root_for_test not in sys.path:
        sys.path.insert(0, project_root_for_test)

    try:
        print(
            "Initializing PostgreSQL database for test "
            "(this will reset data)..."
        )
        # initialize_database() # Uncomment to reset DB - BE CAREFUL
        print("Database should be ready.")
    except ImportError as e:
        print(
            f"Could not import initialize_db: {e}. "
            f"Make sure DB is running and configured."
        )
    except psycopg2.Error as e:
        print(f"Database connection error during example: {e}")

    # TODO: Rename class to PostgreSQLModelRepository *TODO NEED TEST*
    repo = PostgreSQLModelRepository()  # Renamed

    try:
        if not repo.get_by_name("dummy-echo-v1"):
            print("\nAdding default model...")
            default_model = Model(
                name="dummy-echo-v1",
                description="A simple model that echoes input.",
                input_token_price=0.001,  # Example price
                output_token_price=0.002,  # Example price
                is_active=True
            )
            try:
                added = repo.add(default_model)
                print(f"Added model: {added}")
            except Exception as e:
                print(
                    "Failed to add default model "
                    f"(maybe already exists or DB issue?): {e}"
                )
    except psycopg2.Error as e:
        print(f"DB error checking/adding default model: {e}")

    print("\nTesting get_active_model...")
    try:
        active = repo.get_active_model()
        print(f"Active model: {active}")
    except psycopg2.Error as e:
        print(f"DB error getting active model: {e}")

    print("\nTesting list_all...")
    try:
        all_models = repo.list_all()
        print(f"Total models: {len(all_models)}")
        for m in all_models:
            print(m)
    except psycopg2.Error as e:
        print(f"DB error listing all models: {e}")

    print("\nTesting completed.")

