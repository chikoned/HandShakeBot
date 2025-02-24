from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from utils import (
	main_menu,
	social_circle_menu,
	addition_keyboard,
	deletion_keyboard,
	AddContactStates,
	DeleteSocialState
)

import aiosqlite
from config import DATABASE

router = Router()

@router.message(lambda message: message.text == "Добавить круг общения")
async def start_adding_social_contacts(message: types.Message, state: FSMContext):
    await state.set_state(AddContactStates.ADD_SOCIAL_CIRCLE)
    await message.answer(
        "Отправьте контакт для добавления в круг общения. Для этого сначала нажмите скрепку слева внизу, потом 'Контакт' внизу справа, и выберите подходящий контакт",
        reply_markup=addition_keyboard()
                )
    

@router.message(AddContactStates.ADD_SOCIAL_CIRCLE)
async def add_social_circle_contact(message: types.Message, state: FSMContext):
    if message.text == "Завершить добавление":
        await state.clear()
        logger.info(f"Пользователь {message.from_user.id} завершил добавление круга общения")
        await message.answer("Добавление круга общения завершено.", reply_markup=social_circle_menu())
        return

    if not message.contact:
        await message.answer("Отправьте контакт или нажмите 'Завершить добавление'")
        return

    contact = message.contact
    try:
        async with aiosqlite.connect(DATABASE) as db:
            async with db.execute(
                'SELECT user_id FROM users WHERE user_id = ?',
                (contact.user_id,)
            ) as cursor:
                user_exists = await cursor.fetchone()

            await db.execute('''
                INSERT INTO social_circle (user_id, contact_id, contact_name)
                VALUES (?, ?, ?)
            ''', (message.from_user.id, contact.user_id, f"{contact.first_name} {contact.last_name or ''}"))
            await db.commit()

            if user_exists:
                user = message.from_user
                contact_name = f"{message.from_user.full_name}" 
                user_link = (
                    f"[{contact_name}](tg://user?id={message.from_user.id})"
                    if message.from_user.id else f"@{message.from_user.username}"
                )
                try:
                    await bot.send_message(
                        contact.user_id,
                        f"{user_link} добавил вас в свой круг общения!",
                        parse_mode="Markdown"
                    )
                    logger.info(f"Отправлено уведомление пользователю {contact.user_id}")
                except Exception as e:
                    logger.error(f"Ошибка при отправке уведомления: {e}")

        await message.answer("Контакт успешно добавлен")
        
    except aiosqlite.IntegrityError:
        await message.answer("Этот контакт уже есть в вашем круге общения")
    except Exception as e:
        logger.error(f"Ошибка при добавлении контакта: {e}")
        await message.answer("Произошла ошибка при добавлении контакта")

@router.message(lambda message: message.text == "Просмотреть круг общения")
async def view_social_circle(message: types.Message):
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute('SELECT contact_name FROM social_circle WHERE user_id = ?', (message.from_user.id,)) as cursor:
            contacts = await cursor.fetchall()
    if contacts:
        response = "Ваш круг общения:\n"
        for (name,) in contacts:
            response += f"{name}\n"
        await message.answer(response)
    else:
        await message.answer("Ваш круг общения пуст.")

@router.message(lambda message: message.text == "Удалить круг общения")
async def delete_all_social_circle_contacts(message: types.Message):
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute('DELETE FROM social_circle WHERE user_id = ?', (message.from_user.id,))
        await db.commit()
    await message.answer("Все контакты из круга общения удалены.")

async def show_social_deletion_list(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute('SELECT id, contact_name FROM social_circle WHERE user_id = ?', (user_id,)) as cursor:
            contacts = await cursor.fetchall()
    if not contacts:
        await message.answer("Ваш круг общения пуст.", reply_markup=social_circle_menu())
        await state.clear()
        return False
    deletion_map = {}
    response = "Ваш круг общения:\n"
    for i, (db_id, name) in enumerate(contacts, start=1):
        deletion_map[i] = db_id
        response += f"{i}. {name}\n"
    response += "\nВведите номер контакта для удаления или нажмите 'Завершить удаление':"
    await state.update_data(social_deletion_map=deletion_map)
    await message.answer(response, reply_markup=deletion_keyboard())
    return True


@router.message(lambda message: message.text == "Круг общения")
async def social_circle_menu_handler(message: types.Message):
    await message.answer("Выберите действие:", reply_markup=social_circle_menu())

@router.message(lambda message: message.text == "Вернуться в главное меню")
async def back_to_main_menu(message: types.Message):
    await message.answer("Вы вернулись в главное меню. Выберите действие:", reply_markup=main_menu())
    logging.info(f"Пользователь {message.from_user.id} вернулся в главное меню.")

@router.message(lambda message: message.text == "Удалить контакт из круга общения")
async def delete_social_contact(message: types.Message, state: FSMContext):
    if await show_social_deletion_list(message, state):
        await state.set_state(DeleteSocialState.WAITING_FOR_CONTACT_ID)

@router.message(DeleteSocialState.WAITING_FOR_CONTACT_ID)
async def process_social_deletion(msg: types.Message, state: FSMContext):
    if msg.text == "Завершить удаление":
        await msg.answer("Удаление завершено.", reply_markup=social_circle_menu())
        await state.clear()
        return
    data = await state.get_data()
    deletion_map = data.get("social_deletion_map", {})
    try:
        selection = int(msg.text.strip())
    except ValueError:
        await msg.answer("Пожалуйста, введите корректный номер.", reply_markup=deletion_keyboard())
        return
    if selection not in deletion_map:
        await msg.answer("Контакт с таким номером не найден. Попробуйте снова или нажмите 'Завершить удаление'.", reply_markup=deletion_keyboard())
        return
    actual_contact_id = deletion_map[selection]
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute('DELETE FROM social_circle WHERE id = ? AND user_id = ?', (actual_contact_id, msg.from_user.id))
        await db.commit()
    await msg.answer("Контакт успешно удалён.")
    # Обновляем список после удаления, чтобы пользователь мог продолжать удалять, пока не нажмёт "Завершить удаление"
    if not await show_social_deletion_list(msg, state):
        return