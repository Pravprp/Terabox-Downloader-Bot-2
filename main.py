import os
import re
import urllib.parse
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from keep_alive import keep_alive

# Fetch the token from Render's environment variables
BOT_TOKEN = os.environ.get('BOT_TOKEN')

if not BOT_TOKEN:
    raise ValueError("No BOT_TOKEN found. Please set it in your environment variables.")

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if message.chat.type != 'private':
        return
        
    bot.reply_to(message, "Send or forward me any Terabox video link(s), and I will generate watch/download buttons for you!")

# Catch both regular messages and forwarded messages
@bot.message_handler(func=lambda message: True, content_types=['text', 'photo', 'video', 'document'])
def handle_message(message):
    # 1. STRICTLY PRIVATE DMs ONLY
    if message.chat.type != 'private':
        return

    # 2. Extract text (handles regular text AND forwarded media with captions)
    text = message.text or message.caption
    
    if not text:
        return

    # 3. Use Regex to find ALL links hidden inside the forwarded text
    urls = re.findall(r'(https?://[^\s]+)', text)
    
    # Filter out only the links that contain 'terabox'
    terabox_urls = [url for url in urls if 'terabox' in url.lower()]

    if not terabox_urls:
        # Only reply if they actually sent text but it didn't have a valid link
        # You can comment this out if you want the bot to just silently ignore bad messages
        bot.reply_to(message, "No valid Terabox links found in that message.")
        return

    # 4. Process each valid Terabox link found in the message
    for url in terabox_urls:
        # Safely encode the URL so special characters don't break the WebApp
        safe_url = urllib.parse.quote(url, safe='')

        # Generate the final URLs
        final_url_1 = "https://www.teraboxdownloader.pro/p/fs.html?q=" + safe_url
        final_url_2 = "https://teradownloader.com/download?l=" + safe_url

        markup = InlineKeyboardMarkup()
        
        button1 = InlineKeyboardButton(
            text="Watch / Download Server 1", 
            web_app=WebAppInfo(url=final_url_1)
        )
        button2 = InlineKeyboardButton(
            text="Watch / Download Server 2", 
            web_app=WebAppInfo(url=final_url_2)
        )
        
        markup.add(button1)
        markup.add(button2)

        # 5. Send the buttons directly (Animations removed for speed and stability)
        bot.reply_to(
            message, 
            f"✅ **Link Processed!** Choose a server below:\n\n`{url}`", 
            reply_markup=markup,
            parse_mode="Markdown"
        )

# 1. Start the web server for UptimeRobot
keep_alive()

# 2. Start the Telegram bot
print("Bot is running...")
bot.infinity_polling()
