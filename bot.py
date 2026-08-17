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

# --- Магазин предметов (Расширенный: титулы + разная фигня) ---
ITEMS = {
    # Титулы и статусы
    "1": {"name": "⚡ Профи", "icon": "⚡", "price": 50, "category": "Титул"},
    "2": {"name": "🔥 Элита", "icon": "🔥", "price": 150, "category": "Титул"},
    "3": {"name": "👑 Легенда", "icon": "👑", "price": 300, "category": "Титул"},
    "4": {"name": "💻 Сын маминой подруги", "icon": "💻", "price": 600, "category": "Титул"},
    "5": {"name": "🗿 Гигачад", "icon": "🗿", "price": 1000, "category": "Титул"},
    "6": {"name": "🤡 Главный клоун", "icon": "🤡", "price": 200, "category": "Титул"},
    "7": {"name": "🤑 Криптоинвестор", "icon": "🤑", "price": 777, "category": "Титул"},
    "8": {"name": "🥷 Теневой самурай", "icon": "🥷", "price": 500, "category": "Титул"},
    "9": {"name": "🐲 Повелитель драконов", "icon": "🐲", "price": 1500, "category": "Титул"},
    "10": {"name": "🤖 Кибернетический бог", "icon": "🤖", "price": 2500, "category": "Титул"},
    
    # Всякая фигня / Артефакты для кастомизации
    "11": {"name": "🧪 Секретный эликсир", "icon": "🧪", "price": 333, "category": "Артефакт"},
    "12": {"name": "🔮 Магический шар", "icon": "🔮", "price": 777, "category": "Артефакт"},
    "13": {"name": "🍕 Легендарная пицца", "icon": "🍕", "price": 250, "category": "Артефакт"},
    "14": {"name": "🕶 Крутые очки", "icon": "🕶", "price": 400, "category": "Артефакт"}
}

# --- Работа с базой данных ---
def load_data():
    if not os.path.exists(DB_FILE): 
        return {"users": {}, "promos": {}}
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "promos" not in data:
                data["promos"] = {}
            return data
    except:
        return {"users": {}, "promos": {}}

def save_data(data):
    with open(DB_FILE, "w", encoding="utf-8") as f: 
        json.dump(data, f, indent=4)

def ensure_user(data, user):
    uid = str(user.id)
    if uid not in data["users"]:
        data["users"][uid] = {
            "name": user.first_name, 
            "balance": 0, 
            "inventory": [], 
            "active_item": None,
            "last_daily": "2000-01-01"
        }
    return uid

# --- Настройка синего меню ---
async def setup_menu(application):
    commands = [
        BotCommand("start", "Запустить игру и меню"),
        BotCommand("help", "Правила игры"),
        BotCommand("shop", "Магазин предметов"),
        BotCommand("daily", "Ежедневный бонус"),
        BotCommand("casino", "Сыграть в казино"),
        BotCommand("rps", "Камень, ножницы, бумага"),
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
    ensure_user(data, update.effective_user)
    save_data(data)
    
    await update.message.reply_text(
        "👋 Привет! Добро пожаловать в игру.\nИспользуй меню кнопок внизу экрана 👇", 
        reply_markup=get_main_menu()
    )
    return ConversationHandler.END

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🆘 **Как играть и что делать:**\n\n"
        "🎲 **Угадай число**: Жми «Играть» и угадывай число (+10 монет).\n"
        "🎰 **Казино**: `/casino [ставка]`.\n"
        "✂️ **Камень, ножницы, бумага**: `/rps [камень/ножницы/бумага]` (награда за победу: +15 монет!)\n"
        "🎁 **Бонус**: Жми «Бонус» раз в сутки (+25 монет).\n"
        "🛍 **Магазин**: `/shop` — покупка титулов и артефактов.\n"
        "🎒 **Экипировка**: `/set [номер]` — надеть купленный предмет.\n"
        "🎟 **Промокоды**: Вводи `/promo [код]`."
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def hide_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🙈 Панель кнопок скрыта.\nЧтобы вернуть её обратно, отправь команду /start", 
        reply_markup=ReplyKeyboardRemove()
    )

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    uid = ensure_user(data, update.effective_user)
    user = data["users"][uid]
    
    active_id = user.get("active_item")
    item = ITEMS.get(active_id)
    
    icon = item["icon"] if item else "👤"
    title = item["name"] if item else "Новичок"
    
    text = (f"👤 **Профиль: {user['name']}**\n"
            f"🏅 Экипировано: {icon} {title}\n"
            f"💰 Баланс: {user['balance']} монет\n\n"
            f"🎒 Предметов в инвентаре: {len(user['inventory'])}")
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
        active_id = u.get("active_item")
        title = ITEMS[active_id]["name"] if active_id in ITEMS else "Новичок"
        text += f"{i+1}. {u['name']} — {u['balance']} монет ({title})\n"
            
    await update.message.reply_text(text, parse_mode="Markdown")

# --- Ежедневный бонус ---
async def daily_bonus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    uid = ensure_user(data, update.effective_user)
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

# --- Магазин и инвентарь ---
async def shop_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "🛍 **Магазин предметов и статусов:**\n\n"
    
    text += "📜 **— ТИТУЛЫ —**\n"
    for k, v in ITEMS.items():
        if v["category"] == "Титул":
            text += f"{k}️⃣ {v['icon']} {v['name']} — {v['price']} монет\n"
            
    text += "\n🔮 **— АРТЕФАКТЫ И ВЫХОДНЫЕ ВЕЩИ —**\n"
    for k, v in ITEMS.items():
        if v["category"] == "Артефакт":
            text += f"{k}️⃣ {v['icon']} {v['name']} — {v['price']} монет\n"
            
    text += "\n👉 Купить: `/buy [номер]`\n🎒 Надеть: `/set [номер]`"
    await update.message.reply_text(text, parse_mode="Markdown")

async def buy_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Укажи номер товара. Пример: `/buy 1`")
        return
        
    item_id = context.args[0]
    if item_id not in ITEMS:
        await update.message.reply_text("❌ Такого товара нет в магазине.")
        return
        
    item = ITEMS[item_id]
    data = load_data()
    uid = ensure_user(data, update.effective_user)
    user = data["users"][uid]
    
    if item_id in user["inventory"]:
        await update.message.reply_text("⚠️ У тебя уже есть этот предмет! Используй `/set [номер]`, чтобы надеть.")
        return
        
    if user["balance"] < item["price"]:
        await update.message.reply_text(f"❌ Не хватает монет! У тебя {user['balance']}, а нужно {item['price']}.")
        return
        
    user["balance"] -= item["price"]
    user["inventory"].append(item_id)
    save_data(data)
    
    await update.message.reply_text(f"🎉 Успешная покупка: **{item['name']}**!\nИспользуй `/set {item_id}`, чтобы надеть его.", parse_mode="Markdown")

async def set_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Укажи номер предмета из инвентаря. Пример: `/set 1`")
        return
        
    item_id = context.args[0]
    data = load_data()
    uid = ensure_user(data, update.effective_user)
    user = data["users"][uid]
    
    if item_id not in user["inventory"]:
        await update.message.reply_text("❌ У тебя нет этого предмета в инвентаре! Сначала купи его через `/shop`.")
        return
        
    user["active_item"] = item_id
    save_data(data)
    
    await update.message.reply_text(f"✅ Ты успешно надел: **{ITEMS[item_id]['name']}**!", parse_mode="Markdown")

# --- Казино ---
async def casino_play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("🎰 Чтобы сыграть в казино, укажи ставку.\nПример: `/casino 50`", parse_mode="Markdown")
        return
        
    try:
        bet = int(context.args[0])
    except ValueError:
        await update.message.reply_text("⚠️ Ставка должна быть числом! Пример: `/casino 50`")
        return
        
    data = load_data()
    uid = ensure_user(data, update.effective_user)
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

# --- Игра «Камень, Ножницы, Бумага» (С начислением денег за победу!) ---
async def rps_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("🎮 **Камень, Ножницы, Бумага**\nИспользуй: `/rps камень`, `/rps ножницы` или `/rps бумага`\n🏆 Награда за победу: **15 монет**", parse_mode="Markdown")
        return

    user_choice = context.args[0].lower()
    choices = ["камень", "ножницы", "бумага"]
    
    if user_choice not in choices:
        await update.message.reply_text("❌ Выбери правильно: камень, ножницы или бумага!")
        return

    bot_choice = random.choice(choices)
    
    data = load_data()
    uid = ensure_user(data, update.effective_user)
    user = data["users"][uid]
    
    reward = 15
    res = ""
    
    if user_choice == bot_choice:
        res = "🤝 Ничья! Никто ничего не выиграл."
    elif (user_choice == "камень" and bot_choice == "ножницы") or \
         (user_choice == "ножницы" and bot_choice == "бумага") or \
         (user_choice == "бумага" and bot_choice == "камень"):
        user["balance"] += reward
        save_data(data)
        res = f"🎉 Ты победил!\n💰 Награда: **+{reward} монет**."
    else:
        res = "🤖 Бот победил! Ты ничего не получил."

    await update.message.reply_text(f"Ты: {user_choice}\nБот: {bot_choice}\n\n{res}")

# --- Промокоды ---
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

async def use_promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Введи промокод. Пример: `/promo START`", parse_mode="Markdown")
        return
        
    code = context.args[0].upper()
    data = load_data()
    uid = ensure_user(data, update.effective_user)
    
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
        uid = ensure_user(data, update.effective_user)
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

# --- Рассылка ---
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
    app.add_handler(CommandHandler("rps", rps_game))
    app.add_handler(CommandHandler("promo", use_promo))
    app.add_handler(CommandHandler("buy", buy_item))
    app.add_handler(CommandHandler("set", set_item))
    app.add_handler(CommandHandler("hide", hide_panel))
    
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
