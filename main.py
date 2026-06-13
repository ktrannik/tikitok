import os
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler
import asyncio

BOT_TOKEN = "8798378718:AAGRxt_IwUR0m8a2M97l-5TPn8PhWpcNL9s"

flask_app = Flask(__name__)
telegram_app = Application.builder().token(BOT_TOKEN).build()

@flask_app.route(f'/webhook/{BOT_TOKEN}', methods=['POST'])
def webhook():
    json_data = request.get_json(force=True)
    update = Update.de_json(json_data, telegram_app.bot)
    asyncio.run(telegram_app.process_update(update))
    return 'ok', 200

@flask_app.route('/')
def health():
    return 'ok', 200

async def start(update: Update, context):
    await update.message.reply_text("Бот работает!")

if __name__ == '__main__':
    telegram_app.add_handler(CommandHandler("start", start))
    
    # Берём домен из переменной Railway
    railway_domain = os.environ.get("RAILWAY_PUBLIC_DOMAIN")
    if railway_domain:
        webhook_url = f"https://{railway_domain}/webhook/{BOT_TOKEN}"
        asyncio.run(telegram_app.bot.set_webhook(url=webhook_url))
        print(f"Вебхук: {webhook_url}")
    
    port = int(os.environ.get('PORT', 8080))
    flask_app.run(host='0.0.0.0', port=port)