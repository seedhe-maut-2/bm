from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import logging
import asyncio

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
TOKEN = "8078721946:AAEhV6r0kXnmVaaFnRJgOk__pVjXU1mUd7A"
SOURCE_CHANNEL = -1002689206991  # Source channel ID
DESTINATION_CHANNEL = -1002569303552  # Destination channel ID
FORWARD_OLD_POSTS = True  # Set to False if you don't want to forward old posts
MAX_OLD_MESSAGES = 1000  # Maximum number of old messages to forward
DELAY_BETWEEN_FORWARDS = 1  # Delay in seconds between forwarding messages

async def forward_single_message(context, message_id):
    try:
        await context.bot.forward_message(
            chat_id=DESTINATION_CHANNEL,
            from_chat_id=SOURCE_CHANNEL,
            message_id=message_id
        )
        logger.info(f"Forwarded message {message_id}")
        await asyncio.sleep(DELAY_BETWEEN_FORWARDS)  # Add delay to avoid rate limits
    except Exception as e:
        logger.error(f"Error forwarding message {message_id}: {e}")

async def forward_all_existing_posts(application):
    if not FORWARD_OLD_POSTS:
        return
        
    logger.info("Starting to forward old posts...")
    try:
        # Get all available messages
        messages = []
        async for message in application.bot.get_chat_history(
            chat_id=SOURCE_CHANNEL,
            limit=MAX_OLD_MESSAGES
        ):
            messages.append(message)
        
        # Forward messages in reverse order (oldest first)
        for message in reversed(messages):
            await forward_single_message(application, message.message_id)
            
    except Exception as e:
        logger.error(f"Error in forwarding old posts: {e}")

async def handle_new_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.channel_post and update.channel_post.chat.id == SOURCE_CHANNEL:
        await forward_single_message(context, update.channel_post.message_id)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Bot is running! New posts will be forwarded automatically."
    )

def main():
    # Create application
    application = Application.builder().token(TOKEN).build()
    
    # Add handlers
    application.add_handler(MessageHandler(
        filters.ChatType.CHANNEL & filters.Chat(SOURCE_CHANNEL), 
        handle_new_post
    ))
    application.add_handler(CommandHandler("start", start))
    
    # Forward old posts on startup
    application.add_handler(CommandHandler(
        "forward_old", 
        lambda u,c: forward_all_existing_posts(c.application)
    ))
    
    # Run the bot
    application.run_polling()
    logger.info("Bot started and listening for channel posts...")
    
    # Auto-forward old posts when bot starts
    if FORWARD_OLD_POSTS:
        application.create_task(forward_all_existing_posts(application))

if __name__ == '__main__':
    main()
