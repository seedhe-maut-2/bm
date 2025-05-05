import telebot
import subprocess
import datetime
import os
from telebot import types
import time
import re
from threading import Lock, Timer
import logging
import sqlite3

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Bot configuration
bot = telebot.TeleBot('7724010740:AAHl1Avs1FDKlfvTjABS3ffe6-nVhkcGCj0')
admin_id = {"8167507955"}  # Admin user ID
CHANNEL_USERNAME = "@seedhe_maut"  # Your channel username
CHANNEL_ID = -1002440538814  # Your channel ID
INVITE_LINK = "https://t.me/+1AwFhWe8oxg1OTM1"  # Your invite link

# Database setup
DB_FILE = "users.db"
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# Create tables if they don't exist
cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                 (user_id INTEGER PRIMARY KEY, 
                 credits INTEGER DEFAULT 5,
                 invited_by INTEGER DEFAULT NULL)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS invited_users
                 (inviter_id INTEGER,
                  invitee_id INTEGER,
                  PRIMARY KEY (inviter_id, invitee_id))''')
conn.commit()

# Other constants
USER_FILE = "users.txt"
USER_TIME_LIMITS = "user_limits.txt"
LOG_FILE = "attack_logs.txt"
COOLDOWN_TIME = 600  # 5 minutes
MAX_ATTACK_TIME = 240  # 4 minutes (240 seconds)
IMAGE_URL = "https://t.me/gggkkkggggiii/9"
INITIAL_CREDITS = 5
INVITE_CREDITS = 2

# Data storage
user_attack_data = {}
maut_cooldown = {}
active_attacks = {}  # Track active attacks
attack_lock = Lock()  # Thread lock for attack operations

def get_user_credits(user_id):
    """Get user's remaining credits"""
    cursor.execute("SELECT credits FROM users WHERE user_id=?", (user_id,))
    result = cursor.fetchone()
    return result[0] if result else 0

def update_user_credits(user_id, credits):
    """Update user's credits"""
    cursor.execute("INSERT OR IGNORE INTO users (user_id, credits) VALUES (?, ?)", 
                  (user_id, INITIAL_CREDITS))
    cursor.execute("UPDATE users SET credits=? WHERE user_id=?", 
                  (credits, user_id))
    conn.commit()

def add_invited_user(inviter_id, invitee_id):
    """Record that a user was invited by another user"""
    try:
        cursor.execute("INSERT INTO invited_users VALUES (?, ?)", 
                      (inviter_id, invitee_id))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # Already exists

def has_joined_channel(user_id):
    """Check if user has joined the required channel"""
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logger.error(f"Error checking channel membership: {e}")
        return False

def safe_int(value, default=None):
    """Safely convert to integer with default fallback"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def log_attack(user_id, target, port, attack_time):
    """Log attack details to file"""
    try:
        user_id_str = str(user_id)
        with open(LOG_FILE, "a") as f:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"{timestamp} | UserID:{user_id_str} | {target}:{port} | {attack_time}s\n")
    except Exception as e:
        logger.error(f"Logging error: {e}")

def parse_time_input(time_str):
    """Parse human-readable time input into seconds"""
    if not time_str:
        return None
        
    time_str = time_str.lower()
    total_seconds = 0
    
    # Match all time components
    matches = re.findall(r'(\d+)\s*(day|hour|min|sec|d|h|m|s)', time_str)
    
    for amount, unit in matches:
        amount = safe_int(amount, 0)
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
    """Check if any attack is currently active"""
    with attack_lock:
        return bool(active_attacks)

def add_active_attack(user_id, attack_time):
    """Add an attack to the active attacks tracker"""
    with attack_lock:
        active_attacks[str(user_id)] = {
            'start_time': datetime.datetime.now(),
            'duration': safe_int(attack_time, 0)
        }

def remove_active_attack(user_id):
    """Remove an attack from the active attacks tracker"""
    with attack_lock:
        active_attacks.pop(str(user_id), None)

def get_active_attack_info():
    """Get information about the currently active attack"""
    with attack_lock:
        if not active_attacks:
            return None
            
        # Get the first active attack (since we only allow one at a time)
        user_id, attack = next(iter(active_attacks.items()))
        elapsed = (datetime.datetime.now() - attack['start_time']).seconds
        remaining = max(0, attack['duration'] - elapsed)
        return user_id, remaining

def validate_ip(ip):
    """Validate an IPv4 address"""
    if not ip:
        return False
    parts = ip.split('.')
    if len(parts) != 4:
        return False
    try:
        return all(0 <= int(part) <= 255 for part in parts)
    except ValueError:
        return False

def validate_port(port):
    """Validate a port number"""
    port_num = safe_int(port)
    return port_num is not None and 1 <= port_num <= 65535

def validate_attack_time(time_str):
    """Validate attack duration"""
    time_sec = safe_int(time_str)
    return time_sec is not None and 1 <= time_sec <= MAX_ATTACK_TIME

def check_channel_membership(user_id):
    """Check if user is member of required channel"""
    if str(user_id) in admin_id:
        return True
    
    if not has_joined_channel(user_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Join Channel", url=INVITE_LINK))
        markup.add(types.InlineKeyboardButton("✅ I've Joined", callback_data="check_join"))
        return False, markup
    return True, None

@bot.message_handler(commands=['start'])
def start_command(message):
    """Handle /start command"""
    user_id = message.from_user.id
    is_member, markup = check_channel_membership(user_id)
    
    if not is_member:
        bot.send_message(
            message.chat.id,
            "⚠️ You must join our channel to use this bot!",
            reply_markup=markup
        )
        return
    
    # Check if user exists in DB, if not add with initial credits
    cursor.execute("INSERT OR IGNORE INTO users (user_id, credits) VALUES (?, ?)", 
                  (user_id, INITIAL_CREDITS))
    conn.commit()
    
    credits = get_user_credits(user_id)
    
    # Check if user was invited
    if len(message.text.split()) > 1:
        inviter_id = safe_int(message.text.split()[1])
        if inviter_id and inviter_id != user_id:
            if add_invited_user(inviter_id, user_id):
                # Add credits to inviter
                inviter_credits = get_user_credits(inviter_id)
                update_user_credits(inviter_id, inviter_credits + INVITE_CREDITS)
                
                # Add credits to new user
                update_user_credits(user_id, credits + INVITE_CREDITS)
                credits += INVITE_CREDITS
    
    caption = f"""
🚀 *Welcome to MAUT DDoS Bot* 🚀

*Available Commands:*
/maut <ip> <port> <time> - Start attack
/credits - Check your credits
/invite - Get your invite link
/mylogs - View your attack history
/help - Show all commands
/rules - Usage guidelines

*Your Credits:* {credits}

⚡ *Example Attack:*
`/maut 1.1.1.1 80 60`
"""
    try:
        bot.send_photo(
            chat_id=message.chat.id,
            photo=IMAGE_URL,
            caption=caption,
            parse_mode="Markdown",
            reply_markup=create_main_menu()
        )
    except Exception as e:
        logger.error(f"Error sending image: {e}")
        try:
            bot.reply_to(message, caption, parse_mode="Markdown")
        except Exception as e2:
            logger.error(f"Error sending text message: {e2}")

def create_main_menu():
    """Create the main menu keyboard"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("/maut", "/credits")
    markup.row("/invite", "/mylogs")
    markup.row("/help", "/rules")
    return markup

@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def check_join_callback(call):
    """Handle join channel verification"""
    user_id = call.from_user.id
    if has_joined_channel(user_id):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        start_command(call.message)
    else:
        bot.answer_callback_query(call.id, "⚠️ You haven't joined the channel yet!")

@bot.message_handler(commands=['credits'])
def check_credits(message):
    """Check user's credits"""
    user_id = message.from_user.id
    is_member, markup = check_channel_membership(user_id)
    if not is_member:
        bot.send_message(
            message.chat.id,
            "⚠️ You must join our channel to use this bot!",
            reply_markup=markup
        )
        return
    
    credits = get_user_credits(user_id)
    bot.reply_to(message, f"💰 Your current credits: {credits}")

@bot.message_handler(commands=['invite'])
def invite_command(message):
    """Generate invite link"""
    user_id = message.from_user.id
    is_member, markup = check_channel_membership(user_id)
    if not is_member:
        bot.send_message(
            message.chat.id,
            "⚠️ You must join our channel to use this bot!",
            reply_markup=markup
        )
        return
    
    bot.reply_to(
        message,
        f"🔗 Invite others and earn {INVITE_CREDITS} credits per user!\n\n"
        f"Your invite link:\n"
        f"https://t.me/{bot.get_me().username}?start={user_id}",
        disable_web_page_preview=True
    )

@bot.message_handler(commands=['maut'])
def handle_attack_command(message):
    """Handle attack command"""
    user_id = message.from_user.id
    is_member, markup = check_channel_membership(user_id)
    if not is_member:
        bot.send_message(
            message.chat.id,
            "⚠️ You must join our channel to use this bot!",
            reply_markup=markup
        )
        return
    
    # Check credits
    credits = get_user_credits(user_id)
    if credits <= 0:
        bot.reply_to(message, "❌ You don't have enough credits. Use /invite to earn more.")
        return
    
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
    if str(user_id) in maut_cooldown:
        elapsed = (datetime.datetime.now() - maut_cooldown[str(user_id)]).seconds
        remaining = max(0, COOLDOWN_TIME - elapsed)
        if remaining > 0:
            return bot.reply_to(message, f"⏳ Cooldown active. Wait {remaining} seconds.")
    
    # Parse command
    try:
        args = message.text.split()
        if len(args) != 4:
            return bot.reply_to(message, "❌ Usage: /maut <ip> <port> <time>\nExample: /maut 1.1.1.1 80 60")
        
        ip = args[1]
        port = args[2]
        attack_time = args[3]
        
        # Validate inputs
        if not validate_ip(ip):
            return bot.reply_to(message, "❌ Invalid IP format. Example: 1.1.1.1")
        
        if not validate_port(port):
            return bot.reply_to(message, "❌ Invalid port (1-65535)")
        
        attack_time_sec = safe_int(attack_time)
        if not validate_attack_time(attack_time):
            return bot.reply_to(message, f"❌ Invalid time (1-{MAX_ATTACK_TIME} seconds)")
        
        # Store attack data
        user_attack_data[str(user_id)] = {
            'ip': ip,
            'port': port,
            'time': attack_time_sec
        }
        
        # Show confirmation
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ Start Attack", callback_data="start_attack"),
            types.InlineKeyboardButton("❌ Cancel", callback_data="cancel_attack")
        )
        
        bot.send_message(
            message.chat.id,
            f"⚡ *Attack Summary:*\n\n"
            f"🌐 IP: `{ip}`\n"
            f"🔌 Port: `{port}`\n"
            f"⏱ Time: `{attack_time_sec}`s\n"
            f"💰 Cost: 1 credit\n\n"
            f"Confirm attack:",
            parse_mode="Markdown",
            reply_markup=markup
        )
        
    except Exception as e:
        logger.error(f"Error processing attack command: {e}")
        bot.reply_to(message, f"❌ Error processing command: {str(e)}")

# ... (rest of the callback handlers and other commands remain similar, 
# but make sure to add channel membership check at the beginning of each)

def main():
    """Main function to initialize and run the bot"""
    logger.info("⚡ MAUT Bot Starting ⚡")
    
    # Start bot with error recovery
    while True:
        try:
            logger.info("Bot is running...")
            bot.polling(none_stop=True, interval=1, timeout=30)
        except Exception as e:
            logger.error(f"Bot crashed with error: {e}")
            logger.info("Restarting in 5 seconds...")
            time.sleep(5)

if __name__ == "__main__":
    main()
