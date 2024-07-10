from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, URLInputFile, FSInputFile
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.enums import ParseMode, ChatAction
from aiogram.client.bot import DefaultBotProperties

import asyncio
import json

from dotenv import load_dotenv
import os
load_dotenv()

bot = Bot(os.getenv("TOKEN_BOT"), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()


async def start_bot(bot: Bot):
    print("Бот запущен")

# Загружаем данные из JSON файла
with open('questions.json', 'r', encoding='utf-8') as f:
    data = json.load(f)


# Функция для создания ReplyKeyboardMarkup
def create_keyboard(questions):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=question)] for question in questions
        ],
        resize_keyboard=True, # нормальный размер кнопок
        one_time_keyboard=True, # скрытие после нажатия
        input_field_placeholder="Выберите вопрос:", # подсказка
        selective=True # клавиатура видна только открывшему
    )
    return keyboard

questions = create_keyboard(data.keys())

next_question = InlineKeyboardBuilder().add(InlineKeyboardButton(text='Да', callback_data='open_keyboard')).as_markup()

@dp.message(Command(commands=['start']))
async def start(message: Message):
    await message.answer("Добро пожаловать! Это бот который поможет ответить на некоторые ваши воросы.",
                         reply_markup=questions)


types_of_send = {
    'text': ChatAction.TYPING,
    'photo': ChatAction.UPLOAD_PHOTO,
    'document': ChatAction.UPLOAD_DOCUMENT,
    'video': ChatAction.UPLOAD_VIDEO,
}


@dp.message(F.text.in_(data))
async def handle_question(message: Message):
    response = data.get(message.text)
    # Получаем типы отправляемых сообщений
    list_type_messages = list(response.keys())
    
    # Словарь комманд для отправки сообщений
    send_messages = {
        'text': message.answer,
        'photo': message.answer_photo,
        'document': message.answer_document,
        'video': message.answer_video,
    }

    # Отправляем сообщения
    for type in list_type_messages:
        # print("что пришло", response.get(type))
        if type == "text":
            await message.bot.send_chat_action(chat_id=message.chat.id, action=types_of_send[type])
            await send_messages[type](response.get(type))
        else:  
            list_property= list(response.get(type))
            if 'url' in list_property:
                await message.bot.send_chat_action(chat_id=message.chat.id, action=types_of_send[type])
                await send_messages[type](URLInputFile(response.get(type).get("url"), filename=response.get(type).get("filename")), 
                                          caption=response.get(type).get("caption"), action=ChatAction.UPLOAD_DOCUMENT)
            if 'file_path' in list_property:
                await message.bot.send_chat_action(chat_id=message.chat.id, action=types_of_send[type])
                await send_messages[type](FSInputFile(response.get(type).get("file_path"), filename=response.get(type).get("filename")),
                                          caption=response.get(type).get("caption"), action=ChatAction.UPLOAD_DOCUMENT)
    # Следующий вопрос          
    await message.answer("Хотите задать ещё вопрос?",
                        reply_markup= next_question)

    
@dp.callback_query (F.data == 'open_keyboard')
async def open_keyboard(callback: CallbackQuery):
    await callback.message.answer('Выберите вопрос:', reply_markup=questions)
    

@dp.message(Command(commands=['help']))
async def help(message: Message):
    text_help='''
/start - Запуск
/help - Все команды
...
    '''
    await message.answer(text_help)


#Запуск бота
async def main():
    dp.startup.register(start_bot)
    # убрать выпонение команд присланых в отключеном состоянии
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, )

if __name__=="__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt: # убрать ошибки после отключения бота
        print("Бот остановлен")