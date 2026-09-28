from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict, Any

def main_menu_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """کیبورد منوی اصلی ربات (دکمه‌های پایین صفحه)"""
    keyboard = [
        [KeyboardButton("🛍 لیست اشتراک‌ها و خرید")],
        [KeyboardButton("📦 اکانت‌های خریداری شده من"), KeyboardButton("🎧 پشتیبانی و تیکت")]
    ]
    if is_admin:
        keyboard.append([KeyboardButton("⚙️ پنل مدیریت ادمین")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def cancel_keyboard() -> ReplyKeyboardMarkup:
    """کیبورد انصراف"""
    return ReplyKeyboardMarkup([[KeyboardButton("❌ انصراف و بازگشت به منو")]], resize_keyboard=True)

def welcome_inline_keyboard(products: List[Dict[str, Any]], is_admin: bool = False) -> InlineKeyboardMarkup:
    """کیبورد شیشه‌ای خوش‌آمدگویی و دسترسی سریع که مستقیماً زیر پیام ظاهر می‌شود"""
    buttons = []
    
    # دکمه‌های محصولات
    for p in products:
        if p["code"] == "gemini_18m":
            text = f"🤖 {p['title_fa']} - (✅ موجود)"
        elif p["code"] == "youtube_3m":
            text = f"🎬 {p['title_fa']} - (🔔 رزرو)"
        elif p["code"] == "notion_3m":
            text = f"📝 {p['title_fa']} - (🔔 رزرو)"
        else:
            status_icon = "✅ موجود" if p["is_available"] else "🔔 رزرو"
            text = f"{p['title_fa']} - ({status_icon})"
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"prod_{p['code']}")])
    
    # دکمه‌های منو
    buttons.append([
        InlineKeyboardButton("📦 اکانت‌های من", callback_data="menu_my_orders"),
        InlineKeyboardButton("🎧 پشتیبانی", callback_data="menu_support")
    ])
    
    # دکمه پنل ادمین
    if is_admin:
        buttons.append([InlineKeyboardButton("⚙️ پنل مدیریت ادمین", callback_data="menu_admin")])
        
    return InlineKeyboardMarkup(buttons)

def products_inline_keyboard(products: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """کیبورد شیشه‌ای لیست محصولات"""
    buttons = []
    for p in products:
        status_icon = "✅ موجود" if p["is_available"] else "🔔 رزرو (ناموجود)"
        text = f"{p['title_fa']} - {status_icon}"
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"prod_{p['code']}")])
    buttons.append([InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="menu_start")])
    return InlineKeyboardMarkup(buttons)

def product_detail_keyboard(product: Dict[str, Any]) -> InlineKeyboardMarkup:
    """کیبورد جزییات محصول (پرداخت یا رزرو)"""
    buttons = []
    if product["is_available"]:
        buttons.append([InlineKeyboardButton("💳 پرداخت و ثبت سفارش", callback_data=f"buy_{product['code']}")])
    else:
        buttons.append([InlineKeyboardButton("🔔 رزرو این اشتراک", callback_data=f"reserve_{product['code']}")])
    
    buttons.append([InlineKeyboardButton("🔙 بازگشت به لیست اشتراک‌ها", callback_data="catalog_back")])
    return InlineKeyboardMarkup(buttons)

def payment_action_keyboard(order_id: int) -> InlineKeyboardMarkup:
    """کیبورد اقدامات صفحه پرداخت"""
    buttons = [
        [InlineKeyboardButton("📸 ارسال تصویر فیش واریزی", callback_data=f"send_receipt_{order_id}")],
        [InlineKeyboardButton("❌ انصراف از خرید", callback_data="cancel_order")]
    ]
    return InlineKeyboardMarkup(buttons)

def admin_order_keyboard(order_id: int) -> InlineKeyboardMarkup:
    """کیبورد ادمین برای تایید/رد فیش"""
    buttons = [
        [
            InlineKeyboardButton("✅ تایید واریز", callback_data=f"adm_appr_{order_id}"),
            InlineKeyboardButton("❌ رد واریز", callback_data=f"adm_rejc_{order_id}")
        ]
    ]
    return InlineKeyboardMarkup(buttons)

def admin_deliver_keyboard(order_id: int) -> InlineKeyboardMarkup:
    """کیبورد ارسال اطلاعات اکانت یا عودت وجه توسط ادمین"""
    buttons = [
        [InlineKeyboardButton("🚀 ارسال لینک ساب / فعال‌سازی", callback_data=f"adm_deliv_{order_id}")],
        [InlineKeyboardButton("⚠️ عدم امکان تهیه اکانت (درخواست شماره کارت و عودت وجه)", callback_data=f"adm_refund_{order_id}")]
    ]
    return InlineKeyboardMarkup(buttons)

def admin_ticket_reply_keyboard(ticket_id: int) -> InlineKeyboardMarkup:
    """کیبورد پاسخ و بستن تیکت توسط ادمین"""
    buttons = [
        [
            InlineKeyboardButton("✍️ پاسخ به این تیکت", callback_data=f"adm_tkrep_{ticket_id}"),
            InlineKeyboardButton("🔒 بستن تیکت", callback_data=f"adm_close_tk_{ticket_id}")
        ]
    ]
    return InlineKeyboardMarkup(buttons)

def admin_panel_keyboard() -> InlineKeyboardMarkup:
    """کیبورد منوی پنل مدیریت"""
    buttons = [
        [
            InlineKeyboardButton("📥 سفارشات در انتظار (رسیدها)", callback_data="adm_view_pending"),
            InlineKeyboardButton("📦 خریداران و سفارشات موفق", callback_data="adm_view_completed")
        ],
        [
            InlineKeyboardButton("📊 مدیریت موجودی و محصولات", callback_data="adm_manage_products"),
            InlineKeyboardButton("📋 لیست رزروها", callback_data="adm_view_reservations")
        ],
        [
            InlineKeyboardButton("🎧 تیکت‌های پشتیبانی", callback_data="adm_view_tickets"),
            InlineKeyboardButton("💳 تنظیمات شماره کارت", callback_data="adm_edit_card")
        ],
        [
            InlineKeyboardButton("👤 پیام مستقیم به کاربر", callback_data="adm_direct_msg"),
            InlineKeyboardButton("📢 پیام همگانی به همه", callback_data="adm_broadcast")
        ],
        [
            InlineKeyboardButton("🔙 خروج از پنل مدیریت", callback_data="adm_exit")
        ]
    ]
    return InlineKeyboardMarkup(buttons)

def admin_products_keyboard(products: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """کیبورد لیست محصولات جهت مدیریت موجودی توسط ادمین"""
    buttons = []
    for p in products:
        status_tag = f"✅ موجود ({p['stock']} عدد)" if (p["is_available"] and p["stock"] > 0) else "❌ ناموجود"
        buttons.append([InlineKeyboardButton(f"{p['title_fa']} - {status_tag}", callback_data=f"adm_prod_{p['code']}")])
    buttons.append([InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data="adm_back_main")])
    return InlineKeyboardMarkup(buttons)

def admin_product_edit_keyboard(product: Dict[str, Any]) -> InlineKeyboardMarkup:
    """کیبورد ویرایش یک محصول خاص (تغییر موجودی یا وضعیت)"""
    toggle_text = "❌ تغییر وضعیت به ناموجود (رزرو)" if (product["is_available"] and product["stock"] > 0) else "✅ تغییر وضعیت به موجود (فعال برای خرید)"
    buttons = [
        [InlineKeyboardButton(toggle_text, callback_data=f"adm_ptog_{product['code']}")],
        [InlineKeyboardButton("🔢 تغییر تعداد موجودی (عدد)", callback_data=f"adm_pstk_{product['code']}")],
        [InlineKeyboardButton("🔙 بازگشت به لیست محصولات", callback_data="adm_manage_products")]
    ]
    return InlineKeyboardMarkup(buttons)
