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
    from core.entities.user import User
    # Import the concrete implementation
    from infra.db.user_repository_impl import SQLiteUserRepository
except ImportError as e:
    logging.error(f"Failed to import core modules: {e}")
    sys.exit("Error: Could not import necessary core or infra modules.")
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

# --- Initialize Repository ---
# Create an instance of the user repository
user_repo = SQLiteUserRepository()

# --- Handlers ---

@dp.message(CommandStart())
async def handle_start(message: types.Message):
    """Handler for the /start command. Checks if user exists, adds if not."""
    telegram_user = message.from_user
    user_name = telegram_user.full_name
    telegram_id = str(telegram_user.id) # Ensure telegram_id is a string

    logging.info(f"Received /start command from user: {user_name} (ID: {telegram_id})")

    # Check if user exists
    # Using the initialized user_repo instance
    existing_user = user_repo.get_by_telegram_id(telegram_id)

    if existing_user:
        logging.info(f"User {telegram_id} already exists. Balance: {existing_user.balance}")
        await message.answer(
            f"Welcome back, <b>{user_name}</b>! 😊\n"
            # Show balance, formatted to 2 decimal places
            f"Your current balance is: ${existing_user.balance:.2f}"
        )
    else:
        logging.info(f"User {telegram_id} not found. Creating new user.")
        # Create new user object (balance defaults to 0.0 in entity)
        new_user = User(name=user_name, telegram_id=telegram_id)
        try:
            # Add user to the database using the repository instance
            added_user = user_repo.add(new_user)
            logging.info(f"Successfully added new user: {added_user}")
            await message.answer(
                f"Hello, <b>{user_name}</b>! 👋\n"
                f"Welcome to the Simple Billing LLM Bot. I've created an account for you.\n"
                # Show starting balance
                f"Your starting balance is: ${added_user.balance:.2f}"
            )
        except Exception as e:
            # Log the error for debugging
            logging.error(f"Failed to add user {telegram_id}: {e}")
            # Inform the user about the error
            await message.answer(
                "Sorry, there was an error creating your account. Please try again later. 😥"
            )

# --- Main Function to Start Polling ---

async def main() -> None:
    """Starts the bot polling process."""
    logging.info("Starting bot polling...")
    # Start polling - continuously checks for new updates from Telegram
    # skip_updates=True skips updates received while the bot was offline
    await dp.start_polling(bot, skip_updates=True)

# --- Entry Point ---

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot polling stopped by user (KeyboardInterrupt).")
    except Exception as e:
        logging.exception(f"An unexpected error occurred: {e}")
