import os
import re
from datetime import datetime, timedelta
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import yt_dlp
from curl_cffi import requests as curl_requests

# ===== НАСТРОЙКИ =====
BOT_TOKEN = "8798378718:AAGRxt_IwUR0m8a2M97l-5TPn8PhWpcNL9s"
RAILWAY_URL = "https://tikitok-production.up.railway.app"

flask_app = Flask(__name__)
telegram_app = Application.builder().token(BOT_TOKEN).build()

# ===== КОМАНДЫ БОТА =====
async def start(update: Update, context):
    await update.message.reply_text("👋 Бот работает! Напиши #коты")

async def handle_message(update: Update, context):
    await update.message.reply_text(f"Ты написал: {update.message.text}")

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# ===== WEBHOOK =====
@flask_app.route(f'/webhook/{BOT_TOKEN}', methods=['POST'])
async def webhook():
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    await telegram_app.process_update(update)
    return 'ok', 200

@flask_app.route('/', methods=['GET'])
def health():
    return 'Bot is running!', 200

# ===== ЗАПУСК =====
if __name__ == '__main__':
    import asyncio
    
    # Устанавливаем вебхук (всё правильно через async функцию)
    webhook_url = f"{RAILWAY_URL}/webhook/{BOT_TOKEN}"
    print(f"🔗 Устанавливаю вебхук: {webhook_url}")
    
    async def setup_webhook():
        result = await telegram_app.bot.set_webhook(url=webhook_url)
        if result:
            print("✅ Вебхук успешно установлен!")
        else:
            print("❌ Ошибка установки вебхука!")
        
        info = await telegram_app.bot.get_webhook_info()
        print(f"📡 Текущий вебхук: {info.url}")
    
    # Запускаем асинхронную функцию
    asyncio.run(setup_webhook())
    
    # Запускаем Flask сервер
    port = int(os.environ.get('PORT', 8080))
    print(f"🔥 Flask сервер запущен на порту {port}")
    flask_app.run(host='0.0.0.0', port=port)
