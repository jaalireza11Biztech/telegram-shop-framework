import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
import database as db
import keyboards as kb
from config import ADMIN_IDS

logger = logging.getLogger(__name__)

async def admin_panel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ورود به پنل مدیریت"""
    user = update.effective_user
    if user.id not in ADMIN_IDS:
        if update.message:
            await update.message.reply_text("⛔️ شما به پنل مدیریت دسترسی ندارید.")
        elif update.callback_query:
            await update.callback_query.answer("⛔️ دسترسی غیرمجاز.", show_alert=True)
        return

    users_count = len(db.get_all_users())
    pending_orders = len(db.get_pending_orders())
    completed_orders = len(db.get_all_completed_orders())
    reservations = len(db.get_all_reservations())
    open_tickets = len(db.get_open_tickets())

    dashboard_text = f"""👑 **پنل مدیریت ربات تلگرام**

📊 **آمار کلی سیستم:**
👥 کل کاربران: **{users_count} نفر**
📥 رسیدهای در انتظار تایید: **{pending_orders} عدد**
📦 سفارشات موفق و تحویل داده شده: **{completed_orders} عدد**
📋 کل رزروها: **{reservations} مورد**
🎧 تیکت‌های فعال: **{open_tickets} عدد**

💳 شماره کارت فعال: `{db.get_setting('card_number')}`
👤 صاحب حساب: **{db.get_setting('card_holder')}** ({db.get_setting('bank_name')})

جهت مدیریت هر بخش، از دکمه‌های زیر استفاده کنید:"""

    if update.message:
        await update.message.reply_text(
            dashboard_text,
            reply_markup=kb.admin_panel_keyboard(),
            parse_mode="Markdown"
        )
    elif update.callback_query:
        await update.callback_query.edit_message_text(
            dashboard_text,
            reply_markup=kb.admin_panel_keyboard(),
            parse_mode="Markdown"
        )

async def admin_callback_dispatcher(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت دکمه‌های شیشه‌ای پنل ادمین"""
    query = update.callback_query
    user = update.effective_user
    data = query.data

    if user.id not in ADMIN_IDS:
        await query.answer("⛔️ دسترسی غیرمجاز.", show_alert=True)
        return

    await query.answer()

    # خروج از پنل
    if data == "adm_exit":
        await query.edit_message_text("از پنل مدیریت خارج شدید.")
        return

    # مشاهده سفارشات در انتظار
    elif data == "adm_view_pending":
        orders = db.get_pending_orders()
        if not orders:
            buttons = [[InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data="adm_back_main")]]
            await query.edit_message_text("✅ هیچ سفارش در انتظار بررسی یا تحویلی وجود ندارد.", reply_markup=InlineKeyboardMarkup(buttons))
            return
        
        text = "📥 **لیست سفارشات در انتظار:**\n\n"
        buttons = []
        for o in orders:
            status_text = "در انتظار تایید فیش" if o['status'] == 'pending_approval' else "در حال تهیه اکانت (تایید شده)"
            text += f"🔖 `{o['order_code']}` | {o['product_title']}\n👤 {o['full_name']} (@{o['username']}) | آیدی: `{o['telegram_id']}`\nوضعیت: {status_text}\n━━━━━━━━━━━━\n"
            if o['status'] == 'pending_approval':
                buttons.append([InlineKeyboardButton(f"بررسی فیش {o['order_code']}", callback_data=f"adm_appr_{o['id']}")])
            else:
                buttons.append([InlineKeyboardButton(f"🚀 ارسال اکانت {o['order_code']}", callback_data=f"adm_deliv_{o['id']}")])
        
        buttons.append([InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data="adm_back_main")])
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")

    # مشاهده سفارشات موفق و خریداران
    elif data == "adm_view_completed":
        completed_orders = db.get_all_completed_orders()
        if not completed_orders:
            buttons = [[InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data="adm_back_main")]]
            await query.edit_message_text("📦 هنوز هیچ سفارش تکمیل شده‌ای ثبت نشده است.", reply_markup=InlineKeyboardMarkup(buttons))
            return

        text = "📦 **لیست خریداران و سفارشات موفق:**\n\n"
        buttons = []
        for idx, o in enumerate(completed_orders, 1):
            username_str = f"@{o['username']}" if o['username'] else "بدون یوزرنیم"
            text += f"""{idx}️⃣ **{o['product_title']}**
🔖 کد: `{o['order_code']}` | مبلغ: **{o['amount']:,} تومان**
👤 خریدار: {o['full_name']} ({username_str})
🔢 شناسه عددی تلگرام: `{o['telegram_id']}`
📅 تاریخ: {o['created_at']}
━━━━━━━━━━━━━━━━━━━━━\n"""
            # دکمه ارسال پیام مستقیم به هر خریدار
            buttons.append([InlineKeyboardButton(f"✉️ ارسال پیام به {o['full_name']}", callback_data=f"adm_msg_user_{o['telegram_id']}")])

        buttons.append([InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data="adm_back_main")])
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")

    # مدیریت موجودی و وضعیت محصولات
    elif data == "adm_manage_products":
        products = db.get_products()
        text = "📊 **مدیریت موجودی و وضعیت محصولات**\n\nبرای تغییر تعداد موجودی یا تغییر وضعیت (موجود/ناموجود) هر اشتراک، روی آن کلیک کنید:"
        await query.edit_message_text(text, reply_markup=kb.admin_products_keyboard(products), parse_mode="Markdown")

    # صفحه مدیریت یک محصول خاص
    elif data.startswith("adm_prod_"):
        prod_code = data.replace("adm_prod_", "")
        product = db.get_product_by_code(prod_code)
        if not product:
            await query.answer("محصول یافت نشد.", show_alert=True)
            return

        status_str = f"✅ موجود ({product['stock']} اکانت فعال - قابلیت خرید مستقیم)" if (product['is_available'] and product['stock'] > 0) else "❌ ناموجود (فقط قابلیت رزرو)"
        
        text = f"""📦 **مدیریت محصول: {product['title_fa']}**

💰 قیمت ویژه: **{product['price_toman']:,} تومان**
📊 وضعیت فعلی: **{status_str}**
🔢 تعداد موجودی: **{product['stock']} عدد**

جهت تغییر وضعیت یا ویرایش تعداد موجودی، گزینه مورد نظر را انتخاب کنید:"""
        await query.edit_message_text(text, reply_markup=kb.admin_product_edit_keyboard(product), parse_mode="Markdown")

    # تغییر وضعیت موجود / ناموجود
    elif data.startswith("adm_ptog_"):
        prod_code = data.replace("adm_ptog_", "")
        product = db.get_product_by_code(prod_code)
        if not product:
            await query.answer("محصول یافت نشد.", show_alert=True)
            return

        if product["is_available"] and product["stock"] > 0:
            # تغییر به ناموجود
            db.update_product_stock(prod_code, is_available=0, stock=0)
            await query.answer("وضعیت محصول به ناموجود تغییر یافت.")
        else:
            # تغییر به موجود (پیش‌فرض ۱۰ عدد)
            db.update_product_stock(prod_code, is_available=1, stock=10)
            await query.answer("وضعیت محصول به موجود (۱۰ عدد) تغییر یافت.")

        updated_product = db.get_product_by_code(prod_code)
        status_str = f"✅ موجود ({updated_product['stock']} اکانت فعال - قابلیت خرید مستقیم)" if (updated_product['is_available'] and updated_product['stock'] > 0) else "❌ ناموجود (فقط قابلیت رزرو)"
        text = f"""📦 **مدیریت محصول: {updated_product['title_fa']}**

💰 قیمت ویژه: **{updated_product['price_toman']:,} تومان**
📊 وضعیت فعلی: **{status_str}**
🔢 تعداد موجودی: **{updated_product['stock']} عدد**

جهت تغییر وضعیت یا ویرایش تعداد موجودی، گزینه مورد نظر را انتخاب کنید:"""
        await query.edit_message_text(text, reply_markup=kb.admin_product_edit_keyboard(updated_product), parse_mode="Markdown")

    # درخواست تغییر تعداد موجودی
    elif data.startswith("adm_pstk_"):
        prod_code = data.replace("adm_pstk_", "")
        product = db.get_product_by_code(prod_code)
        if not product:
            await query.answer("محصول یافت نشد.", show_alert=True)
            return

        context.user_data["admin_state"] = "WAITING_FOR_PRODUCT_STOCK"
        context.user_data["target_product_code"] = prod_code

        await query.message.reply_text(
            f"🔢 لطفاً **تعداد موجودی جدید** برای اشتراک **{product['title_fa']}** را به صورت عدد انگلیسی وارد نمایید:\n(عدد 0 به معنی ناموجود و اتمام موجودی است)",
            reply_markup=kb.cancel_keyboard(),
            parse_mode="Markdown"
        )

    # مشاهده رزروها
    elif data == "adm_view_reservations":
        res_list = db.get_all_reservations()
        if not res_list:
            buttons = [[InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data="adm_back_main")]]
            await query.edit_message_text("📋 در حال حاضر هیچ درخواست رزروی ثبت نشده است.", reply_markup=InlineKeyboardMarkup(buttons))
            return
        
        text = "📋 **لیست کاربران متقاضی رزرو:**\n\n"
        buttons = []
        for idx, r in enumerate(res_list, 1):
            username_str = f"@{r['username']}" if r['username'] else "بدون یوزرنیم"
            text += f"{idx}️⃣ **{r['product_title']}**\n👤 {r['full_name']} ({username_str}) | شناسه: `{r['telegram_id']}`\n📅 {r['created_at']}\n━━━━━━━━━━━━\n"
            buttons.append([InlineKeyboardButton(f"✉️ پیام به {r['full_name']}", callback_data=f"adm_msg_user_{r['telegram_id']}")])

        buttons.append([InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data="adm_back_main")])
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")

    # مشاهده تیکت‌های باز
    elif data == "adm_view_tickets":
        tickets = db.get_open_tickets()
        if not tickets:
            buttons = [[InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data="adm_back_main")]]
            await query.edit_message_text("🎧 هیچ تیکت فعال یا باز نیازمند پاسخی وجود ندارد.", reply_markup=InlineKeyboardMarkup(buttons))
            return
        
        text = "🎧 **تیکت‌های فعال پشتیبانی:**\n\n"
        buttons = []
        for t in tickets:
            status_tag = "🔴 نیازمند پاسخ" if t['status'] == 'open' else "🟡 پاسخ داده شده (مهلت ۳۰ دقیقه)"
            text += f"🎫 `{t['ticket_code']}` از {t['full_name']} (@{t['username']})\nوضعیت: {status_tag}\nآخرین پیام: {t['last_message'][:60]}...\n━━━━━━━━━━━━\n"
            buttons.append([
                InlineKeyboardButton(f"✍️ پاسخ به {t['ticket_code']}", callback_data=f"adm_tkrep_{t['id']}"),
                InlineKeyboardButton("🔒 بستن", callback_data=f"adm_close_tk_{t['id']}")
            ])
        
        buttons.append([InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data="adm_back_main")])
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")

    # بستن تیکت توسط ادمین
    elif data.startswith("adm_close_tk_"):
        ticket_id = int(data.replace("adm_close_tk_", ""))
        ticket = db.get_ticket(ticket_id)
        if ticket:
            db.close_ticket(ticket_id)
            user_msg = f"""🔒 **تیکت پشتیبانی شما با کد `{ticket['ticket_code']}` بسته شد.**

در صورت داشتن سوال یا درخواست جدید، می‌توانید در هر زمان از بخش «🎧 پشتیبانی و تیکت» پیام جدید ارسال فرمایید."""
            try:
                await context.bot.send_message(chat_id=ticket["telegram_id"], text=user_msg, parse_mode="Markdown")
            except Exception as e:
                logger.error(f"Error notifying ticket close to {ticket['telegram_id']}: {e}")

            await query.edit_message_text(
                f"✅ تیکت `{ticket['ticket_code']}` با موفقیت بسته شد.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت به تیکت‌ها", callback_data="adm_view_tickets")]])
            )

    # تنظیمات شماره کارت
    elif data == "adm_edit_card":
        text = f"""💳 **تنظیمات حساب بانکی**

شماره کارت فعلی: `{db.get_setting('card_number')}`
صاحب حساب: **{db.get_setting('card_holder')}**
نام بانک: **{db.get_setting('bank_name')}**

برای تغییر شماره کارت، روی دکمه زیر کلیک کنید:"""
        buttons = [
            [InlineKeyboardButton("✏️ تغییر شماره کارت و مشخصات", callback_data="adm_change_card_prompt")],
            [InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data="adm_back_main")]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")

    # درخواست تغییر کارت
    elif data == "adm_change_card_prompt":
        context.user_data["admin_state"] = "WAITING_FOR_CARD_NUMBER"
        await query.message.reply_text(
            "لطفاً **شماره کارت جدید** را با ارقام انگلیسی یا فارسی وارد کنید (مثال: 6037997512345678):",
            reply_markup=kb.cancel_keyboard()
        )

    # پیام همگانی
    elif data == "adm_broadcast":
        context.user_data["admin_state"] = "WAITING_FOR_BROADCAST"
        await query.message.reply_text(
            "📢 لطفاً متن پیام همگانی را که می‌خواهید برای تمام کاربران ارسال شود بفرستید:",
            reply_markup=kb.cancel_keyboard()
        )

    # پیام مستقیم به کاربر (نمایش لیست کاربران + امکان تایپ آیدی)
    elif data == "adm_direct_msg":
        users = db.get_all_users()[:10] # ۱۰ کاربر اخیر
        buttons = []
        text = "👤 **ارسال پیام مستقیم به کاربر**\n\nمی‌توانید روی نام یکی از کاربران اخیر زیر کلیک کنید یا **شناسه عددی (Telegram ID)** یا **یوزرنیم** او را بفرستید:\n\n"
        for u in users:
            username_str = f"@{u['username']}" if u['username'] else "بدون یوزرنیم"
            text += f"🔹 {u['full_name']} ({username_str}) | شناسه: `{u['telegram_id']}`\n"
            buttons.append([InlineKeyboardButton(f"✉️ پیام به {u['full_name']}", callback_data=f"adm_msg_user_{u['telegram_id']}")])

        buttons.append([InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data="adm_back_main")])
        context.user_data["admin_state"] = "WAITING_FOR_DIRECT_ID"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")

    # انتخاب مستقیم کاربر از روی دکمه جهت پیام
    elif data.startswith("adm_msg_user_"):
        target_id = int(data.replace("adm_msg_user_", ""))
        context.user_data["target_direct_id"] = target_id
        context.user_data["admin_state"] = "WAITING_FOR_DIRECT_TEXT"
        await query.message.reply_text(
            f"✉️ لطفاً متن پیامی که می‌خواهید برای کاربر با شناسه `{target_id}` ارسال شود را بنویسید:",
            reply_markup=kb.cancel_keyboard(),
            parse_mode="Markdown"
        )

    # بازگشت به منوی اصلی ادمین
    elif data == "adm_back_main":
        await admin_panel_command(update, context)

    # تایید واریز
    elif data.startswith("adm_appr_"):
        order_id = int(data.replace("adm_appr_", ""))
        order = db.get_order(order_id)
        if not order:
            await query.answer("سفارش یافت نشد.", show_alert=True)
            return

        db.update_order_status(order_id, "processing")

        # ارسال پیام به خریدار
        user_msg = f"""🎉 **پرداخت شما تایید شد!**

🔖 کد سفارش: `{order['order_code']}`
📦 محصول: **{order['product_title']}**

⏳ سفارش شما در مرحله تهیه و فعال‌سازی قرار گرفت. به محض آماده شدن، اطلاعات فعال‌سازی و لینک ساب برای شما در همین ربات ارسال خواهد شد."""
        try:
            await context.bot.send_message(chat_id=order["telegram_id"], text=user_msg, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Error notifying buyer {order['telegram_id']}: {e}")

        await query.edit_message_caption(
            caption=f"✅ واریز سفارش `{order['order_code']}` تایید شد.\nاکنون می‌توانید اطلاعات اکانت را جهت تحویل ارسال کنید یا در صورت عدم امکان تهیه، درخواست عودت وجه ثبت فرمایید.",
            reply_markup=kb.admin_deliver_keyboard(order_id),
            parse_mode="Markdown"
        )

    # رد واریز
    elif data.startswith("adm_rejc_"):
        order_id = int(data.replace("adm_rejc_", ""))
        order = db.get_order(order_id)
        if not order:
            await query.answer("سفارش یافت نشد.", show_alert=True)
            return

        db.update_order_status(order_id, "rejected")

        # ارسال پیام به خریدار
        user_msg = f"""❌ **رسید واریزی شما تایید نشد.**

🔖 کد سفارش: `{order['order_code']}`
📦 محصول: **{order['product_title']}**

علت احتمالی: عدم تطابق مبلغ، واریز ناموفق یا ناخوانا بودن فیش.
در صورت نیاز به بررسی مجدد، می‌توانید از طریق بخش **«🎧 پشتیبانی و تیکت»** با ما در ارتباط باشید."""
        try:
            await context.bot.send_message(chat_id=order["telegram_id"], text=user_msg, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Error notifying buyer {order['telegram_id']}: {e}")

        await query.edit_message_caption(
            caption=f"❌ واریز سفارش `{order['order_code']}` رد شد و به مشتری اطلاع‌رسانی گردید.",
            parse_mode="Markdown"
        )

    # درخواست ارسال لینک اکانت به خریدار
    elif data.startswith("adm_deliv_"):
        order_id = int(data.replace("adm_deliv_", ""))
        context.user_data["admin_state"] = "WAITING_FOR_DELIVERY"
        context.user_data["target_order_id"] = order_id
        
        await query.message.reply_text(
            f"🚀 لطفاً **لینک ساب، لینک فعال‌سازی یا مشخصات اکانت** را برای سفارش شماره {order_id} بفرستید تا همراه با راهنمای فعال‌سازی برای خریدار ارسال شود:",
            reply_markup=kb.cancel_keyboard()
        )

    # عدم امکان تهیه اکانت و درخواست عودت وجه
    elif data.startswith("adm_refund_"):
        order_id = int(data.replace("adm_refund_", ""))
        order = db.get_order(order_id)
        if not order:
            await query.answer("سفارش یافت نشد.", show_alert=True)
            return

        db.update_order_status(order_id, "refund_pending")

        user_refund_msg = f"""⚠️ **مشتری گرامی، با پوزش فراوان**

متاسفانه در حال حاضر به دلیل محدودیت‌های تامین‌کننده، امکان آماده‌سازی و فعال‌سازی سفارش **{order['product_title']}** (کد سفارش: `{order['order_code']}`) مقدور نمی‌باشد.

💳 **لطفاً شماره کارت ۱۶ رقمی و نام صاحب حساب خود را همینجا در پاسخ به این پیام (یا از بخش پشتیبانی) ارسال نمایید تا مبلغ واریزی ({order['amount']:,} تومان) فوراً به حساب شما بازگردانده شود.**

از شکیبایی، صبوری و درک شما بی‌نهایت سپاسگزاریم. 🙏"""

        try:
            await context.bot.send_message(chat_id=order["telegram_id"], text=user_refund_msg, parse_mode="Markdown")
            await query.edit_message_caption(
                caption=f"⚠️ به خریدار سفارش `{order['order_code']}` اعلام شد که امکان تهیه اکانت وجود ندارد و درخواست شماره کارت جهت عودت وجه ارسال گردید.",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Error notifying refund to buyer {order['telegram_id']}: {e}")

    # پاسخ به تیکت
    elif data.startswith("adm_tkrep_"):
        ticket_id = int(data.replace("adm_tkrep_", ""))
        ticket = db.get_ticket(ticket_id)
        if not ticket:
            await query.answer("تیکت یافت نشد.", show_alert=True)
            return
        
        context.user_data["admin_state"] = "WAITING_FOR_TICKET_REPLY"
        context.user_data["target_ticket_id"] = ticket_id

        await query.message.reply_text(
            f"✍️ لطفاً متن پاسخ خود را برای تیکت `{ticket['ticket_code']}` (کاربر: {ticket['full_name']}) بنویسید:",
            reply_markup=kb.cancel_keyboard()
        )


async def handle_admin_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """پردازش متن‌های ورودی ادمین در حالت‌های مختلف. در صورت پردازش True برمی‌گرداند."""
    user = update.effective_user
    if user.id not in ADMIN_IDS:
        return False

    state = context.user_data.get("admin_state")
    if not state:
        return False

    text = update.message.text.strip()

    if text in ["❌ انصراف و بازگشت به منو", "انصراف"]:
        context.user_data.pop("admin_state", None)
        context.user_data.pop("target_order_id", None)
        context.user_data.pop("target_ticket_id", None)
        context.user_data.pop("target_direct_id", None)
        await update.message.reply_text("عملیات مدیریتی لغو شد.", reply_markup=kb.main_menu_keyboard(is_admin=True))
        return True

    # حالت ارسال اطلاعات و تحویل اکانت
    if state == "WAITING_FOR_DELIVERY":
        order_id = context.user_data.get("target_order_id")
        order = db.get_order(order_id)
        
        if order:
            db.update_order_status(order_id, "completed", delivery_payload=text)
            
            buyer_msg = f"""🎉 **اکانت شما با موفقیت آماده و تحویل گردید!**

📦 اشتراک: **{order['product_title']}**
🔖 کد سفارش: `{order['order_code']}`

━━━━━━━━━━━━━━━━━━━━━
🔑 **لینک فعال‌سازی / اطلاعات اشتراک شما:**
{text}
━━━━━━━━━━━━━━━━━━━━━

⚠️ **دستورالعمل بسیار مهم فعال‌سازی (لطفاً دقیقاً به ترتیب زیر عمل کنید):**

۱️⃣ **عدم استفاده در مرورگر دیگر:** به هیچ عنوان این لینک را در مرورگر یا اکانت شخص دیگری باز نکنید.
۲️⃣ **انتخاب اکانت صحیح:** صرفاً وارد مرورگر Google Chrome شوید که اکانت جیمیل اصلی‌تان روی آن فعال است و می‌خواهید اشتراک روی همان ایمیل فعال شود.
۳️⃣ **فیلترشکن مناسب:** حتماً و حتماً از وی‌پی‌ان باکیفیت (ترجیحاً با **IP کشور آمریکا - USA**) استفاده کنید.
۴️⃣ **فعال‌سازی:** لینک فعال‌سازی بالا را کپی کرده و در نوار آدرس مرورگر کروم Paste و باز کنید.
۵️⃣ **ثبت در گوگل وان:** وارد صفحه رسمی فعال‌سازی Google One می‌شوید؛ مراحل تایید را بزنید تا اکانت ثبت و فعال شود.
۶️⃣ **ورود به جمینای:** پس از تایید توسط گوگل، هوش مصنوعی جمینای در آدرس زیر برای شما فعال است:
🌐 https://gemini.google.com/

━━━━━━━━━━━━━━━━━━━━━
💡 **راهنما:** شما می‌توانید در هر زمان با مراجعه به بخش «📦 اکانت‌های خریداری شده من» در منوی اصلی ربات، مشخصات و لینک اکانت خود را مجدداً مشاهده نمایید.
در صورت وجود هرگونه سوال، از بخش پشتیبانی پاسخگوی شما هستیم. با تشکر از اعتماد شما! ✨"""

            try:
                await context.bot.send_message(chat_id=order["telegram_id"], text=buyer_msg, parse_mode="Markdown")
                await update.message.reply_text(
                    f"✅ مشخصات اکانت به همراه راهنمای کامل با موفقیت برای خریدار ارسال و سفارش `{order['order_code']}` تکمیل شد.",
                    reply_markup=kb.main_menu_keyboard(is_admin=True)
                )
            except Exception as e:
                await update.message.reply_text(f"❌ خطا در ارسال پیام به کاربر: {e}")

        context.user_data.pop("admin_state", None)
        context.user_data.pop("target_order_id", None)
        return True

    # حالت پاسخ به تیکت
    if state == "WAITING_FOR_TICKET_REPLY":
        ticket_id = context.user_data.get("target_ticket_id")
        ticket = db.get_ticket(ticket_id)
        
        if ticket:
            db.add_ticket_message(ticket_id, "admin", text)
            
            user_msg = f"""📩 **پاسخ پشتیبانی به تیکت شما ({ticket['ticket_code']}):**

{text}

━━━━━━━━━━━━━━━━━━━━━
⏳ **مهلت پاسخ:** در صورتی که تا **۳۰ دقیقه** آینده پاسخی ارسال نفرمایید، این تیکت به صورت خودکار بسته خواهد شد."""

            try:
                await context.bot.send_message(chat_id=ticket["telegram_id"], text=user_msg, parse_mode="Markdown")
                await update.message.reply_text(
                    f"✅ پاسخ شما برای تیکت `{ticket['ticket_code']}` با موفقیت به کاربر ارسال شد (مهلت ۳۰ دقیقه‌ای فعال گردید).",
                    reply_markup=kb.main_menu_keyboard(is_admin=True)
                )
            except Exception as e:
                await update.message.reply_text(f"❌ خطا در ارسال پاسخ به کاربر: {e}")

        context.user_data.pop("admin_state", None)
        context.user_data.pop("target_ticket_id", None)
        return True

    # حالت تغییر شماره کارت
    if state == "WAITING_FOR_CARD_NUMBER":
        db.set_setting("card_number", text)
        context.user_data["admin_state"] = "WAITING_FOR_CARD_HOLDER"
        await update.message.reply_text("✅ شماره کارت ذخیره شد.\nاکنون **نام صاحب حساب** را وارد کنید:")
        return True

    if state == "WAITING_FOR_CARD_HOLDER":
        db.set_setting("card_holder", text)
        context.user_data["admin_state"] = "WAITING_FOR_BANK_NAME"
        await update.message.reply_text("✅ نام صاحب حساب ذخیره شد.\nاکنون **نام بانک** را وارد کنید:")
        return True

    if state == "WAITING_FOR_BANK_NAME":
        db.set_setting("bank_name", text)
        context.user_data.pop("admin_state", None)
        await update.message.reply_text(
            f"✅ اطلاعات حساب بانکی با موفقیت به‌روزرسانی شد:\n💳 کارت: `{db.get_setting('card_number')}`\n👤 نام: {db.get_setting('card_holder')}\n🏛 بانک: {db.get_setting('bank_name')}",
            reply_markup=kb.main_menu_keyboard(is_admin=True)
        )
        return True

    # حالت پیام همگانی
    if state == "WAITING_FOR_BROADCAST":
        users = db.get_all_users()
        sent_count = 0
        fail_count = 0
        await update.message.reply_text(f"⏳ در حال ارسال پیام به {len(users)} کاربر...")

        for u in users:
            try:
                await context.bot.send_message(chat_id=u["telegram_id"], text=text, parse_mode="Markdown")
                sent_count += 1
            except Exception:
                fail_count += 1

        context.user_data.pop("admin_state", None)
        await update.message.reply_text(
            f"📢 ارسال پیام همگانی پایان یافت.\n✅ موفق: {sent_count}\n❌ ناموفق (بلاک ربات یا غیرفعال): {fail_count}",
            reply_markup=kb.main_menu_keyboard(is_admin=True)
        )
        return True

    # حالت دریافت آیدی برای پیام مستقیم
    if state == "WAITING_FOR_DIRECT_ID":
        clean_text = text.replace("@", "").strip()
        target_id = None
        
        if clean_text.isdigit():
            target_id = int(clean_text)
        else:
            # جستجو بر اساس یوزرنیم در دیتابیس
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT telegram_id FROM users WHERE LOWER(username) = LOWER(?)", (clean_text,))
                row = cursor.fetchone()
                if row:
                    target_id = row[0]

        if not target_id:
            await update.message.reply_text("❌ کاربر مورد نظر با این شناسه یا یوزرنیم یافت نشد. لطفاً شناسه عددی تلگرام یا یوزرنیم دقیق را وارد کنید:")
            return True
        
        context.user_data["target_direct_id"] = target_id
        context.user_data["admin_state"] = "WAITING_FOR_DIRECT_TEXT"
        await update.message.reply_text(f"اکنون متن پیامی که می‌خواهید به کاربر `{target_id}` ارسال شود را بنویسید:")
        return True

    # حالت تغییر تعداد موجودی محصول
    if state == "WAITING_FOR_PRODUCT_STOCK":
        prod_code = context.user_data.get("target_product_code")
        product = db.get_product_by_code(prod_code)
        
        if not text.isdigit():
            await update.message.reply_text("❌ لطفاً یک عدد معتبر وارد کنید (مثال: 0 یا 15):")
            return True

        new_stock = int(text)
        is_avail = 1 if new_stock > 0 else 0
        db.update_product_stock(prod_code, is_available=is_avail, stock=new_stock)

        status_desc = f"✅ موجود ({new_stock} عدد - قابلیت خرید مستقیم)" if new_stock > 0 else "❌ ناموجود (ثبت رزرو توسط کاربران)"

        context.user_data.pop("admin_state", None)
        context.user_data.pop("target_product_code", None)

        await update.message.reply_text(
            f"✅ موجودی محصول **{product['title_fa']}** با موفقیت به‌روزرسانی شد:\n📊 وضعیت جدید: **{status_desc}**\n🔢 تعداد: **{new_stock} عدد**",
            reply_markup=kb.main_menu_keyboard(is_admin=True),
            parse_mode="Markdown"
        )
        return True

    # ارسال پیام مستقیم به کاربر
    if state == "WAITING_FOR_DIRECT_TEXT":
        target_id = context.user_data.get("target_direct_id")
        user_msg = f"""📩 **پیام مستقیم از مدیریت:**

{text}"""
        try:
            await context.bot.send_message(chat_id=target_id, text=user_msg, parse_mode="Markdown")
            await update.message.reply_text(f"✅ پیام به کاربر `{target_id}` با موفقیت تحویل داده شد.", reply_markup=kb.main_menu_keyboard(is_admin=True))
        except Exception as e:
            await update.message.reply_text(f"❌ ارسال پیام با خطا مواجه شد: {e}", reply_markup=kb.main_menu_keyboard(is_admin=True))

        context.user_data.pop("admin_state", None)
        context.user_data.pop("target_direct_id", None)
        return True

    return False
