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

CHOOSING_NUMBER = 1

# --- Работа с базой ---
def load_data():
    if not os.path.exists(DB_FILE): 
        return {"users": {}}
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Очищаем старые рекорды с попытками, если они остались
            if "records" in data: 
                del data["records"]
            return data
    except:
        return {"users": {}}

def save_data(data):
    with open(DB_FILE, "w", encoding="utf-8") as f: 
        json.dump(data, f, indent=4)

# --- Клавиатура (Инлайн-кнопки под сообщением) ---
def get_main_menu():
    keyboard = [
        [InlineKeyboardButton("🎲 Играть", callback_data="play")],
        [InlineKeyboardButton("👤 Профиль", callback_data="profile"), 
         InlineKeyboardButton("🏆 Рекорды", callback_data="records")],
        [InlineKeyboardButton("🆘 Помощь", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back")]])

# --- Основные команды ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    user = update.effective_user
    uid = str(user.id)
    if uid not in data["users"]:
        data["users"][uid] = {"name": user.first_name, "balance": 0}
        save_data(data)
    
    text = "👋 Привет! Добро пожаловать в игру «Угадай число»."
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.edit_text(text, reply_markup=get_main_menu())
    else:
        await update.message.reply_text(text, reply_markup=get_main_menu())
    return ConversationHandler.END

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    data = load_data()
    uid = str(update.effective_user.id)
    user = data["users"].get(uid, {"name": "Неизвестно", "balance": 0})
    
    text = f"👤 **{user['name']}**\n💰 Баланс: {user['balance']} монет"
    await update.callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=get_back_button())

async def records(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    data = load_data()
    
    # Сортируем пользователей по балансу (от большего к меньшему)
    users_list = list(data["users"].values())
    top_users = sorted(users_list, key=lambda x: x.get("balance", 0), reverse=True)[:5]
    
    if not top_users or top_users[0].get("balance", 0) == 0:
        text = "Пока никто не заработал монет. Стань первым!"
    else:
        text = "🏆 **ТОП-5 богачей:**\n\n"
        for i, u in enumerate(top_users):
            text += f"{i+1}. {u['name']} — {u['balance']} монет\n"
            
    await update.callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=get_back_button())

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    text = "🆘 **Как играть:**\nЯ загадываю число от 1 до 100. Ты пишешь свои варианты прямо в чат, а я подсказываю (больше или меньше).\nУгадал — получаешь 10 монет!"
    await update.callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=get_back_button())

# --- Механика игры ---
async def game_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    context.user_data["secret"] = random.randint(1, 100)
    
    text = "🎲 Я загадал число от 1 до 100.\nПиши ответ прямо в чат (или напиши /cancel для отмены):"
    await update.callback_query.message.edit_text(text)
    return CHOOSING_NUMBER

async def game_guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    try:
        guess = int(text)
    except ValueError:
        await update.message.reply_text("⚠️ Напиши число цифрами!")
        return CHOOSING_NUMBER

    secret = context.user_data["secret"]
    
    if guess == secret:
        data = load_data()
        uid = str(update.effective_user.id)
        data["users"][uid]["balance"] += 10
        save_data(data)
        
        await update.message.reply_text(
            f"🎉 Угадал! Мое число: {secret}.\nТвоя награда: +10 монет.",
            reply_markup=get_main_menu()
        )
        return ConversationHandler.END
    
    hint = "📈 Мое число больше!" if guess < secret else "📉 Мое число меньше!"
    await update.message.reply_text(hint)
    return CHOOSING_NUMBER

async def cancel_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Игра отменена.")
    await start(update, context)
    return ConversationHandler.END

# --- Рассылка (Только для Админа) ---
async def send_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: 
        return
    
    msg = " ".join(context.args)
    if not msg:
        await update.message.reply_text("Напиши текст: /send_all Текст рассылки")
        return
        
    data = load_data()
    count = 0
    for uid in data["users"]:
        try: 
            await context.bot.send_message(chat_id=uid, text=msg)
            count += 1
        except: 
            pass
    await update.message.reply_text(f"✅ Рассылка отправлена {count} людям.")

# --- Запуск ---
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    
    # Обработчик игры
    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(game_start, pattern="^play$")],
        states={CHOOSING_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, game_guess)]},
        fallbacks=[CommandHandler("cancel", cancel_game)]
    )
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("send_all", send_all))
    
    # Обработчики кнопок меню
    app.add_handler(CallbackQueryHandler(profile, pattern="^profile$"))
    app.add_handler(CallbackQueryHandler(records, pattern="^records$"))
    app.add_handler(CallbackQueryHandler(help_cmd, pattern="^help$"))
    app.add_handler(CallbackQueryHandler(start, pattern="^back$"))
    
    app.add_handler(conv)
    app.run_polling()

if __name__ == "__main__":
    main()
  
