
# Simple billing LLM service

Simple per-token billing LLM service with telegram bot interface.

```
│
├── core/                  # Ядро приложения (бизнес-логика)
│   ├── entities/          # Сущности (бизнес-объекты)
│   │   ├── user.py        # Пример: класс User
│   │   └── query.py       # Запрос к LLM
│   ├── use_cases/         # Сценарии использования (бизнес-правила)
│   │   ├── user_use_cases.py  # Пример: регистрация пользователя
│   │   └── llm_use_cases.py   # Логика обработки запросов к LLM
│   └── repositories/     # Интерфейсы репозиториев (абстракции для работы с данными)
│       ├── user_repository.py  # Пример: интерфейс UserRepository
│       ├── llm_repository.py   # Интерфейс для работы с LLM сервисом
│       └── queue_repository.py # Интерфейс для работы с очередью запросов
│
├── infra/       # Внешние зависимости и реализация
│   ├── db/               # Работа с базой данных
│   │   └── user_repository_impl.py  # Реализация UserRepository
│   ├── llm/              # Реализация взаимодействия с LLM-сервисом
│   │   └── llm_repository_impl.py   # Реализация LLM интерфейса
│   ├── queue/            # Реализация очереди запросов
│   │   └── queue_repository_impl.py # Обработка и хранение очереди запросов
│   ├── telegram/         # Telegram бот
│   │   └── bot.py   # Обработчики сообщений
│   └── web/              # Веб-слой (API, HTTP-запросы)
│       └── controllers/  # Контроллеры (обработчики запросов)
│           └── user_controller.py  # Пример: обработчик запросов для пользователей
│
├── config/               # Конфигурация приложения
│   ├── settings.py       # Настройки (например, подключение к БД)
│   └── llm_config.py     # Настройки для LLM-сервиса
│
│
└── main.py               # Точка входа в приложение
```

## Current status

## Installation

Current pipeline working on Python 3.10.9

1. Create inner app virtual env

    ```bash
    pip install uv
    uv pip install -r pyproject.toml
    ```

2. Run backend

    ```bash
    docker-compose up --build
    ```

3. Run client applications

    Before run any client applications, ensure backend containers is running.

    1. Telegram bot

        ```bash
        python tg_bot_start.py
        ```

    2. HTTP API

        ```bash
        python main.py
        ```

    3. Streamlit app above HTTP API

        ```bash
        streamlit run streamlit_app.py
        ```

## Layers description

Core (Ядро):

- entities: Содержит бизнес-сущности (например, User), которые представляют основные объекты предметной области.
- use_cases: Содержит сценарии использования (бизнес-логику), которые описывают, как приложение должно работать.
- repositories: Определяет интерфейсы для работы с данными (например, UserRepository). Это абстракции, которые не зависят от конкретной реализации.

Infrastructure (Инфраструктура):

- db: Реализация репозиториев (например, UserRepositoryImpl), которая работает с базой данных.
- web: Веб-слой, который обрабатывает HTTP-запросы и взаимодействует с ядром через контроллеры.

Config (Конфигурация):

- main.py:  Точка входа в приложение, где инициализируются зависимости и запускается приложение.

## Planning

- [Постановка](docs/planning/0_task.md) задачи
- [Планирование](docs/planning/1_planning.md) архитектуры, спецификация требований под выбранный сервис

---

Сделано на основе [шаблона](https://github.com/yanchick/CleanArchTemplate).
