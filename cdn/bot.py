import os
import logging
from flask import Flask, request
import telebot

# Создаем Flask приложение
app = Flask(__name__)

# Получаем токен из переменных окружения
TOKEN = os.environ.get('BOT_TOKEN')
if not TOKEN:
    raise ValueError("BOT_TOKEN не найден! Добавьте переменную окружения BOT_TOKEN")

# Создаем бота
bot = telebot.TeleBot(TOKEN)

# Настраиваем логирование
logging.basicConfig(level=logging.INFO)

# ========== ОБРАБОТЧИКИ КОМАНД ==========

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Ответ на команду /start"""
    bot.reply_to(message, "Привет! Я бот, работающий через вебхук на Render. Отправь мне любое сообщение!")

@bot.message_handler(commands=['help'])
def send_help(message):
    """Ответ на команду /help"""
    bot.reply_to(message, "Доступные команды:\n/start - приветствие\n/help - эта справка\n/info - информация о боте")

@bot.message_handler(commands=['info'])
def send_info(message):
    """Ответ на команду /info"""
    bot.reply_to(message, f"Бот запущен на Render\nВерсия: 1.0\nТвой ID: {message.chat.id}")

# ========== ОБРАБОТЧИК ТЕКСТОВЫХ СООБЩЕНИЙ ==========

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    """Эхо-бот: отвечает тем же текстом"""
    bot.reply_to(message, f"Ты написал: {message.text}")

# ========== ЭНДПОИНТЫ FLASK ==========

@app.route('/webhook', methods=['POST'])
def webhook():
    """Эндпоинт для вебхука Telegram"""
    try:
        # Получаем обновление от Telegram
        json_str = request.stream.read().decode('utf-8')
        update = telebot.types.Update.de_json(json_str)
        
        # Обрабатываем обновление
        bot.process_new_updates([update])
        
        return 'OK', 200
    except Exception as e:
        logging.error(f"Ошибка в вебхуке: {e}")
        return 'Error', 500

@app.route('/')
def index():
    """Главная страница для проверки работы"""
    return 'Telegram бот работает! Используй вебхук: /webhook'

@app.route('/set_webhook')
def set_webhook():
    """Эндпоинт для установки вебхука (вызови один раз после деплоя)"""
    try:
        # Формируем URL вебхука (используем текущий хост)
        webhook_url = f"https://{request.host}/webhook"
        
        # Удаляем старый вебхук и устанавливаем новый
        bot.remove_webhook()
        bot.set_webhook(url=webhook_url)
        
        logging.info(f"Вебхук установлен: {webhook_url}")
        return f'✅ Вебхук успешно установлен на: {webhook_url}', 200
    except Exception as e:
        logging.error(f"Ошибка установки вебхука: {e}")
        return f'❌ Ошибка: {e}', 500

@app.route('/get_webhook_info')
def get_webhook_info():
    """Эндпоинт для проверки статуса вебхука"""
    try:
        info = bot.get_webhook_info()
        return f'Статус вебхука:\n{info}', 200
    except Exception as e:
        return f'Ошибка: {e}', 500

# ========== ЗАПУСК (ТОЛЬКО ДЛЯ ЛОКАЛЬНОГО ТЕСТА) ==========

if __name__ == '__main__':
    # Для локального тестирования без вебхука
    # Запусти: python bot.py
    port = int(os.environ.get('PORT', 5000))
    
    # Проверяем, запущен ли бот локально или на сервере
    if os.environ.get('RENDER'):
        # На Render используем вебхук через Flask
        app.run(host='0.0.0.0', port=port)
    else:
        # Локально используем polling
        print("Запуск в локальном режиме (polling)...")
        bot.remove_webhook()
        bot.polling(none_stop=True)
