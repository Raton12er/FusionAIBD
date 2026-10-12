import logging
from telegram import Update
from telegram.ext import ContextTypes
from config import PRICING, BKASH_NUMBER, ROCKET_NUMBER, BINANCE_PAY_ID, USDT_TRC20, USDT_BSC20, ADMIN_IDS
from database import create_payment, get_payment, update_payment_status, activate_premium, get_pending_payments
from keyboards import premium_plans_keyboard, durations_keyboard, payment_methods_keyboard, admin_payment_keyboard

logger = logging.getLogger(__name__)

async def premium_cmd(update, context):
    text = "Fusion AI Premium Plans\n\nFree - 20/day\nPro - 200/day\nPremium - Unlimited\nLifetime - One time\n\nSelect a plan:"
    await update.message.reply_text(text, reply_markup=premium_plans_keyboard())

async def buy_cmd(update, context):
    await premium_cmd(update, context)

async def callback_handler(update, context):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "close":
        await query.message.delete()
        return

    if data in ("open_premium", "back_premium"):
        await query.message.edit_text("Select a plan:", reply_markup=premium_plans_keyboard())
        return

    if data.startswith("plan_"):
        plan_id = data.replace("plan_", "")
        await query.message.edit_text("Select duration for " + plan_id.upper() + ":", reply_markup=durations_keyboard(plan_id))
        return

    if data.startswith("dur_"):
        parts = data.split("_")
        plan_id = parts[1]
        dur_id = parts[2]
        d = PRICING[plan_id][dur_id]
        msg = "Amount: Tk " + str(d['price']) + "\nDuration: " + d['label'] + "\n\nSelect payment method:"
        await query.message.edit_text(msg, reply_markup=payment_methods_keyboard(plan_id, dur_id))
        return

    if data.startswith("pay_"):
        parts = data.split("_")
        method = parts[1]
        plan_id = parts[2]
        dur_id = parts[3]
        d = PRICING[plan_id][dur_id]
        amount = d["price"]
        if method == "bkash":
            info = "bKash Personal: " + BKASH_NUMBER
        elif method == "rocket":
            info = "Rocket Personal: " + ROCKET_NUMBER
        elif method == "binance":
            info = "Binance Pay ID: " + BINANCE_PAY_ID
        elif method == "usdt_trc":
            info = "USDT TRC20: " + USDT_TRC20
        elif method == "usdt_bsc":
            info = "USDT BSC20: " + USDT_BSC20
        else:
            info = "Unknown"
        text = "Amount: Tk " + str(amount) + "\nPlan: " + plan_id.upper() + " - " + d['label'] + "\n\n" + info + "\n\nAfter payment send:\nTrxID: YOUR_ID"
        await query.message.edit_text(text)
        context.user_data["pending_payment"] = {"plan": plan_id, "duration": dur_id, "amount": amount, "method": method}
        return

    if data.startswith("adm_ok_"):
        if query.from_user.id not in ADMIN_IDS:
            await query.answer("Not admin!", show_alert=True)
            return
        pid = int(data.replace("adm_ok_", ""))
        await approve_payment(pid, query)
        return

    if data.startswith("adm_no_"):
        if query.from_user.id not in ADMIN_IDS:
            await query.answer("Not admin!", show_alert=True)
            return
        pid = int(data.replace("adm_no_", ""))
        update_payment_status(pid, "rejected")
        await query.message.edit_text("Payment #" + str(pid) + " rejected.")
        return

    if data == "adm_stats":
        from database import get_stats
        s = get_stats()
        text = "Statistics\n\nUsers: " + str(s['total_users']) + "\nPremium: " + str(s['premium_users']) + "\nAsks: " + str(s['total_asks']) + "\nRevenue: Tk " + str(s['revenue'])
        await query.message.edit_text(text)
        return

    if data == "adm_pending":
        pendings = get_pending_payments()
        if not pendings:
            await query.message.edit_text("No pending payments")
            return
        await query.message.edit_text(str(len(pendings)) + " pending payment(s). See /pending")
        return

    if data == "show_refer":
        bu = (await context.bot.get_me()).username
        ref_link = "https://t.me/" + bu + "?start=ref_" + str(query.from_user.id)
        await query.message.edit_text("Your referral link:\n" + ref_link)
        return

async def handle_payment_proof(update, context):
    user = update.effective_user
    pending = context.user_data.get("pending_payment")
    if not pending:
        return False
    text = update.message.text or ""
    trx_id = ""
    if "trxid" in text.lower():
        for line in text.split("\n"):
            if "trxid" in line.lower():
                trx_id = line.split(":", 1)[-1].strip()
                break
    else:
        trx_id = text.strip()
    if not trx_id:
        await update.message.reply_text("Send TrxID with message")
        return True
    pid = create_payment(user.id, user.full_name, pending["plan"], pending["duration"], pending["amount"], pending["method"], trx_id)
    await update.message.reply_text("Payment request received! ID: #" + str(pid) + "\nWait for admin approval.")
    d = PRICING[pending["plan"]][pending["duration"]]
    admin_text = "New Payment\n\nID: #" + str(pid) + "\nUser: " + user.full_name + " (" + str(user.id) + ")\nPlan: " + pending['plan'].upper() + " - " + d['label'] + "\nAmount: Tk " + str(pending['amount']) + "\nMethod: " + pending['method'] + "\nTrxID: " + trx_id
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(chat_id=admin_id, text=admin_text, reply_markup=admin_payment_keyboard(pid))
        except Exception as e:
            logger.error("Admin notify: " + str(e))
    context.user_data.pop("pending_payment", None)
    return True

async def approve_payment(payment_id, query):
    p = get_payment(payment_id)
    if not p:
        await query.message.edit_text("Payment not found")
        return
    d = PRICING[p["plan"]][p["duration"]]
    activate_premium(p["user_id"], p["plan"], d["days"])
    update_payment_status(payment_id, "approved")
    await query.message.edit_text("Payment #" + str(payment_id) + " approved. User " + str(p["user_id"]) + " got " + str(d["days"]) + " days " + p["plan"].upper())
    try:
        await query.bot.send_message(chat_id=p["user_id"], text="Congratulations! Your " + p["plan"].upper() + " plan is active for " + str(d["days"]) + " days.")
    except Exception as e:
        logger.error("User notify: " + str(e))
