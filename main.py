import telebot
import requests
import os
import threading
from flask import Flask

# Tokens (Seedha yahan daal rahe hain bina kisi galti ke)
TOKEN = "8501333951:AAHSRA5JVmdmWJNvKjzlh_HXaCe8DJ0dJF4"
API_KEY = "44a1f4ca18msh81a7a24cb739bbep16d980jsn9758cb5433bc"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Alive"

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Bot chalu hai! PNR status ke liye likho: /pnr [PNR-Number]")

@bot.message_handler(commands=['pnr'])
def check_pnr(message):
    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "PNR number likhein.")
            return
            
        pnr_no = args[1]
        bot.reply_to(message, "🔍 Server se connect ho raha hu...")

        url = f"https://irctc-indian-railway-pnr-status.p.rapidapi.com/getPNRStatus/{pnr_no}"
        headers = {
            "X-RapidAPI-Key": API_KEY,
            "X-RapidAPI-Host": "irctc-indian-railway-pnr-status.p.rapidapi.com"
        }
        
        response = requests.get(url, headers=headers)
        res = response.json()

        if res.get('success'):
            status = res['data']['pnr_status'][0]['current_status']
            bot.reply_to(message, f"✅ PNR: {pnr_no}\nStatus: {status}")
        else:
            bot.reply_to(message, f"❌ API Message: {res.get('message', 'Subscription check karein')}")

    except Exception as e:
        bot.reply_to(message, f"⚠️ Error: {str(e)}")

def run_bot():
    bot.polling(none_stop=True)

if __name__ == "__main__":
    # Bot ko alag thread mein chalayenge
    threading.Thread(target=run_bot).start()
    # Flask server ko port par chalayenge
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
