import os
import logging
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio
from telegram import (
    InlineKeyboardButton, 
    InlineKeyboardMarkup, 
    Update,
    InputFile
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)
import io

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

# Emoji constants for better readability
EMOJIS = {
    "video": "🎬",
    "user": "👤",
    "admin": "👑",
    "error": "❌",
    "success": "✅",
    "warning": "⚠️",
    "block": "🚫",
    "unblock": "🔓",
    "stats": "📊",
    "time": "⏳",
    "broadcast": "📢",
    "list": "📋",
    "bot": "🤖",
    "channel": "📣",
    "next": "⏭",
    "join": "➕"
}

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
        await update.message.reply_text(f"{EMOJIS['block']} You are blocked from using this bot.")
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
    
    # Notify admin about new user
    asyncio.create_task(notify_admin(
        context.bot, 
        f"{EMOJIS['user']} New user:\n"
        f"🆔 ID: {user.id}\n"
        f"👤 Username: @{user.username}\n"
        f"📛 Name: {user.full_name}"
    ))
    
    welcome_text = f"""
🎬 <b>Welcome to <i>Premium Video Bot</i>!</b> 🎥

Here you can access our exclusive video collection with high-quality content.

{EMOJIS['warning']} <b>Important Notice:</b>
• Videos are protected content
• Forwarding is disabled
• Videos auto-delete after 4 hours

<b>Please join our channels first:</b>
"""
    keyboard = [
        [
            InlineKeyboardButton(f"{EMOJIS['channel']} Main Channel", url="https://t.me/+RhlQLyOfQ48xMjI1"),
            InlineKeyboardButton(f"{EMOJIS['channel']} Backup Channel", url="https://t.me/+ZyYHoZg-qL0zN2Nl")
        ],
        [
            InlineKeyboardButton(f"{EMOJIS['channel']} Discussion", url="https://t.me/DARKMETHODHUB"),
            InlineKeyboardButton(f"{EMOJIS['join']} Verify Join", callback_data='check_join')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send welcome message with photo
    sent_message = await update.message.reply_photo(
        photo="https://t.me/bshshsubjsus/4",
        caption=welcome_text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    
    # Schedule welcome message deletion
    delete_task = asyncio.create_task(delete_message_after_delay(sent_message.chat_id, sent_message.message_id, DELETE_AFTER_SECONDS))
    sent_messages[user.id].append((sent_message.chat_id, sent_message.message_id, delete_task))

async def notify_admin(bot, message: str):
    """Send notification to all admins with error handling"""
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(chat_id=admin_id, text=message)
        except Exception as e:
            logger.error(f"Failed to notify admin {admin_id}: {e}")

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if user_id in blocked_users:
        await query.edit_message_text(text=f"{EMOJIS['block']} You are blocked from using this bot.")
        return

    if query.data == 'check_join':
        try:
            chat_member = await context.bot.get_chat_member(VERIFICATION_CHANNEL_ID, user_id)
            if chat_member.status in ['member', 'administrator', 'creator']:
                keyboard = [[InlineKeyboardButton(f"{EMOJIS['video']} Get Videos", callback_data='videos')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_caption(
                    caption=f"{EMOJIS['success']} <b>Verification Successful!</b>\n\n"
                           "You can now access our video collection.\n\n"
                           f"{EMOJIS['warning']} <i>Note: Videos are protected and will auto-delete.</i>",
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
            else:
                await query.edit_message_caption(
                    caption=f"{EMOJIS['error']} <b>Join Required</b>\n\n"
                           "Please join all channels first to access videos.",
                    parse_mode='HTML'
                )
        except Exception as e:
            logger.error(f"Error checking membership: {e}")
            await query.edit_message_caption(
                caption=f"{EMOJIS['error']} <b>Verification Failed</b>\n\n"
                       "Couldn't verify your channel membership. Please try again /start.",
                parse_mode='HTML'
            )
    
    elif query.data == 'videos':
        user_progress[user_id]['last_sent'] = 0
        await query.edit_message_caption(
            caption=f"{EMOJIS['video']} <b>Preparing your videos...</b>\n\n"
                   "Please wait while we prepare your video collection.",
            parse_mode='HTML'
        )
        asyncio.create_task(send_batch(context.bot, user_id, query.message.chat.id))
    
    elif query.data == 'next':
        await query.edit_message_caption(
            caption=f"{EMOJIS['video']} <b>Loading more videos...</b>",
            parse_mode='HTML'
        )
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
                user_stats[user_id]['last_active'] = datetime.now()
            
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
        keyboard = [[InlineKeyboardButton(f"{EMOJIS['next']} Next Batch", callback_data='next')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        control_message = await bot.send_message(
            chat_id=chat_id,
            text=f"{EMOJIS['success']} Sent {sent_count} protected videos\n"
                 f"{EMOJIS['time']} Auto-delete in {DELETE_AFTER_SECONDS//3600} hours",
            reply_markup=reply_markup
        )
        # Schedule control message deletion with tracking
        delete_task = asyncio.create_task(delete_message_after_delay(chat_id, control_message.message_id, DELETE_AFTER_SECONDS))
        sent_messages[user_id].append((chat_id, control_message.message_id, delete_task))
    else:
        error_message = await bot.send_message(
            chat_id=chat_id,
            text=f"{EMOJIS['error']} No more videos available or failed to send."
        )
        # Schedule error message deletion with tracking
        delete_task = asyncio.create_task(delete_message_after_delay(chat_id, error_message.message_id, DELETE_AFTER_SECONDS))
        sent_messages[user_id].append((chat_id, error_message.message_id, delete_task))

# Admin commands
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    uptime = datetime.now() - bot_start_time
    days, seconds = uptime.days, uptime.seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    
    total_videos = sum(stats.get('video_count', 0) for stats in user_stats.values())
    
    status_text = (
        f"{EMOJIS['bot']} <b>Bot Status</b>\n\n"
        f"{EMOJIS['time']} <b>Uptime:</b> {days}d {hours}h {minutes}m {seconds}s\n"
        f"{EMOJIS['user']} <b>Total Users:</b> {total_users}\n"
        f"{EMOJIS['user']} <b>Active Users:</b> {len(user_progress)}\n"
        f"{EMOJIS['block']} <b>Blocked Users:</b> {len(blocked_users)}\n"
        f"{EMOJIS['video']} <b>Total Videos Sent:</b> {total_videos}\n"
        f"🛡 <b>Content Protection:</b> Enabled\n"
        f"📅 <b>Last Start:</b> {bot_start_time.strftime('%Y-%m-%d %H:%M:%S')}"
    )
    
    await update.message.reply_text(status_text, parse_mode='HTML')

async def block_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    if not context.args:
        await update.message.reply_text(f"{EMOJIS['error']} Usage: /block <user_id>")
        return
    
    try:
        user_id = int(context.args[0])
        blocked_users.add(user_id)
        await cleanup_user_messages(user_id)
        await cleanup_user_tasks(user_id)
        await update.message.reply_text(f"{EMOJIS['success']} User {user_id} has been blocked.")
    except ValueError:
        await update.message.reply_text(f"{EMOJIS['error']} Invalid user ID. Please provide a numeric ID.")

async def unblock_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    if not context.args:
        await update.message.reply_text(f"{EMOJIS['error']} Usage: /unblock <user_id>")
        return
    
    try:
        user_id = int(context.args[0])
        if user_id in blocked_users:
            blocked_users.remove(user_id)
            await update.message.reply_text(f"{EMOJIS['success']} User {user_id} has been unblocked.")
        else:
            await update.message.reply_text(f"{EMOJIS['warning']} User {user_id} is not blocked.")
    except ValueError:
        await update.message.reply_text(f"{EMOJIS['error']} Invalid user ID. Please provide a numeric ID.")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    if not context.args:
        await update.message.reply_text(f"{EMOJIS['error']} Usage: /broadcast <message>")
        return
    
    message = ' '.join(context.args)
    success = 0
    failed = 0
    
    # Add broadcast header
    broadcast_msg = f"{EMOJIS['broadcast']} <b>Announcement</b>\n\n{message}"
    
    for user_id in user_stats:
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=broadcast_msg,
                parse_mode='HTML'
            )
            success += 1
            await asyncio.sleep(0.1)  # Rate limiting
        except Exception as e:
            logger.error(f"Failed to send broadcast to {user_id}: {e}")
            failed += 1
    
    await update.message.reply_text(
        f"{EMOJIS['broadcast']} <b>Broadcast Report</b>\n\n"
        f"{EMOJIS['success']} Success: {success}\n"
        f"{EMOJIS['error']} Failed: {failed}",
        parse_mode='HTML'
    )

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all users with their details in a .txt file"""
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    if not user_stats:
        await update.message.reply_text(f"{EMOJIS['error']} No users found.")
        return
    
    # Create a text file in memory
    file_content = io.StringIO()
    file_content.write("User List\n\n")
    file_content.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    file_content.write(f"Total Users: {len(user_stats)}\n")
    file_content.write(f"Blocked Users: {len(blocked_users)}\n\n")
    
    for user_id, stats in user_stats.items():
        first_seen = stats.get('first_seen', datetime.now())
        last_active = stats.get('last_active', datetime.now())
        usage_time = last_active - first_seen
        days = usage_time.days
        hours, remainder = divmod(usage_time.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        
        file_content.write(
            f"User ID: {user_id}\n"
            f"Name: {stats.get('full_name', 'N/A')}\n"
            f"Username: @{stats.get('username', 'N/A')}\n"
            f"First Seen: {first_seen.strftime('%Y-%m-%d %H:%M')}\n"
            f"Last Active: {last_active.strftime('%Y-%m-%d %H:%M')}\n"
            f"Usage Time: {days}d {hours}h {minutes}m\n"
            f"Videos Watched: {stats.get('video_count', 0)}\n"
            f"Blocked: {'Yes' if user_id in blocked_users else 'No'}\n"
            f"{'-'*40}\n"
        )
    
    # Prepare the file for sending
    file_content.seek(0)
    file_bytes = file_content.getvalue().encode('utf-8')
    file = InputFile(io.BytesIO(file_bytes), filename=f"user_list_{datetime.now().strftime('%Y%m%d')}.txt")
    
    # Send the file with a caption
    await update.message.reply_document(
        document=file,
        caption=f"{EMOJIS['list']} User List\n"
               f"Total Users: {len(user_stats)}\n"
               f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        parse_mode='HTML'
    )

async def user_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show statistics about user activity"""
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    if not user_stats:
        await update.message.reply_text(f"{EMOJIS['error']} No user statistics available.")
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
    
    message = (
        f"{EMOJIS['stats']} <b>User Statistics</b>\n\n"
        f"{EMOJIS['user']} <b>Total Users</b>: {len(user_stats)}\n"
        f"{EMOJIS['user']} <b>Active Users</b>: {active_users}\n"
        f"{EMOJIS['block']} <b>Blocked Users</b>: {len(blocked_users)}\n"
        f"{EMOJIS['video']} <b>Total Videos Sent</b>: {total_videos}\n"
        f"{EMOJIS['stats']} <b>Average Videos per User</b>: {avg_videos:.1f}\n\n"
        f"{EMOJIS['stats']} <b>Top Users by Video Count</b>:\n"
    )
    
    for i, (user_id, stats) in enumerate(top_users, 1):
        message += (
            f"{i}. {stats.get('full_name', 'N/A')} (@{stats.get('username', 'N/A')})\n"
            f"   🆔: {user_id} | 🎬: {stats.get('video_count', 0)}\n"
        )
    
    await update.message.reply_text(message, parse_mode='HTML')

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    
    if update and hasattr(update, 'effective_user'):
        user_id = update.effective_user.id
        try:
            error_message = await context.bot.send_message(
                chat_id=user_id,
                text=f"{EMOJIS['error']} <b>Oops! Something went wrong.</b>\n\n"
                     "Our team has been notified. Please try again later.",
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
    application.add_handler(CommandHandler('users', list_users))
    application.add_handler(CommandHandler('stats', user_stats_command))
    
    # Error handler
    application.add_error_handler(error_handler)
    
    # Start the bot
    logger.info("Starting bot...")
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
