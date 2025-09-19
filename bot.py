import asyncio
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ======= إعدادات البوت =======
TOKEN = "8495219196:AAEOQ1T08E4Go_Wpl2ZFG7N4_8QXtDeir5E"
ADMIN_ID = 5581457665
CHANNEL = "@Qd3Qd"
SERVICE_ID = 9183
API_KEY = "24617bb47d8e9a7b8afdfa385a62aed2"
API_URL = "https://kds1.com/api/v1/order"  # رابط API
QUANTITY = 250  # عدد المشاهدات لكل طلب
INTERVAL = 3600  # كل ساعة بالثواني
MINI_APP_URL = "https://viwoxobot.onrender.com"  # رابط لعبتك XO

services = [{"id": SERVICE_ID, "name": "خدمة kds1 رقم 9183"}]

# ======= أزرار الواجهة =======
def get_main_buttons():
    buttons = [
        [InlineKeyboardButton("🎮 الألعاب", url=MINI_APP_URL)],
        [InlineKeyboardButton(s["name"], callback_data=f"service_{s['id']}") for s in services]
    ]
    return InlineKeyboardMarkup(buttons)

# ======= أمر /start =======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    # إشعار دخول المستخدم للأدمن
    await context.bot.send_message(chat_id=ADMIN_ID, text=f"😂🔔 مستخدم جديد دخل: {user.full_name} (@{user.username})")

    # التحقق من الاشتراك بالقناة الإجباريّة
    chat_member = await context.bot.get_chat_member(CHANNEL, user.id)
    if chat_member.status in ["member", "administrator", "creator"]:
        await update.message.reply_text("مرحبا! اختر الخيار:", reply_markup=get_main_buttons())
    else:
        await update.message.reply_text(f"🔒اشترك حبيبي و {CHANNEL} وأرسل /start .")

# ======= تنفيذ الطلب التلقائي =======
async def execute_service(user_id, service_id):
    while True:
        payload = {
            "api_key": API_KEY,
            "service_id": service_id,
            "quantity": QUANTITY
        }
        try:
            response = requests.post(API_URL, json=payload)
            result = response.json()
            # يمكن إرسال إشعار للأدمن عن نجاح الطلب
            print(f"User {user_id}: {result}")
        except Exception as e:
            print(f"Error for user {user_id}: {e}")
        await asyncio.sleep(INTERVAL)

# ======= التعامل مع اختيار الخدمة =======
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith("service_"):
        service_id = data.split("_")[1]
        user_id = query.from_user.id
        await query.message.reply_text(f"تم اختيار الخدمة {service_id} 😂✅\nستُرسل الطلبات كل ساعة (250 مشاهدة).")
        # تشغيل الخدمة بشكل دوري لكل مستخدم
        context.application.create_task(execute_service(user_id, service_id))

# ======= تشغيل البوت =======
app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(handle_callback))
app.run_polling()
