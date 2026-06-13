from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler
import asyncio
import os

BOT_TOKEN = "8798378718:AAGRxt_IwUR0m8a2M97l-5TPn8PhWpcNL9s"
RAILWAY_URL = "https://tikitok-production.up.railway.app"

flask_app = Flask(__name__)
bot_app = Application.builder().token(BOT_TOKEN).build()

@flask_app.route(f'/webhook/{BOT_TOKEN}', methods=['POST'])
def webhook():
    json_data = request.get_json(force=True)
    update = Update.de_json(json_data, bot_app.bot)
    asyncio.run(bot_app.process_update(update))
    return 'ok', 200

@flask_app.route('/')
def health():
    return 'ok', 200

async def start(update: Update, context):
    await update.message.reply_text("Бот работает!")

if __name__ == '__main__':
    bot_app.add_handler(CommandHandler("start", start))
    
    # Устанавливаем вебхук
    async def setup():
        await bot_app.bot.set_webhook(url=f"{RAILWAY_URL}/webhook/{BOT_TOKEN}")
        print("Вебхук установлен")
    
    asyncio.run(setup())
    
    port = int(os.environ.get('PORT', 8080))
    flask_app.run(host='0.0.0.0', port=port)
