import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import TOKEN
from utils.db import init_db
from handlers import common, social_circle, useful_contacts, notifications, privacy, double_handshake

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Регистрируем все роутеры
dp.include_router(common.router)
dp.include_router(social_circle.router)
dp.include_router(useful_contacts.router)
dp.include_router(notifications.router)
dp.include_router(privacy.router)
dp.include_router(double_handshake.router)

async def main():
    await init_db()	
    await dp.start_polling(bot)

if name == "__main__":
    asyncio.run(main())