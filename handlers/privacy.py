from aiogram import Router, types
from utils import (
	privacy_menu,
	main_menu
)

import aiosqlite
from config import DATABASE

router = Router()

@router.message(lambda message: message.text == "Удалить свой телефон из всех баз данных")
async def request_phone_for_deletion(message: types.Message):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Предоставить номер телефона", request_contact=True)]],
        resize_keyboard=True
    )
    await message.answer(
        "Для удаления вашего телефона из всех баз данных, предоставьте свой номер телефона, нажав на кнопку ниже.",
        reply_markup=keyboard
    )

@router.message(lambda message: message.contact is not None)
async def delete_phone_from_databases(message: types.Message):
    if not message.contact:
        return
    
    if message.contact.user_id != message.from_user.id:
        await message.answer(
            "Вы можете удалить только свой собственный номер телефона.",
            reply_markup=privacy_menu()
        )
        return

    try:
        phone = message.contact.phone_number
        async with aiosqlite.connect(DATABASE) as db:
            cursor = await db.execute('DELETE FROM useful_contacts WHERE contact_phone = ?', (phone,))
            await db.commit()
            deleted_count = cursor.rowcount
            logger.info(f"Удален телефон {phone} из {deleted_count} записей")
            await message.answer(
                f"Ваш телефон был успешно удален из {deleted_count} записей в базе данных.",
                reply_markup=privacy_menu()
            )
    except Exception as e:
        logger.error(f"Ошибка при удалении телефона: {e}")
        await message.answer(
            "Ошибка при удалении телефона. Попробуйте позже.",
            reply_markup=privacy_menu()
        )