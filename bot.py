import os
import time
import requests
import telebot
from threading import Thread
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- МИКРО-СЕРВЕР ДЛЯ ОБМАНА RENDER ---
class SimpleHTTPServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Bot is alive!")

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), SimpleHTTPServer)
    print(f"Старт микро-сервера на порту {port}...")
    server.serve_forever()

Thread(target=run_web_server, daemon=True).start()
# -------------------------------------

BOT_TOKEN = os.environ.get('TELEGRAM_TOKEN')
API_KEY = os.environ.get('OPENROUTER_API_KEY')
SYSTEM_PROMPT = os.environ.get('PROMPT')

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
user_history = {}

# Функция распознавания голоса через OpenRouter (модель Whisper)
def transcribe_audio(file_path):
    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }
    try:
        with open(file_path, 'rb') as f:
            files = {
                'file': ('audio.ogg', f, 'audio/ogg'),
                'model': (None, 'openai/whisper-large-v3')
            }
            # Стучимся на эндпоинт аудио-транскрибации OpenRouter
            response = requests.post(
                "https://openrouter.ai/api/v1/audio/transcriptions",
                headers=headers,
                files=files,
                timeout=30
            )
            result = response.json()
            return result.get('text', '')
    except Exception as e:
        print(f"Ошибка распознавания голоса: {e}")
        return ""

def get_bro_response(chat_id, user_message):
    global user_history
    if chat_id not in user_history:
        user_history[chat_id] = []
    
    user_history[chat_id].append({"role": "user", "content": user_message})
    if len(user_history[chat_id]) > 10:
        user_history[chat_id] = user_history[chat_id][-10:]
        
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + user_history[chat_id]
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "openrouter/auto",
        "messages": messages
    }
    
    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data, timeout=15)
        result = response.json()
        bro_text = result['choices'][0]['message']['content']
        user_history[chat_id].append({"role": "assistant", "content": bro_text})
        return bro_text
    except Exception as e:
        print(f"!!! КРИТИЧЕСКАЯ ОШИБКА OPENROUTER: {e}")
        return "Братка, чё-то связь тупит, повтори мысль!"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        bot.reply_to(message, "Здорово, родной! Я на связи. Можешь писать, накидывать ГС или кружочки — я всё пойму и раскидаю по красоте. Рассказывай, че там у тебя?")
    except Exception as e:
        print(f"Ошибка старта: {e}")

# Обработчик для ГС и кружков
@bot.message_handler(content_types=['voice', 'video_note'])
def handle_audio_messages(message):
    try:
        bot.send_chat_action(message.chat.id, 'record_audio')
        
        # Определяем тип медиа и забираем file_id
        if message.content_type == 'voice':
            file_id = message.voice.file_id
            msg_type = "ГС"
        else:
            file_id = message.video_note.file_id
            msg_type = "кружочек"
            
        print(f"Получен {msg_type}, скачиваем...")
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Временно сохраняем аудиофайл на сервере
        temp_filename = f"temp_{message.chat.id}.ogg"
        with open(temp_filename, 'wb') as new_file:
            new_file.write(downloaded_file)
            
        bot.reply_to(message, f"Так, брат, поймал твой {msg_type}, сейчас расшифрую, вникаю...")
        bot.send_chat_action(message.chat.id, 'typing')
        
        # Переводим аудио в текст
        transcribed_text = transcribe_audio(temp_filename)
        
        # Удаляем временный файл, чтобы не забивать диск Рендера
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
            
        if not transcribed_text:
            bot.reply_to(message, "Братка, чё-то шумно у тебя, не разобрал ни слова. Наговори почётче или черкани текстом!")
            return
            
        print(f"Успешно расшифровано: {transcribed_text}")
        
        # Отправляем распознанный текст в ИИ и отвечаем юзеру
        response = get_bro_response(message.chat.id, f"[Расшифровка моего {msg_type}]: {transcribed_text}")
        bot.reply_to(message, response)
        
    except Exception as e:
        print(f"Ошибка обработки аудио: {e}")
        bot.reply_to(message, "Братка, со звуком какая-то лажа произошла, не могу разобрать!")

# Обработчик для фоток, документов и стикеров
@bot.message_handler(content_types=['photo', 'document', 'sticker'])
def handle_other_media(message):
    try:
        bot.reply_to(message, "Братка, фотки и файлы — это тема, но я пока слепой, глаза еще не настроил. Напиши текстом или наговори ГС/кружок!")
    except Exception as e:
        print(f"Ошибка медиа: {e}")

# Обработчик для обычного текста
@bot.message_handler(content_types=['text'])
def echo_all(message):
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        response = get_bro_response(message.chat.id, message.text)
        bot.reply_to(message, response)
    except Exception as e:
        print(f"Ошибка отправки: {e}")

if __name__ == "__main__":
    print("Запускаем бота...")
    bot.remove_webhook()
    bot.polling(none_stop=True, interval=1, timeout=60)

