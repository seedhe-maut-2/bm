import random
from collections import OrderedDict
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import logging

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class MobileNumberGenerator:
    def __init__(self):
        self.generated_numbers = OrderedDict()
    
    def generate_indian_number(self, prefix, count):
        """Generate valid 10-digit Indian mobile numbers"""
        generated_numbers = []
        attempts = 0
        max_attempts = count * 2  # Prevent infinite loops
        
        while len(generated_numbers) < count and attempts < max_attempts:
            # Generate random 7 digits (prefix provides first 3)
            random_part = ''.join([str(random.randint(0, 9)) for _ in range(7)])
            full_number = f"+91{prefix}{random_part}"
            
            # Validate (Indian numbers start with 6-9 after +91)
            if full_number[3] in '6789' and full_number not in self.generated_numbers:
                self.generated_numbers[full_number] = True
                generated_numbers.append(full_number)
            attempts += 1
        
        return generated_numbers

# Initialize the generator
generator = MobileNumberGenerator()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message"""
    await update.message.reply_text(
        "📱 <b>Indian Mobile Number Generator</b>\n\n"
        "Send: <code>/gen 976 10</code>\n"
        "To generate 10 numbers starting with 976\n\n"
        "<i>Numbers will be valid 10-digit Indian numbers (+91XXXXXXXXXX)</i>",
        parse_mode='HTML'
    )

async def generate_numbers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /gen command"""
    try:
        if len(context.args) < 2:
            await update.message.reply_text("Usage: /gen <prefix> <count>\nExample: /gen 976 10")
            return
        
        prefix = context.args[0]
        count = int(context.args[1])
        
        if not prefix.isdigit() or len(prefix) not in (2, 3, 4):
            await update.message.reply_text("❌ Prefix must be 2-4 digits (e.g., 976, 87, 9999)")
            return
        
        if count <= 0 or count > 1000:
            await update.message.reply_text("❌ Count must be between 1-1000")
            return
        
        # Generate numbers
        numbers = generator.generate_indian_number(prefix, count)
        
        if not numbers:
            await update.message.reply_text("❌ Failed to generate unique numbers. Try a smaller count.")
            return
        
        # Format response
        response = f"✅ Generated {len(numbers)} numbers:\n\n"
        response += "\n".join(numbers[:10])  # Show first 10
        if len(numbers) > 10:
            response += f"\n\n...and {len(numbers)-10} more"
        
        await update.message.reply_text(response)
        
        # Save to file if more than 10 numbers
        if len(numbers) > 10:
            filename = f"numbers_{prefix}.txt"
            with open(filename, 'w') as f:
                f.write("\n".join(numbers))
            with open(filename, 'rb') as f:
                await update.message.reply_document(
                    document=f,
                    caption=f"Full list of {len(numbers)} numbers"
                )
    
    except ValueError:
        await update.message.reply_text("❌ Invalid input. Usage: /gen <prefix> <count>")

def main():
    """Run bot"""
    application = Application.builder().token("YOUR_BOT_TOKEN").build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("gen", generate_numbers))
    
    application.run_polling()

if __name__ == '__main__':
    main()
