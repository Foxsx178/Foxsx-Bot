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
        return {"users": {}, "records": []}
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f: 
            return json.load(f)
    except json.JSONDecodeError:
        return {"users": {}, "records": []}

def save_data(data):
    with open(DB_FILE, "w", encoding="utf-8") as f: 
        json.dump(data, f, indent=4)

# --- Клавиатура (Меню кнопок внизу) ---
def get_menu_keyboard():
    # Создаем кнопки, которые будут постоянно висеть внизу экрана
    return ReplyKeyboardMarkup(
        [["🎮 Играть", "👤 Профиль"], ["🏆 Рекорды", "🆘 Помощь"]],
        resize_keyboard=True
    )

# --- Основные команды ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    uid = str(update.effective_user.id)
    if uid not in data["users"]:
        data["users"][uid] = {"name": update.effective_user.first_name, "balance": 0}
        save_data(data)
    
    await update.message.reply_text(
        "👋 Привет! Добро пожаловать в игру «Угадай число».\nВоспользуйся меню кнопок внизу:", 
        reply_markup=get_menu_keyboard()
    )
    return ConversationHandler.END

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    uid = str(update.effective_user.id)
    if uid not in data["users"]:
        data["users"][uid] = {"name": update.effective_user.first_name, "balance": 0}
        save_data(data)
        
    user = data["users"][uid]
    await update.message.reply_text(f"👤 **{user['name']}**\n💰 Баланс: {user['balance']} монет", parse_mode="Markdown")

async def records(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    recs = sorted(data["records"], key=lambda x: x["attempts"])[:5] # Топ 5 (где меньше попыток)
    
    if not recs:
        await update.message.reply_text("Пока нет рекордов. Стань первым!")
        return
    
    text = "🏆 **ТОП-5 рекордов:**\n" + "\n".join([f"{i+1}. {r['name']} — {r['attempts']} ходов" for i, r in enumerate(recs)])
    await update.message.reply_text(text, parse_mode="Markdown")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "🆘 **Как играть:**\nНажми '🎮 Играть', я загадаю число от 1 до 100. Пиши свои догадки, а я подскажу, больше мое число или меньше. За победу ты получаешь 10 монет!"
    await update.message.reply_text(text, parse_mode="Markdown")

# --- Механика игры ---
async def game_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["secret"] = random.randint(1, 100)
    context.user_data["attempts"] = 0
    await update.message.reply_text("🎲 Загадал число от 1 до 100.\nПиши ответ (или напиши /cancel для выхода):")
    return CHOOSING_NUMBER

async def game_guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    # Если во время игры человек нажал на кнопку из меню
    if text in ["🎮 Играть", "👤 Профиль", "🏆 Рекорды", "🆘 Помощь"]:
        await update.message.reply_text("⚠️ Сначала закончи игру (или напиши /cancel).")
        return CHOOSING_NUMBER

    try:
        guess = int(text)
    except ValueError:
        await update.message.reply_text("⚠️ Пожалуйста, напиши число цифрами!")
        return CHOOSING_NUMBER

    context.user_data["attempts"] += 1
    secret = context.user_data["secret"]
    attempts = context.user_data["attempts"]
    
    if guess == secret:
        data = load_data()
        uid = str(update.effective_user.id)
        data["users"][uid]["balance"] += 10
        data["records"].append({"name": data["users"][uid]["name"], "attempts": attempts})
        save_data(data)
        
        await update.message.reply_text(
            f"🎉 Угадал! Мое число: {secret}.\nТвоя награда: +10 монет.\nПотрачено попыток: {attempts}",
            reply_markup=get_menu_keyboard()
        )
        return ConversationHandler.END
    
    hint = "📈 Мое число больше!" if guess < secret else "📉 Мое число меньше!"
    await update.message.reply_text(f"{hint} (Попытка {attempts})")
    return CHOOSING_NUMBER

async def cancel_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Игра отменена.", reply_markup=get_menu_keyboard())
    return ConversationHandler.END

# --- Рассылка (Только для Админа) ---
async def send_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: 
        return
    
    msg = " ".join(context.args)
    if not msg:
        await update.message.reply_text("Напиши текст: /send_all Текст")
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
        entry_points=[MessageHandler(filters.Regex("^🎮 Играть$"), game_start)],
        states={CHOOSING_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, game_guess)]},
        fallbacks=[CommandHandler("cancel", cancel_game)]
    )
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("send_all", send_all))
    
    # Обработчики кнопок нижнего меню
    app.add_handler(MessageHandler(filters.Regex("^👤 Профиль$"), profile))
    app.add_handler(MessageHandler(filters.Regex("^🏆 Рекорды$"), records))
    app.add_handler(MessageHandler(filters.Regex("^🆘 Помощь$"), help_cmd))
    
    app.add_handler(conv)
    app.run_polling()

if __name__ == "__main__":
    main()
