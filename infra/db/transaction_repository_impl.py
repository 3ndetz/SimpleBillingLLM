# infra/db/transaction_repository_impl.py
import sqlite3
import os
import sys
from typing import Optional, List
from datetime import datetime

# Adjust import paths
try:
    from core.entities.transaction import Transaction
    from core.repositories.transaction_repository import TransactionRepository
except ImportError:
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    from core.entities.transaction import Transaction
    from core.repositories.transaction_repository import TransactionRepository

# Define DB Path
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data')
DB_PATH = os.path.join(DB_DIR, 'billing_llm.db')

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

class SQLiteTransactionRepository(TransactionRepository):
    """SQLite implementation of the TransactionRepository interface."""

    def _map_row_to_transaction(self, row: sqlite3.Row) -> Optional[Transaction]:
        """Helper method to map a database row to a Transaction entity."""
        if row:
            return Transaction(
                id=row['id'],
                user_id=row['user_id'],
                amount=row['amount'],
                description=row['description'],
                prediction_id=row['prediction_id'],
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
            )
        return None

    def add(self, transaction: Transaction) -> Transaction:
        """Adds a new transaction record."""
        conn = get_db_connection()
        cursor = conn.cursor()
        now_iso = datetime.now().isoformat()
        try:
            cursor.execute(
                """INSERT INTO transactions (user_id, amount, description, prediction_id, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (transaction.user_id, transaction.amount, transaction.description, transaction.prediction_id, now_iso)
            )
            transaction.id = cursor.lastrowid
            transaction.created_at = datetime.fromisoformat(now_iso) # Update entity
            conn.commit()
        except Exception as e:
            print(f"Error adding transaction: {e}") # Replace with logging
            conn.rollback()
            raise
        finally:
            conn.close()
        return transaction

    def get_by_id(self, transaction_id: int) -> Optional[Transaction]:
        """Retrieves a transaction by its database ID."""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM transactions WHERE id = ?", (transaction_id,))
            row = cursor.fetchone()
            return self._map_row_to_transaction(row)
        except Exception as e:
            print(f"Error getting transaction by id: {e}") # Replace with logging
            return None
        finally:
            conn.close()

    def list_by_user(self, user_id: int) -> List[Transaction]:
        """Retrieves all transactions for a specific user."""
        conn = get_db_connection()
        cursor = conn.cursor()
        transactions = []
        try:
            cursor.execute("SELECT * FROM transactions WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
            rows = cursor.fetchall()
            transactions = [self._map_row_to_transaction(row) for row in rows if row]
        except Exception as e:
            print(f"Error listing transactions for user {user_id}: {e}") # Replace with logging
        finally:
            conn.close()
        return transactions

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
        # Need a user for testing
        from infra.db.user_repository_impl import SQLiteUserRepository
        user_repo = SQLiteUserRepository()
        test_user = user_repo.get_by_telegram_id("test_tg_123") # Assumes user exists
        if not test_user: print("WARNING: Test user 'test_tg_123' not found.")

    except ImportError as e:
        print(f"Could not import dependencies: {e}. Make sure DB exists.")
        test_user = None

    if test_user:
        repo = SQLiteTransactionRepository()

        print("\nTesting add (deposit)...")
        deposit = Transaction(user_id=test_user.id, amount=10.0, description="Initial deposit")
        try:
            added_deposit = repo.add(deposit)
            print(f"Added deposit: {added_deposit}")

            print("\nTesting add (charge)...")
            # Assume prediction_id 1 exists if testing after prediction tests
            charge = Transaction(user_id=test_user.id, amount=-0.5, description="Prediction cost", prediction_id=1)
            added_charge = repo.add(charge)
            print(f"Added charge: {added_charge}")

            print("\nTesting get_by_id...")
            fetched_tx = repo.get_by_id(added_deposit.id)
            print(f"Fetched by ID: {fetched_tx}")

            print("\nTesting list_by_user...")
            user_txs = repo.list_by_user(test_user.id)
            print(f"Transactions for user {test_user.id}: {len(user_txs)}")
            for tx in user_txs:
                print(tx)

        except Exception as e:
            print(f"An error occurred during testing: {e}")
    else:
        print("\nSkipping transaction repo tests due to missing user.")

    print("\nTesting completed.")
