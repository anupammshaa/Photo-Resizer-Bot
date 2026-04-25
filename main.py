import telebot
from PIL import Image
import io
import os
from flask import Flask
import threading

TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

user_settings = {}

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Namaste Anupam bhai! 🙏\nMain aapki photo ko Exam Form ke hisaab se resize kar sakta hu.\n\n"
                          "1️⃣ Pehle apni Photo bhejein.\n"
                          "2️⃣ Phir Size (KB) ya Dimension (Width x Height) batayein.")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    # Sabse badi size ki photo lena
    file_id = message.photo[-1].file_id
    file_info = bot.get_file(file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    
    user_settings[message.chat.id] = {'image': downloaded_file}
    
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add('Passport Size (3.5x4.5 cm)', 'Compress to 20-50 KB', 'Custom Resize')
    bot.reply_to(message, "Photo mil gayi! Ab kya karna hai?", reply_markup=markup)

@bot.message_handler(func=lambda m: True)
def process_options(message):
    chat_id = message.chat.id
    if chat_id not in user_settings:
        bot.reply_to(message, "Pehle ek photo bhejein!")
        return

    if message.text == 'Passport Size (3.5x4.5 cm)':
        img = Image.open(io.BytesIO(user_settings[chat_id]['image']))
        # Ratio maintain karke resize karna
        img.thumbnail((350, 450))
        
        output = io.BytesIO()
        img.save(output, format="JPEG", quality=95)
        output.seek(0)
        
        bot.send_photo(chat_id, output, caption="Lo bhai, Passport Size taiyaar hai!")

    elif 'KB' in message.text:
        bot.reply_to(message, "Processing... Main ise 50KB ke niche lane ki koshish kar raha hu.")
        # Yahan compression logic aayega (Quality ghatakar size kam karna)
        img = Image.open(io.BytesIO(user_settings[chat_id]['image']))
        output = io.BytesIO()
        img.save(output, format="JPEG", quality=40) # Quality 40% karke size drop hoga
        output.seek(0)
        bot.send_document(chat_id, output, visible_file_name="resized_photo.jpg")

# Server settings
app = Flask(__name__)
@app.route('/')
def home(): return "Photo Bot is Active"

def run(): bot.polling(none_stop=True)

if __name__ == "__main__":
    threading.Thread(target=run).start()
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
