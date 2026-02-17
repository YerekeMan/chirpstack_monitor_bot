import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("CHIRPSTACK_API_KEY")
URL = os.getenv("CHIRPSTACK_URL")

HEADERS = {"Grpc-Metadata-Authorization": f"Bearer {API_KEY}"}

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()