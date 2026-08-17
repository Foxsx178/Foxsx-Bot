import os
import json
import random
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)

# Читаем токен из переменных окружения Render
TOKEN = os.getenv("TOKEN")
USERS_FILE = "users.json"

# Состояния для диалога по шагам (Пункт 4)
GET_NAME, GET_AGE = range(2)

# Состояние для игры "Угадай число"
CHOOSING_NUMBER = 1


# --- РАБОТА С БАЗОЙ ПОЛЬЗОВАТЕЛЕЙ (Пункт 3) ---
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


def save_user(user_id):
    users = load_users()
    if user_id not in users:
        users.append(user_id)
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f)


# --- ОСНОВНЫЕ КОМАНДЫ ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    save_user(user_id)  # Сохраняем пользователя для рассылки

    await update.message.reply_text(
        "Привет! Я твой бот.\n\n"
        "Доступные команды:\n"
        "/game — Сыграть в «Угадай число»\n"
        "/reg — Заполнить анкету (по шагам)\n"
        "/send_all <текст> — Сделать рассылку (только для админа)"
    )


# --- ИГРА «УГАДАЙ ЧИСЛО» ---
async def game_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["secret_number"] = random.randint(1, 10)
    await update.message.reply_text(
        "Я загадал число от 1 до 10. Попробуй угадать!\nНапиши свое число:"
    )
    return CHOOSING_NUMBER


async def game_guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_guess = int(update.message.text)
    except ValueError:
        await update.message.reply_text("Пожалуйста, введи именно число от 1 до 10:")
        return CHOOSING_NUMBER

    secret_number = context.user_data.get("secret_number")

    if user_guess == secret_number:
        await update.message.reply_text("🎉 Поздравляю, ты угадал число!")
        return ConversationHandler.END
    elif user_guess < secret_number:
        await update.message.reply_text("Мое число больше! Попробуй еще раз:")
        return CHOOSING_NUMBER
    else:
        await update.message.reply_text("Мое число меньше! Попробуй еще раз:")
        return CHOOSING_NUMBER


# --- РАССЫЛКА ДЛЯ ВСЕХ (Пункт 3) ---
async def send_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Вставь сюда свой реальный Telegram ID цифрами
    ADMIN_ID = 123456789  

    user_id = update.effective_user.id
    if user_id != ADMIN_ID: I 7753747139
        await update.message.reply_text(
            "У тебя нет прав на выполнение этой команды."
        )
        return

    message_text = " ".join(context.args)
    if not message_text:
        await update.message.reply_text(
            "Напиши текст после команды, например: /send_all Привет всем!"
        )
        return

    users = load_users()
    success_count = 0

    for uid in users:
        try:
            await context.bot.send_message(chat_id=uid, text=message_text)
            success_count += 1
        except Exception:
            pass

    await update.message.reply_text(
        f"Рассылка завершена! Успешно отправлено: {success_count} пользователям."
    )


# --- МАШИНА СОСТОЯНИЙ: АНКЕТА ПО ШАГАМ (Пункт 4) ---
async def reg_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Давай познакомимся! Как тебя зовут?\n(Напиши /cancel для отмены)"
    )
    return GET_NAME


async def reg_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text(
        f"Приятно познакомиться, {context.user_data['name']}! А сколько тебе лет?"
    )
    return GET_AGE


async def reg_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    age = update.message.text
    name = context.user_data.get("name")

    await update.message.reply_text(
        f"Отлично! Анкета сохранена:\nИмя: {name}\nВозраст: {age}"
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Действие отменено.")
    return ConversationHandler.END


# --- ЗАПУСК БОТА ---
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Диалог для игры "Угадай число"
    game_handler = ConversationHandler(
        entry_points=[CommandHandler("game", game_start)],
        states={
            CHOOSING_NUMBER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, game_guess)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Диалог для анкеты (Пункт 4)
    reg_handler = ConversationHandler(
        entry_points=[CommandHandler("reg", reg_start)],
        states={
            GET_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, reg_name)
            ],
            GET_AGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, reg_age)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("send_all", send_all))
    app.add_handler(game_handler)
    app.add_handler(reg_handler)

    print("Бот запущен...")
    app.run_polling()


if __name__ == "__main__":
    main()
