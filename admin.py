from telegram import Update
from telegram.ext import ContextTypes
from config import ADMIN_IDS
from database import get_stats, get_pending_payments, get_user, update_user, activate_premium
from keyboards import admin_panel_keyboard

def is_admin(user_id):
    return user_id in ADMIN_IDS

async def admin_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return
    await update.message.reply_text("Admin Panel\n\nSelect an option:", reply_markup=admin_panel_keyboard())

async def stats_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return
    s = get_stats()
    await update.message.reply_text("Statistics\n\nUsers: " + str(s['total_users']) + "\nPremium: " + str(s['premium_users']) + "\nAsks: " + str(s['total_asks']) + "\nPayments: " + str(s['approved_payments']) + "\nRevenue: Tk " + str(s['revenue']))

async def pending_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return
    pendings = get_pending_payments()
    if not pendings:
        await update.message.reply_text("No pending payment")
        return
    for p in pendings[:5]:
        await update.message.reply_text("#" + str(p['payment_id']) + "\nUser: " + p['user_name'] + " (" + str(p['user_id']) + ")\n" + p['plan'].upper() + " - Tk " + str(p['amount']) + "\nMethod: " + p['method'] + "\nTrxID: " + p['trx_id'])

async def approve_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return
    try:
        parts = update.message.text.split()
        uid = int(parts[1])
        plan = parts[2]
        days = int(parts[3])
        activate_premium(uid, plan, days)
        await update.message.reply_text(str(uid) + " got " + str(days) + " days " + plan)
    except:
        await update.message.reply_text("Usage: /approve user_id plan days")

async def remove_premium_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return
    try:
        uid = int(update.message.text.split()[1])
        update_user(uid, plan="free", premium_until=None)
        await update.message.reply_text(str(uid) + " premium removed")
    except:
        await update.message.reply_text("Usage: /removepremium user_id")

async def ban_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return
    try:
        uid = int(update.message.text.split()[1])
        update_user(uid, banned=1)
        await update.message.reply_text(str(uid) + " banned")
    except:
        await update.message.reply_text("Usage: /ban user_id")

async def unban_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return
    try:
        uid = int(update.message.text.split()[1])
        update_user(uid, banned=0)
        await update.message.reply_text(str(uid) + " unbanned")
    except:
        await update.message.reply_text("Usage: /unban user_id")

async def userinfo_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return
    try:
        uid = int(update.message.text.split()[1])
        u = get_user(uid)
        if not u:
            await update.message.reply_text("User not found")
            return
        await update.message.reply_text("Name: " + str(u['name']) + "\nID: " + str(u['user_id']) + "\nPlan: " + str(u['plan']) + "\nUntil: " + str(u['premium_until'] or 'N/A') + "\nTotal: " + str(u['total_ask']) + "\nToday: " + str(u['daily_count']) + "\nRefer count: " + str(u['refer_count']))
    except:
        await update.message.reply_text("Usage: /userinfo user_id")

async def broadcast_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return
    msg = update.message.text.replace("/broadcast", "").strip()
    if not msg:
        await update.message.reply_text("Usage: /broadcast message")
        return
    import sqlite3
    from database import DB_PATH
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE banned=0")
    users = [row[0] for row in c.fetchall()]
    conn.close()
    sent = 0
    failed = 0
    for uid in users:
        try:
            await context.bot.send_message(uid, msg)
            sent += 1
        except:
            failed += 1
    await update.message.reply_text("Sent: " + str(sent) + ", Failed: " + str(failed))
