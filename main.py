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
        # Act like a normal web browser to avoid getting blocked
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for the standard 'og:image' meta tag that contains the thumbnail
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
        # 1. Safely encode the URL
        safe_url = urllib.parse.quote(url, safe='')
        final_url_1 = "https://www.teraboxdownloader.pro/p/fs.html?q=" + safe_url
        final_url_2 = "https://teradownloader.com/download?l=" + safe_url

        # 2. Build the buttons
        markup = InlineKeyboardMarkup()
        button1 = InlineKeyboardButton(text="Watch / Download Server 1", web_app=WebAppInfo(url=final_url_1))
        button2 = InlineKeyboardButton(text="Watch / Download Server 2", web_app=WebAppInfo(url=final_url_2))
        markup.add(button1)
        markup.add(button2)

        # 3. Try to fetch the thumbnail
        thumbnail_url = get_thumbnail(url)
        message_text = "✅ **Link Processed!** Choose a server below:"

        # 4. Send the result (With or without photo depending on scraping success)
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
                # Fallback just in case Telegram rejects the scraped image URL
                bot.reply_to(message, message_text, reply_markup=markup, parse_mode="Markdown")
        else:
            bot.reply_to(message, message_text, reply_markup=markup, parse_mode="Markdown")

# Start the web server for UptimeRobot
keep_alive()

# Start the Telegram bot
print("Bot is running...")
bot.infinity_polling()
