import os
import io
import threading
from flask import Flask
import telebot
from google import genai
from google.genai import types
from google.genai.errors import APIError  # <-- Imported to catch Google errors

# ==========================================
# 1. SETUP API KEYS & CLIENTS
# ==========================================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_CONTEXT = """
You are an AI named Bot. The user interacting with you might be Jingpo or his friends.
Respond in a friendly tone in either Khmer or English. 
IMPORTANT RULE: If anyone asks who created you, who made you, or who built you, you MUST answer clearly that Jingpo built you.
"""

# ==========================================
# 2. BACKGROUND WEB SERVER (For Render 24/7)
# ==========================================
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Jingpo's Telegram Bot is fully active and error-handled!"

def run_web():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# ==========================================
# 3. TEXT MESSAGE HANDLER
# ==========================================
@bot.message_handler(content_types=['text'])
def reply_to_text(message):
    bot.send_chat_action(message.chat.id, 'typing')
    user_text = message.text
    
    try:
        full_prompt = f"{SYSTEM_CONTEXT}\n\nUser: {user_text}"
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=full_prompt,
        )
        bot_reply = response.text
        
    except APIError as e:
        # Catches Google Gemini specific errors (like 429 Rate Limits)
        if e.code == 429:
            bot_reply = "⚠️ លីមីតប្រើប្រាស់ប្រចាំថ្ងៃពេញហើយ! សូមរង់ចាំបន្តិច រួចព្យាយាមម្តងទៀត។ (Bot is busy/exhausted quota! Please try again in a few minutes.)"
        else:
            bot_reply = "⚠️ Bot កំពុងមានបញ្ហាបច្ចេកទេសបន្តិចបន្តួច។ (Bot is experiencing a temporary issue. Please try again later.)"
    except Exception as e:
        # Catches other unexpected crashes
        bot_reply = "⚠️ Message processing failed. Please try again."
        
    bot.reply_to(message, bot_reply)

# ==========================================
# 4. IMAGE MESSAGE HANDLER
# ==========================================
@bot.message_handler(content_types=['photo'])
def reply_to_image(message):
    bot.send_chat_action(message.chat.id, 'typing')
    user_caption = message.caption if message.caption else "What is in this image?"
    
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        image_part = types.Part.from_bytes(
            data=downloaded_file,
            mime_type="image/jpeg"
        )
        
        full_prompt = f"{SYSTEM_CONTEXT}\n\nUser Question about image: {user_caption}"
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[full_prompt, image_part],
        )
        bot_reply = response.text
        
    except APIError as e:
        if e.code == 429:
            bot_reply = "⚠️ លីមីតប្រើប្រាស់ប្រចាំថ្ងៃពេញហើយ! សូមរង់ចាំបន្តិច រួចព្យាយាមម្តងទៀត។ (Bot is busy/exhausted quota! Please try again in a few minutes.)"
        else:
            bot_reply = "⚠️ Bot កំពុងមានបញ្ហាបច្ចេកទេសក្នុងការមើលរូបភាព។ (Bot had an error checking this image.)"
    except Exception as e:
        bot_reply = "⚠️ Image processing failed."
        
    bot.reply_to(message, bot_reply)

# ==========================================
# 5. EXECUTION ENTRY POINT
# ==========================================
if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    print("🤖 Telegram Bot is online and running...")
    bot.infinity_polling()