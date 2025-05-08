import logging
import os
import sys

# Third-party imports
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv

# Determine the project root directory and add to sys.path
# This needs to be done before project-specific imports
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, project_root)

# Project-specific imports
from core.entities.prediction import Prediction as PredictionEntity
from core.use_cases.user_use_cases import UserUseCases
from infra.db.model_repository_impl import PostgreSQLModelRepository  # Renamed
from infra.db.prediction_repository_impl import (  # Renamed
    PostgreSQLPredictionRepository,
)
from infra.db.user_repository_impl import PostgreSQLUserRepository  # Renamed
from infra.queue.tasks import process_prediction


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Load environment variables from .env file
dotenv_path = os.path.join(project_root, '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
    logging.info(f"Loaded .env file from: {dotenv_path}")
else:
    logging.warning(
        f".env file not found at: {dotenv_path}. Bot token might be missing."
    )

BOT_TOKEN = os.getenv("TELEGRAM_BOT_API")

if not BOT_TOKEN:
    logging.error(
        "TELEGRAM_BOT_API token not found in environment variables. Exiting."
    )
    sys.exit(1)


# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

user_repo = PostgreSQLUserRepository()  # Renamed
user_use_cases = UserUseCases(user_repo)
pred_repo = PostgreSQLPredictionRepository()  # Renamed
model_repo = PostgreSQLModelRepository()  # Renamed


# --- Handlers ---

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    """
    This handler will be called when user sends `/start` command
    """
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
async def send_info(message: types.Message):
    """
    This handler will be called when user sends `/info` command
    """
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
async def predict_command(message: types.Message):
    """
    Handles the /predict command.
    """
    tg_id = str(message.from_user.id)
    user = user_use_cases.get_user_by_telegram_id(tg_id)
    if not user:
        await message.answer("Send /start first to register.")
        return
    prompt = message.text.partition(" ")[2].strip()
    if not prompt:
        await message.reply(
            "Please provide some text after the /predict command. "
            "Usage: /predict <your text>"
        )
        return

    user_id = message.from_user.id
    if user.balance <= 0:
        await message.answer("Insufficient balance to enqueue prediction.")
        return
    # Select the active model for prediction
    active_model = model_repo.get_active_model()
    if not active_model:
        await message.answer("No active model available.")
        return
    # Create prediction entity
    pred = PredictionEntity(
        user_id=user.id,
        model_id=active_model.id,
        input_text=prompt,
        status="pending",
    )
    prediction_id = pred_repo.add(pred)
    logging.info(
        f"Prediction ID {prediction_id} for user {user_id} sent to queue."
    )  # Used prediction_id and shortened line

    # Send to Celery queue
    process_prediction(pred.id, user.id, prompt)
    await message.answer(f"Prediction queued. UUID: {pred.uuid}")


@dp.message(Command("status"))
async def status_command(message: types.Message):
    """
    Handles the /status command to check prediction status.
    """
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
    logging.info("Starting bot...")
    main()
