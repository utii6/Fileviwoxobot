# bot.py
import asyncio
import logging
import re
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from telegram.error import BadRequest

# --------- الإعدادات ---------
TOKEN = "8495219196:AAEOQ1T08E4Go_Wpl2ZFG7N4_8QXtDeir5E"
ADMIN_ID = 5581457665
CHANNEL = "@Qd3Qd"
SERVICE_ID = 9183
API_KEY = "24617bb47d8e9a7b8afdfa385a62aed2"
API_URL = "https://kds1.com/api/v1/order"  # عدله لو غيره
QUANTITY = 250
MINI_APP_URL = "# bot.py
import asyncio
import logging
import re
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from telegram.error import BadRequest

# --------- الإعدادات ---------
TOKEN = "8495219196:AAEOQ1T08E4Go_Wpl2ZFG7N4_8QXtDeir5E"
ADMIN_ID = 5581457665
CHANNEL = "@Qd3Qd"
SERVICE_ID = 9183
API_KEY = "24617bb47d8e9a7b8afdfa385a62aed2"
API_URL = "https://kds1.com/api/v1/order"  # عدله لو غيره
QUANTITY = 250
MINI_APP_URL = "https://myserver.com/xo.html"  # ضع رابط xo.html الحقيقي هنا

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --------- أزرار الواجهة ---------
def get_main_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎮 اللعبه", url=MINI_APP_URL)],
        [InlineKeyboardButton("▶️ مشاهدة 250", callback_data=f"service_{SERVICE_ID}")]
    ])

# --------- /start ---------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    name = user.full_name or user.first_name or "مستخدم"
    welcome = (
        f"هلا {name}، مرحبا.\n"
        "اضغط '🎮 اللعبه' لفتح اللعبة مباشرة.\n"
        "أو اضغط '▶️ مشاهدة 250' لأرسال 250 مشاهدة لمنشورك."
    )

    # إشعار للأدمن بدخول جديد
    try:
        await context.bot.send_message(chat_id=ADMIN_ID,
                                       text=f"🔔 دخول جديد: {name} (@{user.username or '—'}) id:{user.id}")
    except Exception:
        logger.exception("notify admin failed")

    # محاولة التحقق من الاشتراك بالقناة — نتعامل مع BadRequest بصمت
    try:
        member = await context.bot.get_chat_member(CHANNEL, user.id)
        if member.status not in ("member", "creator", "administrator"):
            join = InlineKeyboardMarkup([[InlineKeyboardButton("اشترك بالقناة", url=f"https://t.me/{CHANNEL.lstrip('@')}")]])
            await update.message.reply_text("🔒 لازم تشترك بالقناة أولاً.", reply_markup=join)
            return
    except BadRequest as e:
        # عادة يحصل لو البوت مو مشرف بالقناة. نخلي الواجهة تظهر لكن نحذر الأدمن في اللوق.
        logger.warning("get_chat_member failed: %s", e)
        # نعرض الواجهة رغم عدم التحقق
        await update.message.reply_text(welcome, reply_markup=get_main_buttons())
        return
    except Exception:
        logger.exception("unexpected error checking membership")

    await update.message.reply_text(welcome, reply_markup=get_main_buttons())

# --------- نلتقط ضغط زر الخدمة ---------
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data or ""
    if data.startswith("service_"):
        service_id = int(data.split("_", 1)[1])
        # نطلب رابط المنشور من المستخدم
        cancel_btn = InlineKeyboardMarkup([[InlineKeyboardButton("إلغاء", callback_data="cancel")]])
        await query.message.reply_text(
            "أرسل الآن رابط المنشور اللي تريد توصل له المشاهدات.\nمثال: https://t.me/xxx أو https://www.instagram.com/xxx",
            reply_markup=cancel_btn
        )
        context.user_data["awaiting_service"] = service_id
    elif data == "cancel":
        context.user_data.pop("awaiting_service", None)
        await query.message.reply_text("تم الإلغاء.")

# --------- نلتقط الرابط النصي ---------
URL_RE = re.compile(r"https?://\S+")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "awaiting_service" not in context.user_data:
        return  # رسالة عادية نتركها بدون رد
    link = update.message.text.strip()
    if not URL_RE.search(link):
        await update.message.reply_text("الرابط غير صالح. حاول ترسله بصيغة تبدأ بـ http أو https.")
        return

    service_id = context.user_data.pop("awaiting_service")
    await update.message.reply_text("جاري إرسال الطلب... انتظر النتيجة.")

    payload = {
        "api_key": API_KEY,
        "service_id": service_id,
        "quantity": QUANTITY,
        "link": link  # معظم واجهات SMM تتطلب حقل link أو url
    }

    try:
        # نفعل الطلب في thread حتى ما نحبس الـ event loop
        resp = await asyncio.to_thread(requests.post, API_URL, json=payload, timeout=30)
        data = resp.json()
    except Exception as e:
        logger.exception("request to kds1 failed")
        await update.message.reply_text(f"حصل خطأ أثناء الاتصال بالموقع: {e}")
        await context.bot.send_message(chat_id=ADMIN_ID,
                                       text=f"خطأ طلب من المستخدم {update.effective_user.id}: {e}")
        return

    # تفسير الرد بشكل عام
    status = (data.get("status") or "").lower() if isinstance(data.get("status"), str) else ""
    if status in ("success", "ok", "true"):
        order_id = data.get("order_id") or data.get("id") or "N/A"
        await update.message.reply_text(f"تم إرسال الطلب بنجاح ✅\nرقم الطلب: {order_id}")
        await context.bot.send_message(chat_id=ADMIN_ID,
                                       text=f"طلب ناجح من {update.effective_user.full_name} id:{update.effective_user.id}\nservice:{service_id}\nlink:{link}\norder:{order_id}")
    else:
        # إن لم يكن هناك حقل status واضح نعرض الرسالة كاملة أو رسالة الخطأ
        msg = data.get("message") or str(data)
        await update.message.reply_text(f"فشل إرسال الطلب ❌\n{msg}")
        await context.bot.send_message(chat_id=ADMIN_ID,
                                       text=f"فشل طلب من {update.effective_user.full_name} id:{update.effective_user.id}\nservice:{service_id}\nlink:{link}\nresp:{msg}")

# --------- تشغيل البوت ---------
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.run_polling()

if __name__ == "__main__":
    main()"  # ضع رابط xo.html الحقيقي هنا

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --------- أزرار الواجهة ---------
def get_main_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎮 اللعبه", url=MINI_APP_URL)],
        [InlineKeyboardButton("▶️ مشاهدات", callback_data=f"service_{SERVICE_ID}")]
    ])

# --------- /start ---------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    name = user.full_name or user.first_name or "مستخدم"
    welcome = (
        f"هلا {name}،حبيبي.\n"
        "اضغط '🎮 اللعبه' لفتح اللعبة والربح.\n"
        "أو اضغط '▶️ مشاهدة 2ألف' لأرسال 2ألف مشاهدة لمنشورك."
    )

    # إشعار للأدمن بدخول جديد
    try:
        await context.bot.send_message(chat_id=ADMIN_ID,
                                       text=f"🔔😂 دخول جديد: {name} (@{user.username or '—'}) id:{user.id}")
    except Exception:
        logger.exception("notify admin failed")

    # محاولة التحقق من الاشتراك بالقناة — نتعامل مع BadRequest بصمت
    try:
        member = await context.bot.get_chat_member(CHANNEL, user.id)
        if member.status not in ("member", "creator", "administrator"):
            join = InlineKeyboardMarkup([[InlineKeyboardButton("مـداار", url=f"https://t.me/{CHANNEL.lstrip('@')}")]])
            await update.message.reply_text("🔒 حبيبي اشترك وأرسل /start .", reply_markup=join)
            return
    except BadRequest as e:
        # عادة يحصل لو البوت مو مشرف بالقناة. نخلي الواجهة تظهر لكن نحذر الأدمن في اللوق.
        logger.warning("get_chat_member failed: %s", e)
        # نعرض الواجهة رغم عدم التحقق
        await update.message.reply_text(welcome, reply_markup=get_main_buttons())
        return
    except Exception:
        logger.exception("unexpected error checking membership")

    await update.message.reply_text(welcome, reply_markup=get_main_buttons())

# --------- نلتقط ضغط زر الخدمة ---------
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data or ""
    if data.startswith("service_"):
        service_id = int(data.split("_", 1)[1])
        # نطلب رابط المنشور من المستخدم
        cancel_btn = InlineKeyboardMarkup([[InlineKeyboardButton("إلغاء", callback_data="cancel")]])
        await query.message.reply_text(
            "أرسل الآن رابط منشـورك الجميل 💙 .\nمثال: https://t.me/qd3qd/6",
            reply_markup=cancel_btn
        )
        context.user_data["awaiting_service"] = service_id
    elif data == "cancel":
        context.user_data.pop("awaiting_service", None)
        await query.message.reply_text("💔تم الإلغاء.")

# --------- نلتقط الرابط النصي ---------
URL_RE = re.compile(r"https?://\S+")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "awaiting_service" not in context.user_data:
        return  # رسالة عادية نتركها بدون رد
    link = update.message.text.strip()
    if not URL_RE.search(link):
        await update.message.reply_text("الرابط غير صالح. حاول ترسله بصيغة تبدأ بـ http أو https.")
        return

    service_id = context.user_data.pop("awaiting_service")
    await update.message.reply_text("جاري إرسال الطلب... انتظر النتيجة.")

    payload = {
        "api_key": API_KEY,
        "service_id": service_id,
        "quantity": QUANTITY,
        "link": link  # معظم واجهات SMM تتطلب حقل link أو url
    }

    try:
        # نفعل الطلب في thread حتى ما نحبس الـ event loop
        resp = await asyncio.to_thread(requests.post, API_URL, json=payload, timeout=30)
        data = resp.json()
    except Exception as e:
        logger.exception("request to kds1 failed")
        await update.message.reply_text(f"حصل خطأ أثناء الاتصال: {e}")
        await context.bot.send_message(chat_id=ADMIN_ID,
                                       text=f"خطأ طلب من المستخدم {update.effective_user.id}: {e}")
        return

    # تفسير الرد بشكل عام
    status = (data.get("status") or "").lower() if isinstance(data.get("status"), str) else ""
    if status in ("success", "ok", "true"):
        order_id = data.get("order_id") or data.get("id") or "N/A"
        await update.message.reply_text(f"تم إرسال الطلب بنجاح 😂✅\nرقم الطلب🆔: {order_id}")
        await context.bot.send_message(chat_id=ADMIN_ID,
                                       text=f"طلب ناجح من {update.effective_user.full_name} id:{update.effective_user.id}\nservice:{service_id}\nlink:{link}\norder:{order_id}")
    else:
        # إن لم يكن هناك حقل status واضح نعرض الرسالة كاملة أو رسالة الخطأ
        msg = data.get("message") or str(data)
        await update.message.reply_text(f"فشل إرسال الطلب !❌\n{msg}")
        await context.bot.send_message(chat_id=ADMIN_ID,
                                       text=f"فشل طلب من {update.effective_user.full_name} id:{update.effective_user.id}\nservice:{service_id}\nlink:{link}\nresp:{msg}")

# --------- تشغيل البوت ---------
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.run_polling()

if __name__ == "__main__":
    main()
