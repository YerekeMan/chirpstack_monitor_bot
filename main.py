import logging
from logging.handlers import RotatingFileHandler
import asyncio
from config import dp, bot
import handlers

file_handler = RotatingFileHandler(
    "bot_history.log",
    maxBytes=10 * 1024 * 1024,
    backupCount=2,
    encoding="utf-8"
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        file_handler,
        logging.StreamHandler()
    ]
)

logging.getLogger("aiogram.event").setLevel(logging.WARNING)

async def main():
    logging.info("=== Бот запущен с ротацией логов (max 10MB) ===")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())