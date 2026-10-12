import logging, time
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from config import BOT_TOKEN, FUSION_BADGE, ANTI_SPAM_SECONDS
from database import init_db, get_user, create_user, update_user, increment_ask, check_daily_limit, is_premium_active, add_history, get_history
from ai_engine import fusion_mode, fast_mode, smart_mode, code_mode, detect_language
from payment import premium_cmd, callback_handler, handle_payment_proof
from admin import admin_cmd, stats_cmd, pending_cmd, approve_cmd, remove_premium_cmd, ban_cmd, unban_cmd, userinfo_cmd, broadcast_cmd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
user_last = {}

def is_spam(uid):
    now = time.time()
    if str(uid) in user_last and now - user_last[str(uid)] < ANTI_SPAM_SECONDS:
        return True
    user_last[str(uid)] = now
    return False

async def start(update, context):
    user = update.effective_user
    refer_by = None
    if context.args and context.args[0].startswith("ref_"):
        try:
            refer_by = int(context.args[0].replace("ref_", ""))
            if refer_by == user.id:
                refer_by = None
        except:
            pass
    existing = get_user(user.id)
    if not existing:
        create_user(user.id, user.full_name, user.username or "", refer_by)
    update_user(user.id, mode="fusion")
    m = "Welcome " + user.full_name
    m += "\n\nFusion AI BD - 3 AI in One\n\n"
    m += "/fusion - 3 AI Mix\n/fast - Groq\n/smart - Gemini\n"
    m += "/code - Code Help\n/premium - Premium\n/myaccount - Account\n"
    m += "/refer - Referral\n/history - History\n/help - Help\n\n"
    m += "Send any question!"
    await update.message.reply_text(m)

async def help_cmd(update, context):
    await update.message.reply_text("/start /fusion /fast /smart /code /premium /myaccount /refer /history /about")

async def about_cmd(update, context):
    await update.message.reply_text("Fusion AI BD - 3 AI in One: Groq + Gemini + DeepSeek")

async def fusion_cmd(update, context):
    update_user(update.effective_user.id, mode="fusion")
    await update.message.reply_text("Fusion Mode ON")

async def fast_cmd(update, context):
    update_user(update.effective_user.id, mode="fast")
    await update.message.reply_text("Fast Mode ON")

async def smart_cmd(update, context):
    update_user(update.effective_user.id, mode="smart")
    await update.message.reply_text("Smart Mode ON")

async def code_prompt(update, context):
    update_user(update.effective_user.id, mode="code")
    await update.message.reply_text("Code Mode ON - Send problem")

async def myaccount_cmd(update, context):
    u = get_user(update.effective_user.id)
    if not u:
        await update.message.reply_text("Send /start first")
        return
    p = "Active" if is_premium_active(update.effective_user.id) else "Not Active"
    m = "Name: " + str(u['name']) + "\nPlan: " + str(u['plan'])
    m += "\nPremium: " + p + "\nTotal Asks: " + str(u['total_ask'])
    m += "\nToday: " + str(u['daily_count']) + "\nMode: " + str(u['mode'])
    await update.message.reply_text(m)

async def refer_cmd(update, context):
    bu = (await context.bot.get_me()).username
    link = "https://t.me/" + bu + "?start=ref_" + str(update.effective_user.id)
    await update.message.reply_text("Your referral link:\n" + link)

async def history_cmd(update, context):
    hist = get_history(update.effective_user.id, 10)
    if not hist:
        await update.message.reply_text("No history")
        return
    text = "Last 10 questions:\n"
    for i, h in enumerate(hist, 1):
        text += str(i) + ". " + h['question'][:60] + "\n"
    await update.message.reply_text(text)

async def handle_message(update, context):
    user = update.effective_user
    question = update.message.text.strip()
    if not question:
        return
    if await handle_payment_proof(update, context):
        return
    u = get_user(user.id)
    if u and u.get("banned"):
        await update.message.reply_text("You are banned")
        return
    if is_spam(user.id):
        await update.message.reply_text("Slow down! Wait 5 seconds")
        return
    if not u:
        create_user(user.id, user.full_name, user.username or "")
        u = get_user(user.id)
    if not check_daily_limit(user.id, u["plan"]):
        await update.message.reply_text("Daily limit reached! Use /premium")
        return
    mode = u["mode"]
    lang = detect_language(question)
    await context.bot.send_chat_action(update.effective_chat.id, "typing")
    thinking = await update.message.reply_text("3 AI thinking...")
    try:
        if mode == "fast":
            answer = await fast_mode(question)
        elif mode == "smart":
            answer = await smart_mode(question)
        elif mode == "code":
            answer = await code_mode(question)
        else:
            answer = await fusion_mode(question, lang)
        if mode == "fusion":
            answer += FUSION_BADGE
        increment_ask(user.id)
        add_history(user.id, question, answer, mode)
        if len(answer) > 4000:
            await thinking.edit_text(answer[:4000])
            await update.message.reply_text(answer[4000:8000])
        else:
            await thinking.edit_text(answer)
    except Exception as e:
        logger.error(str(e))
        await thinking.edit_text("Error occurred. Try again.")

async def post_init(app):
    await app.bot.set_my_commands([
        BotCommand("start", "Start"),
        BotCommand("fusion", "Fusion Mode"),
        BotCommand("fast", "Fast Mode"),
        BotCommand("smart", "Smart Mode"),
        BotCommand("code", "Code Help"),
        BotCommand("premium", "Premium"),
        BotCommand("myaccount", "Account"),
        BotCommand("help", "Help"),
    ])

def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("about", about_cmd))
    app.add_handler(CommandHandler("fusion", fusion_cmd))
    app.add_handler(CommandHandler("fast", fast_cmd))
    app.add_handler(CommandHandler("smart", smart_cmd))
    app.add_handler(CommandHandler("code", code_prompt))
    app.add_handler(CommandHandler("premium", premium_cmd))
    app.add_handler(CommandHandler("myaccount", myaccount_cmd))
    app.add_handler(CommandHandler("refer", refer_cmd))
    app.add_handler(CommandHandler("history", history_cmd))
    app.add_handler(CommandHandler("admin", admin_cmd))
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(CommandHandler("pending", pending_cmd))
    app.add_handler(CommandHandler("approve", approve_cmd))
    app.add_handler(CommandHandler("removepremium", remove_premium_cmd))
    app.add_handler(CommandHandler("ban", ban_cmd))
    app.add_handler(CommandHandler("unban", unban_cmd))
    app.add_handler(CommandHandler("userinfo", userinfo_cmd))
    app.add_handler(CommandHandler("broadcast", broadcast_cmd))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Bot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
