# infra/telegram/bot.py
import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from dotenv import load_dotenv

# --- Start of new imports ---
# Add project root to sys.path to find core modules
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    # Import the API Client instead of the repository
    from infra.api_client.client import ApiClient
except ImportError as e:
    logging.error(f"Failed to import API client module: {e}")
    sys.exit("Error: Could not import necessary infra modules.")
# --- End of new imports ---


# --- Setup logging ---
# Configure logging for better visibility
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Load Environment Variables ---
# Construct the path to the .env file (assuming bot.py is in infra/telegram)
# Go up two levels from infra/telegram to the project root
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
dotenv_path = os.path.join(project_root, '.env')

# Load the .env file
if os.path.exists(dotenv_path):
    logging.info(f"Loading environment variables from: {dotenv_path}")
    load_dotenv(dotenv_path=dotenv_path)
else:
    logging.warning(f".env file not found at: {dotenv_path}. Bot token might be missing.")

# --- Get Bot Token ---
BOT_TOKEN = os.getenv('TELEGRAM_BOT_API')

if not BOT_TOKEN:
    logging.error("TELEGRAM_BOT_API token not found in environment variables. Exiting.")
    sys.exit("Error: TELEGRAM_BOT_API token is not set.")

# --- Initialize Bot and Dispatcher ---
# Initialize Bot instance with default parse mode which supports basic Markdown/HTML
bot = Bot(token=BOT_TOKEN) # DO NOT ADD STUPID parse_mode
# Initialize Dispatcher instance
dp = Dispatcher()

# --- Initialize API Client ---
# Create an instance of the API client
# The client will use the API_BASE_URL from environment or default
api_client = ApiClient()


# --- Handlers ---

@dp.message(CommandStart())
async def handle_start(message: types.Message):
    """Handler for the /start command. Uses API client to get/create user."""
    telegram_user = message.from_user
    user_name = telegram_user.full_name
    telegram_id = str(telegram_user.id) # Ensure telegram_id is a string

    logging.info(f"Received /start command from user: {user_name} (ID: {telegram_id})")

    try:
        # Call the API to get or create the user
        user_data = await api_client.get_or_create_user(telegram_id=telegram_id, name=user_name)

        if user_data:
            # Assuming the API returns user data including balance
            balance = user_data.get('balance', 0.0) # Default to 0.0 if balance not in response
            api_user_name = user_data.get('name', user_name) # Use name from API if available

            logging.info(f"API returned user data for {telegram_id}: {user_data}")
            await message.answer(
                f"Hello again, <b>{api_user_name}</b>! 😊\n"
                f"Your current balance is: ${balance:.2f}"
            )
        else:
            # Handle case where API call fails or returns None
            logging.error(f"API client failed to get or create user {telegram_id}.")
            await message.answer(
                "Sorry, there was an issue accessing your account information. Please try again later. 😥"
            )

    except Exception as e:
        # Log the error for debugging
        logging.exception(f"Error processing /start for user {telegram_id}: {e}")
        # Inform the user about the error
        await message.answer(
            "Sorry, an unexpected error occurred. Please try again later. 😥"
        )


# --- Main Function to Start Polling ---

async def main() -> None:
    """Starts the bot polling process."""
    logging.info("Starting bot polling...")
    try:
        # Start polling - continuously checks for new updates from Telegram
        # skip_updates=True skips updates received while the bot was offline
        await dp.start_polling(bot, skip_updates=True)
    finally:
        # Ensure the API client's session is closed gracefully
        await api_client.close()
        logging.info("API Client closed.")

# --- Entry Point ---

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot polling stopped by user (KeyboardInterrupt).")
    except Exception as e:
        logging.exception(f"An unexpected error occurred: {e}")
