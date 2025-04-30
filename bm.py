import os
import requests
import base64
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram.ext import CallbackContext

# Your GitHub Token and repository details
GITHUB_TOKEN = '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'  # Replace with your GitHub token
GITHUB_REPO = 'seedhe-maut-2/ng'         # Repository name
GITHUB_API_URL = f'https://api.github.com/repos/{GITHUB_REPO}/contents/'

# Telegram bot token
TELEGRAM_TOKEN = '7714765260:AAG4yiN5_ow25-feUeKslR2xsdeMFuPllGg'  # Replace with your Telegram bot token

# Function to upload the file to GitHub
def upload_to_github(file_path, file_name):
    with open(file_path, 'rb') as file:
        file_content = file.read()

    url = f'{GITHUB_API_URL}{file_name}'
    headers = {'Authorization': f'token {GITHUB_TOKEN}'}
    
    # Convert file content to Base64
    file_content_b64 = base64.b64encode(file_content).decode('utf-8')
    
    data = {
        'message': 'Upload video file',
        'content': file_content_b64
    }
    
    # Make a PUT request to GitHub API to upload the file
    response = requests.put(url, json=data, headers=headers)
    
    if response.status_code == 201:
        return f'File {file_name} uploaded successfully!'
    else:
        return f'Error uploading file: {response.json()}'

# Command handler for /start
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Hello! Send me a video file, and I'll upload it to GitHub.")

# Handler for receiving video files
def handle_video(update: Update, context: CallbackContext):
    # Get the video file
    video_file = update.message.video.get_file()
    video_file_path = video_file.file_path
    file_name = f"{update.message.video.file_id}.mp4"

    # Download the video file
    video_file.download(file_name)
    
    # Upload to GitHub
    response_message = upload_to_github(file_name, file_name)
    
    # Send response back to user
    update.message.reply_text(response_message)

    # Clean up the local file after upload
    if os.path.exists(file_name):
        os.remove(file_name)

# Main function to run the bot
def main():
    # Create the Updater object and pass the bot token
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    
    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher
    
    # Add command handler for /start
    dispatcher.add_handler(CommandHandler('start', start))
    
    # Add message handler for videos
    dispatcher.add_handler(MessageHandler(Filters.video, handle_video))
    
    # Start polling for updates
    updater.start_polling()

    # Run the bot until you press Ctrl+C
    updater.idle()

if __name__ == '__main__':
    main()
