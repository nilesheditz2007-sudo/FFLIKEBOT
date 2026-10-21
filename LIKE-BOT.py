import logging
from datetime import datetime, timedelta
import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes
)
from telegram.constants import ChatMemberStatus, ChatType
import json
from pathlib import Path

BOT_TOKEN = "8840648014:AAGdVe-to3JM5ohWZH_tTCpTlrRYxXmFSNE"
OWNER_ID = 8739779304
MAIN_GROUP_ID = -1003980053826

API_BASE_URL = "https://silentgmrlikebot.vercel.app/like?uid={uid}&region={region}&key=Nilesh"
DATA_FILE = Path(__file__).parent / "autolike_db.json"

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def load_db():
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text())
        except Exception:
            return {}
    return {}

def save_db(data):
    DATA_FILE.write_text(json.dumps(data, indent=2))

# ---------------- HELPER FUNCTIONS ----------------
async def is_user_in_chat(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in [
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER
        ]
    except Exception:
        return False

async def is_admin_or_owner(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except Exception:
        return False

async def call_like_api(server: str, uid: str) -> dict:
    url = f"{API_BASE_URL}?uid={uid}&region={server}&key=Nilesh"
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(url)
        return response.json()

def is_chat_allowed(update: Update) -> bool:
    chat = update.effective_chat
    return chat.id == MAIN_GROUP_ID or chat.type == ChatType.PRIVATE

# ---------------- COMMAND HANDLERS ----------------
async def handle_like(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_chat_allowed(update):
        return

    if len(context.args) < 2:
        await update.message.reply_text("❌ *Invalid Format!*\n\nUse: `/like <server> <uid>`\nExample: `/like ind 10310075525`", parse_mode="Markdown")
        return

    server = context.args[0].lower()
    uid = context.args[1]

    status_msg = await update.message.reply_text("⏳ *Processing Likes Request...*", parse_mode="Markdown")

    try:
        data = await call_like_api(server, uid)

        nickname = data.get("PlayerNickname", "Unknown")
        likes_given = f"{data.get('LikesGivenByAPI', 0):,}"
        before = f"{data.get('LikesbeforeCommand', 0):,}"
        after = f"{data.get('LikesafterCommand', 0):,}"

        msg = (
            f"╭━〔 ✔️ Lɪᴋᴇꜱ Sᴜᴄᴄᴇꜱꜱ 💗 〕━╮\n\n"
            f"✅ Nᴀᴍᴇ » {nickname}\n"
            f"🎮 Uɪᴅ » `{uid}`\n"
            f"🌎 Rᴇɢɪᴏɴ » {server.upper()}\n\n"
            f"💗 Lɪᴋᴇꜱ Sᴛᴀᴛᴜꜱ\n"
            f"├ Bᴇꜰᴏʀᴇ » {before}\n"
            f"├ Gɪᴠᴇɴ » {likes_given}\n"
            f"└ Aꜰᴛᴇʀ » {after}\n\n"
            f"━━━━━━✦🦋✦━━━━━━━"
        )
        await status_msg.edit_text(msg, parse_mode="Markdown")

    except Exception as e:
        logging.error(f"Error calling like API: {e}")
        await status_msg.edit_text(f"❌ *API Error:* Could not process likes request.\nDetails: `{e}`", parse_mode="Markdown")

async def handle_autolike(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_chat_allowed(update):
        return

    if len(context.args) < 3:
        await update.message.reply_text("❌ *Invalid Format!*\n\nUse: `/autolike <server> <uid> <days>`\nExample: `/autolike ind 10310075525 7`", parse_mode="Markdown")
        return

    server = context.args[0].lower()
    uid = context.args[1]

    try:
        days = int(context.args[2])
        if days <= 0:
            raise ValueError()
    except ValueError:
        await update.message.reply_text("⚠️ *Days must be a valid number!* (e.g., 7)", parse_mode="Markdown")
        return

    user_id = str(update.effective_user.id)
    db = load_db()

    user_data = db.get(user_id, {"targets": []})
    is_admin = await is_admin_or_owner(context, MAIN_GROUP_ID, update.effective_user.id)

    if not is_admin and len(user_data["targets"]) >= 2:
        await update.message.reply_text("⛔ *Limit Reached!*\n\nRegular users can set auto-like for a maximum of **2 UIDs**. Group Admins/Owners have unlimited slots.", parse_mode="Markdown")
        return

    expiry_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")

    new_target = {
        "uid": uid,
        "server": server,
        "days_left": days,
        "expiry": expiry_date,
        "added_on": datetime.now().strftime("%Y-%m-%d")
    }

    user_data["targets"] = [t for t in user_data["targets"] if t["uid"] != uid]
    user_data["targets"].append(new_target)
    db[user_id] = user_data
    save_db(db)

    try:
        api_res = await call_like_api(server, uid)
        nickname = api_res.get("PlayerNickname", "Player")
        before = f"{api_res.get('LikesbeforeCommand', 0):,}"
        given = f"{api_res.get('LikesGivenByAPI', 0):,}"
        after = f"{api_res.get('LikesafterCommand', 0):,}"
    except Exception:
        nickname = "Registered User"
        before, given, after = "N/A", "N/A", "N/A"

    msg = (
        f"╭━〔 ✔️ Aᴜᴛᴏ-ʟɪᴋᴇ Sᴜᴄᴄᴇꜱꜱ 💗 〕━╮\n\n"
        f"✅ Nᴀᴍᴇ » {nickname}\n"
        f"🎮 Uɪᴅ » `{uid}`\n"
        f"🌎 Rᴇɢɪᴏɴ » {server.upper()}\n"
        f"🗓️ Dᴀʏꜱ Lᴇꜰᴛ » {days}\n"
        f"📅 Exᴘɪʀʏ » {expiry_date}\n\n"
        f"💗 Lɪᴋᴇꜱ Sᴛᴀᴛᴜꜱ\n"
        f"├ Bᴇꜰᴏʀᴇ » {before}\n"
        f"├ Gɪᴠᴇɴ » {given}\n"
        f"└ Aꜰᴛᴇʀ » {after}\n\n"
        f"━━━━━━✦🦋✦━━━━━━━"
    )

    await update.message.reply_text(msg, parse_mode="Markdown")

async def handle_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_chat_allowed(update):
        return

    if len(context.args) < 1:
        await update.message.reply_text("❌ *Invalid Format!*\n\nUse: `/remove <uid>`", parse_mode="Markdown")
        return

    uid_to_remove = context.args[0]
    caller_id = update.effective_user.id
    caller_id_str = str(caller_id)
    is_admin = await is_admin_or_owner(context, MAIN_GROUP_ID, caller_id)

    db = load_db()
    found = False

    if not is_admin:
        if caller_id_str in db:
            user_targets = db[caller_id_str].get("targets", [])
            initial_count = len(user_targets)
            db[caller_id_str]["targets"] = [t for t in user_targets if t["uid"] != uid_to_remove]

            if len(db[caller_id_str]["targets"]) < initial_count:
                found = True
                if not db[caller_id_str]["targets"]:
                    del db[caller_id_str]
                save_db(db)

        if found:
            await update.message.reply_text(f"🗑️ *UID Removed!*\n\nUID `{uid_to_remove}` has been removed from your active list.", parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ *Error:* UID not found in your active list.", parse_mode="Markdown")

    else:
        for u_id, u_data in list(db.items()):
            initial_count = len(u_data.get("targets", []))
            u_data["targets"] = [t for t in u_data.get("targets", []) if t["uid"] != uid_to_remove]

            if len(u_data["targets"]) < initial_count:
                found = True
                if not u_data["targets"]:
                    del db[u_id]
                else:
                    db[u_id] = u_data

        if found:
            save_db(db)
            await update.message.reply_text(f"🛡️ *[ADMIN ACTION]*\n\nUID `{uid_to_remove}` has been removed from the database.", parse_mode="Markdown")
        else:
            await update.message.reply_text(f"❌ *Error:* UID `{uid_to_remove}` not found in the database.", parse_mode="Markdown")

async def my_autolikes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_chat_allowed(update):
        return

    user_id = str(update.effective_user.id)
    db = load_db()
    targets = db.get(user_id, {}).get("targets", [])

    if not targets:
        await update.message.reply_text("📂 You currently have no active Auto-Like tasks.", parse_mode="Markdown")
        return

    lines = []
    for t in targets:
        lines.append(f"┣ 🎮 `{t['uid']}` ({t['server'].upper()}) ➔ `{t['days_left']} Days Left` (Exp: {t.get('expiry', 'N/A')})")

    msg = "📂 *Y O U R   A U T O - L I K E S*\n──────────────────────────────\n" + "\n".join(lines)
    await update.message.reply_text(msg, parse_mode="Markdown")

async def daily_autolike_cron(app: Application):
    logging.info("⏰ Starting Daily 4:00 AM Auto-Like Task...")
    db = load_db()
    updated_db = {}

    for user_id_str, user_data in db.items():
        user_id = int(user_id_str)

        still_in_group = await is_user_in_chat(app, MAIN_GROUP_ID, user_id)
        if not still_in_group:
            logging.info(f"User {user_id} left group. Removing auto-like tasks.")
            continue

        active_targets = []
        for target in user_data.get("targets", []):
            uid = target["uid"]
            server = target["server"]
            days_left = target["days_left"]

            if days_left > 0:
                try:
                    res = await call_like_api(server, uid)
                    nickname = res.get("PlayerNickname", "User")
                    before = f"{res.get('LikesbeforeCommand', 0):,}"
                    given = f"{res.get('LikesGivenByAPI', 0):,}"
                    after = f"{res.get('LikesafterCommand', 0):,}"

                    cron_msg = (
                        f"╭━〔 ✔️ Aᴜᴛᴏ-ʟɪᴋᴇ Sᴜᴄᴄᴇꜱꜱ 💗 〕━╮\n\n"
                        f"✅ Nᴀᴍᴇ » {nickname}\n"
                        f"🎮 Uɪᴅ » `{uid}`\n"
                        f"🌎 Rᴇɢɪᴏɴ » {server.upper()}\n"
                        f"🗓️ Dᴀʏꜱ Lᴇꜰᴛ » {days_left - 1}\n"
                        f"📅 Exᴘɪʀʏ » {target.get('expiry', 'N/A')}\n\n"
                        f"💗 Lɪᴋᴇꜱ Sᴛᴀᴛᴜꜱ\n"
                        f"├ Bᴇꜰᴏʀᴇ » {before}\n"
                        f"├ Gɪᴠᴇɴ » {given}\n"
                        f"└ Aꜰᴛᴇʀ » {after}\n\n"
                        f"━━━━━━✦🦋✦━━━━━━━"
                    )
                    await app.bot.send_message(chat_id=MAIN_GROUP_ID, text=cron_msg, parse_mode="Markdown")
                except Exception as e:
                    logging.error(f"Failed auto-like UID {uid}: {e}")

                target["days_left"] = days_left - 1

                if target["days_left"] > 0:
                    active_targets.append(target)

        if active_targets:
            updated_db[user_id_str] = {"targets": active_targets}

    save_db(updated_db)
    logging.info("✅ Daily 4:00 AM Auto-Like Task Completed.")

def main():
    scheduler = AsyncIOScheduler(timezone="Asia/Kolkata")

    async def post_init(app: Application):
        scheduler.add_job(daily_autolike_cron, "cron", hour=4, minute=0, args=[app])
        scheduler.start()
        logging.info("🕐 Scheduler started (daily job set for 04:00 AM IST).")

    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("like", handle_like))
    app.add_handler(CommandHandler("autolike", handle_autolike))
    app.add_handler(CommandHandler("remove", handle_remove))
    app.add_handler(CommandHandler("myautolike", my_autolikes))

    logging.info("🚀 FF Auto-Like Bot Started Successfully!")
    app.run_polling()

if __name__ == "__main__":
    main()
