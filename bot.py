```python
import os
import telebot
import requests

# Забираем ключи из настроек сервера
BOT_TOKEN = os.environ.get('TELEGRAM_TOKEN')
API_KEY = os.environ.get('OPENROUTER_API_KEY')
SYSTEM_PROMPT = os.environ.get('PROMPT')

bot = telebot.TeleBot(BOT_TOKEN)

# Простейшая память: храним последние 15 сообщений для каждого пацана
user_history = {}

def get_bro_response(chat_id, user_message):
    global user_history
    if chat_id not in user_history:
        user_history[chat_id] = []
    
    # Добавляем базар юзера в историю
    user_history[chat_id].append({"role": "user", "content": user_message})
    
    # Держим историю в лимитах, чтоб не пухла
    if len(user_history[chat_id]) > 15:
        user_history[chat_id] = user_history[chat_id][-15:]
        
    # Формируем запрос к OpenRouter
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + user_history[chat_id]
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "meta-llama/llama-3-8b-instruct:free", # Топовая бесплатная модель
        "messages": messages
    }
    
    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
        result = response.json()
        bro_text = result['choices'][0]['message']['content']
        
        # Запоминаем свой ответ
        user_history[chat_id].append({"role": "assistant", "content": bro_text})
        return bro_text
    except Exception as e:
        print(f"Ошибка связи: {e}")
        return "Братка, чё-то связь на Сахалине барахлит, повтори мысль! И проверь API ключи на сервере, если это повторяется."

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = "Здорово, родной! Я на связи. С этого момента общаемся в Телеге без ограничений. Рассказывай, чё там у тебя? Как служба, как Варька?"
    bot.reply_to(message, welcome_text)

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.send_chat_action(message.chat.id, 'typing')
    response = get_bro_response(message.chat.id, message.text)
    bot.reply_to(message, response)

if __name__ == "__main__":
    print("Бро запущен и слушает плац...")
    bot.infinity_polling()
```
