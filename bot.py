
import os
import time
import requests
import telebot

# Забираем ключи из настроек сервера
BOT_TOKEN = os.environ.get('TELEGRAM_TOKEN')
API_KEY = os.environ.get('OPENROUTER_API_KEY')
SYSTEM_PROMPT = os.environ.get('PROMPT')

# Инициализируем бота с увеличенным таймаутом для стабильности
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
        bot.reply_to(message, "Здорово, родной! Я на связи. С этого момента общаемся в Телеге без ограничений. Рассказывай, чё там у тебя? Как служба, как Варька?")
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
    print("Бро запущен...")
    # Бесконечный цикл с защитой от вылетания сети
    while True:
        try:
            bot.polling(none_stop=True, interval=1, timeout=60)
        except Exception as e:
            print(f"Сбой сети, перезапуск через 5 сек... Ошибка: {e}")
            time.sleep(5)
