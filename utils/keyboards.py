from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu():
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
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Просмотреть полезные контакты круга общения")],
            [KeyboardButton(text="Поиск полезных контактов")],
            [KeyboardButton(text="Вернуться в главное меню")]
        ],
        resize_keyboard=True
    )

def privacy_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Удалить свой телефон из всех баз данных")],
            [KeyboardButton(text="Вернуться в главное меню")]
        ],
        resize_keyboard=True
    )

def addition_keyboard():
  return ReplyKeyboardMarkup(
      keyboard=[
          [KeyboardButton(text="Завершить добавление")]
      ],
      resize_keyboard=True,
      one_time_keyboard=False,
      is_persistent=True
  )    

def deletion_keyboard():
    """Клавиатура с кнопкой 'Завершить удаление'"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Завершить удаление")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False,  # Не скрывать после нажатия
        is_persistent=True        # Оставлять на экране
    )  
