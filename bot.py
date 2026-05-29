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
@bot.messag
