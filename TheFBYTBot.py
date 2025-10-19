
import telebot
import yt_dlp
import re
import os
import threading
import http.server
import socketserver

# Replace with your bot token
bot = telebot.TeleBot('8389013020:AAEgFno5oFJkTW4kj3uxXZzHLvY0mV2PFOY')

# Store user states and choices
user_data = {}

# Path to cookies file (upload to server)
COOKIES_FILE = 'cookies.txt'

# Optional: Dummy HTTP server for Render Web Service
"""
def run_dummy_server():
    PORT = int(os.environ.get('PORT', 10000))
    Handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
        print(f"🌐 Dummy server running on port {PORT}")
        httpd.serve_forever()

# Uncomment to enable dummy server for Render Web Service
# threading.Thread(target=run_dummy_server, daemon=True).start()
"""

@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    user_data[user_id] = {'state': 'waiting_for_link'}
    
    welcome_text = """
🎬 **PREMIUM Video Downloader Bot** 🎬

**Choose QUALITY & Download from YouTube, Instagram, Facebook, X/Twitter, Snapchat!**

**How to Use:**
1️⃣ Send a video link
2️⃣ Pick a quality (720p, 480p, 360p, Audio)
3️⃣ Get your video instantly!

**For Private Videos:**
- Upload a cookies file (ask me how with /help)

📝 *Example:* https://youtu.be/dQw4w9WgXcQ
"""
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = telebot.types.KeyboardButton("🎥 Send Link")
    markup.add(btn1)
    
    bot.send_message(message.chat.id, welcome_text, parse_mode='Markdown', reply_markup=markup)

@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = """
🎯 **QUALITY GUIDE:**
• **720p HD** - Best video (20-100MB)
• **480p** - Good balance (10-50MB)
• **360p** - Fastest (5-20MB)
• **Audio** - Music only (1-10MB)

**Private Videos (YouTube/Facebook):**
1. Open browser in **incognito mode**
2. Log into YouTube/Facebook
3. Go to `https://www.youtube.com/robots.txt` (YouTube) or any video page
4. Use **Get cookies.txt LOCALLY** (Chrome) or **cookies.txt** (Firefox)
5. Save as `cookies.txt` & upload to server
6. Try again!

**Tips:**
• YouTube: All qualities work
• Instagram/FB: Best available quality
• Twitter/Snapchat: Usually 480p max
• Errors? Send /help or check your link

🚀 Send /start to begin!
"""
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    text = message.text.strip()
    
    state = user_data.get(user_id, {}).get('state', 'waiting_for_link')
    
    if state == 'waiting_for_link':
        urls = re.findall(r'https?://[^\s]+', text)
        
        if not urls:
            bot.send_message(message.chat.id, 
                           "❌ No link found!\n\n📝 *Paste a video link:*\nhttps://youtu.be/...", 
                           parse_mode='Markdown')
            return
        
        user_data[user_id] = {'state': 'waiting_for_quality', 'urls': urls}
        
        markup = telebot.types.InlineKeyboardMarkup(row_width=2)
        btn_720 = telebot.types.InlineKeyboardButton("🎬 720p HD", callback_data="quality_720")
        btn_480 = telebot.types.InlineKeyboardButton("📺 480p", callback_data="quality_480")
        btn_360 = telebot.types.InlineKeyboardButton("📱 360p", callback_data="quality_360")
        btn_audio = telebot.types.InlineKeyboardButton("🎵 Audio Only", callback_data="quality_audio")
        markup.add(btn_720, btn_480, btn_360, btn_audio)
        
        bot.send_message(
            message.chat.id,
            f"🎯 **Choose QUALITY** for:\n{urls[0][:50]}...\n\n*Fastest = 360p | Best = 720p*",
            parse_mode='Markdown',
            reply_markup=markup
        )
        
    elif state == 'waiting_for_quality':
        bot.send_message(message.chat.id, "👆 Please tap a QUALITY button above!")

@bot.callback_query_handler(func=lambda call: True)
def handle_quality_selection(call):
    user_id = call.from_user.id
    quality = call.data.split('_')[1]
    
    user_data[user_id]['quality'] = quality
    urls = user_data[user_id]['urls']
    user_data[user_id]['state'] = 'processing'
    
    bot.answer_callback_query(call.id)
    bot.edit_message_text("⏳ Starting downloads...", call.message.chat.id, call.message.message_id)
    
    for i, url in enumerate(urls, 1):
        process_single_url(user_id, url, i, len(urls), quality)
    
    user_data[user_id]['state'] = 'waiting_for_link'
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = telebot.types.KeyboardButton("🎥 Send Link")
    markup.add(btn1)
    bot.send_message(
        user_id,
        "🎉 **DONE!** Want another video?\nJust send a new link! 👇",
        reply_markup=markup
    )

def process_single_url(user_id, url, current, total, quality):
    bot.send_message(user_id, f"⏳ Downloading {current}/{total}...")
    
    try:
        # QUALITY SETTINGS
        if quality == '720':
            format_str = 'bestvideo[height<=720]+bestaudio/best[height<=720]'
            file_type = 'video'
        elif quality == '480':
            format_str = 'bestvideo[height<=480]+bestaudio/best[height<=480]'
            file_type = 'video'
        elif quality == '360':
            format_str = 'bestvideo[height<=360]+bestaudio/best[height<=360]'
            file_type = 'video'
        else:  # audio
            format_str = 'bestaudio/best'
            file_type = 'audio'
        
        ydl_opts = {
            'format': format_str,
            'outtmpl': f'{user_id}_{current}_%(title)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
        }
        
        # Add cookies if file exists
        if os.path.exists(COOKIES_FILE):
            ydl_opts['cookiefile'] = COOKIES_FILE
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Video')
            duration = info.get('duration', 0)
            
            ydl.download([url])
            filename = ydl.prepare_filename(info)
        
        if file_type == 'video':
            with open(filename, 'rb') as video_file:
                caption = f"✅ **{quality.upper()}** from:\n{url}\n\n*{title}*\n⏱ {duration//60}:{duration%60:02d}"
                bot.send_video(
                    user_id,
                    video_file,
                    caption=caption,
                    parse_mode='Markdown',
                    supports_streaming=True
                )
        else:
            with open(filename, 'rb') as audio_file:
                caption = f"✅ **AUDIO** from:\n{url}\n\n*{title}*\n⏱ {duration//60}:{duration%60:02d}"
                bot.send_audio(
                    user_id,
                    audio_file,
                    caption=caption,
                    parse_mode='Markdown',
                    title=title[:50]
                )
        
        os.remove(filename)
        
    except Exception as e:
        error_msg = f"❌ **Failed:** {url}\n\n"
        if "Sign in to confirm you’re not a bot" in str(e):
            error_msg += "🔐 *Authentication needed!* Please upload a cookies file (see /help)."
        elif "Unsupported URL" in str(e):
            error_msg += "🚫 *Invalid URL!* Ensure it's a direct video link (not a login page)."
        else:
            error_msg += f"*{str(e)[:80]}*"
        bot.send_message(user_id, error_msg, parse_mode='Markdown')

print("🤖 PREMIUM Bot with QUALITY Selection & Cookies Support Started!")
bot.polling()
