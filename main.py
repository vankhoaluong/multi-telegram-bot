import os
import asyncio
import logging
from flask import Flask, request, Response
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)

# Danh sách bot - Token lấy từ Environment Variables
BOTS = {
    "nutritron": os.getenv("NUTRITRON_TOKEN"),
    "timesheet": os.getenv("TIMESHEET_TOKEN"),
}

# ===== HANDLERS CHUNG =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Xin chào! Bot đang hoạt động.")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📋 Lệnh: /start, /help")

# ===== ROUTES =====
@app.route("/")
def home():
    return "✅ All bots running!", 200

@app.route("/webhook/<bot_name>", methods=["POST"])
async def webhook(bot_name):
    if bot_name not in BOTS or not BOTS[bot_name]:
        return "Bot not found", 404
    
    try:
        token = BOTS[bot_name]
        bot = Bot(token=token)
        app_bot = Application.builder().token(token).build()
        app_bot.add_handler(CommandHandler("start", start))
        app_bot.add_handler(CommandHandler("help", help_cmd))
        await app_bot.initialize()
        
        update = Update.de_json(request.get_json(force=True), bot)
        await app_bot.process_update(update)
        
        return Response(status=200)
    except Exception as e:
        logger.error(f"Error in {bot_name}: {e}")
        return Response(status=500)

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
            webhook_url = f"{base_url}/webhook/{name}"
            await bot.set_webhook(url=webhook_url)
            logger.info(f"✅ {name}: Webhook set!")
        except Exception as e:
            logger.error(f"❌ {name}: {e}")

# ===== KHỞI ĐỘNG =====
if __name__ == "__main__":
    # Set webhooks
    asyncio.run(setup_webhooks())
    
    # Chạy Flask
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
