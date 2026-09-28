import logging
import sys
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters
)
import config
import database as db
import handlers_user as user_handlers
import handlers_admin as admin_handlers

# تنظیم لاگر
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """نقطه ورود و اجرای اصلی ربات تلگرام"""
    print("=" * 60)
    print("🚀 در حال راه‌اندازی ربات فروش و رزرو اکانت‌های اشتراکی...")
    print("=" * 60)

    # بررسی توکن ربات
    if not config.BOT_TOKEN or config.BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("\n❌ خطا: توکن ربات تلگرام تنظیم نشده است!")
        print("💡 لطفاً فایل .env را باز کرده و مقدار BOT_TOKEN را با توکن دریافتی از @BotFather جایگزین کنید.")
        print("مثال: BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRstuVWXyz\n")
        sys.exit(1)

    # آماده‌سازی و راه‌اندازی دیتابیس
    print("📦 در حال بررسی و ساخت جداول دیتابیس (SQLite)...")
    db.init_db()
    print("✅ دیتابیس با موفقیت متصل شد.")

    if not config.ADMIN_IDS or config.ADMIN_IDS == [0]:
        print("⚠️ هشدار: شناسه عددی ادمین (ADMIN_IDS) در فایل .env تنظیم نشده است.")
        print("💡 برای دسترسی به پنل مدیریت، شناسه عددی تلگرام خود را در .env قرار دهید.\n")
    else:
        print(f"👑 ادمین‌های مجاز شناسایی شدند: {config.ADMIN_IDS}")

    # ساخت اپلیکیشن تلگرام
    application = ApplicationBuilder().token(config.BOT_TOKEN).build()

    # --- ثبت دستورات ---
    application.add_handler(CommandHandler(["start", "menu"], user_handlers.start_command))
    application.add_handler(CommandHandler("admin", admin_handlers.admin_panel_command))

    # --- ثبت رویدادهای شیشه‌ای (Callback Queries) ---
    # محصولات و خرید
    application.add_handler(CallbackQueryHandler(user_handlers.catalog_back_callback, pattern="^catalog_back$"))
    application.add_handler(CallbackQueryHandler(user_handlers.product_detail_callback, pattern="^prod_"))
    application.add_handler(CallbackQueryHandler(user_handlers.buy_callback, pattern="^buy_"))
    application.add_handler(CallbackQueryHandler(user_handlers.reserve_callback, pattern="^reserve_"))
    application.add_handler(CallbackQueryHandler(user_handlers.send_receipt_action_callback, pattern="^send_receipt_"))
    application.add_handler(CallbackQueryHandler(user_handlers.cancel_order_callback, pattern="^cancel_order$"))
    application.add_handler(CallbackQueryHandler(user_handlers.menu_callback_dispatcher, pattern="^menu_"))

    # پنل و اقدامات ادمین
    application.add_handler(CallbackQueryHandler(admin_handlers.admin_callback_dispatcher, pattern="^adm_"))

    # --- ثبت پیام‌های متنی و تصاویر ---
    # عکس‌ها (فیش واریز، تیکت پشتیبانی)
    application.add_handler(MessageHandler(filters.PHOTO, user_handlers.handle_user_photo_receipt))

    # پیام‌های متنی
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, user_handlers.handle_user_text_message))

    print("\n✅ ربات با موفقیت فعال شد و آماده دریافت پیام‌ها می‌باشد (Long Polling)...")
    print("برای توقف ربات کلیدهای Ctrl + C را فشار دهید.\n")

    # اجرای ربات با Polling
    application.run_polling()

if __name__ == "__main__":
    main()
