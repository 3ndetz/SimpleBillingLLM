import psycopg2
import os
import sys
from psycopg2.extras import DictCursor  # For dictionary-like row access

# Environment variables for PostgreSQL connection
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "admin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "admin")
DB_NAME = os.getenv("DB_NAME", "billing_llm_db")

# Define the DSN (Data Source Name) for PostgreSQL
DSN = (
    f"host={DB_HOST} port={DB_PORT} user={DB_USER} "
    f"password={DB_PASSWORD} dbname={DB_NAME}"
)


def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    conn = psycopg2.connect(DSN)
    # conn.autocommit = False  # Default is False
    return conn


def initialize_database():
    """
    Initializes the PostgreSQL database by creating tables based on the DDL
    schema.
    """
    print(
        f"Connecting to PostgreSQL: dbname='{DB_NAME}' user='{DB_USER}' "
        f"host='{DB_HOST}' port='{DB_PORT}'"
    )
    conn = None
    cursor = None  # Initialize cursor to None for finally block
    try:
        conn = get_db_connection()
        # Use DictCursor for dictionary-like row access
        cursor = conn.cursor(cursor_factory=DictCursor)
        print("PostgreSQL database connection established.")

        print("Dropping existing tables (if any)...")
        cursor.execute("DROP TABLE IF EXISTS transactions CASCADE;")
        cursor.execute("DROP TABLE IF EXISTS predictions CASCADE;")
        cursor.execute("DROP TABLE IF EXISTS models CASCADE;")
        cursor.execute("DROP TABLE IF EXISTS users CASCADE;")
        print("Existing tables dropped.")

        print("Creating new tables...")
        # --- Create Tables ---
        # users table
        cursor.execute("""
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            telegram_id TEXT UNIQUE,
            balance REAL DEFAULT 0.0 NOT NULL,
            password_hash TEXT,
            api_key TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        """)
        print("Created 'users' table.")

        # models table
        cursor.execute("""
        CREATE TABLE models (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            input_token_price REAL NOT NULL,
            output_token_price REAL NOT NULL,
            is_active BOOLEAN DEFAULT TRUE
        );
        """)
        print("Created 'models' table.")

        # predictions table
        cursor.execute("""
        CREATE TABLE predictions (
            id SERIAL PRIMARY KEY,
            uuid TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            model_id INTEGER NOT NULL,
            input_text TEXT NOT NULL,
            output_text TEXT,
            input_tokens INTEGER,
            output_tokens INTEGER,
            total_cost REAL,
            status TEXT NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP WITH TIME ZONE,
            queue_time INTEGER,
            process_time INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE RESTRICT
        );
        """)
        print("Created 'predictions' table.")

        # transactions table
        cursor.execute("""
        CREATE TABLE transactions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            description TEXT,
            prediction_id INTEGER,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (prediction_id)
                REFERENCES predictions(id) ON DELETE SET NULL
        );
        """)
        print("Created 'transactions' table.")

        # --- Create Indexes ---
        print("Creating indexes...")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_users_telegram_id "
            "ON users(telegram_id);"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_models_name ON models(name);"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_predictions_uuid "
            "ON predictions(uuid);"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_predictions_user_id "
            "ON predictions(user_id);"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_transactions_user_id "
            "ON transactions(user_id);"
        )
        print("Indexes created.")

        # --- Add Default Data (Optional but helpful) ---
        print("Adding default data (if necessary)...")
        cursor.execute(
            "SELECT COUNT(*) FROM models WHERE name = %s", ('dummy-echo-v1',)
        )
        # Access by index for COUNT(*)
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO models (
                    name, description, input_token_price,
                    output_token_price, is_active
                )
                VALUES (%s, %s, %s, %s, %s)
            """, (
                'dummy-echo-v1',
                'A simple model that echoes input.',
                0.001,
                0.002,
                True
            ))
            print("Added default model 'dummy-echo-v1'.")
        else:
            print("Default model 'dummy-echo-v1' already exists.")

        # --- Add Default User (admin) ---
        print("Adding default user 'admin' (if necessary)...")
        cursor.execute(
            "SELECT COUNT(*) FROM users WHERE name = %s", ('admin',)
        )
        if cursor.fetchone()[0] == 0:
            # Hash the password for the admin user
            # IMPORTANT: In a real app, use a secure random password
            # and consider where this logic best resides.
            # For now, directly using the utility.
            # You'll need to ensure core.security.password_utils
            # is accessible here or replicate hashing.
            # This example assumes direct access for simplicity of this script.
            try:
                from core.security.password_utils import hash_password
                admin_password_hash = hash_password("admin_password")
            except ImportError:
                # Fallback or raise error if module not found
                # For this script, we might just use a placeholder
                # if direct import is an issue during init
                print(
                    "Warning: core.security.password_utils not found, "
                    "using placeholder for password hash."
                )
                admin_password_hash = "placeholder_hash"  # Not secure!

            # Generate a secure API key
            import secrets
            admin_api_key = secrets.token_hex(32)

            cursor.execute("""
                INSERT INTO users (
                    name, balance, password_hash, api_key, telegram_id
                )
                VALUES (%s, %s, %s, %s, %s)
            """, (
                'admin',
                1000.0,
                admin_password_hash,
                admin_api_key,
                None  # Admin user might not have a Telegram ID
            ))
            print(
                "Added default user 'admin' with balance 1000, "
                "hashed password, and API key."
            )
        else:
            print("Default user 'admin' already exists.")

        conn.commit()
        print("Database initialization complete and changes committed.")
    except psycopg2.Error as e:
        print(f"PostgreSQL Error during initialization: {e}")
        if conn:
            conn.rollback()
        raise
    except Exception as e:
        print(f"An unexpected error occurred during initialization: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if cursor:  # Ensure cursor exists before trying to close
            cursor.close()
        if conn:
            conn.close()
            print("PostgreSQL connection closed.")


if __name__ == "__main__":
    # This might be needed if core/infra paths are not set up in PYTHONPATH
    # for direct script execution
    project_root_for_test = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    if project_root_for_test not in sys.path:
        sys.path.insert(0, project_root_for_test)
        print(
            f"Added {project_root_for_test} to sys.path for script execution"
        )

    print("Running database initialization script for PostgreSQL...")
    try:
        initialize_database()
        print("PostgreSQL Script finished successfully.")
    except Exception as e:
        print(f"Failed to initialize PostgreSQL database: {e}")
