import os
import json
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler, 
    MessageHandler, ContextTypes, ConversationHandler, filters
)

TOKEN = os.getenv("TOKEN")
ADMIN_ID = 7753747139
DB_FILE = "data.json"

# --- Работа с базой ---
def load_data():
    if not os.path.exists(DB_FILE): return {"users": {}, "records": []}
    with open(DB_FILE, "r", encoding="utf-8") as f: return json.load(f)

def save_data(data):
    with open(DB_FILE, "w", encoding="utf-8") as f: json.dump(data, f, indent=4)

# --- Игровые функции ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    uid = str(update.effective_user.id)
    if uid not in data["users"]:
        data["users"][uid] = {"name": update.effective_user.first_name, "balance": 0}
        save_data(data)
    
    keyboard = [
        [InlineKeyboardButton("🎲 Играть (1-100)", callback_data="play")],
        [InlineKeyboardButton("👤 Профиль", callback_data="profile"), InlineKeyboardButton("🏆 Рекорды", callback_data="records")],
        [InlineKeyboardButton("🆘 Помощь", callback_data="help")]
    ]
    await update.message.reply_text("👋 Привет! Добро пожаловать в игру.", reply_markup=InlineKeyboardMarkup(keyboard))

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    user = data["users"].get(str(update.effective_user.id))
    await update.callback_query.message.edit_text(f"👤 **{user['name']}**\n💰 Баланс: {user['balance']} монет", parse_mode="Markdown")

async def records(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    recs = sorted(data["records"], key=lambda x: x["attempts"])[:5]
    text = "🏆 **ТОП-5 рекордов (попытки):**\n" + "\n".join([f"{i+1}. {r['name']} — {r['attempts']} ходов" for i, r in enumerate(recs)])
    await update.callback_query.message.edit_text(text, parse_mode="Markdown")

async def game_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.update({"secret": random.randint(1, 100), "attempts": 0})
    await update.callback_query.message.edit_text("🎲 Загадал число от 1 до 100. Пиши ответ:")
    return 1

async def game_guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    guess = int(update.message.text)
    context.user_data["attempts"] += 1
    secret = context.user_data["secret"]
    
    if guess == secret:
        data = load_data()
        uid = str(update.effective_user.id)
        data["users"][uid]["balance"] += 10
        data["records"].append({"name": data["users"][uid]["name"], "attempts": context.user_data["attempts"]})
        save_data(data)
        await update.message.reply_text(f"🎉 Угадал! +10 монет. Всего попыток: {context.user_data['attempts']}")
        return ConversationHandler.END
    
    hint = "📈 Больше!" if guess < secret else "📉 Меньше!"
    await update.message.reply_text(f"{hint} (Попытка {context.user_data['attempts']})")
    return 1

# --- Рассылка (пишется: /send_all текст) ---
async def send_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    msg = " ".join(context.args)
    data = load_data()
    for uid in data["users"]:
        try: await context.bot.send_message(chat_id=uid, text=msg)
        except: pass
    await update.message.reply_text("✅ Рассылка завершена.")

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    
    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(game_start, pattern="play")],
        states={1: [MessageHandler(filters.TEXT & ~filters.COMMAND, game_guess)]},
        fallbacks=[CommandHandler("cancel", start)]
    )
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("send_all", send_all))
    app.add_handler(CallbackQueryHandler(profile, pattern="profile"))
    app.add_handler(CallbackQueryHandler(records, pattern="records"))
    app.add_handler(conv)
    app.run_polling()

if __name__ == "__main__":
    main()
