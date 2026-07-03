import telebot
from telebot import types
import yt_dlp
import os
import threading
import time
import base64
from flask import Flask
from threading import Thread

# ====================== SECURED LINKS ======================
YOUTUBE_CHANNEL = base64.b64decode("aHR0cHM6Ly93d3cueW91dHViZS5jb20vQGJsYWNrX2tub3dsZWRnZV8xOTA=").decode('utf-8')
SUPPORT_GROUP = base64.b64decode("aHR0cHM6Ly90Lm1lL0JMQUNLX0tOT1dMRURHRV8xOTA=").decode('utf-8')
# ========================================================

# Bot Token (Set as Environment Variable on Render)
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set!")

bot = telebot.TeleBot(TOKEN)

# Flask for 24/7 uptime on Render
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ BLACK_KNOWLEDGE_190 Video Downloader Bot is Running!"

def run_flask():
    app.run(host='0.0.0.0', port=10000)

# Keep-alive thread
def keep_alive():
    while True:
        try:
            bot.get_me()
            time.sleep(300)
        except:
            time.sleep(60)

# Start background services
flask_thread = Thread(target=run_flask)
flask_thread.daemon = True
flask_thread.start()

keep_thread = Thread(target=keep_alive)
keep_thread.daemon = True
keep_thread.start()

def create_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    btn1 = types.InlineKeyboardButton("📢 SUBSCRIBE CHANNEL", url=YOUTUBE_CHANNEL)
    btn2 = types.InlineKeyboardButton("📚 ALL TUTORIALS", url=YOUTUBE_CHANNEL)
    btn3 = types.InlineKeyboardButton("👨‍💻 CONTACT OWNER", url=SUPPORT_GROUP)
    keyboard.add(btn1, btn2, btn3)
    return keyboard

@bot.message_handler(commands=['start'])
def start(message):
    welcome_text = (
        "🌟 **Premium Video Downloader Bot** 🌟\n\n"
        "Send any video link from:\n"
        "• YouTube\n"
        "• Instagram Reels\n"
        "• Facebook\n"
        "• And 1000+ other sites\n\n"
        "🤖 Powered by @BLACK_KNOWLEDGE_190"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode='Markdown', reply_markup=create_keyboard())

def progress_hook(d, message, chat_id):
    try:
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', '0%')
            bot.edit_message_text(
                f"⬇️ **Downloading...** {percent}",
                chat_id=chat_id,
                message_id=message.message_id
            )
        elif d['status'] == 'finished':
            bot.edit_message_text(
                "✅ Download complete!\n⬆️ Uploading to Telegram...",
                chat_id=chat_id,
                message_id=message.message_id
            )
    except:
        pass

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    if not message.text or not any(x in message.text.lower() for x in ['http', 'www']):
        return

    url = message.text.strip()
    chat_id = message.chat.id

    status_msg = bot.reply_to(message, "🔍 **Analyzing link...**")

    try:
        ydl_opts = {
            'format': 'best[height<=720]/best',  # Good quality, Telegram-friendly
            'outtmpl': '%(title)s.%(ext)s',
            'progress_hooks': [lambda d: progress_hook(d, status_msg, chat_id)],
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            filename = ydl.prepare_filename(info)

            # Download phase
            bot.edit_message_text("⬇️ **Downloading...**", chat_id, status_msg.message_id)
            ydl.download([url])

            # Upload phase
            bot.edit_message_text("⬆️ **Uploading to Telegram...**", chat_id, status_msg.message_id)

            with open(filename, 'rb') as video_file:
                bot.send_video(
                    chat_id,
                    video_file,
                    caption="✅ **Downloaded Successfully!**\nPower by: @BLACK_KNOWLEDGE_190",
                    supports_streaming=True
                )

            # Cleanup
            if os.path.exists(filename):
                os.remove(filename)

            # Delete status message
            bot.delete_message(chat_id, status_msg.message_id)

    except Exception as e:
        error_msg = str(e)[:300]
        bot.edit_message_text(f"❌ **Error:** {error_msg}\n\nTry again or contact owner.", chat_id, status_msg.message_id)

if __name__ == '__main__':
    print("🚀 BLACK_KNOWLEDGE_190 Video Downloader Bot Started...")
    bot.infinity_polling()
