import random
from collections import OrderedDict
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, filters, CallbackContext
import os
import logging

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

class MobileNumberGenerator:
    def __init__(self):
        self.generated_numbers = OrderedDict()
        self.default_filename = "mobile_numbers.txt"
    
    def generate_number(self, pattern):
        """Generate a mobile number based on the pattern"""
        number = []
        for char in pattern:
            if char == '^':
                number.append(str(random.randint(0, 9)))
            else:
                number.append(char)
        return ''.join(number)
    
    def generate_unique_numbers(self, pattern, count, filename=None):
        """Generate unique mobile numbers and return them as a list"""
        if filename is None:
            filename = self.default_filename
        
        digits_needed = pattern.count('^')
        total_possible = 10 ** digits_needed
        
        if count > total_possible:
            count = total_possible
        
        generated_numbers = []
        generated = 0
        
        while generated < count:
            num = self.generate_number(pattern)
            if num not in self.generated_numbers:
                self.generated_numbers[num] = True
                generated_numbers.append(num)
                generated += 1
        
        return generated_numbers

# Initialize the generator
generator = MobileNumberGenerator()

# Telegram bot commands
def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    welcome_msg = (
        f"Hi {user.first_name}! 👋\n\n"
        "I'm Mobile Number Generator Bot 🤖\n\n"
        "📱 Send me commands like:\n"
        "/gen +91976^^^^^^ 10 - To generate 10 numbers starting with +91976\n"
        "/gen +91754^^^^^^ 5  - To generate 5 numbers starting with +91754\n\n"
        "Each '^' will be replaced with a random digit\n"
        "Example: +91976^^^^^^ creates 10-digit numbers"
    )
    update.message.reply_text(welcome_msg)

def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    help_text = (
        "🆘 <b>Help Guide</b> 🆘\n\n"
        "🔹 <b>Generate Numbers</b>:\n"
        "<code>/gen +91976^^^^^^ 10</code> - Generates 10 numbers starting with +91976\n\n"
        "🔹 <b>Pattern Rules</b>:\n"
        "- Must start with country code (e.g., +91)\n"
        "- Use ^ symbols for random digits\n"
        "- Example: +91754^^^^^^ generates 10-digit numbers\n\n"
        "🔹 <b>Other Commands</b>:\n"
        "/start - Show welcome message\n"
        "/stats - Show generation statistics\n"
        "/clear - Clear all generated numbers from memory"
    )
    update.message.reply_text(help_text, parse_mode='HTML')

def generate_numbers(update: Update, context: CallbackContext) -> None:
    """Generate mobile numbers based on user pattern"""
    try:
        if len(context.args) < 2:
            update.message.reply_text("⚠️ Usage: /gen +91976^^^^^^ 10")
            return
        
        pattern = context.args[0]
        count = int(context.args[1])
        
        if count <= 0:
            update.message.reply_text("❌ Count must be greater than 0")
            return
        
        if not pattern.startswith('+') or '^' not in pattern:
            update.message.reply_text("❌ Invalid pattern. Must start with '+' and contain '^'")
            return
        
        # Calculate expected length for Indian numbers (+91 + 10 digits)
        if len(pattern.replace('^', '0')) != 12 or pattern.count('^') != 10 - (len(pattern) - pattern.count('^') - 3):
            update.message.reply_text("⚠️ Note: Pattern should result in 10-digit Indian numbers (+91XXXXXXXXXX)")
        
        numbers = generator.generate_unique_numbers(pattern, count)
        
        if not numbers:
            update.message.reply_text("❌ No numbers generated. Try a different pattern.")
            return
        
        # Send first 10 numbers in message (Telegram has message length limits)
        preview = "\n".join(numbers[:10])
        if len(numbers) > 10:
            preview += f"\n\n...and {len(numbers)-10} more numbers"
        
        # Save all numbers to file
        filename = f"numbers_{pattern[:6]}.txt"
        with open(filename, 'w') as f:
            f.write("\n".join(numbers))
        
        # Send response
        update.message.reply_text(
            f"✅ Generated {len(numbers)} unique numbers:\n\n{preview}"
        )
        
        # Send the complete file
        with open(filename, 'rb') as f:
            update.message.reply_document(
                document=f,
                caption=f"Complete list of {len(numbers)} numbers"
            )
        
    except (ValueError, IndexError):
        update.message.reply_text("⚠️ Invalid command format. Use: /gen +91976^^^^^^ 10")

def stats_command(update: Update, context: CallbackContext) -> None:
    """Show generation statistics"""
    if not generator.generated_numbers:
        update.message.reply_text("ℹ️ No numbers generated yet")
        return
    
    patterns = {}
    for num in generator.generated_numbers:
        prefix = num[:7]  # Get the base pattern (+91976 or +91754 etc.)
        patterns[prefix] = patterns.get(prefix, 0) + 1
    
    stats_msg = "📊 Generation Statistics:\n\n"
    for pattern, count in patterns.items():
        stats_msg += f"{pattern}******: {count} numbers\n"
    
    update.message.reply_text(stats_msg)

def clear_command(update: Update, context: CallbackContext) -> None:
    """Clear all generated numbers from memory"""
    generator.generated_numbers.clear()
    update.message.reply_text("♻️ All generated numbers cleared from memory")

def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater("7818864949:AAEpqPVZj4oUAl2hFyiTSbZqfbzDr3TQ9fw")

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("gen", generate_numbers))
    dispatcher.add_handler(CommandHandler("stats", stats_command))
    dispatcher.add_handler(CommandHandler("clear", clear_command))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C
    updater.idle()

if __name__ == '__main__':
    main()
