import os
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8798378718:AAGRxt_IwUR0m8a2M97l-5TPn8PhWpcNL9s")

flask_app = Flask(__name__)
telegram_app = Application.builder().token(BOT_TOKEN).build()

# ===== ВЕБХУК =====
@flask_app.route(f'/webhook/{BOT_TOKEN}', methods=['POST'])
def webhook():
    try:
        update = Update.de_json(request.get_json(force=True), telegram_app.bot)
        telegram_app.process_update(update)
        return 'ok', 200
    except Exception as e:
        print(f"Ошибка: {e}")
        return 'error', 500

@flask_app.route('/')
def health():
    return 'ok', 200

# ===== КОМАНДА =====
async def start(update: Update, context):
    await update.message.reply_text("✅ Бот работает!")

telegram_app.add_handler(CommandHandler("start", start))

# ===== ЗАПУСК =====
if __name__ == '__main__':
    # Устанавливаем вебхук
    railway_domain = os.environ.get("RAILWAY_PUBLIC_DOMAIN")
    if railway_domain:
        webhook_url = f"https://{railway_domain}/webhook/{BOT_TOKEN}"
        telegram_app.bot.set_webhook(url=webhook_url)
        print(f"✅ Вебхук установлен: {webhook_url}")
    else:
        print("⚠️ RAILWAY_PUBLIC_DOMAIN не задан")
    
    port = int(os.environ.get('PORT', 8080))
    flask_app.run(host='0.0.0.0', port=port)
