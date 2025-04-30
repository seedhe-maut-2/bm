import requests
import telebot
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup

TOKEN = '8078721946:AAEhV6r0kXnmVaaFnRJgOk__pVjXU1mUd7A'
bot = telebot.TeleBot(TOKEN)

def extract_instagram_id(url):
    """Extract Instagram post ID from URL"""
    parsed = urlparse(url)
    if 'instagram.com' in parsed.netloc:
        path = parsed.path.strip('/').split('/')
        if len(path) >= 2 and path[0] == 'reel':
            return path[1].split('?')[0]
        elif len(path) >= 3 and path[1] == 'p':
            return path[2].split('?')[0]
    return None

def get_download_url(post_id):
    """Get download URL from indownloader.app API"""
    try:
        # First get the page to extract the download link
        page_url = f"https://indownloader.app/download.php?id={post_id}"
        response = requests.get(page_url)
        
        # Parse the HTML to find the download link
        soup = BeautifulSoup(response.text, 'html.parser')
        download_link = soup.find('a', {'id': 'download-btn'})['href']
        return download_link
        
    except Exception as e:
        print(f"Error getting download URL: {e}")
        return None

def download_media(url):
    """Download media from indownloader.app"""
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            return response.content
        return None
    except Exception as e:
        print(f"Error downloading media: {e}")
        return None

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = """
    📱 *Instagram Downloader Bot* 📱

Send me an Instagram post URL (reel or photo) and I'll download it for you!

Examples:
- https://www.instagram.com/reel/DJEdWQtN-H9/
- https://www.instagram.com/p/Cxyz12345ab/

Note: Only works with public posts.
    """
    bot.send_message(message.chat.id, welcome_text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text.strip()
    
    # Check if it's an Instagram URL
    if 'instagram.com' not in url:
        bot.reply_to(message, "❌ Please send a valid Instagram post URL")
        return
    
    # Extract post ID
    post_id = extract_instagram_id(url)
    if not post_id:
        bot.reply_to(message, "❌ Couldn't extract post ID from URL")
        return
    
    # Get download URL
    bot.send_chat_action(message.chat.id, 'typing')
    download_url = get_download_url(post_id)
    if not download_url:
        bot.reply_to(message, "❌ Failed to get download link")
        return
    
    # Check if it's video or image
    is_video = 'video' in download_url.lower() or 'mp4' in download_url.lower()
    
    try:
        if is_video:
            # For videos, send as document to preserve quality
            bot.send_video(
                chat_id=message.chat.id,
                video=download_url,
                caption="Here's your downloaded video!",
                supports_streaming=True
            )
        else:
            # For images, send as photo
            bot.send_photo(
                chat_id=message.chat.id,
                photo=download_url,
                caption="Here's your downloaded image!"
            )
            
    except Exception as e:
        print(f"Error sending media: {e}")
        # Fallback to sending as document
        try:
            bot.send_document(
                chat_id=message.chat.id,
                document=download_url,
                caption="Here's your downloaded media!"
            )
        except Exception as e:
            bot.reply_to(message, f"❌ Failed to send media: {str(e)}")

if __name__ == '__main__':
    print("Bot is running...")
    bot.polling(none_stop=True)
