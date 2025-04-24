from telegram import Update
from telegram.ext import Application, MessageHandler, filters
import logging

# लॉगिंग सेटअप
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# टोकन और चैनल आईडी
TOKEN = "8078721946:AAEhV6r0kXnmVaaFnRJgOk__pVjXU1mUd7A"
SOURCE_CHANNEL = -1002512368825  # सोर्स चैनल ID
DESTINATION_CHANNEL = -1002569303552  # डेस्टिनेशन चैनल ID

async def forward_message(update: Update, context):
    try:
        # सिर्फ सोर्स चैनल से मैसेज को फॉरवर्ड करें
        if update.channel_post and update.channel_post.chat.id == SOURCE_CHANNEL:
            # मैसेज को डेस्टिनेशन चैनल में फॉरवर्ड करें
            await context.bot.forward_message(
                chat_id=DESTINATION_CHANNEL,
                from_chat_id=SOURCE_CHANNEL,
                message_id=update.channel_post.message_id
            )
            logger.info(f"Message forwarded from {SOURCE_CHANNEL} to {DESTINATION_CHANNEL}")
    except Exception as e:
        logger.error(f"Error forwarding message: {e}")

def main():
    # Application बनाएं
    application = Application.builder().token(TOKEN).build()
    
    # चैनल पोस्ट हैंडलर जोड़ें (यहाँ सही फिल्टर का उपयोग)
    application.add_handler(MessageHandler(filters.ChatType.CHANNEL, forward_message))
    
    # बॉट स्टार्ट करें
    application.run_polling()
    logger.info("Bot started and listening for channel posts...")

if __name__ == '__main__':
    main()
