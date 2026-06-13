from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import asyncio

BOT_TOKEN = "8798378718:AAGRxt_IwUR0m8a2M97l-5TPn8PhWpcNL9s"
RAILWAY_URL = "https://tikitok-production.up.railway.app"

flask_app = Flask(__name__)
bot_app = Application.builder().token(BOT_TOKEN).build()

# Синхронный обработчик (без async)
@flask_app.route(f'/webhook/{BOT_TOKEN}', methods=['POST'])
def webhook():
    try:
        json_data = request.get_json(force=True)
        update = Update.de_json(json_data, bot_app.bot)
        # Запускаем асинхронную обработку синхронно
        asyncio.run(bot_app.process_update(update))
        return 'ok', 200
    except Exception as e:
        print(f"Ошибка: {e}")
        return 'error', 500

@flask_app.route('/')
def health():
    return 'Bot is running!', 200

async def start(update: Update, context):
    await update.message.reply_text("👋 Бот работает! Отправь #хештег")

async def handle_message(update: Update, context):
    await update.message.reply_text(f"Ты написал: {update.message.text}")

def setup():
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Устанавливаем вебхук
    webhook_url = f"{RAILWAY_URL}/webhook/{BOT_TOKEN}"
    print(f"Устанавливаю вебхук: {webhook_url}")
    
    async def set_webhook():
        return await bot_app.bot.set_webhook(url=webhook_url)
    
    result = asyncio.run(set_webhook())
    print("Вебхук установлен!" if result else "Ошибка!")

if __name__ == '__main__':
    setup()
    port = int(os.environ.get('PORT', 8080))
    flask_app.run(host='0.0.0.0', port=port)
