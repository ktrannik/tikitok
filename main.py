import os
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler

BOT_TOKEN = "8798378718:AAGRxt_IwUR0m8a2M97l-5TPn8PhWpcNL9s"
flask_app = Flask(__name__)
telegram_app = Application.builder().token(BOT_TOKEN).build()

@flask_app.route(f'/webhook/{BOT_TOKEN}', methods=['POST'])
def webhook():
    try:
        data = request.get_json(force=True)
        update = Update.de_json(data, telegram_app.bot)
        # Запускаем асинхронную обработку в фоне
        asyncio.create_task(telegram_app.process_update(update))
        return 'ok', 200
    except Exception as e:
        print(f"Webhook error: {e}")
        return 'error', 500

@flask_app.route('/', methods=['GET'])
def health():
    return 'ok', 200

async def start(update: Update, context):
    await update.message.reply_text("Бот работает!")

def setup():
    telegram_app.add_handler(CommandHandler("start", start))
    webhook_url = f"https://{os.environ.get('RAILWAY_PUBLIC_DOMAIN')}/webhook/{BOT_TOKEN}"
    # Синхронно устанавливаем вебхук (но нужен event loop)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(telegram_app.bot.set_webhook(url=webhook_url))
    print(f"Webhook set to {webhook_url}")

if __name__ == '__main__':
    setup()
    port = int(os.environ.get('PORT', 8080))
    flask_app.run(host='0.0.0.0', port=port)
