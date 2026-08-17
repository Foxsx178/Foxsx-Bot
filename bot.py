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
        return {"users": {}, "promos": {}}
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "records" in data: 
                del data["records"]
            if "promos" not in data:
                data["promos"] = {}
            return data
    except:
        return {"users": {}, "promos": {}}

def save_data(data):
    with open(DB_FILE, "w", encoding="utf-8") as f: 
        json.dump(data, f, indent=4)

# --- Настройка синего меню ---
async def setup_menu(application):
    commands = [
        BotCommand("start", "Запустить игру и меню"),
        BotCommand("help", "Правила игры"),
        BotCommand("shop", "Магазин званий"),
        BotCommand("daily", "Ежедневный бонус"),
        BotCommand("casino", "Сыграть в казино"),
        BotCommand("hide", "Скрыть панель")
    ]
    await application.bot.set_my_commands(commands)

# --- Клавиатура внизу экрана ---
def get_main_menu():
    return ReplyKeyboardMarkup(
        [["🎮 Играть", "🎰 Казино"], 
         ["👤 Профиль", "🛍 Магазин"],
         ["🏆 Рекорды", "🎁 Бонус"],
         ["🙈 Скрыть панель"]],
        resize_keyboard=True,
        is_persistent=True
    )

# --- Базовые команды ---
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
        "👋 Привет! Добро пожаловать в игру.\nИспользуй меню кнопок внизу экрана 👇", 
        reply_markup=get_main_menu()
    )
    return ConversationHandler.END

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🆘 **Как играть и что делать:**\n\n"
        "🎲 **Угадай число**: Жми «Играть» и угадывай число от 1 до 100 (+10 монет).\n"
        "🎰 **Казино**: Нажми кнопку «Казино» или пиши `/casino [ставка]`.\n"
        "🎁 **Бонус**: Жми «Бонус» раз в сутки (+25 монет).\n"
        "🛍 **Магазин**: Покупай крутые звания через `/shop`.\n"
        "🎟 **Промокоды**: Вводи `/promo [код]` для получения халявы."
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
    
    if now - last_date < timedelta(days=1):
        left_time = timedelta(days=1) - (now - last_date)
        hours = left_time.seconds // 3600
        minutes = (left_time.seconds % 3600) // 60
        await update.message.reply_text(f"⏳ Ты уже забирал бонус сегодня!\nПриходи через {hours} ч. {minutes} мин.")
        return
        
    user["balance"] += 25
    user["last_daily"] = now.strftime("%Y-%m-%d")
    save_data(data)
    
    await update.message.reply_text("🎁 Ежедневный бонус получен!\n💰 Начислено: **+25 монет**.", parse_mode="Markdown")

# --- Магазин статусов ---
ITEMS = {
    "1": {"name": "⚡ Профи", "price": 50},
    "2": {"name": "🔥 Элита", "price": 150},
    "3": {"name": "👑 Легенда", "price": 300},
    "4": {"name": "💻 Сын маминой подруги", "price": 600},
    "5": {"name": "🗿 Гигачад", "price": 1000},
    "6": {"name": "🤡 Главный клоун", "price": 200},
    "7": {"name": "🤑 Криптоинвестор", "price": 777},
    "8": {"name": "🥷 Теневой самурай", "price": 500}
}

async def shop_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🛍 **Магазин званий:**\n"
        "Выбери статус, который будет виден в твоем профиле и топе:\n\n"
        "1️⃣ **⚡ Профи** — 50 монет\n"
        "2️⃣ **🔥 Элита** — 150 монет\n"
        "3️⃣ **👑 Легенда** — 300 монет\n"
        "4️⃣ **💻 Сын маминой подруги** — 600 монет\n"
        "5️⃣ **🗿 Гигачад** — 1000 монет\n"
        "6️⃣ **🤡 Главный клоун** — 200 монет\n"
        "7️⃣ **🤑 Криптоинвестор** — 777 монет\n"
        "8️⃣ **🥷 Теневой самурай** — 500 монет\n\n"
        "👉 Купить: `/buy [номер]` (например: `/buy 4`)"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def buy_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Укажи номер товара. Пример: `/buy 1`", parse_mode="Markdown")
        return
        
    item_id = context.args[0]
    if item_id not in ITEMS:
        await update.message.reply_text("❌ Такого товара нет в магазине.")
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
        await update.message.reply_text(f"❌ Не хватает монет! У тебя {user['balance']}, а нужно {item['price']}.")
        return
        
    user["balance"] -= item["price"]
    user["title"] = item["name"]
    save_data(data)
    
    await update.message.reply_text(f"🎉 Успешная покупка!\nНовое звание: **{item['name']}**.", parse_mode="Markdown")

# --- Казино ---
async def casino_play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Если нажали кнопку в меню без указания ставки, кидаем подсказку или дефолтную ставку
    if not context.args:
        await update.message.reply_text("🎰 Чтобы сыграть в казино, укажи ставку.\nПример: `/casino 50`", parse_mode="Markdown")
        return
        
    try:
        bet = int(context.args[0])
    except ValueError:
        await update.message.reply_text("⚠️ Ставка должна быть числом! Пример: `/casino 50`")
        return
        
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
    
    if bet <= 0:
        await update.message.reply_text("❌ Ставка должна быть больше нуля!")
        return
        
    if user["balance"] < bet:
        await update.message.reply_text(f"❌ У тебя недостаточно монет! На балансе: {user['balance']} монет.")
        return
        
    user["balance"] -= bet
    
    symbols = ["🍒", "🍋", "🔔", "💎", "7️⃣"]
    res1 = random.choice(symbols)
    res2 = random.choice(symbols)
    res3 = random.choice(symbols)
    
    slot_result = f"[{res1} | {res2} | {res3}]"
    
    if res1 == res2 == res3:
        if res1 == "7️⃣":
            win = bet * 10
            user["balance"] += win
            msg = f"🎰 {slot_result}\n🎉 ДЖЕКПОТ! Ставка умножена на 10!\n💰 Выигрыш: **+{win} монет**"
        else:
            win = bet * 3
            user["balance"] += win
            msg = f"🎰 {slot_result}\n✨ Отлично! Все символы совпали!\n💰 Выигрыш: **+{win} монет**"
    elif res1 == res2 or res2 == res3 or res1 == res3:
        win = int(bet * 1.5)
        user["balance"] += win
        msg = f"🎰 {slot_result}\n👍 Почти джекпот (2 совпадения).\n💰 Выигрыш: **+{win} монет**"
    else:
        msg = f"🎰 {slot_result}\n😢 К сожалению, ты проиграл ставку ({bet} монет)."
        
    save_data(data)
    await update.message.reply_text(msg, parse_mode="Markdown")

# --- Система промокодов (Создание админом: /add_promo КОД СУММА) ---
async def create_promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
        
    if len(context.args) < 2:
        await update.message.reply_text("Формат: `/add_promo [код] [сумма]`", parse_mode="Markdown")
        return
        
    code = context.args[0].upper()
    try:
        amount = int(context.args[1])
    except ValueError:
        await update.message.reply_text("Сумма должна быть числом!")
        return
        
    data = load_data()
    data["promos"][code] = {"amount": amount, "used": []}
    save_data(data)
    
    await update.message.reply_text(f"✅ Промокод **{code}** на **{amount} монет** успешно создан!", parse_mode="Markdown")

# --- Активация промокода игроком: /promo КОД ---
async def use_promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Введи промокод. Пример: `/promo START`", parse_mode="Markdown")
        return
        
    code = context.args[0].upper()
    data = load_data()
    uid = str(update.effective_user.id)
    
    if uid not in data["users"]:
        data["users"][uid] = {
            "name": update.effective_user.first_name, 
            "balance": 0, 
            "title": "Новичок",
            "last_daily": "2000-01-01"
        }
        
    if code not in data["promos"]:
        await update.message.reply_text("❌ Такого промокода не существует.")
        return
        
    promo = data["promos"][code]
    
    if uid in promo["used"]:
        await update.message.reply_text("⚠️ Ты уже активировал этот промокод раньше!")
        return
        
    amount = promo["amount"]
    data["users"][uid]["balance"] += amount
    promo["used"].append(uid)
    save_data(data)
    
    await update.message.reply_text(f"🎁 Промокод активирован!\n💰 Тебе зачислено: **+{amount} монет**.", parse_mode="Markdown")

# --- Игра «Угадай число» ---
async def game_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["secret"] = random.randint(1, 100)
    await update.message.reply_text("🎲 Я загадал число от 1 до 100.\nПиши ответ прямо в чат (или напиши /cancel для отмены):")
    return CHOOSING_NUMBER

async def game_guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    menu_buttons = ["🎮 Играть", "🎰 Казино", "👤 Профиль", "🛍 Магазин", "🏆 Рекорды", "🎁 Бонус", "🙈 Скрыть панель"]
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

# --- Скрытая рассылка ---
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

# --- Главная функция ---
def main():
    app = ApplicationBuilder().token(TOKEN).post_init(setup_menu).build()
    
    conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🎮 Играть$"), game_start)],
        states={CHOOSING_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, game_guess)]},
        fallbacks=[CommandHandler("cancel", cancel_game)]
    )
    
    # Команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("shop", shop_menu))
    app.add_handler(CommandHandler("daily", daily_bonus))
    app.add_handler(CommandHandler("casino", casino_play))
    app.add_handler(CommandHandler("promo", use_promo))
    app.add_handler(CommandHandler("hide", hide_panel))
    app.add_handler(CommandHandler("buy", buy_item))
    
    # Админские команды
    app.add_handler(CommandHandler("send_all", send_all))
    app.add_handler(CommandHandler("add_promo", create_promo))
    
    # Кнопки нижнего меню
    app.add_handler(MessageHandler(filters.Regex("^👤 Профиль$"), profile))
    app.add_handler(MessageHandler(filters.Regex("^🎰 Казино$"), casino_play))
    app.add_handler(MessageHandler(filters.Regex("^🏆 Рекорды$"), records))
    app.add_handler(MessageHandler(filters.Regex("^🛍 Магазин$"), shop_menu))
    app.add_handler(MessageHandler(filters.Regex("^🎁 Бонус$"), daily_bonus))
    app.add_handler(MessageHandler(filters.Regex("^🙈 Скрыть панель$"), hide_panel))
    
    app.add_handler(conv)
    app.run_polling()

if __name__ == "__main__":
    main()
