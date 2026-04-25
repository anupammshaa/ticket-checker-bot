import telebot
import requests
import os
from flask import Flask
import threading
import time

TOKEN = os.environ.get('BOT_TOKEN')
API_KEY = os.environ.get('RAPIDAPI_KEY') # RapidAPI se milegi
bot = telebot.TeleBot(TOKEN)

# Alert list store karne ke liye
alerts = {}

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Anupam bhai, Ticket Auto-Alert Bot taiyaar hai! 🚂\n\n"
                          "Alert lagane ke liye aise likhein:\n"
                          "`/alert [Train_No] [From] [To] [Date] [Class]`\n\n"
                          "Example: `/alert 12155 BPL NZM 28-04-2026 SL`")

@bot.message_handler(commands=['alert'])
def set_alert(message):
    try:
        args = message.text.split()
        if len(args) < 6:
            bot.reply_to(message, "Sahi format: `/alert 12155 BPL NZM 28-04-2026 SL`")
            return
        
        chat_id = message.chat.id
        alert_data = {
            'train': args[1],
            'from': args[2].upper(),
            'to': args[3].upper(),
            'date': args[4],
            'class': args[5].upper()
        }
        
        alerts[chat_id] = alert_data
        bot.reply_to(message, f"✅ Alert Set! Main har 15 minute mein check karunga. Seat milte hi batata hu.")
    except Exception as e:
        bot.reply_to(message, f"⚠️ Error: {e}")

def check_tickets_loop():
    while True:
        for chat_id, data in list(alerts.items()):
            try:
                url = "https://irctc1.p.rapidapi.com/api/v1/checkSeatAvailability"
                querystring = {
                    "trainNo": data['train'],
                    "fromStationCode": data['from'],
                    "toStationCode": data['to'],
                    "date": data['date'],
                    "class": data['class'],
                    "quota": "GN"
                }
                headers = {
                    "X-RapidAPI-Key": API_KEY,
                    "X-RapidAPI-Host": "irctc1.p.rapidapi.com"
                }
                
                response = requests.get(url, headers=headers, params=querystring)
                res_data = response.json()
                
                if res_data.get('status'):
                    current_status = res_data['data'][0]['current_status']
                    
                    # Agar status 'AVAILABLE' hai toh turant message bhejo
                    if "AVAILABLE" in current_status.upper():
                        bot.send_message(chat_id, f"🚨 **KHUSHKHABRI ANUPAM BHAI!** 🚨\n\n"
                                                  f"Train {data['train']} mein seat mil gayi hai!\n"
                                                  f"Status: {current_status}\n"
                                                  f"Jaldi jaakar book karo! 🏃‍♂️💨")
                        # Ek baar mil gayi toh alert hata do
                        del alerts[chat_id]
                
            except Exception as e:
                print(f"Loop Error: {e}")
        
        # 15 minute ka intezar (900 seconds)
        time.sleep(900)

# Server for Render
app = Flask(__name__)
@app.route('/')
def home(): return "Ticket Alert Bot is Running"

if __name__ == "__main__":
    # Alert loop ko alag thread mein chalana
    threading.Thread(target=check_tickets_loop, daemon=True).start()
    
    # Bot polling aur Flask server
    threading.Thread(target=lambda: bot.polling(none_stop=True)).start()
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
