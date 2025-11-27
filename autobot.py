import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import ChatJoinRequest
from dotenv import load_dotenv
from datetime import datetime
import os
import uvicorn
from fastapi import FastAPI
from threading import Thread

# импортируем словарь источников из другого файла
from sources import SOURCES

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(token=TOKEN)
dp = Dispatcher()

def get_source_name(invite_link):
    if not invite_link:
        return "Нет данных (Telegram не прислал ссылку)"

    # сама пригласительная ссылка
    link = invite_link.invite_link

    # убираем параметры, если есть
    link = link.split("?")[0]

    # если ссылка есть в словаре → вернуть название
    if link in SOURCES:
        return SOURCES[link]

    # иначе вернуть саму ссылку
    return link

# Создаем FastAPI-приложение
app = FastAPI()

@app.get("/")
async def read_root():
    return {"message": "Bot is running!"}

@dp.chat_join_request()
async def approve_join_request(event: ChatJoinRequest):
    try:
        # одобряем заявку
        await bot.approve_chat_join_request(
            chat_id=event.chat.id,
            user_id=event.from_user.id
        )

        username = event.from_user.username or event.from_user.full_name
        source = get_source_name(event.invite_link)

        # уведомление админу
        await bot.send_message(
            ADMIN_ID,
            f"🔔 *Новый подписчик*\n"
            f"👤 `{username}`\n"
            f"🌐 Линк: *{source}*\n"
            f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            parse_mode="Markdown"
        )

        print(f"Approved: {username} | Source: {source}")

    except Exception as e:
        print("Error:", e)

async def main():
    # Запуск FastAPI сервера в отдельном потоке
    def run_fastapi():
        uvicorn.run(app, host="0.0.0.0", port=8000)

    fastapi_thread = Thread(target=run_fastapi)
    fastapi_thread.start()

    # Запуск бота в асинхронном режиме
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
