import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
import database as db
import keyboards as kb
import config
from config import ADMIN_IDS

logger = logging.getLogger(__name__)

def format_price(amount: int) -> str:
    """فرمت‌بندی قیمت به ریال/تومان با جداکننده سه رقمی"""
    return f"{amount:,} تومان"

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندلر دستور /start یا دکمه شروع با نمایش مستقیم دکمه‌های شیشه‌ای"""
    user = update.effective_user
    db_user = db.get_or_create_user(user.id, user.username, user.full_name)
    is_admin = user.id in ADMIN_IDS
    products = db.get_products()

    welcome_text = f"""سلام {user.first_name} عزیز! 👋
به ربات رسمی فروش و رزرو اکانت‌های اشتراکی خوش آمدید.

💎 **اشتراک‌های ویژه موجود و در دسترس:**
🔹 **جمینای پرو ۱۸ ماهه (Gemini AI Pro)** - موجود با تخفیف ۵۰٪!

🔔 سایر اشتراک‌ها (یوتیوب پریمیوم و نوشن بیزینس) در حال حاضر ناموجود هستند، اما می‌توانید به صورت رایگان **رزرو** نمایید تا به محض موجودی به شما اطلاع دهیم.

کدام یک از اشتراک‌های زیر را می‌خواهید تهیه یا رزرو کنید؟ 👇"""

    reply_markup = kb.welcome_inline_keyboard(products, is_admin=is_admin)

    if update.callback_query:
        query = update.callback_query
        await query.answer()
        if query.message.photo:
            try:
                await query.message.delete()
            except Exception:
                pass
            await context.bot.send_message(chat_id=query.message.chat_id, text=welcome_text, reply_markup=reply_markup, parse_mode="Markdown")
        else:
            await query.edit_message_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

async def catalog_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش لیست کاتالوگ اشتراک‌ها"""
    products = db.get_products()
    text = "کدام یک از اشتراک‌های زیر را می‌خواهید تهیه یا رزرو کنید؟ 👇"
    await update.message.reply_text(
        text,
        reply_markup=kb.products_inline_keyboard(products)
    )

async def catalog_back_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بازگشت به لیست اشتراک‌ها"""
    query = update.callback_query
    await query.answer()
    user = update.effective_user
    is_admin = user.id in ADMIN_IDS
    products = db.get_products()
    
    welcome_text = f"""سلام {user.first_name} عزیز! 👋
کدام یک از اشتراک‌های زیر را می‌خواهید تهیه یا رزرو کنید؟ 👇"""
    
    if query.message.photo:
        try:
            await query.message.delete()
        except Exception:
            pass
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=welcome_text,
            reply_markup=kb.welcome_inline_keyboard(products, is_admin=is_admin),
            parse_mode="Markdown"
        )
    else:
        await query.edit_message_text(
            welcome_text,
            reply_markup=kb.welcome_inline_keyboard(products, is_admin=is_admin),
            parse_mode="Markdown"
        )

async def product_detail_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش توضیحات و جزییات یک اشتراک به همراه تصویر بنر اختصاصی"""
    query = update.callback_query
    await query.answer()
    product_code = query.data.replace("prod_", "")
    product = db.get_product_by_code(product_code)
    
    if not product:
        await query.edit_message_text("❌ متاسفانه محصول مورد نظر یافت نشد.")
        return

    banner_path = config.BASE_DIR / "gemini_banner.jpg"

    # ارسال تصویر بنر برای جمینای پرو
    if product_code == "gemini_18m" and banner_path.exists():
        try:
            await query.message.delete()
        except Exception:
            pass
        with open(banner_path, "rb") as f:
            await context.bot.send_photo(
                chat_id=query.message.chat_id,
                photo=f,
                caption=product["description_fa"],
                reply_markup=kb.product_detail_keyboard(product),
                parse_mode="Markdown"
            )
        return

    if query.message.photo:
        try:
            await query.message.delete()
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=product["description_fa"],
                reply_markup=kb.product_detail_keyboard(product),
                parse_mode="Markdown"
            )
        except Exception:
            await query.edit_message_caption(
                caption=product["description_fa"],
                reply_markup=kb.product_detail_keyboard(product),
                parse_mode="Markdown"
            )
    else:
        await query.edit_message_text(
            product["description_fa"],
            reply_markup=kb.product_detail_keyboard(product),
            parse_mode="Markdown"
        )

async def buy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع فرایند پرداخت و خرید اشتراک موجود"""
    query = update.callback_query
    await query.answer()
    product_code = query.data.replace("buy_", "")
    product = db.get_product_by_code(product_code)
    user = update.effective_user
    db_user = db.get_or_create_user(user.id, user.username, user.full_name)

    if not product or not product["is_available"]:
        await query.edit_message_text("❌ متاسفانه این محصول در حال حاضر موجود نمی‌باشد.")
        return

    # ایجاد سفارش در دیتابیس
    order = db.create_order(db_user["id"], product["id"], product["price_toman"])
    context.user_data["active_order_id"] = order["id"]
    context.user_data["state"] = "WAITING_FOR_RECEIPT"

    card_number = db.get_setting("card_number")
    card_holder = db.get_setting("card_holder")
    bank_name = db.get_setting("bank_name")

    payment_text = f"""💳 **اطلاعات واریز و ثبت سفارش**

📦 سفارش: **{product['title_fa']}**
💰 مبلغ قابل پرداخت: **{format_price(product['price_toman'])}**
🔖 کد سفارش: `{order['order_code']}`

━━━━━━━━━━━━━━━━━━━━━
لطفاً مبلغ فوق را به شماره کارت زیر واریز نمایید:

💳 شماره کارت (برای کپی لمس کنید):
`{card_number}`

👤 به نام: **{card_holder}**
🏛 بانک: **{bank_name}**
━━━━━━━━━━━━━━━━━━━━━

⚠️ **نکته مهم:** پس از انجام واریز، تصویر فیش واریزی (رسید کارت به کارت) را همینجا در ربات ارسال کنید تا سفارش شما برای تایید به مدیریت ارسال شود."""

    if query.message.photo:
        try:
            await query.message.delete()
        except Exception:
            pass
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=payment_text,
            reply_markup=kb.payment_action_keyboard(order["id"]),
            parse_mode="Markdown"
        )
    else:
        await query.edit_message_text(
            payment_text,
            reply_markup=kb.payment_action_keyboard(order["id"]),
            parse_mode="Markdown"
        )

async def reserve_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """رزرو اشتراک‌های ناموجود"""
    query = update.callback_query
    await query.answer()
    product_code = query.data.replace("reserve_", "")
    product = db.get_product_by_code(product_code)
    user = update.effective_user
    db_user = db.get_or_create_user(user.id, user.username, user.full_name)
    is_admin = user.id in ADMIN_IDS

    if not product:
        await query.edit_message_text("❌ محصول یافت نشد.")
        return

    # ثبت رزرو در دیتابیس
    res = db.create_reservation(db_user["id"], product["id"])

    # پیام به کاربر
    success_text = f"""✅ **درخواست رزرو شما با موفقیت ثبت شد!**

📦 اشتراک: **{product['title_fa']}**
👤 نام شما: **{user.full_name}**

به محض موجود شدن این اشتراک، اطلاعات فعال‌سازی و تخفیف ویژه به اکانت تلگرام شما ارسال خواهد شد. از شکیبایی شما سپاسگزاریم! 🙏"""

    buttons = [[InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="menu_start")]]
    if query.message.photo:
        try:
            await query.message.delete()
        except Exception:
            pass
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=success_text,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode="Markdown"
        )
    else:
        await query.edit_message_text(
            success_text,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode="Markdown"
        )

    # ارسال اعلان به تمام ادمین‌ها
    admin_alert = f"""🔔 **رزرو جدید ثبت شد!**

📦 اشتراک: **{product['title_fa']}**
👤 کاربر: {user.full_name}
🆔 یوزرنیم: @{user.username if user.username else 'ندارد'}
🔢 شناسه عددی: `{user.id}`
📅 تاریخ: {res['created_at']}"""

    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(chat_id=admin_id, text=admin_alert, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Error sending reserve alert to admin {admin_id}: {e}")

async def send_receipt_action_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """کاربر روی دکمه ارسال فیش کلیک می‌کند"""
    query = update.callback_query
    await query.answer()
    order_id = int(query.data.replace("send_receipt_", ""))
    context.user_data["active_order_id"] = order_id
    context.user_data["state"] = "WAITING_FOR_RECEIPT"
    
    await query.message.reply_text(
        "📸 لطفاً تصویر فیش یا رسید واریزی خود را به صورت عکس در این چت ارسال کنید:\n(برای انصراف عبارت /start را بفرستید)",
        reply_markup=kb.cancel_keyboard()
    )

async def cancel_order_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """انصراف از سفارش"""
    query = update.callback_query
    await query.answer()
    context.user_data.pop("active_order_id", None)
    context.user_data.pop("state", None)
    
    buttons = [[InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="menu_start")]]
    await query.edit_message_text(
        "❌ سفارش لغو شد. می‌توانید از منوی زیر مجدداً اقدام کنید.",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def menu_callback_dispatcher(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت دکمه‌های شیشه‌ای منوی اصلی (اکانت‌ها، پشتیبانی، ادمین)"""
    query = update.callback_query
    data = query.data
    user = update.effective_user
    is_admin = user.id in ADMIN_IDS

    if data == "menu_start":
        await start_command(update, context)
        return
    elif data == "menu_my_orders":
        await query.answer()
        db_user = db.get_or_create_user(user.id, user.username, user.full_name)
        orders = db.get_user_completed_orders(db_user["id"])

        if not orders:
            buttons = [[InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="menu_start")]]
            await query.edit_message_text(
                "📦 شما تاکنون سفارشی ثبت نکرده‌اید یا سفارش شما هنوز در حال پردازش است.\nجهت خرید اشتراک می‌توانید از منوی اصلی اقدام نمایید.",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
            return

        text = "📦 **اکانت‌های خریداری شده شما:**\n\n"
        for idx, o in enumerate(orders, 1):
            status_fa = "✅ تحویل داده شده" if o["status"] == "completed" else "⏳ در حال آماده‌سازی اکانت"
            delivery_info = o["delivery_payload"] if o["delivery_payload"] else "اکانت در حال آماده‌سازی است..."
            
            text += f"""{idx}️⃣ **{o['product_title']}**
🔖 کد سفارش: `{o['order_code']}`
وضعیت: {status_fa}
🔑 **اطلاعات فعال‌سازی / لینک ساب:**
{delivery_info}
━━━━━━━━━━━━━━━━━━━━━\n"""

        buttons = [[InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="menu_start")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")

    elif data == "menu_support":
        await query.answer()
        context.user_data["state"] = "WAITING_FOR_TICKET"
        guide_text = db.get_setting("support_guide", "لطفاً سوال، مشکل یا درخواست خود را در قالب یک پیام (متن، عکس، ویس و ...) در این چت ارسال کنید:")
        
        await query.message.reply_text(
            f"🎧 **واحد پشتیبانی مشتریان**\n\n{guide_text}",
            reply_markup=kb.cancel_keyboard(),
            parse_mode="Markdown"
        )

    elif data == "menu_admin" and is_admin:
        await query.answer()
        from handlers_admin import admin_panel_command
        await admin_panel_command(update, context)

async def handle_user_photo_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت تصویر فیش واریزی از کاربر"""
    user = update.effective_user
    state = context.user_data.get("state")
    order_id = context.user_data.get("active_order_id")

    # اگر کاربر در حالت ارسال فیش است
    if state == "WAITING_FOR_RECEIPT" and order_id:
        photo = update.message.photo[-1] # باکیفیت‌ترین عکس
        file_id = photo.file_id
        
        db.update_order_receipt(order_id, file_id)
        order = db.get_order(order_id)
        
        context.user_data.pop("active_order_id", None)
        context.user_data.pop("state", None)

        # پیام به کاربر
        await update.message.reply_text(
            f"""✅ **رسید واریزی شما با موفقیت دریافت شد!**

🔖 کد پیگیری: `{order['order_code']}`
⏳ سفارش شما در صف بررسی ادمین قرار گرفت. پس از بررسی و تایید واریز، پیام تایید و اطلاعات اکانت برای شما ارسال خواهد شد. سپاس از صبوری شما.""",
            reply_markup=kb.welcome_inline_keyboard(db.get_products(), is_admin=(user.id in ADMIN_IDS)),
            parse_mode="Markdown"
        )

        # ارسال رسید و جزییات به ادمین‌ها
        admin_caption = f"""💳 **رسید واریز جدید جهت بررسی!**

🔖 کد سفارش: `{order['order_code']}`
📦 محصول: **{order['product_title']}**
💰 مبلغ: **{format_price(order['amount'])}**
👤 خریدار: {user.full_name} (@{user.username if user.username else 'ندارد'})
🔢 شناسه عددی: `{user.id}`"""

        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_photo(
                    chat_id=admin_id,
                    photo=file_id,
                    caption=admin_caption,
                    reply_markup=kb.admin_order_keyboard(order_id),
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Error forwarding receipt to admin {admin_id}: {e}")
        return

    # اگر کاربر در حالت تیکت پشتیبانی است و عکس فرستاده
    if state == "WAITING_FOR_TICKET":
        photo = update.message.photo[-1]
        file_id = photo.file_id
        caption = update.message.caption or "بدون توضیحات متنی"
        
        db_user = db.get_or_create_user(user.id, user.username, user.full_name)
        ticket = db.create_ticket(db_user["id"], caption, file_id=file_id, file_type="photo")
        
        context.user_data.pop("state", None)
        
        await update.message.reply_text(
            f"""✅ **تیکت پشتیبانی شما با موفقیت ثبت شد.**

🎫 شماره تیکت: `{ticket['ticket_code']}`
👨‍💻 کارشناسان ما به زودی پیام شما را بررسی کرده و پاسخ را از طریق همین ربات برای شما ارسال خواهند کرد.""",
            reply_markup=kb.welcome_inline_keyboard(db.get_products(), is_admin=(user.id in ADMIN_IDS)),
            parse_mode="Markdown"
        )

        # اطلاع به ادمین‌ها
        admin_msg = f"""🎧 **تیکت پشتیبانی جدید!**

🎫 کد تیکت: `{ticket['ticket_code']}`
👤 کاربر: {user.full_name} (@{user.username if user.username else 'ندارد'})
🔢 شناسه عددی: `{user.id}`
📝 متن: {caption}"""

        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_photo(
                    chat_id=admin_id,
                    photo=file_id,
                    caption=admin_msg,
                    reply_markup=kb.admin_ticket_reply_keyboard(ticket["id"]),
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Error forwarding ticket photo to admin {admin_id}: {e}")
        return

async def my_purchased_accounts_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش لیست اکانت‌های خریداری شده و تحویل داده شده به کاربر"""
    user = update.effective_user
    db_user = db.get_or_create_user(user.id, user.username, user.full_name)
    orders = db.get_user_completed_orders(db_user["id"])

    if not orders:
        await update.message.reply_text(
            "📦 شما تاکنون سفارشی ثبت نکرده‌اید یا سفارش شما هنوز در حال پردازش است.\nجهت خرید اشتراک می‌توانید از منوی اصلی اقدام نمایید.",
            reply_markup=kb.welcome_inline_keyboard(db.get_products(), is_admin=(user.id in ADMIN_IDS))
        )
        return

    text = "📦 **اکانت‌های خریداری شده شما:**\n\n"
    for idx, o in enumerate(orders, 1):
        status_fa = "✅ تحویل داده شده" if o["status"] == "completed" else "⏳ در حال آماده‌سازی اکانت"
        delivery_info = o["delivery_payload"] if o["delivery_payload"] else "اکانت در حال آماده‌سازی است..."
        
        text += f"""{idx}️⃣ **{o['product_title']}**
🔖 کد سفارش: `{o['order_code']}`
وضعیت: {status_fa}
🔑 **اطلاعات فعال‌سازی / لینک ساب:**
{delivery_info}
━━━━━━━━━━━━━━━━━━━━━\n"""

    await update.message.reply_text(
        text,
        reply_markup=kb.welcome_inline_keyboard(db.get_products(), is_admin=(user.id in ADMIN_IDS)),
        parse_mode="Markdown"
    )

async def support_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """درخواست ثبت تیکت پشتیبانی"""
    user = update.effective_user
    context.user_data["state"] = "WAITING_FOR_TICKET"
    
    guide_text = db.get_setting("support_guide", "لطفاً سوال، مشکل یا درخواست خود را در قالب یک پیام (متن، عکس، ویس و ...) ارسال کنید:")
    
    await update.message.reply_text(
        f"🎧 **واحد پشتیبانی مشتریان**\n\n{guide_text}",
        reply_markup=kb.cancel_keyboard(),
        parse_mode="Markdown"
    )

async def handle_user_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش متن‌های کاربر (تیکت، انصراف یا سایر دستورات)"""
    user = update.effective_user
    text = update.message.text.strip()
    
    # بررسی آیا پیام مربوط به عملیات ادمین است
    from handlers_admin import handle_admin_text_input
    if await handle_admin_text_input(update, context):
        return

    state = context.user_data.get("state")

    # بررسی دکمه انصراف
    if text in ["❌ انصراف و بازگشت به منو", "انصراف", "منو"]:
        context.user_data.pop("state", None)
        context.user_data.pop("active_order_id", None)
        await start_command(update, context)
        return

    # منوهای اصلی متنی
    if text == "🛍 لیست اشتراک‌ها و خرید":
        await catalog_message(update, context)
        return
    elif text == "📦 اکانت‌های خریداری شده من":
        await my_purchased_accounts_message(update, context)
        return
    elif text == "🎧 پشتیبانی و تیکت":
        await support_message(update, context)
        return
    # بررسی اگر کاربر سفارشی در انتظار عودت وجه دارد و شماره کارت فرستاده
    db_user = db.get_or_create_user(user.id, user.username, user.full_name)
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM orders WHERE user_id = ? AND status = 'refund_pending' ORDER BY id DESC LIMIT 1", (db_user["id"],))
        refund_order = cursor.fetchone()
        
    if refund_order and state != "WAITING_FOR_TICKET":
        order_dict = dict(refund_order)
        # اطلاع فوری به ادمین
        admin_refund_card_alert = f"""💳 **اطلاعات شماره کارت جهت عودت وجه!**

🔖 کد سفارش: `{order_dict['order_code']}`
💰 مبلغ عودت: **{order_dict['amount']:,} تومان**
👤 مشتری: {user.full_name} (@{user.username if user.username else 'ندارد'})
🔢 شناسه عددی: `{user.id}`
━━━━━━━━━━━━━━━━━━━━━
📝 **اطلاعات ارسالی خریدار (شماره کارت):**
`{text}`
━━━━━━━━━━━━━━━━━━━━━"""
        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_message(chat_id=admin_id, text=admin_refund_card_alert, parse_mode="Markdown")
            except Exception as e:
                logger.error(f"Error sending refund card alert to admin {admin_id}: {e}")

        await update.message.reply_text(
            f"""✅ **اطلاعات کارت شما با موفقیت برای مدیریت ارسال شد.**

مبلغ **{order_dict['amount']:,} تومان** مربوط به سفارش `{order_dict['order_code']}` در اسرع وقت به حساب شما واریز و پیام تایید برایتان ارسال خواهد شد. سپاس از صبوری شما.""",
            reply_markup=kb.welcome_inline_keyboard(db.get_products(), is_admin=(user.id in ADMIN_IDS)),
            parse_mode="Markdown"
        )
        return

    # دریافت پیام تیکت
    if state == "WAITING_FOR_TICKET":
        db_user = db.get_or_create_user(user.id, user.username, user.full_name)
        ticket = db.create_ticket(db_user["id"], text)
        context.user_data.pop("state", None)

        await update.message.reply_text(
            f"""✅ **تیکت پشتیبانی شما با موفقیت ثبت شد.**

🎫 شماره تیکت: `{ticket['ticket_code']}`
👨‍💻 پیام شما برای تیم پشتیبانی ارسال گردید و پاسخ به زودی از طریق همین ربات برای شما ارسال خواهد شد.""",
            reply_markup=kb.welcome_inline_keyboard(db.get_products(), is_admin=(user.id in ADMIN_IDS)),
            parse_mode="Markdown"
        )

        admin_ticket_msg = f"""🎧 **تیکت پشتیبانی جدید!**

🎫 کد تیکت: `{ticket['ticket_code']}`
👤 کاربر: {user.full_name} (@{user.username if user.username else 'ندارد'})
🔢 شناسه عددی: `{user.id}`
📝 متن پیام:
{text}"""

        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=admin_ticket_msg,
                    reply_markup=kb.admin_ticket_reply_keyboard(ticket["id"]),
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Error forwarding ticket to admin {admin_id}: {e}")
        return
