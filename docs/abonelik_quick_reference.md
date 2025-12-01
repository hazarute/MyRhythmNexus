# Abonelik Takip - Quick Reference

## 📊 DATA FLOW DIAGRAM

```
┌─────────────────────────────────────────────────────────────────────┐
│                        ÜYELIK YÖNETIMI                               │
└─────────────────────────────────────────────────────────────────────┘

1️⃣ ÜYELER (Users)
   ├─ id: user_456
   ├─ name: Ahmet Yılmaz
   ├─ email: ahmet@example.com
   └─ is_active: true
       │
       │ [1:N Relationship]
       ▼
2️⃣ ABONELİKLER (Subscriptions) ⭐ TRACK POINT
   ├─ id: sub_123
   ├─ member_user_id: user_456  ← ÜYEYE BAĞLI
   ├─ purchase_price: 500.00 TL
   ├─ start_date: 2025-01-01
   ├─ end_date: 2025-01-31
   ├─ status: active
   └─ used_sessions: 4/10
       │
       ├─ [1:N] → 3️⃣ ÖDEMELER (Payments)
       │           ├─ pay_001: 250.00 TL (01 Ocak)
       │           └─ pay_002: 250.00 TL (15 Ocak)
       │
       ├─ [1:1] → 4️⃣ HİZMET PAKETİ (ServicePackage)
       │           ├─ name: Standart Paket
       │           ├─ price: 500.00 TL
       │           └─ plan: SESSION_BASED (10 seans)
       │
       └─ [1:N] → 5️⃣ DERS PROGRAMLARI (ClassEvents)
                   ├─ Monday 10:30 (Hoca: Mehmet)
                   └─ Wednesday 10:30 (Hoca: Mehmet)
```

## 🔍 SORGU AKIŞI

```
┌─────────────────────────────────────────────────────────────────┐
│ Desktop: ProfileTab açıldığında                                  │
└─────────────────────────────────────────────────────────────────┘
                          │
                          ▼
        ┌──────────────────────────────────┐
        │ self.api_client.get()            │
        │ "/api/v1/sales/subscriptions"    │
        │ ?member_id=user_456              │
        └──────────────────────────────────┘
                          │
                    🌐 Network
                          │
                          ▼
        ┌──────────────────────────────────┐
        │ Backend: FastAPI Endpoint        │
        │ @router.get("/subscriptions")    │
        │ if member_id: ...where(...)      │ ⭐ FILTER
        └──────────────────────────────────┘
                          │
                          ▼
        ┌──────────────────────────────────┐
        │ SQLAlchemy ORM Query:            │
        │ SELECT s FROM subscriptions s    │
        │ WHERE s.member_user_id = X       │
        │ WITH (payments, package, plan)   │ ✅ Eager Load
        └──────────────────────────────────┘
                          │
                          ▼
        ┌──────────────────────────────────┐
        │ PostgreSQL Database              │
        │ SELECT * FROM subscriptions      │
        │ WHERE member_user_id = X;        │
        └──────────────────────────────────┘
                          │
                          ▼
        ┌──────────────────────────────────┐
        │ Response: SubscriptionRead[]      │
        │ JSON Array with nested objects   │
        └──────────────────────────────────┘
                          │
                    🌐 Network
                          │
                          ▼
        ┌──────────────────────────────────┐
        │ Desktop: ProfileTab.setup()      │
        │ subs = [{ ... }, { ... }, ...]   │
        └──────────────────────────────────┘
                          │
        ┌─────────────────┴─────────────────┐
        │                                   │
        ▼                                   ▼
    Stats Bar               Aktif Paketler Paneli
    ├─ 💰 Borç             ├─ 📦 Paket Adı
    ├─ 📦 Aktif (2)        ├─ Bitiş: 31 Ocak
    ├─ 🏃 Son Ziyaret      └─ 🎯 6 ders kaldı
    └─ ✅ Durumu
```

## 💾 DATABASE SCHEMA

```sql
-- USERS (Üyeler)
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY,
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    email VARCHAR(320) UNIQUE,
    is_active BOOLEAN DEFAULT true
);

-- SUBSCRIPTIONS (Abonelikler) ⭐ MAIN TABLE
CREATE TABLE subscriptions (
    id VARCHAR(36) PRIMARY KEY,
    member_user_id VARCHAR(36) NOT NULL,  ← users.id
    package_id VARCHAR(36) NOT NULL,       ← service_packages.id
    purchase_price DECIMAL(10,2),
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    status VARCHAR(20),  -- active, expired, cancelled
    used_sessions INTEGER DEFAULT 0,
    FOREIGN KEY (member_user_id) REFERENCES users(id),
    FOREIGN KEY (package_id) REFERENCES service_packages(id)
);

-- PAYMENTS (Ödemeler)
CREATE TABLE payments (
    id VARCHAR(36) PRIMARY KEY,
    subscription_id VARCHAR(36) NOT NULL,  ← subscriptions.id
    amount_paid DECIMAL(10,2),
    payment_date TIMESTAMP,
    payment_method VARCHAR(20),
    FOREIGN KEY (subscription_id) REFERENCES subscriptions(id)
        ON DELETE CASCADE  ← Abonelik silinirse ödemeler de silinir
);

-- SERVICE_PACKAGES (Hizmet Paketleri)
CREATE TABLE service_packages (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(160),
    price DECIMAL(10,2),
    plan_id VARCHAR(36),
    FOREIGN KEY (plan_id) REFERENCES plan_definitions(id)
);

-- CLASS_EVENTS (Ders Programları)
CREATE TABLE class_events (
    id VARCHAR(36) PRIMARY KEY,
    subscription_id VARCHAR(36),  ← subscriptions.id
    instructor_id VARCHAR(36),
    days VARCHAR(100),  -- "MONDAY,WEDNESDAY"
    hour INTEGER,
    minute INTEGER,
    FOREIGN KEY (subscription_id) REFERENCES subscriptions(id)
        ON DELETE CASCADE
);

-- INDEX (Performans)
CREATE INDEX idx_subscriptions_member ON subscriptions(member_user_id);
CREATE INDEX idx_payments_subscription ON payments(subscription_id);
CREATE INDEX idx_class_events_subscription ON class_events(subscription_id);
```

## 📝 PYTHON API CALL

```python
# 1️⃣ INITIALIZATION
from desktop.core.api_client import ApiClient

api_client = ApiClient()
member_id = "user_456"

# 2️⃣ GET DATA
subscriptions = api_client.get(
    f"/api/v1/sales/subscriptions?member_id={member_id}"
)

# 3️⃣ STRUCTURE
# subscriptions = [
#     {
#         "id": "sub_123",
#         "purchase_price": "500.00",
#         "status": "active",
#         "used_sessions": 4,
#         "package": {
#             "name": "Standart Paket",
#             "plan": {
#                 "sessions_granted": 10,
#                 "access_type": "SESSION_BASED"
#             }
#         },
#         "payments": [
#             {"amount_paid": "250.00", "payment_date": "2025-01-01"},
#             {"amount_paid": "250.00", "payment_date": "2025-01-15"}
#         ]
#     }
# ]

# 4️⃣ CALCULATIONS
total_debt = 0.0
active_count = 0

for sub in subscriptions:
    # Cancelled abonelikleri atla
    if sub.get('status') == 'cancelled':
        continue
    
    # Aktif olanları say
    if sub.get('status') == 'active':
        active_count += 1
    
    # Borç hesapla
    price = float(sub.get('purchase_price', 0))
    paid = sum(float(p.get('amount_paid', 0)) 
               for p in sub.get('payments', []))
    remaining = price - paid
    
    if remaining > 0:
        total_debt += remaining

print(f"Toplam Borç: {total_debt:.2f} TL")
print(f"Aktif Paketler: {active_count}")
```

## 🎯 TAKIP CHECKLIST

Üyenin aboneliklerini izlemek için kontrol noktaları:

```
┌─────────────────────────────────────────┐
│ SUBSCRIPTION STATUS TRACKING            │
├─────────────────────────────────────────┤

✅ Database'de kayıt var mı?
   SELECT COUNT(*) FROM subscriptions 
   WHERE member_user_id = 'user_456'

✅ API'den geri dönüyor mu?
   curl http://localhost:8000/api/v1/sales/subscriptions?member_id=user_456

✅ Desktop'ta görünüyor mu?
   - Stats Card: Aktif Paketler sayısı
   - Sol Panel: Paket detayları
   - Sağ Panel: Son hareketler

✅ Borç Hesabı doğru mu?
   Fiyat - Toplam Ödenen = Borç

✅ Status Güncelleme çalışıyor mu?
   - active → Yeşil ve gösteriliyor
   - expired → Turuncu uyarısı
   - cancelled → Gizleniyor

✅ Ödeme İzleme:
   - Her ödeme aboneliğe bağlı
   - Cascade delete: Abonelik silinirse ödemeler de silinir
   
✅ Ders Programları:
   - Class Events subscription'a bağlı
   - Abonelik iptal → Dersler otomatik silinir
```

## 🔧 DEBUGGING QUICK TIPS

| Problem | Çözüm |
|---------|-------|
| **Abonelik gözükmüyor** | `SELECT * FROM subscriptions WHERE member_user_id = ?` |
| **Borç yanlış** | `sum(payments.amount_paid)` tüm ödemeler toplandı mı? |
| **Status güncellenmiyor** | Database'de status alanı güncellendi mi? |
| **API 500 hatası** | `selectinload()` eager loading eksik mi? |
| **Performance yavaş** | Kaç abonelik var? Index eksik mi? |
| **Cascade delete çalışmıyor** | `cascade="all, delete-orphan"` tanımlı mı? |

## 📚 İlişkili Dosyalar

```
Backend:
├─ backend/models/operation.py      ← Subscription, Payment, ClassEvent
├─ backend/models/user.py           ← User & subscriptions relationship
├─ backend/api/v1/sales.py          ← GET /api/v1/sales/subscriptions endpoint
└─ backend/schemas/sales.py         ← SubscriptionRead response schema

Desktop:
├─ desktop/ui/views/tabs/profile_tab.py       ← Profil tab & gösterim
├─ desktop/core/api_client.py                 ← HTTP istekleri
└─ desktop/ui/views/member_detail.py          ← Üye detay wrapper

Database:
├─ alembic/versions/                          ← Migration history
└─ Database: subscriptions, payments, service_packages
```
