# infra/db/user_repository_impl.py
import psycopg2  # Changed from sqlite3
import os
from typing import Optional, List
from datetime import datetime
from psycopg2.extras import DictCursor  # For dictionary-like row access

# --- Start of fix ---
# Adjust import paths for direct script execution vs. module import
try:
    # This works when imported as a module
    from core.entities.user import User
    from core.repositories.user_repository import UserRepository
    # Import the new get_db_connection function
    from infra.db.initialize_db import get_db_connection
except ImportError:
    # This works when run as a script
    import sys
    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    from core.entities.user import User
    from core.repositories.user_repository import UserRepository
    # Import the new get_db_connection function
    from infra.db.initialize_db import get_db_connection
# --- End of fix ---

# DB_DIR and DB_PATH are no longer needed for SQLite connection


# Consider renaming to PostgreSQLUserRepository
class PostgreSQLUserRepository(UserRepository):  # Renamed
    """PostgreSQL implementation of the UserRepository interface."""

    def _map_row_to_user(self, row: DictCursor) -> Optional[User]:
        """Helper method to map a database row to a User entity."""
        if row:
            return User(
                id=row['id'],
                name=row['name'],
                telegram_id=row['telegram_id'],
                balance=row['balance'],
                password_hash=row['password_hash'],
                api_key=row['api_key'],
                # PostgreSQL returns datetime objects directly
                # for TIMESTAMP WITH TIME ZONE
                created_at=row['created_at']
            )
        return None

    def add(self, user: User) -> User:
        """Adds a new user to the database."""
        conn = get_db_connection()
        cursor = None
        try:
            cursor = conn.cursor(cursor_factory=DictCursor)
            cursor.execute(
                """INSERT INTO users
                   (name, telegram_id, balance, password_hash, api_key)
                   VALUES (%s, %s, %s, %s, %s)
                   RETURNING id, created_at""",  # Use %s and RETURNING
                (user.name, user.telegram_id, user.balance,
                 user.password_hash, user.api_key)
            )
            returned_data = cursor.fetchone()
            user.id = returned_data['id']
            user.created_at = returned_data['created_at']
            conn.commit()
            print(f"User added successfully with ID: {user.id}")
        except psycopg2.IntegrityError as e:  # Catch psycopg2.IntegrityError
            # More specific error checking for PostgreSQL if needed
            # e.g., by checking e.pgcode
            print(f"Error adding user (IntegrityError): {e}")
            if conn:
                conn.rollback()
            raise
        except psycopg2.Error as e:
            print(f"An unexpected error occurred while adding user: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        return user

    def get_by_id(self, user_id: int) -> Optional[User]:
        """Retrieves a user by their database ID."""
        conn = get_db_connection()
        cursor = None
        try:
            cursor = conn.cursor(cursor_factory=DictCursor)
            cursor.execute(
                """SELECT id, name, telegram_id, balance, password_hash,
                          api_key, created_at
                   FROM users WHERE id = %s""",  # Use %s
                (user_id,)
            )
            row = cursor.fetchone()
            return self._map_row_to_user(row)
        except psycopg2.Error as e:
            print(f"An error occurred fetching user by ID {user_id}: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def get_by_telegram_id(self, telegram_id: str) -> Optional[User]:
        """Retrieves a user by their Telegram ID."""
        conn = get_db_connection()
        cursor = None
        try:
            cursor = conn.cursor(cursor_factory=DictCursor)
            cursor.execute(
                """SELECT id, name, telegram_id, balance, password_hash,
                          api_key, created_at
                   FROM users WHERE telegram_id = %s""",  # Use %s
                (telegram_id,)
            )
            row = cursor.fetchone()
            return self._map_row_to_user(row)
        except psycopg2.Error as e:
            print(
                f"An error occurred fetching user by Telegram ID "
                f"{telegram_id}: {e}"
            )
            return None
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def get_by_name(self, name: str) -> Optional[User]:
        """Retrieves a user by their name."""
        conn = get_db_connection()
        cursor = None
        try:
            cursor = conn.cursor(cursor_factory=DictCursor)
            cursor.execute(
                """SELECT id, name, telegram_id, balance, password_hash,
                          api_key, created_at
                   FROM users WHERE name = %s""",  # Use %s
                (name,)
            )
            row = cursor.fetchone()
            return self._map_row_to_user(row)
        except psycopg2.Error as e:
            print(f"An error occurred fetching user by name '{name}': {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def update_balance(self, user_id: int, new_balance: float) -> bool:
        """Updates the balance for a specific user."""
        conn = get_db_connection()
        cursor = None
        try:
            cursor = conn.cursor()  # No DictCursor needed for rowcount
            cursor.execute(
                "UPDATE users SET balance = %s WHERE id = %s",  # Use %s
                (new_balance, user_id)
            )
            conn.commit()
            success = cursor.rowcount > 0
            if success:
                print(f"Successfully updated balance for user ID: {user_id}")
            else:
                print(f"User ID: {user_id} not found for balance update.")
            return success
        except psycopg2.Error as e:
            print(
                f"An error occurred updating balance for user ID "
                f"{user_id}: {e}"
            )
            if conn:
                conn.rollback()
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def list_all(self) -> List[User]:
        """Retrieves a list of all users."""
        conn = get_db_connection()
        cursor = None
        users = []
        try:
            cursor = conn.cursor(cursor_factory=DictCursor)
            cursor.execute(
                """SELECT id, name, telegram_id, balance, password_hash,
                          api_key, created_at
                   FROM users ORDER BY created_at DESC"""
            )
            rows = cursor.fetchall()
            for row in rows:
                user = self._map_row_to_user(row)
                if user:
                    users.append(user)
            return users
        except psycopg2.Error as e:
            print(f"An error occurred listing all users: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def update_password_hash(self, user_id: int, password_hash: str) -> bool:
        """Updates the password_hash for a specific user."""
        conn = get_db_connection()
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET password_hash = %s WHERE id = %s",  # Use %s
                (password_hash, user_id)
            )
            conn.commit()
            return cursor.rowcount > 0
        except psycopg2.Error as e:
            print(f"Error updating password hash for user {user_id}: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def update_api_key(self, user_id: int, api_key: str) -> bool:
        """Updates the api_key for a specific user."""
        conn = get_db_connection()
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET api_key = %s WHERE id = %s",  # Use %s
                (api_key, user_id)
            )
            conn.commit()
            return cursor.rowcount > 0
        except psycopg2.Error as e:
            print(f"Error updating API key for user {user_id}: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def get_by_api_key(self, api_key: str) -> Optional[User]:
        """Retrieves a user by their API key."""
        conn = get_db_connection()
        cursor = None
        try:
            cursor = conn.cursor(cursor_factory=DictCursor)
            cursor.execute(
                """SELECT id, name, telegram_id, balance, password_hash,
                          api_key, created_at
                   FROM users WHERE api_key = %s""",  # Use %s
                (api_key,)
            )
            row = cursor.fetchone()
            return self._map_row_to_user(row)
        except psycopg2.Error as e:
            print(f"Error fetching user by API key: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()


# Example Usage (Optional - for testing this script directly)
if __name__ == '__main__':
    project_root_for_test = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    if project_root_for_test not in sys.path:
        sys.path.insert(0, project_root_for_test)

    print(
        "Running PostgreSQLUserRepository tests... "  # Renamed
        "Ensure DB is initialized and running."
    )

    # TODO: Rename class to PostgreSQLUserRepository
    repo = PostgreSQLUserRepository()

    timestamp_ms = int(datetime.now().timestamp() * 1000)
    test_name = f'Test User {timestamp_ms}'
    test_telegram_id = f'test_tg_{timestamp_ms}'
    test_password_hash = "dummy_hash_main_test_pg"
    test_api_key = f"dummy_api_key_pg_{timestamp_ms}"

    new_user = User(
        name=test_name,
        telegram_id=test_telegram_id,
        balance=100.0,
        password_hash=test_password_hash,
        api_key=test_api_key
    )
    added_user = None
    test_user_id = None
    try:
        print(f"Attempting to add user: {new_user.name}")
        added_user = repo.add(new_user)
        assert added_user.id is not None, "Added user should have an ID."
        assert added_user.name == test_name
        assert added_user.created_at is not None, "created_at should be set."
        print(
            f"User added: {added_user.name}, ID: {added_user.id}, "
            f"Created: {added_user.created_at}"
        )
        test_user_id = added_user.id
    except psycopg2.Error as e:  # Catch psycopg2 errors
        print(f"Error adding user during test: {e}")
        # If add fails, many other tests might not be meaningful
        test_user_id = None  # Ensure it's None if add failed

    print("-" * 30)

    if test_user_id:
        # Test 2: Get user by ID
        try:
            print(f"Attempting to get user by ID: {test_user_id}")
            retrieved_user = repo.get_by_id(test_user_id)
            assert retrieved_user is not None, "User should be found by ID."
            assert retrieved_user.id == test_user_id
            assert retrieved_user.name == test_name
            assert retrieved_user.password_hash == test_password_hash
            assert retrieved_user.api_key == test_api_key
            print(f"User retrieved by ID: {retrieved_user.name}")
        except psycopg2.Error as e:
            print(f"DB error during get by ID test: {e}")
        except Exception as e:
            print(f"General error during get by ID test: {e}")

        # Test 3: Get user by Telegram ID
        try:
            print(f"Attempting to get user by Telegram ID: {test_telegram_id}")
            retrieved_user_tg = repo.get_by_telegram_id(test_telegram_id)
            assert retrieved_user_tg is not None, (
                "User should be found by Telegram ID."
            )
            assert retrieved_user_tg.telegram_id == test_telegram_id
            print(f"User retrieved by Telegram ID: {retrieved_user_tg.name}")
        except psycopg2.Error as e:
            print(f"DB error during get by Telegram ID test: {e}")
        except Exception as e:
            print(f"General error during get by Telegram ID test: {e}")

        # Test 4: Get user by Name
        try:
            print(f"Attempting to get user by Name: {test_name}")
            retrieved_user_name = repo.get_by_name(test_name)
            assert retrieved_user_name is not None, (
                "User should be found by Name."
            )
            assert retrieved_user_name.name == test_name
            print(f"User retrieved by Name: {retrieved_user_name.name}")
        except psycopg2.Error as e:
            print(f"DB error during get by Name test: {e}")
        except Exception as e:
            print(f"General error during get by Name test: {e}")

        # Test 5: Update balance
        try:
            new_balance = 150.75
            print(f"Attempting to update balance for user ID: {test_user_id}")
            update_success = repo.update_balance(test_user_id, new_balance)
            assert update_success, "Balance update should be successful."
            updated_user = repo.get_by_id(test_user_id)
            assert updated_user is not None
            assert updated_user.balance == new_balance, (
                "Balance should be updated."
            )
            print(
                f"Balance updated for {updated_user.name} "
                f"to {updated_user.balance}"
            )
        except psycopg2.Error as e:
            print(f"DB error during update balance test: {e}")
        except Exception as e:
            print(f"General error during update balance test: {e}")

        # Test 6: Update password hash
        try:
            new_password_hash = "new_dummy_hash_updated_pg"
            print(
                f"Attempting to update password hash for user ID: "
                f"{test_user_id}"
            )
            update_ph_success = repo.update_password_hash(
                test_user_id, new_password_hash
            )
            assert update_ph_success, (
                "Password hash update should be successful."
            )
            updated_user_ph = repo.get_by_id(test_user_id)
            assert updated_user_ph is not None
            assert updated_user_ph.password_hash == new_password_hash
            print(f"Password hash updated for {updated_user_ph.name}")
        except psycopg2.Error as e:
            print(f"DB error during update password hash test: {e}")
        except Exception as e:
            print(f"General error during update password hash test: {e}")

        # Test 7: Update API key
        try:
            new_api_key = f"new_dummy_api_key_pg_updated_{timestamp_ms}"
            print(f"Attempting to update API key for user ID: {test_user_id}")
            update_ak_success = repo.update_api_key(test_user_id, new_api_key)
            assert update_ak_success, "API key update should be successful."
            updated_user_ak = repo.get_by_id(test_user_id)
            assert updated_user_ak is not None
            assert updated_user_ak.api_key == new_api_key
            print(f"API key updated for {updated_user_ak.name}")

            print(f"Attempting to get user by new API key: {new_api_key}")
            retrieved_by_api_key = repo.get_by_api_key(new_api_key)
            assert retrieved_by_api_key is not None, (
                "User should be found by API key."
            )
            assert retrieved_by_api_key.id == test_user_id
            print(f"User retrieved by API key: {retrieved_by_api_key.name}")
        except psycopg2.Error as e:
            print(f"DB error during update API key test: {e}")
        except Exception as e:
            print(f"General error during update API key test: {e}")

        # Test 8: Delete user (and verify)
        try:
            print("\n--- Test: Delete User ---")
            # Assuming delete method exists and works
            delete_success = repo.delete(test_user_id)
            assert delete_success, "User deletion should be successful."
            deleted_user_check = repo.get_by_id(test_user_id)
            assert deleted_user_check is None, (
                "User should not be found after deletion."
            )
            print(f"User ID {test_user_id} deleted successfully.")
        except psycopg2.Error as e:
            print(f"DB error during delete user test: {e}")
        except Exception as e:
            print(f"General error during delete user test: {e}")

    else:
        print(
            "Skipping further tests as initial user add failed or was skipped."
        )

    # Test 9: List all users (after potential add/delete)
    try:
        print("Attempting to list all users...")
        all_users = repo.list_all()
        assert isinstance(all_users, list), "Should return a list."
        if added_user and test_user_id:
            assert any(u.id == test_user_id for u in all_users)
        print(
            f"Listed {len(all_users)} users. First few: "
            f"{[(u.name, u.id) for u in all_users[:3]]}"
        )
    except psycopg2.Error as e:
        print(f"DB error during list all users test: {e}")
    except Exception as e:
        print(f"General error during list all users test: {e}")

    # Test 10: Handle duplicates (name, telegram_id)
    if added_user and test_user_id:
        try:
            print(f"Attempting to add user with duplicate name: {test_name}")
            duplicate_user_name = User(
                name=test_name,
                telegram_id=f"another_tg_{timestamp_ms}_dup_pg",
                balance=50.0,
                password_hash="hash123_dup_name_pg",
                api_key=f"key_{timestamp_ms}_dup_name_pg"
            )
            try:
                repo.add(duplicate_user_name)
                assert False, (
                    "Should have raised IntegrityError for duplicate name."
                )
            except psycopg2.IntegrityError as e:  # Catch psycopg2 error
                # For PostgreSQL, check unique violation by e.pgcode == '23505'
                # Or check str(e) for
                # "duplicate key value violates unique constraint"
                print(f"Correctly caught error for duplicate name: {e}")
            except Exception as e:
                assert False, f"Wrong exception type for duplicate name: {e}"

            print(
                f"Attempting to add user with duplicate telegram_id: "
                f"{test_telegram_id}"
            )
            duplicate_tg_user = User(
                name=f"Another Name {timestamp_ms}_dup_pg",
                telegram_id=test_telegram_id,
                balance=70.0,
                password_hash="hash456_dup_tg_pg",
                api_key=f"key_{timestamp_ms}_dup_tg_pg"
            )
            try:
                repo.add(duplicate_tg_user)
                assert False, (
                    "IntegrityError for duplicate telegram_id expected."
                )
            except psycopg2.IntegrityError as e:  # Catch psycopg2 error
                print(
                    f"Correctly caught IntegrityError for duplicate "
                    f"telegram_id: {e}"
                )
                assert "users_telegram_id_key" in str(e) or \
                       "duplicate key" in str(e).lower()
            except Exception as e:
                assert False, (
                    f"Wrong exception type for duplicate telegram_id: {e}"
                )
        except psycopg2.Error as e:
            print(f"DB error during duplicate user tests: {e}")
        except Exception as e:
            print(f"General error during duplicate user tests: {e}")

    print("PostgreSQLUserRepository tests completed.")
