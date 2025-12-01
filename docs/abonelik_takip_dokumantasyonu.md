# Üye Abonelikleri Takip Sistemi - Detaylı Dokümantasyon

## 1. DATABASE YAPISI (PostgreSQL)

### Ana Tablolar Arasındaki İlişki

```
users (üyeler)
  ├─ id (Primary Key)
  ├─ first_name, last_name
  ├─ email, phone_number
  ├─ is_active (boolean)
  └─ [1:N Relationship] → subscriptions

subscriptions (abonelikler)
  ├─ id (Primary Key)
  ├─ member_user_id (Foreign Key → users.id) ⭐
  ├─ package_id (Foreign Key → service_packages.id)
  ├─ purchase_price (fiyat)
  ├─ start_date, end_date (tarihler)
  ├─ status (active, expired, cancelled, pending, suspended)
  ├─ used_sessions (kullanılan seans)
  └─ [1:N Relationships]
      ├─ payments (ödemeler)
      ├─ bookings (rezervasyonlar)
      ├─ session_check_ins (giriş kontrolleri)
      └─ class_events (ders programları)

service_packages (hizmet paketleri)
  ├─ id (Primary Key)
  ├─ name, price
  ├─ plan_id (bir plana bağlı)
  └─ [1:N Relationship] → subscriptions

payments (ödemeler)
  ├─ id (Primary Key)
  ├─ subscription_id (Foreign Key → subscriptions.id)
  ├─ amount_paid (ödenen miktar)
  ├─ payment_date, payment_method
  ├─ refund_amount, refund_date
  └─ recorded_by_user_id (kaydeden kişi)
```

### SQLAlchemy ORM Relationships

**User Model (backend/models/user.py):**
```python
class User(Base):
    __tablename__ = "users"
    id = Column(String(36), primary_key=True)
    # ...
    subscriptions = relationship("Subscription", back_populates="member")
```

**Subscription Model (backend/models/operation.py):**
```python
class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column(String(36), primary_key=True)
    member_user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    package_id = Column(String(36), ForeignKey("service_packages.id"), nullable=False)
    status = Column(Enum(SubscriptionStatus), nullable=False)
    used_sessions = Column(Integer, default=0)
    # ...
    member = relationship("User", back_populates="subscriptions")
    package = relationship("ServicePackage", back_populates="subscriptions")
    payments = relationship("Payment", back_populates="subscription", cascade="all, delete-orphan")
    class_events = relationship("ClassEvent", back_populates="subscription", cascade="all, delete-orphan")
```

---

## 2. API ENDPOINTS (FastAPI Backend)

### GET /api/v1/sales/subscriptions

**Request:**
```http
GET http://localhost:8000/api/v1/sales/subscriptions?member_id={user_id}
```

**Query Parameters:**
- `member_id` (Optional): Belirli üye için abonelikleri filtrele
- `skip` (Default: 0): Pagination başlama noktası
- `limit` (Default: 100): Kaç kayıt getir

**Backend Kodu (sales.py - Line 125):**
```python
@router.get("/subscriptions", response_model=List[SubscriptionRead])
async def list_subscriptions(
    skip: int = 0, 
    limit: int = 100, 
    member_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Subscription).options(
        selectinload(Subscription.payments),           # ✅ Ödemeler
        selectinload(Subscription.class_events),        # ✅ Ders programları
        selectinload(Subscription.package).selectinload(ServicePackage.category),
        selectinload(Subscription.package).selectinload(ServicePackage.offering),
        selectinload(Subscription.package).selectinload(ServicePackage.plan)
    )
    
    if member_id:
        query = query.where(Subscription.member_user_id == member_id)  # ⭐ FILTER
        
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()
```

**Dönen Response (SubscriptionRead Schema):**
```json
[
  {
    "id": "sub_123",
    "member_user_id": "user_456",
    "package_id": "pkg_789",
    "purchase_price": 500.00,
    "start_date": "2025-01-01T10:00:00",
    "end_date": "2025-01-31T23:59:59",
    "status": "active",
    "used_sessions": 4,
    "package": {
      "id": "pkg_789",
      "name": "Standart Paket",
      "price": 500.00,
      "plan": {
        "id": "plan_101",
        "sessions_granted": 10,
        "access_type": "SESSION_BASED",
        "repeat_weeks": 4
      }
    },
    "payments": [
      {
        "id": "pay_001",
        "amount_paid": 250.00,
        "payment_date": "2025-01-01",
        "payment_method": "KREDI_KARTI"
      }
    ],
    "class_events": [
      {
        "id": "ce_001",
        "days": ["MONDAY", "WEDNESDAY"],
        "hour": 10,
        "minute": 30,
        "instructor_id": "staff_001"
      }
    ]
  }
]
```

---

## 3. DESKTOP UI TARAFINDA TAKIP (profile_tab.py)

### Step-by-Step Akış

```
1. Üye Detay Sayfası Açılırsa
   ↓
2. ProfileTab.__init__() → api_client referansını al
   ↓
3. ProfileTab.setup() → İstatistikler yükle
   ↓
4. API CALL 1: subs = api_client.get(f"/api/v1/sales/subscriptions?member_id={self.member['id']}")
   ↓
   ✅ Backend: Üyenin TÜM aboneliklerini döner (active, expired, cancelled vb.)
   ↓
5. API CALL 2: checkins = api_client.get(f"/api/v1/checkin/history?member_id={self.member['id']}")
   ↓
   ✅ Backend: Üyenin giriş geçmişini döner
   ↓
6. HESAPLAMALAR:
   - total_debt = Tüm abonelikler toplam fiyat - toplam ödenen
   - active_packages_count = status=='active' olan abonelik sayısı
   - last_visit = En son giriş tarihi
   ↓
7. GÖSTERIM:
   - Stats Cards (üst satır): Borç, Aktif Paketler, Son Ziyaret, Üyelik Durumu
   - Left Panel: Aktif Paketler Detayı
   - Right Panel: Son Hareketler
```

### Kod Örneği (profile_tab.py - Line 22-50)

```python
def setup(self):
    # Üyenin aboneliklerini getir
    subs = self.api_client.get(f"/api/v1/sales/subscriptions?member_id={self.member['id']}")
    
    # BORÇ HESAPLA
    total_debt = 0.0
    for s in subs:
        if s.get('status') == 'cancelled': 
            continue  # İptal edilenler hariç
        
        price = float(s.get('purchase_price', 0))                          # Abonelik fiyatı
        paid = sum(float(p.get('amount_paid', 0)) for p in s.get('payments', []))  # Ödenen toplam
        remaining = price - paid                                           # Kalan borç
        if remaining > 0:
            total_debt += remaining
    
    # AKTİF PAKET SAYISI
    active_packages_count = sum(1 for s in subs if s.get('status') == 'active')
    
    # İSTATİSTİK KARTLARI
    self.create_stat_card(stats_frame, "Toplam Borç", f"{total_debt:,.2f} TL", "💰", 
                         "#E04F5F" if total_debt > 0 else "#2CC985", 0)
    self.create_stat_card(stats_frame, "Aktif Paketler", str(active_packages_count), "📦", 
                         "#3B8ED0", 1)
```

### Aktif Paketler Paneli (Line 88-103)

```python
# Sadece 'active' durumdaki abonelikleri göster
left_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
ctk.CTkLabel(left_frame, text="📦 Aktif Paketler", font=("Roboto", 16, "bold")).pack()

if subs:
    active_subs = [s for s in subs if s.get('status') == 'active']  # ⭐ FILTER
    for sub in active_subs:
        self.create_profile_package_card(packages_scroll, sub)
```

### Paket Kartı Detayı (Line 109-143)

Her abonelik için gösterilen bilgiler:

```python
def create_profile_package_card(self, parent, sub):
    pkg_name = sub.get('package', {}).get('name', 'Paket')          # Paket adı
    end_date = sub.get('end_date', '')[:10]                          # Bitiş tarihi
    access_type = sub.get('package', {}).get('plan', {}).get('access_type')  # Paket tipi
    used = sub.get('used_sessions', 0)                               # Kullanılan seans
    limit = sub.get('package', {}).get('plan', {}).get('sessions_granted', 0)  # Seans limiti
    
    # KART İÇERİĞİ:
    # 📦 Paket Adı
    # Bitiş: YYYY-MM-DD
    # 🎯 5 ders kaldı / ♾️ Sınırsız / ❌ 0 ders kaldı
```

---

## 4. VERİ AKIŞI ÖZET TABLO

| Seviye | Bileşen | Sorumuluk | Veriler |
|--------|---------|-----------|---------|
| **Database** | PostgreSQL | Subscription, Payment, ClassEvent saklama | status, used_sessions, payments |
| **ORM** | SQLAlchemy | Relationships tanımlama | member.subscriptions → List[Subscription] |
| **API** | FastAPI (sales.py) | Filtreleme + Eager Loading | GET ?member_id= → SubscriptionRead[] |
| **Desktop UI** | ApiClient | HTTP İsteği yapma | api_client.get("/api/v1/sales/...") |
| **Desktop UI** | ProfileTab | Gösterimi hazırlama | İstatistikler + Kartlar |
| **Desktop UI** | Diğer Tabs | Abonelik yönetimi | Oluştur, Sil, Güncelle |

---

## 5. SORGU ÖRNEKLERI

### Python ile API'yi Kullanma

```python
# 1. Belirli üyenin tüm aboneliklerini getir
subscriptions = api_client.get("/api/v1/sales/subscriptions?member_id=user_123")

# 2. Üyenin aktif paketlerini filtrele
active_subs = [s for s in subscriptions if s.get('status') == 'active']

# 3. Toplam borç hesapla
total_debt = 0.0
for sub in subscriptions:
    if sub.get('status') != 'cancelled':
        price = float(sub.get('purchase_price', 0))
        paid = sum(float(p.get('amount_paid', 0)) for p in sub.get('payments', []))
        total_debt += (price - paid)

# 4. Belirli bir paket için ödemeler
payments = subscriptions[0].get('payments', [])
total_paid = sum(float(p.get('amount_paid', 0)) for p in payments)
```

### cURL ile API'yi Test Etme

```bash
# Üye 'user_456' için abonelikleri getir
curl -X GET "http://localhost:8000/api/v1/sales/subscriptions?member_id=user_456" \
     -H "Authorization: Bearer {TOKEN}" \
     -H "Content-Type: application/json"

# Sonuç: JSON array of SubscriptionRead objects
```

---

## 6. İLERİ ÖZELLIKLER

### Cascade Delete (Abonelik Silindiğinde)

```python
# Subscription silinirse, ilişkili veriler de silinir:
class Subscription(Base):
    # ...
    payments = relationship("Payment", back_populates="subscription", cascade="all, delete-orphan")
    class_events = relationship("ClassEvent", back_populates="subscription", cascade="all, delete-orphan")
```

**Sonuç:** 1 abonelik silinmesi → 10+ ödeme + 5 ders programı otomatik silinir

### Subscription Status Türleri

```python
class SubscriptionStatus(PyEnum):
    active = "active"           # Aktif, geçerli
    expired = "expired"         # Süresi dolmuş
    cancelled = "cancelled"     # İptal edilmiş
    pending = "pending"         # Beklemede
    suspended = "suspended"     # Askıya alınmış
```

### Ödeme İzleme

Her ödeme aboneliğe bağlıdır:

```json
{
  "subscription": {
    "id": "sub_123",
    "status": "active",
    "purchase_price": 500.00,
    "payments": [
      { "amount_paid": 250.00, "date": "2025-01-01" },
      { "amount_paid": 250.00, "date": "2025-01-15" }
    ],
    "remaining_debt": 0.00
  }
}
```

---

## 7. TAKIP İÇİN KONTROL LİSTESİ

Üyelerin aboneliklerini izlemek için:

- [ ] Profile Tab açıldığında: `GET /api/v1/sales/subscriptions?member_id=X`
- [ ] Stats gösteriliyor: Borç, Aktif Paketler, Son Ziyaret
- [ ] Aktif Paketler panelinde: Detaylar + Kalan Seans gösteriliyor
- [ ] Status güncellemesi: Abonelik iptal edildiyse "Pasif" gösterilir
- [ ] Ödeme detayı: Her aboneliğin ödeme bilgileri erişilebilir
- [ ] ClassEvent detayı: Eğer plana ders programı bağlıysa gösterilir

---

## 8. DEBUGGING TIPLERI

### Abonelik Gözükmüyor
```python
# Kontrol: Database'de member_user_id doğru mu?
SELECT * FROM subscriptions WHERE member_user_id = 'user_123';

# Kontrol: API'den döner mi?
curl -X GET "http://localhost:8000/api/v1/sales/subscriptions?member_id=user_123"

# Kontrol: Desktop'ta API call yapılıyor mu?
print(subs)  # Desktop code içinde debug
```

### Ödeme Bilgisi Gözükmüyor
```python
# Kontrol: selectinload kullanılıyor mu?
selectinload(Subscription.payments)  # ✅ Gerekli

# Kontrol: Response'da payments field var mı?
# SubscriptionRead schema'da payments field tanımlı olmalı
```

### Borç Hesabı Yanlış
```python
# Kontrol: Cancelled abonelikler hariç mı?
if s.get('status') == 'cancelled': continue

# Kontrol: Tüm ödemeler toplandı mı?
paid = sum(float(p.get('amount_paid', 0)) for p in s.get('payments', []))
```
