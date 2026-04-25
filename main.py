import telebot
import requests
import os
from flask import Flask
import threading
import time

# Tokens
TOKEN = os.environ.get('BOT_TOKEN')
API_KEY = os.environ.get('RAPIDAPI_KEY')
bot = telebot.TeleBot(TOKEN)

pnr_alerts = {}

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🚂 **Anupam's Final PNR Bot** 🚂\n\nLikho: `/pnr [10-digit-number]`")

@bot.message_handler(commands=['pnr'])
def check_pnr(message):
    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "PNR number toh likho!")
            return
            
        pnr_no = args[1]
        bot.reply_to(message, "🔍 Railway server se connect ho raha hu...")

        # Amitesh API URL
        url = f"https://irctc-indian-railway-pnr-status.p.rapidapi.com/getPNRStatus/{pnr_no}"
        headers = {
            "X-RapidAPI-Key": API_KEY,
            "X-RapidAPI-Host": "irctc-indian-railway-pnr-status.p.rapidapi.com"
        }
        
        response = requests.get(url, headers=headers)
        
        # Error Checking
        if response.status_code != 200:
            bot.reply_to(message, f"❌ API Error: Code {response.status_code}. Check RapidAPI Subscription!")
            return

        res = response.json()
        if res.get('success'):
            data = res['data']
            current_status = data['pnr_status'][0]['current_status']
            bot.send_message(message.chat.id, f"✅ **STATUS MIL GAYA!**\n\nPNR: {pnr_no}\nStatus: {current_status}\n\nMain check karta rahunga, confirm hote hi msg aayega!")
            pnr_alerts[message.chat.id] = pnr_no
        else:
            bot.reply_to(message, f"❌ API ne mana kar diya: {res.get('message', 'Galat PNR')}")

    except Exception as e:
        bot.reply_to(message, f"⚠️ Coding Error: {str(e)}")

# Background Monitor (Har 20 minute mein)
def monitor():
    while True:
        for chat_id, pnr in list(pnr_alerts.items()):
            try:
                url = f"https://irctc-indian-railway-pnr-status.p.rapidapi.com/getPNRStatus/{pnr}"
                headers = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": "irctc-indian-railway-pnr-status.p.rapidapi.com"}
                res = requests.get(url, headers=headers).json()
                if res.get('success'):
                    curr = res['data']['pnr_status'][0]['current_status']
                    if "CNF" in curr.upper() or "CONFIRM" in curr.upper():
                        bot.send_message(chat_id, f"🎊 **MUBARAK HO! CONFIRM HO GAYA** 🎊\nPNR: {pnr}\nStatus: {curr}")
                        del pnr_alerts[chat_id]
            except: pass
        time.sleep(1200)

app = Flask(__name__)
@app.route('/')
def home(): return "Active"

if __name__ == "__main__":
    threading.Thread(target=monitor, daemon=True).start()
    threading.Thread(target=lambda: bot.polling(none_stop=True)).start()
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
