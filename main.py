import telebot, requests, threading, time
from flask import Flask

# Yahan apni details seedha bhar dein (Bina kisi galti ke)
TOKEN = "8501333951:AAHSRA5JVmdmWJNvKjzlh_HXaCe8DJ0dJF4"
API_KEY = "44a1f4ca18msh81a7a24cb739bbep16d980jsn9758cb5433bc"

bot = telebot.TeleBot(TOKEN)

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

        if res.get('success') == True:
            data = res.get('data', {})
            pnr_status_list = data.get('pnr_status', [])
            if pnr_status_list:
                status = pnr_status_list[0].get('current_status', 'Status nahi mila')
                bot.reply_to(message, f"✅ PNR: {pnr_no}\nStatus: {status}")
            else:
                bot.reply_to(message, "❌ API response khali hai.")
        else:
            bot.reply_to(message, f"❌ API Message: {res.get('message', 'Subscription check karein')}")

    except Exception as e:
        bot.reply_to(message, f"⚠️ Error: {str(e)}")

app = Flask(__name__)
@app.route('/')
def home(): return "Bot Active"

if __name__ == "__main__":
    threading.Thread(target=lambda: bot.polling(none_stop=True)).start()
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
