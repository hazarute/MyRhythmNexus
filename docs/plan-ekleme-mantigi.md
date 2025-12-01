# Plan Ekleme Mantığı

Bu doküman, masaüstü uygulamasındaki "Yeni Plan Ekle" diyaloğunun iş akışını ve backend ile nasıl iletişime geçtiğini özetler.

## Form Alanları ve Beklenen Davranış
- **Plan Adı**: Kullanıcı tarafından sağlanması zorunlu olup boş bırakılırsa uyarı gösterilir.
- **Geçerlilik Süresi**: Sabit seçenekler (Aylık, 3 Aylık, 6 Aylık, Yıllık, Haftalık ve Özel Tarih) sunulur. Bu alan `CTkComboBox` aracılığıyla seçilir ve tüm seçimlerde `cycle_period` alanı backend için Türkçe etiketlerden İngilizce karşılığa çevrilir.
- **Seans Sayısı**: 0 veya boş bırakılırsa sınırsız olarak kabul edilir. Sayı girildiğinde pozitif olması beklenir, negatif veya geçersiz değerlerde uyarı verilir.
- **Tekrarlayan Haftalar**: Başlangıçta pasif (devre dışı) gelir. Sadece "📆 Haftalık (7 gün)" seçildiğinde alan etkinleşir. Diğer döngüler seçildiğinde alan `1` olarak resetlenir ve kullanıcı düzenleyemez. Bu alan sadece haftalık döngü için geçerlidir ve haftalık planlarda `repeat_weeks` değerini belirtir.
- **Açıklama**: Opsiyonel metin alanıdır.

## Döngü Değişimine Tepki
`CTkComboBox` içindeki seçim değiştiğinde `_on_cycle_change` fonksiyonu tetiklenir. Haftalık döngü seçilmişse "Tekrarlayan Haftalar" alanı aktif olur, aksi hâlde alan devre dışı bırakılır ve değeri `1` olarak sıfırlanır.

## Kaydetme İşlemi
1. Formdaki değerler toplanır ve doğrulanır.
2. Seans sayısı pozitif olarak girilmişse `SESSION_BASED`, aksi hâlde `TIME_BASED` erişim tipi atanır.
3. Haftalık planlarda kullanıcı girmişse `repeat_weeks` alanına girilen sayı kullanılır; alan boşsa varsayılan `1` kalır.
4. Tüm alanlar `name`, `access_type`, `sessions_granted`, `cycle_period`, `repeat_weeks`, `description`, `is_active` şeklinde bir JSON nesnesinde toplanır.
5. Bu payload `/api/v1/services/plans` endpoint'ine POST edilir.
6. Başarılıysa bilgi mesajı gösterilir, diyalog kapanır ve liste güncelleme callback'i çağrılır; hata durumunda hata mesajı ekrana gelir.

## Örnek Senaryo
- `Seans Sayısı`: 8 (paket toplam 8 seans hakkı verir).
- `Geçerlilik Süresi`: 📆 Haftalık (7 gün).
- `Tekrarlayan Haftalar`: 4 yazılırsa plan 4 hafta boyunca geçerli olur; `repeat_weeks=4` backend’e giderken toplam 8 seans hakkı haftalık 4 tekrar boyunca kullanılabilir.

Bu `repeat_weeks` değeri, satış ekranındaki tahmini bitiş tarihini hesaplayan `calculate_end_date` fonksiyonuna da aktarılır; böylece "Haftalık" seçilmiş ama 4 haftalık plan yaratılmışsa bitiş 4 hafta sonraya ayarlanır.

Diğer döngülerde (örneğin Aylık) `Tekrarlayan Haftalar` alanı pasif olduğu için sadece varsayılan `1` değeri gönderilir ve toplam seans sayısı sadece paketin tüm hakkını belirler.

## Backend Etkileşimi
- `repeat_weeks` alanı artık Plan Definition modelinde yer alır ve Alembic migrasyonu ile veritabanına eklendi.
- Backend tarafında bu alan, haftalık döngüsü için plan tanımına haftalık tekrar sayısını belirtmek amacıyla kullanılabilir.

Bu mantık sayesinde yalnızca haftalık döngülerde tekrarlayan hafta sayısı girilebilir, diğer döngüler için alan korunur ve API payload'ı her zaman tutarlı kalır.