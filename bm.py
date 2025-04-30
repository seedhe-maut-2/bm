import os
import requests
import telebot
import time
from telebot import TeleBot, types
from datetime import datetime

# Bot configuration
TOKEN = '8078721946:AAEhV6r0kXnmVaaFnRJgOk__pVjXU1mUd7A'
bot = telebot.TeleBot(TOKEN)
OWNER_USERNAME = "seedhe_maut"

# Instagram API configuration
INSTA_HEADERS = {
    'x-ig-app-id': '936619743392459',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def safe_get(data, keys, default=None):
    """Safely get nested dictionary values"""
    for key in keys.split('.'):
        try:
            data = data.get(key, {})
        except AttributeError:
            return default
    return data if data != {} else default

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = """
    <b>🌟 Instagram Profile Info Bot 🌟</b>

Send me an Instagram username to get:
- Profile information
- All public posts (photos/videos)

<b>Owner:</b> @seedhe_maut
    """
    bot.send_message(message.chat.id, welcome_text, parse_mode='HTML')

def get_instagram_profile(username):
    url = f'https://www.instagram.com/api/v1/users/web_profile_info/?username={username}'
    try:
        response = requests.get(url, headers=INSTA_HEADERS, timeout=10)
        if response.status_code == 200:
            return response.json().get('data', {}).get('user')
    except Exception:
        return None
    return None

def get_instagram_posts(user_id):
    url = f'https://www.instagram.com/api/v1/feed/user/{user_id}/?count=12'
    try:
        response = requests.get(url, headers=INSTA_HEADERS, timeout=10)
        if response.status_code == 200:
            return response.json().get('items', [])
    except Exception:
        return []
    return []

def format_post(post):
    """Safely format post information with proper error handling"""
    try:
        post_type = "📷 Photo" if safe_get(post, 'media_type') == 1 else "🎥 Video"
        caption = safe_get(post, 'caption.text', 'No caption')
        like_count = safe_get(post, 'like_count', 0)
        comment_count = safe_get(post, 'comment_count', 0)
        timestamp = datetime.fromtimestamp(safe_get(post, 'taken_at', 0)).strftime('%Y-%m-%d %H:%M:%S')
        
        return f"""
<b>{post_type}</b> • {timestamp}
❤️ <b>{like_count}</b> • 💬 <b>{comment_count}</b>

{caption}
"""
    except Exception:
        return "📄 Post information"

def get_media_url(post):
    """Safely extract media URL from different post types"""
    try:
        if safe_get(post, 'media_type') == 1:  # Photo
            return safe_get(post, 'image_versions2.candidates.0.url')
        elif safe_get(post, 'media_type') == 2:  # Video
            return safe_get(post, 'video_versions.0.url')
        elif safe_get(post, 'media_type') == 8:  # Carousel
            first_item = safe_get(post, 'carousel_media.0')
            if safe_get(first_item, 'media_type') == 1:
                return safe_get(first_item, 'image_versions2.candidates.0.url')
            else:
                return safe_get(first_item, 'video_versions.0.url')
    except Exception:
        return None

@bot.message_handler(func=lambda message: True)
def handle_instagram_username(message):
    user = message.text.strip().lstrip('@')
    if not user:
        return

    try:
        bot.send_chat_action(message.chat.id, 'typing')
        
        # Get profile info
        profile = get_instagram_profile(user)
        if not profile:
            bot.reply_to(message, f"❌ Couldn't fetch profile for @{user}. Account may not exist or be private.")
            return
            
        # Send profile info
        profile_msg = f"""
<b>📷 Instagram Profile Info</b>

<b>Username:</b> @{safe_get(profile, 'username')}
<b>Name:</b> {safe_get(profile, 'full_name', 'N/A')}
<b>🔒 Private:</b> {'✅' if safe_get(profile, 'is_private') else '❌'}
        
<b>👥 Followers:</b> {safe_get(profile, 'edge_followed_by.count', 0):,}
<b>👤 Following:</b> {safe_get(profile, 'edge_follow.count', 0):,}
<b>📮 Posts:</b> {safe_get(profile, 'edge_owner_to_timeline_media.count', 0):,}

<b>📝 Bio:</b>
{safe_get(profile, 'biography', 'No bio available')}
        """
        
        bot.send_photo(
            chat_id=message.chat.id,
            photo=safe_get(profile, 'profile_pic_url'),
            caption=profile_msg,
            parse_mode='HTML'
        )
        
        # Skip if private account
        if safe_get(profile, 'is_private'):
            bot.reply_to(message, "🔒 Private account - cannot fetch posts.")
            return
        
        # Get and send posts
        posts = get_instagram_posts(safe_get(profile, 'id'))
        if not posts:
            bot.reply_to(message, "No public posts found for this account.")
            return
            
        bot.reply_to(message, f"📂 Found {len(posts)} recent posts. Downloading...")
        
        for post in posts:
            try:
                media_url = get_media_url(post)
                if not media_url:
                    continue
                    
                caption = format_post(post)
                
                if safe_get(post, 'media_type') == 2:  # Video
                    bot.send_video(
                        chat_id=message.chat.id,
                        video=media_url,
                        caption=caption,
                        parse_mode='HTML'
                    )
                else:  # Photo or carousel
                    bot.send_photo(
                        chat_id=message.chat.id,
                        photo=media_url,
                        caption=caption,
                        parse_mode='HTML'
                    )
                
                time.sleep(2)  # Rate limit protection
                
            except Exception as e:
                print(f"Error sending post: {e}")
                continue
                
    except Exception as e:
        bot.reply_to(message, f"⚠️ Error processing @{user}: {str(e)}")

if __name__ == '__main__':
    print("Bot is running...")
    bot.polling(none_stop=True)
