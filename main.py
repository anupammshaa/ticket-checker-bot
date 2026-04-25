import telebot, requests, os, threading, time
from flask import Flask

# Variables
TOKEN = os.environ.get('BOT_TOKEN')
API_KEY = os.environ.get('RAPIDAPI_KEY')
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['pnr'])
def check_pnr(message):
    try:
        pnr_no = message.text.split()[1]
        bot.reply_to(message, "🔍 Checking...")

        # Amitesh API
        url = f"https://irctc-indian-railway-pnr-status.p.rapidapi.com/getPNRStatus/{pnr_no}"
        headers = {
            "X-RapidAPI-Key": API_KEY,
            "X-RapidAPI-Host": "irctc-indian-railway-pnr-status.p.rapidapi.com"
        }
        
        response = requests.get(url, headers=headers)
        res = response.json()

        if res.get('success'):
            status = res['data']['pnr_status'][0]['current_status']
            bot.reply_to(message, f"✅ Status: {status}")
        else:
            bot.reply_to(message, f"❌ API Problem: {res.get('message')}")

    except Exception as e:
        bot.reply_to(message, f"⚠️ Error: {str(e)}")

# Render ko zinda rakhne ke liye
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is Running"

if __name__ == "__main__":
    threading.Thread(target=lambda: bot.polling(none_stop=True)).start()
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
