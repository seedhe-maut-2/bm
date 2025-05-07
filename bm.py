import random
import requests
import time
from collections import OrderedDict
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import logging
import os
from typing import List, Dict

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
    
    def generate_indian_number(self, prefix: str, count: int) -> List[str]:
        """Generate valid 10-digit Indian mobile numbers"""
        valid_numbers = []
        attempts = 0
        max_attempts = count * 10
        
        while len(valid_numbers) < count and attempts < max_attempts:
            remaining_digits = 10 - len(prefix)
            random_part = ''.join([str(random.randint(0, 9)) for _ in range(remaining_digits)])
            full_number = f"+91{prefix}{random_part}"
            
            if (len(full_number) == 13 and
                full_number[3] in '6789' and
                full_number not in self.generated_numbers):
                
                self.generated_numbers[full_number] = True
                valid_numbers.append(full_number)
            attempts += 1
        
        return valid_numbers
    
    def save_to_file(self, prefix: str, numbers: List[str]) -> str:
        """Save numbers to a text file"""
        filename = f"numbers_{prefix}.txt"
        with open(filename, 'w') as f:
            f.write('\n'.join(numbers))
        self.number_files[prefix] = filename
        return filename

class NumberChecker:
    def __init__(self):
        self.api_url = "https://newtrue.rishuapi.workers.dev/?number="
    
    async def check_single_number(self, number: str) -> Dict:
        """Check single number with progress callback"""
        try:
            response = requests.get(f"{self.api_url}{number}", timeout=5)
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def format_result(self, number: str, data: Dict) -> str:
        """Format verification results beautifully"""
        if 'error' in data:
            return f"❌ {number}: {data['error']}"
        
        return (
            f"📱 *Number*: `{number}`\n"
            f"🏢 *Carrier*: {data.get('carrier', 'Unknown')}\n"
            f"🌍 *Location*: {data.get('location', 'Unknown')}\n"
            f"🆔 *Truecaller*: {data.get('Truecaller', 'Not available')}\n"
            f"⏱ *Last Checked*: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data.get('timestamp', 0)/1000))}\n"
            f"🔗 *API*: [RishuAPI](https://t.me/RishuApi)"
        )

checker = NumberChecker()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message"""
    help_text = (
        "🔍 *Mobile Number Verification Bot*\n\n"
        "✨ *Features*:\n"
        "- Generate valid Indian numbers\n"
        "- Detailed carrier/lookup information\n"
        "- Truecaller integration\n"
        "- Progress tracking\n\n"
        "📌 *Commands*:\n"
        "`/gen <prefix> <count>` - Generate numbers\n"
        "`/check` - Verify numbers from file\n\n"
        "Example: `/gen 976 10` then reply with `/check`"
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
        
        if not (2 <= len(prefix) <= 4 and prefix.isdigit()):
            await update.message.reply_text("❌ Prefix must be 2-4 digits (e.g. 98, 976, 9999)")
            return
        
        if count <= 0 or count > 10000:
            await update.message.reply_text("❌ Count must be 1-10000")
            return
        
        # Send generating message with progress
        progress_msg = await update.message.reply_text("🔄 Generating numbers... (0%)")
        
        numbers = []
        for i in range(1, count+1):
            num = generator.generate_indian_number(prefix, 1)
            if num:
                numbers.extend(num)
            # Update progress every 10% or 10 numbers
            if i % max(10, count//10) == 0 or i == count:
                progress = int((i/count)*100)
                await progress_msg.edit_text(f"🔄 Generating numbers... ({progress}%)")
        
        if not numbers:
            await progress_msg.edit_text("❌ Failed to generate numbers. Try different prefix.")
            return
        
        filename = generator.save_to_file(prefix, numbers)
        
        # Final message
        await progress_msg.edit_text(
            f"✅ Successfully generated {len(numbers)} numbers!\n"
            f"📁 File: `{filename}`"
        )
        
        # Send file
        with open(filename, 'rb') as f:
            await update.message.reply_document(
                document=f,
                caption=f"📊 {len(numbers)} numbers starting with {prefix}"
            )
            
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def check_numbers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle number verification with progress tracking"""
    if not update.message.reply_to_message or not update.message.reply_to_message.document:
        await update.message.reply_text("❌ Please reply to a number file with `/check`")
        return
    
    try:
        # Download file
        file = await update.message.reply_to_message.document.get_file()
        filename = "numbers_to_check.txt"
        await file.download_to_drive(filename)
        
        # Read numbers
        with open(filename, 'r') as f:
            numbers = [line.strip() for line in f if line.strip()]
        
        if not numbers:
            await update.message.reply_text("❌ No valid numbers found in file")
            return
        
        # Limit to 100 numbers per check
        numbers = numbers[:100]
        total = len(numbers)
        
        # Send initial progress message
        progress_msg = await update.message.reply_text(
            f"🔍 Verifying {total} numbers...\n"
            "🔄 Progress: 0% (0/{total})\n"
            "⏱ Estimated time: Calculating..."
        )
        
        results = []
        start_time = time.time()
        
        for i, number in enumerate(numbers, 1):
            # Check number
            data = await checker.check_single_number(number)
            results.append(checker.format_result(number, data))
            
            # Update progress every 25% or 5 numbers
            if i % max(5, total//4) == 0 or i == total:
                progress = int((i/total)*100)
                elapsed = time.time() - start_time
                remaining = (elapsed/i) * (total-i)
                
                await progress_msg.edit_text(
                    f"🔍 Verifying {total} numbers...\n"
                    f"🔄 Progress: {progress}% ({i}/{total})\n"
                    f"⏱ Remaining: {int(remaining)} seconds\n"
                    f"✅ Verified: {i - results.count('❌')} ✔️\n"
                    f"❌ Errors: {results.count('❌')} ✖️"
                )
        
        # Save results
        results_filename = "verification_results.txt"
        with open(results_filename, 'w') as f:
            f.write("\n\n".join(results))
        
        # Send sample results
        sample = "\n\n".join(results[:3])
        await update.message.reply_text(
            f"📊 Verification Complete!\n\n"
            f"Sample Results:\n\n{sample}\n\n"
            f"✅ Success: {len([r for r in results if '❌' not in r])}\n"
            f"❌ Errors: {results.count('❌')}",
            parse_mode='Markdown'
        )
        
        # Send full results
        with open(results_filename, 'rb') as f:
            await update.message.reply_document(
                document=f,
                caption=f"Full verification results ({total} numbers)"
            )
            
    except Exception as e:
        await update.message.reply_text(f"❌ Verification failed: {str(e)}")

def main():
    """Run the bot"""
    application = Application.builder().token("7818864949:AAEpqPVZj4oUAl2hFyiTSbZqfbzDr3TQ9fw").build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("gen", generate_numbers))
    application.add_handler(CommandHandler("check", check_numbers))
    
    # Run bot
    application.run_polling()

if __name__ == '__main__':
    main()
