import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email_validator import validate_email, EmailNotValidError
from aiogram import Bot, Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from aiogram.types import Message
import asyncio
from dotenv import load_dotenv
import os

load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")
FROM_EMAIL = os.getenv("FROM_EMAIL")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.yandex.ru")  # По умолчанию Yandex
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))  # По умолчанию порт 465 для SSL

bot = Bot(token=API_TOKEN)
dp = Dispatcher()


# Проверка валидности email
def is_valid_email(email: str) -> bool:
    try:
        validate_email(email)
        return True
    except EmailNotValidError:
        return False


# Функция для отправки письма через SMTP
async def send_email(to_email: str, message: str):
    msg = MIMEMultipart()
    msg['From'] = FROM_EMAIL
    msg['To'] = to_email
    msg['Subject'] = "Сообщение от Telegram-бота"
    msg.attach(MIMEText(message, 'plain'))

    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(FROM_EMAIL, EMAIL_PASSWORD)
            server.sendmail(FROM_EMAIL, to_email, msg.as_string())
        return "Письмо успешно отправлено!"
    except Exception as e:
        return f"Ошибка при отправке письма: {e}"


# Класс для управления состояниями
class Form(StatesGroup):
    email = State()   # Состояние для ввода email
    message = State()  # Состояние для ввода сообщения


# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await message.answer("Привет! Пожалуйста, введи свой email:")
    await state.set_state(Form.email)


# Обработчик для проверки и сохранения email
@dp.message(Form.email)
async def process_email(message: Message, state: FSMContext):
    email = message.text
    if is_valid_email(email):
        await state.update_data(email=email)
        await message.answer("Email принят! Теперь напиши сообщение, которое хочешь отправить:")
        await state.set_state(Form.message)
    else:
        await message.answer("Пожалуйста, введи корректный email.")


# Обработчик для отправки сообщения на email
@dp.message(Form.message)
async def process_message(message: Message, state: FSMContext):
    user_data = await state.get_data()
    email = user_data['email']
    msg_text = message.text
    result = await send_email(email, msg_text)
    await message.answer(result)
    await state.clear()


# Основная функция запуска бота
async def main():
    await dp.start_polling(bot)

# Точка входа в программу
if __name__ == "__main__":
    asyncio.run(main())
