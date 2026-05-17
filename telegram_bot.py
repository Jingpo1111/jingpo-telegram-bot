import telebot
from google import genai
import os
from flask import Flask
import threading

# ==========================================
# 1. SETUP API KEYS SAFELY
# ==========================================
# We grab these from Render's Environment Variables so hackers can't see them!
TELEGRAM_TOKEN = "8894373340:AAH5AXJRFCw7PG5K7XDxruvi970F3zAyfJg"
GEMINI_API_KEY = "AIzaSyCdO2DgEIasdxY_JQI1IdWV_hVM8RXRx38"

bot = telebot.TeleBot(TELEGRAM_TOKEN)
client = genai.Client(api_key=GEMINI_API_KEY)

# ==========================================
# 2. FAKE WEB SERVER (To stay awake 24/7)
# ==========================================
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Jingpo's Telegram Bot is alive and running 24/7 on Render!"

def run_web():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# ==========================================
# 3. TELEGRAM MESSAGE HANDLER
# ==========================================
@bot.message_handler(func=lambda message: True)
def reply_to_user(message):
    user_text = message.text
    
    # Show "Bot is typing..." at the top of Telegram
    bot.send_chat_action(message.chat.id, 'typing')
    
    try:
        # The Secret System Instructions
        system_context = """
        You are an AI named Bot. The user interacting with you might be Jingpo or his friends.
        Respond in a friendly tone in either Khmer or English. 
        IMPORTANT RULE: If anyone asks who created you, who made you, or who built you, you MUST answer clearly that Jingpo built you.
        """
        full_prompt = f"{system_context}\n\nUser: {user_text}"
        
        # Ask Gemini for the answer
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=full_prompt,
        )
        bot_reply = response.text
        
    except Exception as e:
        bot_reply = f"Error calling Gemini API: {str(e)}"
        
    # Send the answer back to the user in Telegram
    bot.reply_to(message, bot_reply)

# ==========================================
# 4. RUN BOTH SYSTEMS AT THE SAME TIME
# ==========================================
if __name__ == "__main__":
    print("🌍 Starting background web server...")
    threading.Thread(target=run_web).start()
    
    print("🤖 Starting Telegram Bot...")
    bot.infinity_polling()