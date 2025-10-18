# 🤖 FinAlert – Telegram Finans Botu

![FinAlert Logo/Bannerı (Placeholder)](https://github.com/mustafaatakli/FinAlert-Telegram-Finans-Botu/blob/main/finalertimg/finalert.png)

**FinAlert**, anlık piyasa verilerinden seviye bazlı uyarı sistemlerine, zamanlanmış raporlardan detaylı **Portföy Kâr/Zarar** takibine kadar tüm finansal ihtiyaçlarınızı tek bir Telegram botunda birleştiren kapsamlı bir çözümdür.

---

## 📁 Proje yapısı:

```
FinAlert/
├── alert_manager.py      -> Uyarı yönetimi
├── bot.py                -> Ana bot dosyası
├── config.py             -> Yapılandırma ayarları
├── database.py           -> Veritabanı modelleri
├── finalert.db           -> SQLite veritabanı
├── portfolio_manager.py  -> Portföy yönetimi
├── requirements.txt      -> Python paketleri
├── scrapers.py           -> Veri çekme fonksiyonları
└── README.md             -> Dokümantasyon
```
---

## ✨ Temel Özellikler

| Modül | Açıklama |
| :--- | :--- |
| 💸 **Anlık Piyasa Verileri** | Gerçek zamanlı **Döviz** (USD, EUR, GBP), **Altın** (Gram, Çeyrek, Ons) ve **Borsa** (BIST 100, seçili hisseler) fiyatları. |
| 🔔 **Seviye Bazlı Uyarılar** | Belirlediğiniz fiyata ulaşıldığında (üstüne çıkma/altına düşme) anında otomatik bildirim alın. (Örn: "USD 42 TL olunca haber ver") |
| ⏰ **Zaman Bazlı Raporlar** | Günlük, saatlik veya belirlediğiniz aralıkta otomatik ve güncel piyasa raporları alın. |
| 💼 **Portföy Takibi** | Alış fiyatı ve miktarı girerek yatırımınızın anlık kâr/zarar durumunu ve yüzdesini takip edin. |
| 🌐 **Çoklu Veri Kaynağı** | Veri akışında kesinti olmaması için her modül için birden fazla (4-5 adet) yedek kaynak kullanılır. |

---

## 🔧 Kurulum (4 Adım)

Botu hemen çalıştırmak için gerekenler:

1. Repo'yu klonlayın:
   ```
   git clone https://github.com/kullaniciadi/borsatakip-telegram-bot.git
   cd FinAlert-Telegram-Finans-Botu
   ```


2. Gereksinimleri yükleyin:
   ```
   pip install -r requirements.txt
   ```


3. `telegram_bot.py` dosyasında Telegram Bot Token'ınızı ayarlayın:
   ```python
   TOKEN = "BOTFATHER'DAN_ALDIĞINIZ_TOKENi BURAYA EKLEYİN!"
   ```


4. Bot'u çalıştırın:
   ```
   python bot.py
   ```
🎉 Artık botunuz çalışıyor! Telegram'da /start komutunu kullanarak test edebilirsiniz.

---

## ⏰ Zaman Bazlı Bildirim Komutları

"/zaman" komutu zaman bazlı bildirim kurar.
**Seçenekler:**
- Her saat
- Her 4 saat
- Her 8 saat
- Günlük

**Varlık Tipleri:**
- Döviz
- Altın
- Borsa
- Hepsi

---

## 🛠️ Detaylı Kurulum ve Bağımlılıklar

- **Python 3.8+**
- `python-telegram-bot`
- `beautifulsoup4`, `requests`, `lxml` *(Web Scraping)*
- `APScheduler` *(Zamanlanmış görevler için)*
- `sqlalchemy` *(Veritabanı işlemleri için)*
- `yfinance` *(Yahoo Finance API)*

---

## 🌐 Veri Kaynakları

FinAlert, veri güvenilirliği için birden fazla kaynak kullanır ve bir kaynak başarısız olduğunda otomatik olarak yedeğe geçer.
Bot, sırasıyla önceden tanımlanmış web sitelerinden veri çeker (Web Scraping) veya belirlenmiş API'ler üzerinden bilgi alır.
*Projede "test" amacıyla kullanılan web siteleri:

| 🏷️ **Varlık** | 🥇 **Öncelikli Kaynak** | 🔁 **Yedek Kaynaklar** | ⏱️ **Güncelleme Sıklığı** |
|----------------|--------------------------|--------------------------|-----------------------------|
| 💵 **Döviz** | BigPara (HTML) | ExchangeRate API, TCMB, Doviz.com | Gerçek Zamanlı |
| 🥇 **Altın** | Mynet Finans (HTML) | BigPara, TRT Finans, Genelpara API | 1–2 Dakikada Bir |
| 📈 **Borsa** | Yahoo Finance (API) | Genelpara API, BigPara, Foreks | 15 Dakikada Bir |

---

## 💬 Komutlar ve Kullanım Örnekleri

| 💻 **Komut** | 🧩 **Açıklama** | ⚙️ **Örnek Kullanım** |
|--------------|----------------|------------------------|
| `/start` | Hoş geldin mesajı ve ana menü | - |
| `/doviz` | Anlık döviz kurlarını sorgula | `/doviz` |
| `/altin` | Anlık altın fiyatlarını sorgula | `/altin` |
| `/borsa` | Borsa ve hisse senedi verilerini sorgula | `/borsa` |
| `/uyari` | Seviye bazlı fiyat uyarısı kur | `/uyari USD 42.00` |
| `/zaman` | Otomatik zamanlı rapor kur veya yönet | `/zaman saatlik doviz` |
| `/portfoy` | Portföy kar/zarar takibini yönet | `/portfoy ekle USD 100 41.50` |

---

## 💼 Örnek: Portföy Takibi

Kullanıcının etkileşimi ve botun yanıtı:

- (```bash
Kullanıcı: /portfoy ekle GramAltın 50 5800)

- Bot:
- ✅ Portföyünüze eklendi!
- 📦 Gram Altın: 50 adet
- 💰 Alış: ₺5,800.00 | Güncel: ₺5,782.43
- 📉 Kâr/Zarar: ₺-878.50 (%-3.03)

---

## ⚠️ Önemli Yasal Uyarı

**FinAlert botu**, yalnızca **bilgilendirme** ve **demo** amaçlı geliştirilmiştir.  
Botta kullanılan ve belirtilen veri kaynakları (*BigPara, Mynet Finans, Yahoo Finance* vb.) örnek olarak gösterilmiştir ve kaynakların kullanımı **herhangi bir ticari amaç taşımamaktadır**.
Veriler yalnızca **test, eğitim ve geliştirme amaçlarıyla** kullanılmıştır.

Bot tarafından sağlanan tüm veriler, yazılımcı tarafından geliştirilen bir projenin çıktısı olup, **hiçbir şekilde yatırım tavsiyesi değildir**.  
Ticari veya yatırım kararları için bir dayanak teşkil etmez.  
Yatırım kararlarınızı kendi araştırmanız, risk analiziniz ve yetkili finans uzmanlarına danışarak vermelisiniz.  

> **FinAlert ve geliştiricisi**, bu verilerin kullanımından doğacak doğrudan veya dolaylı zararlardan **sorumlu tutulamaz**.

---

## 🔗 Veri Kaynağı Notu

Bu botun geliştirme ve test aşamasında çeşitli haber ve finans web sitelerinden **örnek veriler** kullanılmıştır.  
Botun gösterdiği tüm sonuçlar ve değerler, tamamen bu örnek verilere dayanmaktadır.

Kod içerisinde yer alan **veri kaynağı bağlantı kısımları**, genellikle **boş bırakılmış** veya **link (etiketiyle)** olarak tanımlanmıştır.  
Projeyi kendi amaçları doğrultusunda kullanacak geliştiriciler ve kullanıcılar:

- Bu link kısımlarını **kendi güvenilir ve yasal veri kaynaklarıyla** güncelleyebilir,  
- Projeyi **özelleştirebilir ve genişletebilir**.

---

## 🖼️ Örnek Çalışma Görüntüleri

<img src="https://github.com/mustafaatakli/FinAlert-Telegram-Finans-Botu/blob/main/finalertimg/Ekran%20g%C3%B6r%C3%BCnt%C3%BCs%C3%BC%202025-10-17%20190703.png" width="auto">

---

<img src="https://github.com/mustafaatakli/FinAlert-Telegram-Finans-Botu/blob/main/finalertimg/Ekran%20g%C3%B6r%C3%BCnt%C3%BCs%C3%BC%202025-10-17%20202303.png" width="auto">

---

<img src="https://github.com/mustafaatakli/FinAlert-Telegram-Finans-Botu/blob/main/finalertimg/Ekran%20g%C3%B6r%C3%BCnt%C3%BCs%C3%BC%202025-10-17%20183853.png" width="auto">

---

<img src="https://github.com/mustafaatakli/FinAlert-Telegram-Finans-Botu/blob/main/finalertimg/Ekran%20g%C3%B6r%C3%BCnt%C3%BCs%C3%BC%202025-10-17%20184014.png" width="auto">

---

<img src="https://github.com/mustafaatakli/FinAlert-Telegram-Finans-Botu/blob/main/finalertimg/Ekran%20g%C3%B6r%C3%BCnt%C3%BCs%C3%BC%202025-10-17%20215218.png" width="auto">

---

<img src="https://github.com/mustafaatakli/FinAlert-Telegram-Finans-Botu/blob/main/finalertimg/Ekran%20g%C3%B6r%C3%BCnt%C3%BCs%C3%BC%202025-10-17%20213448.png" width="auto">

---

<img src="https://github.com/mustafaatakli/FinAlert-Telegram-Finans-Botu/blob/main/finalertimg/Ekran%20g%C3%B6r%C3%BCnt%C3%BCs%C3%BC%202025-10-17%20184109.png" width="auto">

---

<img src="https://github.com/mustafaatakli/FinAlert-Telegram-Finans-Botu/blob/main/finalertimg/Ekran%20g%C3%B6r%C3%BCnt%C3%BCs%C3%BC%202025-10-17%20202148.png" width="auto">

---

<img src="https://github.com/mustafaatakli/FinAlert-Telegram-Finans-Botu/blob/main/finalertimg/Ekran%20g%C3%B6r%C3%BCnt%C3%BCs%C3%BC%202025-10-17%20184149.png" width="auto">

---

<img src="https://github.com/mustafaatakli/FinAlert-Telegram-Finans-Botu/blob/main/finalertimg/Gemini_Generated_Image_mvj55xmvj55xmvj5.png" width="auto">