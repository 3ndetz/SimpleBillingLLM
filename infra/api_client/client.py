# infra/api_client/client.py
import asyncio
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
        # Endpoint matches the controller
        endpoint = "/users/"
        payload = {"telegram_id": telegram_id, "name": name}
        logging.info(f"Calling API: POST {endpoint} for telegram_id={telegram_id}")

        # --- Actual API Call --- TODO: Replace with actual API call - *DONE*
        try:
            response = await self._client.post(endpoint, json=payload)
            # Raise exception for 4xx/5xx errors
            response.raise_for_status()
            user_data = response.json()
            logging.info(f"API Response for {telegram_id}: {user_data}")
            return user_data
        except httpx.RequestError as e:
            logging.error(
                f"API request failed for get_or_create_user({telegram_id}): {e}"
            )
            return None
        except httpx.HTTPStatusError as e:
            logging.error(
                f"API returned error for get_or_create_user({telegram_id}): "
                f"{e.response.status_code} - {e.response.text}"
            )
            return None
        except Exception as e:
            logging.exception(
                f"Unexpected error during API call for "
                f"get_or_create_user({telegram_id}): {e}"
            )
            return None
        # --- End Actual API Call ---

    async def get_user_balance(self, telegram_id: str) -> Optional[float]:
        """Gets the user's current balance from the API."""
        # Endpoint matches the controller
        endpoint = f"/users/by-telegram/{telegram_id}/balance"
        logging.info(f"Calling API: GET {endpoint}")

        # --- Actual API Call --- TODO: Replace with actual API call - *DONE*
        try:
            response = await self._client.get(endpoint)
            response.raise_for_status()
            data = response.json()
            # Extract balance from the response structure defined in controller
            balance = data.get("balance")
            logging.info(f"API Response for balance ({telegram_id}): {balance}")
            # Ensure balance is a number before returning
            return balance if isinstance(balance, (int, float)) else None
        except httpx.RequestError as e:
            logging.error(
                f"API request failed for get_user_balance({telegram_id}): {e}"
            )
            return None
        except httpx.HTTPStatusError as e:
            # Handle 404 Not Found specifically if needed
            if e.response.status_code == 404:
                logging.warning(
                    f"User {telegram_id} not found via API for balance check."
                )
            else:
                logging.error(
                    f"API returned error for get_user_balance({telegram_id}): "
                    f"{e.response.status_code} - {e.response.text}"
                )
            return None
        except Exception as e:
            logging.exception(
                f"Unexpected error during API call for "
                f"get_user_balance({telegram_id}): {e}"
            )
            return None
        # --- End Actual API Call ---

    # TODO: Add methods for creating predictions, getting prediction status, etc.

# Example usage (optional, for testing client directly)
async def _test_client():
    logging.basicConfig(level=logging.INFO)
    client = ApiClient()
    print("--- Testing get_or_create_user (new) ---")
    # Use a unique ID for testing creation
    test_id_new = f"test_tg_{asyncio.get_event_loop().time()}"
    user1 = await client.get_or_create_user(test_id_new, "Test User New")
    print(user1)

    print("--- Testing get_or_create_user (existing - assuming ID 1 exists or was created) ---")
    # Use an ID likely to exist if the API/DB is running
    test_id_existing = "123456789" # Or use test_id_new if you run test immediately after
    user2 = await client.get_or_create_user(test_id_existing, "Existing Test User")
    print(user2)

    print("--- Testing get_user_balance (new) ---")
    balance1 = await client.get_user_balance(test_id_new)
    print(balance1)

    print("--- Testing get_user_balance (existing) ---")
    balance2 = await client.get_user_balance(test_id_existing)
    print(balance2)

    print("--- Testing get_user_balance (non-existent) ---")
    balance3 = await client.get_user_balance("non_existent_id_12345")
    print(balance3)


    await client.close()

if __name__ == "__main__":
    # Make sure the API server is running before executing this test
    print("*** Ensure the FastAPI server (main.py) is running! ***")
    asyncio.run(_test_client())
