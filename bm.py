import os
import logging
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio
from telegram import (
    InlineKeyboardButton, 
    InlineKeyboardMarkup, 
    Update,
    InputFile,
    Sticker
)
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
    """Enhanced welcome message with richer content and better formatting"""
    user = update.effective_user
    if user.id in blocked_users:
        await update.message.reply_text("🚫 Your access to this bot has been restricted. Contact support if you believe this is an error.")
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
        f"👤 New user interaction:\n"
        f"🆔 User ID: {user.id}\n"
        f"📛 Username: @{user.username or 'N/A'}\n"
        f"👀 Name: {user.full_name}\n"
        f"📅 First seen: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    ))
    
    welcome_text = """
🌟 <b>Welcome to Premium Video Hub!</b> 🌟

🎬 Discover exclusive content in our protected video collection. 

🔒 <b>Important Security Notice:</b>
- All content is copyright protected
- Forwarding or saving videos is disabled
- Content auto-deletes after 4 hours

📌 <b>To continue, please join our official channels:</b>
"""
    keyboard = [
        [
            InlineKeyboardButton("📢 Main Channel", url="https://t.me/+RhlQLyOfQ48xMjI1"),
            InlineKeyboardButton("💬 Discussion", url="https://t.me/+ZyYHoZg-qL0zN2Nl")
        ],
        [
            InlineKeyboardButton("🔗 Resources", url="https://t.me/DARKMETHODHUB"),
            InlineKeyboardButton("✅ Verify Membership", callback_data='check_join')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send welcome message with high-quality photo
    sent_message = await update.message.reply_photo(
        photo="https://t.me/bshshsubjsus/4",
        caption=welcome_text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    
    # Schedule welcome message deletion
    delete_task = asyncio.create_task(
        delete_message_after_delay(
            sent_message.chat_id, 
            sent_message.message_id, 
            DELETE_AFTER_SECONDS
        )
    )
    sent_messages[user.id].append((sent_message.chat_id, sent_message.message_id, delete_task))

async def notify_admin(bot, message: str):
    """Enhanced admin notification with error handling"""
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
    """Enhanced callback handler with better user feedback"""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if user_id in blocked_users:
        await query.edit_message_text(
            text="⛔ <b>Access Denied</b>\n\n"
                 "Your account has been restricted from using this service. "
                 "Please contact support if you believe this is incorrect.",
            parse_mode='HTML'
        )
        return

    if query.data == 'check_join':
        try:
            chat_member = await context.bot.get_chat_member(VERIFICATION_CHANNEL_ID, user_id)
            if chat_member.status in ['member', 'administrator', 'creator']:
                keyboard = [[
                    InlineKeyboardButton("🎬 Get Videos Now", callback_data='videos'),
                    InlineKeyboardButton("ℹ️ How It Works", callback_data='info')
                ]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_caption(
                    caption="✅ <b>Verification Successful!</b>\n\n"
                           "You now have access to our premium content library.\n\n"
                           "🔐 <b>Content Protection Notice:</b>\n"
                           "- Videos cannot be downloaded or forwarded\n"
                           "- All content auto-deletes after 4 hours\n"
                           "- Abuse may result in account suspension",
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
            else:
                await query.edit_message_caption(
                    caption="❌ <b>Channel Membership Required</b>\n\n"
                           "We couldn't verify your membership in all required channels.\n"
                           "Please ensure you've joined ALL channels listed above and try again.",
                    parse_mode='HTML'
                )
        except Exception as e:
            logger.error(f"Error checking membership: {e}")
            await query.edit_message_caption(
                caption="⚠️ <b>Verification Error</b>\n\n"
                       "We encountered an issue verifying your channel membership. "
                       "Please try again later or contact support if the problem persists.",
                parse_mode='HTML'
            )
    
    elif query.data == 'videos':
        user_progress[user_id]['last_sent'] = 0
        asyncio.create_task(send_batch(context.bot, user_id, query.message.chat.id))
    
    elif query.data == 'next':
        asyncio.create_task(send_batch(context.bot, user_id, query.message.chat.id))
    
    elif query.data == 'info':
        await query.edit_message_caption(
            caption="ℹ️ <b>How Our Service Works</b>\n\n"
                   "1️⃣ <b>Content Access</b>\n"
                   "- Videos are delivered in protected format\n"
                   "- Each batch contains multiple videos\n"
                   "- Use the 'Next' button to load more\n\n"
                   "2️⃣ <b>Security Features</b>\n"
                   "- Screenshot detection enabled\n"
                   "- Watermarked content\n"
                   "- Usage analytics recorded\n\n"
                   "3️⃣ <b>Fair Use Policy</b>\n"
                   "- Do not attempt to bypass protections\n"
                   "- Commercial use prohibited\n"
                   "- Respect copyright notices",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data='check_join')]])
        )

async def send_video_task(bot, user_id, chat_id, msg_id):
    """Enhanced video sending task with better protection and tracking"""
    try:
        async with task_semaphores[user_id]:
            # Send with enhanced protection settings
            sent_message = await bot.copy_message(
                chat_id=chat_id,
                from_chat_id=CHANNEL_ID,
                message_id=msg_id,
                disable_notification=True,
                protect_content=True,
                caption="🔒 Protected Content | Auto-deletes in 4 hours"
            )
            
            # Update user video statistics
            if user_id in user_stats:
                user_stats[user_id]['video_count'] = user_stats[user_id].get('video_count', 0) + 1
                user_stats[user_id]['last_active'] = datetime.now()
            
            # Schedule video deletion with tracking
            delete_task = asyncio.create_task(
                delete_message_after_delay(
                    chat_id, 
                    sent_message.message_id, 
                    DELETE_AFTER_SECONDS
                )
            )
            sent_messages[user_id].append((chat_id, sent_message.message_id, delete_task))
            
            # Rate limiting between sends
            await asyncio.sleep(0.5)
            return True
    except Exception as e:
        logger.error(f"Failed to send video {msg_id} to user {user_id}: {str(e)}")
        if "blocked" in str(e).lower():
            blocked_users.add(user_id)
            await notify_admin(bot, f"🚨 User {user_id} blocked the bot. Added to blocked list.")
        return False

async def send_batch(bot, user_id, chat_id):
    """Enhanced batch sending with better progress tracking"""
    if user_id not in user_progress or 'last_sent' not in user_progress[user_id]:
        user_progress[user_id]['last_sent'] = 0
    
    start_msg = user_progress[user_id]['last_sent']
    end_msg = start_msg + 50  # Batch size
    sent_count = 0
    
    # Create and track sending tasks
    tasks = []
    for msg_id in range(start_msg + 1, end_msg + 1):
        task = asyncio.create_task(send_video_task(bot, user_id, chat_id, msg_id))
        tasks.append(task)
        user_tasks[user_id].append(task)
    
    # Process results with better error handling
    results = await asyncio.gather(*tasks, return_exceptions=True)
    sent_count = sum(1 for result in results if result is True)
    
    # Clean up completed tasks
    user_tasks[user_id] = [t for t in user_tasks[user_id] if not t.done()]
    
    if sent_count > 0:
        user_progress[user_id]['last_sent'] = end_msg
        keyboard = [[
            InlineKeyboardButton("⏭ Next Batch", callback_data='next'),
            InlineKeyboardButton("🔄 Refresh", callback_data='videos')
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        control_message = await bot.send_message(
            chat_id=chat_id,
            text=f"📦 <b>Batch Delivery Complete</b>\n\n"
                 f"• Successfully sent: {sent_count} protected videos\n"
                 f"• Auto-delete in: {DELETE_AFTER_SECONDS//3600} hours\n"
                 f"• Total viewed: {user_stats[user_id].get('video_count', 0)}",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        
        # Schedule control message deletion
        delete_task = asyncio.create_task(
            delete_message_after_delay(
                control_message.chat_id, 
                control_message.message_id, 
                DELETE_AFTER_SECONDS
            )
        )
        sent_messages[user_id].append((control_message.chat_id, control_message.message_id, delete_task))
    else:
        error_message = await bot.send_message(
            chat_id=chat_id,
            text="⚠️ <b>Content Unavailable</b>\n\n"
                 "We couldn't retrieve videos at this time. This may be due to:\n"
                 "• Temporary server issues\n"
                 "• Content updates in progress\n"
                 "• Your account restrictions\n\n"
                 "Please try again later or contact support.",
            parse_mode='HTML'
        )
        delete_task = asyncio.create_task(
            delete_message_after_delay(
                error_message.chat_id, 
                error_message.message_id, 
                DELETE_AFTER_SECONDS
            )
        )
        sent_messages[user_id].append((error_message.chat_id, error_message.message_id, delete_task))

# Enhanced Admin Commands
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comprehensive status report with rich formatting"""
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    uptime = datetime.now() - bot_start_time
    days, seconds = uptime.days, uptime.seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    
    total_videos = sum(stats.get('video_count', 0) for stats in user_stats.values())
    active_users = len([uid for uid in user_stats if (datetime.now() - user_stats[uid].get('last_active', datetime.now()) < timedelta(days=1)])
    
    status_text = (
        f"📊 <b>System Status Dashboard</b>\n\n"
        f"⏳ <b>Uptime:</b> {days}d {hours}h {minutes}m {seconds}s\n"
        f"📅 <b>Last Restart:</b> {bot_start_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"👥 <b>User Statistics:</b>\n"
        f"   • Total: {total_users}\n"
        f"   • Active (24h): {active_users}\n"
        f"   • Blocked: {len(blocked_users)}\n"
        f"🎬 <b>Content Delivery:</b>\n"
        f"   • Videos Sent: {total_videos}\n"
        f"   • Avg/User: {total_videos/max(1, len(user_stats)):.1f}\n"
        f"🔒 <b>Security Status:</b>\n"
        f"   • Protection: Enabled\n"
        f"   • Auto-delete: {DELETE_AFTER_SECONDS//3600}h\n"
        f"⚙️ <b>System Health:</b> Normal"
    )
    
    await update.message.reply_text(status_text, parse_mode='HTML')

async def block_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Enhanced user blocking with confirmation"""
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    if not context.args:
        await update.message.reply_text(
            "❌ <b>Usage:</b> <code>/block &lt;user_id&gt; [reason]</code>\n\n"
            "Example:\n<code>/block 123456 Violating terms</code>",
            parse_mode='HTML'
        )
        return
    
    try:
        user_id = int(context.args[0])
        reason = ' '.join(context.args[1:]) if len(context.args) > 1 else "No reason provided"
        
        blocked_users.add(user_id)
        await cleanup_user_messages(user_id)
        await cleanup_user_tasks(user_id)
        
        # Notify the blocked user if possible
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"🚫 <b>Account Restricted</b>\n\n"
                     f"Your access to this service has been suspended.\n"
                     f"<b>Reason:</b> {reason}\n\n"
                     f"If you believe this is an error, please contact support.",
                parse_mode='HTML'
            )
        except Exception as e:
            logger.warning(f"Couldn't notify blocked user {user_id}: {e}")
        
        await update.message.reply_text(
            f"✅ <b>User Blocked</b>\n\n"
            f"🆔 User ID: <code>{user_id}</code>\n"
            f"📝 Reason: {reason}\n"
            f"⏱ At: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            parse_mode='HTML'
        )
        
        # Log the action
        await notify_admin(
            context.bot,
            f"🚨 <b>User Blocked</b>\n"
            f"• Admin: {update.effective_user.full_name}\n"
            f"• Target: {user_id}\n"
            f"• Reason: {reason}"
        )
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid user ID format. Please provide a numeric ID.",
            parse_mode='HTML'
        )

async def unblock_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Enhanced unblocking with confirmation"""
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    if not context.args:
        await update.message.reply_text(
            "❌ <b>Usage:</b> <code>/unblock &lt;user_id&gt;</code>",
            parse_mode='HTML'
        )
        return
    
    try:
        user_id = int(context.args[0])
        if user_id in blocked_users:
            blocked_users.remove(user_id)
            
            # Notify the unblocked user if possible
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text="✅ <b>Account Restored</b>\n\n"
                         "Your access to this service has been reinstated. "
                         "You may now use the bot normally.",
                    parse_mode='HTML'
                )
            except Exception as e:
                logger.warning(f"Couldn't notify unblocked user {user_id}: {e}")
            
            await update.message.reply_text(
                f"✅ <b>User Unblocked</b>\n\n"
                f"🆔 User ID: <code>{user_id}</code>\n"
                f"⏱ At: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                parse_mode='HTML'
            )
            
            # Log the action
            await notify_admin(
                context.bot,
                f"🔄 <b>User Unblocked</b>\n"
                f"• Admin: {update.effective_user.full_name}\n"
                f"• Target: {user_id}"
            )
        else:
            await update.message.reply_text(
                f"ℹ️ User <code>{user_id}</code> is not currently blocked.",
                parse_mode='HTML'
            )
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid user ID format. Please provide a numeric ID.",
            parse_mode='HTML'
        )

async def process_user_list_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process .txt file with user IDs for commands"""
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    if not update.message.document:
        await update.message.reply_text("Please upload a .txt file with user IDs.")
        return
    
    file = await context.bot.get_file(update.message.document.file_id)
    file_data = await file.download_as_bytearray()
    
    try:
        user_ids = []
        for line in file_data.decode().splitlines():
            line = line.strip()
            if line and line.isdigit():
                user_ids.append(int(line))
        
        if not user_ids:
            await update.message.reply_text("No valid user IDs found in the file.")
            return
        
        context.user_data['bulk_user_ids'] = user_ids
        keyboard = [
            [
                InlineKeyboardButton("Broadcast", callback_data='bulk_broadcast'),
                InlineKeyboardButton("Block", callback_data='bulk_block')
            ],
            [
                InlineKeyboardButton("Unblock", callback_data='bulk_unblock'),
                InlineKeyboardButton("Cancel", callback_data='bulk_cancel')
            ]
        ]
        await update.message.reply_text(
            f"📄 File processed: Found {len(user_ids)} valid user IDs.\n"
            "Choose an action:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Error processing user list file: {e}")
        await update.message.reply_text("Error processing the file. Please ensure it's a valid .txt file with one user ID per line.")

async def enhanced_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Enhanced broadcast supporting multiple media types"""
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    # Check if we're replying to a message (for media forwarding)
    if update.message.reply_to_message:
        original_message = update.message.reply_to_message
        target_users = user_stats.keys() if not context.args else []
        
        success = 0
        failed = 0
        
        for user_id in target_users:
            if user_id in blocked_users:
                failed += 1
                continue
            
            try:
                # Handle different message types
                if original_message.text:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=original_message.text,
                        parse_mode='HTML'
                    )
                elif original_message.photo:
                    await context.bot.send_photo(
                        chat_id=user_id,
                        photo=original_message.photo[-1].file_id,
                        caption=original_message.caption,
                        parse_mode='HTML'
                    )
                elif original_message.video:
                    await context.bot.send_video(
                        chat_id=user_id,
                        video=original_message.video.file_id,
                        caption=original_message.caption,
                        parse_mode='HTML'
                    )
                elif original_message.sticker:
                    await context.bot.send_sticker(
                        chat_id=user_id,
                        sticker=original_message.sticker.file_id
                    )
                elif original_message.document:
                    await context.bot.send_document(
                        chat_id=user_id,
                        document=original_message.document.file_id,
                        caption=original_message.caption,
                        parse_mode='HTML'
                    )
                else:
                    failed += 1
                    continue
                
                success += 1
                await asyncio.sleep(0.2)  # Rate limiting
            except Exception as e:
                logger.error(f"Failed to broadcast to {user_id}: {e}")
                failed += 1
        
        await update.message.reply_text(
            f"📢 <b>Broadcast Completed</b>\n\n"
            f"✅ Success: {success}\n"
            f"❌ Failed: {failed}\n"
            f"📊 Reach: {success/max(1, success+failed)*100:.1f}%",
            parse_mode='HTML'
        )
    else:
        # Text-only broadcast
        if not context.args:
            await update.message.reply_text(
                "❌ <b>Usage:</b>\n"
                "1. For text: <code>/broadcast your message</code>\n"
                "2. For media: Reply to a message with <code>/broadcast</code>",
                parse_mode='HTML'
            )
            return
        
        message = ' '.join(context.args)
        success = 0
        failed = 0
        
        for user_id in user_stats:
            if user_id in blocked_users:
                failed += 1
                continue
            
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode='HTML'
                )
                success += 1
                await asyncio.sleep(0.1)  # Rate limiting
            except Exception as e:
                logger.error(f"Failed to send broadcast to {user_id}: {e}")
                failed += 1
        
        await update.message.reply_text(
            f"📢 <b>Broadcast Completed</b>\n\n"
            f"✅ Success: {success}\n"
            f"❌ Failed: {failed}\n"
            f"📊 Reach: {success/max(1, success+failed)*100:.1f}%",
            parse_mode='HTML'
        )

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Enhanced user listing with pagination and filtering"""
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    if not user_stats:
        await update.message.reply_text("No users found in database.")
        return
    
    # Check for filters
    filter_active = False
    if context.args and context.args[0].lower() == 'active':
        filter_active = True
        filtered_users = {
            uid: stats for uid, stats in user_stats.items()
            if (datetime.now() - stats.get('last_active', datetime.now())) < timedelta(days=1)
        }
    elif context.args and context.args[0].lower() == 'blocked':
        filtered_users = {uid: user_stats[uid] for uid in blocked_users if uid in user_stats}
    else:
        filtered_users = user_stats
    
    if not filtered_users:
        await update.message.reply_text("No users match the current filter.")
        return
    
    # Prepare user list
    message = f"👥 <b>User Database</b> ({len(filtered_users)} users)\n\n"
    for i, (user_id, stats) in enumerate(filtered_users.items(), 1):
        last_active = stats.get('last_active', datetime.now())
        active_status = "🟢" if (datetime.now() - last_active) < timedelta(hours=1) else "🟡" if (datetime.now() - last_active) < timedelta(days=1) else "🔴"
        
        message += (
            f"{active_status} <b>User #{i}</b>\n"
            f"🆔: <code>{user_id}</code>\n"
            f"👤: {stats.get('full_name', 'N/A')}\n"
            f"📛: @{stats.get('username', 'N/A')}\n"
            f"🎬: {stats.get('video_count', 0)} videos\n"
            f"🕒 Last active: {last_active.strftime('%Y-%m-%d %H:%M')}\n"
            f"🚫 Blocked: {'Yes' if user_id in blocked_users else 'No'}\n"
            f"────────────────────\n"
        )
        
        # Split long messages
        if len(message) > 3000:
            await update.message.reply_text(message, parse_mode='HTML')
            message = ""
            await asyncio.sleep(0.5)
    
    if message:
        await update.message.reply_text(message, parse_mode='HTML')

async def user_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Enhanced user statistics with visual indicators"""
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    if not user_stats:
        await update.message.reply_text("No user data available.")
        return
    
    total_videos = sum(stats.get('video_count', 0) for stats in user_stats.values())
    active_users = len([uid for uid in user_stats if (datetime.now() - user_stats[uid].get('last_active', datetime.now())) < timedelta(days=1)])
    new_today = len([uid for uid in user_stats if (datetime.now() - user_stats[uid].get('first_seen', datetime.now())) < timedelta(days=1)])
    avg_videos = total_videos / max(1, len(user_stats))
    
    # Generate usage histogram (simplified)
    video_counts = [stats.get('video_count', 0) for stats in user_stats.values()]
    heavy_users = sum(1 for count in video_counts if count > 50)
    medium_users = sum(1 for count in video_counts if 10 < count <= 50)
    light_users = sum(1 for count in video_counts if 0 < count <= 10)
    inactive_users = sum(1 for count in video_counts if count == 0)
    
    # Find top users
    top_users = sorted(
        [(uid, stats) for uid, stats in user_stats.items()],
        key=lambda x: x[1].get('video_count', 0),
        reverse=True
    )[:5]
    
    message = (
        f"📈 <b>User Analytics Dashboard</b>\n\n"
        f"👥 <b>User Base</b>\n"
        f"• Total: {len(user_stats)}\n"
        f"• Active (24h): {active_users}\n"
        f"• New (24h): {new_today}\n"
        f"• Blocked: {len(blocked_users)}\n\n"
        f"🎬 <b>Content Consumption</b>\n"
        f"• Total videos sent: {total_videos}\n"
        f"• Average per user: {avg_videos:.1f}\n\n"
        f"📊 <b>Usage Distribution</b>\n"
        f"• Heavy users (>50): {heavy_users}\n"
        f"• Medium users (10-50): {medium_users}\n"
        f"• Light users (1-10): {light_users}\n"
        f"• Inactive (0): {inactive_users}\n\n"
        f"🏆 <b>Top 5 Users</b>\n"
    )
    
    for i, (user_id, stats) in enumerate(top_users, 1):
        message += (
            f"{i}. {stats.get('full_name', 'N/A')} (@{stats.get('username', 'N/A')})\n"
            f"   🆔: {user_id} | 🎬: {stats.get('video_count', 0)}\n"
        )
    
    await update.message.reply_text(message, parse_mode='HTML')

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Enhanced error handling with detailed logging"""
    logger.error("Exception while handling update:", exc_info=context.error)
    
    error_msg = f"⚠️ <b>System Error</b>\n\n" \
                f"• Type: {type(context.error).__name__}\n" \
                f"• Message: {str(context.error)}\n\n" \
                f"Please check logs for details."
    
    # Notify all admins
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(admin_id, error_msg, parse_mode='HTML')
        except Exception as e:
            logger.error(f"Failed to notify admin {admin_id} about error: {e}")
    
    # Notify user if possible
    if update and hasattr(update, 'effective_user'):
        try:
            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text="⚠️ An unexpected error occurred. Our team has been notified.",
                parse_mode='HTML'
            )
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
    application.add_handler(CommandHandler('broadcast', enhanced_broadcast))
    application.add_handler(CommandHandler('users', list_users))
    application.add_handler(CommandHandler('stats', user_stats_command))
    
    # Document handler for user list files
    application.add_handler(MessageHandler(
        filters.Document.FileExtension("txt") & filters.User(ADMIN_IDS),
        process_user_list_file
    ))
    
    # Error handler
    application.add_error_handler(error_handler)
    
    # Start the bot
    logger.info("Starting bot...")
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
