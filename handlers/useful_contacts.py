from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from utils import (
	main_menu,
	useful_contacts_menu,
	addition_keyboard,
	deletion_keyboard,
	AddContactStates,
	EditContactStates,
	DeleteUsefulState
)

import aiosqlite
from config import DATABASE

router = Router()

# --- Добавление полезных контактов ---
@router.message(lambda message: message.text == "Добавить полезные контакты")
async def start_adding_useful_contacts(message: types.Message, state: FSMContext):
    logger.info(f"Пользователь {message.from_user.id} начал добавлять полезные контакты.")
    await state.set_state(AddContactStates.ADD_USEFUL_CONTACT)
    await message.answer(
        "Отправьте контакт для добавления в полезные контакты. Для этого сначала нажмите скрепку слева внизу, потом 'Контакт' внизу справа, и выберите подходящий контакт. \n Напишите пару слов о том, чем может быть полезен ваш контакт. И, пожалуйста, укажите локацию.",
        reply_markup=addition_keyboard()
            )
    

@router.message(AddContactStates.ADD_USEFUL_CONTACT)
async def add_useful_contact(message: types.Message, state: FSMContext):
    logger.info(f"Получено сообщение: {message.text}")
    if message.text == "Завершить добавление":
        await state.clear()
        logger.info(f"Пользователь {message.from_user.id} завершил добавление полезных контактов.")
        await message.answer("Добавление полезных контактов завершено.", reply_markup=useful_contacts_menu())
        return

    if not message.contact:
        await message.answer("Отправьте контакт или нажмите 'Завершить добавление'.")
        return

    contact = message.contact
    await state.update_data(contact_name=f"{contact.first_name} {contact.last_name or ''}", contact_phone=contact.phone_number)
    await state.set_state(AddContactStates.ADD_DESCRIPTION)
    await message.answer("Введите описание для этого контакта.")

@router.message(AddContactStates.ADD_DESCRIPTION)
async def save_contact_with_description(message: types.Message, state: FSMContext):
    data = await state.get_data()
    contact_name = data["contact_name"]
    contact_phone = data["contact_phone"]

    raw_text = message.text
    description = raw_text.strip()
    description = description.lstrip("\ufeff\u200b")

    logging.info(f"[save_contact_with_description] Description (raw): {repr(raw_text)}")
    logging.info(f"[save_contact_with_description] Description (strip): {repr(description)}")
    desc_bytes = description.encode('utf-8')

    try:
        async with aiosqlite.connect(DATABASE) as db:
            await db.execute('''
                INSERT INTO useful_contacts (user_id, contact_name, contact_phone, description)
                VALUES (?, ?, ?, ?)
            ''', (message.from_user.id, contact_name, contact_phone, description))
            await db.commit()

        logging.info(
            f"Контакт '{contact_name}' (тел. {contact_phone}) с описанием '{description}' добавлен пользователем {message.from_user.id}."
        )
        await message.answer("Контакт с описанием успешно добавлен.",
                             reply_markup=addition_keyboard())
    except aiosqlite.IntegrityError as e:
        logging.error(f"Ошибка при добавлении контакта: {e}")
        await message.answer("Не удалось добавить контакт. Возможно, он уже есть в базе.")
    finally:
        await state.set_state(AddContactStates.ADD_USEFUL_CONTACT)

@router.message(lambda message: message.text == "Просмотреть полезные контакты")
async def view_useful_contacts(message: types.Message):
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute('SELECT contact_name, contact_phone, description FROM useful_contacts WHERE user_id = ?', (message.from_user.id,)) as cursor:
            contacts = await cursor.fetchall()
    if contacts:
        response = "Ваши полезные контакты:\n"
        for name, phone, desc in contacts:
            response += f"{name}. {phone}. {desc}\n"
        await message.answer(response)
    else:
        await message.answer("Ваш список полезных контактов пуст.")

@router.message(lambda message: message.text == "Удалить все контакты")
async def delete_all_useful_contacts(message: types.Message):
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute('DELETE FROM useful_contacts WHERE user_id = ?', (message.from_user.id,))
        await db.commit()
    await message.answer("Все полезные контакты удалены.")

async def show_useful_deletion_list(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute('SELECT id, contact_name FROM useful_contacts WHERE user_id = ?', (user_id,)) as cursor:
            contacts = await cursor.fetchall()
    if not contacts:
        await message.answer("Ваш список полезных контактов пуст.", reply_markup=useful_contacts_menu())
        await state.clear()
        return False
    deletion_map = {}
    response = "Ваши полезные контакты:\n"
    for i, (db_id, name) in enumerate(contacts, start=1):
        deletion_map[i] = db_id
        response += f"{i}. {name}\n"
    response += "\nВведите номер контакта для удаления или нажмите 'Завершить удаление':"
    await state.update_data(useful_deletion_map=deletion_map)
    await message.answer(response, reply_markup=deletion_keyboard())
    return True

@router.message(lambda message: message.text == "Полезные контакты")
async def useful_contacts_menu_handler(message: types.Message):
    await message.answer("Выберите действие:", reply_markup=useful_contacts_menu())

@router.message(lambda message: message.text == "Вернуться в главное меню")
async def back_to_main_menu(message: types.Message):
    await message.answer("Вы вернулись в главное меню. Выберите действие:", reply_markup=main_menu())
    logging.info(f"Пользователь {message.from_user.id} вернулся в главное меню.")

# --- Удаление полезного контакта с использованием FSM ---
@router.message(lambda message: message.text == "Удалить полезный контакт")
async def delete_useful_contact(message: types.Message, state: FSMContext):
    if await show_useful_deletion_list(message, state):
        await state.set_state(DeleteUsefulState.WAITING_FOR_CONTACT_ID)

@router.message(DeleteUsefulState.WAITING_FOR_CONTACT_ID)
async def process_useful_deletion(msg: types.Message, state: FSMContext):
    if msg.text == "Завершить удаление":
        await msg.answer("Удаление завершено.", reply_markup=useful_contacts_menu())
        await state.clear()
        return
    data = await state.get_data()
    deletion_map = data.get("useful_deletion_map", {})
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
        await db.execute('DELETE FROM useful_contacts WHERE id = ? AND user_id = ?', (actual_contact_id, msg.from_user.id))
        await db.commit()
    await msg.answer("Контакт успешно удалён.")
    if not await show_useful_deletion_list(msg, state):
        return


# --- Редактирование описания контакта ---
@router.message(lambda message: message.text == "Редактировать описание контакта")
async def edit_contact_description(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute('SELECT id, contact_name FROM useful_contacts WHERE user_id = ?', (user_id,)) as cursor:
            contacts = await cursor.fetchall()

    if not contacts:
        await message.answer("У вас нет полезных контактов.")
        return

    response = "Ваши полезные контакты:\n"
    for contact_id, name in contacts:
        response += f"{contact_id}. {name}\n"
    response += "\nВведите номер контакта для редактирования:"
    await message.answer(response)
    await state.set_state(EditContactStates.SELECT_CONTACT)
    logger.info(f"Пользователь {user_id} перешёл в состояние выбора контакта для редактирования.")

@router.message(EditContactStates.SELECT_CONTACT)
async def process_contact_selection(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    try:
        contact_id = int(message.text.strip())
    except ValueError:
        await message.answer("Пожалуйста, введите корректный номер.")
        return

    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute('SELECT id FROM useful_contacts WHERE id = ? AND user_id = ?', (contact_id, user_id)) as cursor:
            contact = await cursor.fetchone()

    if not contact:
        await message.answer("Контакт с таким номером не найден.")
        logger.info(f"Пользователь {user_id} указал неверный номер контакта: {contact_id}.")
        return

    await state.update_data(contact_id=contact_id)
    await state.set_state(EditContactStates.EDIT_DESCRIPTION)
    await message.answer("Введите новое описание для контакта:")
    logger.info(f"Пользователь {user_id} выбрал контакт с id {contact_id} для редактирования.")

@router.message(EditContactStates.EDIT_DESCRIPTION)
async def save_new_description(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    new_description = message.text
    data = await state.get_data()
    contact_id = data.get("contact_id")
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute('UPDATE useful_contacts SET description = ? WHERE id = ? AND user_id = ?', (new_description, contact_id, user_id))
        await db.commit()
    await state.clear()
    await message.answer("Описание контакта успешно обновлено.", reply_markup=useful_contacts_menu())
    logger.info(f"Пользователь {user_id} обновил описание контакта с id {contact_id}.")

