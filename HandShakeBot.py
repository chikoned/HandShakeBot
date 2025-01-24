
!pip install aiogram
!pip install aiosqlite

import asyncio
import logging
from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import aiosqlite

# --- Конфигурация ---
TOKEN = '8051939836:AAEFHZQMerIjZZI_VcQkk9V58G6FrE-mY1M'  # Замените на свой токен
DATABASE = 'contacts.db'

# --- Настройка логирования ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ],
    force=True
)
logger = logging.getLogger(__name__)

# --- FSM ---
class AddContactStates(StatesGroup):
    ADD_SOCIAL_CIRCLE = State()
    ADD_USEFUL_CONTACT = State()
    ADD_DESCRIPTION = State()
    
class EditContactStates(StatesGroup):
    SELECT_CONTACT = State()     # Выбор контакта
    EDIT_DESCRIPTION = State()  # Ввод нового описания


# --- Инициализация бота ---
bot = Bot(token=TOKEN)
storage = MemoryStorage()
router = Router()

# --- Инициализация базы данных ---
async def init_db():
    """Создаёт таблицы базы данных при необходимости."""
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXTб
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS social_circle (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                contact_id INTEGER,
                contact_name TEXT,
                UNIQUE(user_id, contact_id)
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS useful_contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                contact_name TEXT,
                contact_phone TEXT,
                description TEXT,
                UNIQUE(user_id, contact_phone)
            )
        ''')
        await db.commit()
        logging.info("База данных успешно инициализирована.")

# --- Клавиатуры ---

def main_menu():
    """Основное меню."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Круг общения")],
            [KeyboardButton(text="Полезные контакты")],
            [KeyboardButton(text="Два рукопожатия")],
            [KeyboardButton(text="Приватность")]
        ],
        resize_keyboard=True
    )


def social_circle_menu():
    """Меню для работы с кругом общения."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Просмотреть круг общения")],
            [KeyboardButton(text="Добавить круг общения")],
            [KeyboardButton(text="Удалить контакт из круга общения")],
            [KeyboardButton(text="Удалить круг общения")],
            [KeyboardButton(text="Вернуться в главное меню")]
        ],
        resize_keyboard=True
    )

def useful_contacts_menu():
    """Меню для работы с полезными контактами."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Просмотреть полезные контакты")],
            [KeyboardButton(text="Добавить полезные контакты")],
            [KeyboardButton(text="Редактировать описание контакта")],
            [KeyboardButton(text="Удалить полезный контакт")],
            [KeyboardButton(text="Удалить все контакты")],
            [KeyboardButton(text="Вернуться в главное меню")]
        ],
        resize_keyboard=True
    )

def two_handshake_menu():
    """Меню для работы с двумя рукопожатиями."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Просмотреть полезные контакты круга общения")],
            [KeyboardButton(text="Поиск полезных контактов")],
            [KeyboardButton(text="Вернуться в главное меню")]
        ],
        resize_keyboard=True
    )


def privacy_menu():
    """Меню для работы с настройками приватности."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Удалить свой телефон из всех баз данных")],
            [KeyboardButton(text="Вернуться в главное меню")]
        ],
        resize_keyboard=True
    )



# --- Обработчики ---
@router.message(Command("start"))
async def start_handler(message: types.Message):
    """Обрабатывает команду /start."""
    user = message.from_user
    logging.info(f"Пользователь {user.id} ({user.full_name or user.first_name}) начал регистрацию.")

    async with aiosqlite.connect(DATABASE) as db:
        await db.execute('''
            INSERT OR IGNORE INTO users (user_id, username, full_name)
            VALUES (?, ?, ?)
        ''', (user.id, user.username, user.full_name or user.first_name))
        await db.commit()
        logging.info(f"Пользователь {user.id} успешно зарегистрирован в базе данных.")

        # Уведомляем о регистрации
        async with db.execute('''
            SELECT user_id, contact_name
            FROM social_circle
            WHERE contact_id = ?
        ''', (user.id,)) as cursor:
            linked_users = await cursor.fetchall()

    if linked_users:
        logging.info(f"Найдено {len(linked_users)} пользователей, добавивших ID {user.id} в свой круг общения.")
        for linked_user_id, contact_name in linked_users:
            try:
                await bot.send_message(
                    linked_user_id,
                    f"Ваш контакт {contact_name} зарегистрировался в боте!"
                )
                logging.info(f"Уведомление отправлено пользователю {linked_user_id}: контакт {contact_name}.")
            except Exception as e:
                logging.error(f"Ошибка при уведомлении {linked_user_id}: {e}")
    else:
        logging.info(f"У пользователя {user.id} нет связанных контактов в базе данных.")

    await message.answer("Добро пожаловать! Выберите действие из меню:", reply_markup=main_menu())

# --- Добавление круга общения ---
@router.message(lambda message: message.text == "Добавить круг общения")
async def start_adding_social_contacts(message: types.Message, state: FSMContext):
    #logger.info(f"Пользователь {message.from_user.id} начал добавлять контакты в круг общения.")
    await state.set_state(AddContactStates.ADD_SOCIAL_CIRCLE)
    await message.answer(
        "Отправьте контакт для добавления в круг общения.",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Завершить добавление")]],
            resize_keyboard=True
        )
    )

@router.message(AddContactStates.ADD_SOCIAL_CIRCLE)
async def add_social_circle_contact(message: types.Message, state: FSMContext):
    if message.text == "Завершить добавление":
        await state.clear()
        logging.info(f"Пользователь {message.from_user.id} завершил добавление круга общения.")
        await message.answer("Добавление круга общения завершено.", reply_markup=social_circle_menu())
        return

    if not message.contact:
        await message.answer("Отправьте контакт или нажмите 'Завершить добавление'.")
        return

    contact = message.contact
    contact_id = contact.user_id  # ID Telegram-пользователя
    full_name = f"{contact.first_name} {contact.last_name or ''}".strip()
    try:
        async with aiosqlite.connect(DATABASE) as db:
            await db.execute('''
                INSERT INTO social_circle (user_id, contact_id, contact_name)
                VALUES (?, ?, ?)
            ''', (message.from_user.id, contact.user_id, f"{contact.first_name} {contact.last_name or ''}"))
            await db.commit()
        logging.info(f"Контакт {full_name} (ID: {contact_id}) добавлен пользователем {message.from_user.id}.")
        await message.answer("Контакт успешно добавлен.")
    except aiosqlite.IntegrityError:
        await message.answer("Этот контакт уже есть в вашем круге общения.")

# --- Добавление полезных контактов ---
@router.message(lambda message: message.text == "Добавить полезные контакты")
async def start_adding_useful_contacts(message: types.Message, state: FSMContext):
    logging.info(f"Пользователь {message.from_user.id} начал добавлять полезные контакты.")
    await state.set_state(AddContactStates.ADD_USEFUL_CONTACT)
    await message.answer(
        "Отправьте контакт для добавления в полезные контакты.",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Завершить добавление")]],
            resize_keyboard=True
        )
    )

@router.message(AddContactStates.ADD_USEFUL_CONTACT)
async def add_useful_contact(message: types.Message, state: FSMContext):
    logging.info(f"Получено сообщение: {message.text}")
    if message.text == "Завершить добавление":
        await state.clear()
        logging.info(f"Пользователь {message.from_user.id} завершил добавление полезных контактов.")
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
    description = message.text

    try:
        async with aiosqlite.connect(DATABASE) as db:
            await db.execute('''
                INSERT INTO useful_contacts (user_id, contact_name, contact_phone, description)
                VALUES (?, ?, ?, ?)
            ''', (message.from_user.id, contact_name, contact_phone, description))
            await db.commit()
        logging.info(f"Контакт {contact_name} с описанием добавлен пользователем {message.from_user.id}.")
        await message.answer("Контакт с описанием успешно добавлен.")
    finally:
        await state.set_state(AddContactStates.ADD_USEFUL_CONTACT)

# --- Просмотр и удаление контактов ---
@router.message(lambda message: message.text == "Просмотреть круг общения")
async def view_social_circle(message: types.Message):
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute('''
            SELECT id, contact_name FROM social_circle WHERE user_id = ?
        ''', (message.from_user.id,)) as cursor:
            contacts = await cursor.fetchall()

    if contacts:
        response = "Ваш круг общения:\n"
        for contact_id, name in contacts:
          response += f'{contact_id}. {name}\n'
        await message.answer(response)
    else:
        await message.answer("Ваш круг общения пуст.")

@router.message(lambda message: message.text == "Удалить круг общения")
async def delete_all_social_circle_contacts(message: types.Message):
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute('DELETE FROM social_circle WHERE user_id = ?', (message.from_user.id,))
        await db.commit()
    await message.answer("Все контакты из круга общения удалены.")

@router.message(lambda message: message.text == "Просмотреть полезные контакты")
async def view_useful_contacts(message: types.Message):
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute('''
            SELECT id, contact_name, contact_phone, description FROM useful_contacts WHERE user_id = ?
        ''', (message.from_user.id,)) as cursor:
            contacts = await cursor.fetchall()

    if contacts:
        response = "Ваши полезные контакты:\n"
        for id, name, phone, desc in contacts:
          response += f'{id}. {name}. {phone}. {desc}\n'
        await message.answer(response)
    else:
        await message.answer("Ваш список полезных контактов пуст.")

@router.message(lambda message: message.text == "Удалить все полезные контакты")
async def delete_all_useful_contacts(message: types.Message):
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute('DELETE FROM useful_contacts WHERE user_id = ?', (message.from_user.id,))
        await db.commit()
    await message.answer("Все полезные контакты удалены.")

@router.message(lambda message: message.text == "Просмотреть полезные контакты круга общения")
async def view_useful_contacts_of_social_circle(message: types.Message):
    """Выводит полезные контакты круга общения пользователя."""
    async with aiosqlite.connect(DATABASE) as db:
        # SQL-запрос для получения полезных контактов из круга общения
        async with db.execute('''
            SELECT sc.contact_name AS owner_name, uc.contact_name AS useful_name,
                   uc.contact_phone, uc.description
            FROM social_circle AS sc
            JOIN useful_contacts AS uc ON sc.contact_id = uc.user_id
            WHERE sc.user_id = ?
        ''', (message.from_user.id,)) as cursor:
            contacts = await cursor.fetchall()

    if not contacts:
        await message.answer("У ваших контактов из круга общения нет полезных контактов.")
    else:
        response = "Полезные контакты вашего круга общения:\n"
        for owner_name, useful_name, contact_phone, description in contacts:
            response += (
                f"От: {owner_name}\n"
                f"Имя: {useful_name}\n"
                f"Телефон: {contact_phone}\n"
                f"Описание: {description}\n\n"
            )
        await message.answer(response)



@router.message(lambda message: message.text == "Круг общения")
async def social_circle_menu_handler(message: types.Message):
    """Открывает подменю для работы с кругом общения."""
    await message.answer("Выберите действие:", reply_markup=social_circle_menu())

@router.message(lambda message: message.text == "Полезные контакты")
async def useful_contacts_menu_handler(message: types.Message):
    """Открывает подменю для работы с полезными контактами."""
    await message.answer("Выберите действие:", reply_markup=useful_contacts_menu())


@router.message(lambda message: message.text == "Два рукопожатия")
async def two_handshake_menu_handler(message: types.Message):
    """Открывает подменю для двух рукопожатий."""
    await message.answer("Выберите действие:", reply_markup=two_handshake_menu())


@router.message(lambda message: message.text == "Приватность")
async def privacy_menu_handler(message: types.Message):
    """Открывает подменю для работы с приватностью."""
    await message.answer("Выберите действие:", reply_markup=privacy_menu())

@router.message(lambda message: message.text == "Вернуться в главное меню")
async def back_to_main_menu(message: types.Message):
    """Возвращает пользователя в главное меню."""
    await message.answer("Вы вернулись в главное меню. Выберите действие:", reply_markup=main_menu())
    logging.info(f"Пользователь {message.from_user.id} вернулся в главное меню.")

@router.message(lambda message: message.text == "Удалить контакт из круга общения")
async def delete_social_contact(message: types.Message):
    """Удаляет контакт из круга общения по номеру."""
    user_id = message.from_user.id

    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute('''
            SELECT id, contact_name FROM social_circle WHERE user_id = ?
        ''', (user_id,)) as cursor:
            contacts = await cursor.fetchall()

    if not contacts:
        await message.answer("Ваш круг общения пуст.")
        logging.info(f"Пользователь {user_id} пытался удалить контакт, но список пуст.")
        return

    # Отображаем список контактов с номерами
    response = "Ваш круг общения:\n"
    for contact_id, name in contacts:
        response += f"{contact_id}. {name}\n"
    response += "\nВведите номер контакта для удаления:"
    await message.answer(response)

    # Ждём номер для удаления
    @router.message()
    async def process_deletion_request(msg: types.Message):
        try:
            contact_id = int(msg.text.strip())
        except ValueError:
            await msg.answer("Пожалуйста, введите корректный номер.")
            return

        async with aiosqlite.connect(DATABASE) as db:
            async with db.execute('SELECT id FROM social_circle WHERE id = ? AND user_id = ?', (contact_id, user_id)) as cursor:
                contact = await cursor.fetchone()

            if not contact:
                await msg.answer("Контакт с таким номером не найден.")
                logging.info(f"Контакт с номером {contact_id} не найден у пользователя {user_id}.")
                return

            # Удаляем контакт
            await db.execute('DELETE FROM social_circle WHERE id = ? AND user_id = ?', (contact_id, user_id))
            await db.commit()
            logging.info(f"Контакт с номером {contact_id} удалён у пользователя {user_id}.")

            # Переприсваиваем номера
            await renumber_contacts(db, "social_circle", user_id)

        await msg.answer("Контакт успешно удалён.", reply_markup=social_circle_menu())


@router.message(lambda message: message.text == "Удалить полезный контакт")
async def delete_useful_contact(message: types.Message):
    """Удаляет контакт из полезных контактов по номеру."""
    user_id = message.from_user.id

    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute('''
            SELECT id, contact_name FROM useful_contacts WHERE user_id = ?
        ''', (user_id,)) as cursor:
            contacts = await cursor.fetchall()

    if not contacts:
        await message.answer("Ваш список полезных контактов пуст.")
        logging.info(f"Пользователь {user_id} пытался удалить контакт, но список пуст.")
        return

    # Отображаем список контактов с номерами
    response = "Ваши полезные контакты:\n"
    for contact_id, name in contacts:
        response += f"{contact_id}. {name}\n"
    response += "\nВведите номер контакта для удаления:"
    await message.answer(response)

    # Ждём номер для удаления
    @router.message()
    async def process_deletion_request(msg: types.Message):
        try:
            contact_id = int(msg.text.strip())
        except ValueError:
            await msg.answer("Пожалуйста, введите корректный номер.")
            return

        async with aiosqlite.connect(DATABASE) as db:
            async with db.execute('SELECT id FROM useful_contacts WHERE id = ? AND user_id = ?', (contact_id, user_id)) as cursor:
                contact = await cursor.fetchone()

            if not contact:
                await msg.answer("Контакт с таким номером не найден.")
                logging.info(f"Контакт с номером {contact_id} не найден у пользователя {user_id}.")
                return

            # Удаляем контакт
            await db.execute('DELETE FROM useful_contacts WHERE id = ? AND user_id = ?', (contact_id, user_id))
            await db.commit()
            logging.info(f"Контакт с номером {contact_id} удалён у пользователя {user_id}.")

            # Переприсваиваем номера
            await renumber_contacts(db, "useful_contacts", user_id)

        await msg.answer("Контакт успешно удалён.", reply_markup=useful_contacts_menu())


async def renumber_contacts(db, table, user_id):
    """Перенумеровывает контакты после удаления."""
    async with db.execute(f"SELECT id FROM {table} WHERE user_id = ? ORDER BY id", (user_id,)) as cursor:
        contacts = await cursor.fetchall()

    for index, (old_id,) in enumerate(contacts, start=1):
        await db.execute(f"UPDATE {table} SET id = ? WHERE id = ?", (index, old_id))
    await db.execute(F"UPDATE sqlite_sequence SET seq = (SELECT MAX(id) FROM {table}) WHERE name = ?", (table,))
    await db.commit()
    logger.info(f"Контакты в таблице {table} перенумерованы для пользователя {user_id}.") 


@router.message(lambda message: message.text == "Редактировать описание контакта")
async def edit_contact_description(message: types.Message, state: FSMContext):
    """Редактирует описание выбранного контакта."""
    user_id = message.from_user.id

    # Получаем список контактов пользователя
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute('SELECT id, contact_name FROM useful_contacts WHERE user_id = ?', (user_id,)) as cursor:
            contacts = await cursor.fetchall()

    if not contacts:
        await message.answer("У вас нет полезных контактов.")
        return

    # Отправляем пользователю список контактов
    response = "Ваши полезные контакты:\n"
    for contact_id, name in contacts:
        response += f"{contact_id}. {name}\n"
    response += "\nВведите номер контакта для редактирования:"
    await message.answer(response)

    # Переводим в состояние выбора контакта
    await state.set_state(EditContactStates.SELECT_CONTACT)
    logging.info(f"Пользователь {user_id} перешёл в состояние выбора контакта для редактирования.")

@router.message(EditContactStates.SELECT_CONTACT)
async def process_contact_selection(message: types.Message, state: FSMContext):
    """Обрабатывает выбор контакта для редактирования."""
    user_id = message.from_user.id

    try:
        contact_id = int(message.text.strip())
    except ValueError:
        await message.answer("Пожалуйста, введите корректный номер.")
        return

    # Проверяем, существует ли контакт
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute('SELECT id FROM useful_contacts WHERE id = ? AND user_id = ?', (contact_id, user_id)) as cursor:
            contact = await cursor.fetchone()

    if not contact:
        await message.answer("Контакт с таким номером не найден.")
        logging.info(f"Пользователь {user_id} указал неверный номер контакта: {contact_id}.")
        return

    # Сохраняем id контакта в состоянии FSM
    await state.update_data(contact_id=contact_id)

    # Переводим в состояние ввода нового описания
    await state.set_state(EditContactStates.EDIT_DESCRIPTION)
    await message.answer("Введите новое описание для контакта:")
    logging.info(f"Пользователь {user_id} выбрал контакт с id {contact_id} для редактирования.")

@router.message(EditContactStates.EDIT_DESCRIPTION)
async def save_new_description(message: types.Message, state: FSMContext):
    """Сохраняет новое описание для контакта."""
    user_id = message.from_user.id
    new_description = message.text

    # Получаем данные контакта из состояния FSM
    data = await state.get_data()
    contact_id = data.get("contact_id")

    # Обновляем описание в базе данных
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute('UPDATE useful_contacts SET description = ? WHERE id = ? AND user_id = ?', (new_description, contact_id, user_id))
        await db.commit()

    # Сбрасываем состояние FSM
    await state.clear()

    await message.answer("Описание контакта успешно обновлено.", reply_markup=useful_contacts_menu())
    logging.info(f"Пользователь {user_id} обновил описание контакта с id {contact_id}.")        

@router.message(lambda message: message.text == "Поиск полезных контактов")
async def search_useful_contacts(message: types.Message):
    """Ищет полезные контакты через два рукопожатия."""
    await message.answer("Введите ключевое слово для поиска:")
    @router.message()
    async def perform_search(msg: types.Message):
        keyword = f"%{msg.text.strip()}%"
        async with aiosqlite.connect(DATABASE) as db:
            async with db.execute('''
                SELECT u.username, uc.contact_name, uc.contact_phone, uc.description
                FROM social_circle AS sc
                JOIN useful_contacts AS uc ON sc.contact_id = uc.user_id
                JOIN users AS u ON sc.contact_id = u.user_id
                WHERE uc.description LIKE ?
            ''', (keyword,)) as cursor:
                results = await cursor.fetchall()

        if not results:
            await msg.answer("Контакты с таким ключевым словом не найдены.")
        else:
            response = "Найденные контакты:\n"
            for owner, name, phone, description in results:
                response += f"От: {owner}\nИмя: {name}\nТелефон: {phone}\nОписание: {description}\n\n"
            await msg.answer(response)


# --- Основной цикл ---
async def main():
    await init_db()
    dp = Dispatcher(storage=storage)
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
   await main()
