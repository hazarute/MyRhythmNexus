import asyncio
import sys
import os
from datetime import timedelta

# Proje kök dizinini path'e ekle
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.core.database import SessionLocal
from backend.models.license import License
from backend.services.license import generate_license_key
from backend.core.time_utils import get_turkey_time

async def create_license(client_name: str = "Test Kullanicisi", days: int = 365):
    print("Veritabanına bağlanılıyor...")
    async with SessionLocal() as db:
        key = generate_license_key()
        now = get_turkey_time()
        expires_at = now + timedelta(days=days)
        
        # Varsayılan özellikler (Tüm modüller açık)
        features = {
            "qr_checkin": True,
            "finance": True,
            "reporting": True,
            "member_management": True,
            "sales": True
        }
        
        license_obj = License(
            license_key=key,
            client_name=client_name,
            contact_email="test@myrhythmnexus.com",
            is_active=True,
            expires_at=expires_at,
            features=features,
            hardware_id=None # NULL bırakıyoruz ki ilk giren cihaza kilitlensin
        )
        
        db.add(license_obj)
        await db.commit()
        
        print("\n" + "="*60)
        print("✅ YENİ LİSANS BAŞARIYLA OLUŞTURULDU")
        print("="*60)
        print(f"🔑 Lisans Anahtarı : {key}")
        print(f"👤 Müşteri         : {client_name}")
        print(f"📅 Bitiş Tarihi    : {expires_at.strftime('%d.%m.%Y %H:%M')}")
        print(f"⚙️  Durum           : Aktif (Cihaz kilidi yok, ilk girişte kilitlenecek)")
        print("="*60 + "\n")
        print("👉 Bu anahtarı kopyalayıp Desktop uygulamasındaki kutucuğa yapıştırın.")

if __name__ == "__main__":
    try:
        asyncio.run(create_license())
    except Exception as e:
        print(f"Hata oluştu: {e}")
