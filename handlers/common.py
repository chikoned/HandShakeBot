from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from utils import main_menu
import aiosqlite
from config import DATABASE

router = Router()

@router.message(Command("start"))
async def start_handler(message: types.Message):
    try:
        user = message.from_user
        logger.info(f"Пользователь {user.id} ({user.full_name or user.first_name}) начал регистрацию")

        async with aiosqlite.connect(DATABASE) as db:
            await db.execute('''
                INSERT OR IGNORE INTO users (user_id, username, full_name)
                VALUES (?, ?, ?)
            ''', (user.id, user.username, user.full_name or user.first_name))
            await db.commit()
            logger.info(f"Пользователь {user.id} успешно зарегистрирован в базе данных")

            async with db.execute('''
                SELECT user_id, contact_name
                FROM social_circle
                WHERE contact_id = ?
            ''', (user.id,)) as cursor:
                linked_users = await cursor.fetchall()

        if linked_users:
            for linked_user_id, contact_name in linked_users:
                try:
                    user_link = (
                        f"[{contact_name}](tg://user?id={user.id})"
                        if user.id else f"@{message.from_user.username}"
                    )
                    await bot.send_message(
                        linked_user_id,
                         f"Ваш контакт {user_link} зарегистрировался в боте!",
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.error(f"Ошибка при отправке уведомления пользователю {linked_user_id}: {e}")

        await message.answer("Добро пожаловать! Выберите действие из меню:", reply_markup=main_menu())
    except Exception as e:
        logger.error(f"Ошибка в обработчике start: {e}")
        await message.answer("Произошла ошибка при регистрации. Попробуйте позже.")