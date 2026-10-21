LIKE-BOT.py
SETUP
1. Open LIKE-BOT.py
2. Add your Telegram BotFather token:
   BOT_TOKEN = "YOUR_BOT_TOKEN"
3. Install packages:
   pip install -r requirements.txt
4. Start the bot:
   python premium_like_bot_v2.py

MAIN COMMAND FORMAT
/Auto REGION UID
/like REGION UID

EXAMPLE
/Auto BD 3058108458 
/like bd 10609031393

The bot will generate this API request automatically:
http://sell-20-like-50-taka.vercel.app/like?uid={uid}&server_name={region}&key=SHAPPNO9X

The old format /like UID REGION is also supported for compatibility.

USER COMMANDS
/start
/like REGION UID
/limit
/id
/ping

OWNER COMMANDS
/Auto REGION UID
/addvip TELEGRAM_ID
/delvip TELEGRAM_ID
/viplist
/ban TELEGRAM_ID
/unban TELEGRAM_ID
/stats
