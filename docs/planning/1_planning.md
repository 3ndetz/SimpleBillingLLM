# Planning

Should be complimentary to task description: docs\planning\0_task.md

## System overall description

Simple billing LLM service.

External Interface - telegram bot (aiogram)

1. Проработка бизнес и намётки по БЛ(концепции)
    1. Пользователь
        1. Логин (name, got from telegram)
        2. Пароль (not used when telegram bind)
        3. Telegram user id
        4. Баланс (float, spent when user using the LLM, calculation varies on token and model) 
        5. ИД (DB)
    2. Модельки
        1. Список моделей LLM (will be 1 model for now)
            1. Model ID
            2. Price per input token
            3. Price per output token
        2. Predict table
            1. User ID
            2. Model ID
            3. User Input
            4. Prediction Result
        3. Код красиво и асинхронно predict next token
           1. Priority queue for multiple users.
           Queue conditions:
           - Refuse queue putting on too big current queue (>100)
           - Alternately adding tasks from the queue depending on the unique user (попеременно исполняем задачи для каждого юзера чтоб не было застоя на одном)
           - Queue entry deletion support
           - Queue time counter, process time counter

    3. Слой биллинга
        1. Ставим задачу на расчет.
            1. проверить  баланс и все вокруг
            2. звездочку - пополнить баланс
        2. История транзакций
        3. тарифы (цены за токены)
        4. бонусы, скидосы (пока без этого)
2. Дизайн АПИ
    1. /users  - get post
       1. get user info
       2. post new user
    2. /model - get
       1. get model info
    3. Авторизации
       1. пока без этого, т.к. у нас тг бот
    4. /predict - пост (new predict), гет (get result)
        1. /predict/{uuid}
3. Дизайн базы данных
    1. Таблички
4. Слой БЛ
        1.  АПИ - слой БЛ - БД - Слой БД - возращаем чо-то в апи
5. Пользовательский интерфейс(стримлит, даш), TG BOT
    1. логин
    2. послать задачу
    3. история моих посылок акк транзакции
    4. пополнить баланс
6. Наблюдатели и все-все-все

## Database (simpliest, sqlite)

### Description

Текстовое описание таблицы

1. **users** - для хранения информации о пользователях:
   - id, имя, telegram_id и баланс пользователя
   - дата создания учетной записи

2. **models** - для хранения информации о доступных LLM моделях:
   - id, название, описание модели
   - цены за входные и выходные токены
   - флаг активности модели

3. **predictions** - для хранения информации о запросах предсказаний:
   - id, uuid для удобного API доступа
   - связи с пользователем и моделью
   - входной и выходной текст
   - количество токенов и общая стоимость
   - статус запроса и метрики времени выполнения

4. **transactions** - для учета пополнений и списаний:
   - id, связь с пользователем
   - сумма транзакции (положительная - пополнение, отрицательная - списание)
   - описание и связь с предсказанием (если применимо)

5. **queue_items** - для реализации очереди задач:
   - id, связи с предсказанием и пользователем
   - приоритет и статус элемента очереди
   - время постановки в очередь

### SQLite DDL creation code

WARNING!
TODO:
NOT IDEAL!
TOO HARD FOR NOW! TABLE MAY BE REVISED COMPLETELY TO MAKE MORE SIMPLIER!

```sql
-- Таблица пользователей
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,                     -- имя пользователя из телеграма
    telegram_id TEXT UNIQUE,                -- ID пользователя из телеграма
    balance REAL DEFAULT 0.0 NOT NULL,      -- текущий баланс пользователя
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица моделей
CREATE TABLE models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,              -- название модели
    description TEXT,                       -- описание модели
    input_token_price REAL NOT NULL,        -- цена за входной токен
    output_token_price REAL NOT NULL,       -- цена за выходной токен
    is_active BOOLEAN DEFAULT TRUE          -- активна ли модель
);

-- Таблица предсказаний
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

-- Таблица транзакций
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

-- Таблица очереди
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

-- Индексы для ускорения запросов
CREATE INDEX idx_predictions_user_id ON predictions(user_id);
CREATE INDEX idx_transactions_user_id ON transactions(user_id);
CREATE INDEX idx_queue_items_user_id ON queue_items(user_id);
CREATE INDEX idx_queue_items_status ON queue_items(status);
```
