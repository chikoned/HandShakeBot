from aiogram.fsm.state import State, StatesGroup

# --- FSM States ---
class AddContactStates(StatesGroup):
    ADD_SOCIAL_CIRCLE = State()
    ADD_USEFUL_CONTACT = State()
    ADD_DESCRIPTION = State()

class EditContactStates(StatesGroup):
    SELECT_CONTACT = State()
    EDIT_DESCRIPTION = State()

class DeleteSocialState(StatesGroup):
    WAITING_FOR_CONTACT_ID = State()

class DeleteUsefulState(StatesGroup):
    WAITING_FOR_CONTACT_ID = State()

class SearchUsefulState(StatesGroup):
    WAITING_FOR_KEYWORD = State()