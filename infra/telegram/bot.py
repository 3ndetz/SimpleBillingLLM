# infra/telegram/bot.py
import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from dotenv import load_dotenv

"""
Using direct repository and use-case logic in Telegram bot instead of HTTP API.
"""

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
print(project_root)
sys.path.insert(0, project_root)  # Add project root to sys.path for imports

from infra.db.user_repository_impl import SQLiteUserRepository
from core.use_cases.user_use_cases import UserUseCases
from infra.db.prediction_repository_impl import SQLitePredictionRepository
from infra.db.model_repository_impl import SQLiteModelRepository
from infra.db.model_repository_impl import SQLiteModelRepository
from core.entities.prediction import Prediction as PredictionEntity
from infra.queue.tasks import process_prediction
"""
Telegram bot uses repository/use-case pipeline; no HTTP client.
"""


# --- Setup logging ---
# Configure logging for better visibility
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Load Environment Variables ---
# Construct the path to the .env file (assuming bot.py is in infra/telegram)
# Go up two levels from infra/telegram to the project root

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

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

user_repo = SQLiteUserRepository()
user_use_cases = UserUseCases(user_repo)
pred_repo = SQLitePredictionRepository()
model_repo = SQLiteModelRepository()
model_repo = SQLiteModelRepository()


# --- Handlers ---

@dp.message(CommandStart())
async def handle_start(message: types.Message):
    """Handler for /start: create or fetch user via use-case."""
    tg_user = message.from_user
    name = tg_user.full_name
    tg_id = str(tg_user.id)
    logging.info(f"Telegram: /start from {name} (ID={tg_id})")
    try:
        user = user_use_cases.get_or_create_user_by_telegram_id(
            telegram_id=tg_id,
            name=name,
        )
        await message.answer(
            f"Hello, {user.name}! 😊\n"
            f"Your current balance: ${user.balance:.2f}"
        )
    except Exception:
        logging.exception(f"Error in /start for {tg_id}")
        await message.answer(
            "Sorry, something went wrong. Please try again later. 😥"
        )
    # end /start
@dp.message(Command("info"))
async def handle_info(message: types.Message):
    """Handler for /info: provide user information."""
    tg_user = message.from_user
    name = tg_user.full_name
    tg_id = str(tg_user.id)
    logging.info(f"Telegram: /info from {name} (ID={tg_id})")
    try:
        user = user_use_cases.get_or_create_user_by_telegram_id(
            telegram_id=tg_id,
            name=name,
        )
        await message.answer(
            f"Your name: {user.name}! 😊\n"
            f"Your ID: {str(user.id)}\n"
            f"Your Telegram ID: {str(user.telegram_id)}\n"
            f"You were created at: {str(user.created_at)}\n"
            f"You were updated at: {str(user.updated_at)}\n"
            f"Your current balance: ${user.balance:.2f}"
        )
    except Exception:
        logging.exception(f"Error in /info for {tg_id}")
        await message.answer(
            "Sorry, something went wrong. Please try again later. 😥"
        )

@dp.message(Command("predict"))
async def handle_predict(message: types.Message):
    """Handler for /predict: enqueue a new prediction."""
    tg_id = str(message.from_user.id)
    user = user_use_cases.get_user_by_telegram_id(tg_id)
    if not user:
        await message.answer("Send /start first to register.")
        return
    prompt = message.text.partition(" ")[2].strip()
    if not prompt:
        await message.answer("Usage: /predict <prompt>")
        return
    if user.balance <= 0:
        await message.answer("Insufficient balance to enqueue prediction.")
        return
    # Select the active model for prediction
    active_model = model_repo.get_active_model()
    if not active_model:
        await message.answer("No active model available.")
        return
    pred = PredictionEntity(user_id=user.id, model_id=active_model.id, input_text=prompt, status="pending")
    pred = pred_repo.add(pred)
    # Enqueue prediction job using RQ instead of Celery
    process_prediction(pred.id, user.id, prompt)
    await message.answer(f"Prediction queued. UUID: {pred.uuid}")

@dp.message(Command("status"))
async def handle_status(message: types.Message):
    """Handler for /status: check prediction status/result."""
    uuid = message.text.partition(" ")[2].strip()
    if not uuid:
        await message.answer("Usage: /status <prediction_uuid>")
        return
    pred = pred_repo.get_by_uuid(uuid)
    if not pred:
        await message.answer(f"Prediction {uuid} not found.")
        return
    if pred.status != "completed":
        await message.answer(f"Status: {pred.status}")
    else:
        await message.answer(f"Result for {uuid}:\n{pred.output_text}")


# --- Main Function to Start Polling ---

def main() -> None:
    """Starts the bot polling process."""
    logging.info("Starting bot polling...")
    # Start polling - continuously checks for new updates from Telegram
    # skip_updates=True skips updates received while the bot was offline
    dp.run_polling(bot, skip_updates=True)
    logging.info("Bot poller stopped.")

# --- Entry Point ---

if __name__ == "__main__":
    try:
        import time
        dp.run_polling(bot, skip_updates=True)
        time.sleep(100)
    except KeyboardInterrupt:
        logging.info("Bot polling stopped by user (KeyboardInterrupt).")
    except Exception as e:
        logging.exception(f"An unexpected error occurred: {e}")
