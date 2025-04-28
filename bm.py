import os
import logging
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InputFile
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)

# Configuration
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '7714765260:AAG4yiN5_ow25-feUeKslR2xsdeMFuPllGg')
CHANNEL_ID = -1002441094491  # Channel where videos are stored
VERIFICATION_CHANNEL_ID = -1002512368825  # Channel users must join
ADMIN_IDS = {8167507955}  # Admin user IDs
DELETE_AFTER_SECONDS = 14400  # Auto-delete messages after 4 hours
MAX_CONCURRENT_TASKS = 10  # Limit concurrent video sending tasks per user
MAX_DELETE_RETRIES = 3  # Max attempts to delete a message

# Store user progress and bot data
user_progress = defaultdict(dict)
bot_start_time = datetime.now()
total_users = 0
blocked_users = set()
sent_messages = defaultdict(list)  # {user_id: [(chat_id, message_id, delete_task), ...]}
user_stats = defaultdict(dict)  # {user_id: {'first_seen': datetime, 'last_active': datetime, 'video_count': int}}
user_tasks = defaultdict(list)  # Track active tasks per user
task_semaphores = defaultdict(asyncio.Semaphore)  # Limit concurrent tasks per user

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Global application reference for cleanup tasks
application = None

# Brutal ASCII Art
BRUTAL_ASCII = """
██████╗░██████╗░░█████╗░████████╗░█████╗░██╗░░░░░
██╔══██╗██╔══██╗██╔══██╗╚══██╔══╝██╔══██╗██║░░░░░
██████╦╝██████╔╝██║░░██║░░░██║░░░██║░░██║██║░░░░░
██╔══██╗██╔══██╗██║░░██║░░░██║░░░██║░░██║██║░░░░░
██████╦╝██║░░██║╚█████╔╝░░░██║░░░╚█████╔╝███████╗
╚═════╝░╚═╝░░╚═╝░╚════╝░░░░╚═╝░░░░╚════╝░╚══════╝

░██████╗░███████╗███╗░░██╗███████╗██████╗░██╗░█████╗░███╗░░██╗
██╔════╝░██╔════╝████╗░██║██╔════╝██╔══██╗██║██╔══██╗████╗░██║
██║░░██╗░█████╗░░██╔██╗██║█████╗░░██████╔╝██║██║░░██║██╔██╗██║
██║░░╚██╗██╔══╝░░██║╚████║██╔══╝░░██╔══██╗██║██║░░██║██║╚████║
╚██████╔╝███████╗██║░╚███║███████╗██║░░██║██║╚█████╔╝██║░╚███║
░╚═════╝░╚══════╝╚═╝░░╚══╝╚══════╝╚═╝░░╚═╝╚═╝░╚════╝░╚═╝░░╚══╝
"""

async def delete_message_with_retry(chat_id: int, message_id: int):
    """Delete a message with retry logic"""
    for attempt in range(MAX_DELETE_RETRIES):
        try:
            await application.bot.delete_message(chat_id=chat_id, message_id=message_id)
            logger.info(f"Successfully deleted message {message_id} in chat {chat_id}")
            return True
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1} failed to delete message {message_id}: {e}")
            if attempt < MAX_DELETE_RETRIES - 1:
                await asyncio.sleep(2)  # Wait before retrying
    return False

async def delete_message_after_delay(chat_id: int, message_id: int, delay: int):
    """Delete a message after specified delay with proper error handling"""
    try:
        await asyncio.sleep(delay)
        await delete_message_with_retry(chat_id, message_id)
    except Exception as e:
        logger.error(f"Failed in delete_message_after_delay for message {message_id}: {e}")

async def cleanup_user_messages(user_id: int):
    """Cleanup all scheduled messages for a user"""
    if user_id in sent_messages:
        for chat_id, message_id, delete_task in sent_messages[user_id]:
            try:
                if not delete_task.done():
                    delete_task.cancel()
                await delete_message_with_retry(chat_id, message_id)
            except Exception as e:
                logger.error(f"Failed to cleanup message {message_id} for user {user_id}: {e}")
        sent_messages[user_id].clear()

async def cleanup_user_tasks(user_id: int):
    """Cancel all active tasks for a user"""
    if user_id in user_tasks:
        for task in user_tasks[user_id]:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    logger.error(f"Error in cancelled task for user {user_id}: {e}")
        user_tasks[user_id].clear()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if user.id in blocked_users:
        await update.message.reply_text("🚫 YOU ARE BANNED FROM THIS REALM! 🚫")
        return
    
    global total_users
    if user.id not in user_stats:
        total_users += 1
        user_stats[user.id] = {
            'first_seen': datetime.now(),
            'last_active': datetime.now(),
            'video_count': 0,
            'username': user.username,
            'full_name': user.full_name
        }
    else:
        user_stats[user.id]['last_active'] = datetime.now()
    
    # Initialize semaphore for this user if not exists
    if user.id not in task_semaphores:
        task_semaphores[user.id] = asyncio.Semaphore(MAX_CONCURRENT_TASKS)
    
    # Brutal welcome message
    welcome_text = f"""
╔══════════════════════════════════╗
║  🔥 WELCOME TO THE BRUTAL ZONE! 🔥  ║
╚══════════════════════════════════╝

{BRUTAL_ASCII}

⚡ <b>WARNING:</b> This is a HIGH-SECURITY zone!
🛡️ All content is PROTECTED and TRACKED!

<b>JOIN THESE CHANNELS TO PROCEED:</b>
"""
    keyboard = [
        [
            InlineKeyboardButton("🔥 MAIN CHANNEL", url="https://t.me/+RhlQLyOfQ48xMjI1"),
            InlineKeyboardButton("💀 SECONDARY", url="https://t.me/+ZyYHoZg-qL0zN2Nl")
        ],
        [
            InlineKeyboardButton("☠️ DARK HUB", url="https://t.me/DARKMETHODHUB"),
            InlineKeyboardButton("✅ VERIFY JOIN", callback_data='check_join')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send brutal welcome message with photo
    sent_message = await update.message.reply_photo(
        photo="https://t.me/bshshsubjsus/4",
        caption=welcome_text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    
    # Schedule message deletion
    delete_task = asyncio.create_task(delete_message_after_delay(sent_message.chat_id, sent_message.message_id, DELETE_AFTER_SECONDS))
    sent_messages[user.id].append((sent_message.chat_id, sent_message.message_id, delete_task))

    # Notify admin about new user in a brutal way
    brutal_notification = f"""
☠️ NEW USER ALERT! ☠️
━━━━━━━━━━━━━━━━━━
🆔 ID: <code>{user.id}</code>
👤 NAME: {user.full_name}
📛 USERNAME: @{user.username if user.username else 'N/A'}
⏱ TIME: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
━━━━━━━━━━━━━━━━━━
TOTAL USERS: {total_users}
"""
    asyncio.create_task(notify_admin(context.bot, brutal_notification))

async def notify_admin(bot, message: str):
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                chat_id=admin_id,
                text=message,
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Failed to notify admin {admin_id}: {e}")

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if user_id in blocked_users:
        await query.edit_message_text(text="🚫 YOU HAVE BEEN EXILED FROM THIS REALM!")
        return

    if query.data == 'check_join':
        try:
            chat_member = await context.bot.get_chat_member(VERIFICATION_CHANNEL_ID, user_id)
            if chat_member.status in ['member', 'administrator', 'creator']:
                keyboard = [[InlineKeyboardButton("🔥 GET CONTENT", callback_data='videos')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                brutal_access = """
╔══════════════════════════════════╗
║   ACCESS GRANTED! WELCOME!       ║
╚══════════════════════════════════╝

⚠️ <b>WARNING:</b> All content is:
- PROTECTED 🛡️
- TRACKED 🔍
- AUTO-DELETING 💣
"""
                await query.edit_message_caption(
                    caption=brutal_access,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
            else:
                await query.edit_message_caption(
                    caption="❌ ACCESS DENIED! JOIN ALL CHANNELS FIRST! ❌",
                    parse_mode='HTML'
                )
        except Exception as e:
            logger.error(f"Error checking membership: {e}")
            await query.edit_message_caption(
                caption="⚠️ SYSTEM ERROR! TRY AGAIN WITH /start",
                parse_mode='HTML'
            )
    
    elif query.data == 'videos':
        user_progress[user_id]['last_sent'] = 0
        asyncio.create_task(send_batch(context.bot, user_id, query.message.chat.id))
    
    elif query.data == 'next':
        asyncio.create_task(send_batch(context.bot, user_id, query.message.chat.id))

async def send_video_task(bot, user_id, chat_id, msg_id):
    """Task to send a single video with error handling and content protection"""
    try:
        async with task_semaphores[user_id]:
            sent_message = await bot.copy_message(
                chat_id=chat_id,
                from_chat_id=CHANNEL_ID,
                message_id=msg_id,
                disable_notification=True,
                protect_content=True  # This prevents saving/forwarding
            )
            
            # Update user video count
            if user_id in user_stats:
                user_stats[user_id]['video_count'] = user_stats[user_id].get('video_count', 0) + 1
            
            # Schedule video deletion with proper tracking
            delete_task = asyncio.create_task(delete_message_after_delay(chat_id, sent_message.message_id, DELETE_AFTER_SECONDS))
            sent_messages[user_id].append((chat_id, sent_message.message_id, delete_task))
            
            # Small delay between videos
            await asyncio.sleep(0.3)
            return True
    except Exception as e:
        logger.error(f"Failed to copy message {msg_id} for user {user_id}: {e}")
        return False

async def send_batch(bot, user_id, chat_id):
    if user_id not in user_progress or 'last_sent' not in user_progress[user_id]:
        user_progress[user_id]['last_sent'] = 0
    
    start_msg = user_progress[user_id]['last_sent']
    end_msg = start_msg + 50
    sent_count = 0
    
    # Create tasks for sending videos
    tasks = []
    for msg_id in range(start_msg + 1, end_msg + 1):
        task = asyncio.create_task(send_video_task(bot, user_id, chat_id, msg_id))
        tasks.append(task)
        user_tasks[user_id].append(task)
    
    # Wait for all tasks to complete
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Count successful sends
    sent_count = sum(1 for result in results if result is True)
    
    # Clean up completed tasks
    user_tasks[user_id] = [t for t in user_tasks[user_id] if not t.done()]
    
    if sent_count > 0:
        user_progress[user_id]['last_sent'] = end_msg
        keyboard = [[InlineKeyboardButton("🔥 NEXT BATCH", callback_data='next')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        brutal_batch = f"""
╔══════════════════════════════════╗
║  BATCH DELIVERED! 💣            ║
╚══════════════════════════════════╝

📦 CONTENT: {sent_count} protected files
💣 AUTO-DELETE: {DELETE_AFTER_SECONDS//60} minutes
🛡️ PROTECTION: ACTIVE
"""
        control_message = await bot.send_message(
            chat_id=chat_id,
            text=brutal_batch,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        # Schedule control message deletion with tracking
        delete_task = asyncio.create_task(delete_message_after_delay(chat_id, control_message.message_id, DELETE_AFTER_SECONDS))
        sent_messages[user_id].append((chat_id, control_message.message_id, delete_task))
    else:
        error_message = await bot.send_message(
            chat_id=chat_id,
            text="💀 SYSTEM OVERLOAD! TRY AGAIN LATER!",
            parse_mode='HTML'
        )
        # Schedule error message deletion with tracking
        delete_task = asyncio.create_task(delete_message_after_delay(chat_id, error_message.message_id, DELETE_AFTER_SECONDS))
        sent_messages[user_id].append((chat_id, error_message.message_id, delete_task))

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    uptime = datetime.now() - bot_start_time
    days, seconds = uptime.days, uptime.seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    
    total_videos = sum(stats.get('video_count', 0) for stats in user_stats.values())
    
    brutal_status = f"""
╔══════════════════════════════════╗
║  BRUTAL BOT STATUS 💀            ║
╚══════════════════════════════════╝

⏳ UPTIME: {days}d {hours}h {minutes}m {seconds}s
👥 TOTAL USERS: {total_users}
🔫 BLOCKED USERS: {len(blocked_users)}
🎬 VIDEOS SENT: {total_videos}
🛡️ PROTECTION: ACTIVE
💣 AUTO-DELETE: {DELETE_AFTER_SECONDS//3600}h

⚡ LAST START: {bot_start_time.strftime('%Y-%m-%d %H:%M:%S')}
"""
    await update.message.reply_text(brutal_status, parse_mode='HTML')

async def block_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    if not context.args:
        await update.message.reply_text("💀 USAGE: /block <user_id>")
        return
    
    try:
        user_id = int(context.args[0])
        blocked_users.add(user_id)
        await cleanup_user_messages(user_id)
        await cleanup_user_tasks(user_id)
        
        brutal_block = f"""
╔══════════════════════════════════╗
║  USER TERMINATED! ☠️             ║
╚══════════════════════════════════╝

🆔 ID: {user_id}
⏱ TIME: {datetime.now().strftime('%H:%M:%S')}
"""
        await update.message.reply_text(brutal_block, parse_mode='HTML')
    except ValueError:
        await update.message.reply_text("💀 INVALID USER ID! USE NUMBERS ONLY!")

async def unblock_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    if not context.args:
        await update.message.reply_text("💀 USAGE: /unblock <user_id>")
        return
    
    try:
        user_id = int(context.args[0])
        if user_id in blocked_users:
            blocked_users.remove(user_id)
            brutal_unblock = f"""
╔══════════════════════════════════╗
║  USER PARDONED! 🕊️               ║
╚══════════════════════════════════╝

🆔 ID: {user_id}
⏱ TIME: {datetime.now().strftime('%H:%M:%S')}
"""
            await update.message.reply_text(brutal_unblock, parse_mode='HTML')
        else:
            await update.message.reply_text(f"USER {user_id} IS NOT IN THE BLACKLIST!")
    except ValueError:
        await update.message.reply_text("💀 INVALID USER ID! USE NUMBERS ONLY!")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    if not context.args:
        await update.message.reply_text("💀 USAGE: /broadcast <message>")
        return
    
    message = ' '.join(context.args)
    success = 0
    failed = 0
    
    brutal_header = """
╔══════════════════════════════════╗
║  BRUTAL BROADCAST INITIATED! 📢  ║
╚══════════════════════════════════╝
"""
    await update.message.reply_text(brutal_header, parse_mode='HTML')
    
    progress_msg = await update.message.reply_text("⚡ SENDING TO ALL USERS...")
    
    for user_id in user_stats:
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"📢 ADMIN MESSAGE:\n\n{message}"
            )
            success += 1
            if success % 10 == 0:  # Update progress every 10 sends
                await progress_msg.edit_text(f"⚡ PROGRESS: {success} sent, {failed} failed")
            await asyncio.sleep(0.1)  # Rate limiting
        except Exception as e:
            logger.error(f"Failed to send broadcast to {user_id}: {e}")
            failed += 1
    
    brutal_result = f"""
╔══════════════════════════════════╗
║  BROADCAST COMPLETE! 💥         ║
╚══════════════════════════════════╝

✅ SUCCESS: {success}
❌ FAILED: {failed}
"""
    await progress_msg.delete()
    await update.message.reply_text(brutal_result, parse_mode='HTML')

async def export_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Export all users to a text file"""
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    if not user_stats:
        await update.message.reply_text("💀 NO USERS TO EXPORT!")
        return
    
    # Create a temporary file
    filename = f"users_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("USER EXPORT - BRUTAL BOT\n")
        f.write(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total users: {len(user_stats)}\n")
        f.write("="*50 + "\n\n")
        
        for user_id, stats in user_stats.items():
            f.write(f"🆔 ID: {user_id}\n")
            f.write(f"👤 NAME: {stats.get('full_name', 'N/A')}\n")
            f.write(f"📛 USERNAME: @{stats.get('username', 'N/A')}\n")
            f.write(f"📅 FIRST SEEN: {stats.get('first_seen', 'N/A')}\n")
            f.write(f"⏱ LAST ACTIVE: {stats.get('last_active', 'N/A')}\n")
            f.write(f"🎬 VIDEOS: {stats.get('video_count', 0)}\n")
            f.write(f"🚫 BLOCKED: {'YES' if user_id in blocked_users else 'NO'}\n")
            f.write("-"*50 + "\n")
    
    # Send the file
    with open(filename, 'rb') as f:
        await update.message.reply_document(
            document=InputFile(f),
            caption=f"📊 USER EXPORT: {len(user_stats)} users",
            parse_mode='HTML'
        )
    
    # Clean up
    os.remove(filename)

async def user_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show statistics about user activity"""
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    if not user_stats:
        await update.message.reply_text("💀 NO USER DATA AVAILABLE!")
        return
    
    total_videos = sum(stats.get('video_count', 0) for stats in user_stats.values())
    active_users = len([uid for uid in user_stats if uid not in blocked_users])
    avg_videos = total_videos / len(user_stats) if len(user_stats) > 0 else 0
    
    # Find top users by video count
    top_users = sorted(
        [(uid, stats) for uid, stats in user_stats.items()],
        key=lambda x: x[1].get('video_count', 0),
        reverse=True
    )[:5]
    
    brutal_stats = f"""
╔══════════════════════════════════╗
║  BRUTAL USER STATISTICS 📊       ║
╚══════════════════════════════════╝

👥 TOTAL USERS: {len(user_stats)}
🔥 ACTIVE USERS: {active_users}
💀 BLOCKED USERS: {len(blocked_users)}
🎬 TOTAL VIDEOS SENT: {total_videos}
📈 AVG VIDEOS PER USER: {avg_videos:.1f}

🏆 TOP 5 USERS:
"""
    
    for i, (user_id, stats) in enumerate(top_users, 1):
        brutal_stats += (
            f"{i}. {stats.get('full_name', 'N/A')} (@{stats.get('username', 'N/A')})\n"
            f"   🆔: {user_id} | 🎬: {stats.get('video_count', 0)}\n"
        )
    
    await update.message.reply_text(brutal_stats, parse_mode='HTML')

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(msg="BRUTAL ERROR:", exc_info=context.error)
    
    if update and hasattr(update, 'effective_user'):
        user_id = update.effective_user.id
        try:
            error_message = await context.bot.send_message(
                chat_id=user_id,
                text="💀 SYSTEM MELTDOWN! TRY AGAIN LATER!",
                parse_mode='HTML'
            )
            # Schedule error message deletion
            asyncio.create_task(delete_message_after_delay(error_message.chat_id, error_message.message_id, DELETE_AFTER_SECONDS))
        except Exception:
            pass

def main() -> None:
    global application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # User commands
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(button))
    
    # Admin commands
    application.add_handler(CommandHandler('status', status))
    application.add_handler(CommandHandler('block', block_user))
    application.add_handler(CommandHandler('unblock', unblock_user))
    application.add_handler(CommandHandler('broadcast', broadcast))
    application.add_handler(CommandHandler('export', export_users))  # New export command
    application.add_handler(CommandHandler('stats', user_stats_command))
    
    # Error handler
    application.add_error_handler(error_handler)
    
    # Start the bot with brutal style
    logger.info(BRUTAL_ASCII)
    logger.info("🔥 BRUTAL BOT IS COMING ONLINE! 🔥")
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
