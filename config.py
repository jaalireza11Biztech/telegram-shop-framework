import os
from pathlib import Path

# مسیر پایه پروژه
BASE_DIR = Path(__file__).resolve().parent

# لودر ساده و مستقل .env بدون نیاز به پکیج‌های خارجی
def load_env():
    env_path = BASE_DIR / ".env"
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))

load_env()

# توکن ربات تلگرام (از @BotFather دریافت می‌شود)
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# شناسه عددی تلگرام ادمین‌ها (با کاما جدا شوند، مثلا: 123456789,987654321)
ADMIN_IDS_RAW = os.getenv("ADMIN_IDS", "6394055914")
ADMIN_IDS = [int(x.strip()) for x in ADMIN_IDS_RAW.split(",") if x.strip().isdigit()]

# مسیر فایل دیتابیس SQLite
DB_PATH = os.getenv("DB_PATH", str(BASE_DIR / "bot_database.db"))

# اطلاعات پیش‌فرض کارت بانکی
DEFAULT_CARD_NUMBER = os.getenv("DEFAULT_CARD_NUMBER", "6104337940547613")
DEFAULT_CARD_HOLDER = os.getenv("DEFAULT_CARD_HOLDER", "علیرضا جلالیان")
DEFAULT_BANK_NAME = os.getenv("DEFAULT_BANK_NAME", "بانک ملت")
