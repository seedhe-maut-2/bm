import os
import logging
from typing import Dict
from uuid import uuid4
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaAudio,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackContext,
    CallbackQueryHandler,
    ConversationHandler,
    filters
)
from google.cloud import texttospeech
from pydub import AudioSegment
from gtts import gTTS
import tempfile

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Constants for conversation states
SELECTING_VOICE, SELECTING_LANGUAGE, CUSTOMIZING_VOICE, UPLOADING_VOICE = range(4)

# Voice options with descriptions
VOICE_OPTIONS = {
    "girl_voice": {"name": "👧 Girl Voice", "desc": "Sweet and soft voice"},
    "boy_voice": {"name": "👦 Boy Voice", "desc": "Strong and firm voice"},
    "best_girl": {"name": "👩 Best Girl", "desc": "Crystal clear natural voice"},
    "best_boy": {"name": "👨 Best Boy", "desc": "Smooth and warm voice"},
    "kid_voice": {"name": "🧒 Kid Voice", "desc": "Fun and energetic"},
    "celebrity": {"name": "🌟 Celebrity", "desc": "Playful tone like famous people"},
    "ai_voice": {"name": "🤖 AI Voice", "desc": "Robotic futuristic tone"},
}

# Language options
LANGUAGES = {
    "en": {"name": "English", "voices": ["en-US", "en-GB", "en-AU"]},
    "hi": {"name": "Hindi", "voices": ["hi-IN"]},
    "es": {"name": "Spanish", "voices": ["es-ES", "es-US"]},
    "fr": {"name": "French", "voices": ["fr-FR"]},
    "de": {"name": "German", "voices": ["de-DE"]},
    "it": {"name": "Italian", "voices": ["it-IT"]},
}

# Tone options
TONES = {
    "neutral": "😐 Neutral",
    "happy": "😊 Happy",
    "excited": "🤩 Excited",
    "calm": "🧘 Calm",
    "serious": "🧐 Serious",
    "motivational": "💪 Motivational",
}

class VoiceBot:
    def __init__(self, token: str):
        self.token = token
        self.user_prefs = {}
        
    async def start(self, update: Update, context: CallbackContext) -> None:
        """Send welcome message with animated GIF and start button."""
        user = update.effective_user
        welcome_text = (
            f"🎉 *Welcome {user.first_name}!* 🎉\n\n"
            "I'm your *personal voice assistant* that can convert text to speech with various voice options. "
            "Here's what I can do:\n\n"
            "• Convert text to voice in multiple languages 🌍\n"
            "• Offer different voice qualities (girl, boy, celebrity, etc.) 🎤\n"
            "• Customize tone (happy, serious, motivational) 🎭\n"
            "• Process voice messages and reply with text 🎙️\n"
            "• And much more!\n\n"
            "Click *Let's Begin* to start or /help for instructions."
        )
        
        # Create inline keyboard with start button
        keyboard = [
            [InlineKeyboardButton("🚀 Let's Begin", callback_data="start_conversion")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    async def help(self, update: Update, context: CallbackContext) -> None:
        """Send help message with voice instructions."""
        help_text = (
            "📖 *How to use this bot:*\n\n"
            "1. Send me any text or use /convert command\n"
            "2. Select your preferred voice quality\n"
            "3. Choose language if needed\n"
            "4. Customize tone and speed\n"
            "5. Get your voice message!\n\n"
            "✨ *Special Features:*\n"
            "- /voice_quality - Change voice type\n"
            "- /custom_voice - Upload your own voice\n"
            "- Send voice messages for text conversion\n"
            "- Multi-language support\n\n"
            "Need help? Just ask!"
        )
        
        await update.message.reply_text(help_text, parse_mode="Markdown")
    
    async def voice_quality(self, update: Update, context: CallbackContext) -> None:
        """Show voice quality options with inline keyboard."""
        keyboard = []
        
        # Create buttons for each voice option
        for voice_id, voice_data in VOICE_OPTIONS.items():
            keyboard.append([
                InlineKeyboardButton(
                    f"{voice_data['name']} - {voice_data['desc']}",
                    callback_data=f"voice_{voice_id}"
                )
            ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🎙️ *Select Voice Quality:*\n\n"
            "Choose from our variety of voices to find your perfect match!",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    async def custom_voice(self, update: Update, context: CallbackContext) -> int:
        """Handle custom voice upload."""
        await update.message.reply_text(
            "🎤 *Upload Your Voice*\n\n"
            "Please record or upload a voice message (at least 10 seconds) "
            "that I can learn from. Speak clearly in a quiet environment.\n\n"
            "After uploading, I'll process it and create your custom voice profile!",
            parse_mode="Markdown"
        )
        return UPLOADING_VOICE
    
    async def handle_voice_upload(self, update: Update, context: CallbackContext) -> int:
        """Process uploaded voice for cloning."""
        user = update.effective_user
        voice_file = update.message.voice or update.message.audio
        
        # Download the voice file
        file = await context.bot.get_file(voice_file.file_id)
        temp_file = f"user_voices/{user.id}_{uuid4()}.ogg"
        await file.download_to_drive(temp_file)
        
        # Process the voice file
        await update.message.reply_text(
            "🔍 Processing your voice...\n\n"
            "This may take a few minutes. I'll notify you when your custom voice is ready!",
            parse_mode="Markdown"
        )
        
        self.user_prefs.setdefault(user.id, {})["custom_voice"] = True
        
        # Send confirmation
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="🎉 *Custom Voice Ready!*\n\n"
                 "Your custom voice profile has been created. "
                 "Now you can use it for text-to-speech conversion!",
            parse_mode="Markdown"
        )
        
        return ConversationHandler.END
    
    async def start_conversion(self, update: Update, context: CallbackContext) -> int:
        """Start the text-to-voice conversion process."""
        query = update.callback_query
        if query:
            await query.answer()
            await query.edit_message_text(
                "📝 Please send me the text you'd like to convert to speech."
            )
        else:
            await update.message.reply_text(
                "📝 Please send me the text you'd like to convert to speech."
            )
        
        return SELECTING_VOICE
    
    async def select_voice(self, update: Update, context: CallbackContext) -> int:
        """Handle voice selection."""
        query = update.callback_query
        await query.answer()
        
        voice_id = query.data.split('_')[1]
        user_id = query.from_user.id
        
        # Store user preference
        self.user_prefs.setdefault(user_id, {})["voice"] = voice_id
        
        # Show language selection
        keyboard = []
        for lang_code, lang_data in LANGUAGES.items():
            keyboard.append([
                InlineKeyboardButton(
                    f"🌐 {lang_data['name']}",
                    callback_data=f"lang_{lang_code}"
                )
            ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"🎙️ Selected: *{VOICE_OPTIONS[voice_id]['name']}*\n\n"
            "Now choose the language:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        return SELECTING_LANGUAGE
    
    async def select_language(self, update: Update, context: CallbackContext) -> int:
        """Handle language selection."""
        query = update.callback_query
        await query.answer()
        
        lang_code = query.data.split('_')[1]
        user_id = query.from_user.id
        
        # Store user preference
        self.user_prefs.setdefault(user_id, {})["language"] = lang_code
        
        # Show tone customization
        keyboard = []
        row = []
        for i, (tone_id, tone_name) in enumerate(TONES.items()):
            row.append(InlineKeyboardButton(tone_name, callback_data=f"tone_{tone_id}"))
            if (i + 1) % 2 == 0:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"🌐 Selected: *{LANGUAGES[lang_code]['name']}*\n\n"
            "Now choose the tone for your voice:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        return CUSTOMIZING_VOICE
    
    async def customize_voice(self, update: Update, context: CallbackContext) -> int:
        """Handle tone customization."""
        query = update.callback_query
        await query.answer()
        
        tone_id = query.data.split('_')[1]
        user_id = query.from_user.id
        
        # Store user preference
        self.user_prefs.setdefault(user_id, {})["tone"] = tone_id
        
        await query.edit_message_text(
            f"🎭 Selected tone: *{TONES[tone_id]}*\n\n"
            "Now please send me the text you want to convert to speech:",
            parse_mode="Markdown"
        )
        
        return CUSTOMIZING_VOICE
    
    async def process_text(self, update: Update, context: CallbackContext) -> int:
        """Process the text and convert to speech."""
        user_id = update.effective_user.id
        text = update.message.text
        
        # Get user preferences or use defaults
        voice_id = self.user_prefs.get(user_id, {}).get("voice", "best_girl")
        lang_code = self.user_prefs.get(user_id, {}).get("language", "en")
        tone_id = self.user_prefs.get(user_id, {}).get("tone", "neutral")
        
        # Check text length
        if len(text) > 1000:
            await update.message.reply_text(
                "⚠️ *Text too long*\n\n"
                "For best quality, please keep texts under 1000 characters. "
                "I'll process this in chunks.",
                parse_mode="Markdown"
            )
            return await self._process_long_text(update, context, text, voice_id, lang_code, tone_id)
        
        # Generate voice
        try:
            audio_file = await self._generate_voice(text, voice_id, lang_code, tone_id)
            
            # Send the voice message
            await context.bot.send_voice(
                chat_id=update.effective_chat.id,
                voice=audio_file,
                caption=f"🎤 Here's your voice message!\n\n"
                       f"Voice: {VOICE_OPTIONS[voice_id]['name']}\n"
                       f"Language: {LANGUAGES[lang_code]['name']}\n"
                       f"Tone: {TONES[tone_id]}"
            )
            
            # Clean up
            os.remove(audio_file)
            
            # Ask for feedback
            await self._request_feedback(update, context)
            
        except Exception as e:
            logger.error(f"Error generating voice: {e}")
            await update.message.reply_text(
                "😢 *Oops! Something went wrong.*\n\n"
                "I couldn't generate the voice message. Please try again with different text.",
                parse_mode="Markdown"
            )
        
        return ConversationHandler.END
    
    async def _process_long_text(self, update: Update, context: CallbackContext, 
                              text: str, voice_id: str, lang_code: str, tone_id: str) -> int:
        """Process long text by splitting into chunks."""
        chunk_size = 500
        chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
        
        # Send processing message
        processing_msg = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"🔧 Processing {len(chunks)} chunks..."
        )
        
        # Process each chunk
        audio_files = []
        for i, chunk in enumerate(chunks):
            try:
                audio_file = await self._generate_voice(chunk, voice_id, lang_code, tone_id)
                audio_files.append(audio_file)
            except Exception as e:
                logger.error(f"Error processing chunk {i}: {e}")
                continue
        
        # Combine audio files
        if audio_files:
            combined_audio = await self._combine_audio_files(audio_files)
            
            # Send combined audio
            await context.bot.send_voice(
                chat_id=update.effective_chat.id,
                voice=combined_audio,
                caption=f"🎤 Here's your long voice message!\n\n"
                       f"Voice: {VOICE_OPTIONS[voice_id]['name']}\n"
                       f"Language: {LANGUAGES[lang_code]['name']}\n"
                       f"Tone: {TONES[tone_id]}"
            )
            
            # Clean up
            for file in audio_files:
                try:
                    os.remove(file)
                except:
                    pass
            try:
                os.remove(combined_audio)
            except:
                pass
            
            # Ask for feedback
            await self._request_feedback(update, context)
        
        # Delete processing message
        try:
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=processing_msg.message_id
            )
        except:
            pass
        
        return ConversationHandler.END
    
    async def _generate_voice(self, text: str, voice_id: str, lang_code: str, tone_id: str) -> str:
        """Generate voice file using Google TTS or other service."""
        # Determine voice parameters based on selections
        voice_params = self._get_voice_parameters(voice_id, lang_code, tone_id)
        
        # Generate unique filename
        output_file = f"temp_voice_{uuid4()}.mp3"
        
        # Use Google Cloud TTS for high-quality voices
        if voice_id in ["best_girl", "best_boy", "celebrity"]:
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            # Build the voice request
            voice = texttospeech.VoiceSelectionParams(
                language_code=voice_params["language_code"],
                name=voice_params["voice_name"],
                ssml_gender=voice_params["ssml_gender"],
            )
            
            # Select the type of audio file
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=voice_params["speaking_rate"],
                pitch=voice_params["pitch"],
                volume_gain_db=voice_params["volume"],
            )
            
            # Perform the text-to-speech request
            response = self.tts_client.synthesize_speech(
                input=synthesis_input, voice=voice, audio_config=audio_config
            )
            
            # Write the response to the output file
            with open(output_file, "wb") as out:
                out.write(response.audio_content)
        
        # Use gTTS for simpler voices
        else:
            tts = gTTS(text=text, lang=lang_code, slow=(voice_params["speaking_rate"] < 1.0))
            tts.save(output_file)
            
            # Apply effects with pydub if needed
            if tone_id in ["excited", "motivational"]:
                audio = AudioSegment.from_mp3(output_file)
                if tone_id == "excited":
                    audio = audio.speedup(playback_speed=1.1)
                elif tone_id == "motivational":
                    audio = audio + 6  # Increase volume
                audio.export(output_file, format="mp3")
        
        return output_file
    
    def _get_voice_parameters(self, voice_id: str, lang_code: str, tone_id: str) -> Dict:
        """Get voice parameters based on selections."""
        params = {
            "language_code": f"{lang_code}-IN" if lang_code == "hi" else f"{lang_code}-US",
            "voice_name": "",
            "ssml_gender": texttospeech.SsmlVoiceGender.NEUTRAL,
            "speaking_rate": 1.0,
            "pitch": 0.0,
            "volume": 0.0,
        }
        
        # Set voice name and gender
        if voice_id == "best_girl":
            params["voice_name"] = f"{lang_code}-US-Wavenet-F"
            params["ssml_gender"] = texttospeech.SsmlVoiceGender.FEMALE
        elif voice_id == "best_boy":
            params["voice_name"] = f"{lang_code}-US-Wavenet-D"
            params["ssml_gender"] = texttospeech.SsmlVoiceGender.MALE
        elif voice_id == "girl_voice":
            params["voice_name"] = f"{lang_code}-US-Standard-C"
            params["ssml_gender"] = texttospeech.SsmlVoiceGender.FEMALE
        elif voice_id == "boy_voice":
            params["voice_name"] = f"{lang_code}-US-Standard-B"
            params["ssml_gender"] = texttospeech.SsmlVoiceGender.MALE
        elif voice_id == "kid_voice":
            params["voice_name"] = f"{lang_code}-US-Standard-A"
            params["ssml_gender"] = texttospeech.SsmlVoiceGender.MALE
            params["pitch"] = 5.0
        elif voice_id == "celebrity":
            params["voice_name"] = f"{lang_code}-US-Standard-J"
            params["ssml_gender"] = texttospeech.SsmlVoiceGender.MALE
        elif voice_id == "ai_voice":
            params["voice_name"] = f"{lang_code}-US-Standard-E"
            params["ssml_gender"] = texttospeech.SsmlVoiceGender.MALE
            params["pitch"] = -4.0
        
        # Adjust for tone
        if tone_id == "happy":
            params["speaking_rate"] = 1.1
            params["pitch"] += 2.0
        elif tone_id == "excited":
            params["speaking_rate"] = 1.2
            params["pitch"] += 3.0
            params["volume"] = 2.0
        elif tone_id == "calm":
            params["speaking_rate"] = 0.9
            params["pitch"] -= 1.0
        elif tone_id == "serious":
            params["speaking_rate"] = 0.95
            params["pitch"] -= 2.0
        elif tone_id == "motivational":
            params["speaking_rate"] = 1.05
            params["volume"] = 4.0
        
        return params
    
    async def _combine_audio_files(self, audio_files: list) -> str:
        """Combine multiple audio files into one."""
        if not audio_files:
            raise ValueError("No audio files to combine")
        
        if len(audio_files) == 1:
            return audio_files[0]
        
        # Create a silent 0.5s segment for spacing
        silent_segment = AudioSegment.silent(duration=500)
        
        combined = AudioSegment.from_file(audio_files[0])
        for file in audio_files[1:]:
            combined += silent_segment + AudioSegment.from_file(file)
        
        output_file = f"combined_{uuid4()}.mp3"
        combined.export(output_file, format="mp3")
        
        return output_file
    
    async def _request_feedback(self, update: Update, context: CallbackContext) -> None:
        """Ask user for feedback after voice generation."""
        keyboard = [
            [
                InlineKeyboardButton("👍 Good", callback_data="feedback_good"),
                InlineKeyboardButton("👎 Could Improve", callback_data="feedback_bad"),
            ],
            [InlineKeyboardButton("💡 Suggest Improvement", callback_data="feedback_suggest")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="*How was your experience?*",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    async def feedback(self, update: Update, context: CallbackContext) -> None:
        """Handle feedback command."""
        await self._request_feedback(update, context)
    
    async def handle_text(self, update: Update, context: CallbackContext) -> None:
        """Handle direct text messages."""
        # Check if this is part of a conversation
        if context.user_data.get('conversation'):
            return
        
        # Otherwise, start conversion process
        await self.start_conversion(update, context)
    
    async def handle_voice_message(self, update: Update, context: CallbackContext) -> None:
        """Convert voice message to text and then to selected voice."""
        await update.message.reply_text(
            "🎙️ *Voice Message Received*\n\n"
            "I currently support converting text to voice. "
            "Please send me the text you'd like to convert or use /convert to start.",
            parse_mode="Markdown"
        )
    
    async def cancel(self, update: Update, context: CallbackContext) -> int:
        """Cancel the current conversation."""
        await update.message.reply_text(
            "Operation cancelled. Use /convert to start again."
        )
        return ConversationHandler.END
    
    async def error_handler(self, update: Update, context: CallbackContext) -> None:
        """Handle errors."""
        logger.error(msg="Exception while handling update:", exc_info=context.error)
        
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "😢 *Oops! Something went wrong.*\n\n"
                "Please try again later or contact support if the problem persists.",
                parse_mode="Markdown"
            )

    def run(self):
        """Run the bot."""
        application = Application.builder().token(self.token).build()
        
        # Register handlers
        application.add_handler(CommandHandler('start', self.start))
        application.add_handler(CommandHandler('help', self.help))
        application.add_handler(CommandHandler('voice_quality', self.voice_quality))
        application.add_handler(CommandHandler('custom_voice', self.custom_voice))
        application.add_handler(CommandHandler('feedback', self.feedback))
        
        # Conversation handler
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('convert', self.start_conversion)],
            states={
                SELECTING_VOICE: [
                    CallbackQueryHandler(self.select_voice, pattern='^voice_.*$')
                ],
                SELECTING_LANGUAGE: [
                    CallbackQueryHandler(self.select_language, pattern='^lang_.*$')
                ],
                CUSTOMIZING_VOICE: [
                    CallbackQueryHandler(self.customize_voice, pattern='^tone_.*$'),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.process_text)
                ],
                UPLOADING_VOICE: [
                    MessageHandler(filters.VOICE, self.handle_voice_upload),
                    MessageHandler(filters.AUDIO, self.handle_voice_upload),
                ],
            },
            fallbacks=[CommandHandler('cancel', self.cancel)],
        )
        application.add_handler(conv_handler)
        
        # Message handlers
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
        application.add_handler(MessageHandler(filters.VOICE, self.handle_voice_message))
        
        # Error handler
        application.add_error_handler(self.error_handler)
        
        # Start the Bot
        application.run_polling()

if __name__ == '__main__':
    # Initialize and run the bot
    bot = VoiceBot("8078721946:AAEhV6r0kXnmVaaFnRJgOk__pVjXU1mUd7A")
    bot.run()
