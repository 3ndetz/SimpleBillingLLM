import sqlite3
import os
import sys

# Define the path for the SQLite database file relative to the project root
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data')
DB_PATH = os.path.join(DB_DIR, 'billing_llm.db')

def initialize_database():
    """
    Initializes the SQLite database by creating tables based on the DDL schema.
    Creates the data directory if it doesn't exist.
    """
    print(f"Ensuring database directory exists at: {DB_DIR}")
    os.makedirs(DB_DIR, exist_ok=True) # Create the data directory if it doesn't exist

    print(f"Connecting to database at: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    print("Database connection established.")

    # Drop existing tables if they exist (for clean initialization during development)
    # In a production scenario, you'd use migrations.
    print("Dropping existing tables (if any)...")
    cursor.execute("DROP TABLE IF EXISTS queue_items;")
    cursor.execute("DROP TABLE IF EXISTS transactions;")
    cursor.execute("DROP TABLE IF EXISTS predictions;")
    cursor.execute("DROP TABLE IF EXISTS models;")
    cursor.execute("DROP TABLE IF EXISTS users;")
    print("Existing tables dropped.")

    print("Creating new tables...")
    # --- Create Tables ---
    # users table
    cursor.execute("""
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,                     -- имя пользователя из телеграма
        telegram_id TEXT UNIQUE,                -- ID пользователя из телеграма
        balance REAL DEFAULT 0.0 NOT NULL,      -- текущий баланс пользователя
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    print("Created 'users' table.")

    # models table
    cursor.execute("""
    CREATE TABLE models (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,              -- название модели
        description TEXT,                       -- описание модели
        input_token_price REAL NOT NULL,        -- цена за входной токен
        output_token_price REAL NOT NULL,       -- цена за выходной токен
        is_active BOOLEAN DEFAULT TRUE          -- активна ли модель
    );
    """)
    print("Created 'models' table.")

    # predictions table
    cursor.execute("""
    CREATE TABLE predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        uuid TEXT UNIQUE NOT NULL,              -- уникальный идентификатор предсказания
        user_id INTEGER NOT NULL,               -- ID пользователя
        model_id INTEGER NOT NULL,              -- ID модели
        input_text TEXT NOT NULL,               -- входной текст
        output_text TEXT,                       -- текст предсказания
        input_tokens INTEGER,                   -- количество входных токенов
        output_tokens INTEGER,                  -- количество выходных токенов
        total_cost REAL,                        -- полная стоимость
        status TEXT NOT NULL,                   -- статус: pending, processing, completed, failed
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP,
        queue_time INTEGER,                     -- время в очереди в миллисекундах
        process_time INTEGER,                   -- время обработки в миллисекундах
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (model_id) REFERENCES models(id)
    );
    """)
    print("Created 'predictions' table.")

    # transactions table
    cursor.execute("""
    CREATE TABLE transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,               -- ID пользователя
        amount REAL NOT NULL,                   -- сумма транзакции (положительная - пополнение, отрицательная - списание)
        description TEXT,                       -- описание транзакции
        prediction_id INTEGER,                  -- ссылка на предсказание (если транзакция связана с предсказанием)
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (prediction_id) REFERENCES predictions(id)
    );
    """)
    print("Created 'transactions' table.")

    # queue_items table
    cursor.execute("""
    CREATE TABLE queue_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        prediction_id INTEGER UNIQUE NOT NULL,  -- ID предсказания
        user_id INTEGER NOT NULL,               -- ID пользователя
        priority INTEGER DEFAULT 0,             -- приоритет в очереди
        status TEXT NOT NULL,                   -- статус: waiting, processing, completed, canceled
        queued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (prediction_id) REFERENCES predictions(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
    """)
    print("Created 'queue_items' table.")

    # --- Create Indexes ---
    print("Creating indexes...")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_models_name ON models(name);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_predictions_uuid ON predictions(uuid);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_predictions_user_id ON predictions(user_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_queue_items_prediction_id ON queue_items(prediction_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_queue_items_user_id ON queue_items(user_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_queue_items_status ON queue_items(status);")
    print("Indexes created.")

    # --- Add Default Data (Optional but helpful) ---
    print("Adding default data (if necessary)...")
    # Add a default model if none exists
    cursor.execute("SELECT COUNT(*) FROM models WHERE name = 'dummy-echo-v1'")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO models (name, description, input_token_price, output_token_price, is_active)
            VALUES (?, ?, ?, ?, ?)
        """, ('dummy-echo-v1', 'A simple model that echoes input.', 0.001, 0.002, 1))
        print("Added default model 'dummy-echo-v1'.")
    else:
        print("Default model 'dummy-echo-v1' already exists.")

    # Commit changes and close connection
    conn.commit()
    conn.close()
    print("Database initialization complete.")


if __name__ == "__main__":
    print("Running database initialization script...")
    initialize_database()
    print("Script finished.")

