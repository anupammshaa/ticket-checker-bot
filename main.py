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

# User ki data store karne ke liye
seat_alerts = {}
pnr_alerts = {}

@bot.message_handler(commands=['start'])
def start(message):
    welcome_text = (
        "🚂 **Anupam's Railway Assistant** 🚂\n\n"
        "1️⃣ **Instant PNR + Auto Alert:**\n"
        "`/pnr [10-digit-PNR]`\n"
        "_Example: /pnr 4526123456_\n\n"
        "2️⃣ **Seat Availability Alert:**\n"
        "`/alert [Train] [From] [To] [Date] [Class]`\n"
        "_Example: /alert 12155 BPL NZM 28-04-2026 SL_\n\n"
        "Main har 15 minute mein status check karta rahunga!"
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

# --- PNR Command (Instant Status + Monitoring) ---
@bot.message_handler(commands=['pnr'])
def set_pnr(message):
    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "❌ PNR number bhi likhein. Example: `/pnr 1234567890`")
            return
            
        pnr_no = args[1]
        if len(pnr_no) != 10:
            bot.reply_to(message, "❌ PNR 10 digit ka hona chahiye.")
            return
        
        bot.reply_to(message, f"🔍 PNR {pnr_no} ka status check kar raha hu...")
        
        # Instant Status Check
        url = "https://irctc1.p.rapidapi.com/api/v3/getPNRStatus"
        headers = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": "irctc1.p.rapidapi.com"}
        res = requests.get(url, headers=headers, params={"pnrNumber": pnr_no}).json()
        
        if res.get('status'):
            current_status = res['data']['ticket_status'][0]['current_status']
            booking_status = res['data']['ticket_status'][0]['booking_status']
            
            # Abhi ka status turant batayega
            bot.send_message(message.chat.id, f"📊 **ABHI KA STATUS:**\n\nPNR: {pnr_no}\nBooking: {booking_status}\nCurrent: {current_status}\n\n✅ Maine register kar liya hai. Confirm hote hi msg karunga!")
            
            # Background monitor ke liye save karein
            pnr_alerts[message.chat.id] = pnr_no
        else:
            bot.reply_to(message, "❌ PNR details nahi mili. Number check karein.")
    except Exception as e:
        bot.reply_to(message, f"⚠️ Error: {e}")

# --- Seat Alert Command ---
@bot.message_handler(commands=['alert'])
def set_seat_alert(message):
    try:
        args = message.text.split()
        if len(args) < 6:
            bot.reply_to(message, "Format: `/alert [Train] [From] [To] [Date] [Class]`")
            return
        
        seat_alerts[message.chat.id] = {
            'train': args[1], 'from': args[2].upper(), 'to': args[3].upper(),
            'date': args[4], 'class': args[5].upper()
        }
        bot.reply_to(message, f"✅ Seat Alert Set! {args[1]} mein seat milte hi batata hu.")
    except:
        bot.reply_to(message, "❌ Format check karein.")

# --- Background Monitor Loop ---
def monitor_loop():
    while True:
        # PNR Monitoring
        for chat_id, pnr in list(pnr_alerts.items()):
            try:
                url = "https://irctc1.p.rapidapi.com/api/v3/getPNRStatus"
                headers = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": "irctc1.p.rapidapi.com"}
                res = requests.get(url, headers=headers, params={"pnrNumber": pnr}).json()
                
                if res.get('status'):
                    curr = res['data']['ticket_status'][0]['current_status']
                    if "CNF" in curr.upper() or "CONFIRM" in curr.upper():
                        bot.send_message(chat_id, f"🎊 **PNR CONFIRMED!** 🎊\nPNR: {pnr}\nStatus: {curr}")
                        del pnr_alerts[chat_id]
            except: pass

        # Seat Monitoring
        for chat_id, data in list(seat_alerts.items()):
            try:
                url = "https://irctc1.p.rapidapi.com/api/v3/checkSeatAvailability"
                headers = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": "irctc1.p.rapidapi.com"}
                params = {"trainNo": data['train'], "fromStationCode": data['from'], "toStationCode": data['to'], "date": data['date'], "class": data['class'], "quota": "GN"}
                res = requests.get(url, headers=headers, params=params).json()
                
                if res.get('status'):
                    curr = res['data'][0]['current_status']
                    if "AVAILABLE" in curr.upper():
                        bot.send_message(chat_id, f"🚨 **SEAT AVAILABLE!** 🚨\nTrain: {data['train']}\nStatus: {curr}")
                        del seat_alerts[chat_id]
            except: pass

        time.sleep(900) # 15 Minute Sleep

# Server Settings
app = Flask(__name__)
@app.route('/')
def home(): return "Railway Bot Active"

if __name__ == "__main__":
    threading.Thread(target=monitor_loop, daemon=True).start()
    threading.Thread(target=lambda: bot.polling(none_stop=True)).start()
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
