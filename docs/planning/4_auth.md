# Authorization Plan for HTTP API

## 1. Objectives

- Prevent unauthorized calls to user and prediction endpoints.
- Ensure each request is tied to a valid, authenticated user.
- Maintain simplicity and minimal code changes.

## 2. Proposed Approach for the HTTP API

### User Authentication (Register and Login)

1. On registration (user create):
   - Validate password payload.
   - Hash password using `passlib` (e.g. `CryptContext(schemes=["bcrypt"])`) in `core/security/password_utils.py`.
   - Store `password_hash` in `core/entities/user.py` via `infra/db/user_repository_impl.py`.
2. On login:
   - Retrieve user by email using `core/repositories/user_repository.py`.
   - Verify password with `password_utils.verify`.

### API Key for Predictions

1. Add nullable `api_key` field to `core/entities/user.py` and corresponding column in `infra/db/initialize_db.py` migration.
2. Create POST /apikey in `web/controllers/auth_controller.py`:
   - Require valid user login (basic http auth).
   - Generate secure API key (e.g. `secrets.token_hex(32)`).
   - Store `api_key` for the user in `user_repository_impl.py`.
   - Return key in response.
3. Protect /predict endpoint in `web/controllers/prediction_controller.py`:
   - Read API key from `X-API-KEY` header.
   - Validate against `user_repository.get_by_api_key`.
   - Reject unauthorized requests (HTTP 401).

### File Changes Overview

- Add `core/security/password_utils.py` (hashing and verification).
- Update `core/entities/user.py` to include `password_hash` and `api_key`.
- Update `infra/db/initialize_db.py` to alter user table.
- Update `infra/db/user_repository_impl.py` to handle `password_hash` and `api_key`.
- Create `web/controllers/auth_controller.py` endpoints.
- Update `web/controllers/prediction_controller.py` to enforce API key header.

## 3. TODO List

- [ ] Define password hashing utilities (`core/security/password_utils.py`).
- [ ] Update database schema and migration for user table.
- [ ] Implement repository updates in `infra/db/user_repository_impl.py`.
- [ ] Implement business logic in `core/use_cases/user_use_cases.py`.
- [ ] Add to tg bot api key command.
- [ ] (Optional) Simple app for http web integration (may be in streamlit).
- [ ] Secure `/predict` with API key validation.
- [ ] Write unit tests for:
    - Registration and login flows.
    - API key generation and validation.
    - Protected prediction endpoint.