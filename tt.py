import os
import re
from datetime import datetime, timedelta
import yt_dlp
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram.request import HTTPXRequest

BOT_TOKEN = "8798378718:AAGRxt_IwUR0m8a2M97l-5TPn8PhWpcNL9s"  # Вставь сюда токен

# Настройка прокси для httpx
# В твоей ошибке вижу порт 8080, пробуем SOCKS5
PROXY_URL = "socks5://127.0.0.1:8080"  # Поменяй порт если нужно (10808, 1080 и т.д.)

# Создаём кастомный request с прокси
request = HTTPXRequest(proxy=PROXY_URL)

async def search_tiktok_by_hashtags(hashtags, limit=3, max_days_old=3):
    # ВРЕМЕННО: тестовые ссылки
    return [
        {"url": "https://www.tiktok.com/@tiktok/video/123456789", "source": "test"},
    ][:limit]

async def download_video(url: str) -> str:
    output_path = "temp_video.mp4"
    ydl_opts = {
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return output_path
    except Exception as e:
        print(f"Ошибка: {e}")
        return None

async def start(update: Update, context):
    await update.message.reply_text("👋 Бот работает! Напиши #коты")

async def handle_hashtag(update: Update, context):
    text = update.message.text.strip()
    hashtags = re.findall(r'#\w+', text)
    
    if not hashtags:
        await update.message.reply_text("Напиши хештег, например: #коты")
        return
    
    await update.message.reply_text(f"🔍 Ищу видео по {hashtags[0]}...")
    
    videos = await search_tiktok_by_hashtags(hashtags, limit=2)
    
    if not videos:
        await update.message.reply_text("Не нашёл видео")
        return
    
    for video in videos:
        video_path = await download_video(video['url'])
        if video_path and os.path.exists(video_path):
            with open(video_path, 'rb') as f:
                await update.message.reply_video(video=f)
            os.remove(video_path)

def main():
    # Используем request с прокси
    app = (Application.builder()
           .token(BOT_TOKEN)
           .request(request)
           .build())
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_hashtag))
    
    print("🤖 Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()