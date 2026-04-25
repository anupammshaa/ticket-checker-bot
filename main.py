import telebot, requests, os, threading
from flask import Flask

# Seedha Token aur Key (Koi galti ki gunjayish nahi)
TOKEN = "8501333951:AAHSRA5JVmdmWJNvKjzlh_HXaCe8DJ0dJF4"
API_KEY = "44a1f4ca18msh81a7a24cb739bbep16d980jsn9758cb5433bc"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Bot Chalu hai! `/pnr [Number]` likho.")

@bot.message_handler(commands=['pnr'])
def check_pnr(message):
    try:
        pnr_no = message.text.split()[1]
        bot.reply_to(message, "🔍 Stable Server se check kar raha hu...")

        # IRCTC1 API (Ye sabse stable hai)
        url = "https://irctc1.p.rapidapi.com/api/v3/getPNRStatus"
        headers = {
            "X-RapidAPI-Key": API_KEY,
            "X-RapidAPI-Host": "irctc1.p.rapidapi.com" # Dono match hone chahiye
        }
        
        response = requests.get(url, headers=headers, params={"pnrNumber": pnr_no})
        res = response.json()

        if res.get('status') == True:
            # Data nikalne ka sahi tarika
            current_status = res['data']['ticket_status'][0]['current_status']
            bot.reply_to(message, f"✅ PNR: {pnr_no}\nStatus: {current_status}")
        else:
            bot.reply_to(message, f"❌ API Error: {res.get('message', 'Data nahi mila')}")

    except Exception as e:
        bot.reply_to(message, f"⚠️ Error: {str(e)}")

@app.route('/')
def home(): return "Bot Running"

if __name__ == "__main__":
    threading.Thread(target=lambda: bot.polling(none_stop=True)).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
