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

# --- Магазин предметов ---
ITEMS = {
    "1": {"name": "⚡ Профи", "icon": "⚡", "price": 50},
    "2": {"name": "🔥 Элита", "icon": "🔥", "price": 150},
    "3": {"name": "👑 Легенда", "icon": "👑", "price": 300},
    "4": {"name": "💻 Сын маминой подруги", "icon": "💻", "price": 600},
    "5": {"name": "🗿 Гигачад", "icon": "🗿", "price": 1000},
    "6": {"name": "🤡 Главный клоун", "icon": "🤡", "price": 200},
    "7": {"name": "🤑 Криптоинвестор", "icon": "🤑", "price": 777},
    "8": {"name": "🥷 Теневой самурай", "icon": "🥷", "price": 500}
}

def load_data():
    if not os.path.exists(DB_FILE): 
        return {"users": {}, "promos": {}}
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
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

# --- Команды ---

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    uid = ensure_user(data, update.effective_user)
    user = data["users"][uid]
    
    active_id = user.get("active_item")
    item = ITEMS.get(active_id)
    
    icon = item["icon"] if item else "👤"
    title = item["name"] if item else "Новичок"
    
    text = (f"👤 **Профиль: {user['name']}**\n"
            f"🏅 Статус: {icon} {title}\n"
            f"💰 Баланс: {user['balance']} монет\n\n"
            f"🎒 Инвентарь: {len(user['inventory'])} предметов")
    await update.message.reply_text(text, parse_mode="Markdown")

async def buy_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Используй: /buy [номер]")
        return
    item_id = context.args[0]
    if item_id not in ITEMS:
        await update.message.reply_text("❌ Нет такого товара!")
        return
        
    data = load_data()
    uid = ensure_user(data, update.effective_user)
    user = data["users"][uid]
    
    if item_id in user["inventory"]:
        await update.message.reply_text("⚠️ У тебя уже есть этот предмет!")
        return
        
    if user["balance"] < ITEMS[item_id]["price"]:
        await update.message.reply_text("❌ Не хватает монет!")
        return
        
    user["balance"] -= ITEMS[item_id]["price"]
    user["inventory"].append(item_id)
    save_data(data)
    await update.message.reply_text(f"✅ Куплено: {ITEMS[item_id]['name']}. Используй /set {item_id}, чтобы надеть.")

async def set_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Используй: /set [номер]")
        return
    item_id = context.args[0]
    data = load_data()
    uid = ensure_user(data, update.effective_user)
    
    if item_id in data["users"][uid]["inventory"]:
        data["users"][uid]["active_item"] = item_id
        save_data(data)
        await update.message.reply_text(f"✅ Экипировано: {ITEMS[item_id]['name']}")
    else:
        await update.message.reply_text("❌ Сначала купи этот предмет!")

async def rps_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Используй: /rps [камень/ножницы/бумага]")
        return
    
    user_choice = context.args[0].lower()
    choices = ["камень", "ножницы", "бумага"]
    
    if user_choice not in choices:
        await update.message.reply_text("Выбери: камень, ножницы или бумага!")
        return

    bot_choice = random.choice(choices)
    if user_choice == bot_choice:
        res = "🤝 Ничья!"
    elif (user_choice == "камень" and bot_choice == "ножницы") or \
         (user_choice == "ножницы" and bot_choice == "бумага") or \
         (user_choice == "бумага" and bot_choice == "камень"):
        res = "🎉 Победа!"
    else:
        res = "🤖 Бот победил!"
    await update.message.reply_text(f"Ты: {user_choice}\nБот: {bot_choice}\n\n{res}")

# --- Добавление в main() ---
# Не забудь прописать app.add_handler(CommandHandler("set", set_item))
# И app.add_handler(CommandHandler("rps", rps_game))
