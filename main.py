import os
import re
import urllib.parse
import requests
from bs4 import BeautifulSoup
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from keep_alive import keep_alive

# Fetch the token from Render's environment variables
BOT_TOKEN = os.environ.get('BOT_TOKEN')

if not BOT_TOKEN:
    raise ValueError("No BOT_TOKEN found. Please set it in your environment variables.")

bot = telebot.TeleBot(BOT_TOKEN)

# Helper function to scrape the thumbnail from the Terabox link
def get_thumbnail(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        meta_og_image = soup.find('meta', property='og:image')
        if meta_og_image and meta_og_image.get('content'):
            return meta_og_image['content']
    except Exception as e:
        print(f"Failed to fetch thumbnail for {url}: {e}")
    
    return None

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if message.chat.type != 'private':
        return
        
    bot.reply_to(message, "Send or forward me any Terabox video link(s), and I will generate watch/download buttons for you!")

@bot.message_handler(func=lambda message: True, content_types=['text', 'photo', 'video', 'document'])
def handle_message(message):
    if message.chat.type != 'private':
        return

    text = message.text or message.caption
    
    if not text:
        return

    urls = re.findall(r'(https?://[^\s]+)', text)
    terabox_urls = [url for url in urls if 'terabox' in url.lower()]

    if not terabox_urls:
        return

    for url in terabox_urls:
        # 1. Safely encode the full original URL for servers 1 and 2
        safe_url = urllib.parse.quote(url, safe='')
        
        # 2. Extract just the ID for server 3
        # This splits the URL by '/' and grabs the last part (the ID)
        video_id = url.rstrip('/').split('/')[-1]

        # 3. Generate the final URLs
        final_url_1 = "https://www.teraboxdownloader.pro/p/fs.html?q=" + safe_url
        final_url_2 = "https://teradownloader.com/download?l=" + safe_url
        
        # Server 3 ignores the original domain and appends the ID to the 1024terabox format
        final_url_3 = "https://www.teraboxfast.com/?q=https%3A%2F%2F1024terabox.com%2Fs%2F" + video_id

        # 4. Build the buttons
        markup = InlineKeyboardMarkup()
        button1 = InlineKeyboardButton(text="Watch / Download Server 1", web_app=WebAppInfo(url=final_url_1))
        button2 = InlineKeyboardButton(text="Watch / Download Server 2", web_app=WebAppInfo(url=final_url_2))
        button3 = InlineKeyboardButton(text="Watch / Download Server 3", web_app=WebAppInfo(url=final_url_3))
        
        markup.add(button1)
        markup.add(button2)
        markup.add(button3)

        # 5. Try to fetch the thumbnail
        thumbnail_url = get_thumbnail(url)
        message_text = "✅ **Link Processed!** Choose a server below:"

        # 6. Send the result
        if thumbnail_url:
            try:
                bot.send_photo(
                    chat_id=message.chat.id, 
                    photo=thumbnail_url, 
                    caption=message_text, 
                    reply_markup=markup,
                    parse_mode="Markdown"
                )
            except Exception:
                bot.reply_to(message, message_text, reply_markup=markup, parse_mode="Markdown")
        else:
            bot.reply_to(message, message_text, reply_markup=markup, parse_mode="Markdown")

# Start the web server for UptimeRobot
keep_alive()

# Start the Telegram bot
print("Bot is running...")
bot.infinity_polling()
