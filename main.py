import telebot
from PIL import Image
import io
import os
from flask import Flask
import threading

TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

user_data = {}

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Anupam bhai, ab ye bot ekdum perfect kaam karega! 🔥\n\n"
                          "1️⃣ Photo bhejein.\n"
                          "2️⃣ Niche diye gaye buttons chunein ya khud likhein (e.g., '50kb' ya '300x400').")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    file_id = message.photo[-1].file_id
    file_info = bot.get_file(file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    
    user_data[message.chat.id] = {'image': downloaded_file}
    
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add('Passport Size', 'Compress to 50KB', 'Compress to 20KB')
    bot.reply_to(message, "Photo mil gayi! Ab size batayein (Example: '40kb' ya '200x300')", reply_markup=markup)

@bot.message_handler(func=lambda m: True)
def process_logic(message):
    chat_id = message.chat.id
    if chat_id not in user_data:
        bot.reply_to(message, "Pehle photo toh bhejo bhai!")
        return

    text = message.text.lower()
    img = Image.open(io.BytesIO(user_data[chat_id]['image']))

    # --- Case 1: Custom Resolution (e.g., 300x400) ---
    if 'x' in text:
        try:
            w, h = map(int, text.split('x'))
            img = img.resize((w, h), Image.Resampling.LANCZOS)
            output = io.BytesIO()
            img.save(output, format="JPEG", quality=90)
            output.seek(0)
            bot.send_document(chat_id, output, visible_file_name=f"resized_{w}x{h}.jpg")
        except:
            bot.reply_to(message, "Sahi format likhein, jaise: 300x400")

    # --- Case 2: Exact KB Compression (e.g., 50kb) ---
    elif 'kb' in text:
        try:
            target_kb = int(text.replace('kb', '').strip())
            bot.reply_to(message, f"Ise {target_kb}KB ke niche la raha hu...")
            
            quality = 95
            for i in range(10): # 10 baar try karega quality ghatane ki
                output = io.BytesIO()
                img.save(output, format="JPEG", quality=quality)
                size_kb = output.tell() / 1024
                
                if size_kb <= target_kb or quality <= 10:
                    break
                quality -= 15 # Har baar quality 15% kam karega
            
            output.seek(0)
            bot.send_document(chat_id, output, visible_file_name=f"compressed_{target_kb}kb.jpg", 
                             caption=f"Size: {size_kb:.1f} KB")
        except:
            bot.reply_to(message, "Sahi KB likhein, jaise: 50kb")

    elif 'passport' in text:
        # Passport Standard (350x450 pixels)
        img = img.resize((350, 450), Image.Resampling.LANCZOS)
        output = io.BytesIO()
        img.save(output, format="JPEG", quality=90)
        output.seek(0)
        bot.send_document(chat_id, output, visible_file_name="passport_size.jpg")

# Server settings
app = Flask(__name__)
@app.route('/')
def home(): return "Photo Bot is Active"

def run(): bot.polling(none_stop=True)

if __name__ == "__main__":
    threading.Thread(target=run).start()
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
