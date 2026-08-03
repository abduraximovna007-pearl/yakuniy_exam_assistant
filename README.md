# 📚 Test Bot — Telegram Bot

**Test Bot** — talabalar uchun yaratilgan Telegram boti. Foydalanuvchilar test fayllarini yuklaydi, to'lov qiladi, admin tasdiqlaydi va talabalar online test ishlaydi.

---

## 🚀 Imkoniyatlar

- 👤 **Ro'yxatdan o'tish** — ism, fakultet, guruh kiritish
- 📤 **Test yuklash** — `.docx` yoki `.txt` fayl yuborish + to'lov skrinshoti
- ✅ **Admin tasdiqlash** — admin faylni ko'rib chiqib tasdiqlaydi/rad etadi
- 📝 **Test ishlash** — tasdiqlangan testlardan savollar yechish
- 🏆 **Reyting** — fakultet va guruh bo'yicha eng yaxshi natijalar
- 👤 **Profil** — foydalanuvchining ma'lumotlari va ballari
- 📋 **Xatolar tahlili** — test yakunida noto'g'ri javoblarni ko'rish
- 🖥️ **Admin panel** — FastAPI orqali veb-interfeys

---

## 🛠️ Texnologiyalar

| Texnologiya | Maqsad |
|-------------|--------|
| Python 3.11+ | Asosiy til |
| aiogram 3.x | Telegram Bot Framework |
| SQLAlchemy 2.x | ORM (asinxron) |
| aiosqlite | SQLite asinxron driver |
| FastAPI | Admin veb-panel |
| python-docx | Word fayl o'qish |
| Jinja2 | HTML shablonlar |

---

## 📁 Loyiha Strukturasi

```
withopencode/
│
├── bot.py              # Botni ishga tushirish
├── admin_app.py        # FastAPI admin panel
├── config.py           # Sozlamalar (.env o'qish)
├── database.py         # DB ulanish va sessiya
├── models.py           # SQLAlchemy modellari
├── crud.py             # Database CRUD operatsiyalari
├── keyboards.py        # Telegram klaviaturalar
├── states.py           # FSM holatlari
├── parser.py           # Fayl parser (.docx / .txt)
│
├── handlers/
│   ├── __init__.py
│   ├── start.py        # Start va ro'yxat handlerlari
│   ├── upload.py       # Test yuklash handleri
│   ├── test_take.py    # Test ishlash handleri
│   ├── rating.py       # Reyting va profil
│   └── admin_actions.py# Admin tasdiqlash/rad etish
│
├── templates/
│   └── base.html       # Jinja2 HTML shablon
│
├── uploads/            # Yuklangan fayllar (auto yaratiladi)
├── .env                # Sozlamalar (yaratish kerak!)
├── .env.example        # Sozlamalar namunasi
├── requirements.txt    # Python kutubxonalari
└── README.md           # Shu fayl
```

---

## ⚙️ O'rnatish va Ishga Tushirish

### 1. Repozitoriyani klonlash

```bash
git clone https://github.com/yourusername/withopencode.git
cd withopencode
```

### 2. Virtual muhit yaratish

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Kutubxonalarni o'rnatish

```bash
pip install -r requirements.txt
```

### 4. `.env` faylini sozlash

```bash
# .env.example ni ko'chirib .env yarating
copy .env.example .env   # Windows
cp .env.example .env     # Linux/macOS
```

So'ngra `.env` faylini oching va quyidagilarni to'ldiring:

```env
BOT_TOKEN=your_bot_token_here
ADMIN_ID=123456789
DATABASE_URL=sqlite+aiosqlite:///testbot.db
TEST_PRICE=50000
```

> **BOT_TOKEN** — [@BotFather](https://t.me/BotFather) orqali olinadi  
> **ADMIN_ID** — [@userinfobot](https://t.me/userinfobot) ga `/start` yuborib bilib olinadi

### 5. Botni ishga tushirish

```bash
python bot.py
```

### 6. Admin panelni ishga tushirish (ixtiyoriy)

Alohida terminalda:

```bash
python admin_app.py
```

Admin panel manzili: `http://localhost:8000/admin/dashboard`

---

## 📄 Test Fayl Formati

Bot `.docx` va `.txt` formatlarini qabul qiladi. Savollar quyidagi formatda yozilishi kerak:

```
Savolning matni bu yerga yoziladi

A. Birinchi variant
B. Ikkinchi variant
#C. To'g'ri javob (# belgisi to'g'ri javobni belgilaydi)
D. To'rtinchi variant

===
```

**Qoidalar:**
- Savollar bir-biridan `===` yoki `---` yoki **3 ta bo'sh qator** bilan ajratiladi
- To'g'ri javob oldiga `#` belgisi qo'yiladi (masalan: `#C. To'g'ri javob`)
- Kamida 2 ta variant bo'lishi shart

---

## 🔐 Xavfsizlik

> ⚠️ **DIQQAT:** `.env` faylini hech qachon GitHub yoki boshqa public joyga yuklamang!

`.gitignore` fayliga qo'shish tavsiya etiladi:

```
.env
.venv/
__pycache__/
uploads/
*.db
```

---

## 📡 Admin Panel Endpointlar

| Endpoint | Tavsif |
|----------|--------|
| `GET /admin/dashboard` | Umumiy statistika |
| `GET /admin/tests` | Barcha testlar ro'yxati |
| `GET /admin/users` | Barcha foydalanuvchilar |
| `GET /admin/rating` | Umumiy reyting (top 50) |

> 🔒 **Eslatma:** Admin panel hozir autentifikatsiyasiz. Ishlatishdan oldin HTTP Basic Auth yoki API key himoyasini qo'shish tavsiya etiladi.

---

## 🧪 Ma'lumotlar Bazasi

Bot SQLite ishlatadi — alohida o'rnatish shart emas. DB fayli `testbot.db` nomi bilan avtomatik yaratiladi.

PostgreSQL ga o'tish uchun `.env` da:
```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/testbot_db
```
va `asyncpg` ni o'rnatish:
```bash
pip install asyncpg
```

---

## 🐳 Docker orqali Deploy Qilish (Tavsiya etiladi)

Loyiha to'liq Docker va `docker-compose` tayyor holatga keltirilgan.

### 1. Ishga tushirish buyrug'i:

```bash
docker-compose up -d --build
```

Ushbu buyruq:
- `test_telegram_bot` (Telegram bot) va `test_bot_admin` (Admin panel) konteynerlarini avtomatik yig'adi va fonda ishga tushiradi.
- `uploads/` va `testbot.db` fayllarini saqlab qoladi (server o'chib yonsa ham ma'lumot yoqolmaydi).

### 2. Holatni va loglarni ko'rish:

```bash
docker-compose ps
docker-compose logs -f
```

### 3. To'xtatish:

```bash
docker-compose down
```

---

## 📞 Murojaat

Savollar uchun: Telegram — [@yourusername](https://t.me/yourusername)

