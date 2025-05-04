# Start Telegram bot
import time


if __name__ == "__main__":
    import logging
    import asyncio
    from infra.telegram.bot import dp, bot

    logging.basicConfig(level=logging.DEBUG)

    try:
        dp.run_polling(bot, skip_updates=True)
        time.sleep(100)
    except KeyboardInterrupt:
        logging.info("Bot polling stopped by user (KeyboardInterrupt).")
    except Exception as e:
        logging.exception(f"An unexpected error occurred: {e}")
    finally:
        logging.info("Bot polling stopped.")