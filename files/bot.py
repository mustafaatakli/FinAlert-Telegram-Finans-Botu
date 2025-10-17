# FinAlert - Telegram Finans Botu
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler, 
    CallbackQueryHandler, 
    MessageHandler, 
    filters, 
    ContextTypes,
    ConversationHandler
)
from datetime import datetime
import config
from database import (
    init_db, get_db, User, Portfolio, Alert, TimeNotification
)
from scrapers import get_doviz_data, get_altin_data, get_borsa_data
from alert_manager import start_alert_checker, start_time_notification_checker
from portfolio_manager import (
    add_portfolio_item, calculate_portfolio_profit_loss, 
    delete_portfolio_item, format_portfolio_report
)

# Logging ayarları
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
(WAITING_PORTFOLIO_TYPE, WAITING_PORTFOLIO_ASSET, WAITING_PORTFOLIO_AMOUNT, 
 WAITING_PORTFOLIO_PRICE, WAITING_ALERT_TYPE, WAITING_ALERT_ASSET, 
 WAITING_ALERT_PRICE, WAITING_ALERT_CONDITION, WAITING_NOTIFICATION_INTERVAL,
 WAITING_NOTIFICATION_TYPES) = range(10)


# ===== YARDIMCI FONKSİYONLAR =====
def get_or_create_user(telegram_id, username=None):
    """Kullanıcıyı veritabanında al veya oluştur"""
    db = get_db()
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    
    if not user:
        user = User(telegram_id=telegram_id, username=username)
        db.add(user)
        db.commit()
        db.refresh(user)
    
    db.close()
    return user


def get_current_price(asset_type, asset_name):
    """Şu anki fiyatı al"""
    try:
        if asset_type == 'doviz':
            data = get_doviz_data()
            if data and asset_name in data:
                # Alış ve satış ortalaması
                alis = data[asset_name].get('alis', 0)
                satis = data[asset_name].get('satis', 0)
                if alis and satis:
                    return (float(alis) + float(satis)) / 2
        elif asset_type == 'altin':
            data = get_altin_data()
            if data and asset_name in data:
                # Satış fiyatını kullan
                satis = data[asset_name].get('satis', 0)
                if satis:
                    return float(satis)
        elif asset_type == 'borsa':
            data = get_borsa_data()
            if data and asset_name in data:
                fiyat = data[asset_name].get('fiyat', 0)
                if fiyat:
                    return float(fiyat)
    except Exception as e:
        logger.error(f"Fiyat alma hatası: {e}")
    
    return None


def format_price(price):
    """Fiyatı formatla"""
    if price is None:
        return "N/A"
    
    # Binlik ayırıcı ve 2 ondalık basamak
    return f"{price:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.')


# ===== BOT KOMUTLARI =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bot başlangıç komutu"""
    user = update.effective_user
    get_or_create_user(user.id, user.username)
    
    welcome_text = f"""
🎯 *FinAlert'e Hoş Geldiniz!* 🎯

Merhaba {user.first_name}! 

FinAlert ile anlık piyasa verileri, otomatik uyarılar ve portföy takibi yapabilirsiniz.

📊 *Özellikler:*
• Döviz, Altın ve Borsa verilerini anlık sorgulama
• Hedef fiyat uyarıları
• Periyodik raporlar
• Portföy kar/zarar takibi

Başlamak için /menu komutunu kullanın!
"""
    
    await update.message.reply_text(welcome_text, parse_mode='Markdown')


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ana menü"""
    keyboard = [
        [
            InlineKeyboardButton("💵 Döviz", callback_data='menu_doviz'),
            InlineKeyboardButton("🏆 Altın", callback_data='menu_altin'),
        ],
        [
            InlineKeyboardButton("📈 Borsa", callback_data='menu_borsa'),
            InlineKeyboardButton("💼 Portföy", callback_data='menu_portfolio'),
        ],
        [
            InlineKeyboardButton("🔔 Uyarılar", callback_data='menu_alerts'),
            InlineKeyboardButton("⏰ Bildirimler", callback_data='menu_notifications'),
        ],
        [
            InlineKeyboardButton("❓ Yardım", callback_data='menu_help'),
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            '📱 *Ana Menü*\n\nBir seçenek seçin:',
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            '📱 *Ana Menü*\n\nBir seçenek seçin:',
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )


# ===== DÖVİZ MENÜSÜ =====
async def doviz_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Döviz menüsü"""
    keyboard = [
        [
            InlineKeyboardButton("💵 USD", callback_data='doviz_USD'),
            InlineKeyboardButton("💶 EUR", callback_data='doviz_EUR'),
        ],
        [
            InlineKeyboardButton("💷 GBP", callback_data='doviz_GBP'),
            InlineKeyboardButton("📊 Tümü", callback_data='doviz_all'),
        ],
        [InlineKeyboardButton("◀️ Geri", callback_data='menu_main')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            '💱 *Döviz Kurları*\n\nHangi dövizi görmek istersiniz?',
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            '💱 *Döviz Kurları*\n\nHangi dövizi görmek istersiniz?',
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )


async def show_doviz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Döviz bilgilerini göster"""
    query = update.callback_query
    await query.answer()
    
    doviz_type = query.data.split('_')[1]
    
    # Döviz verilerini çek
    doviz_data = get_doviz_data()
    kaynak = doviz_data.get('_kaynak', 'Bilinmeyen')
    
    if doviz_type == 'all':
        # Tüm dövizleri göster
        message = "💱 *Güncel Döviz Kurları*\n\n"
        
        # Döviz isimleri Türkçe
        currency_names = {
            'USD': '💵 Dolar (USD)',
            'EUR': '💶 Euro (EUR)',
            'GBP': '💷 Sterlin (GBP)'
        }
        
        for currency, data in doviz_data.items():
            if currency == '_kaynak':
                continue
            currency_name = currency_names.get(currency, currency)
            message += f"*{currency_name}*\n"
            message += f"  Alış: ₺{format_price(data['alis'])}\n"
            message += f"  Satış: ₺{format_price(data['satis'])}\n\n"
        
        message += f"📡 Kaynak: {kaynak}\n"
        message += f"🕐 {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    else:
        # Tek döviz göster
        if doviz_type in doviz_data:
            data = doviz_data[doviz_type]
            
            # Döviz isimleri Türkçe
            currency_names = {
                'USD': '💵 Dolar',
                'EUR': '💶 Euro',
                'GBP': '💷 Sterlin'
            }
            currency_name = currency_names.get(doviz_type, doviz_type)
            
            message = f"💱 *{currency_name} Kuru*\n\n"
            message += f"Alış: ₺{format_price(data['alis'])}\n"
            message += f"Satış: ₺{format_price(data['satis'])}\n\n"
            message += f"📡 Kaynak: {kaynak}\n"
            message += f"🕐 {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        else:
            message = "❌ Veri çekilemedi. Lütfen tekrar deneyin."
    
    keyboard = [[InlineKeyboardButton("◀️ Geri", callback_data='menu_doviz')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')


# ===== ALTIN MENÜSÜ =====
async def altin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Altın menüsü"""
    keyboard = [
        [
            InlineKeyboardButton("📏 Gram", callback_data='altin_gram'),
            InlineKeyboardButton("🪙 Çeyrek", callback_data='altin_ceyrek'),
        ],
        [
            InlineKeyboardButton("🥇 Yarım", callback_data='altin_yarim'),
            InlineKeyboardButton("🏆 Tam", callback_data='altin_tam'),
        ],
        [
            InlineKeyboardButton("🇹🇷 Cumhuriyet", callback_data='altin_cumhuriyet'),
            InlineKeyboardButton("🌍 Ons", callback_data='altin_ons'),
        ],
        [InlineKeyboardButton("📊 Tümü", callback_data='altin_all')],
        [InlineKeyboardButton("◀️ Geri", callback_data='menu_main')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            '🏆 *Altın Fiyatları*\n\nHangisini görmek istersiniz?',
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            '🏆 *Altın Fiyatları*\n\nHangisini görmek istersiniz?',
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )


async def show_altin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Altın bilgilerini göster"""
    query = update.callback_query
    await query.answer()
    
    altin_type = query.data.split('_')[1]
    
    # Altın verilerini çek
    altin_data = get_altin_data()
    kaynak = altin_data.get('_kaynak', 'Bilinmeyen')
    
    if altin_type == 'all':
        # Tüm altın türlerini göster
        message = "🏆 *Güncel Altın Fiyatları*\n\n"
        
        altin_names = {
            'gram': '📏 Gram Altın',
            'ceyrek': '🪙 Çeyrek Altın',
            'yarim': '🥇 Yarım Altın',
            'tam': '🏆 Tam Altın',
            'cumhuriyet': '🇹🇷 Cumhuriyet Altını',
            'ons': '🌍 Ons Altın'
        }
        
        for key, name in altin_names.items():
            if key in altin_data and key != '_kaynak':
                data = altin_data[key]
                message += f"*{name}*\n"
                message += f"  Alış: ₺{format_price(data['alis'])}\n"
                message += f"  Satış: ₺{format_price(data['satis'])}\n\n"
        
        message += f"📡 Kaynak: {kaynak}\n"
        message += f"🕐 {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    else:
        # Tek altın türü göster
        if altin_type in altin_data:
            data = altin_data[altin_type]
            altin_names = {
                'gram': '📏 Gram Altın',
                'ceyrek': '🪙 Çeyrek Altın',
                'yarim': '🥇 Yarım Altın',
                'tam': '🏆 Tam Altın',
                'cumhuriyet': '🇹🇷 Cumhuriyet Altını',
                'ons': '🌍 Ons Altın'
            }
            
            message = f"🏆 *{altin_names.get(altin_type, altin_type)}*\n\n"
            message += f"Alış: ₺{format_price(data['alis'])}\n"
            message += f"Satış: ₺{format_price(data['satis'])}\n\n"
            message += f"📡 Kaynak: {kaynak}\n"
            message += f"🕐 {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        else:
            message = "❌ Veri çekilemedi. Lütfen tekrar deneyin."
    
    keyboard = [[InlineKeyboardButton("◀️ Geri", callback_data='menu_altin')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')


# ===== BORSA MENÜSÜ =====
async def borsa_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Borsa menüsü"""
    keyboard = [
        [InlineKeyboardButton("📊 BIST 100", callback_data='borsa_XU100')],
        [
            InlineKeyboardButton("THYAO", callback_data='borsa_THYAO'),
            InlineKeyboardButton("GARAN", callback_data='borsa_GARAN'),
        ],
        [
            InlineKeyboardButton("AKBNK", callback_data='borsa_AKBNK'),
            InlineKeyboardButton("EREGL", callback_data='borsa_EREGL'),
        ],
        [InlineKeyboardButton("📊 Tümü", callback_data='borsa_all')],
        [InlineKeyboardButton("◀️ Geri", callback_data='menu_main')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            '📈 *Borsa İstanbul*\n\nHangisini görmek istersiniz?',
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            '📈 *Borsa İstanbul*\n\nHangisini görmek istersiniz?',
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )


async def show_borsa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Borsa bilgilerini göster"""
    query = update.callback_query
    await query.answer()
    
    borsa_type = query.data.split('_')[1]
    
    # Borsa verilerini çek
    borsa_data = get_borsa_data()
    kaynak = borsa_data.get('_kaynak', 'Bilinmeyen')
    
    if borsa_type == 'all':
        # Tüm hisseleri göster
        message = "📈 *Borsa İstanbul - Güncel Değerler*\n\n"
        
        for symbol, data in borsa_data.items():
            if symbol == '_kaynak':
                continue
            degisim = data['degisim_yuzde']
            emoji = "📈" if degisim > 0 else "📉" if degisim < 0 else "➖"
            
            message += f"*{symbol}*\n"
            message += f"  Değer: ₺{format_price(data['deger'])}\n"
            message += f"  Değişim: {emoji} %{degisim:.2f}\n\n"
        
        message += f"📡 Kaynak: {kaynak}\n"
        message += f"🕐 {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    else:
        # Tek hisse göster
        if borsa_type in borsa_data:
            data = borsa_data[borsa_type]
            degisim = data['degisim_yuzde']
            emoji = "📈" if degisim > 0 else "📉" if degisim < 0 else "➖"
            
            message = f"📈 *{borsa_type}*\n\n"
            message += f"Değer: ₺{format_price(data['deger'])}\n"
            message += f"Değişim: {emoji} %{degisim:.2f}\n\n"
            message += f"📡 Kaynak: {kaynak}\n"
            message += f"🕐 {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        else:
            message = "❌ Veri çekilemedi. Lütfen tekrar deneyin."
    
    keyboard = [[InlineKeyboardButton("◀️ Geri", callback_data='menu_borsa')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')


# ===== CALLBACK HANDLER =====
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tüm buton callback'lerini yönet"""
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    
    # Menü yönlendirmeleri
    if callback_data == 'menu_main':
        await menu(update, context)
    elif callback_data == 'menu_doviz':
        await doviz_menu(update, context)
    elif callback_data == 'menu_altin':
        await altin_menu(update, context)
    elif callback_data == 'menu_borsa':
        await borsa_menu(update, context)
    elif callback_data.startswith('doviz_'):
        await show_doviz(update, context)
    elif callback_data.startswith('altin_'):
        await show_altin(update, context)
    elif callback_data.startswith('borsa_'):
        await show_borsa(update, context)
    elif callback_data == 'menu_portfolio':
        await portfolio_menu(update, context)
    elif callback_data == 'portfolio_report':
        await portfolio_report(update, context)
    elif callback_data == 'portfolio_add':
        await portfolio_add_start(update, context)
    elif callback_data == 'portfolio_delete':
        await portfolio_delete_start(update, context)
    elif callback_data.startswith('portfolio_add_'):
        await portfolio_select_type(update, context)
    elif callback_data.startswith('portfolio_asset_'):
        await portfolio_select_asset(update, context)
    elif callback_data.startswith('portfolio_del_'):
        await portfolio_delete_confirm(update, context)
    elif callback_data == 'menu_alerts':
        await alerts_menu(update, context)
    elif callback_data == 'alert_list':
        await alert_list(update, context)
    elif callback_data == 'alert_add':
        await alert_add_start(update, context)
    elif callback_data == 'alert_delete':
        await alert_delete_start(update, context)
    elif callback_data.startswith('alert_type_'):
        await alert_select_type(update, context)
    elif callback_data.startswith('alert_asset_'):
        await alert_select_asset(update, context)
    elif callback_data.startswith('alert_cond_'):
        await alert_select_condition(update, context)
    elif callback_data.startswith('alert_del_'):
        await alert_delete_confirm(update, context)
    elif callback_data == 'menu_notifications':
        await notifications_menu(update, context)
    elif callback_data == 'notification_list':
        await notification_list(update, context)
    elif callback_data == 'notification_add':
        await notification_add_start(update, context)
    elif callback_data == 'notification_delete':
        await notification_delete_start(update, context)
    elif callback_data.startswith('notif_interval_'):
        await notification_select_interval(update, context)
    elif callback_data.startswith('notif_type_'):
        await notification_select_types(update, context)
    elif callback_data.startswith('notif_del_'):
        await notification_delete_confirm(update, context)
    elif callback_data == 'menu_help':
        await show_help(update, context)


async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Yardım mesajı"""
    help_text = """
📚 *FinAlert Yardım*

*Komutlar:*
/start - Botu başlat
/menu - Ana menü
/doviz - Döviz kurları
/altin - Altın fiyatları
/borsa - Borsa verileri
/portfolio - Portföyünüz
/alerts - Uyarılarınız
/notifications - Bildirimleriniz

*Özellikler:*
• 💱 Anlık döviz kurları
• 🏆 Altın fiyatları
• 📈 Borsa verileri
• 💼 Portföy takibi
• 🔔 Fiyat uyarıları
• ⏰ Periyodik raporlar
"""
    
    keyboard = [[InlineKeyboardButton("◀️ Ana Menü", callback_data='menu_main')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            help_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            help_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )


# ===== PORTFÖY MENÜSÜ =====
async def portfolio_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Portföy menüsü"""
    user = update.effective_user if update.message else update.callback_query.from_user
    user_obj = get_or_create_user(user.id, user.username)
    
    # Portföy verilerini al
    portfolio_data = calculate_portfolio_profit_loss(user_obj.id)
    
    keyboard = [
        [InlineKeyboardButton("➕ Varlık Ekle", callback_data='portfolio_add')],
        [InlineKeyboardButton("📊 Detaylı Rapor", callback_data='portfolio_report')],
        [InlineKeyboardButton("🗑 Varlık Sil", callback_data='portfolio_delete')],
        [InlineKeyboardButton("◀️ Geri", callback_data='menu_main')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if portfolio_data and portfolio_data['items']:
        total_emoji = "📈" if portfolio_data['total_profit_loss'] > 0 else "📉"
        summary = f"""💼 *Portföy Özeti*

💰 Toplam Yatırım: ₺{format_price(portfolio_data['total_investment'])}
💎 Güncel Değer: ₺{format_price(portfolio_data['total_current_value'])}
{total_emoji} Toplam K/Z: ₺{format_price(portfolio_data['total_profit_loss'])} (%{portfolio_data['total_profit_loss_percent']:.2f})

Toplam {len(portfolio_data['items'])} varlık"""
    else:
        summary = "💼 *Portföyünüz*\n\nHenüz portföyünüze varlık eklemediniz.\n\n'Varlık Ekle' butonunu kullanarak başlayabilirsiniz!"
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            summary,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            summary,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )


async def portfolio_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Detaylı portföy raporu göster"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    user_obj = get_or_create_user(user.id, user.username)
    
    portfolio_data = calculate_portfolio_profit_loss(user_obj.id)
    report = format_portfolio_report(portfolio_data)
    
    keyboard = [[InlineKeyboardButton("◀️ Geri", callback_data='menu_portfolio')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(report, reply_markup=reply_markup, parse_mode='Markdown')


async def portfolio_add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Portföye varlık eklemeye başla"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("💱 Döviz", callback_data='portfolio_add_doviz')],
        [InlineKeyboardButton("🏆 Altın", callback_data='portfolio_add_altin')],
        [InlineKeyboardButton("📈 Hisse", callback_data='portfolio_add_hisse')],
        [InlineKeyboardButton("❌ İptal", callback_data='menu_portfolio')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        '➕ *Varlık Ekle*\n\nHangi tür varlık eklemek istersiniz?',
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def portfolio_select_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Portföy varlık türü seçildi - Adım 1"""
    query = update.callback_query
    await query.answer()
    
    asset_type = query.data.replace('portfolio_add_', '')
    context.user_data['portfolio_asset_type'] = asset_type
    
    # Varlık türüne göre seçenekler
    if asset_type == 'doviz':
        message = "💱 *Hangi Döviz?*"
        keyboard = [
            [InlineKeyboardButton("USD (Dolar)", callback_data='portfolio_asset_USD')],
            [InlineKeyboardButton("EUR (Euro)", callback_data='portfolio_asset_EUR')],
            [InlineKeyboardButton("GBP (Sterlin)", callback_data='portfolio_asset_GBP')],
            [InlineKeyboardButton("◀️ Geri", callback_data='portfolio_add')]
        ]
    elif asset_type == 'altin':
        message = "🏆 *Hangi Altın?*"
        keyboard = [
            [InlineKeyboardButton("📏 Gram Altın", callback_data='portfolio_asset_gram')],
            [InlineKeyboardButton("🪙 Çeyrek Altın", callback_data='portfolio_asset_ceyrek')],
            [InlineKeyboardButton("🥇 Yarım Altın", callback_data='portfolio_asset_yarim')],
            [InlineKeyboardButton("🏆 Tam Altın", callback_data='portfolio_asset_tam')],
            [InlineKeyboardButton("◀️ Geri", callback_data='portfolio_add')]
        ]
    else:  # hisse
        message = "📈 *Hangi Hisse?*"
        keyboard = [
            [InlineKeyboardButton("BIST 100", callback_data='portfolio_asset_XU100')],
            [InlineKeyboardButton("THYAO", callback_data='portfolio_asset_THYAO')],
            [InlineKeyboardButton("GARAN", callback_data='portfolio_asset_GARAN')],
            [InlineKeyboardButton("AKBNK", callback_data='portfolio_asset_AKBNK')],
            [InlineKeyboardButton("◀️ Geri", callback_data='portfolio_add')]
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')


async def portfolio_select_asset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Portföy varlık seçildi - Adım 2: Miktar sor"""
    query = update.callback_query
    await query.answer()
    
    asset_name = query.data.replace('portfolio_asset_', '')
    context.user_data['portfolio_asset_name'] = asset_name
    
    asset_type = context.user_data['portfolio_asset_type']
    
    # Şu anki fiyatı göster
    current_price = get_current_price(asset_type, asset_name)
    
    if current_price:
        price_text = f"Şu anki fiyat: ₺{format_price(current_price)}"
    else:
        price_text = "Şu anki fiyat alınamadı"
    
    message = f"""📊 *{asset_name} Ekle*

{price_text}

Kaç adet/miktar eklemek istersiniz?
(Örneğin: 100)"""
    
    keyboard = [[InlineKeyboardButton("◀️ İptal", callback_data='menu_portfolio')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
    
    # Bir sonraki mesaj için handler state'i kaydet
    context.user_data['waiting_for_portfolio_amount'] = True


async def portfolio_save_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Portföy miktar girişi - Adım 3: Alış fiyatı sor"""
    if not context.user_data.get('waiting_for_portfolio_amount'):
        return
    
    try:
        # Miktarı parse et
        amount_text = update.message.text.replace(',', '.').strip()
        amount = float(amount_text)
        
        if amount <= 0:
            await update.message.reply_text(
                "❌ Geçersiz miktar! Pozitif bir sayı girin.\n\nTekrar deneyin:"
            )
            return
        
        context.user_data['portfolio_amount'] = amount
        context.user_data.pop('waiting_for_portfolio_amount', None)
        
        asset_name = context.user_data['portfolio_asset_name']
        asset_type = context.user_data['portfolio_asset_type']
        
        # Şu anki fiyatı göster
        current_price = get_current_price(asset_type, asset_name)
        
        if current_price:
            price_text = f"(Şu anki: ₺{format_price(current_price)})"
        else:
            price_text = ""
        
        message = f"""💰 *Alış Fiyatı*

{asset_name} - {amount} adet

Kaç TL'den aldınız? {price_text}
(Örneğin: 40.50)"""
        
        keyboard = [[InlineKeyboardButton("◀️ İptal", callback_data='menu_portfolio')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        
        # Bir sonraki mesaj için handler state'i kaydet
        context.user_data['waiting_for_portfolio_price'] = True
    
    except ValueError:
        await update.message.reply_text(
            "❌ Geçersiz format! Sayı girin (örn: 100).\n\nTekrar deneyin:"
        )


async def portfolio_save_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Portföy alış fiyatı - Adım 4: Kaydet"""
    if not context.user_data.get('waiting_for_portfolio_price'):
        return
    
    try:
        # Fiyatı parse et
        price_text = update.message.text.replace(',', '.').strip()
        purchase_price = float(price_text)
        
        if purchase_price <= 0:
            await update.message.reply_text(
                "❌ Geçersiz fiyat! Pozitif bir sayı girin.\n\nTekrar deneyin:"
            )
            return
        
        # Veritabanına kaydet
        user = update.effective_user
        user_obj = get_or_create_user(user.id, user.username)
        
        asset_type = context.user_data['portfolio_asset_type']
        asset_name = context.user_data['portfolio_asset_name']
        amount = context.user_data['portfolio_amount']
        
        db = get_db()
        new_portfolio_item = Portfolio(
            user_id=user_obj.id,
            asset_type=asset_type,
            asset_name=asset_name,
            amount=amount,
            purchase_price=purchase_price
        )
        db.add(new_portfolio_item)
        db.commit()
        db.close()
        
        # Temizle
        context.user_data.pop('waiting_for_portfolio_price', None)
        context.user_data.pop('portfolio_asset_type', None)
        context.user_data.pop('portfolio_asset_name', None)
        context.user_data.pop('portfolio_amount', None)
        
        total_investment = amount * purchase_price
        
        message = f"""✅ *Portföye Eklendi!*

📊 {asset_name}
📦 Miktar: {amount}
💰 Alış Fiyatı: ₺{format_price(purchase_price)}
💵 Toplam Yatırım: ₺{format_price(total_investment)}

Portföy raporunuzdan kar/zarar takibi yapabilirsiniz!"""
        
        keyboard = [
            [InlineKeyboardButton("💼 Portföyüm", callback_data='menu_portfolio')],
            [InlineKeyboardButton("📱 Ana Menü", callback_data='menu_main')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
    
    except ValueError:
        await update.message.reply_text(
            "❌ Geçersiz format! Sayı girin (örn: 40.50).\n\nTekrar deneyin:"
        )
    except Exception as e:
        await update.message.reply_text(
            f"❌ Hata oluştu: {e}\n\n/menu ile ana menüye dönebilirsiniz."
        )
        context.user_data.pop('waiting_for_portfolio_price', None)


async def portfolio_delete_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Portföy varlık silme - Silmek için varlık seç"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    user_obj = get_or_create_user(user.id, user.username)
    
    # Portföy verilerini al
    db = get_db()
    portfolio_items = db.query(Portfolio).filter(Portfolio.user_id == user_obj.id).all()
    db.close()
    
    if not portfolio_items:
        message = "🗑 *Varlık Sil*\n\nPortföyünüzde varlık yok."
        keyboard = [[InlineKeyboardButton("◀️ Geri", callback_data='menu_portfolio')]]
    else:
        message = "🗑 *Hangi Varlığı Silmek İstersiniz?*\n\nSeçmek için aşağıdan birine tıklayın:"
        
        keyboard = []
        for item in portfolio_items:
            emoji = {'doviz': '💱', 'altin': '🏆', 'hisse': '📈'}.get(item.asset_type, '💰')
            button_text = f"{emoji} {item.asset_name} ({item.amount} adet)"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f'portfolio_del_{item.id}')])
        
        keyboard.append([InlineKeyboardButton("◀️ İptal", callback_data='menu_portfolio')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')


async def portfolio_delete_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Portföy varlık silme - Onay ve sil"""
    query = update.callback_query
    await query.answer()
    
    item_id = int(query.data.replace('portfolio_del_', ''))
    
    user = query.from_user
    user_obj = get_or_create_user(user.id, user.username)
    
    db = get_db()
    portfolio_item = db.query(Portfolio).filter(
        Portfolio.id == item_id,
        Portfolio.user_id == user_obj.id
    ).first()
    
    if portfolio_item:
        # Varlık bilgilerini kaydet
        asset_name = portfolio_item.asset_name
        amount = portfolio_item.amount
        
        # Veritabanından sil
        db.delete(portfolio_item)
        db.commit()
        
        message = f"""✅ *Varlık Silindi!*

{asset_name} ({amount} adet) portföyünüzden çıkarıldı."""
    else:
        message = "❌ Varlık bulunamadı!"
    
    db.close()
    
    keyboard = [
        [InlineKeyboardButton("💼 Portföyüm", callback_data='menu_portfolio')],
        [InlineKeyboardButton("📱 Ana Menü", callback_data='menu_main')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')


# ===== UYARILAR MENÜSÜ =====
async def alerts_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Uyarılar menüsü"""
    user = update.effective_user if update.message else update.callback_query.from_user
    user_obj = get_or_create_user(user.id, user.username)
    
    # Aktif uyarıları al
    db = get_db()
    alerts = db.query(Alert).filter(
        Alert.user_id == user_obj.id,
        Alert.is_active == True
    ).all()
    db.close()
    
    keyboard = [
        [InlineKeyboardButton("➕ Yeni Uyarı", callback_data='alert_add')],
        [InlineKeyboardButton("📋 Uyarılarım", callback_data='alert_list')],
        [InlineKeyboardButton("🗑 Uyarı Sil", callback_data='alert_delete')],
        [InlineKeyboardButton("◀️ Geri", callback_data='menu_main')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    summary = f"""🔔 *Fiyat Uyarıları*

Aktif Uyarı Sayısı: {len(alerts)}

Hedef fiyata ulaşıldığında otomatik bildirim alırsınız."""
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            summary,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            summary,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )


async def alert_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Uyarı listesini göster"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    user_obj = get_or_create_user(user.id, user.username)
    
    db = get_db()
    alerts = db.query(Alert).filter(
        Alert.user_id == user_obj.id,
        Alert.is_active == True
    ).all()
    db.close()
    
    if not alerts:
        message = "📋 *Uyarılarınız*\n\nHenüz aktif uyarınız yok."
    else:
        message = "📋 *Aktif Uyarılarınız*\n\n"
        
        for alert in alerts:
            emoji = {'doviz': '💱', 'altin': '🏆', 'hisse': '📈'}.get(alert.asset_type, '💰')
            condition = 'üstüne çıkınca' if alert.condition == 'ustu' else 'altına düşünce'
            
            message += f"{emoji} *{alert.asset_name}*\n"
            message += f"  ₺{format_price(alert.target_price)} {condition}\n\n"
    
    keyboard = [[InlineKeyboardButton("◀️ Geri", callback_data='menu_alerts')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')


async def alert_delete_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Uyarı silme - Silmek için uyarı seç"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    user_obj = get_or_create_user(user.id, user.username)
    
    db = get_db()
    alerts = db.query(Alert).filter(
        Alert.user_id == user_obj.id,
        Alert.is_active == True
    ).all()
    db.close()
    
    if not alerts:
        message = "🗑 *Uyarı Sil*\n\nHenüz aktif uyarınız yok."
        keyboard = [[InlineKeyboardButton("◀️ Geri", callback_data='menu_alerts')]]
    else:
        message = "🗑 *Hangi Uyarıyı Silmek İstersiniz?*\n\nSeçmek için aşağıdan birine tıklayın:"
        
        keyboard = []
        for alert in alerts:
            emoji = {'doviz': '💱', 'altin': '🏆', 'borsa': '📈'}.get(alert.asset_type, '💰')
            condition = '📈' if alert.condition == 'ustu' else '📉'
            button_text = f"{emoji} {alert.asset_name} {condition} ₺{format_price(alert.target_price)}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f'alert_del_{alert.id}')])
        
        keyboard.append([InlineKeyboardButton("◀️ İptal", callback_data='menu_alerts')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')


async def alert_delete_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Uyarı silme - Onay ve sil"""
    query = update.callback_query
    await query.answer()
    
    alert_id = int(query.data.replace('alert_del_', ''))
    
    user = query.from_user
    user_obj = get_or_create_user(user.id, user.username)
    
    db = get_db()
    alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.user_id == user_obj.id
    ).first()
    
    if alert:
        # Uyarı bilgilerini kaydet
        asset_name = alert.asset_name
        target_price = alert.target_price
        
        # Veritabanından sil (soft delete - is_active = False)
        alert.is_active = False
        db.commit()
        
        message = f"""✅ *Uyarı Silindi!*

{asset_name} - ₺{format_price(target_price)} uyarısı başarıyla silindi."""
    else:
        message = "❌ Uyarı bulunamadı!"
    
    db.close()
    
    keyboard = [
        [InlineKeyboardButton("🔔 Uyarılarım", callback_data='alert_list')],
        [InlineKeyboardButton("📱 Ana Menü", callback_data='menu_main')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')


# ===== BİLDİRİMLER MENÜSÜ =====
async def notifications_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bildirimler menüsü"""
    user = update.effective_user if update.message else update.callback_query.from_user
    user_obj = get_or_create_user(user.id, user.username)
    
    # Aktif bildirimleri al
    db = get_db()
    notifications = db.query(TimeNotification).filter(
        TimeNotification.user_id == user_obj.id,
        TimeNotification.is_active == True
    ).all()
    db.close()
    
    keyboard = [
        [InlineKeyboardButton("➕ Yeni Bildirim", callback_data='notification_add')],
        [InlineKeyboardButton("📋 Bildirimlerim", callback_data='notification_list')],
        [InlineKeyboardButton("🗑 Bildirim Sil", callback_data='notification_delete')],
        [InlineKeyboardButton("◀️ Geri", callback_data='menu_main')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    summary = f"""⏰ *Periyodik Bildirimler*

Aktif Bildirim: {len(notifications)}

Belirlediğiniz aralıklarla otomatik piyasa raporu alırsınız."""
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            summary,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            summary,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )


async def notification_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bildirim listesini göster"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    user_obj = get_or_create_user(user.id, user.username)
    
    db = get_db()
    notifications = db.query(TimeNotification).filter(
        TimeNotification.user_id == user_obj.id,
        TimeNotification.is_active == True
    ).all()
    db.close()
    
    if not notifications:
        message = "📋 *Bildirimleriniz*\n\nHenüz aktif bildiriminiz yok."
    else:
        message = "📋 *Aktif Bildirimleriniz*\n\n"
        
        interval_names = {
            'her_saat': '⏰ Her Saat',
            'her_4_saat': '⏰ Her 4 Saat',
            'her_8_saat': '⏰ Her 8 Saat',
            'gunluk': '⏰ Günlük'
        }
        
        for notif in notifications:
            interval_name = interval_names.get(notif.interval, notif.interval)
            types = notif.asset_types.replace(',', ', ').upper()
            
            message += f"{interval_name}\n"
            message += f"  📊 {types}\n\n"
    
    keyboard = [[InlineKeyboardButton("◀️ Geri", callback_data='menu_notifications')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')


async def notification_delete_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bildirim silme - Silmek için bildirim seç"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    user_obj = get_or_create_user(user.id, user.username)
    
    db = get_db()
    notifications = db.query(TimeNotification).filter(
        TimeNotification.user_id == user_obj.id,
        TimeNotification.is_active == True
    ).all()
    db.close()
    
    if not notifications:
        message = "🗑 *Bildirim Sil*\n\nHenüz aktif bildiriminiz yok."
        keyboard = [[InlineKeyboardButton("◀️ Geri", callback_data='menu_notifications')]]
    else:
        message = "🗑 *Hangi Bildirimi Silmek İstersiniz?*\n\nSeçmek için aşağıdan birine tıklayın:"
        
        interval_names = {
            'her_saat': '⏰ Her Saat',
            'her_4_saat': '⏰ Her 4 Saat',
            'her_8_saat': '⏰ Her 8 Saat',
            'gunluk': '⏰ Günlük'
        }
        
        keyboard = []
        for notif in notifications:
            interval_name = interval_names.get(notif.interval, notif.interval)
            types = notif.asset_types.replace(',', '+').upper()
            button_text = f"{interval_name} - {types}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f'notif_del_{notif.id}')])
        
        keyboard.append([InlineKeyboardButton("◀️ İptal", callback_data='menu_notifications')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')


async def notification_delete_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bildirim silme - Onay ve sil"""
    query = update.callback_query
    await query.answer()
    
    notif_id = int(query.data.replace('notif_del_', ''))
    
    user = query.from_user
    user_obj = get_or_create_user(user.id, user.username)
    
    db = get_db()
    notification = db.query(TimeNotification).filter(
        TimeNotification.id == notif_id,
        TimeNotification.user_id == user_obj.id
    ).first()
    
    if notification:
        # Bildirim bilgilerini kaydet
        interval_names = {
            'her_saat': 'Her Saat',
            'her_4_saat': 'Her 4 Saat',
            'her_8_saat': 'Her 8 Saat',
            'gunluk': 'Günlük'
        }
        interval_name = interval_names.get(notification.interval, notification.interval)
        
        # Veritabanından sil (soft delete - is_active = False)
        notification.is_active = False
        db.commit()
        
        message = f"""✅ *Bildirim Silindi!*

{interval_name} bildirimi başarıyla silindi."""
    else:
        message = "❌ Bildirim bulunamadı!"
    
    db.close()
    
    keyboard = [
        [InlineKeyboardButton("📋 Bildirimlerim", callback_data='notification_list')],
        [InlineKeyboardButton("📱 Ana Menü", callback_data='menu_main')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')


# ===== UYARI EKLEME =====
async def alert_add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Yeni uyarı ekleme başlat - Adım 1: Varlık türü seç"""
    query = update.callback_query
    await query.answer()
    
    message = """🔔 *Yeni Fiyat Uyarısı Oluştur*

Hangi varlık türü için uyarı oluşturmak istersiniz?"""
    
    keyboard = [
        [InlineKeyboardButton("💵 Döviz", callback_data='alert_type_doviz')],
        [InlineKeyboardButton("🏆 Altın", callback_data='alert_type_altin')],
        [InlineKeyboardButton("📈 Borsa", callback_data='alert_type_borsa')],
        [InlineKeyboardButton("◀️ İptal", callback_data='menu_alerts')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')


async def alert_select_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Uyarı ekleme - Adım 2: Varlık seç"""
    query = update.callback_query
    await query.answer()
    
    asset_type = query.data.replace('alert_type_', '')
    context.user_data['alert_asset_type'] = asset_type
    
    # Varlık türüne göre seçenekler
    if asset_type == 'doviz':
        message = "💵 *Hangi döviz için uyarı?*"
        keyboard = [
            [InlineKeyboardButton("USD (Dolar)", callback_data='alert_asset_USD')],
            [InlineKeyboardButton("EUR (Euro)", callback_data='alert_asset_EUR')],
            [InlineKeyboardButton("GBP (Sterlin)", callback_data='alert_asset_GBP')],
            [InlineKeyboardButton("◀️ Geri", callback_data='alert_add')]
        ]
    elif asset_type == 'altin':
        message = "🏆 *Hangi altın için uyarı?*"
        keyboard = [
            [InlineKeyboardButton("📏 Gram Altın", callback_data='alert_asset_gram')],
            [InlineKeyboardButton("🪙 Çeyrek Altın", callback_data='alert_asset_ceyrek')],
            [InlineKeyboardButton("🥇 Yarım Altın", callback_data='alert_asset_yarim')],
            [InlineKeyboardButton("🏆 Tam Altın", callback_data='alert_asset_tam')],
            [InlineKeyboardButton("◀️ Geri", callback_data='alert_add')]
        ]
    else:  # borsa
        message = "📈 *Hangi hisse için uyarı?*"
        keyboard = [
            [InlineKeyboardButton("BIST 100", callback_data='alert_asset_XU100')],
            [InlineKeyboardButton("THYAO", callback_data='alert_asset_THYAO')],
            [InlineKeyboardButton("GARAN", callback_data='alert_asset_GARAN')],
            [InlineKeyboardButton("AKBNK", callback_data='alert_asset_AKBNK')],
            [InlineKeyboardButton("◀️ Geri", callback_data='alert_add')]
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')


async def alert_select_asset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Uyarı ekleme - Adım 3: Hedef fiyat ve koşul"""
    query = update.callback_query
    await query.answer()
    
    asset_name = query.data.replace('alert_asset_', '')
    context.user_data['alert_asset_name'] = asset_name
    
    # Şu anki fiyatı göster
    asset_type = context.user_data['alert_asset_type']
    current_price = get_current_price(asset_type, asset_name)
    
    if current_price:
        price_text = f"Şu anki fiyat: ₺{format_price(current_price)}"
    else:
        price_text = "Şu anki fiyat alınamadı"
    
    message = f"""⚡ *{asset_name} Uyarısı*

{price_text}

Hedef fiyata ulaştığında bildirim almak ister misiniz?"""
    
    keyboard = [
        [InlineKeyboardButton("📈 Üstüne çıkınca", callback_data='alert_cond_ustu')],
        [InlineKeyboardButton("📉 Altına düşünce", callback_data='alert_cond_alti')],
        [InlineKeyboardButton("◀️ Geri", callback_data=f'alert_type_{asset_type}')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')


async def alert_select_condition(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Uyarı ekleme - Adım 4: Fiyat gir"""
    query = update.callback_query
    await query.answer()
    
    condition = query.data.replace('alert_cond_', '')
    context.user_data['alert_condition'] = condition
    
    asset_name = context.user_data['alert_asset_name']
    asset_type = context.user_data['alert_asset_type']
    
    cond_text = "üstüne çıkınca" if condition == 'ustu' else "altına düşünce"
    
    message = f"""💰 *Hedef Fiyat Belirle*

{asset_name} {cond_text} bildirim alacaksınız.

Lütfen hedef fiyatı yazın (örn: 42.50):"""
    
    keyboard = [[InlineKeyboardButton("◀️ İptal", callback_data='menu_alerts')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
    
    # Bir sonraki mesaj için handler state'i kaydet
    context.user_data['waiting_for_alert_price'] = True


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tüm mesaj girişlerini yönet"""
    # Portföy miktar girişi
    if context.user_data.get('waiting_for_portfolio_amount'):
        await portfolio_save_amount(update, context)
    # Portföy fiyat girişi
    elif context.user_data.get('waiting_for_portfolio_price'):
        await portfolio_save_price(update, context)
    # Uyarı fiyat girişi
    elif context.user_data.get('waiting_for_alert_price'):
        await alert_save_price(update, context)


async def alert_save_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Uyarı ekleme - Adım 5: Kaydet"""
    if not context.user_data.get('waiting_for_alert_price'):
        return
    
    try:
        # Fiyatı parse et
        price_text = update.message.text.replace(',', '.').strip()
        target_price = float(price_text)
        
        if target_price <= 0:
            await update.message.reply_text(
                "❌ Geçersiz fiyat! Pozitif bir sayı girin.\n\nTekrar deneyin:"
            )
            return
        
        # Veritabanına kaydet
        user = update.effective_user
        user_obj = get_or_create_user(user.id, user.username)
        
        asset_type = context.user_data['alert_asset_type']
        asset_name = context.user_data['alert_asset_name']
        condition = context.user_data['alert_condition']
        
        db = get_db()
        new_alert = Alert(
            user_id=user_obj.id,
            asset_type=asset_type,
            asset_name=asset_name,
            target_price=target_price,
            condition=condition,
            is_active=True
        )
        db.add(new_alert)
        db.commit()
        db.close()
        
        # Temizle
        context.user_data.pop('waiting_for_alert_price', None)
        context.user_data.pop('alert_asset_type', None)
        context.user_data.pop('alert_asset_name', None)
        context.user_data.pop('alert_condition', None)
        
        cond_text = "üstüne çıkınca" if condition == 'ustu' else "altına düşünce"
        
        message = f"""✅ *Uyarı Oluşturuldu!*

📊 {asset_name}
💰 Hedef: ₺{format_price(target_price)}
⚡ Koşul: {cond_text}

Bot her 4 dakikada kontrol edip, hedefe ulaşınca bildirim gönderecek!"""
        
        keyboard = [
            [InlineKeyboardButton("🔔 Uyarılarım", callback_data='alert_list')],
            [InlineKeyboardButton("📱 Ana Menü", callback_data='menu_main')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
    
    except ValueError:
        await update.message.reply_text(
            "❌ Geçersiz format! Sayı girin (örn: 42.50).\n\nTekrar deneyin:"
        )
    except Exception as e:
        await update.message.reply_text(
            f"❌ Hata oluştu: {e}\n\n/menu ile ana menüye dönebilirsiniz."
        )
        context.user_data.pop('waiting_for_alert_price', None)


# ===== BİLDİRİM EKLEME =====
async def notification_add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Yeni bildirim ekleme başlat - Adım 1: Aralık seç"""
    query = update.callback_query
    await query.answer()
    
    message = """⏰ *Yeni Periyodik Bildirim*

Ne sıklıkta piyasa raporu almak istersiniz?"""
    
    keyboard = [
        [InlineKeyboardButton("⏰ Her Saat", callback_data='notif_interval_her_saat')],
        [InlineKeyboardButton("⏰ Her 4 Saat", callback_data='notif_interval_her_4_saat')],
        [InlineKeyboardButton("⏰ Her 8 Saat", callback_data='notif_interval_her_8_saat')],
        [InlineKeyboardButton("⏰ Günlük", callback_data='notif_interval_gunluk')],
        [InlineKeyboardButton("◀️ İptal", callback_data='menu_notifications')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')


async def notification_select_interval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bildirim ekleme - Adım 2: Varlık türlerini seç"""
    query = update.callback_query
    await query.answer()
    
    interval = query.data.replace('notif_interval_', '')
    context.user_data['notif_interval'] = interval
    
    interval_names = {
        'her_saat': 'Her Saat',
        'her_4_saat': 'Her 4 Saat',
        'her_8_saat': 'Her 8 Saat',
        'gunluk': 'Günlük'
    }
    
    message = f"""📊 *Bildirim İçeriği*

Aralık: {interval_names.get(interval)}

Hangi piyasa verilerini raporlara dahil etmek istersiniz?
(Birden fazla seçebilirsiniz)"""
    
    keyboard = [
        [InlineKeyboardButton("💵 Döviz", callback_data='notif_type_doviz')],
        [InlineKeyboardButton("🏆 Altın", callback_data='notif_type_altin')],
        [InlineKeyboardButton("📈 Borsa", callback_data='notif_type_borsa')],
        [InlineKeyboardButton("✅ Tümü", callback_data='notif_type_all')],
        [InlineKeyboardButton("◀️ Geri", callback_data='notification_add')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')


async def notification_select_types(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bildirim ekleme - Adım 3: Kaydet"""
    query = update.callback_query
    await query.answer()
    
    selected_type = query.data.replace('notif_type_', '')
    
    if selected_type == 'all':
        asset_types = 'doviz,altin,borsa'
    else:
        asset_types = selected_type
    
    # Veritabanına kaydet
    user = query.from_user
    user_obj = get_or_create_user(user.id, user.username)
    
    interval = context.user_data['notif_interval']
    
    db = get_db()
    new_notification = TimeNotification(
        user_id=user_obj.id,
        interval=interval,
        asset_types=asset_types,
        is_active=True
    )
    db.add(new_notification)
    db.commit()
    db.close()
    
    # Temizle
    context.user_data.pop('notif_interval', None)
    
    interval_names = {
        'her_saat': 'Her Saat',
        'her_4_saat': 'Her 4 Saat',
        'her_8_saat': 'Her 8 Saat',
        'gunluk': 'Günlük'
    }
    
    type_names = {
        'doviz': '💵 Döviz',
        'altin': '🏆 Altın',
        'borsa': '📈 Borsa',
        'doviz,altin,borsa': '💵 Döviz, 🏆 Altın, 📈 Borsa'
    }
    
    message = f"""✅ *Bildirim Oluşturuldu!*

⏰ Aralık: {interval_names.get(interval)}
📊 İçerik: {type_names.get(asset_types, asset_types)}

Bot düzenli olarak piyasa raporu gönderecek!"""
    
    keyboard = [
        [InlineKeyboardButton("📋 Bildirimlerim", callback_data='notification_list')],
        [InlineKeyboardButton("📱 Ana Menü", callback_data='menu_main')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')


# ===== ANA FONKSİYON =====
def main():
    """Bot'u başlat"""
    # Veritabanını başlat
    init_db()
    
    # Bot uygulamasını oluştur
    application = Application.builder().token(config.BOT_TOKEN).build()
    
    # Komut handler'ları
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", menu))
    application.add_handler(CommandHandler("doviz", doviz_menu))
    application.add_handler(CommandHandler("altin", altin_menu))
    application.add_handler(CommandHandler("borsa", borsa_menu))
    application.add_handler(CommandHandler("portfolio", portfolio_menu))
    application.add_handler(CommandHandler("alerts", alerts_menu))
    application.add_handler(CommandHandler("notifications", notifications_menu))
    
    # Mesaj handler (fiyat/miktar girişi için)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    # Callback handler
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Arka plan görevlerini başlat
    start_alert_checker(application)
    start_time_notification_checker(application)
    
    # Bot'u çalıştır
    logger.info("🚀 FinAlert botu başlatılıyor...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()

