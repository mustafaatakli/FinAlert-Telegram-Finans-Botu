[🇹🇷 Türkçe](#-finalert--telegram-finans-botu) | [🇬🇧 English](#-finalert--telegram-finance-bot)

---

# 🤖 FinAlert – Telegram Finans Botu

![FinAlert Logo/Bannerı (Placeholder)](https://github.com/mustafaatakli/FinAlert-Telegram-Finans-Botu/blob/main/finalertimg/finalert.png)
🤖 **Telegram Botu Canlı Deneyin:** [@MyFinAlertBot](https://t.me/MyFinAlertBot) 

**FinAlert**, anlık piyasa verilerinden seviye bazlı uyarı sistemlerine, zamanlanmış raporlardan detaylı Portföy Kâr/Zarar takibine kadar tüm finansal ihtiyaçlarınızı tek bir Telegram botunda birleştiren kapsamlı bir çözümdür. Tüm bu işlevleri sunarken, gücünü Python programlama dilinden ve güncel piyasa bilgilerini sağlamak için kullanılan Web Scraping (Veri Kazıma) yöntemlerinden alır. Bu teknik altyapı sayesinde FinAlert, kullanıcılarına hızlı, güvenilir ve eyleme geçirilebilir finansal veriler sunarak takip süreçlerini kolaylaştırır.

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
   git clone https://github.com/kullaniciadi/FinAlert-Telegram-Finans-Botu.git
   cd FinAlert-Telegram-Finans-Botu
   ```


2. Gereksinimleri yükleyin:
   ```
   pip install -r requirements.txt
   ```


3. `telegram_bot.py` dosyasında Telegram Bot Token'ınızı ayarlayın:
   ```python
   TOKEN = "BOTFATHER'DAN_ALDIĞINIZ_TOKENi_BURAYA_EKLEYİN!"
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

(```bash
Kullanıcı: /portfoy ekle GramAltın 50 5800)

Bot:
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

### Proje yakın zamanda 2. versiyonu olan FinAlert Web - Finans Takip Sistemi isimli , kullanıcılara **anlık piyasa verileri**, **günlük finans haberleri**, **e-posta bildirimleri** ve **portföy kar/zarar takibi** sunan kapsamlı bir web uygulama olarak hizmet verecektir.

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

---

---

---

# 🤖 FinAlert – Telegram Finance Bot

![FinAlert Logo/Banner (Placeholder)](https://github.com/mustafaatakli/FinAlert-Telegram-Finans-Botu/blob/main/finalertimg/finalert.png)
🤖 **Try the Telegram Bot Live:** [@MyFinAlertBot](https://t.me/MyFinAlertBot)

**FinAlert** is a comprehensive solution that combines all your financial needs in one Telegram bot, from real-time market data to level-based alert systems, scheduled reports to detailed Portfolio Profit/Loss tracking. While offering all these functions, it derives its power from the Python programming language and Web Scraping methods used to provide up-to-date market information. Thanks to this technical infrastructure, FinAlert facilitates tracking processes by providing users with fast, reliable, and actionable financial data.

---

## 📁 Project Structure:

```
FinAlert/
├── alert_manager.py      -> Alert management
├── bot.py                -> Main bot file
├── config.py             -> Configuration settings
├── database.py           -> Database models
├── finalert.db           -> SQLite database
├── portfolio_manager.py  -> Portfolio management
├── requirements.txt      -> Python packages
├── scrapers.py           -> Data scraping functions
└── README.md             -> Documentation
```
---

## ✨ Key Features

| Module | Description |
| :--- | :--- |
| 💸 **Real-Time Market Data** | Real-time **Currency** (USD, EUR, GBP), **Gold** (Gram, Quarter, Ounce) and **Stock** (BIST 100, selected stocks) prices. |
| 🔔 **Level-Based Alerts** | Get instant automatic notifications when the price you set is reached (rise above/fall below). (E.g., "Notify me when USD reaches 42 TRY") |
| ⏰ **Time-Based Reports** | Get automatic and up-to-date market reports daily, hourly, or at intervals you specify. |
| 💼 **Portfolio Tracking** | Track the instant profit/loss status and percentage of your investment by entering purchase price and quantity. |
| 🌐 **Multiple Data Sources** | Multiple (4-5) backup sources are used for each module to ensure no interruption in data flow. |

---

## 🔧 Installation (4 Steps)

What you need to run the bot immediately:

1. Clone the repository:
   ```
   git clone https://github.com/kullaniciadi/FinAlert-Telegram-Finans-Botu.git
   cd FinAlert-Telegram-Finans-Botu
   ```


2. Install requirements:
   ```
   pip install -r requirements.txt
   ```


3. Set your Telegram Bot Token in the `telegram_bot.py` file:
   ```python
   TOKEN = "ADD_YOUR_TOKEN_FROM_BOTFATHER_HERE!"
   ```


4. Run the bot:
   ```
   python bot.py
   ```
🎉 Your bot is now running! You can test it using the /start command on Telegram.

---

## ⏰ Time-Based Notification Commands

The "/zaman" command sets up time-based notifications.
**Options:**
- Every hour
- Every 4 hours
- Every 8 hours
- Daily

**Asset Types:**
- Currency
- Gold
- Stock
- All

---

## 🛠️ Detailed Installation and Dependencies

- **Python 3.8+**
- `python-telegram-bot`
- `beautifulsoup4`, `requests`, `lxml` *(Web Scraping)*
- `APScheduler` *(For scheduled tasks)*
- `sqlalchemy` *(For database operations)*
- `yfinance` *(Yahoo Finance API)*

---

## 🌐 Data Sources

FinAlert uses multiple sources for data reliability and automatically switches to backup when one source fails.
The bot retrieves data from predefined websites (Web Scraping) or through specified APIs in order.
*Websites used for "testing" purposes in the project:

| 🏷️ **Asset** | 🥇 **Primary Source** | 🔁 **Backup Sources** | ⏱️ **Update Frequency** |
|----------------|--------------------------|--------------------------|-----------------------------|
| 💵 **Currency** | BigPara (HTML) | ExchangeRate API, TCMB, Doviz.com | Real-Time |
| 🥇 **Gold** | Mynet Finance (HTML) | BigPara, TRT Finance, Genelpara API | Every 1-2 Minutes |
| 📈 **Stock** | Yahoo Finance (API) | Genelpara API, BigPara, Foreks | Every 15 Minutes |

---

## 💬 Commands and Usage Examples

| 💻 **Command** | 🧩 **Description** | ⚙️ **Example Usage** |
|--------------|----------------|------------------------|
| `/start` | Welcome message and main menu | - |
| `/doviz` | Query real-time currency rates | `/doviz` |
| `/altin` | Query real-time gold prices | `/altin` |
| `/borsa` | Query stock market and stock data | `/borsa` |
| `/uyari` | Set level-based price alert | `/uyari USD 42.00` |
| `/zaman` | Set or manage automatic timed reports | `/zaman saatlik doviz` |
| `/portfoy` | Manage portfolio profit/loss tracking | `/portfoy ekle USD 100 41.50` |

---

## 💼 Example: Portfolio Tracking

User interaction and bot response:

(```bash
User: /portfoy ekle GramAltın 50 5800)

Bot:
- ✅ Added to your portfolio!
- 📦 Gram Gold: 50 units
- 💰 Purchase: ₺5,800.00 | Current: ₺5,782.43
- 📉 Profit/Loss: ₺-878.50 (%-3.03)


---

## ⚠️ Important Legal Notice

**The FinAlert bot** has been developed for **informational** and **demo purposes only**.
The data sources used and mentioned in the bot (*BigPara, Mynet Finance, Yahoo Finance*, etc.) are shown as examples and the use of these sources **does not carry any commercial purpose**.
Data was used only for **testing, educational, and development purposes**.

All data provided by the bot is the output of a project developed by a software developer and is **not investment advice in any way**.
It does not constitute a basis for commercial or investment decisions.
You should make your investment decisions based on your own research, risk analysis, and consultation with authorized financial experts.

> **FinAlert and its developer** cannot be held **responsible** for direct or indirect damages arising from the use of this data.

---

## 🔗 Data Source Note

Various news and finance websites' **sample data** were used during the development and testing phase of this bot.
All results and values shown by the bot are entirely based on this sample data.

The **data source link sections** in the code are generally **left blank** or defined as **link (tag)**.
Developers and users who will use the project for their own purposes can:

- Update these link sections with **their own reliable and legal data sources**,
- **Customize and expand** the project.

---

### The project will soon serve as a comprehensive web application called FinAlert Web - Finance Tracking System, the 2nd version, offering users **real-time market data**, **daily finance news**, **email notifications** and **portfolio profit/loss tracking**.

---

## 🖼️ Sample Working Screenshots

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
