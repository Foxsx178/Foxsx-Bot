import os
import json
import random
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, BotCommand
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, 
    ContextTypes, ConversationHandler, filters
)

TOKEN = os.getenv("TOKEN")
ADMIN_ID = 7753747139
DB_FILE = "data.json"

CHOOSING_NUMBER = 1

# --- Работа с базой данных ---
def load_data():
    if not os.path.exists(DB_FILE): 
        return {"users": {}}
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "records" in data: 
                del data["records"]
            return data
    except:
        return {"users": {}}

def save_data(data):
    with open(DB_FILE, "w", encoding="utf-8") as f: 
        json.dump(data, f, indent=4)

# --- Настройка синего меню (в левом нижнем углу) ---
async def setup_menu(application):
    commands = [
        BotCommand("start", "Запустить игру и меню"),
        BotCommand("help", "Правила игры"),
        BotCommand("shop", "Магазин статусов"),
        BotCommand("daily", "Ежедневный бонус"),
        BotCommand("hide", "Скрыть панель")
    ]
    await application.bot.set_my_commands(commands)

# --- Клавиатура внизу экрана ---
def get_main_menu():
    return ReplyKeyboardMarkup(
        [["🎮 Играть", "👤 Профиль"], 
         ["🏆 Рекорды", "🛍 Магазин"],
         ["🎁 Бонус", "🙈 Скрыть панель"]],
        resize_keyboard=True,
        is_persistent=True
    )

# --- Команды: Старт, Помощь, Скрытие ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    user = update.effective_user
    uid = str(user.id)
    
    if uid not in data["users"]:
        data["users"][uid] = {
            "name": user.first_name, 
            "balance": 0, 
            "title": "Новичок", 
            "last_daily": "2000-01-01"
        }
        save_data(data)
    
    await update.message.reply_text(
        "👋 Привет! Добро пожаловать в игру «Угадай число».\nИспользуй меню кнопок внизу экрана 👇", 
        reply_markup=get_main_menu()
    )
    return ConversationHandler.END

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🆘 **Как играть:**\n"
        "Я загадываю число от 1 до 100. Ты пишешь свои варианты прямо в чат, а я подсказываю (больше или меньше).\n"
        "Угадал — получаешь **10 монет**!\n\n"
        "🎁 Используй кнопку **Бонус**, чтобы получать монеты каждый день.\n"
        "🛍 В **Магазине** можно купить крутые звания в профиль."
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def hide_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🙈 Панель кнопок скрыта.\nЧтобы вернуть её обратно, отправь команду /start", 
        reply_markup=ReplyKeyboardRemove()
    )

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    uid = str(update.effective_user.id)
    
    if uid not in data["users"]:
        data["users"][uid] = {
            "name": update.effective_user.first_name, 
            "balance": 0, 
            "title": "Новичок",
            "last_daily": "2000-01-01"
        }
        save_data(data)
        
    user = data["users"][uid]
    title = user.get("title", "Новичок")
    
    text = f"👤 **Профиль: {user['name']}**\n🏆 Звание: {title}\n💰 Баланс: {user['balance']} монет"
    await update.message.reply_text(text, parse_mode="Markdown")

async def records(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    users_list = list(data["users"].values())
    top_users = sorted(users_list, key=lambda x: x.get("balance", 0), reverse=True)[:5]
    
    if not top_users or top_users[0].get("balance", 0) == 0:
        await update.message.reply_text("Пока никто не заработал монет. Стань первым!")
        return
        
    text = "🏆 **ТОП-5 богачей:**\n\n"
    for i, u in enumerate(top_users):
        text += f"{i+1}. {u['name']} — {u['balance']} монет ({u.get('title', 'Новичок')})\n"
            
    await update.message.reply_text(text, parse_mode="Markdown")

# --- Ежедневный бонус ---
async def daily_bonus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    uid = str(update.effective_user.id)
    
    if uid not in data["users"]:
        data["users"][uid] = {
            "name": update.effective_user.first_name, 
            "balance": 0, 
            "title": "Новичок",
            "last_daily": "2000-01-01"
        }
    
    user = data["users"][uid]
    last_date_str = user.get("last_daily", "2000-01-01")
    last_date = datetime.strptime(last_date_str, "%Y-%m-%d")
    now = datetime.now()
    
    # Проверка прошли ли сутки
    if now - last_date < timedelta(days=1):
        left_time = timedelta(days=1) - (now - last_date)
        hours = left_time.seconds // 3600
        minutes = (left_time.seconds % 3600) // 60
        await update.message.reply_text(f"⏳ Ты уже забирал бонус сегодня!\nСледующий бонус будет доступен через {hours} ч. {minutes} мин.")
        return
        
    user["balance"] += 25
    user["last_daily"] = now.strftime("%Y-%m-%d")
    save_data(data)
    
    await update.message.reply_text("🎁 Ты успешно забрал ежедневный бонус!\n💰 На твой баланс зачислено: **+25 монет**.", parse_mode="Markdown")

# --- Магазин статусов ---
ITEMS = {
    "1": {"name": "⚡ Профи", "price": 50},
    "2": {"name": "🔥 Элита", "price": 150},
    "3": {"name": "👑 Легенда", "price": 300},
    "4": {"name": "💻 Сын маминой подруги", "price": 600}
}

async def shop_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🛍 **Магазин званий:**\n"
        "Купи крутой статус, который будет виден в твоем профиле и топе!\n\n"
        "1️⃣ **⚡ Профи** — 50 монет\n"
        "2️⃣ **🔥 Элита** — 150 монет\n"
        "3️⃣ **👑 Легенда** — 300 монет\n"
        "4️⃣ **💻 Сын маминой подруги** — 600 монет\n\n"
        "👉 Чтобы купить, напиши команду в формате: `/buy номер`\n"
        "*(Например: `/buy 1`)*"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def buy_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Укажи номер товара. Пример: `/buy 1`", parse_mode="Markdown")
        return
        
    item_id = context.args[0]
    if item_id not in ITEMS:
        await update.message.reply_text("❌ Такого товара не существует. Посмотри список в Магазине.")
        return
        
    item = ITEMS[item_id]
    data = load_data()
    uid = str(update.effective_user.id)
    
    if uid not in data["users"]:
        data["users"][uid] = {
            "name": update.effective_user.first_name, 
            "balance": 0, 
            "title": "Новичок",
            "last_daily": "2000-01-01"
        }
        
    user = data["users"][uid]
    
    if user["balance"] < item["price"]:
        await update.message.reply_text(f"❌ Не хватает монет! У тебя {user['balance']} монет, а нужно {item['price']}.")
        return
        
    user["balance"] -= item["price"]
    user["title"] = item["name"]
    save_data(data)
    
    await update.message.reply_text(f"🎉 Поздравляю с покупкой!\nТеперь твое звание: **{item['name']}**.", parse_mode="Markdown")

# --- Механика игры ---
async def game_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["secret"] = random.randint(1, 100)
    await update.message.reply_text("🎲 Я загадал число от 1 до 100.\nПиши ответ прямо в чат (или напиши /cancel для отмены):")
    return CHOOSING_NUMBER

async def game_guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    menu_buttons = ["🎮 Играть", "👤 Профиль", "🏆 Рекорды", "🛍 Магазин", "🎁 Бонус", "🙈 Скрыть панель"]
    if text in menu_buttons:
        await update.message.reply_text("⚠️ Сначала закончи текущую игру (угадай число или напиши /cancel).")
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
        
        if uid not in data["users"]:
            data["users"][uid] = {
                "name": update.effective_user.first_name, 
                "balance": 0, 
                "title": "Новичок",
                "last_daily": "2000-01-01"
            }
            
        data["users"][uid]["balance"] += 10
        save_data(data)
        
        await update.message.reply_text(
            f"🎉 Угадал! Мое число было {secret}.\n💰 Твоя награда: +10 монет.",
            reply_markup=get_main_menu()
        )
        return ConversationHandler.END
    
    hint = "📈 Мое число больше!" if guess < secret else "📉 Мое число меньше!"
    await update.message.reply_text(hint)
    return CHOOSING_NUMBER

async def cancel_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Игра отменена.", reply_markup=get_main_menu())
    return ConversationHandler.END

# --- Скрытая рассылка (Только для Админа) ---
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

# --- Главная функция запуска ---
def main():
    app = ApplicationBuilder().token(TOKEN).post_init(setup_menu).build()
    
    conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🎮 Играть$"), game_start)],
        states={CHOOSING_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, game_guess)]},
        fallbacks=[CommandHandler("cancel", cancel_game)]
    )
    
    # Команды со слэшем
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("shop", shop_menu))
    app.add_handler(CommandHandler("daily", daily_bonus))
    app.add_handler(CommandHandler("hide", hide_panel))
    app.add_handler(CommandHandler("buy", buy_item))
    app.add_handler(CommandHandler("send_all", send_all)) # Скрыта от общего меню, но работает для тебя
    
    # Кнопки нижнего меню
    app.add_handler(MessageHandler(filters.Regex("^👤 Профиль$"), profile))
    app.add_handler(MessageHandler(filters.Regex("^🏆 Рекорды$"), records))
    app.add_handler(MessageHandler(filters.Regex("^🛍 Магазин$"), shop_menu))
    app.add_handler(MessageHandler(filters.Regex("^🎁 Бонус$"), daily_bonus))
    app.add_handler(MessageHandler(filters.Regex("^🙈 Скрыть панель$"), hide_panel))
    
    app.add_handler(conv)
    app.run_polling()

if __name__ == "__main__":
    main()
