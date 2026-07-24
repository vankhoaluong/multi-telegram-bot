import os
import asyncio
import logging
from flask import Flask, request, Response
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

BOTS = {
    "nutritron": os.getenv("NUTRITRON_TOKEN"),
    "timesheet": os.getenv("TIMESHEET_TOKEN"),
}

# ===== HANDLERS =====
async def nutritron_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🍎 *Nutritron Bot - Hướng dẫn sử dụng*\n\n"
        "/start - Xem hướng dẫn\n"
        "/help - Trợ giúp",
        parse_mode="Markdown"
    )

async def timesheet_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⏰ *Timesheet Bot - Hướng dẫn sử dụng*\n\n"
        "/start - Xem hướng dẫn\n"
        "/checkin - Check in\n"
        "/checkout - Check out",
        parse_mode="Markdown"
    )

# ===== KHỞI TẠO APPS 1 LẦN =====
nutritron_app = None
timesheet_app = None

def init_apps():
    global nutritron_app, timesheet_app
    
    if BOTS.get("nutritron"):
        nutritron_app = Application.builder().token(BOTS["nutritron"]).build()
        nutritron_app.add_handler(CommandHandler("start", nutritron_start))
    
    if BOTS.get("timesheet"):
        timesheet_app = Application.builder().token(BOTS["timesheet"]).build()
        timesheet_app.add_handler(CommandHandler("start", timesheet_start))

# ===== ROUTES =====
@app.route("/")
def home():
    return "✅ All bots running!", 200

@app.route("/webhook/nutritron", methods=["POST"])
def webhook_nutritron():
    if not nutritron_app:
        return "Nutritron bot not configured", 404
    
    data = request.get_json(force=True)
    bot = Bot(token=BOTS["nutritron"])
    
    async def process():
        async with nutritron_app:
            update = Update.de_json(data, bot)
            await nutritron_app.process_update(update)
    
    asyncio.run(process())
    return Response(status=200)

@app.route("/webhook/timesheet", methods=["POST"])
def webhook_timesheet():
    if not timesheet_app:
        return "Timesheet bot not configured", 404
    
    data = request.get_json(force=True)
    bot = Bot(token=BOTS["timesheet"])
    
    async def process():
        async with timesheet_app:
            update = Update.de_json(data, bot)
            await timesheet_app.process_update(update)
    
    asyncio.run(process())
    return Response(status=200)

# ===== SETUP WEBHOOKS =====
async def setup_webhooks():
    base_url = os.getenv("RENDER_EXTERNAL_URL", "")
    if not base_url:
        logger.error("❌ RENDER_EXTERNAL_URL not set!")
        return
    
    for name, token in BOTS.items():
        if not token:
            continue
        bot = Bot(token=token)
        await bot.initialize()
        webhook_url = f"{base_url}/webhook/{name}"
        await bot.set_webhook(url=webhook_url)
        logger.info(f"✅ {name}: Webhook set!")
        await bot.shutdown()

if __name__ == "__main__":
    init_apps()
    asyncio.run(setup_webhooks())
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
