import os
import re
import json
from datetime import datetime, timedelta
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import yt_dlp
from curl_cffi import requests as curl_requests

# ===== НАСТРОЙКИ =====
BOT_TOKEN = os.environ.get("8798378718:AAGRxt_IwUR0m8a2M97l-5TPn8PhWpcNL9s")
RAILWAY_URL = os.environ.get("tikitok-production.up.railway.app")  # Например: https://tikitok.up.railway.app

# Проверка переменных
if not BOT_TOKEN:
    raise Exception("BOT_TOKEN не задан в переменных Railway!")
if not RAILWAY_URL:
    raise Exception("RAILWAY_PUBLIC_DOMAIN не задан! Добавь переменную с твоим URL")

# Flask приложение для вебхуков
flask_app = Flask(__name__)

# Telegram приложение
telegram_app = Application.builder().token(BOT_TOKEN).build()

# ===== ФУНКЦИИ ПОИСКА В TIKTOK =====
async def get_video_date(video_url: str) -> datetime:
    try:
        response = curl_requests.get(video_url, impersonate="chrome", timeout=10)
        match = re.search(r'"createTime":\s*"(\d{4}-\d{2}-\d{2})"', response.text)
        if match:
            return datetime.strptime(match.group(1), '%Y-%m-%d')
        return datetime.now() - timedelta(days=999)
    except Exception:
        return datetime.now() - timedelta(days=999)

async def is_video_fresh(video_url: str, max_days_old: int = 3) -> bool:
    video_date = await get_video_date(video_url)
    return (datetime.now() - video_date).days <= max_days_old

async def check_video_hashtags(video_url: str, required_tags: list) -> bool:
    try:
        response = curl_requests.get(video_url, impersonate="chrome", timeout=10)
        found_tags = re.findall(r'#([\wа-яё]+)', response.text, re.IGNORECASE)
        found_tags = [tag.lower() for tag in found_tags]
        return all(tag.lower() in found_tags for tag in required_tags)
    except Exception:
        return False

async def search_tiktok_by_hashtags(hashtags: list, limit: int = 3, max_days_old: int = 3):
    primary_tag = hashtags[0].strip('#')
    other_tags = [tag.strip('#') for tag in hashtags[1:]]
    
    videos_found = []
    checked_urls = set()
    page = 0
    
    while len(videos_found) < limit and page < 8:
        try:
            url = f"https://www.tiktok.com/tag/{primary_tag}"
            if page > 0:
                url += f"?page={page}"
            
            response = curl_requests.get(url, impersonate="chrome", timeout=15)
            raw_urls = re.findall(r'https://www\.tiktok\.com/@[\w\.]+/video/\d+', response.text)
            raw_urls = list(dict.fromkeys(raw_urls))
            
            for video_url in raw_urls:
                if len(videos_found) >= limit:
                    break
                if video_url in checked_urls:
                    continue
                checked_urls.add(video_url)
                
                if not await is_video_fresh(video_url, max_days_old):
                    continue
                
                if other_tags and not await check_video_hashtags(video_url, other_tags):
                    continue
                
                videos_found.append({"url": video_url})
            
            page += 1
        except Exception as e:
            print(f"Ошибка поиска: {e}")
            break
    
    return videos_found[:limit]

async def download_video(url: str) -> str:
    output_path = "temp_video.mp4"
    ydl_opts = {
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
        'format': 'best[ext=mp4]/best',
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return output_path
    except Exception as e:
        print(f"Ошибка скачивания: {e}")
        return None

# ===== КОМАНДЫ БОТА =====
async def start(update: Update, context):
    await update.message.reply_text(
        "👋 Привет! Я ищу видео в TikTok по хештегам.\n\n"
        "📌 *Команды:*\n"
        "`#коты` - поиск за последние 3 дня\n"
        "`#коты #смешные` - видео с ОБОИМИ тегами\n"
        "`#коты days=7` - видео за последнюю неделю\n\n"
        "🔍 Бот ищет только свежие видео!",
        parse_mode="Markdown"
    )

async def handle_hashtag(update: Update, context):
    text = update.message.text.strip()
    
    days_match = re.search(r'days[=\s]+(\d+)', text, re.IGNORECASE)
    max_days = int(days_match.group(1)) if days_match else 3
    
    clean_text = re.sub(r'\s*days[=\s]+\d+', '', text, flags=re.IGNORECASE)
    hashtags = re.findall(r'#\w+', clean_text)
    
    if not hashtags:
        await update.message.reply_text("❌ Напиши хотя бы один хештег, например: #коты")
        return
    
    if len(hashtags) > 3:
        await update.message.reply_text("⚠️ Можно искать максимум по 3 хештегам")
        return
    
    tags_str = ' '.join(hashtags)
    msg = await update.message.reply_text(f"🔍 Ищу видео (до {max_days} дней) с тегами: {tags_str}\n⏱️ Займёт 20-40 секунд...")
    
    videos = await search_tiktok_by_hashtags(hashtags, limit=2, max_days_old=max_days)
    
    if not videos:
        await msg.edit_text(f"❌ Не нашёл свежих видео с тегами: {tags_str}\n💡 Попробуй: {hashtags[0]} days=10")
        return
    
    await msg.edit_text(f"📹 Нашёл {len(videos)} видео, скачиваю...")
    
    for i, video in enumerate(videos, 1):
        status_msg = await update.message.reply_text(f"⏳ Скачиваю {i} из {len(videos)}...")
        video_path = await download_video(video['url'])
        
        if video_path and os.path.exists(video_path):
            try:
                with open(video_path, 'rb') as f:
                    await update.message.reply_video(
                        video=f, 
                        caption=f"📌 {tags_str}\n📅 За {max_days} дней"
                    )
                os.remove(video_path)
                await status_msg.delete()
            except Exception as e:
                await status_msg.edit_text(f"❌ Ошибка: {str(e)[:100]}")
        else:
            await status_msg.edit_text("❌ Не удалось скачать видео")
    
    await update.message.reply_text("✅ Готово!")

# Регистрируем обработчики
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_hashtag))

# ===== WEBHOOK ЭНДПОИНТ =====
@flask_app.route(f'/webhook/{BOT_TOKEN}', methods=['POST'])
async def webhook():
    """Принимает обновления от Telegram"""
    try:
        update = Update.de_json(request.get_json(force=True), telegram_app.bot)
        await telegram_app.process_update(update)
        return 'ok', 200
    except Exception as e:
        print(f"Ошибка webhook: {e}")
        return 'error', 500

@flask_app.route('/', methods=['GET'])
def health():
    """Health check для Railway"""
    return 'Bot is running!', 200

# ===== ЗАПУСК =====
def setup_webhook():
    """Устанавливает вебхук при запуске"""
    webhook_url = f"{RAILWAY_URL}/webhook/{BOT_TOKEN}"
    print(f"🔗 Устанавливаю вебхук: {webhook_url}")
    
    # Устанавливаем вебхук
    result = telegram_app.bot.set_webhook(url=webhook_url)
    if result:
        print("✅ Вебхук успешно установлен!")
    else:
        print("❌ Ошибка установки вебхука!")
    
    # Показываем информацию о вебхуке
    webhook_info = telegram_app.bot.get_webhook_info()
    print(f"📡 Текущий вебхук: {webhook_info.url}")

if __name__ == '__main__':
    print("🚀 Запуск бота на Railway с Webhook...")
    
    # Устанавливаем вебхук перед запуском Flask
    # ВНИМАНИЕ! Для асинхронной установки используем run_until_complete
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(setup_webhook())
    
    # Запускаем Flask сервер
    port = int(os.environ.get('PORT', 8080))
    print(f"🔥 Flask сервер запущен на порту {port}")
    flask_app.run(host='0.0.0.0', port=port)
