import os
import yt_dlp
import telebot
from telebot import types

# Bot tokeningizni shu yerga yozing
TOKEN = '7402798345:AAHiE4j5YtRAjxvbagNraNK5QN9IkmBPoqE'  # ← bu yerga o'z tokeningizni yozing

# FFmpeg to‘liq yo‘li (faqat shu papkada tursa)
FFMPEG_PATH = os.path.join(os.getcwd(), 'ffmpeg', 'bin', 'ffmpeg.exe')

# Botni yaratish
bot = telebot.TeleBot(TOKEN)

# Har bir foydalanuvchi uchun linkni saqlovchi dict
user_links = {}

# /start komandasi
@bot.message_handler(commands=['start'])
def welcome(message):
    bot.send_message(message.chat.id, "Salom! YouTube yoki Instagram linkini yuboring.")

# Link yuborilganda
@bot.message_handler(func=lambda msg: msg.text and msg.text.startswith("http"))
def handle_link(message):
    user_links[message.chat.id] = message.text.strip()
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🎥 Video (MP4 360p)", callback_data="video"),
        types.InlineKeyboardButton("🎧 MP3 (audio)", callback_data="mp3")
    )
    bot.send_message(message.chat.id, "Qaysi formatda yuklab olay?", reply_markup=markup)

# Tugma bosilganda ishlovchi funksiya
@bot.callback_query_handler(func=lambda call: call.data in ["video", "mp3"])
def download_media(call):
    url = user_links.get(call.message.chat.id)
    if not url:
        bot.send_message(call.message.chat.id, "Avval link yuboring.")
        return

    media_type = call.data
    bot.send_message(call.message.chat.id, "⏳ Yuklab olinmoqda, biroz kuting...")

    os.makedirs("downloads", exist_ok=True)

    if media_type == "video":
        ydl_opts = {
            'format': 'bestvideo[height<=360]+bestaudio/best',
            'merge_output_format': 'mp4',
            'ffmpeg_location': FFMPEG_PATH,
            'outtmpl': 'downloads/%(title).50s.%(ext)s',
            'quiet': True,
            'noplaylist': True
        }
    else:
        ydl_opts = {
            'format': 'bestaudio/best',
            'ffmpeg_location': FFMPEG_PATH,
            'outtmpl': 'downloads/%(title).50s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
            'noplaylist': True
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filepath = ydl.prepare_filename(info)

        if media_type == "mp3":
            filepath = os.path.splitext(filepath)[0] + ".mp3"
            with open(filepath, 'rb') as f:
                bot.send_audio(call.message.chat.id, f)
        else:
            filepath = os.path.splitext(filepath)[0] + ".mp4"
            with open(filepath, 'rb') as f:
                bot.send_video(call.message.chat.id, f)

        os.remove(filepath)

    except Exception as e:
        print(str(e))  # terminalga chiqaradi
        bot.send_message(call.message.chat.id, f"❌ Xatolik:\n{str(e)}")

# Botni ishga tushirish
bot.polling(none_stop=True)
