# infra/api_client/client.py
import httpx
import logging
import os
from typing import Optional, Dict, Any

# Assuming the FastAPI backend will run locally for now
# You might want to move this to config later
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/api/v1")

class ApiClient:
    """Client for interacting with the SimpleBillingLLM FastAPI backend."""

    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        # Use a persistent client for connection pooling
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=10.0)
        logging.info(f"API Client initialized for base URL: {self.base_url}")

    async def close(self):
        """Closes the underlying HTTP client."""
        await self._client.aclose()
        logging.info("API Client closed.")

    async def get_or_create_user(self, telegram_id: str, name: str) -> Optional[Dict[str, Any]]:
        """Gets user info from the API, creating the user if they don't exist."""
        endpoint = "/users/"
        payload = {"telegram_id": telegram_id, "name": name}
        logging.info(f"Calling API: POST {endpoint} for telegram_id={telegram_id}")

        # --- Placeholder Logic --- TODO: Replace with actual API call
        logging.warning("API CALL MOCKED: get_or_create_user")
        # Simulate API response for a new or existing user
        # In a real scenario, you'd handle potential API errors (4xx, 5xx)
        # and parse the actual JSON response.
        mock_response = {
            "id": 123, # Example DB ID from API
            "name": name,
            "telegram_id": telegram_id,
            "balance": 10.0 if telegram_id != "123456789" else 100.0, # Simulate different balances
            "created_at": "2025-04-16T10:00:00Z" # Example timestamp
        }
        return mock_response
        # --- End Placeholder Logic ---

        # --- Actual API Call (when backend is ready) ---
        # try:
        #     response = await self._client.post(endpoint, json=payload)
        #     response.raise_for_status() # Raise exception for 4xx/5xx errors
        #     user_data = response.json()
        #     logging.info(f"API Response for {telegram_id}: {user_data}")
        #     return user_data
        # except httpx.RequestError as e:
        #     logging.error(f"API request failed for get_or_create_user({telegram_id}): {e}")
        #     return None
        # except httpx.HTTPStatusError as e:
        #     logging.error(f"API returned error for get_or_create_user({telegram_id}): {e.response.status_code} - {e.response.text}")
        #     return None
        # except Exception as e:
        #     logging.exception(f"Unexpected error during API call for get_or_create_user({telegram_id}): {e}")
        #     return None
        # --- End Actual API Call ---

    async def get_user_balance(self, telegram_id: str) -> Optional[float]:
        """Gets the user's current balance from the API."""
        endpoint = f"/users/by-telegram/{telegram_id}/balance"
        logging.info(f"Calling API: GET {endpoint}")

        # --- Placeholder Logic --- TODO: Replace with actual API call
        logging.warning("API CALL MOCKED: get_user_balance")
        # Simulate API response
        mock_balance = 10.0 if telegram_id != "123456789" else 100.0 # Consistent with above mock
        return mock_balance
        # --- End Placeholder Logic ---

        # --- Actual API Call (when backend is ready) ---
        # try:
        #     response = await self._client.get(endpoint)
        #     response.raise_for_status()
        #     data = response.json()
        #     balance = data.get("balance")
        #     logging.info(f"API Response for balance ({telegram_id}): {balance}")
        #     return balance if isinstance(balance, (int, float)) else None
        # except httpx.RequestError as e:
        #     logging.error(f"API request failed for get_user_balance({telegram_id}): {e}")
        #     return None
        # except httpx.HTTPStatusError as e:
        #     # Handle 404 Not Found specifically if needed
        #     if e.response.status_code == 404:
        #         logging.warning(f"User {telegram_id} not found via API for balance check.")
        #     else:
        #         logging.error(f"API returned error for get_user_balance({telegram_id}): {e.response.status_code} - {e.response.text}")
        #     return None
        # except Exception as e:
        #     logging.exception(f"Unexpected error during API call for get_user_balance({telegram_id}): {e}")
        #     return None
        # --- End Actual API Call ---

    # TODO: Add methods for creating predictions, getting prediction status, etc.

# Example usage (optional, for testing client directly)
async def _test_client():
    logging.basicConfig(level=logging.INFO)
    client = ApiClient()
    print("--- Testing get_or_create_user (new) ---")
    user1 = await client.get_or_create_user("test_tg_123", "Test User One")
    print(user1)

    print("--- Testing get_or_create_user (existing) ---")
    user2 = await client.get_or_create_user("123456789", "Existing Test User")
    print(user2)

    print("--- Testing get_user_balance (new) ---")
    balance1 = await client.get_user_balance("test_tg_123")
    print(balance1)

    print("--- Testing get_user_balance (existing) ---")
    balance2 = await client.get_user_balance("123456789")
    print(balance2)

    await client.close()

if __name__ == "__main__":
    asyncio.run(_test_client())
