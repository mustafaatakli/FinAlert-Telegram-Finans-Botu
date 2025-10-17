import asyncio
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database import get_db, User, Alert, TimeNotification
from scrapers import get_doviz_data, get_altin_data, get_borsa_data
import logging

logger = logging.getLogger(__name__)


def format_price(price):
    """Fiyatı Türk Lirası formatında göster"""
    return f"{price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ===== SEVİYE BAZLI UYARILAR =====
async def check_price_alerts(application):
    """
    Aktif uyarıları kontrol et ve hedef fiyata ulaşıldığında bildir
    """
    db = get_db()
    
    try:
        # Aktif uyarıları al
        active_alerts = db.query(Alert).filter(Alert.is_active == True).all()
        
        if not active_alerts:
            db.close()
            return
        
        # Veri kaynaklarını çek
        doviz_data = get_doviz_data()
        altin_data = get_altin_data()
        borsa_data = get_borsa_data()
        
        # Kaynak bilgilerini al
        doviz_kaynak = doviz_data.get('_kaynak', 'Bilinmeyen')
        altin_kaynak = altin_data.get('_kaynak', 'Bilinmeyen')
        borsa_kaynak = borsa_data.get('_kaynak', 'Bilinmeyen')
        
        for alert in active_alerts:
            current_price = None
            kaynak = 'Bilinmeyen'
            
            # İlgili varlığın mevcut fiyatını al
            if alert.asset_type == 'doviz':
                if alert.asset_name in doviz_data:
                    current_price = doviz_data[alert.asset_name]['satis']
                    kaynak = doviz_kaynak
            
            elif alert.asset_type == 'altin':
                if alert.asset_name in altin_data:
                    current_price = altin_data[alert.asset_name]['satis']
                    kaynak = altin_kaynak
            
            elif alert.asset_type == 'hisse':
                if alert.asset_name in borsa_data:
                    current_price = borsa_data[alert.asset_name]['deger']
                    kaynak = borsa_kaynak
            
            # Fiyat kontrolü yap
            if current_price is not None:
                triggered = False
                
                if alert.condition == 'ustu' and current_price >= alert.target_price:
                    triggered = True
                elif alert.condition == 'alti' and current_price <= alert.target_price:
                    triggered = True
                
                # Uyarı tetiklenirse
                if triggered:
                    # Kullanıcıya bildirim gönder
                    user = db.query(User).filter(User.id == alert.user_id).first()
                    
                    if user:
                        asset_emoji = {
                            'doviz': '💱',
                            'altin': '🏆',
                            'hisse': '📈'
                        }
                        
                        condition_text = 'üstüne çıktı' if alert.condition == 'ustu' else 'altına düştü'
                        
                        message = f"""
🔔 *Fiyat Uyarısı!*

{asset_emoji.get(alert.asset_type, '💰')} *{alert.asset_name}*

Hedef Fiyat: ₺{format_price(alert.target_price)}
Güncel Fiyat: ₺{format_price(current_price)}

{alert.asset_name} hedef fiyatın {condition_text}! 

📡 Kaynak: {kaynak}
🕐 {datetime.now().strftime('%d.%m.%Y %H:%M')}
"""
                        
                        try:
                            await application.bot.send_message(
                                chat_id=user.telegram_id,
                                text=message,
                                parse_mode='Markdown'
                            )
                            
                            # Uyarıyı devre dışı bırak
                            alert.is_active = False
                            alert.triggered_at = datetime.now()
                            db.commit()
                            
                            logger.info(f"✅ Uyarı gönderildi: {user.telegram_id} - {alert.asset_name}")
                        
                        except Exception as e:
                            logger.error(f"❌ Bildirim gönderme hatası: {e}")
    
    except Exception as e:
        logger.error(f"❌ Uyarı kontrolü hatası: {e}")
    
    finally:
        db.close()


# ===== ZAMAN BAZLI BİLDİRİMLER =====
async def check_time_notifications(application):
    """
    Periyodik bildirimleri kontrol et ve zamanı gelenleri gönder
    """
    db = get_db()
    
    try:
        # Aktif bildirimleri al
        active_notifications = db.query(TimeNotification).filter(
            TimeNotification.is_active == True
        ).all()
        
        if not active_notifications:
            db.close()
            return
        
        now = datetime.now()
        
        for notification in active_notifications:
            # Son gönderim zamanını kontrol et
            should_send = False
            
            if notification.last_sent is None:
                should_send = True
            else:
                # Interval'e göre kontrol
                time_diff = (now - notification.last_sent).total_seconds()
                
                if notification.interval == 'her_saat' and time_diff >= 3600:
                    should_send = True
                elif notification.interval == 'her_4_saat' and time_diff >= 14400:
                    should_send = True
                elif notification.interval == 'her_8_saat' and time_diff >= 28800:
                    should_send = True
                elif notification.interval == 'gunluk' and time_diff >= 86400:
                    should_send = True
            
            if should_send:
                # Kullanıcıya rapor gönder
                user = db.query(User).filter(User.id == notification.user_id).first()
                
                if user:
                    # Varlık türlerine göre rapor oluştur
                    asset_types = notification.asset_types.split(',')
                    report = generate_report(asset_types)
                    
                    try:
                        await application.bot.send_message(
                            chat_id=user.telegram_id,
                            text=report,
                            parse_mode='Markdown'
                        )
                        
                        # Son gönderim zamanını güncelle
                        notification.last_sent = now
                        db.commit()
                        
                        logger.info(f"✅ Periyodik rapor gönderildi: {user.telegram_id}")
                    
                    except Exception as e:
                        logger.error(f"❌ Rapor gönderme hatası: {e}")
    
    except Exception as e:
        logger.error(f"❌ Bildirim kontrolü hatası: {e}")
    
    finally:
        db.close()


def generate_report(asset_types):
    """
    Belirtilen varlık türleri için rapor oluştur
    """
    report = f"📊 *Piyasa Raporu*\n\n🕐 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
    
    kaynaklar = []
    
    if 'doviz' in asset_types:
        doviz_data = get_doviz_data()
        doviz_kaynak = doviz_data.get('_kaynak', 'Bilinmeyen')
        kaynaklar.append(f"Döviz: {doviz_kaynak}")
        
        report += "💱 *Döviz Kurları*\n"
        
        # Döviz isimleri Türkçe
        currency_names = {
            'USD': 'Dolar',
            'EUR': 'Euro',
            'GBP': 'Sterlin'
        }
        
        for currency, data in doviz_data.items():
            if currency == '_kaynak':
                continue
            currency_name = currency_names.get(currency, currency)
            report += f"{currency_name}: ₺{format_price(data['satis'])}\n"
        
        report += "\n"
    
    if 'altin' in asset_types:
        altin_data = get_altin_data()
        altin_kaynak = altin_data.get('_kaynak', 'Bilinmeyen')
        kaynaklar.append(f"Altın: {altin_kaynak}")
        
        report += "🏆 *Altın Fiyatları*\n"
        
        altin_names = {
            'gram': 'Gram',
            'ceyrek': 'Çeyrek',
            'tam': 'Tam'
        }
        
        for key, name in altin_names.items():
            if key in altin_data:
                report += f"{name}: ₺{format_price(altin_data[key]['satis'])}\n"
        
        report += "\n"
    
    if 'hisse' in asset_types:
        borsa_data = get_borsa_data()
        borsa_kaynak = borsa_data.get('_kaynak', 'Bilinmeyen')
        kaynaklar.append(f"Borsa: {borsa_kaynak}")
        
        report += "📈 *Borsa İstanbul*\n"
        
        for symbol, data in list(borsa_data.items())[:5]:  # İlk 5 veriyi göster
            if symbol == '_kaynak':
                continue
            degisim = data['degisim_yuzde']
            emoji = "📈" if degisim > 0 else "📉"
            report += f"{symbol}: ₺{format_price(data['deger'])} {emoji}%{degisim:.2f}\n"
        
        report += "\n"
    
    # Kaynakları ekle
    if kaynaklar:
        report += "📡 *Kaynaklar:*\n"
        for kaynak in kaynaklar:
            report += f"• {kaynak}\n"
    
    return report


# ===== SCHEDULER BAŞLATMA =====
def start_alert_checker(application):
    """Uyarı kontrolcüsünü başlat"""
    scheduler = AsyncIOScheduler()
    
    # Her 2 dakikada bir kontrol et (GÜVENLİ ve ETKİLİ)
    # API'lerin güncelleme sıklığına uygun
    # Ban riski minimal
    scheduler.add_job(
        check_price_alerts,
        'interval',
        minutes=2,  # ← 2 dakika (720 istek/gün)
        args=[application],
        id='alert_checker'
    )
    
    scheduler.start()
    logger.info("✅ Uyarı kontrolcüsü başlatıldı (her 2 dakika - güvenli mod)")


def start_time_notification_checker(application):
    """Zaman bazlı bildirim kontrolcüsünü başlat"""
    scheduler = AsyncIOScheduler()
    
    # Her 2 dakikada bir kontrol et (DAHA SIK)
    scheduler.add_job(
        check_time_notifications,
        'interval',
        minutes=2,  # ← 2 dakika
        args=[application],
        id='notification_checker'
    )
    
    scheduler.start()
    logger.info("✅ Bildirim kontrolcüsü başlatıldı (her 2 dakika)")

