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

TOKEN = os.getenv("TOKEN")
USERS_FILE = "users.json"
ADMIN_ID = 7753747139

GET_NAME, GET_AGE, CHOOSING_NUMBER = range(3)

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except:
                return []
    return []

def save_user(user_id):
    users = load_users()
    if user_id not in users:
        users.append(user_id)
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user(update.effective_user.id)
    await update.message.reply_text("Привет! Команды: /game, /reg")

async def game_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["secret_number"] = random.randint(1, 10)
    await update.message.reply_text("Угадай число от 1 до 10:")
    return CHOOSING_NUMBER

async def game_guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        guess = int(update.message.text)
    except:
        return CHOOSING_NUMBER
    if guess == context.user_data["secret_number"]:
        await update.message.reply_text("Угадал!")
        return ConversationHandler.END
    await update.message.reply_text("Неверно, попробуй еще:")
    return CHOOSING_NUMBER

async def send_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    text = " ".join(context.args)
    for uid in load_users():
        try: await context.bot.send_message(chat_id=uid, text=text)
        except: pass

async def reg_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Как тебя зовут?")
    return GET_NAME

async def reg_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("Сколько лет?")
    return GET_AGE

async def reg_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Записал: {context.user_data['name']}, {update.message.text} лет.")
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    
    conv_game = ConversationHandler(
        entry_points=[CommandHandler("game", game_start)],
        states={CHOOSING_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, game_guess)]},
        fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)]
    )
    
    conv_reg = ConversationHandler(
        entry_points=[CommandHandler("reg", reg_start)],
        states={GET_NAME: [MessageHandler(filters.TEXT, reg_name)], GET_AGE: [MessageHandler(filters.TEXT, reg_age)]},
        fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("send_all", send_all))
    app.add_handler(conv_game)
    app.add_handler(conv_reg)
    app.run_polling()

if __name__ == "__main__":
    main()
      
