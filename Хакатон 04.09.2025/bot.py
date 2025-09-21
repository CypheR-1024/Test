from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Путь к файлу с данными о породах
BREEDS_FILE = 'breeds.txt'

# Вопросы (12 параметров)
QUESTIONS = [
    {"text": "Оцените желаемую агрессивность:", "key": "aggressiveness"},
    {"text": "Оцените желаемую активность:", "key": "activity"},
    {"text": "Оцените желаемую легкость дрессировки:", "key": "trainability"},
    {"text": "Оцените допустимую интенсивность линьки:", "key": "shedding"},
    {"text": "Оцените допустимую потребность в уходе:", "key": "grooming"},
    {"text": "Оцените желаемую дружелюбность:", "key": "friendliness"},
    {"text": "Оцените допустимые проблемы со здоровьем:", "key": "health"},
    {"text": "Оцените бюджет на содержание:", "key": "cost"},
    {"text": "Как долго животное будет оставаться одно?", "key": "alone_tolerance"},
    {"text": "Оцените желаемый уровень интеллекта:", "key": "intelligence"},
    {"text": "Оцените допустимый уровень шума:", "key": "noise"},
    {"text": "Оцените важность охранных качеств:", "key": "guarding"}
]

# Варианты оценок
OPTIONS = ['1', '2', '3', '4', '5']

user_data = {}

# Загрузка пород из файла
def load_breeds():
    try:
        with open(BREEDS_FILE, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
    except FileNotFoundError:
        raise Exception(f"Файл {BREEDS_FILE} не найден!")

    breeds = []
    index = 0
    while index + 28 < len(lines):
        try:
            breed = {
                "name": lines[index + 0],
                "country": lines[index + 1],
                "weight": lines[index + 2],
                "height": lines[index + 3],
                "lifespan": lines[index + 4],
                "aggressiveness_text": lines[index + 5],
                "aggressiveness": int(lines[index + 6]),
                "activity_text": lines[index + 7],
                "activity": int(lines[index + 8]),
                "trainability_text": lines[index + 9],
                "trainability": int(lines[index + 10]),
                "shedding_text": lines[index + 11],
                "shedding": int(lines[index + 12]),
                "grooming_text": lines[index + 13],
                "grooming": int(lines[index + 14]),
                "friendliness_text": lines[index + 15],
                "friendliness": int(lines[index + 16]),
                "health_text": lines[index + 17],
                "health": int(lines[index + 18]),
                "cost_text": lines[index + 19],
                "cost": int(lines[index + 20]),
                "alone_tolerance_text": lines[index + 21],
                "alone_tolerance": int(lines[index + 22]),
                "intelligence_text": lines[index + 23],
                "intelligence": int(lines[index + 24]),
                "noise_text": lines[index + 25],
                "noise": int(lines[index + 26]),
                "guarding_text": lines[index + 27],
                "guarding": int(lines[index + 28]),
            }
            breeds.append(breed)
            index += 29
        except Exception as e:
            logging.warning(f"Ошибка при парсинге породы, начиная с {lines[index] if index < len(lines) else 'конец файла'}: {e}")
            index += 1
    return breeds

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name or "Пользователь"

    # Приветственное сообщение
    welcome_text = (
        f"Привет, {user_name}! 👋\n\n"
        "Я — *Собачий Подборщик* 🐶✨\n"
        "Помогу подобрать идеальную породу собаки под твой образ жизни и предпочтения.\n\n"
        "Пройди короткий опрос из 12 вопросов — и получишь персональную рекомендацию!\n\n"
        "Готов? Нажимай на кнопку ниже, чтобы начать! 🚀"
    )

    # начало опроса
    keyboard = [[InlineKeyboardButton("🐾 Начать подбор породы", callback_data="start_quiz")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Отправляем приветствие
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

    # Инициализируем данные пользователя
    user_data[user_id] = {"answers": {}, "current_question": 0}

# следующий вопрос
async def ask_question(update_or_query, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    question_index = user_data[user_id]["current_question"]

    if question_index >= len(QUESTIONS):
        await process_results(update_or_query, context)
        return

    question = QUESTIONS[question_index]
    keyboard = [
        [InlineKeyboardButton(f"{opt}/5", callback_data=f"{question['key']}|{opt}")]
        for opt in OPTIONS
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # chat_id
    if isinstance(update_or_query, Update):
        chat_id = update_or_query.effective_chat.id
    else:
        chat_id = update_or_query.message.chat_id

    await context.bot.send_message(
        chat_id=chat_id,
        text=question["text"],
        reply_markup=reply_markup
    )

# Обработка ответов
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = update.effective_user.id

    # Проверка, существует ли пользователь
    if user_id not in user_data:
        await query.message.reply_text("Начните с команды /start")
        return

    # Обработка нажатия на кнопку "Начать"
    if data == "start_quiz":
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except Exception as e:
            logging.warning(f"Не удалось убрать клавиатуру: {e}")
        await ask_question(query, context, user_id)
        return

    # Обработка ответов на вопросы
    if '|' not in data:
        await query.message.reply_text("Ошибка: неверный формат данных.")
        return

    key, value_str = data.split('|', 1)

    if value_str not in OPTIONS:
        await query.message.reply_text("Выберите оценку от 1 до 5.")
        return

    # Сохраняем ответ
    user_data[user_id]["answers"][key] = int(value_str)

    # Убираем клавиатуру
    try:
        await query.edit_message_reply_markup(reply_markup=None)
    except Exception as e:
        logging.warning(f"Не удалось убрать клавиатуру: {e}")

    # Переход к следующему вопросу
    user_data[user_id]["current_question"] += 1
    await ask_question(query, context, user_id)

# Поиск лучшей породы и вывод результата
async def process_results(update_or_query, context: ContextTypes.DEFAULT_TYPE):
    # Определяем user_id и chat_id
    if isinstance(update_or_query, Update):
        user_id = update_or_query.effective_user.id
        chat_id = update_or_query.effective_chat.id
    else:
        user_id = update_or_query.from_user.id
        chat_id = update_or_query.message.chat_id

    if user_id not in user_data:
        await context.bot.send_message(
            chat_id=chat_id,
            text="Начните с команды /start"
        )
        return

    user_answers = user_data[user_id]["answers"]

    try:
        breeds = load_breeds()
    except Exception as e:
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"Ошибка загрузки данных: {e}"
        )
        return

    best_breed = None
    min_diff = float('inf')

    for breed in breeds:
        total_diff = 0
        for param in ["aggressiveness", "activity", "trainability", "shedding", "grooming",
                      "friendliness", "health", "cost", "alone_tolerance", "intelligence", "noise", "guarding"]:
            user_val = user_answers.get(param, 3)
            breed_val = breed.get(param, 3)
            total_diff += abs(user_val - breed_val)

        if total_diff < min_diff:
            min_diff = total_diff
            best_breed = breed

    if best_breed:
        result = (
            f"🐾 *Рекомендуемая порода: {best_breed['name']}*\n\n"
            f"🌍 *Страна:* {best_breed['country']}\n"
            f"⚖️ *Вес:* {best_breed['weight']}\n"
            f"📏 *Рост:* {best_breed['height']}\n"
            f"⏳ *Продолжительность жизни:* {best_breed['lifespan']}\n\n"
            f"🔥 *Агрессивность:* {best_breed['aggressiveness_text']} ({best_breed['aggressiveness']}/5)\n"
            f"⚡ *Активность:* {best_breed['activity_text']} ({best_breed['activity']}/5)\n"
            f"🎓 *Дрессировка:* {best_breed['trainability_text']} ({best_breed['trainability']}/5)\n"
            f"🍂 *Линька:* {best_breed['shedding_text']} ({best_breed['shedding']}/5)\n"
            f"🛁 *Уход:* {best_breed['grooming_text']} ({best_breed['grooming']}/5)\n"
            f"❤️ *Дружелюбность:* {best_breed['friendliness_text']} ({best_breed['friendliness']}/5)\n"
            f"🏥 *Здоровье:* {best_breed['health_text']} ({best_breed['health']}/5)\n"
            f"💰 *Стоимость:* {best_breed['cost_text']} ({best_breed['cost']}/5)\n"
            f"🕒 *Одиночество:* {best_breed['alone_tolerance_text']} ({best_breed['alone_tolerance']}/5)\n"
            f"🧠 *Интеллект:* {best_breed['intelligence_text']} ({best_breed['intelligence']}/5)\n"
            f"🔊 *Шум:* {best_breed['noise_text']} ({best_breed['noise']}/5)\n"
            f"🛡️ *Охрана:* {best_breed['guarding_text']} ({best_breed['guarding']}/5)\n\n"
            f"✅ *Наилучшее совпадение!*"
        )
        await context.bot.send_message(
            chat_id=chat_id,
            text=result,
            parse_mode='Markdown'
        )
    else:
        await context.bot.send_message(
            chat_id=chat_id,
            text="К сожалению, не удалось найти подходящую породу."
        )

# Запуск бота
def main():
    TOKEN = "*"  # !Заменить на реальный токен!

    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))

    print("Бот запущен. Ожидание команд...")
    application.run_polling()

if __name__ == "__main__":
    main()
