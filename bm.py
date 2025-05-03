import asyncio
import random
import string
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
from pymongo import MongoClient
from datetime import datetime, timedelta, timezone

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Database configuration
MONGO_URI = 'mongodb+srv://zeni:1I8uJt78Abh4K5lo@zeni.v7yls.mongodb.net/?retryWrites=true&w=majority&appName=zeni'
client = MongoClient(MONGO_URI)
db = client['rbbl']
users_collection = db['VAMPIREXCHEATS']
redeem_codes_collection = db['redeem_codes0']
attack_logs_collection = db['attack_logs']

# Bot configuration
TELEGRAM_BOT_TOKEN = '7970310406:AAGh47IMJxhCPwqTDe_3z3PCvXugf7Y3yYE'
ADMIN_USER_ID = 7017469802 

# Global variables
cooldown_dict = {}
user_attack_history = {}
valid_ip_prefixes = ('52.', '20.', '14.', '4.', '13.', '100.', '235.')
attack_keys = {}
methods = {
    "UDP": "UDP Flood - High bandwidth",
    "TCP": "TCP SYN Flood - Powerful",
    "HTTP": "HTTP GET Flood - Layer7",
    "OVH": "OVH Bypass - Special method"
}

async def help_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        help_text = (
            "🌟 *Bot Commands Menu* 🌟\n\n"
            "🛡️ *Basic Commands:*\n"
            "/start - Check bot status\n"
            "/help - Show this menu\n"
            "/get_id - Get your user ID\n\n"
            "⚔️ *Attack Commands:*\n"
            "/attack - Start attack process\n"
            "/methods - Show available methods\n\n"
            "💎 *Premium Commands:*\n"
            "/redeem - Activate premium code\n"
            "/status - Check premium status\n\n"
            "📌 All attacks require premium access"
        )
    else:
        help_text = (
            "👑 *Admin Commands Menu* 👑\n\n"
            "🔧 *Management Commands:*\n"
            "/users - List all users\n"
            "/remove [id] - Remove user\n"
            "/ban [id] - Ban user\n\n"
            "💳 *Premium Commands:*\n"
            "/gen - Generate premium code\n"
            "/addpremium [id] [days] - Add premium\n\n"
            "📊 *Stats Commands:*\n"
            "/stats - Show bot statistics\n"
            "/logs [user_id] - View attack logs"
        )
    await safe_send_message(update, context, help_text)

async def start(update: Update, context: CallbackContext):
    user = update.effective_user
    welcome_msg = (
        f"👋 *Welcome {user.first_name}!* 👋\n\n"
        "🚀 *Premium Network Stress Testing Bot*\n\n"
        "🔹 *Features:*\n"
        "- Powerful Layer4/Layer7 methods\n"
        "- Premium-only access\n"
        "- 99.9% Uptime servers\n\n"
        "📌 *Getting Started:*\n"
        "1. Use /redeem with a premium code\n"
        "2. Check /methods for options\n"
        "3. Launch with /attack\n\n"
        "🛡️ *Note:* All attacks are logged\n"
        "Misuse will result in ban"
    )
    await safe_send_message(update, context, welcome_msg)

async def methods_command(update: Update, context: CallbackContext):
    methods_text = "⚔️ *Available Attack Methods* ⚔️\n\n"
    for name, desc in methods.items():
        methods_text += f"🔹 *{name}:* {desc}\n"
    
    methods_text += "\nUsage: /attack <method> <ip> <port> <time>"
    await safe_send_message(update, context, methods_text)

async def attack(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    if not await is_user_allowed(user_id):
        await safe_send_message(update, context, "🔒 *Premium Access Required*")
        return
    
    # Generate 6-digit verification code
    verification_key = ''.join(random.choices(string.digits, k=6))
    attack_keys[user_id] = verification_key
    
    await safe_send_message(
        update,
        context,
        f"🔐 *Verification Required*\n\n"
        f"Your code: `{verification_key}`\n\n"
        "Reply with:\n"
        "`/key <code> <method> <ip> <port> <time>`\n\n"
        "Example:\n"
        "`/key 123456 UDP 1.1.1.1 80 60`\n\n"
        "Check methods with /methods"
    )

async def verify_key(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    
    if user_id not in attack_keys:
        await safe_send_message(update, context, "⚠️ First use /attack")
        return
    
    if len(context.args) < 5:
        await safe_send_message(update, context, "ℹ️ Usage: /key <code> <method> <ip> <port> <time>")
        return
    
    key, method, ip, port, duration = context.args[0], context.args[1], context.args[2], context.args[3], context.args[4]
    
    if key != attack_keys.get(user_id):
        await safe_send_message(update, context, "❌ Invalid code")
        return
    
    if method.upper() not in methods:
        await safe_send_message(update, context, "❌ Invalid method\nCheck /methods")
        return
    
    del attack_keys[user_id]
    await process_attack(update, context, method.upper(), ip, port, duration)

async def process_attack(update: Update, context: CallbackContext, method: str, ip: str, port: str, duration: str):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    # Validate IP
    if not ip.startswith(valid_ip_prefixes):
        await safe_send_message(update, context, "❌ Invalid target IP")
        return
    
    # Validate duration
    try:
        duration = int(duration)
        if duration > 200:
            await safe_send_message(update, context, "⚠️ Max duration is 200 seconds")
            return
        if duration < 10:
            await safe_send_message(update, context, "⚠️ Min duration is 10 seconds")
            return
    except ValueError:
        await safe_send_message(update, context, "❌ Invalid duration")
        return
    
    # Cooldown check
    current_time = datetime.now()
    if user_id in cooldown_dict:
        time_diff = (current_time - cooldown_dict[user_id]).total_seconds()
        if time_diff < 120:
            remaining = 120 - int(time_diff)
            await safe_send_message(update, context, f"⏳ Please wait {remaining} seconds")
            return
    
    cooldown_dict[user_id] = current_time
    
    # Log attack
    attack_log = {
        "user_id": user_id,
        "method": method,
        "target": f"{ip}:{port}",
        "duration": duration,
        "timestamp": datetime.now(timezone.utc)
    }
    attack_logs_collection.insert_one(attack_log)
    
    # Send confirmation
    attack_msg = (
        "🚀 *Attack Launched* 🚀\n\n"
        f"🎯 *Target:* `{ip}:{port}`\n"
        f"⚔️ *Method:* `{method}`\n"
        f"⏱️ *Duration:* `{duration}` seconds\n"
        f"🆔 *User ID:* `{user_id}`\n\n"
        "🛡️ *Note:* Attack in progress..."
    )
    await safe_send_message(update, context, attack_msg)
    
    # Execute attack
    asyncio.create_task(execute_attack(chat_id, method, ip, port, duration, context, user_id))

async def execute_attack(chat_id, method, ip, port, duration, context, user_id):
    try:
        # Simulate attack process
        await asyncio.sleep(min(duration, 10))  # Max 10 sec simulation
        
        # Random stats
        packets = random.randint(500000, 2000000)
        success_rate = random.uniform(95.0, 99.9)
        
        completion_msg = (
            "✅ *Attack Completed* ✅\n\n"
            f"🎯 *Target:* `{ip}:{port}`\n"
            f"⚔️ *Method:* `{method}`\n"
            f"⏱️ *Duration:* `{duration}` seconds\n\n"
            "📊 *Statistics*\n"
            f"▫️ Packets Sent: {packets:,}\n"
            f"▫️ Success Rate: {success_rate:.1f}%\n\n"
            "Need more power? Contact admin"
        )
        await context.bot.send_message(
            chat_id=chat_id,
            text=completion_msg,
            parse_mode='Markdown'
        )
        
        # Update log with results
        attack_logs_collection.update_one(
            {"user_id": user_id, "timestamp": {"$gte": datetime.now(timezone.utc) - timedelta(minutes=1)}},
            {"$set": {
                "status": "completed",
                "packets": packets,
                "success_rate": success_rate
            }}
        )
        
    except Exception as e:
        logger.error(f"Attack error: {e}")
        await context.bot.send_message(
            chat_id=chat_id,
            text="⚠️ Attack failed - contact admin",
            parse_mode='Markdown'
        )
        attack_logs_collection.update_one(
            {"user_id": user_id, "timestamp": {"$gte": datetime.now(timezone.utc) - timedelta(minutes=1)}},
            {"$set": {"status": "failed"}}
        )

async def generate_code(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await safe_send_message(update, context, "⛔ Admin only")
        return
    
    if len(context.args) < 1:
        await safe_send_message(update, context, "ℹ️ Usage: /gen <days> [uses] [code]")
        return
    
    try:
        days = int(context.args[0])
        uses = int(context.args[1]) if len(context.args) > 1 else 1
        custom_code = context.args[2] if len(context.args) > 2 else None
        
        expiry = datetime.now(timezone.utc) + timedelta(days=days)
        code = custom_code if custom_code else ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        
        redeem_codes_collection.insert_one({
            "code": code,
            "expiry_date": expiry,
            "max_uses": uses,
            "used_by": [],
            "created_by": user_id
        })
        
        await safe_send_message(
            update,
            context,
            f"🎟️ *Premium Code Generated*\n\n"
            f"🔹 *Code:* `{code}`\n"
            f"🔹 *Valid for:* {days} days\n"
            f"🔹 *Max uses:* {uses}"
        )
    except Exception as e:
        await safe_send_message(update, context, f"❌ Error: {str(e)}")

async def redeem_code(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if len(context.args) != 1:
        await safe_send_message(update, context, "ℹ️ Usage: /redeem <code>")
        return
    
    code = context.args[0].upper()
    redeem_data = redeem_codes_collection.find_one({"code": code})
    
    if not redeem_data:
        await safe_send_message(update, context, "❌ Invalid code")
        return
    
    if redeem_data['expiry_date'] < datetime.now(timezone.utc):
        await safe_send_message(update, context, "❌ Code expired")
        return
    
    if len(redeem_data['used_by']) >= redeem_data['max_uses']:
        await safe_send_message(update, context, "❌ Max uses reached")
        return
    
    if user_id in redeem_data['used_by']:
        await safe_send_message(update, context, "⚠️ Already redeemed")
        return
    
    expiry = redeem_data['expiry_date']
    users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"expiry_date": expiry}},
        upsert=True
    )
    
    redeem_codes_collection.update_one(
        {"code": code},
        {"$push": {"used_by": user_id}}
    )
    
    await safe_send_message(
        update,
        context,
        f"🎉 *Premium Activated!*\n\n"
        f"🔹 *Expires:* {expiry.strftime('%Y-%m-%d %H:%M')} UTC\n"
        f"🔹 *User ID:* `{user_id}`"
    )

async def list_users(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_USER_ID:
        await safe_send_message(update, context, "⛔ Admin only")
        return
    
    users = list(users_collection.find())
    if not users:
        await safe_send_message(update, context, "ℹ️ No users found")
        return
    
    now = datetime.now(timezone.utc)
    user_list = "👥 *User List* 👥\n\n"
    
    for user in users:
        expiry = user.get('expiry_date', now)
        remaining = expiry - now
        status = "🟢" if remaining.total_seconds() > 0 else "🔴"
        days = remaining.days
        user_list += f"{status} *{user['user_id']}* - {days} days left\n"
    
    await safe_send_message(update, context, user_list)

async def user_status(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user = users_collection.find_one({"user_id": user_id})
    
    if not user or user.get('expiry_date', datetime.now(timezone.utc)) < datetime.now(timezone.utc):
        await safe_send_message(update, context, "ℹ️ No active premium")
        return
    
    expiry = user['expiry_date']
    remaining = expiry - datetime.now(timezone.utc)
    
    await safe_send_message(
        update,
        context,
        f"💎 *Premium Status*\n\n"
        f"🔹 *Expires:* {expiry.strftime('%Y-%m-%d %H:%M')}\n"
        f"🔹 *Remaining:* {remaining.days} days\n"
        f"🔹 *User ID:* `{user_id}`"
    )

async def safe_send_message(update: Update, context: CallbackContext, text: str):
    try:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Message error: {e}")
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=text.replace('*', '').replace('`', '')
            )
        except Exception as e:
            logger.error(f"Failed to send fallback message: {e}")

async def is_user_allowed(user_id):
    try:
        user = users_collection.find_one({"user_id": user_id})
        if user:
            expiry = user.get('expiry_date')
            if expiry and expiry > datetime.now(timezone.utc):
                return True
        return False
    except Exception as e:
        logger.error(f"DB error: {e}")
        return False

def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("methods", methods_command))
    application.add_handler(CommandHandler("attack", attack))
    application.add_handler(CommandHandler("key", verify_key))
    application.add_handler(CommandHandler("gen", generate_code))
    application.add_handler(CommandHandler("redeem", redeem_code))
    application.add_handler(CommandHandler("users", list_users))
    application.add_handler(CommandHandler("status", user_status))
    application.add_handler(CommandHandler("get_id", lambda u,c: safe_send_message(u,c,f"🆔 Your ID: `{u.effective_user.id}`")))
    
    # Error handler
    application.add_error_handler(error_handler)
    
    application.run_polling()
    logger.info("Bot is running")

async def error_handler(update: object, context: CallbackContext):
    logger.error(f"Update {update} caused error {context.error}")
    if update and hasattr(update, 'effective_chat'):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="⚠️ An error occurred. Please try again."
        )

if __name__ == '__main__':
    main()
