from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import PLANS, PRICING

def premium_plans_keyboard():
    buttons = []
    for plan_id, plan in PLANS.items():
        if plan_id == "free":
            continue
        buttons.append([InlineKeyboardButton(plan['name'] + " - Tk " + str(plan['price_bdt']), callback_data="plan_" + plan_id)])
    buttons.append([InlineKeyboardButton("Close", callback_data="close")])
    return InlineKeyboardMarkup(buttons)

def durations_keyboard(plan_id):
    buttons = []
    if plan_id in PRICING:
        for dur_id, d in PRICING[plan_id].items():
            buttons.append([InlineKeyboardButton(d['label'] + " - Tk " + str(d['price']), callback_data="dur_" + plan_id + "_" + dur_id)])
    buttons.append([InlineKeyboardButton("Back", callback_data="back_premium")])
    return InlineKeyboardMarkup(buttons)

def payment_methods_keyboard(plan_id, dur_id):
    buttons = [
        [InlineKeyboardButton("bKash", callback_data="pay_bkash_" + plan_id + "_" + dur_id)],
        [InlineKeyboardButton("Rocket", callback_data="pay_rocket_" + plan_id + "_" + dur_id)],
        [InlineKeyboardButton("Binance Pay", callback_data="pay_binance_" + plan_id + "_" + dur_id)],
        [InlineKeyboardButton("USDT TRC20", callback_data="pay_usdt_trc_" + plan_id + "_" + dur_id)],
        [InlineKeyboardButton("USDT BSC20", callback_data="pay_usdt_bsc_" + plan_id + "_" + dur_id)],
        [InlineKeyboardButton("Back", callback_data="plan_" + plan_id)],
    ]
    return InlineKeyboardMarkup(buttons)

def admin_payment_keyboard(payment_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Approve", callback_data="adm_ok_" + str(payment_id)), InlineKeyboardButton("Reject", callback_data="adm_no_" + str(payment_id))]
    ])

def admin_panel_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Stats", callback_data="adm_stats")],
        [InlineKeyboardButton("Pending", callback_data="adm_pending")],
        [InlineKeyboardButton("Close", callback_data="close")],
    ])

def my_account_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Buy Premium", callback_data="open_premium")],
        [InlineKeyboardButton("Refer Link", callback_data="show_refer")],
        [InlineKeyboardButton("Close", callback_data="close")],
    ])
