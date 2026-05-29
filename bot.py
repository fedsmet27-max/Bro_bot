
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
    # Render передает порт в переменную окружения PORT
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), SimpleHTTPServer)
    print(f"Старт микро-сервера на порту {port}...")
    server.serve_forever()

# Запускаем веб-сервер в отдельном потоке, чтобы не мешал боту
Thread(target=run_web_server, daemon=True).start()
# -------------------------------------

# Забираем ключи из настроек сервера
BOT_TOKEN = os.environ.get('TELEGRAM_TOKEN')
API_KEY = os.environ.get('OPENROUTER_API_KEY')
SYSTEM_PROMPT = os.environ.get('PROMPT')

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
user_history = {}

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
        "model": "meta-llama/llama-3-8b-instruct:free",
        "messages": messages
    }
    
    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data, timeout=15)
        result = response.json()
        bro_text = result['choices'][0]['message']['content']
        
        user_history[chat_id].append({"role": "assistant", "content": bro_text})
        return bro_text
    except Exception as e:
        print(f"Ошибка OpenRouter: {e}")
        return "Братка, чё-то связь тупит, повтори мысль!"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        bot.reply_to(message, "Здорово, родной! Я на связи. С этого момента общаемся в Телеге без ограничений. Рассказывай, чё там у тебя?")
    except Exception as e:
        print(f"Ошибка старта: {e}")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        response = get_bro_response(message.chat.id, message.text)
        bot.reply_to(message, response)
    except Exception as e:
        print(f"Ошибка отправки: {e}")


    if __name__ == "__main__":
    print("=== ЗАПУСК БОТА СТАРТОВАЛ ===")
    try:
        print(f"Пробуем подключиться с токеном: {BOT_TOKEN[:10]}...***") # покажет первые 10 символов токена
        bot.remove_webhook() # на всякий случай сбрасываем старые вебхуки
        print("Вебхуки сброшены, запускаем polling...")
        bot.polling(none_stop=True, interval=1, timeout=60)
    except Exception as e:
        print(f"!!! КРИТИЧЕСКАЯ ОШИБКА СТАРТА: {e}")

