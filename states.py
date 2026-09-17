from aiogram.fsm.state import State, StatesGroup

class RegisterState(StatesGroup):
    full_name = State()
    faculty = State()
    group_name = State()

class UploadState(StatesGroup):
    waiting_for_file = State()
    waiting_for_payment = State()

class TestState(StatesGroup):
    answering = State()

class AdminCardState(StatesGroup):
    waiting_for_card = State()