import sqlite3
import datetime
from typing import Optional, List, Dict, Any
from config import DB_PATH, DEFAULT_CARD_NUMBER, DEFAULT_CARD_HOLDER, DEFAULT_BANK_NAME

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """ایجاد جداول دیتابیس و داده‌های پیش‌فرض اولیه"""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # جدول کاربران
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            full_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # جدول محصولات
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            title_fa TEXT NOT NULL,
            description_fa TEXT NOT NULL,
            price_toman INTEGER NOT NULL,
            original_price_toman INTEGER NOT NULL,
            is_available INTEGER DEFAULT 1,
            stock INTEGER DEFAULT 0
        )
        """)
        
        # جدول سفارشات
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_code TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            receipt_file_id TEXT,
            status TEXT DEFAULT 'pending_receipt',
            delivery_payload TEXT,
            admin_notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
        """)
        
        # جدول رزروها
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
        """)
        
        # جدول تیکت‌های پشتیبانی
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_code TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            status TEXT DEFAULT 'open',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """)
        
        # جدول پیام‌های تیکت
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ticket_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER NOT NULL,
            sender TEXT NOT NULL,
            text TEXT,
            file_id TEXT,
            file_type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ticket_id) REFERENCES tickets (id)
        )
        """)
        
        # جدول تنظیمات سیستم (شماره کارت، نام صاحب حساب و ...)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """)
        
        # درج محصولات اولیه در صورت خالی بودن
        cursor.execute("SELECT COUNT(*) FROM products")
        if cursor.fetchone()[0] == 0:
            gemini_desc = """🤖 **اکانت اشتراکی جمینای پرو ۱۸ ماهه (Google AI Pro)**

💲 قیمت ویژه: **۹۰۰,۰۰۰ تومان** (قیمت اصلی: ~~۱,۸۰۰,۰۰۰ تومان~~)
📊 موجودی: ۳۱ اکانت فعال

📋 **مشخصات و قابلیت‌های ویژه:**
🔹 **۵ ترابایت فضای ذخیره‌سازی ابری گوگل (5 TB Cloud Storage)**
🔹 دسترسی کامل به بالاترین مدل هوش مصنوعی **Gemini 3.1 Pro**
🔹 قابلیت تحقیق عمیق و هوشمند **(Deep Research)**
🔹 ادغام کامل جمینای در ابزارهای **Gmail, Google Docs & Sheets**
🔹 بدون نیاز به کردیت کارت یا حساب بانکی خارجی
🔹 فعال‌سازی رسمی و قانونی روی اکانت جیمیل شخصی شما
🔹 بدون محدودیت کشوری (No Country Issue)
🔹 تحویل فوری و فعال‌سازی آسان

✨ **گارانتی و ضمانت:**
🛡 ۱۲ ساعت گارانتی نگهداری و تعویض اولیه
⚡️ تحویل سریع لینک فعال‌سازی پس از تایید واریز"""

            youtube_desc = """🎬 **اشتراک یوتیوب پریمیوم ۳ ماهه (YouTube Premium)**

💲 قیمت ویژه: **۱,۱۰۰,۰۰۰ تومان** (قیمت اصلی: ~~۱,۹۰۰,۰۰۰ تومان~~)
📊 وضعیت: **ناموجود** (امکان ثبت رزرو رایگان)

📋 **توضیحات و مزایا:**
✅ اشتراک ۳ ماهه یوتیوب پریمیوم اختصاصی
🚫 مشاهده تمام ویدیوهای یوتیوب بدون هیچ‌گونه تبلیغات (Ad-Free)
🎵 دسترسی رایگان به سرویس YouTube Music Premium
📱 قابلیت پخش در پس‌زمینه گوشی (Background Play)
⬇️ امکان دانلود مستقیم و تماشای آفلاین ویدیوها

✨ **شرایط مهم فعال‌سازی:**
🆕 فقط قابل فعال‌سازی روی اکانت‌های جدید یا اکانت‌هایی که قبلا ترایال نداشته‌اند.
🌍 پشتیبانی از کشورهای فعال (آمریکا، آلمان، ترکیه، امارات، کانادا و...)
🛡 ضمانت تعویض لینک در صورت هرگونه مشکل"""

            notion_desc = """📝 **اشتراک نوشن بیزینس ۳ ماهه (Notion Business)**

💲 قیمت ویژه: **۱,۶۰۰,۰۰۰ تومان** (قیمت اصلی: ~~۲,۵۰۰,۰۰۰ تومان~~)
📊 وضعیت: **ناموجود** (امکان ثبت رزرو رایگان)

📋 **توضیحات و مزایا:**
⚡️ تحویل کد/کوپن فعال‌سازی اختصاصی
✔️ دریافت ۴۰۰ کردیت ماهانه (400 Credits Per Month)
👥 دسترسی کامل به قابلیت‌های تیم و ورک‌اسپیس بیزینس
🤖 هوش مصنوعی قدرتمند نوشن (Notion AI)
🛡⚡️ دارای ۳ ماه گارانتی کامل"""

            products_data = [
                ("gemini_18m", "جمینای پرو ۱۸ ماهه (Gemini Pro)", gemini_desc, 900000, 1800000, 1, 31),
                ("youtube_3m", "یوتیوب پریمیوم ۳ ماهه (YouTube Premium)", youtube_desc, 1100000, 1900000, 0, 0),
                ("notion_3m", "نوشن بیزینس ۳ ماهه (Notion Business)", notion_desc, 1600000, 2500000, 0, 0),
            ]
            cursor.executemany("""
            INSERT INTO products (code, title_fa, description_fa, price_toman, original_price_toman, is_available, stock)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, products_data)

        # درج تنظیمات پیش‌فرض در صورت عدم وجود
        default_settings = [
            ("card_number", DEFAULT_CARD_NUMBER),
            ("card_holder", DEFAULT_CARD_HOLDER),
            ("bank_name", DEFAULT_BANK_NAME),
            ("support_guide", "لطفاً متن، عکس یا داکیومنت مشکل خود را ارسال کنید تا برای کارشناسان پشتیبانی تیکت ثبت شود.")
        ]
        for key, val in default_settings:
            cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, val))
            
        conn.commit()


# --- توابع مدیریت کاربران ---
def get_or_create_user(telegram_id: int, username: Optional[str], full_name: Optional[str]) -> Dict[str, Any]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        row = cursor.fetchone()
        if row:
            # بروزرسانی نام و یوزرنیم
            cursor.execute("UPDATE users SET username = ?, full_name = ? WHERE telegram_id = ?", (username, full_name, telegram_id))
            conn.commit()
            return dict(row)
        else:
            cursor.execute("INSERT INTO users (telegram_id, username, full_name) VALUES (?, ?, ?)", (telegram_id, username, full_name))
            conn.commit()
            cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
            return dict(cursor.fetchone())

def get_all_users() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users ORDER BY id DESC")
        return [dict(r) for r in cursor.fetchall()]

def get_user_by_telegram_id(telegram_id: int) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


# --- توابع محصولات ---
def get_products() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products ORDER BY id ASC")
        return [dict(r) for r in cursor.fetchall()]

def get_product_by_code(code: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE code = ?", (code,))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_product_by_id(product_id: int) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def update_product_stock(code: str, is_available: int, stock: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE products SET is_available = ?, stock = ? WHERE code = ?", (is_available, stock, code))
        conn.commit()


# --- توابع سفارشات ---
def create_order(user_id: int, product_id: int, amount: int) -> Dict[str, Any]:
    with get_connection() as conn:
        cursor = conn.cursor()
        # ایجاد کد سفارش یکتا
        timestamp_part = datetime.datetime.now().strftime("%y%m%d%H%M")
        cursor.execute("INSERT INTO orders (order_code, user_id, product_id, amount, status) VALUES (?, ?, ?, ?, 'pending_receipt')",
                       (f"ORD-{timestamp_part}", user_id, product_id, amount))
        order_id = cursor.lastrowid
        order_code = f"ORD-{timestamp_part}-{order_id}"
        cursor.execute("UPDATE orders SET order_code = ? WHERE id = ?", (order_code, order_id))
        conn.commit()
        cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        return dict(cursor.fetchone())

def update_order_receipt(order_id: int, receipt_file_id: str):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE orders 
        SET receipt_file_id = ?, status = 'pending_approval', updated_at = CURRENT_TIMESTAMP 
        WHERE id = ?
        """, (receipt_file_id, order_id))
        conn.commit()

def update_order_status(order_id: int, status: str, delivery_payload: Optional[str] = None, admin_notes: Optional[str] = None):
    with get_connection() as conn:
        cursor = conn.cursor()
        if delivery_payload is not None:
            cursor.execute("""
            UPDATE orders 
            SET status = ?, delivery_payload = ?, admin_notes = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
            """, (status, delivery_payload, admin_notes, order_id))
        else:
            cursor.execute("""
            UPDATE orders 
            SET status = ?, admin_notes = COALESCE(?, admin_notes), updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
            """, (status, admin_notes, order_id))
        conn.commit()

def get_order(order_id: int) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT o.*, p.title_fa as product_title, p.code as product_code, u.telegram_id, u.username, u.full_name
        FROM orders o
        JOIN products p ON o.product_id = p.id
        JOIN users u ON o.user_id = u.id
        WHERE o.id = ?
        """, (order_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_user_completed_orders(user_id: int) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT o.*, p.title_fa as product_title
        FROM orders o
        JOIN products p ON o.product_id = p.id
        WHERE o.user_id = ? AND o.status IN ('completed', 'processing')
        ORDER BY o.id DESC
        """, (user_id,))
        return [dict(r) for r in cursor.fetchall()]

def get_pending_orders() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT o.*, p.title_fa as product_title, u.telegram_id, u.username, u.full_name
        FROM orders o
        JOIN products p ON o.product_id = p.id
        JOIN users u ON o.user_id = u.id
        WHERE o.status IN ('pending_approval', 'processing')
        ORDER BY o.id DESC
        """)
        return [dict(r) for r in cursor.fetchall()]


# --- توابع رزرو ---
def create_reservation(user_id: int, product_id: int) -> Dict[str, Any]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO reservations (user_id, product_id) VALUES (?, ?)", (user_id, product_id))
        res_id = cursor.lastrowid
        conn.commit()
        cursor.execute("""
        SELECT r.*, p.title_fa as product_title, u.telegram_id, u.username, u.full_name
        FROM reservations r
        JOIN products p ON r.product_id = p.id
        JOIN users u ON r.user_id = u.id
        WHERE r.id = ?
        """, (res_id,))
        return dict(cursor.fetchone())

def get_all_reservations() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT r.*, p.title_fa as product_title, u.telegram_id, u.username, u.full_name
        FROM reservations r
        JOIN products p ON r.product_id = p.id
        JOIN users u ON r.user_id = u.id
        ORDER BY r.id DESC
        """)
        return [dict(r) for r in cursor.fetchall()]


def get_all_completed_orders() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT o.*, p.title_fa as product_title, u.telegram_id, u.username, u.full_name
        FROM orders o
        JOIN products p ON o.product_id = p.id
        JOIN users u ON o.user_id = u.id
        WHERE o.status = 'completed'
        ORDER BY o.id DESC
        """)
        return [dict(r) for r in cursor.fetchall()]

# --- توابع تیکت‌ها ---
def create_ticket(user_id: int, text: str, file_id: Optional[str] = None, file_type: Optional[str] = None) -> Dict[str, Any]:
    with get_connection() as conn:
        cursor = conn.cursor()
        ticket_code = f"TCK-{datetime.datetime.now().strftime('%m%d')}-{user_id}"
        cursor.execute("INSERT INTO tickets (ticket_code, user_id, status) VALUES (?, ?, 'open')", (ticket_code, user_id))
        ticket_id = cursor.lastrowid
        # اضافه کردن کد منحصر به فرد با آی‌دی
        full_code = f"TCK-{1000 + ticket_id}"
        cursor.execute("UPDATE tickets SET ticket_code = ? WHERE id = ?", (full_code, ticket_id))
        
        cursor.execute("INSERT INTO ticket_messages (ticket_id, sender, text, file_id, file_type) VALUES (?, 'user', ?, ?, ?)",
                       (ticket_id, text, file_id, file_type))
        conn.commit()
        
        cursor.execute("""
        SELECT t.*, u.telegram_id, u.username, u.full_name
        FROM tickets t
        JOIN users u ON t.user_id = u.id
        WHERE t.id = ?
        """, (ticket_id,))
        return dict(cursor.fetchone())

def add_ticket_message(ticket_id: int, sender: str, text: str, file_id: Optional[str] = None, file_type: Optional[str] = None):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO ticket_messages (ticket_id, sender, text, file_id, file_type) VALUES (?, ?, ?, ?, ?)",
                       (ticket_id, sender, text, file_id, file_type))
        if sender == "admin":
            cursor.execute("UPDATE tickets SET status = 'answered' WHERE id = ?", (ticket_id,))
        else:
            cursor.execute("UPDATE tickets SET status = 'open' WHERE id = ?", (ticket_id,))
        conn.commit()

def close_ticket(ticket_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE tickets SET status = 'closed' WHERE id = ?", (ticket_id,))
        conn.commit()

def get_ticket(ticket_id: int) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT t.*, u.telegram_id, u.username, u.full_name
        FROM tickets t
        JOIN users u ON t.user_id = u.id
        WHERE t.id = ?
        """, (ticket_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_open_tickets() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        # بستن خودکار تیکت‌هایی که بیش از ۳۰ دقیقه از پاسخ ادمین گذشته و کاربر پاسخی نداده است
        cursor.execute("""
        UPDATE tickets 
        SET status = 'closed'
        WHERE status = 'answered' 
        AND id IN (
            SELECT ticket_id FROM ticket_messages 
            WHERE sender = 'admin'
            GROUP BY ticket_id
            HAVING (strftime('%s', 'now') - strftime('%s', MAX(created_at))) > 1800
        )
        """)
        conn.commit()

        # بازگرداندن تیکت‌های نیازمند پاسخ (open یا پاسخ داده شده کمتر از ۳۰ دقیقه)
        cursor.execute("""
        SELECT t.*, u.telegram_id, u.username, u.full_name,
               (SELECT text FROM ticket_messages WHERE ticket_id = t.id ORDER BY id DESC LIMIT 1) as last_message,
               (SELECT sender FROM ticket_messages WHERE ticket_id = t.id ORDER BY id DESC LIMIT 1) as last_sender,
               (SELECT created_at FROM ticket_messages WHERE ticket_id = t.id ORDER BY id DESC LIMIT 1) as last_msg_time
        FROM tickets t
        JOIN users u ON t.user_id = u.id
        WHERE t.status != 'closed'
        ORDER BY (CASE WHEN t.status = 'open' THEN 1 ELSE 2 END), t.id DESC
        """)
        return [dict(r) for r in cursor.fetchall()]

def get_ticket_messages(ticket_id: int) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ticket_messages WHERE ticket_id = ? ORDER BY id ASC", (ticket_id,))
        return [dict(r) for r in cursor.fetchall()]


# --- توابع تنظیمات ---
def get_setting(key: str, default: str = "") -> str:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row[0] if row else default

def set_setting(key: str, value: str):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
        conn.commit()
