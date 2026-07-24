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

# ===== HANDLER RIÊNG CHO NUTRITRON BOT =====
async def nutritron_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🍎 *Nutritron Bot - Hướng dẫn sử dụng*\n\n"
        "/start - Xem hướng dẫn\n"
        "/help - Trợ giúp\n"
        "/menu - Xem menu dinh dưỡng",
        parse_mode="Markdown"
    )

async def nutritron_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📋 Đây là bot dinh dưỡng. Liên hệ @admin để được hỗ trợ.")

# ===== HANDLER RIÊNG CHO TIMESHEET BOT =====
async def timesheet_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⏰ *Timesheet Bot - Hướng dẫn sử dụng*\n\n"
        "/start - Xem hướng dẫn\n"
        "/checkin - Check in\n"
        "/checkout - Check out\n"
        "/report - Xem báo cáo",
        parse_mode="Markdown"
    )

async def timesheet_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📋 Đây là bot chấm công. Liên hệ HR để được hỗ trợ.")

# ===== CACHE APPS =====
apps = {}

def get_nutritron_app(token):
    if "nutritron" not in apps:
        app_bot = Application.builder().token(token).build()
        app_bot.add_handler(CommandHandler("start", nutritron_start))
        app_bot.add_handler(CommandHandler("help", nutritron_help))
        apps["nutritron"] = app_bot
    return apps["nutritron"]

def get_timesheet_app(token):
    if "timesheet" not in apps:
        app_bot = Application.builder().token(token).build()
        app_bot.add_handler(CommandHandler("start", timesheet_start))
        app_bot.add_handler(CommandHandler("help", timesheet_help))
        apps["timesheet"] = app_bot
    return apps["timesheet"]

# ===== ROUTES =====
@app.route("/")
def home():
    return "✅ All bots running!", 200

@app.route("/webhook/nutritron", methods=["POST"])
def webhook_nutritron():
    token = BOTS.get("nutritron")
    if not token:
        return "Bot not found", 404
    
    data = request.get_json(force=True)
    
    async def process():
        bot = Bot(token=token)
        await bot.initialize()
        
        app_bot = get_nutritron_app(token)
        await app_bot.initialize()
        await app_bot.start()
        
        update = Update.de_json(data, bot)
        await app_bot.process_update(update)
        
        await app_bot.stop()
        await bot.shutdown()
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(process())
    
    return Response(status=200)

@app.route("/webhook/timesheet", methods=["POST"])
def webhook_timesheet():
    token = BOTS.get("timesheet")
    if not token:
        return "Bot not found", 404
    
    data = request.get_json(force=True)
    
    async def process():
        bot = Bot(token=token)
        await bot.initialize()
        
        app_bot = get_timesheet_app(token)
        await app_bot.initialize()
        await app_bot.start()
        
        update = Update.de_json(data, bot)
        await app_bot.process_update(update)
        
        await app_bot.stop()
        await bot.shutdown()
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(process())
    
    return Response(status=200)

# ===== SETUP WEBHOOKS =====
async def setup_webhooks():
    base_url = os.getenv("RENDER_EXTERNAL_URL", "")
    if not base_url:
        logger.error("❌ RENDER_EXTERNAL_URL not set!")
        return
    
    for name, token in BOTS.items():
        if not token:
            logger.warning(f"⚠️ {name}: Token not found")
            continue
        
        try:
            bot = Bot(token=token)
            await bot.initialize()
            webhook_url = f"{base_url}/webhook/{name}"
            await bot.set_webhook(url=webhook_url)
            logger.info(f"✅ {name}: Webhook set!")
            await bot.shutdown()
        except Exception as e:
            logger.error(f"❌ {name}: {e}")

if __name__ == "__main__":
    asyncio.run(setup_webhooks())
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
