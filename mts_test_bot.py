import json
import os
import smtplib as smtp
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import requests
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart, StateFilter, Text
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (CallbackQuery, Document, InlineKeyboardButton,
                           InlineKeyboardMarkup, Message)
from dotenv import load_dotenv

load_dotenv()


BOT_TOKEN = os.getenv('TELEGRAM_TOKEN')
SERVER_API = os.getenv('SERVER_API')
BASE_DIR = Path(__file__).resolve().parent
MEDIA_DIR = os.path.join(BASE_DIR, 'media')

storage: MemoryStorage = MemoryStorage()


bot: Bot = Bot(BOT_TOKEN)
dp: Dispatcher = Dispatcher(storage=storage)


user_dict: dict[int, dict[str, str | int | bool]] = {}


class FSMFillForm(StatesGroup):
    theme = State()
    description = State()
    email = State()      
    file = State()
    email_password = State()


request_button: InlineKeyboardButton = InlineKeyboardButton(
        text='Отправить запрос',
        callback_data='request_button_pressed',
    )
email_button: InlineKeyboardButton = InlineKeyboardButton(
        text='Отправить запрос по email',
        callback_data='email_button_pressed',
    )
add_file_button: InlineKeyboardButton = InlineKeyboardButton(
    text='Да',
    callback_data='yes_add_file',
)
skip_file_button: InlineKeyboardButton = InlineKeyboardButton(
    text='Нет',
    callback_data='no_add_file',
)
add_contact_button: InlineKeyboardButton = InlineKeyboardButton(
    text='Да',
    callback_data='yes_add_email',
)
skip_contact_button: InlineKeyboardButton = InlineKeyboardButton(
    text='Нет',
    callback_data='no_add_email',
)
file_keyboard: InlineKeyboardMarkup = InlineKeyboardMarkup(
    inline_keyboard=[
        [add_file_button, skip_file_button]
    ]
)
empty_keyboard: InlineKeyboardMarkup = InlineKeyboardMarkup(
    inline_keyboard=[[]]
)
email_keyboard: InlineKeyboardMarkup = InlineKeyboardMarkup(
    inline_keyboard=[
        [add_contact_button, skip_contact_button]
    ]
)
keyboard_without_add_file_and_add_contact: InlineKeyboardMarkup = InlineKeyboardMarkup(
        inline_keyboard=[
            [request_button],
            [email_button]
        ]
    )

@dp.message(CommandStart(), StateFilter(default_state))
async def process_start_command(message: Message):
    await message.answer(text=f'Приветствую Вас, {message.chat.full_name}\n'
                              'Чтобы задать вопрос в техподдержку - '
                              'отправьте команду /ask_question')


@dp.message(Command(commands='cancel'), ~StateFilter(default_state))
async def process_cancel_command_state(message: Message, state: FSMContext):
    await message.answer(text='Вы вышли из машины состояний\n\n'
                              'Чтобы снова перейти к заполнению опросника - '
                              'отправьте команду /ask_question')
    await state.clear()


@dp.message(Command(commands='cancel'), StateFilter(default_state))
async def process_cancel_command(message: Message):
    await message.answer(text='Отменять нечего. Вы вне машины состояний\n\n'
                              'Чтобы перейти к заполнению анкеты - '
                              'отправьте команду /ask_question')


@dp.message(Command(commands='ask_question'), StateFilter(default_state))
async def process_fillform_command(message: Message, state: FSMContext):
    await message.answer(text='Пожалуйста, введите тему сообщения')
    await state.set_state(FSMFillForm.theme)


@dp.message(StateFilter(FSMFillForm.theme))
async def process_theme_sent(message: Message, state: FSMContext):
    await state.update_data(theme=message.text)
    await message.answer(
        text='Спасибо!\n\nА теперь введите описание проблемы с которой Вы столкнулись'
    )
    await state.set_state(FSMFillForm.description)


@dp.message(StateFilter(FSMFillForm.description))
async def process_description_sent(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer(
        text='Спасибо, хотите ли вы оставить свои контактные данные?',
        reply_markup=email_keyboard
    )


@dp.callback_query(Text(text=['yes_add_email']), ~StateFilter(default_state))
async def process_buttons_email_press(callback: CallbackQuery, state: FSMContext):
    await callback.answer(text='добавь пожалуйста свой емайл')
    await callback.message.edit_text(
        text='Отлично! Оставьте свой email',
        reply_markup=empty_keyboard,
    )
    await state.set_state(FSMFillForm.email)
    
@dp.callback_query(Text(text=['no_add_email']), ~StateFilter(default_state))
async def process_buttons_no_email_press(callback: CallbackQuery, state: FSMContext):
    await callback.answer(text='Имеете право.')
    await callback.message.edit_text(
        text='Отлично! Желаете добавить файл?',
        reply_markup=file_keyboard,
    )

@dp.callback_query(Text(text=['yes_add_file']), ~StateFilter(default_state))
async def process_buttons_press(callback: CallbackQuery, state: FSMContext):
    await callback.answer(text='Добавь пожалуйста файл')
    await callback.message.edit_text(
        text='Отлично! Добавьте файлик',
        reply_markup=empty_keyboard,
    )
    await state.set_state(FSMFillForm.file)


@dp.callback_query(Text(text=['no_add_file']), ~StateFilter(default_state))
async def process_buttons_press(callback: CallbackQuery, state: FSMContext):
    await callback.answer(text='Как так то?')
    await callback.message.edit_text(
        text='Как хотите отправить заявку?',
        reply_markup=keyboard_without_add_file_and_add_contact,
    )

@dp.callback_query(Text(text=['request_button_pressed']), ~StateFilter(default_state))
async def process_buttons_press(callback: CallbackQuery, state: FSMContext):
    user_dict[callback.from_user.id] = await state.get_data()
    await state.clear()
    result_dict = json.dumps(user_dict[callback.from_user.id], indent=4)
    request = requests.post(SERVER_API, data=result_dict)
    print(request.status_code)
    print(result_dict)
    await callback.message.edit_text(text='Спасибо! Ваш запрос отправлен!')


@dp.callback_query(Text(text=['email_button_pressed']), ~StateFilter(default_state))
async def process_buttons_press(callback: CallbackQuery, state: FSMContext):
    await callback.answer('Введите пароль:')
    await state.set_state(FSMFillForm.email_password)


def send_mail(message):
    msg = MIMEMultipart()
    server = smtp.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(
        user_dict[message.from_user.id]['email'],
        user_dict[message.from_user.id]['email_password']
    )
    msg['Subject'] = user_dict[message.from_user.id]['theme']
    msg['text'] = user_dict[message.from_user.id]['description']
    attach = os.path.join(MEDIA_DIR, 'text.txt')
    msg.attach(MIMEText(open(attach).read()))
    mime = MIMEText(msg['text'], 'plain', 'utf-8')
    mime['Subject'] = Header(msg['subject'], 'utf-8')
    server.sendmail(
        from_addr=user_dict[message.from_user.id]['email'],
        to_addrs='artemchepa@yandex.ru',
        msg=mime.as_string(),
    )


@dp.message(StateFilter(FSMFillForm.email_password), )
async def process_send_email_password(message: Message, state: FSMContext):
    await state.update_data(email_password=message.text)
    user_dict[message.from_user.id] = await state.get_data()
    await state.clear()
    send_mail(message=message)
    await message.answer(text='Ваш запрос успешно отправлен по почте.')



@dp.message(StateFilter(FSMFillForm.email),)
async def process_contact_sent(message: Message, state: FSMContext,):
    await state.update_data(email=message.text)
    await message.answer(
        text='Будете добавлять файл?',
        reply_markup=file_keyboard
    )

@dp.message(StateFilter(FSMFillForm.file), F.document.as_('file'))
async def process_file_sent(message: Message,
                             state: FSMContext, 
                             file: Document):
    await state.update_data(file_unique_id=file.file_unique_id,
                            file_id=file.file_id)
    file_d = await bot.get_file(file.file_id)
    await bot.download_file(
        file_path=file_d.file_path,
        destination=os.path.join(MEDIA_DIR, 'text.txt'),
    )
    await message.answer(
        text='Каким образом желаете отправить заявку?',
        reply_markup=keyboard_without_add_file_and_add_contact
    )

@dp.message(StateFilter(default_state))
async def send_echo(message: Message):
    await message.reply(text='Извините, вы ввели некоректный запрос')

if __name__ == '__main__':
    dp.run_polling(bot)