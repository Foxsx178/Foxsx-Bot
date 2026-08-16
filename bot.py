import json
import os
import random

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    ConversationHandler,
)

TOKEN = os.getenv("TOKEN")
DATA_FILE = "users.json"

# Состояние для игры "Угадай число"
CHOOSING_NUMBER = 1


def load_users():
    if not os.path.exists(DATA_FILE):
        return {}

    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def save_users(users):
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(users, file, ensure_ascii=False, indent=4)


users = load_users()


def get_user(update):
    user = update.effective_user
    user_id = str(user.id)

    if user_id not in users:
        users[user_id] = {
            "name": user.first_name,
            "coins": 0,
            "games": 0,
            "wins": 0
        }
        save_users(users)

    return users[user_id]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    get_user(update)

    keyboard = [
        ["👤 Профиль"],
        ["🎮 Игра", "🏆 Топ игроков"]
    ]

    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

    await update.message.reply_text(
        "Привет! 🤖\n\nВыбери действие:",
        reply_markup=reply_markup
    )


async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update)

    await update.message.reply_text(
        f"👤 Профиль\n\n"
        f"🪙 Монетки: {user['coins']}\n"
        f"🎮 Игр сыграно: {user['games']}\n"
        f"🏆 Побед: {user['wins']}"
    )


# --- Логика игры "Угадай число (1-100)" ---

async def play_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Загадываем число от 1 до 100
    secret_number = random.randint(1, 100)
    context.user_data["secret_number"] = secret_number

    await update.message.reply_text(
        "🎮 Я загадал число **от 1 до 100**.\n"
        "Попробуй угадать! Напиши свое число в чат 👇\n\n"
        "*(Если хочешь выйти, просто нажми другую кнопку в меню)*"
    )
    return CHOOSING_NUMBER


async def guess_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    # Если пользователь нажал на кнопку меню, прерываем игру
    if text in ["👤 Профиль", "🎮 Игра", "🏆 Топ игроков"]:
        return ConversationHandler.END

    # Проверяем, ввел ли пользователь именно число
    if not text.isdigit():
        await update.message.reply_text("⚠️ Пожалуйста, введи число цифрами от 1 до 100!")
        return CHOOSING_NUMBER

    user_guess = int(text)
    secret_number = context.user_data.get("secret_number")
    user = get_user(update)

    if user_guess == secret_number:
        user["games"] += 1
        user["coins"] += 10
        user["wins"] += 1
        save_users(users)

        await update.message.reply_text(
            f"🎉 Поздравляю! Ты угадал число {secret_number}!\n"
            f"🪙 Ты получил +10 монеток!"
        )
        return ConversationHandler.END

    elif user_guess < secret_number:
        await update.message.reply_text("📈 Мое число **больше**! Попробуй еще раз:")
        return CHOOSING_NUMBER

    else:
        await update.message.reply_text("📉 Мое число **меньше**! Попробуй еще раз:")
        return CHOOSING_NUMBER


async def cancel_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Игра отменена.")
    return ConversationHandler.END


# --- Обработчик обычных кнопок меню ---

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "👤 Профиль":
        await profile(update, context)
    elif text == "🏆 Топ игроков":
        await update.message.reply_text("🏆 Таблица лидеров пока пустая.")


# Инициализация приложения
app = Application.builder().token(TOKEN).build()

# Создаем обработчик диалога для игры
game_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.Regex("^🎮 Игра$"), play_game)],
    states={
        CHOOSING_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, guess_number)],
    },
    fallbacks=[CommandHandler("cancel", cancel_game)],
)

# Регистрируем хендлеры
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("profile", profile))
app.add_handler(game_handler)  # Игра должна стоять выше общего текстового обработчика
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler))

print("Бот запущен!")
app.run_polling()
      
