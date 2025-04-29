import os
import logging
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)

# Configuration
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8087788328:AAHjdilblfkK3YP9oD0elv2GIq25vI2skKI')
CHANNEL_ID = -1002679575112  # Channel where videos are stored
CHANNEL_ID_2 = -1002519127627  # Channel where 2 videos are stored
CHANNEL_ID_3 = -1002641054833  # Channel where 3 videos are stored

VERIFICATION_CHANNEL_ID = -1002436203627  # Channel users must join
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
        await update.message.reply_text("🚫 You are blocked from using this bot.")
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
    asyncio.create_task(notify_admin(context.bot, f"👤 New user:\nID: {user.id}\nUsername: @{user.username}\nName: {user.full_name}"))
    
    welcome_text = """
🎬 <b>Welcome to Video Bot!</b> 🎥

Here you can get access to our exclusive video collection.

⚠️ <b>Important:</b> Videos are protected content and cannot be saved or forwarded.

Please join our channels first to use this bot:
"""
    keyboard = [
        [
            InlineKeyboardButton("Channel 1", url="https://t.me/+RhlQLyOfQ48xMjI1"),
            InlineKeyboardButton("Channel 2", url="https://t.me/+L1iX_sYvsSYzNDI1"),
            InlineKeyboardButton("Channel 3", url="https://t.me/+OOhMrSgdTOdjMGU1")
        ],
        [InlineKeyboardButton("✅ I've Joined", callback_data='check_join')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send welcome message with photo
    sent_message = await update.message.reply_photo(
        photo="https://t.me/bshshsubjsus/7",
        caption=welcome_text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    
    # Schedule welcome message deletion
    delete_task = asyncio.create_task(delete_message_after_delay(sent_message.chat_id, sent_message.message_id, DELETE_AFTER_SECONDS))
    sent_messages[user.id].append((sent_message.chat_id, sent_message.message_id, delete_task))

async def notify_admin(bot, message: str):
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
        await query.edit_message_text(text="🚫 You are blocked from using this bot.")
        return

    if query.data == 'check_join':
        try:
            chat_member = await context.bot.get_chat_member(VERIFICATION_CHANNEL_ID, user_id)
            if chat_member.status in ['member', 'administrator', 'creator']:
                keyboard = [
                    [InlineKeyboardButton("Full sexii Video ♨️", callback_data='videos_1')],
                    [InlineKeyboardButton("Sexi Webseries🥠", callback_data='videos_2')],
                    [InlineKeyboardButton("Movies video🍵", callback_data='videos_3')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_caption(
                    caption="✅ Thanks for joining! Choose a video source:\n\n⚠️ Note: Videos are protected and cannot be saved or forwarded.",
                    reply_markup=reply_markup
                )
            else:
                await query.edit_message_caption(caption="❌ Please join all channels first to access videos.")
        except Exception as e:
            logger.error(f"Error checking membership: {e}")
            await query.edit_message_caption(caption="⚠️ Couldn't verify your channel membership. Please try again /start.")
    
    elif query.data.startswith('videos_'):
        channel_num = query.data.split('_')[1]
        user_progress[user_id] = {
            'last_sent': 0,
            'channel_id': {
                '1': CHANNEL_ID,
                '2': CHANNEL_ID_2,
                '3': CHANNEL_ID_3
            }[channel_num]
        }
        asyncio.create_task(send_batch(context.bot, user_id, query.message.chat.id, channel_num))
    
    elif query.data == 'next':
        channel_num = user_progress[user_id].get('channel_num', '1')
        asyncio.create_task(send_batch(context.bot, user_id, query.message.chat.id, channel_num))

async def send_video_task(bot, user_id, chat_id, msg_id, channel_id):
    """Task to send a single video with error handling and content protection"""
    try:
        async with task_semaphores[user_id]:
            sent_message = await bot.copy_message(
                chat_id=chat_id,
                from_chat_id=channel_id,
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

async def send_batch(bot, user_id, chat_id, channel_num):
    if user_id not in user_progress or 'last_sent' not in user_progress[user_id]:
        user_progress[user_id] = {
            'last_sent': 0,
            'channel_id': {
                '1': CHANNEL_ID,
                '2': CHANNEL_ID_2,
                '3': CHANNEL_ID_3
            }[channel_num],
            'channel_num': channel_num
        }
    
    start_msg = user_progress[user_id]['last_sent']
    end_msg = start_msg + 20
    sent_count = 0
    
    # Create tasks for sending videos
    tasks = []
    for msg_id in range(start_msg + 1, end_msg + 1):
        task = asyncio.create_task(send_video_task(bot, user_id, chat_id, msg_id, user_progress[user_id]['channel_id']))
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
        keyboard = [[InlineKeyboardButton("Next", callback_data='next')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        channel_name = {
            '1': 'Channel 1',
            '2': 'Channel 2',
            '3': 'Channel 3'
        }[channel_num]
        
        control_message = await bot.send_message(
            chat_id=chat_id,
            text=f"Sent {sent_count} protected videos from {channel_name} (will auto-delete in {DELETE_AFTER_SECONDS//60} mins).",
            reply_markup=reply_markup
        )
        # Schedule control message deletion with tracking
        delete_task = asyncio.create_task(delete_message_after_delay(chat_id, control_message.message_id, DELETE_AFTER_SECONDS))
        sent_messages[user_id].append((chat_id, control_message.message_id, delete_task))
    else:
        error_message = await bot.send_message(
            chat_id=chat_id,
            text="No more videos available or failed to send."
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
        f"🤖 <b>Bot Status</b>\n\n"
        f"⏳ <b>Uptime:</b> {days}d {hours}h {minutes}m {seconds}s\n"
        f"👥 <b>Total Users:</b> {total_users}\n"
        f"📊 <b>Active Users:</b> {len(user_progress)}\n"
        f"🚫 <b>Blocked Users:</b> {len(blocked_users)}\n"
        f"🎬 <b>Total Videos Sent:</b> {total_videos}\n"
        f"🔒 <b>Content Protection:</b> Enabled\n"
        f"📅 <b>Last Start:</b> {bot_start_time.strftime('%Y-%m-%d %H:%M:%S')}"
    )
    
    await update.message.reply_text(status_text, parse_mode='HTML')

async def block_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /block <user_id>")
        return
    
    try:
        user_id = int(context.args[0])
        blocked_users.add(user_id)
        await cleanup_user_messages(user_id)
        await cleanup_user_tasks(user_id)
        await update.message.reply_text(f"✅ User {user_id} has been blocked.")
    except ValueError:
        await update.message.reply_text("Invalid user ID. Please provide a numeric ID.")

async def unblock_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /unblock <user_id>")
        return
    
    try:
        user_id = int(context.args[0])
        if user_id in blocked_users:
            blocked_users.remove(user_id)
            await update.message.reply_text(f"✅ User {user_id} has been unblocked.")
        else:
            await update.message.reply_text(f"User {user_id} is not blocked.")
    except ValueError:
        await update.message.reply_text("Invalid user ID. Please provide a numeric ID.")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /broadcast <message>")
        return
    
    message = ' '.join(context.args)
    success = 0
    failed = 0
    
    for user_id in user_progress:
        try:
            await context.bot.send_message(chat_id=user_id, text=message)
            success += 1
            await asyncio.sleep(0.1)  # Rate limiting
        except Exception as e:
            logger.error(f"Failed to send broadcast to {user_id}: {e}")
            failed += 1
    
    await update.message.reply_text(
        f"📢 Broadcast completed:\n"
        f"✅ Success: {success}\n"
        f"❌ Failed: {failed}"
    )

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all users with their details in a .txt file"""
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    if not user_stats:
        await update.message.reply_text("No users found.")
        return
    
    # Create a temporary file
    with open('users_list.txt', 'w', encoding='utf-8') as f:
        f.write("User List:\n\n")
        for user_id, stats in user_stats.items():
            first_seen = stats.get('first_seen', datetime.now())
            last_active = stats.get('last_active', datetime.now())
            usage_time = last_active - first_seen
            days = usage_time.days
            hours, remainder = divmod(usage_time.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            
            f.write(
                f"🆔 ID: {user_id}\n"
                f"👤 Name: {stats.get('full_name', 'N/A')}\n"
                f"📛 Username: @{stats.get('username', 'N/A')}\n"
                f"⏱ Usage Time: {days}d {hours}h {minutes}m\n"
                f"🎬 Videos Watched: {stats.get('video_count', 0)}\n"
                f"📅 First Seen: {first_seen.strftime('%Y-%m-%d %H:%M')}\n"
                f"🔍 Last Active: {last_active.strftime('%Y-%m-%d %H:%M')}\n"
                f"🚫 Blocked: {'Yes' if user_id in blocked_users else 'No'}\n"
                f"────────────────────\n"
            )
    
    # Send the file
    with open('users_list.txt', 'rb') as f:
        await update.message.reply_document(
            document=f,
            caption="Here's the complete user list."
        )

async def user_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show statistics about user activity"""
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    if not user_stats:
        await update.message.reply_text("No user statistics available.")
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
        f"📊 <b>User Statistics</b>\n\n"
        f"👥 <b>Total Users</b>: {len(user_stats)}\n"
        f"🔄 <b>Active Users</b>: {active_users}\n"
        f"🚫 <b>Blocked Users</b>: {len(blocked_users)}\n"
        f"🎬 <b>Total Videos Sent</b>: {total_videos}\n"
        f"📈 <b>Average Videos per User</b>: {avg_videos:.1f}\n\n"
        f"🏆 <b>Top Users by Video Count</b>:\n"
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
                text="Sorry, an error occurred. Please try again later."
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
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
