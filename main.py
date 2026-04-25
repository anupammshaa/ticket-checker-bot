import telebot, requests, os, threading, time
from flask import Flask

TOKEN = os.environ.get('BOT_TOKEN')
API_KEY = os.environ.get('RAPIDAPI_KEY')
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['pnr'])
def check_pnr(message):
    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "PNR number likhein.")
            return
            
        pnr_no = args[1]
        bot.reply_to(message, "🔍 Server se data nikal raha hu...")

        url = f"https://irctc-indian-railway-pnr-status.p.rapidapi.com/getPNRStatus/{pnr_no}"
        headers = {
            "X-RapidAPI-Key": API_KEY,
            "X-RapidAPI-Host": "irctc-indian-railway-pnr-status.p.rapidapi.com"
        }
        
        response = requests.get(url, headers=headers)
        res = response.json()

        # Agar success sahi hai
        if res.get('success') == True:
            # Data nikalne ki koshish
            data = res.get('data', {})
            pnr_status_list = data.get('pnr_status', [])
            
            if pnr_status_list:
                status = pnr_status_list[0].get('current_status', 'Status nahi mila')
                bot.reply_to(message, f"✅ PNR: {pnr_no}\nStatus: {status}")
            else:
                bot.reply_to(message, "❌ API ne data bheja par status list khali hai.")
        else:
            msg = res.get('message', 'Unknown API Error')
            bot.reply_to(message, f"❌ API Message: {msg}")

    except Exception as e:
        # Ye line aapko Telegram par asli galti batayegi
        bot.reply_to(message, f"⚠️ Technical Error: {str(e)}")

app = Flask(__name__)
@app.route('/')
def home(): return "Active"

if __name__ == "__main__":
    threading.Thread(target=lambda: bot.polling(none_stop=True)).start()
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
