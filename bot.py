import logging
import time
import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ===== إعداداتك =====
BOT_TOKEN = "8495219196:AAEOQ1T08E4Go_Wpl2ZFG7N4_8QXtDeir5E"
ADMIN_ID = 5581457665
CHANNEL_USERNAME = "@Qd3Qd"

API_KEY = "24617bb47d8e9a7b8afdfa385a62aed2"   # KDS API
SERVICE_ID = 9183   # رقم الخدمة
QUANTITY = 250      # عدد المشاهدات
COOLDOWN = 3600     # (بالثواني) كل ساعة مرة

# تخزين آخر طلب لكل يوزر
last_request = {}

# ===== تفعيل اللوج =====
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== /start =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id

    # إشعار للادمن
    if user.id != ADMIN_ID:
        await context.bot.send_message(ADMIN_ID, f"😂🔔 مستخدم جديد دخل: {user.first_name} ({user.id})")

    # الأزرار
    keyboard = [
        [InlineKeyboardButton("🚀 طلب مشاهدات", callback_data="views")],
        [InlineKeyboardButton("🎮 العب وفوز XO", callback_data="play_xo")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"اهلا {user.first_name} 🌹\n"
        " حبيبي اختار من القائمة:\n\n"
        "💎🚀 لطلب مشاهدات (كل ساعة 250 مجانا)\n"
        "😂🎮 أو جرب حظك باللعبة XO",
        reply_markup=reply_markup
    )

# ===== التعامل مع الأزرار =====
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "views":
        user_id = query.from_user.id
        now = time.time()

        if user_id in last_request and now - last_request[user_id] < COOLDOWN:
            remaining = int((COOLDOWN - (now - last_request[user_id])) / 60)
            await query.message.reply_text(f"🤯⏳ تقدر تطلب بعد {remaining} دقيقة.")
            return

        await query.message.reply_text("😂📌 أرسل رابط منشـورك الجميل.")
        context.user_data["awaiting_link"] = True

    elif query.data == "https://viwoxobot.onrender.com":
        await query.message.reply_text("🎮 لعبة XO انطلقت! (هنا تدمج كود اللعبة مالك).")

# ===== استقبال الرابط =====
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_link"):
        link = update.message.text
        user_id = update.message.from_user.id

        # إرسال الطلب لـ KDS API
        url = "https://kds1.net/api/v2"
        payload = {
            "key": API_KEY,
            "action": "add",
            "service": SERVICE_ID,
            "link": link,
            "quantity": QUANTITY
        }
        try:
            response = requests.post(url, data=payload)
            data = response.json()
            if "order" in data:
                last_request[user_id] = time.time()
                await update.message.reply_text("✅ تم استلام طلبك وإضافة الف مشاهدة.")
            else:
                await update.message.reply_text("❌ فشل إرسال الطلب، جرب رابط صحيح.")
        except Exception as e:
            await update.message.reply_text("⚠️ خطأ بالاتصال.")

        context.user_data["awaiting_link"] = False

# ===== تشغيل البوت =====
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()

if __name__ == "__main__":
    main()
