import telebot
from google import genai
import os
import io
from flask import Flask
import threading

# ==========================================
# 1. SETUP API KEYS & CLIENTS
# ==========================================
# These keys are loaded securely from Render's Environment Variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
client = genai.Client(api_key=GEMINI_API_KEY)

# System instruction block to guide the AI behavior
SYSTEM_CONTEXT = """
You are an AI named Bot. The user interacting with you might be Jingpo or his friends.
Respond in a friendly tone in either Khmer or English. 
IMPORTANT RULE: If anyone asks who created you, who made you, or who built you, you MUST answer clearly that Jingpo built you.
"""

# ==========================================
# 2. FAKE WEB SERVER (To stay awake 24/7)
# ==========================================
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Jingpo's Telegram Bot is alive and analyzing images!"

def run_web():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# ==========================================
# 3. TEXT MESSAGE HANDLER
# ==========================================
@bot.message_handler(content_types=['text'])
def reply_to_text(message):
    user_text = message.text
    bot.send_chat_action(message.chat.id, 'typing')
    
    try:
        full_prompt = f"{SYSTEM_CONTEXT}\n\nUser: {user_text}"
        
        # Ask Gemini for the answer
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=full_prompt,
        )
        bot_reply = response.text
        
    except Exception as e:
        bot_reply = f"Error calling Gemini API: {str(e)}"
        
    bot.reply_to(message, bot_reply)

# ==========================================
# 4. IMAGE MESSAGE HANDLER (New Upgrade!)
# ==========================================
@bot.message_handler(content_types=['photo'])
def reply_to_image(message):
    bot.send_chat_action(message.chat.id, 'typing')
    
    # If the user added a caption with the image, use it. Otherwise, default question.
    user_caption = message.caption if message.caption else "What is in this image?"
    
    try:
        # 1. Get the highest resolution photo file from Telegram
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # 2. Convert the raw file bytes into a format Gemini can read
        image_data = {"data": downloaded_file, "mime_type": "image/jpeg"}
        
        # 3. Bundle the system rules, user caption, and image data together
        full_prompt = f"{SYSTEM_CONTEXT}\n\nUser Question about image: {user_caption}"
        contents = [full_prompt, image_data]
        
        # 4. Call Gemini 2.5 Flash to process the image
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents,
        )
        bot_reply = response.text
        
    except Exception as e:
        bot_reply = f"Error processing image with Gemini: {str(e)}"
        
    bot.reply_to(message, bot_reply)

# ==========================================
# 5. RUN BOTH SYSTEMS TOGETHER
# ==========================================
if __name__ == "__main__":
    # Start the web server in a background thread so Render doesn't shut us down
    threading.Thread(target=run_web).start()
    
    # Start checking for Telegram messages/images
    print("🤖 Telegram Bot is running and waiting for text or images...")
    bot.infinity_polling()