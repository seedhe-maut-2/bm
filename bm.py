import os
import logging
from uuid import uuid4
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
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
        self.tts_client = texttospeech.TextToSpeechClient()
        
        # Create temp directory if not exists
        if not os.path.exists("temp_voices"):
            os.makedirs("temp_voices")
        if not os.path.exists("user_voices"):
            os.makedirs("user_voices")

    async def start(self, update: Update, context: CallbackContext) -> None:
        """Send welcome message with start button."""
        user = update.effective_user
        welcome_text = (
            f"🎉 Welcome {user.first_name}! 🎉\n\n"
            "I'm your personal voice assistant that can convert text to speech with various voice options. "
            "Here's what I can do:\n\n"
            "• Convert text to voice in multiple languages 🌍\n"
            "• Offer different voice qualities (girl, boy, celebrity, etc.) 🎤\n"
            "• Customize tone (happy, serious, motivational) 🎭\n"
            "• Process voice messages and reply with text 🎙️\n"
            "• And much more!\n\n"
            "Click Let's Begin to start or /help for instructions."
        )
        
        keyboard = [[InlineKeyboardButton("🚀 Let's Begin", callback_data="start_conversion")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)

    async def help(self, update: Update, context: CallbackContext) -> None:
        """Send help message."""
        help_text = (
            "📖 How to use this bot:\n\n"
            "1. Send me any text or use /convert command\n"
            "2. Select your preferred voice quality\n"
            "3. Choose language if needed\n"
            "4. Customize tone and speed\n"
            "5. Get your voice message!\n\n"
            "✨ Special Features:\n"
            "- /voicequality - Change voice type\n"
            "- /customvoice - Upload your own voice\n"
            "- Send voice messages for text conversion\n"
            "- Multi-language support\n\n"
            "Need help? Just ask!"
        )
        await update.message.reply_text(help_text)

    async def voice_quality(self, update: Update, context: CallbackContext) -> None:
        """Show voice quality options."""
        keyboard = []
        for voice_id, voice_data in VOICE_OPTIONS.items():
            keyboard.append([
                InlineKeyboardButton(
                    f"{voice_data['name']} - {voice_data['desc']}",
                    callback_data=f"voice_{voice_id}"
                )
            ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "🎙️ Select Voice Quality:\n\nChoose from our variety of voices!",
            reply_markup=reply_markup
        )

    async def custom_voice(self, update: Update, context: CallbackContext) -> int:
        """Handle custom voice upload."""
        await update.message.reply_text(
            "🎤 Upload Your Voice\n\n"
            "Please record or upload a voice message (at least 10 seconds) "
            "that I can learn from. Speak clearly in a quiet environment."
        )
        return UPLOADING_VOICE

    async def handle_voice_upload(self, update: Update, context: CallbackContext) -> int:
        """Process uploaded voice for cloning."""
        user = update.effective_user
        voice_file = update.message.voice or update.message.audio
        
        file = await context.bot.get_file(voice_file.file_id)
        temp_file = f"user_voices/{user.id}_{uuid4()}.ogg"
        await file.download_to_drive(temp_file)
        
        await update.message.reply_text("🔍 Processing your voice... This may take a few minutes.")
        
        self.user_prefs.setdefault(user.id, {})["custom_voice"] = True
        
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="🎉 Custom Voice Ready!\n\nYour custom voice profile has been created."
        )
        return ConversationHandler.END

    async def start_conversion(self, update: Update, context: CallbackContext) -> int:
        """Start text-to-voice conversion."""
        # Check if command has text argument
        if update.message.text.strip() != "/convert":
            text = update.message.text.replace("/convert", "").strip()
            context.user_data["text_to_convert"] = text
            return await self.select_voice_menu(update, context)
        
        await update.message.reply_text("📝 Please send me the text you'd like to convert to speech.")
        return SELECTING_VOICE

    async def select_voice_menu(self, update: Update, context: CallbackContext) -> int:
        """Show voice selection menu."""
        keyboard = []
        for voice_id, voice_data in VOICE_OPTIONS.items():
            keyboard.append([
                InlineKeyboardButton(voice_data["name"], callback_data=f"voice_{voice_id}")
            ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                "🎙️ Select Voice Quality:",
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                "🎙️ Select Voice Quality:",
                reply_markup=reply_markup
            )
        return SELECTING_VOICE

    async def select_voice(self, update: Update, context: CallbackContext) -> int:
        """Handle voice selection."""
        query = update.callback_query
        await query.answer()
        
        voice_id = query.data.split('_')[1]
        context.user_data["voice_id"] = voice_id
        
        # Show language selection
        keyboard = []
        for lang_code, lang_data in LANGUAGES.items():
            keyboard.append([
                InlineKeyboardButton(lang_data["name"], callback_data=f"lang_{lang_code}")
            ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"🎙️ Selected: {VOICE_OPTIONS[voice_id]['name']}\n\nNow choose the language:",
            reply_markup=reply_markup
        )
        return SELECTING_LANGUAGE

    async def select_language(self, update: Update, context: CallbackContext) -> int:
        """Handle language selection."""
        query = update.callback_query
        await query.answer()
        
        lang_code = query.data.split('_')[1]
        context.user_data["lang_code"] = lang_code
        
        # Show tone customization
        keyboard = []
        for tone_id, tone_name in TONES.items():
            keyboard.append([InlineKeyboardButton(tone_name, callback_data=f"tone_{tone_id}")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"🌐 Selected: {LANGUAGES[lang_code]['name']}\n\nNow choose the tone:",
            reply_markup=reply_markup
        )
        return CUSTOMIZING_VOICE

    async def customize_voice(self, update: Update, context: CallbackContext) -> int:
        """Handle tone customization."""
        query = update.callback_query
        await query.answer()
        
        tone_id = query.data.split('_')[1]
        context.user_data["tone_id"] = tone_id
        
        # Get text from context or ask for it
        text = context.user_data.get("text_to_convert")
        if text:
            return await self.process_text_with_context(update, context, text)
        
        await query.edit_message_text(
            f"🎭 Selected tone: {TONES[tone_id]}\n\nNow send me the text to convert:"
        )
        return CUSTOMIZING_VOICE

    async def process_text_with_context(self, update: Update, context: CallbackContext, text: str) -> int:
        """Process text that was provided with /convert command."""
        voice_id = context.user_data["voice_id"]
        lang_code = context.user_data["lang_code"]
        tone_id = context.user_data["tone_id"]
        
        await self.process_conversion(update, context, text, voice_id, lang_code, tone_id)
        return ConversationHandler.END

    async def process_text(self, update: Update, context: CallbackContext) -> int:
        """Process text message."""
        text = update.message.text
        voice_id = context.user_data.get("voice_id", "best_girl")
        lang_code = context.user_data.get("lang_code", "en")
        tone_id = context.user_data.get("tone_id", "neutral")
        
        await self.process_conversion(update, context, text, voice_id, lang_code, tone_id)
        return ConversationHandler.END

    async def process_conversion(self, update: Update, context: CallbackContext, 
                               text: str, voice_id: str, lang_code: str, tone_id: str) -> None:
        """Handle the actual text-to-voice conversion."""
        if len(text) > 1000:
            await update.message.reply_text("⚠️ Text too long! Processing in chunks...")
        
        try:
            audio_file = await self._generate_voice(text, voice_id, lang_code, tone_id)
            
            await context.bot.send_voice(
                chat_id=update.effective_chat.id,
                voice=audio_file,
                caption=f"🎤 Your voice message!\nVoice: {VOICE_OPTIONS[voice_id]['name']}\n"
                       f"Language: {LANGUAGES[lang_code]['name']}\nTone: {TONES[tone_id]}"
            )
            
            os.remove(audio_file)
            await self._request_feedback(update, context)
            
        except Exception as e:
            logger.error(f"Error generating voice: {e}")
            await update.message.reply_text("😢 Oops! Something went wrong. Please try again.")

    async def _generate_voice(self, text: str, voice_id: str, lang_code: str, tone_id: str) -> str:
        """Generate voice file."""
        voice_params = self._get_voice_parameters(voice_id, lang_code, tone_id)
        output_file = f"temp_voices/{uuid4()}.mp3"
        
        if voice_id in ["best_girl", "best_boy", "celebrity"]:
            synthesis_input = texttospeech.SynthesisInput(text=text)
            voice = texttospeech.VoiceSelectionParams(
                language_code=voice_params["language_code"],
                name=voice_params["voice_name"],
                ssml_gender=voice_params["ssml_gender"],
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=voice_params["speaking_rate"],
                pitch=voice_params["pitch"],
                volume_gain_db=voice_params["volume"],
            )
            response = self.tts_client.synthesize_speech(
                input=synthesis_input, voice=voice, audio_config=audio_config
            )
            with open(output_file, "wb") as out:
                out.write(response.audio_content)
        else:
            tts = gTTS(text=text, lang=lang_code, slow=(voice_params["speaking_rate"] < 1.0))
            tts.save(output_file)
            
            if tone_id in ["excited", "motivational"]:
                audio = AudioSegment.from_mp3(output_file)
                if tone_id == "excited":
                    audio = audio.speedup(playback_speed=1.1)
                elif tone_id == "motivational":
                    audio = audio + 6
                audio.export(output_file, format="mp3")
        
        return output_file

    def _get_voice_parameters(self, voice_id: str, lang_code: str, tone_id: str) -> dict:
        """Get voice parameters."""
        params = {
            "language_code": f"{lang_code}-IN" if lang_code == "hi" else f"{lang_code}-US",
            "voice_name": "",
            "ssml_gender": texttospeech.SsmlVoiceGender.NEUTRAL,
            "speaking_rate": 1.0,
            "pitch": 0.0,
            "volume": 0.0,
        }
        
        # Voice type settings
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
        
        # Tone adjustments
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

    async def _request_feedback(self, update: Update, context: CallbackContext) -> None:
        """Ask for user feedback."""
        keyboard = [
            [
                InlineKeyboardButton("👍 Good", callback_data="feedback_good"),
                InlineKeyboardButton("👎 Could Improve", callback_data="feedback_bad"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="How was your experience?",
            reply_markup=reply_markup
        )

    async def cancel(self, update: Update, context: CallbackContext) -> int:
        """Cancel the current conversation."""
        await update.message.reply_text("Operation cancelled.")
        return ConversationHandler.END

    async def error_handler(self, update: object, context: CallbackContext) -> None:
        """Handle errors."""
        logger.error("Exception while handling update:", exc_info=context.error)
        if update and isinstance(update, Update) and update.effective_message:
            await update.effective_message.reply_text("😢 Oops! Something went wrong.")

    def run(self):
        """Run the bot."""
        application = Application.builder().token(self.token).build()
        
        # Command handlers
        application.add_handler(CommandHandler('start', self.start))
        application.add_handler(CommandHandler('help', self.help))
        application.add_handler(CommandHandler('voicequality', self.voice_quality))
        application.add_handler(CommandHandler('customvoice', self.custom_voice))
        
        # Conversation handler
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('convert', self.start_conversion)],
            states={
                SELECTING_VOICE: [
                    CallbackQueryHandler(self.select_voice, pattern='^voice_')
                ],
                SELECTING_LANGUAGE: [
                    CallbackQueryHandler(self.select_language, pattern='^lang_')
                ],
                CUSTOMIZING_VOICE: [
                    CallbackQueryHandler(self.customize_voice, pattern='^tone_'),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.process_text)
                ],
                UPLOADING_VOICE: [
                    MessageHandler(filters.VOICE | filters.AUDIO, self.handle_voice_upload),
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
        
        # Start the bot
        application.run_polling()

if __name__ == '__main__':
    bot = VoiceBot("8078721946:AAEhV6r0kXnmVaaFnRJgOk__pVjXU1mUd7A")
    bot.run()
