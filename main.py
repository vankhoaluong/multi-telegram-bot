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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Xin chào! Bot đang hoạt động.")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📋 Lệnh: /start, /help")

async def process_telegram_update(token, data):
    """Xử lý update từ Telegram bất đồng bộ"""
    bot = Bot(token=token)
    app_bot = Application.builder().token(token).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("help", help_cmd))
    await app_bot.initialize()
    
    update = Update.de_json(data, bot)
    await app_bot.process_update(update)

@app.route("/")
def home():
    return "✅ All bots running!", 200

@app.route("/webhook/<bot_name>", methods=["POST"])
def webhook(bot_name):  # KHÔNG async
    if bot_name not in BOTS or not BOTS[bot_name]:
        return "Bot not found", 404
    
    token = BOTS[bot_name]
    data = request.get_json(force=True)
    
    # Chạy async trong event loop mới
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(process_telegram_update(token, data))
    
    return Response(status=200)

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
            webhook_url = f"{base_url}/webhook/{name}"
            await bot.set_webhook(url=webhook_url)
            logger.info(f"✅ {name}: Webhook set!")
        except Exception as e:
            logger.error(f"❌ {name}: {e}")

if __name__ == "__main__":
    asyncio.run(setup_webhooks())
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
