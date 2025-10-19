
import telebot
import yt_dlp
import re
import os

# Replace with your bot token
bot = telebot.TeleBot('8301963675:AAGf0NNо6AStRZwG1tAUI9wfQcCjajRx9HI')

# Store user states and choices
user_data = {}

@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    user_data[user_id] = {'state': 'waiting_for_link'}
    
    welcome_text = """
🎬 PREMIUM Video Downloader Bot 🎬

Choose your QUALITY & Get INSTANT Downloads!

Supported Sites:
✅ YouTube • Instagram • Facebook
✅ X/Twitter • Snapchat

Just send your link! 👇

*Example:* https://www.youtube.com/watch?v=dQw4w9WgXcQ
"""
    
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = telebot.types.KeyboardButton("🎥 Send Link")
    markup.add(btn1)
    
    bot.send_message(message.chat.id, welcome_text, parse_mode='Markdown', reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    text = message.text.strip()
    
    # Check current state
    state = user_data.get(user_id, {}).get('state', 'waiting_for_link')
    
    if state == 'waiting_for_link':
        urls = re.findall(r'https?://[^\s]+', text)
        
        if not urls:
            bot.send_message(message.chat.id, 
                           "❌ No link found!\n\n📝 *Paste a video link:*\nhttps://youtube.com/watch?v=...", 
                           parse_mode='Markdown')
            return
        
        # Save URL and show quality options
        user_data[user_id] = {'state': 'waiting_for_quality', 'urls': urls}
        
        # Show quality buttons
        markup = telebot.types.InlineKeyboardMarkup(row_width=2)
        btn_720 = telebot.types.InlineKeyboardButton("🎬 720p HD", callback_data="quality_720")
        btn_480 = telebot.types.InlineKeyboardButton("📺 480p", callback_data="quality_480")
        btn_360 = telebot.types.InlineKeyboardButton("📱 360p", callback_data="quality_360")
        btn_audio = telebot.types.InlineKeyboardButton("🎵 Audio Only", callback_data="quality_audio")
        markup.add(btn_720, btn_480, btn_360, btn_audio)
        
        bot.send_message(
            message.chat.id,
            f"🎯 Choose QUALITY for:\n{urls[0][:50]}...\n\n*Fastest = 360p | Best = 720p*",
            parse_mode='Markdown',
            reply_markup=markup
        )
        
    elif state == 'waiting_for_quality':
        bot.send_message(message.chat.id, "👆 Please tap a QUALITY button above!")

@bot.callback_query_handler(func=lambda call: True)
def handle_quality_selection(call):
    user_id = call.from_user.id
    quality = call.data.split('_')[1]
    
    # Update user data
    user_data[user_id]['quality'] = quality
    urls = user_data[user_id]['urls']
    user_data[user_id]['state'] = 'processing'
    
    bot.answer_callback_query(call.id)
    bot.edit_message_text("⏳ Starting downloads...", call.message.chat.id, call.message.message_id)
    
    # Process each URL
    for i, url in enumerate(urls, 1):
        process_single_url(user_id, url, i, len(urls), quality)
    
    # Reset for next download
    user_data[user_id]['state'] = 'waiting_for_link'
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = telebot.types.KeyboardButton("🎥 Send Link")
    markup.add(btn1)
    bot.send_message(
        user_id,
        "🎉 DONE! Want another video?\nJust send a new link! 👇",
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
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Video')
            duration = info.get('duration', 0)
            
            # Download
            ydl.download([url])
            filename = ydl.prepare_filename(info)
        
        # Send file
        if file_type == 'video':
            with open(filename, 'rb') as video_file:
                caption = f"✅ {quality.upper()} from:\n{url}\n\n*{title}*\n⏱ {duration//60}:{duration%60:02d}"
                bot.send_video(
                    user_id,
                    video_file,
                    caption=caption,
                    parse_mode='Markdown',
                    supports_streaming=True
                )
        else:  # audio
            with open(filename, 'rb') as audio_file:
                caption = f"✅ AUDIO from:\n{url}\n\n*{title}*\n⏱ {duration//60}:{duration%60:02d}"
                bot.send_audio(
                    user_id,
                    audio_file,
                    caption=caption,
                    parse_mode='Markdown',
                    title=title[:50]
                )
        
        # Cleanup
        os.remove(filename)
        
    except Exception as e:
        error_msg = f"❌ Failed: {url}\n\n*{str(e)[:80]}*"
        bot.send_message(user_id, error_msg, parse_mode='Markdown')

@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = """
🎯 QUALITY GUIDE:

• 720p HD - Best video (20-100MB)
• 480p - Good balance (10-50MB) 
• 360p - Fastest (5-20MB)
• Audio - Music only (1-10MB)

Pro Tips:
• YouTube = All qualities work!
• Instagram/FB = Auto best available
• Twitter = Usually 480p max

🚀 Send /start to begin!
"""
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown')

print("🤖 PREMIUM Bot with QUALITY Selection Started!")
bot.polling()