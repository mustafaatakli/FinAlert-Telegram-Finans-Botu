# FinAlert Bot Yapılandırması
import os

# Telegram Bot Token (BotFather'dan alınacak)
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'TOKEN KODUNU BURAYA YAPIŞTIRIN!')

# Veritabanı
DATABASE_URL = 'sqlite:///finalert.db'

# Scraping ayarları
REQUEST_TIMEOUT = 10
REQUEST_DELAY = 2  # Saniye cinsinden istekler arası bekleme süresi
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

# Bildirim kontrol aralığı (dakika)
ALERT_CHECK_INTERVAL = 4  # Her 4 dakikada kontrol et (ÇOK GÜVENLİ - BAN RİSKİ %0)

# Zaman bazlı bildirim seçenekleri
TIME_INTERVALS = {
    'her_saat': 3600,
    'her_4_saat': 14400,
    'her_8_saat': 28800,
    'gunluk': 86400
}

# NOT: Tüm URL'ler ve kaynak yönetimi scrapers.py'de yapılır
# Bu dosya sadece referans için - gerçek URL'ler orada

