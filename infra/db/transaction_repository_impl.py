# infra/db/transaction_repository_impl.py
import os  # Added: For path operations
import sys  # Added: For system-specific parameters and functions
from typing import List, Optional

import psycopg2  # Changed from sqlite3
from psycopg2.extras import DictCursor  # For dictionary-like row access

# Adjust import paths
try:
    from core.entities.transaction import Transaction
    from core.repositories.transaction_repository import TransactionRepository
    # Import the new get_db_connection function
    from infra.db.initialize_db import get_db_connection
except ImportError:
    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    from core.entities.transaction import Transaction
    from core.repositories.transaction_repository import TransactionRepository
    # Import the new get_db_connection function
    from infra.db.initialize_db import get_db_connection

# DB_DIR and DB_PATH are no longer needed for SQLite connection


class PostgreSQLTransactionRepository(TransactionRepository):  # Renamed
    """PostgreSQL implementation of the TransactionRepository interface."""

    # TODO NEED TEST
    def _map_row_to_transaction(
        self, row: DictCursor
    ) -> Optional[Transaction]:
        """Maps a database row to a Transaction object."""
        if row:
            return Transaction(
                id=row['id'],
                user_id=row['user_id'],
                amount=row['amount'],
                description=row['description'],
                prediction_id=row['prediction_id'],
                created_at=row['created_at']
            )
        return None

    def add(self, transaction: Transaction) -> Transaction:
        """Adds a new transaction record."""
        conn = get_db_connection()
        cursor = None
        try:
            cursor = conn.cursor(cursor_factory=DictCursor)  # Use DictCursor
            cursor.execute(
                """INSERT INTO transactions
                   (user_id, amount, description, prediction_id)
                   VALUES (%s, %s, %s, %s)
                   RETURNING id, created_at""",  # Use %s and RETURNING
                (transaction.user_id, transaction.amount,
                 transaction.description, transaction.prediction_id)
            )
            returned_data = cursor.fetchone()
            transaction.id = returned_data['id']
            transaction.created_at = returned_data['created_at']
            conn.commit()
        except psycopg2.Error as e:  # Catch psycopg2.Error
            # Replace with proper logging
            print(f"Error adding transaction: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        return transaction

    def get_by_id(self, transaction_id: int) -> Optional[Transaction]:
        """Retrieves a transaction by its database ID."""
        conn = get_db_connection()
        cursor = None
        try:
            cursor = conn.cursor(cursor_factory=DictCursor)  # Use DictCursor
            cursor.execute(
                """SELECT id, user_id, amount, description, prediction_id,
                          created_at
                   FROM transactions WHERE id = %s""",  # Use %s
                (transaction_id,)
            )
            row = cursor.fetchone()
            return self._map_row_to_transaction(row)
        except psycopg2.Error as e:  # Catch psycopg2.Error
            # Replace with proper logging
            print(f"Error getting transaction by id: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def list_by_user(self, user_id: int) -> List[Transaction]:
        """Retrieves all transactions for a specific user."""
        conn = get_db_connection()
        cursor = None
        transactions = []
        try:
            cursor = conn.cursor(cursor_factory=DictCursor)  # Use DictCursor
            cursor.execute(
                """SELECT id, user_id, amount, description, prediction_id,
                          created_at
                   FROM transactions WHERE user_id = %s
                   ORDER BY created_at DESC""",  # Use %s
                (user_id,)
            )
            rows = cursor.fetchall()
            for row in rows:
                mapped_transaction = self._map_row_to_transaction(row)
                if mapped_transaction:
                    transactions.append(mapped_transaction)
        except psycopg2.Error as e:  # Catch psycopg2.Error
            # Replace with proper logging
            print(f"Error listing transactions for user {user_id}: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        return transactions

# Example Usage (Optional - Needs update for PostgreSQL and new User Repo)
# if __name__ == '__main__':
#     # Ensure correct imports and DB setup
#     project_root_for_test = os.path.dirname(
#         os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#     )
#     if project_root_for_test not in sys.path:
#         sys.path.insert(0, project_root_for_test)
#     try:
#         # from infra.db.initialize_db import initialize_database
#         # initialize_database might need to be called if schema is not there
#         print("Initializing database for test...")
#         print("Database ready.")
#         # Need a user for testing - USE PostgreSQLUserRepository
#         # UPDATED
#         from infra.db.user_repository_impl import PostgreSQLUserRepository
#         user_repo = PostgreSQLUserRepository()  # UPDATED
#
#         # Create or get a test user
#         test_user_telegram_id = "test_tg_for_tx_pg"
#         test_user = user_repo.get_by_telegram_id(test_user_telegram_id)
#         if not test_user:
#             # TODO NEED TEST
#             # print(
#             # f"Test user {test_user_telegram_id} not found, creating..."
#             # )
#             # user_repo = PostgreSQLUserRepository()
#             # # Changed from SQLiteUserRepository
#             # test_user = user_repo.get_by_telegram_id(test_user_telegram_id)
#             # if test_user and test_user.id is not None:
#             # # Ensure user and user.id exists
#             # transaction_repo = PostgreSQLTransactionRepository() # Changed
#             from core.entities.user import User  # Import User entity
#             test_user = User(
#                 name="Tx Test User PG",
#                 telegram_id=test_user_telegram_id,
#                 balance=1000,
#                 password_hash="test_pg_pw",
#                 api_key="test_pg_api_key_tx"
#             )
#             test_user = user_repo.add(test_user)
#             print(f"Created test user: {test_user.id}")
#
#     except ImportError as e:
#         print(
#             f"Could not import dependencies: {e}. "
#             f"Make sure DB exists and user repo is updated."
#         )
#         test_user = None
#     except psycopg2.Error as db_error:
#         print(f"Database error during setup: {db_error}")
#         test_user = None
#
#     if test_user and test_user.id is not None:  # Ensure user and user.id exists
#         repo = PostgreSQLTransactionRepository()  # UPDATED
#
#         print("\nTesting add (deposit)...")
#         deposit = Transaction(
#             user_id=test_user.id,
#             amount=10.0,
#             description="Initial deposit PG"
#         )
#         try:
#             added_deposit = repo.add(deposit)
#             print(f"Added deposit: {added_deposit}")
#             assert added_deposit.id is not None
#             assert added_deposit.created_at is not None
#
#             print("\nTesting add (charge)...")
#             # Assume prediction_id 1 might not exist, or use None
#             charge = Transaction(
#                 user_id=test_user.id, amount=-0.5,
#                 description="Prediction cost PG", prediction_id=None
#             )  # Using None for prediction_id
#             added_charge = repo.add(charge)
#             print(f"Added charge: {added_charge}")
#             assert added_charge.id is not None
#
#             print("\nTesting get_by_id...")
#             fetched_tx = repo.get_by_id(added_deposit.id)
#             print(f"Fetched by ID: {fetched_tx}")
#             assert fetched_tx is not None
#             assert fetched_tx.id == added_deposit.id
#
#             print("\nTesting list_by_user...")
#             user_txs = repo.list_by_user(test_user.id)
#             print(f"Transactions for user {test_user.id}: {len(user_txs)}")
#             for tx in user_txs:
#                 print(tx)
#             assert len(user_txs) >= 2  # At least the two we added
#
#         except psycopg2.Error as e:  # Catch psycopg2.Error
#             print(f"A database error occurred during testing: {e}")
#         except Exception as e:
#             print(f"An unexpected error occurred during testing: {e}")
#     else:
#         print(
#             "\\nSkipping transaction repo tests due to missing or "
#             "incomplete user."
#         )
#
#     print("\nTransaction repository tests (PostgreSQL) completed.")
