import telebot
import requests
import os
from flask import Flask
import threading
import time

# Tokens (Render ke Environment Variables se aayenge)
TOKEN = os.environ.get('BOT_TOKEN')
API_KEY = os.environ.get('RAPIDAPI_KEY')
bot = telebot.TeleBot(TOKEN)

# User ki alerts store karne ke liye
seat_alerts = {}
pnr_alerts = {}

@bot.message_handler(commands=['start'])
def start(message):
    welcome_text = (
        "🚂 **Anupam's Railway Assistant** 🚂\n\n"
        "Main 24/7 seat aur PNR status check karta rahunga!\n\n"
        "1️⃣ **Seat Alert Lagayein:**\n"
        "`/alert [Train] [From] [To] [Date] [Class]`\n"
        "_Example: /alert 12155 BPL NZM 28-04-2026 SL_\n\n"
        "2️⃣ **PNR Status Alert:**\n"
        "`/pnr [10-digit-PNR]`\n"
        "_Example: /pnr 4526123456_\n\n"
        "Har 15 minute mein update milega!"
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

# --- PNR Command ---
@bot.message_handler(commands=['pnr'])
def set_pnr(message):
    try:
        pnr_no = message.text.split()[1]
        if len(pnr_no) != 10:
            bot.reply_to(message, "❌ PNR 10 digit ka hona chahiye.")
            return
        
        pnr_alerts[message.chat.id] = pnr_no
        bot.reply_to(message, f"✅ PNR {pnr_no} register ho gaya! Confirm hote hi message karunga.")
    except:
        bot.reply_to(message, "Sahi format: `/pnr 1234567890`")

# --- Seat Alert Command ---
@bot.message_handler(commands=['alert'])
def set_seat_alert(message):
    try:
        args = message.text.split()
        if len(args) < 6:
            bot.reply_to(message, "Sahi format: `/alert 12155 BPL NZM 28-04-2026 SL`")
            return
        
        seat_alerts[message.chat.id] = {
            'train': args[1], 'from': args[2].upper(), 'to': args[3].upper(),
            'date': args[4], 'class': args[5].upper()
        }
        bot.reply_to(message, f"✅ Seat Alert Set! {args[1]} mein seat milte hi batata hu.")
    except:
        bot.reply_to(message, "Error! Format check karein.")

# --- Background Monitor Loop ---
def monitor_loop():
    while True:
        print("--- Checking Status Round Started ---")
        
        # 1. PNR Check
        for chat_id, pnr in list(pnr_alerts.items()):
            try:
                url = "https://irctc1.p.rapidapi.com/api/v3/getPNRStatus"
                headers = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": "irctc1.p.rapidapi.com"}
                res = requests.get(url, headers=headers, params={"pnrNumber": pnr}).json()
                
                if res.get('status'):
                    current_status = res['data']['ticket_status'][0]['current_status']
                    if "CNF" in current_status.upper() or "CONFIRM" in current_status.upper():
                        bot.send_message(chat_id, f"🎊 **PNR UPDATE:** Aapki ticket CONFIRM ho gayi!\nPNR: {pnr}\nStatus: {current_status}")
                        del pnr_alerts[chat_id]
            except Exception as e: print(f"PNR Error: {e}")

        # 2. Seat Check
        for chat_id, data in list(seat_alerts.items()):
            try:
                url = "https://irctc1.p.rapidapi.com/api/v3/checkSeatAvailability"
                headers = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": "irctc1.p.rapidapi.com"}
                params = {"trainNo": data['train'], "fromStationCode": data['from'], "toStationCode": data['to'], "date": data['date'], "class": data['class'], "quota": "GN"}
                res = requests.get(url, headers=headers, params=params).json()
                
                if res.get('status'):
                    curr_status = res['data'][0]['current_status']
                    if "AVAILABLE" in curr_status.upper():
                        bot.send_message(chat_id, f"🚨 **SEAT MIL GAYI!** 🚨\nTrain: {data['train']}\nStatus: {curr_status}\nJaldi book karein!")
                        del seat_alerts[chat_id]
            except Exception as e: print(f"Seat Error: {e}")

        print("Round Complete. Sleeping for 15 minutes...")
        time.sleep(900) # 15 Minute Sleep

# Server for Render
app = Flask(__name__)
@app.route('/')
def home(): return "Railway Bot Alive"

if __name__ == "__main__":
    threading.Thread(target=monitor_loop, daemon=True).start()
    threading.Thread(target=lambda: bot.polling(none_stop=True)).start()
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
