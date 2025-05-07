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
        max_attempts = count * 10  # Increased attempts for better success
        
        while len(valid_numbers) < count and attempts < max_attempts:
            # Calculate remaining digits needed (total 10 digits including prefix)
            remaining_digits = 10 - len(prefix)
            if remaining_digits <= 0:
                break
                
            random_part = ''.join([str(random.randint(0, 9)) for _ in range(remaining_digits)])
            full_number = f"+91{prefix}{random_part}"
            
            # Validate Indian number format
            if (len(full_number) == 13 and  # +91 + 10 digits
                full_number[3] in '6789' and  # Valid Indian starting digit
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
    
    def check_numbers_from_file(self, filename):
        """Check numbers from file using API"""
        results = []
        try:
            with open(filename, 'r') as f:
                numbers = [line.strip() for line in f if line.strip()]
                
                for number in numbers[:100]:  # Limit to 100 checks per file
                    try:
                        response = requests.get(
                            f"https://newtrue.rishuapi.workers.dev/?number={number}",
                            timeout=3
                        )
                        results.append(f"{number}: {response.json()}")
                    except:
                        results.append(f"{number}: API Error")
        except Exception as e:
            results.append(f"File Error: {str(e)}")
        return results

generator = NumberGenerator()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message"""
    help_text = (
        "📱 *Mobile Number Generator Bot*\n\n"
        "🔹 Generate numbers:\n"
        "`/gen <prefix> <count>`\n"
        "Example: `/gen 976 10`\n\n"
        "🔹 Check numbers from file:\n"
        "`/check` (reply to a .txt file)\n\n"
        "📝 Prefix must be 2-4 digits\n"
        "💾 All numbers saved in .txt files"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def generate_numbers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle number generation"""
    try:
        if len(context.args) < 2:
            await update.message.reply_text("Usage: `/gen <prefix> <count>`\nExample: `/gen 976 10`", parse_mode='Markdown')
            return
        
        prefix = context.args[0]
        count = int(context.args[1])
        
        # Validate prefix
        if not (2 <= len(prefix) <= 4 and prefix.isdigit()):
            await update.message.reply_text("❌ Prefix must be 2-4 digits (e.g. 98, 976, 9999)")
            return
        
        # Validate count
        if count <= 0 or count > 10000:
            await update.message.reply_text("❌ Count must be 1-10000")
            return
        
        # Generate numbers
        numbers = generator.generate_indian_number(prefix, count)
        
        if not numbers:
            await update.message.reply_text("❌ Failed to generate numbers. Try a different prefix or smaller count.")
            return
        
        # Save to file
        filename = generator.save_to_file(prefix, numbers)
        
        # Send results
        preview = "\n".join(numbers[:5])
        msg = f"✅ Generated {len(numbers)} numbers starting with {prefix}:\n\n{preview}"
        if len(numbers) > 5:
            msg += f"\n\n...and {len(numbers)-5} more"
        
        await update.message.reply_text(msg)
        
        # Send file
        with open(filename, 'rb') as f:
            await update.message.reply_document(
                document=f,
                caption=f"Full list of {len(numbers)} numbers"
            )
            
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def check_numbers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle number verification"""
    if not update.message.document and not update.message.reply_to_message:
        await update.message.reply_text("❌ Please reply to a .txt file with `/check`")
        return
    
    try:
        # Get the file
        if update.message.document:
            file = await update.message.document.get_file()
        else:
            if not update.message.reply_to_message.document:
                await update.message.reply_text("❌ Please reply to a .txt file")
                return
            file = await update.message.reply_to_message.document.get_file()
        
        # Download file
        filename = "numbers_to_check.txt"
        await file.download_to_drive(filename)
        
        # Check numbers
        results = generator.check_numbers_from_file(filename)
        
        # Send results
        if not results:
            await update.message.reply_text("❌ No valid numbers found in file")
            return
        
        # Send preview
        preview = "\n".join(results[:5])
        await update.message.reply_text(f"🔍 Verification Results (sample):\n\n{preview}")
        
        # Send full results file
        results_filename = "verification_results.txt"
        with open(results_filename, 'w') as f:
            f.write("\n".join(results))
        
        with open(results_filename, 'rb') as f:
            await update.message.reply_document(
                document=f,
                caption="Full verification results"
            )
            
    except Exception as e:
        await update.message.reply_text(f"❌ Error checking numbers: {str(e)}")

def main():
    """Run the bot"""
    # WARNING: Replace with your actual token
    application = Application.builder().token("7818864949:AAEpqPVZj4oUAl2hFyiTSbZqfbzDr3TQ9fw").build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("gen", generate_numbers))
    application.add_handler(CommandHandler("check", check_numbers))
    
    # Run bot
    application.run_polling()

if __name__ == '__main__':
    main()
