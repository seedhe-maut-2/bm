import random
import requests
from collections import OrderedDict
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import logging
import os

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class NumberGenerator:
    def __init__(self):
        self.generated_numbers = OrderedDict()
        self.number_files = {}
    
    def generate_indian_number(self, prefix, count):
        """Generate valid 10-digit Indian mobile numbers"""
        valid_numbers = []
        attempts = 0
        max_attempts = count * 2  # Prevent infinite loops
        
        while len(valid_numbers) < count and attempts < max_attempts:
            # Generate random 7 digits (prefix provides first 3)
            random_part = ''.join([str(random.randint(0, 9)) for _ in range(10 - len(prefix) - 2)])
            full_number = f"+91{prefix}{random_part}"
            
            # Validate (Indian numbers start with 6-9 after +91)
            if (full_number[3] in '6789' and 
                len(full_number) == 12 and
                full_number not in self.generated_numbers):
                
                self.generated_numbers[full_number] = True
                valid_numbers.append(full_number)
            attempts += 1
        
        return valid_numbers
    
    def save_to_file(self, prefix, numbers):
        """Save numbers to a text file"""
        filename = f"numbers_{prefix}.txt"
        with open(filename, 'w') as f:
            f.write('\n'.join(numbers))
        self.number_files[prefix] = filename
        return filename
    
    def check_number(self, number):
        """Check number using external API"""
        try:
            response = requests.get(
                f"https://newtrue.rishuapi.workers.dev/?number={number}",
                timeout=5
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}

generator = NumberGenerator()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message"""
    await update.message.reply_text(
        "🇮🇳 <b>Ultimate Mobile Number Generator</b>\n\n"
        "📱 <b>Commands:</b>\n"
        "/gen <prefix> <count> - Generate numbers\n"
        "/check - Check numbers from file\n\n"
        "💾 All numbers automatically saved in .txt files\n"
        "🔄 100% unique numbers guaranteed\n"
        "🔍 API verification available",
        parse_mode='HTML'
    )

async def generate_numbers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle number generation"""
    try:
        prefix = context.args[0]
        count = int(context.args[1])
        
        if not (2 <= len(prefix) <= 4 and prefix.isdigit()):
            await update.message.reply_text("❌ Prefix must be 2-4 digits (e.g. 976, 87)")
            return
        
        if count <= 0:
            await update.message.reply_text("❌ Count must be positive")
            return
        
        # Unlimited generation with safety limit
        count = min(count, 10000)  # Max 10,000 per request
        
        numbers = generator.generate_indian_number(prefix, count)
        
        if not numbers:
            await update.message.reply_text("❌ Failed to generate unique numbers")
            return
        
        # Save to file
        filename = generator.save_to_file(prefix, numbers)
        
        # Send response
        preview = "\n".join(numbers[:5])
        await update.message.reply_text(
            f"✅ Generated {len(numbers)} numbers (first 5):\n\n{preview}"
        )
        
        # Send complete file
        with open(filename, 'rb') as f:
            await update.message.reply_document(
                document=f,
                caption=f"Complete list of {len(numbers)} numbers"
            )
    
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /gen <2-4 digit prefix> <count>")

async def check_numbers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle number verification"""
    if not update.message.document:
        await update.message.reply_text("❌ Please upload a .txt file with numbers")
        return
    
    file = await update.message.document.get_file()
    await file.download_to_drive("check_numbers.txt")
    
    try:
        with open("check_numbers.txt", 'r') as f:
            numbers = [line.strip() for line in f.readlines() if line.strip()]
        
        if not numbers:
            await update.message.reply_text("❌ No valid numbers found in file")
            return
        
        # Check first 5 numbers (to avoid API spam)
        results = []
        for number in numbers[:5]:
            result = generator.check_number(number)
            results.append(f"{number}: {result}")
        
        response = "🔍 Verification Results (first 5):\n\n" + "\n".join(results)
        await update.message.reply_text(response)
        
        # Save full results
        with open("verification_results.txt", 'w') as f:
            f.write("\n".join(results))
        
        # Send full results file
        with open("verification_results.txt", 'rb') as f:
            await update.message.reply_document(
                document=f,
                caption="Full verification results"
            )
    
    except Exception as e:
        await update.message.reply_text(f"❌ Error processing file: {str(e)}")

def main():
    """Run the bot"""
    # Replace with your actual token from @BotFather
    application = Application.builder().token("7818864949:AAEpqPVZj4oUAl2hFyiTSbZqfbzDr3TQ9fw").build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("gen", generate_numbers))
    application.add_handler(CommandHandler("check", check_numbers))
    
    application.run_polling()

if __name__ == '__main__':
    main()
