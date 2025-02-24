from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from utils import (
	two_handshake_menu,
	main_menu
)

import aiosqlite
from config import DATABASE

router = Router()

@router.message(lambda message: message.text == "Просмотреть полезные контакты круга общения")
async def view_useful_contacts_of_social_circle(message: types.Message):
    """Выводит полезные контакты круга общения пользователя, если оба пользователя есть друг у друга в круге общения."""
    user_id = message.from_user.id

    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute('''
            SELECT u1.contact_name AS owner_name, uc.contact_name AS useful_name,
                   uc.contact_phone, uc.description
            FROM social_circle AS u1
            JOIN social_circle AS u2 ON u1.contact_id = u2.user_id AND u2.contact_id = u1.user_id
            JOIN useful_contacts AS uc ON u1.contact_id = uc.user_id
            WHERE u1.user_id = ?
        ''', (user_id,)) as cursor:
            contacts = await cursor.fetchall()

    if not contacts:
        await message.answer("У ваших контактов из круга общения нет доступных полезных контактов.")
    else:
        response = "Полезные контакты вашего круга общения (только взаимные связи):\n\n"
        for owner_name, useful_name, contact_phone, description in contacts:
            response += (
                f"От: {owner_name}\n"
                f"Имя: {useful_name}\n"
                f"Телефон: {contact_phone}\n"
                f"Описание: {description}\n"
                f"{'='*30}\n"
            )
        await message.answer(response)

@router.message(lambda message: message.text == "Два рукопожатия")
async def two_handshake_menu_handler(message: types.Message):
    await message.answer("Выберите действие:", reply_markup=two_handshake_menu())

@router.message(lambda message: message.text == "Вернуться в главное меню")
async def back_to_main_menu(message: types.Message):
    await message.answer("Вы вернулись в главное меню. Выберите действие:", reply_markup=main_menu())
    logging.info(f"Пользователь {message.from_user.id} вернулся в главное меню.")

# --- Поиск полезных контактов с использованием FSM ---
@router.message(lambda message: message.text == "Поиск полезных контактов")
async def search_useful_contacts(message: types.Message, state: FSMContext):
    await message.answer("Введите ключевое слово для поиска:")
    await state.set_state(SearchUsefulState.WAITING_FOR_KEYWORD)

@router.message(SearchUsefulState.WAITING_FOR_KEYWORD)
async def perform_search(msg: types.Message, state: FSMContext):
    search_term = msg.text.strip()
    keyword = f"%{search_term}%"
    try:
        async with aiosqlite.connect(DATABASE) as db:
            async with db.execute('''
                SELECT DISTINCT 
                    u.username,
                    uc.contact_name,
                    uc.contact_phone,
                    uc.description
                FROM social_circle AS sc
                JOIN useful_contacts AS uc ON sc.contact_id = uc.user_id
                JOIN users AS u ON sc.contact_id = u.user_id
                WHERE 
                    uc.description LIKE ? OR
                    uc.contact_name LIKE ? OR
                    uc.contact_phone LIKE ?
                ORDER BY 
                    CASE 
                        WHEN uc.description LIKE ? THEN 1
                        WHEN uc.contact_name LIKE ? THEN 2
                        ELSE 3
                    END
            ''', (keyword, keyword, keyword, keyword, keyword)) as cursor:
                results = await cursor.fetchall()

        if not results:
            keyword_lower = f"%{search_term.lower()}%"
            async with aiosqlite.connect(DATABASE) as db:
                async with db.execute('''
                    SELECT DISTINCT 
                        u.username,
                        uc.contact_name,
                        uc.contact_phone,
                        uc.description
                    FROM social_circle AS sc
                    JOIN useful_contacts AS uc ON sc.contact_id = uc.user_id
                    JOIN users AS u ON sc.contact_id = u.user_id
                    WHERE 
                        LOWER(uc.description) LIKE ? OR
                        LOWER(uc.contact_name) LIKE ? OR
                        LOWER(uc.contact_phone) LIKE ?
                ''', (keyword_lower, keyword_lower, keyword_lower)) as cursor:
                    results = await cursor.fetchall()

        if not results:
            await msg.answer(
                "Контакты с таким ключевым словом не найдены.\n"
                "Попробуйте другое ключевое слово или часть слова."
            )
            logger.info(f"Поиск по ключевому слову '{search_term}' не дал результатов")
        else:
            response = "Найденные контакты:\n\n"
            for owner, name, phone, description in results:
                response += (
                    f"От: {owner}\n"
                    f"Имя: {name}\n"
                    f"Телефон: {phone}\n"
                    f"Описание: {description}\n"
                    f"{'='*30}\n"
                )
            await msg.answer(response)
            logger.info(f"Найдено {len(results)} контактов по запросу '{search_term}'")
    except Exception as e:
        logger.error(f"Ошибка при поиске контактов: {e}")
        await msg.answer("Ошибка при поиске. Попробуйте позже.")
    await state.clear()