import os
import json
import random
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, 
    ContextTypes, ConversationHandler, filters
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
            # Удаляем старый формат рекордов (с попытками), если он остался в файле
            if "records" in data: 
                del data["records"]
            return data
    except:
        return {"users": {}}

def save_data(data):
    with open(DB_FILE, "w", encoding="utf-8") as f: 
        json.dump(data, f, indent=4)

# --- Клавиатура (Меню внизу экрана) ---
def get_main_menu():
    return ReplyKeyboardMarkup(
        [["🎮 Играть", "👤 Профиль"], 
         ["🏆 Рекорды", "🆘 Помощь"]],
        resize_keyboard=True, # Подстраивает размер кнопок
        is_persistent=True    # Меню не пропадает
    )

# --- Основные команды ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    user = update.effective_user
    uid = str(user.id)
    if uid not in data["users"]:
        data["users"][uid] = {"name": user.first_name, "balance": 0}
        save_data(data)
    
    await update.message.reply_text(
        "👋 Привет! Добро пожаловать в игру «Угадай число».\nИспользуй меню кнопок внизу экрана 👇", 
        reply_markup=get_main_menu()
    )
    return ConversationHandler.END

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    uid = str(update.effective_user.id)
    user = data["users"].get(uid, {"name": "Неизвестно", "balance": 0})
    
    text = f"👤 **{user['name']}**\n💰 Баланс: {user['balance']} монет"
    await update.message.reply_text(text, parse_mode="Markdown")

async def records(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    
    # Сортируем пользователей по количеству монет (от большего к меньшему)
    users_list = list(data["users"].values())
    top_users = sorted(users_list, key=lambda x: x.get("balance", 0), reverse=True)[:5]
    
    if not top_users or top_users[0].get("balance", 0) == 0:
        await update.message.reply_text("Пока никто не заработал монет. Стань первым!")
        return
        
    text = "🏆 **ТОП-5 богачей:**\n\n"
    for i, u in enumerate(top_users):
        text += f"{i+1}. {u['name']} — {u['balance']} монет\n"
            
    await update.message.reply_text(text, parse_mode="Markdown")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "🆘 **Как играть:**\nЯ загадываю число от 1 до 100. Ты пишешь свои варианты прямо в чат, а я подсказываю (больше или меньше).\nУгадал — получаешь 10 монет!"
    await update.message.reply_text(text, parse_mode="Markdown")

# --- Механика игры ---
async def game_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["secret"] = random.randint(1, 100)
    await update.message.reply_text("🎲 Я загадал число от 1 до 100.\nПиши ответ прямо в чат (или напиши /cancel для отмены):")
    return CHOOSING_NUMBER

async def game_guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    # Защита: если во время игры случайно нажали кнопку из меню
    if text in ["🎮 Играть", "👤 Профиль", "🏆 Рекорды", "🆘 Помощь"]:
        await update.message.reply_text("⚠️ Сначала закончи игру (угадай число или напиши /cancel).")
        return CHOOSING_NUMBER

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
        
        await update.message.reply_text(f"🎉 Угадал! Мое число: {secret}.\nТвоя награда: +10 монет.")
        return ConversationHandler.END
    
    hint = "📈 Мое число больше!" if guess < secret else "📉 Мое число меньше!"
    await update.message.reply_text(hint)
    return CHOOSING_NUMBER

async def cancel_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Игра отменена.", reply_markup=get_main_menu())
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
    await update.message.reply_text(f"✅ Рассылка отправлена {count} пользователям.")

# --- Запуск ---
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    
    # Обработчик игры
    conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🎮 Играть$"), game_start)],
        states={CHOOSING_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, game_guess)]},
        fallbacks=[CommandHandler("cancel", cancel_game)]
    )
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("send_all", send_all))
    
    # Обработчики обычных кнопок
    app.add_handler(MessageHandler(filters.Regex("^👤 Профиль$"), profile))
    app.add_handler(MessageHandler(filters.Regex("^🏆 Рекорды$"), records))
    app.add_handler(MessageHandler(filters.Regex("^🆘 Помощь$"), help_cmd))
    
    app.add_handler(conv)
    app.run_polling()

if __name__ == "__main__":
    main()
