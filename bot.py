import os
import json
import random
from datetime import datetime, timedelta

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    BotCommand
)

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters
)


# =========================================================
# НАСТРОЙКИ
# =========================================================

TOKEN = os.getenv("TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

DB_FILE = "data.json"

CHOOSING_NUMBER = 1


# =========================================================
# МАГАЗИН
# =========================================================

ITEMS = {
    "1": {
        "name": "⚡ Профи",
        "icon": "⚡",
        "price": 50,
        "category": "Титул"
    },
    "2": {
        "name": "🔥 Элита",
        "icon": "🔥",
        "price": 150,
        "category": "Титул"
    },
    "3": {
        "name": "👑 Легенда",
        "icon": "👑",
        "price": 300,
        "category": "Титул"
    },
    "4": {
        "name": "💻 Сын маминой подруги",
        "icon": "💻",
        "price": 600,
        "category": "Титул"
    },
    "5": {
        "name": "🗿 Гигачад",
        "icon": "🗿",
        "price": 1000,
        "category": "Титул"
    },
    "6": {
        "name": "🤡 Главный клоун",
        "icon": "🤡",
        "price": 200,
        "category": "Титул"
    },
    "7": {
        "name": "🤑 Криптоинвестор",
        "icon": "🤑",
        "price": 777,
        "category": "Титул"
    },
    "8": {
        "name": "🥷 Теневой самурай",
        "icon": "🥷",
        "price": 500,
        "category": "Титул"
    },
    "9": {
        "name": "🐲 Повелитель драконов",
        "icon": "🐲",
        "price": 1500,
        "category": "Титул"
    },
    "10": {
        "name": "🤖 Кибернетический бог",
        "icon": "🤖",
        "price": 2500,
        "category": "Титул"
    },

    "11": {
        "name": "🧪 Секретный эликсир",
        "icon": "🧪",
        "price": 333,
        "category": "Артефакт"
    },
    "12": {
        "name": "🔮 Магический шар",
        "icon": "🔮",
        "price": 777,
        "category": "Артефакт"
    },
    "13": {
        "name": "🍕 Легендарная пицца",
        "icon": "🍕",
        "price": 250,
        "category": "Артефакт"
    },
    "14": {
        "name": "🕶 Крутые очки",
        "icon": "🕶",
        "price": 400,
        "category": "Артефакт"
    }
}


# =========================================================
# БАЗА ДАННЫХ JSON
# =========================================================

def load_data():
    if not os.path.exists(DB_FILE):
        return {
            "users": {},
            "promos": {}
        }

    try:
        with open(DB_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            raise ValueError("Неверный формат базы")

        data.setdefault("users", {})
        data.setdefault("promos", {})

        return data

    except Exception:
        return {
            "users": {},
            "promos": {}
        }


def save_data(data):
    temp_file = DB_FILE + ".tmp"

    with open(temp_file, "w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=4
        )

    os.replace(temp_file, DB_FILE)


# =========================================================
# ПОЛЬЗОВАТЕЛЬ
# =========================================================

def ensure_user(data, user):
    uid = str(user.id)

    if uid not in data["users"]:

        data["users"][uid] = {
            "name": user.first_name or "Игрок",

            "balance": 0,

            "inventory": [],

            "active_item": None,

            "last_daily": None,

            "games": 0,

            "wins": 0,

            "rps_games": 0,

            "rps_wins": 0,

            "luck_games": 0
        }

    else:
        # Добавляем новые поля старым пользователям
        # если их ещё нет.

        user_data = data["users"][uid]

        user_data.setdefault(
            "name",
            user.first_name or "Игрок"
        )

        user_data.setdefault("balance", 0)
        user_data.setdefault("inventory", [])
        user_data.setdefault("active_item", None)
        user_data.setdefault("last_daily", None)
        user_data.setdefault("games", 0)
        user_data.setdefault("wins", 0)
        user_data.setdefault("rps_games", 0)
        user_data.setdefault("rps_wins", 0)
        user_data.setdefault("luck_games", 0)

    return uid


# =========================================================
# МЕНЮ
# =========================================================

def get_main_menu():

    keyboard = [
        ["🎮 Играть", "🎰 Удача"],
        ["👤 Профиль", "🛍 Магазин"],
        ["🏆 Рекорды", "🎁 Бонус"],
        ["🙈 Скрыть панель"]
    ]

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        is_persistent=True
    )


# =========================================================
# КОМАНДЫ TELEGRAM
# =========================================================

async def setup_menu(application):

    commands = [
        BotCommand("start", "Запустить игру"),
        BotCommand("help", "Правила игры"),
        BotCommand("shop", "Магазин"),
        BotCommand("daily", "Ежедневный бонус"),
        BotCommand("rps", "Камень, ножницы, бумага"),
        BotCommand("promo", "Промокод"),
        BotCommand("buy", "Купить предмет"),
        BotCommand("set", "Надеть предмет"),
        BotCommand("hide", "Скрыть панель")
    ]

    await application.bot.set_my_commands(commands)


# =========================================================
# START
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    data = load_data()

    ensure_user(
        data,
        update.effective_user
    )

    save_data(data)

    await update.message.reply_text(
        "👋 Привет!\n\n"
        "Добро пожаловать в игру 🤖\n"
        "Выбирай действие в меню ниже 👇",
        reply_markup=get_main_menu()
    )

    return ConversationHandler.END


# =========================================================
# HELP
# =========================================================

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = (
        "🆘 *Как играть:*\n\n"

        "🎲 *Угадай число*\n"
        "Я загадаю число от 1 до 100.\n"
        "За победу: +10 монет.\n\n"

        "🎰 *Удача*\n"
        "Небольшая случайная игра без ставок.\n\n"

        "✂️ *Камень, ножницы, бумага*\n"
        "Победа: +15 монет.\n\n"

        "🎁 *Бонус*\n"
        "Раз в 24 часа: +25 монет.\n\n"

        "🛍 *Магазин*\n"
        "Покупай титулы и артефакты.\n\n"

        "🎒 *Экипировка*\n"
        "Используй `/set номер`.\n\n"

        "🎟 *Промокоды*\n"
        "Используй `/promo код`."
    )

    await update.message.reply_text(
        text,
        parse_mode="Markdown"
    )


# =========================================================
# СКРЫТЬ ПАНЕЛЬ
# =========================================================

async def hide_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🙈 Панель скрыта.\n"
        "Чтобы вернуть её, отправь /start.",
        reply_markup=ReplyKeyboardRemove()
    )


# =========================================================
# ПРОФИЛЬ
# =========================================================

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):

    data = load_data()

    uid = ensure_user(
        data,
        update.effective_user
    )

    user = data["users"][uid]

    active_id = user.get("active_item")
    item = ITEMS.get(active_id)

    if item:
        title = f"{item['icon']} {item['name']}"
    else:
        title = "👤 Новичок"

    text = (
        f"👤 *Профиль: {user['name']}*\n\n"

        f"🏅 Титул: {title}\n"
        f"💰 Монеты: {user['balance']}\n\n"

        f"🎮 Игр сыграно: {user['games']}\n"
        f"🏆 Побед: {user['wins']}\n\n"

        f"✂️ КНБ сыграно: {user['rps_games']}\n"
        f"🥇 Побед в КНБ: {user['rps_wins']}\n\n"

        f"🎒 Предметов: {len(user['inventory'])}"
    )

    save_data(data)

    await update.message.reply_text(
        text,
        parse_mode="Markdown"
    )


# =========================================================
# РЕКОРДЫ
# =========================================================

async def records(update: Update, context: ContextTypes.DEFAULT_TYPE):

    data = load_data()

    users_list = list(
        data["users"].values()
    )

    top_users = sorted(
        users_list,
        key=lambda x: x.get("balance", 0),
        reverse=True
    )[:5]

    if not top_users:
        await update.message.reply_text(
            "🏆 Пока игроков нет."
        )
        return

    text = "🏆 *ТОП-5 игроков по монетам:*\n\n"

    for i, user in enumerate(top_users, start=1):

        active_id = user.get("active_item")

        if active_id in ITEMS:
            title = ITEMS[active_id]["name"]
        else:
            title = "Новичок"

        text += (
            f"{i}. {user.get('name', 'Игрок')} — "
            f"💰 {user.get('balance', 0)} "
            f"({title})\n"
        )

    await update.message.reply_text(
        text,
        parse_mode="Markdown"
    )


# =========================================================
# DAILY
# =========================================================

async def daily_bonus(update: Update, context: ContextTypes.DEFAULT_TYPE):

    data = load_data()

    uid = ensure_user(
        data,
        update.effective_user
    )

    user = data["users"][uid]

    now = datetime.now()

    last_daily = user.get("last_daily")

    if last_daily:

        try:
            last_time = datetime.fromisoformat(
                last_daily
            )

            elapsed = now - last_time

            if elapsed < timedelta(hours=24):

                left = timedelta(hours=24) - elapsed

                hours = left.seconds // 3600
                minutes = (left.seconds % 3600) // 60

                await update.message.reply_text(
                    f"⏳ Бонус уже получен.\n"
                    f"Следующий через {hours} ч. {minutes} мин."
                )

                return

        except ValueError:
            pass

    user["balance"] += 25

    user["last_daily"] = now.isoformat()

    save_data(data)

    await update.message.reply_text(
        "🎁 Ежедневный бонус получен!\n"
        "💰 +25 монет"
    )


# =========================================================
# МАГАЗИН
# =========================================================

async def shop_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = "🛍 *МАГАЗИН*\n\n"

    text += "📜 *ТИТУЛЫ*\n"

    for item_id, item in ITEMS.items():

        if item["category"] == "Титул":

            text += (
                f"{item_id}. "
                f"{item['icon']} "
                f"{item['name']} — "
                f"{item['price']} 🪙\n"
            )

    text += "\n🔮 *АРТЕФАКТЫ*\n"

    for item_id, item in ITEMS.items():

        if item["category"] == "Артефакт":

            text += (
                f"{item_id}. "
                f"{item['icon']} "
                f"{item['name']} — "
                f"{item['price']} 🪙\n"
            )

    text += (
        "\n"
        "👉 Купить: `/buy номер`\n"
        "🎒 Надеть: `/set номер`"
    )

    await update.message.reply_text(
        text,
        parse_mode="Markdown"
    )


# =========================================================
# ПОКУПКА
# =========================================================

async def buy_item(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:

        await update.message.reply_text(
            "⚠️ Напиши номер товара.\n"
            "Например: `/buy 1`"
        )

        return

    item_id = context.args[0]

    if item_id not in ITEMS:

        await update.message.reply_text(
            "❌ Такого товара нет."
        )

        return

    data = load_data()

    uid = ensure_user(
        data,
        update.effective_user
    )

    user = data["users"][uid]

    item = ITEMS[item_id]

    if item_id in user["inventory"]:

        await update.message.reply_text(
            "⚠️ Этот предмет уже есть у тебя."
        )

        return

    if user["balance"] < item["price"]:

        await update.message.reply_text(
            f"❌ Недостаточно монет.\n"
            f"Баланс: {user['balance']} 🪙\n"
            f"Цена: {item['price']} 🪙"
        )

        return

    user["balance"] -= item["price"]

    user["inventory"].append(item_id)

    save_data(data)

    await update.message.reply_text(
        f"🎉 Куплено!\n"
        f"{item['icon']} {item['name']}\n\n"
        f"💰 Осталось: {user['balance']} 🪙"
    )


# =========================================================
# НАДЕТЬ ПРЕДМЕТ
# =========================================================

async def set_item(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:

        await update.message.reply_text(
            "⚠️ Напиши номер предмета.\n"
            "Например: `/set 1`"
        )

        return

    item_id = context.args[0]

    data = load_data()

    uid = ensure_user(
        data,
        update.effective_user
    )

    user = data["users"][uid]

    if item_id not in user["inventory"]:

        await update.message.reply_text(
            "❌ У тебя нет этого предмета."
        )

        return

    if item_id not in ITEMS:

        await update.message.reply_text(
            "❌ Предмет больше не существует."
        )

        return

    user["active_item"] = item_id

    save_data(data)

    await update.message.reply_text(
        f"✅ Экипировано:\n"
        f"{ITEMS[item_id]['icon']} "
        f"{ITEMS[item_id]['name']}"
    )


# =========================================================
# КАМЕНЬ НОЖНИЦЫ БУМАГА
# =========================================================

async def rps_game(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:

        await update.message.reply_text(
            "✂️ Камень, ножницы, бумага!\n\n"
            "Используй:\n"
            "/rps камень\n"
            "/rps ножницы\n"
            "/rps бумага"
        )

        return

    user_choice = context.args[0].lower()

    choices = [
        "камень",
        "ножницы",
        "бумага"
    ]

    if user_choice not in choices:

        await update.message.reply_text(
            "❌ Выбери камень, ножницы или бумагу."
        )

        return

    bot_choice = random.choice(choices)

    data = load_data()

    uid = ensure_user(
        data,
        update.effective_user
    )

    user = data["users"][uid]

    user["rps_games"] += 1

    if user_choice == bot_choice:

        result = "🤝 Ничья!"

    elif (
        (user_choice == "камень" and bot_choice == "ножницы")
        or
        (user_choice == "ножницы" and bot_choice == "бумага")
        or
        (user_choice == "бумага" and bot_choice == "камень")
    ):

        user["balance"] += 15
        user["rps_wins"] += 1

        result = "🎉 Ты победил!\n💰 +15 монет"

    else:

        result = "🤖 Бот победил!"

    save_data(data)

    await update.message.reply_text(
        f"Ты: {user_choice}\n"
        f"Бот: {bot_choice}\n\n"
        f"{result}"
    )


# =========================================================
# УДАЧА
# =========================================================

async def luck_game(update: Update, context: ContextTypes.DEFAULT_TYPE):

    data = load_data()

    uid = ensure_user(
        data,
        update.effective_user
    )

    user = data["users"][uid]

    user["luck_games"] += 1

    reward = random.choice([
        0,
        0,
        5,
        10,
        15,
        25
    ])

    user["balance"] += reward

    save_data(data)

    if reward == 0:

        text = "😢 Сегодня удача не на твоей стороне."

    else:

        text = (
            f"🍀 Тебе повезло!\n"
            f"💰 +{reward} монет"
        )

    await update.message.reply_text(text)


# =========================================================
# УГАДАЙ ЧИСЛО
# =========================================================

async def game_start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["secret"] = random.randint(
        1,
        100
    )

    await update.message.reply_text(
        "🎲 Я загадал число от 1 до 100.\n\n"
        "Пиши свой вариант."
    )

    return CHOOSING_NUMBER


async def game_guess(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    try:
        guess = int(text)

    except ValueError:

        await update.message.reply_text(
            "⚠️ Напиши число от 1 до 100."
        )

        return CHOOSING_NUMBER

    if guess < 1 or guess > 100:

        await update.message.reply_text(
            "⚠️ Число должно быть от 1 до 100."
        )

        return CHOOSING_NUMBER

    secret = context.user_data["secret"]

    if guess == secret:

        data = load_data()

        uid = ensure_user(
            data,
            update.effective_user
        )

        user = data["users"][uid]

        user["balance"] += 10
        user["games"] += 1
        user["wins"] += 1

        save_data(data)

        await update.message.reply_text(
            f"🎉 Ты угадал!\n"
            f"Моё число: {secret}\n\n"
            f"💰 +10 монет",
            reply_markup=get_main_menu()
        )

        return ConversationHandler.END

    if guess < secret:

        await update.message.reply_text(
            "📈 Моё число больше!"
        )

    else:

        await update.message.reply_text(
            "📉 Моё число меньше!"
        )

    return CHOOSING_NUMBER


async def cancel_game(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data.pop(
        "secret",
        None
    )

    await update.message.reply_text(
        "❌ Игра отменена.",
        reply_markup=get_main_menu()
    )

    return ConversationHandler.END


# =========================================================
# ПРОМОКОДЫ
# =========================================================

async def create_promo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    if len(context.args) < 2:

        await update.message.reply_text(
            "Формат:\n"
            "/add_promo КОД СУММА"
        )

        return

    code = context.args[0].upper()

    try:
        amount = int(context.args[1])

    except ValueError:

        await update.message.reply_text(
            "❌ Сумма должна быть числом."
        )

        return

    if amount <= 0:

        await update.message.reply_text(
            "❌ Сумма должна быть больше нуля."
        )

        return

    data = load_data()

    data["promos"][code] = {
        "amount": amount,
        "used": []
    }

    save_data(data)

    await update.message.reply_text(
        f"✅ Промокод {code} создан!\n"
        f"💰 Награда: {amount} монет"
    )


async def use_promo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:

        await update.message.reply_text(
            "⚠️ Напиши промокод.\n"
            "Например: `/promo START`"
        )

        return

    code = context.args[0].upper()

    data = load_data()

    uid = ensure_user(
        data,
        update.effective_user
    )

    if code not in data["promos"]:

        await update.message.reply_text(
            "❌ Такого промокода нет."
        )

        return

    promo = data["p
